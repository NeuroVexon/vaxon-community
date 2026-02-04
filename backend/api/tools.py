"""
Axon by NeuroVexon - Tools API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from db.database import get_db
from agent.tool_registry import tool_registry, RiskLevel
from agent.permission_manager import permission_manager, PermissionScope
from agent.audit_logger import AuditLogger, AuditEventType

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolApprovalRequest(BaseModel):
    session_id: str
    tool: str
    params: dict
    decision: str  # once, session, never


class ToolInfo(BaseModel):
    name: str
    description: str
    description_de: str
    risk_level: str
    parameters: dict


@router.get("")
async def list_tools():
    """List all available tools"""
    tools = tool_registry.list_tools()
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "description_de": tool.description_de,
            "risk_level": tool.risk_level.value,
            "parameters": tool.parameters,
            "requires_approval": tool.requires_approval
        }
        for tool in tools
    ]


@router.get("/{tool_name}")
async def get_tool(tool_name: str):
    """Get details for a specific tool"""
    tool = tool_registry.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    return {
        "name": tool.name,
        "description": tool.description,
        "description_de": tool.description_de,
        "risk_level": tool.risk_level.value,
        "parameters": tool.parameters,
        "requires_approval": tool.requires_approval
    }


@router.post("/approve")
async def approve_tool(
    request: ToolApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """Approve or reject a tool execution"""
    # Validate tool exists
    tool = tool_registry.get(request.tool)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {request.tool}")

    # Validate decision
    try:
        scope = PermissionScope(request.decision)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision: {request.decision}. Must be: once, session, never"
        )

    # Grant or block permission
    permission_manager.grant_permission(
        session_id=request.session_id,
        tool=request.tool,
        params=request.params,
        scope=scope
    )

    # Log the decision
    audit = AuditLogger(db)
    if scope == PermissionScope.NEVER:
        await audit.log_tool_rejection(
            request.session_id,
            request.tool,
            request.params,
            "blocked"
        )
    else:
        await audit.log_tool_approval(
            request.session_id,
            request.tool,
            request.params,
            scope.value
        )

    await db.commit()

    return {
        "status": "ok",
        "tool": request.tool,
        "decision": request.decision
    }


@router.post("/revoke")
async def revoke_permission(
    session_id: str,
    tool: str,
    db: AsyncSession = Depends(get_db)
):
    """Revoke a tool permission"""
    permission_manager.revoke_permission(session_id, tool)

    audit = AuditLogger(db)
    await audit.log(
        session_id=session_id,
        event_type=AuditEventType.PERMISSION_REVOKED,
        tool_name=tool
    )
    await db.commit()

    return {"status": "revoked", "tool": tool}


@router.post("/unblock")
async def unblock_tool(
    tool: str,
    params: Optional[dict] = None
):
    """Remove a tool from the blocklist"""
    permission_manager.unblock(tool, params)
    return {"status": "unblocked", "tool": tool}


@router.get("/permissions/{session_id}")
async def get_session_permissions(session_id: str):
    """Get all permissions for a session (debug)"""
    permissions = permission_manager.get_session_permissions(session_id)
    return {
        "session_id": session_id,
        "permissions": permissions
    }
