"""
Axon by NeuroVexon - Audit API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import csv
import io

from db.database import get_db
from db.models import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def list_audit_logs(
    session_id: Optional[str] = None,
    event_type: Optional[str] = None,
    tool_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List audit logs with optional filters"""
    query = select(AuditLog).order_by(AuditLog.timestamp.desc())

    if session_id:
        query = query.where(AuditLog.conversation_id == session_id)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    if tool_name:
        query = query.where(AuditLog.tool_name == tool_name)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        {
            "id": log.id,
            "session_id": log.conversation_id,
            "timestamp": log.timestamp.isoformat(),
            "event_type": log.event_type,
            "tool_name": log.tool_name,
            "tool_params": log.tool_params,
            "result": log.result[:200] if log.result else None,  # Truncate
            "error": log.error,
            "user_decision": log.user_decision,
            "execution_time_ms": log.execution_time_ms
        }
        for log in logs
    ]


@router.get("/stats")
async def get_audit_stats(
    session_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get audit statistics"""
    from sqlalchemy import func

    base_query = select(AuditLog)
    if session_id:
        base_query = base_query.where(AuditLog.conversation_id == session_id)

    # Total count
    total_result = await db.execute(
        select(func.count(AuditLog.id)).select_from(AuditLog)
    )
    total = total_result.scalar()

    # Count by event type
    type_result = await db.execute(
        select(AuditLog.event_type, func.count(AuditLog.id))
        .group_by(AuditLog.event_type)
    )
    by_type = {row[0]: row[1] for row in type_result}

    # Count by tool
    tool_result = await db.execute(
        select(AuditLog.tool_name, func.count(AuditLog.id))
        .where(AuditLog.tool_name.isnot(None))
        .group_by(AuditLog.tool_name)
    )
    by_tool = {row[0]: row[1] for row in tool_result}

    # Average execution time
    time_result = await db.execute(
        select(func.avg(AuditLog.execution_time_ms))
        .where(AuditLog.execution_time_ms.isnot(None))
    )
    avg_time = time_result.scalar()

    return {
        "total": total,
        "by_event_type": by_type,
        "by_tool": by_tool,
        "avg_execution_time_ms": round(avg_time, 2) if avg_time else None
    }


@router.get("/export")
async def export_audit_logs(
    format: str = "csv",
    session_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Export audit logs as CSV or JSON"""
    query = select(AuditLog).order_by(AuditLog.timestamp.desc())
    if session_id:
        query = query.where(AuditLog.conversation_id == session_id)

    result = await db.execute(query)
    logs = result.scalars().all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "session_id", "timestamp", "event_type",
            "tool_name", "tool_params", "result", "error",
            "user_decision", "execution_time_ms"
        ])
        for log in logs:
            writer.writerow([
                log.id,
                log.conversation_id,
                log.timestamp.isoformat(),
                log.event_type,
                log.tool_name,
                str(log.tool_params) if log.tool_params else "",
                log.result[:500] if log.result else "",
                log.error or "",
                log.user_decision or "",
                log.execution_time_ms or ""
            ])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=axon_audit_log.csv"}
        )
    else:
        return [
            {
                "id": log.id,
                "session_id": log.conversation_id,
                "timestamp": log.timestamp.isoformat(),
                "event_type": log.event_type,
                "tool_name": log.tool_name,
                "tool_params": log.tool_params,
                "result": log.result,
                "error": log.error,
                "user_decision": log.user_decision,
                "execution_time_ms": log.execution_time_ms
            }
            for log in logs
        ]
