"""
Axon by NeuroVexon - Chat API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import asyncio
import json
import logging

from db.database import get_db
from db.models import Conversation, Message, Settings
from llm.router import llm_router
from llm.provider import ChatMessage
from agent.orchestrator import AgentOrchestrator
from agent.memory import MemoryManager
from agent.permission_manager import permission_manager, PermissionScope
from sqlalchemy import select
from core.config import LLMProvider
from core.security import decrypt_value

ENCRYPTED_SETTINGS = {"anthropic_api_key", "openai_api_key"}

# Pending approval events: approval_id -> (asyncio.Event, result_holder)
_approval_events: dict[str, tuple[asyncio.Event, dict]] = {}

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


async def load_settings_to_router(db: AsyncSession):
    """Load settings from database and update the LLM router"""
    result = await db.execute(select(Settings))
    db_settings = {s.key: s.value for s in result.scalars().all()}

    # Decrypt encrypted settings before passing to router
    for key in ENCRYPTED_SETTINGS:
        if key in db_settings and db_settings[key]:
            db_settings[key] = decrypt_value(db_settings[key])

    llm_router.update_settings(db_settings)
    return db_settings


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    message: str
    tool_calls: Optional[list] = None


class ToolApprovalRequest(BaseModel):
    session_id: str
    tool: str
    params: dict
    decision: str  # once, session, never


@router.post("/send")
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send a message and get a response (non-streaming)"""
    # Load settings and update router
    db_settings = await load_settings_to_router(db)
    current_provider = db_settings.get("llm_provider", "ollama")

    # Get or create conversation
    if request.session_id:
        conversation = await db.get(Conversation, request.session_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(
            system_prompt=request.system_prompt
        )
        db.add(conversation)
        await db.flush()

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    await db.flush()

    # Build message history from DB
    messages = []
    if conversation.system_prompt:
        messages.append(ChatMessage(role="system", content=conversation.system_prompt))

    # Load previous messages (limit to 50 for token budget)
    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .where(Message.role.in_(["user", "assistant"]))
        .order_by(Message.created_at.asc())
        .limit(50)
    )
    for msg in history_result.scalars().all():
        messages.append(ChatMessage(role=msg.role, content=msg.content))

    # Get LLM response with configured provider
    try:
        provider = llm_router.get_provider(LLMProvider(current_provider))
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid LLM provider: {current_provider}")
    response = await provider.chat(messages)

    # Save assistant message
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=response.content or ""
    )
    db.add(assistant_message)
    await db.commit()

    return ChatResponse(
        session_id=conversation.id,
        message=response.content or "",
        tool_calls=[tc.model_dump() for tc in response.tool_calls] if response.tool_calls else None
    )


@router.post("/stream")
async def stream_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send a message and stream the response"""
    # Load settings and update router
    db_settings = await load_settings_to_router(db)
    current_provider = db_settings.get("llm_provider", "ollama")

    # Get or create conversation
    if request.session_id:
        conversation = await db.get(Conversation, request.session_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(
            system_prompt=request.system_prompt
        )
        db.add(conversation)
        await db.flush()

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    await db.commit()

    # Build message history from DB
    messages = []
    if conversation.system_prompt:
        messages.append(ChatMessage(role="system", content=conversation.system_prompt))

    # Load previous messages (limit to 50 for token budget)
    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .where(Message.role.in_(["user", "assistant"]))
        .order_by(Message.created_at.asc())
        .limit(50)
    )
    for msg in history_result.scalars().all():
        messages.append(ChatMessage(role=msg.role, content=msg.content))

    async def generate():
        try:
            provider = llm_router.get_provider(LLMProvider(current_provider))
        except ValueError:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Invalid LLM provider: {current_provider}'})}\n\n"
            return
        full_response = ""

        try:
            async for chunk in provider.chat_stream(messages):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return

        # Save complete response
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=full_response
        )
        db.add(assistant_message)
        await db.commit()

        yield f"data: {json.dumps({'type': 'done', 'session_id': conversation.id})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.post("/agent")
async def agent_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message through the Agent Orchestrator (SSE stream).
    This is the primary endpoint — uses tool approval system.

    DB session is released before streaming starts to avoid SQLite locks.
    The generator uses its own session for saving results.
    """
    # Load settings and update router
    db_settings = await load_settings_to_router(db)
    current_provider = db_settings.get("llm_provider", "ollama")

    # Get or create conversation
    if request.session_id:
        conversation = await db.get(Conversation, request.session_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(
            system_prompt=request.system_prompt
        )
        db.add(conversation)
        await db.flush()

    # Auto-title from first message
    if not conversation.title:
        conversation.title = request.message[:40] + ("..." if len(request.message) > 40 else "")

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    await db.commit()

    # Build message history from DB
    # NOTE: mistral:7b-instruct breaks tool calling when system/markdown prompt is present.
    # Use plain text memory as initial assistant message to preserve tool calling.
    memory_manager = MemoryManager(db)
    memory_block = await memory_manager.build_memory_prompt(plain=True)

    messages = []

    # Memory context as assistant self-introduction (preserves tool calling)
    if memory_block:
        messages.append(ChatMessage(
            role="assistant",
            content=f"Ich bin Axon, dein KI-Assistent. {memory_block}"
        ))

    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .where(Message.role.in_(["user", "assistant"]))
        .order_by(Message.created_at.asc())
        .limit(50)
    )
    for msg in history_result.scalars().all():
        messages.append(ChatMessage(role=msg.role, content=msg.content))

    session_id = conversation.id

    # Capture data we need, then release the initial DB session
    # The streaming generator will use its own sessions
    await db.close()

    async def on_approval_needed(request_data: dict) -> Optional[PermissionScope]:
        """Callback: pause stream and wait for frontend approval via /tools/approve"""
        approval_id = request_data.get("approval_id")
        if not approval_id:
            return None

        # Create an event to wait on
        event = asyncio.Event()
        result_holder = {"decision": None}
        _approval_events[approval_id] = (event, result_holder)

        try:
            # Wait for approval (timeout 120s)
            await asyncio.wait_for(event.wait(), timeout=120.0)
            decision = result_holder["decision"]
            if decision is None or decision == "never":
                return None
            return PermissionScope(decision)
        except asyncio.TimeoutError:
            return None
        finally:
            _approval_events.pop(approval_id, None)

    async def generate():
        from db.database import async_session

        try:
            provider = llm_router.get_provider(LLMProvider(current_provider))
        except ValueError:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Invalid LLM provider: {current_provider}'})}\n\n"
            return

        # Use a fresh DB session for the streaming phase (audit logging, memory tools)
        async with async_session() as stream_db:
            orchestrator = AgentOrchestrator(
                llm_provider=provider,
                db_session=stream_db
            )

            full_response = ""

            try:
                async for event in orchestrator.process_message(
                    session_id=session_id,
                    messages=messages,
                    on_approval_needed=on_approval_needed
                ):
                    event_type = event.get("type")

                    if event_type == "text":
                        full_response += event.get("content", "")

                    yield f"data: {json.dumps(event)}\n\n"

                    if event_type == "done":
                        break
            except Exception as e:
                logger.error(f"Agent error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

            # Save assistant response with the stream session
            if full_response:
                assistant_message = Message(
                    conversation_id=session_id,
                    role="assistant",
                    content=full_response
                )
                stream_db.add(assistant_message)
                await stream_db.commit()

        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


def resolve_approval(approval_id: str, decision: str) -> bool:
    """Resolve a pending approval (called from tools.py /approve endpoint)"""
    if approval_id not in _approval_events:
        return False
    event, result_holder = _approval_events[approval_id]
    result_holder["decision"] = decision
    event.set()
    return True


@router.post("/approve/{approval_id}")
async def approve_agent_tool(
    approval_id: str,
    decision: str = "once"
):
    """Approve or reject a pending tool request from the agent stream"""
    if decision not in ("once", "session", "never"):
        raise HTTPException(status_code=400, detail="Decision must be: once, session, never")

    if not resolve_approval(approval_id, decision):
        raise HTTPException(status_code=404, detail="Approval not found or expired")

    return {"status": "ok", "approval_id": approval_id, "decision": decision}


@router.get("/conversations")
async def list_conversations(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List recent conversations"""
    from sqlalchemy import select
    result = await db.execute(
        select(Conversation)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
    )
    conversations = result.scalars().all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat()
        }
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a conversation with messages"""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": conversation.id,
        "title": conversation.title,
        "system_prompt": conversation.system_prompt,
        "created_at": conversation.created_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat()
            }
            for m in sorted(conversation.messages, key=lambda x: x.created_at)
        ]
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation"""
    conversation = await db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conversation)
    await db.commit()
    return {"status": "deleted"}
