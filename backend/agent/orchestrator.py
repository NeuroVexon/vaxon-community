"""
Axon by NeuroVexon - Agent Orchestrator

Koordiniert LLM, Tools und Permissions.
"""

from typing import AsyncGenerator, Optional, Callable, Awaitable
import asyncio
import time
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from .tool_registry import ToolRegistry, tool_registry, RiskLevel
from .permission_manager import PermissionManager, permission_manager, PermissionScope
from .audit_logger import AuditLogger, AuditEventType
from .tool_handlers import execute_tool, ToolExecutionError
from llm.provider import BaseLLMProvider, ChatMessage, LLMResponse

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates the agent loop:
    1. User sends message
    2. LLM responds (possibly with tool calls)
    3. Tool calls require user approval
    4. Tools are executed and results fed back to LLM
    5. Repeat until LLM gives final response
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        db_session: AsyncSession,
        tools: Optional[ToolRegistry] = None,
        permissions: Optional[PermissionManager] = None
    ):
        self.llm = llm_provider
        self.tools = tools or tool_registry
        self.permissions = permissions or permission_manager
        self.audit = AuditLogger(db_session)

    async def process_message(
        self,
        session_id: str,
        messages: list[ChatMessage],
        on_approval_needed: Callable[[dict], Awaitable[Optional[PermissionScope]]],
        max_tool_iterations: int = 10
    ) -> AsyncGenerator[dict, None]:
        """
        Process a message with tool support.

        Args:
            session_id: The conversation session ID
            messages: Chat history including the new user message
            on_approval_needed: Async callback when tool approval is needed.
                                Returns PermissionScope or None for rejection.
            max_tool_iterations: Maximum number of tool call iterations

        Yields:
            Dicts with type: 'text', 'tool_request', 'tool_result', 'done'
        """

        iteration = 0

        while iteration < max_tool_iterations:
            iteration += 1

            # Call LLM with tools
            response = await self.llm.chat(
                messages=messages,
                tools=self.tools.get_tools_for_llm()
            )

            # If no tool calls, we're done
            if not response.tool_calls:
                if response.content:
                    yield {"type": "text", "content": response.content}
                yield {"type": "done"}
                return

            # Process each tool call
            for tool_call in response.tool_calls:
                tool_name = tool_call.name
                tool_params = tool_call.parameters

                # Get tool definition
                tool_def = self.tools.get(tool_name)
                if not tool_def:
                    yield {
                        "type": "tool_error",
                        "tool": tool_name,
                        "error": f"Unknown tool: {tool_name}"
                    }
                    continue

                # Log the request
                await self.audit.log_tool_request(
                    session_id, tool_name, tool_params
                )

                # Yield tool request to UI
                yield {
                    "type": "tool_request",
                    "tool": tool_name,
                    "params": tool_params,
                    "description": tool_def.description_de,
                    "risk_level": tool_def.risk_level.value
                }

                # Check existing permission
                has_permission = self.permissions.check_permission(
                    session_id, tool_name, tool_params
                )

                if not has_permission:
                    # Check if blocked
                    if self.permissions.is_blocked(tool_name, tool_params):
                        await self.audit.log_tool_rejection(
                            session_id, tool_name, tool_params, "blocked"
                        )
                        yield {
                            "type": "tool_blocked",
                            "tool": tool_name,
                            "message": "Tool wurde vom Benutzer blockiert"
                        }
                        # Add to messages so LLM knows
                        messages.append(ChatMessage(
                            role="assistant",
                            content=f"Tool {tool_name} wurde blockiert."
                        ))
                        continue

                    # Request approval
                    decision = await on_approval_needed({
                        "tool": tool_name,
                        "params": tool_params,
                        "description": tool_def.description_de,
                        "risk_level": tool_def.risk_level.value
                    })

                    if decision is None:
                        # Rejected
                        await self.audit.log_tool_rejection(
                            session_id, tool_name, tool_params, "rejected"
                        )
                        yield {
                            "type": "tool_rejected",
                            "tool": tool_name
                        }
                        messages.append(ChatMessage(
                            role="assistant",
                            content=f"Benutzer hat {tool_name} abgelehnt."
                        ))
                        continue

                    # Grant permission
                    self.permissions.grant_permission(
                        session_id, tool_name, tool_params, decision
                    )
                    await self.audit.log_tool_approval(
                        session_id, tool_name, tool_params, decision.value
                    )

                # Execute the tool
                start_time = time.time()
                try:
                    result = await execute_tool(tool_name, tool_params)
                    execution_time_ms = int((time.time() - start_time) * 1000)

                    await self.audit.log_tool_execution(
                        session_id, tool_name, tool_params,
                        str(result), execution_time_ms
                    )

                    yield {
                        "type": "tool_result",
                        "tool": tool_name,
                        "result": result,
                        "execution_time_ms": execution_time_ms
                    }

                    # Add result to messages for next LLM call
                    messages.append(ChatMessage(
                        role="assistant",
                        content=f"Tool {tool_name} executed. Result: {str(result)[:500]}"
                    ))

                except ToolExecutionError as e:
                    await self.audit.log_tool_failure(
                        session_id, tool_name, tool_params, str(e)
                    )
                    yield {
                        "type": "tool_error",
                        "tool": tool_name,
                        "error": str(e)
                    }
                    messages.append(ChatMessage(
                        role="assistant",
                        content=f"Tool {tool_name} failed: {str(e)}"
                    ))

                except Exception as e:
                    logger.exception(f"Unexpected error executing {tool_name}")
                    await self.audit.log_tool_failure(
                        session_id, tool_name, tool_params, str(e)
                    )
                    yield {
                        "type": "tool_error",
                        "tool": tool_name,
                        "error": f"Unexpected error: {str(e)}"
                    }

            # If we had partial text response, yield it
            if response.content:
                yield {"type": "text", "content": response.content}

        # Max iterations reached
        yield {
            "type": "warning",
            "message": "Maximum tool iterations reached"
        }
        yield {"type": "done"}
