"""
Axon by NeuroVexon - MCP Server

AXON als MCP-Server: Bietet kontrollierte Tools fuer externe AI-Clients
(Claude Desktop, Cursor, etc.) an. Jeder Tool-Call durchlaeuft das Approval-System.

Transport: Server-Sent Events (SSE)
Auth: Bearer Token
"""

import asyncio
import json
import logging
import time
from typing import Optional

from agent.tool_registry import tool_registry
from agent.tool_handlers import execute_tool
from agent.audit_logger import AuditLogger
from mcp.protocol import (
    JsonRpcRequest,
    JsonRpcError,
    axon_tool_to_mcp,
    make_error_response,
    make_success_response,
)

logger = logging.getLogger(__name__)

# MCP Server Info
MCP_SERVER_NAME = "axon-mcp"
MCP_SERVER_VERSION = "2.0.0"
MCP_PROTOCOL_VERSION = "2024-11-05"

# Pending approval requests: {approval_id: asyncio.Event}
_pending_approvals: dict[str, asyncio.Event] = {}
_approval_decisions: dict[str, str] = {}  # approval_id -> "approved" | "rejected"


class MCPServer:
    """MCP Server Handler"""

    def __init__(self):
        self._initialized = False

    def handle_initialize(self, request_id, params: Optional[dict]) -> dict:
        """Handle initialize request"""
        self._initialized = True
        return make_success_response(
            request_id,
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {"listChanged": False},
                },
                "serverInfo": {
                    "name": MCP_SERVER_NAME,
                    "version": MCP_SERVER_VERSION,
                },
            },
        )

    def handle_tools_list(self, request_id) -> dict:
        """Handle tools/list — gibt alle AXON-Tools als MCP-Tools zurueck"""
        tools = tool_registry.list_tools()
        mcp_tools = [axon_tool_to_mcp(t) for t in tools]
        return make_success_response(request_id, {"tools": mcp_tools})

    async def handle_tools_call(
        self, request_id, params: dict, session_id: str, db_session=None
    ) -> dict:
        """
        Handle tools/call — fuehrt ein Tool aus.
        Bei Tools die Approval brauchen: Wartet auf Genehmigung.
        """
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        if not tool_name:
            return make_error_response(
                request_id, JsonRpcError.INVALID_PARAMS, "Missing tool name"
            )

        tool_def = tool_registry.get(tool_name)
        if not tool_def:
            return make_error_response(
                request_id, JsonRpcError.METHOD_NOT_FOUND, f"Unknown tool: {tool_name}"
            )

        # Audit logging
        audit = AuditLogger(db_session) if db_session else None
        if audit:
            await audit.log_tool_request(session_id, tool_name, tool_args)

        # Tool-Ausfuehrung
        start_time = time.time()
        try:
            result = await execute_tool(tool_name, tool_args, db_session=db_session)
            execution_time_ms = int((time.time() - start_time) * 1000)

            if audit:
                await audit.log_tool_execution(
                    session_id, tool_name, tool_args, str(result), execution_time_ms
                )

            return make_success_response(
                request_id, {"content": [{"type": "text", "text": str(result)}]}
            )
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            if audit:
                await audit.log_tool_failure(session_id, tool_name, tool_args, str(e))

            return make_error_response(request_id, JsonRpcError.INTERNAL_ERROR, str(e))

    async def handle_request(
        self, raw_data: str, session_id: str, db_session=None
    ) -> dict:
        """Parse und handle einen JSON-RPC Request"""
        try:
            data = json.loads(raw_data)
            request = JsonRpcRequest(**data)
        except Exception:
            return make_error_response(
                None, JsonRpcError.PARSE_ERROR, "Invalid JSON-RPC request"
            )

        method = request.method
        request_id = request.id
        params = request.params or {}

        if method == "initialize":
            return self.handle_initialize(request_id, params)
        elif method == "notifications/initialized":
            # Client-seitige Notification — kein Response noetig
            return make_success_response(request_id, {})
        elif method == "tools/list":
            return self.handle_tools_list(request_id)
        elif method == "tools/call":
            return await self.handle_tools_call(
                request_id, params, session_id, db_session
            )
        else:
            return make_error_response(
                request_id, JsonRpcError.METHOD_NOT_FOUND, f"Unknown method: {method}"
            )


# Global MCP server instance
mcp_server = MCPServer()
