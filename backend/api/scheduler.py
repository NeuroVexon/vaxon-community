"""
Axon by NeuroVexon - Scheduled Tasks API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from db.database import get_db
from db.models import ScheduledTask
from agent.scheduler import task_scheduler, MAX_ACTIVE_TASKS

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    name: str
    cron_expression: str
    prompt: str
    agent_id: Optional[str] = None
    approval_required: bool = True
    notification_channel: str = "web"
    max_retries: int = 1


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    cron_expression: Optional[str] = None
    prompt: Optional[str] = None
    agent_id: Optional[str] = None
    approval_required: Optional[bool] = None
    notification_channel: Optional[str] = None
    max_retries: Optional[int] = None
    enabled: Optional[bool] = None


def _task_to_dict(task: ScheduledTask) -> dict:
    return {
        "id": task.id,
        "name": task.name,
        "cron_expression": task.cron_expression,
        "agent_id": task.agent_id,
        "prompt": task.prompt,
        "approval_required": task.approval_required,
        "notification_channel": task.notification_channel,
        "max_retries": task.max_retries,
        "last_run": task.last_run.isoformat() if task.last_run else None,
        "last_result": task.last_result,
        "next_run": task.next_run.isoformat() if task.next_run else None,
        "enabled": task.enabled,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


def _validate_cron(expression: str) -> bool:
    """Cron-Ausdruck validieren"""
    try:
        from apscheduler.triggers.cron import CronTrigger

        CronTrigger.from_crontab(expression)
        return True
    except Exception:
        return False


@router.get("")
async def list_tasks(db: AsyncSession = Depends(get_db)):
    """Alle geplanten Tasks auflisten"""
    result = await db.execute(
        select(ScheduledTask).order_by(ScheduledTask.created_at.desc())
    )
    tasks = result.scalars().all()
    return [_task_to_dict(t) for t in tasks]


@router.get("/{task_id}")
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Task Details"""
    task = await db.get(ScheduledTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task nicht gefunden")
    return _task_to_dict(task)


@router.post("")
async def create_task(data: TaskCreate, db: AsyncSession = Depends(get_db)):
    """Neuen Task erstellen"""
    # Safety: Max Tasks
    result = await db.execute(select(ScheduledTask).where(ScheduledTask.enabled))
    active_count = len(result.scalars().all())
    if active_count >= MAX_ACTIVE_TASKS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximale Anzahl aktiver Tasks erreicht ({MAX_ACTIVE_TASKS})",
        )

    # Validate cron
    if not _validate_cron(data.cron_expression):
        raise HTTPException(status_code=400, detail="Ungueltiger Cron-Ausdruck")

    task = ScheduledTask(
        name=data.name,
        cron_expression=data.cron_expression,
        prompt=data.prompt,
        agent_id=data.agent_id,
        approval_required=data.approval_required,
        notification_channel=data.notification_channel,
        max_retries=data.max_retries,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Sync scheduler
    await task_scheduler.sync_tasks()

    return _task_to_dict(task)


@router.put("/{task_id}")
async def update_task(
    task_id: str, data: TaskUpdate, db: AsyncSession = Depends(get_db)
):
    """Task aktualisieren"""
    task = await db.get(ScheduledTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task nicht gefunden")

    updates = data.model_dump(exclude_unset=True)

    # Validate cron if changed
    if "cron_expression" in updates and not _validate_cron(updates["cron_expression"]):
        raise HTTPException(status_code=400, detail="Ungueltiger Cron-Ausdruck")

    for key, value in updates.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)

    # Sync scheduler
    await task_scheduler.sync_tasks()

    return _task_to_dict(task)


@router.delete("/{task_id}")
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Task loeschen"""
    task = await db.get(ScheduledTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task nicht gefunden")

    await db.delete(task)
    await db.commit()

    # Sync scheduler
    await task_scheduler.sync_tasks()

    return {"status": "deleted"}


@router.post("/{task_id}/run")
async def run_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Task sofort manuell ausfuehren"""
    task = await db.get(ScheduledTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task nicht gefunden")

    result = await task_scheduler.run_task_now(task_id)

    # Reload task to get updated last_run/last_result
    await db.refresh(task)

    return {"status": "executed", "result": result, "task": _task_to_dict(task)}


@router.post("/{task_id}/toggle")
async def toggle_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Task aktivieren/deaktivieren"""
    task = await db.get(ScheduledTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task nicht gefunden")

    task.enabled = not task.enabled
    await db.commit()
    await db.refresh(task)

    # Sync scheduler
    await task_scheduler.sync_tasks()

    return _task_to_dict(task)
