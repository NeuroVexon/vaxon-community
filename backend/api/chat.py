"""
Axon by NeuroVexon - Chat API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import json
import logging

from db.database import get_db
from db.models import Conversation, Message
from llm.router import llm_router
from llm.provider import ChatMessage
from agent.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


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

    # Build message history
    messages = []
    if conversation.system_prompt:
        messages.append(ChatMessage(role="system", content=conversation.system_prompt))
    messages.append(ChatMessage(role="user", content=request.message))

    # Get LLM response
    provider = llm_router.get_provider()
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

    # Build message history
    messages = []
    if conversation.system_prompt:
        messages.append(ChatMessage(role="system", content=conversation.system_prompt))
    messages.append(ChatMessage(role="user", content=request.message))

    async def generate():
        provider = llm_router.get_provider()
        full_response = ""

        async for chunk in provider.chat_stream(messages):
            full_response += chunk
            yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"

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
