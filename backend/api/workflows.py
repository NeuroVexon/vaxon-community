"""
Axon by NeuroVexon - Workflow API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from db.database import get_db
from db.models import Workflow, WorkflowRun, User
from core.dependencies import get_current_active_user
from agent.workflows import WorkflowEngine, workflow_to_dict, run_to_dict

router = APIRouter(prefix="/workflows", tags=["workflows"])

MAX_WORKFLOWS = 50


class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_phrase: Optional[str] = None
    agent_id: Optional[str] = None
    steps: list[dict]  # [{order, prompt, store_as}]
    approval_mode: str = "each_step"


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_phrase: Optional[str] = None
    agent_id: Optional[str] = None
    steps: Optional[list[dict]] = None
    approval_mode: Optional[str] = None
    enabled: Optional[bool] = None


@router.get("")
async def list_workflows(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Alle Workflows auflisten"""
    result = await db.execute(select(Workflow).order_by(Workflow.created_at.desc()))
    workflows = result.scalars().all()
    return [workflow_to_dict(wf) for wf in workflows]


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Workflow Details"""
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow nicht gefunden")
    return workflow_to_dict(wf)


@router.post("")
async def create_workflow(
    data: WorkflowCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Neuen Workflow erstellen"""
    # Safety: Max Workflows
    result = await db.execute(select(Workflow))
    count = len(result.scalars().all())
    if count >= MAX_WORKFLOWS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximale Anzahl Workflows erreicht ({MAX_WORKFLOWS})",
        )

    if not data.steps:
        raise HTTPException(
            status_code=400, detail="Workflow muss mindestens einen Step haben"
        )

    if data.approval_mode not in ("each_step", "once_at_start", "never"):
        raise HTTPException(status_code=400, detail="Ungueltiger approval_mode")

    wf = Workflow(
        name=data.name,
        description=data.description,
        trigger_phrase=data.trigger_phrase,
        agent_id=data.agent_id,
        steps=data.steps,
        approval_mode=data.approval_mode,
    )
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return workflow_to_dict(wf)


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    data: WorkflowUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Workflow aktualisieren"""
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow nicht gefunden")

    updates = data.model_dump(exclude_unset=True)
    if "approval_mode" in updates and updates["approval_mode"] not in (
        "each_step",
        "once_at_start",
        "never",
    ):
        raise HTTPException(status_code=400, detail="Ungueltiger approval_mode")

    for key, value in updates.items():
        setattr(wf, key, value)

    await db.commit()
    await db.refresh(wf)
    return workflow_to_dict(wf)


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Workflow loeschen"""
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow nicht gefunden")

    await db.delete(wf)
    await db.commit()
    return {"status": "deleted"}


@router.post("/{workflow_id}/run")
async def run_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Workflow manuell ausfuehren"""
    wf = await db.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow nicht gefunden")

    engine = WorkflowEngine(db)
    run = await engine.execute_workflow(workflow_id)
    return run_to_dict(run)


@router.get("/{workflow_id}/history")
async def workflow_history(
    workflow_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Workflow-Ausfuehrungshistorie"""
    result = await db.execute(
        select(WorkflowRun)
        .where(WorkflowRun.workflow_id == workflow_id)
        .order_by(WorkflowRun.started_at.desc())
        .limit(20)
    )
    runs = result.scalars().all()
    return [run_to_dict(r) for r in runs]
