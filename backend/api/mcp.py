"""
Axon by NeuroVexon - MCP Server API Endpoint

SSE-Transport fuer das Model Context Protocol.
Ermoeglicht externen AI-Clients (Claude Desktop, Cursor) AXON-Tools zu nutzen.
"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from mcp.server import mcp_server
from core.security import rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])

# MCP Auth Token (aus DB Settings laden)
MCP_ENABLED_KEY = "mcp_enabled"
MCP_AUTH_TOKEN_KEY = "mcp_auth_token"


async def _get_mcp_settings(db: AsyncSession) -> dict:
    """MCP-Einstellungen aus DB laden"""
    from sqlalchemy import select
    from db.models import Settings
    from core.security import decrypt_value

    result = await db.execute(select(Settings))
    db_settings = {s.key: s.value for s in result.scalars().all()}
    return {
        "enabled": db_settings.get(MCP_ENABLED_KEY, "false") == "true",
        "auth_token": decrypt_value(db_settings.get(MCP_AUTH_TOKEN_KEY, "")) if db_settings.get(MCP_AUTH_TOKEN_KEY) else "",
    }


def _validate_auth(request: Request, mcp_settings: dict) -> bool:
    """Bearer Token validieren"""
    token = mcp_settings.get("auth_token", "")
    if not token:
        return True  # Kein Token konfiguriert = offen (fuer lokale Nutzung)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False
    return auth_header[7:] == token


@router.get("/v1/sse")
async def mcp_sse_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    """
    MCP SSE Endpoint — Hauptendpoint fuer externe AI-Clients.

    Clients senden JSON-RPC Requests, Server antwortet via SSE.
    """
    mcp_settings = await _get_mcp_settings(db)

    if not mcp_settings["enabled"]:
        raise HTTPException(status_code=403, detail="MCP Server ist deaktiviert")

    if not _validate_auth(request, mcp_settings):
        raise HTTPException(status_code=401, detail="Ungueliger Auth-Token")

    # Rate Limiting
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(f"mcp:{client_ip}"):
        raise HTTPException(status_code=429, detail="Rate Limit erreicht")

    session_id = f"mcp-{uuid.uuid4().hex[:12]}"

    async def event_stream():
        # Send endpoint info
        yield f"event: endpoint\ndata: /mcp/v1/messages?session_id={session_id}\n\n"

        # Keep connection alive
        try:
            while True:
                if await request.is_disconnected():
                    break
                yield ": keepalive\n\n"
                import asyncio
                await asyncio.sleep(15)
        except Exception:
            pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/v1/messages")
async def mcp_messages_endpoint(
    request: Request,
    session_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    MCP Messages Endpoint — empfaengt JSON-RPC Requests.
    """
    mcp_settings = await _get_mcp_settings(db)

    if not mcp_settings["enabled"]:
        raise HTTPException(status_code=403, detail="MCP Server ist deaktiviert")

    if not _validate_auth(request, mcp_settings):
        raise HTTPException(status_code=401, detail="Ungueliger Auth-Token")

    # Rate Limiting
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(f"mcp:{client_ip}"):
        raise HTTPException(status_code=429, detail="Rate Limit erreicht")

    body = await request.body()
    raw_data = body.decode("utf-8")

    sid = session_id or f"mcp-{uuid.uuid4().hex[:12]}"
    response = await mcp_server.handle_request(raw_data, sid, db_session=db)
    await db.commit()

    return response


@router.get("/v1/info")
async def mcp_info():
    """MCP Server Info"""
    from mcp.server import MCP_SERVER_NAME, MCP_SERVER_VERSION, MCP_PROTOCOL_VERSION
    from agent.tool_registry import tool_registry

    return {
        "name": MCP_SERVER_NAME,
        "version": MCP_SERVER_VERSION,
        "protocol_version": MCP_PROTOCOL_VERSION,
        "tools_count": len(tool_registry.list_tools()),
    }
