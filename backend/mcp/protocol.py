"""
Axon by NeuroVexon - MCP Protocol (JSON-RPC 2.0)

Nachrichtenformat fuer das Model Context Protocol.
Konvertiert AXON-Tools in MCP-Tool-Schema und zurueck.
"""

from typing import Any, Optional
from pydantic import BaseModel


class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 Request"""

    jsonrpc: str = "2.0"
    id: Optional[int | str] = None
    method: str
    params: Optional[dict[str, Any]] = None


class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 Response"""

    jsonrpc: str = "2.0"
    id: Optional[int | str] = None
    result: Optional[Any] = None
    error: Optional[dict[str, Any]] = None


class JsonRpcError:
    """Standard JSON-RPC error codes"""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


def axon_tool_to_mcp(tool_def) -> dict:
    """Konvertiert ein AXON ToolDefinition in MCP-Tool-Format"""
    properties = {}
    required = []

    for param_name, param_info in tool_def.parameters.items():
        prop = {
            "type": param_info.get("type", "string"),
            "description": param_info.get("description", ""),
        }
        if "default" in param_info:
            prop["default"] = param_info["default"]
        properties[param_name] = prop

        if param_info.get("required", False):
            required.append(param_name)

    return {
        "name": tool_def.name,
        "description": tool_def.description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


def make_error_response(
    request_id: Optional[int | str], code: int, message: str
) -> dict:
    """Erstellt eine JSON-RPC Error-Response"""
    return JsonRpcResponse(
        id=request_id, error={"code": code, "message": message}
    ).model_dump()


def make_success_response(request_id: Optional[int | str], result: Any) -> dict:
    """Erstellt eine JSON-RPC Success-Response"""
    return JsonRpcResponse(id=request_id, result=result).model_dump()
