"""
Axon by NeuroVexon - Dashboard & Analytics API
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from db.database import get_db
from db.models import (
    Conversation, Message, AuditLog, Agent, ScheduledTask,
    Workflow, Skill
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def get_overview(db: AsyncSession = Depends(get_db)):
    """Dashboard-Uebersicht: Kernmetriken"""
    # Conversations
    conv_count = await db.scalar(select(func.count(Conversation.id)))

    # Messages
    msg_count = await db.scalar(select(func.count(Message.id)))

    # Agents
    agent_count = await db.scalar(
        select(func.count(Agent.id)).where(Agent.enabled)
    )

    # Tool Calls (aus Audit)
    tool_calls = await db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.event_type == "tool_executed"
        )
    )

    # Approval Rate
    total_requests = await db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.event_type == "tool_requested"
        )
    )
    approved = await db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.event_type == "tool_approved"
        )
    )
    approval_rate = (approved / total_requests * 100) if total_requests > 0 else 0

    # Scheduled Tasks
    active_tasks = await db.scalar(
        select(func.count(ScheduledTask.id)).where(ScheduledTask.enabled)
    )

    # Workflows
    workflow_count = await db.scalar(
        select(func.count(Workflow.id)).where(Workflow.enabled)
    )

    # Skills
    active_skills = await db.scalar(
        select(func.count(Skill.id)).where(Skill.enabled, Skill.approved)
    )

    return {
        "conversations": conv_count or 0,
        "messages": msg_count or 0,
        "agents": agent_count or 0,
        "tool_calls": tool_calls or 0,
        "approval_rate": round(approval_rate, 1),
        "active_tasks": active_tasks or 0,
        "workflows": workflow_count or 0,
        "active_skills": active_skills or 0,
    }


@router.get("/tools")
async def get_tool_stats(db: AsyncSession = Depends(get_db)):
    """Tool-Statistiken: Nutzung, Fehlerrate, Ausfuehrungszeit"""
    # Meistgenutzte Tools
    result = await db.execute(
        select(
            AuditLog.tool_name,
            func.count(AuditLog.id).label("count"),
            func.avg(AuditLog.execution_time_ms).label("avg_time"),
        )
        .where(
            AuditLog.event_type == "tool_executed",
            AuditLog.tool_name.isnot(None)
        )
        .group_by(AuditLog.tool_name)
        .order_by(func.count(AuditLog.id).desc())
        .limit(20)
    )
    tool_usage = [
        {
            "tool": row.tool_name,
            "count": row.count,
            "avg_time_ms": round(row.avg_time, 1) if row.avg_time else 0,
        }
        for row in result
    ]

    # Fehlerrate pro Tool
    result = await db.execute(
        select(
            AuditLog.tool_name,
            func.count(AuditLog.id).label("failures"),
        )
        .where(
            AuditLog.event_type == "tool_failed",
            AuditLog.tool_name.isnot(None)
        )
        .group_by(AuditLog.tool_name)
    )
    failures = {row.tool_name: row.failures for row in result}

    # Merge
    for tool in tool_usage:
        tool["failures"] = failures.get(tool["tool"], 0)
        total = tool["count"] + tool["failures"]
        tool["error_rate"] = round(tool["failures"] / total * 100, 1) if total > 0 else 0

    return {"tools": tool_usage}


@router.get("/timeline")
async def get_timeline(days: int = 30, db: AsyncSession = Depends(get_db)):
    """30-Tage Verlauf: Conversations und Tool-Calls pro Tag"""
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Conversations pro Tag
    result = await db.execute(
        select(
            func.date(Conversation.created_at).label("day"),
            func.count(Conversation.id).label("count"),
        )
        .where(Conversation.created_at >= cutoff)
        .group_by(func.date(Conversation.created_at))
        .order_by(func.date(Conversation.created_at))
    )
    conv_by_day = {str(row.day): row.count for row in result}

    # Tool-Calls pro Tag
    result = await db.execute(
        select(
            func.date(AuditLog.timestamp).label("day"),
            func.count(AuditLog.id).label("count"),
        )
        .where(
            AuditLog.timestamp >= cutoff,
            AuditLog.event_type == "tool_executed"
        )
        .group_by(func.date(AuditLog.timestamp))
        .order_by(func.date(AuditLog.timestamp))
    )
    tools_by_day = {str(row.day): row.count for row in result}

    # Alle Tage im Zeitraum
    timeline = []
    for i in range(days):
        day = (datetime.utcnow() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        timeline.append({
            "date": day,
            "conversations": conv_by_day.get(day, 0),
            "tool_calls": tools_by_day.get(day, 0),
        })

    return {"timeline": timeline}


@router.get("/agents")
async def get_agent_stats(db: AsyncSession = Depends(get_db)):
    """Agent-Statistiken"""
    result = await db.execute(
        select(Agent).where(Agent.enabled).order_by(Agent.is_default.desc())
    )
    agents = result.scalars().all()

    agent_stats = []
    for agent in agents:
        agent_stats.append({
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "is_default": agent.is_default,
            "tools_count": len(agent.allowed_tools) if agent.allowed_tools else "alle",
            "auto_approve_count": len(agent.auto_approve_tools) if agent.auto_approve_tools else 0,
            "risk_level_max": agent.risk_level_max,
        })

    return {"agents": agent_stats}


@router.get("/tasks")
async def get_task_overview(db: AsyncSession = Depends(get_db)):
    """Scheduled Tasks Uebersicht"""
    result = await db.execute(
        select(ScheduledTask).order_by(ScheduledTask.enabled.desc(), ScheduledTask.name)
    )
    tasks = result.scalars().all()

    return {
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "cron": t.cron_expression,
                "enabled": t.enabled,
                "last_run": t.last_run.isoformat() if t.last_run else None,
                "last_result_status": (
                    "success" if t.last_result and not t.last_result.startswith("Fehler") and not t.last_result.startswith("Timeout")
                    else "error" if t.last_result else "pending"
                ),
            }
            for t in tasks
        ]
    }
