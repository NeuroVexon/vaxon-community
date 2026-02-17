"""
Axon by NeuroVexon - Agents API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from db.database import get_db
from agent.agent_manager import AgentManager

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentCreate(BaseModel):
    name: str
    description: str = ""
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    allowed_tools: Optional[list[str]] = None
    allowed_skills: Optional[list[str]] = None
    risk_level_max: str = "high"
    auto_approve_tools: Optional[list[str]] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    allowed_tools: Optional[list[str]] = None
    allowed_skills: Optional[list[str]] = None
    risk_level_max: Optional[str] = None
    auto_approve_tools: Optional[list[str]] = None
    enabled: Optional[bool] = None


def _agent_to_dict(agent) -> dict:
    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "system_prompt": agent.system_prompt,
        "model": agent.model,
        "allowed_tools": agent.allowed_tools,
        "allowed_skills": agent.allowed_skills,
        "risk_level_max": agent.risk_level_max,
        "auto_approve_tools": agent.auto_approve_tools,
        "is_default": agent.is_default,
        "enabled": agent.enabled,
        "created_at": agent.created_at.isoformat(),
        "updated_at": agent.updated_at.isoformat(),
    }


@router.get("")
async def list_agents(db: AsyncSession = Depends(get_db)):
    """Alle Agents auflisten"""
    manager = AgentManager(db)
    agents = await manager.list_agents()
    return [_agent_to_dict(a) for a in agents]


@router.get("/{agent_id}")
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Agent Details"""
    manager = AgentManager(db)
    agent = await manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent nicht gefunden")
    return _agent_to_dict(agent)


@router.post("")
async def create_agent(data: AgentCreate, db: AsyncSession = Depends(get_db)):
    """Neuen Agent erstellen"""
    manager = AgentManager(db)
    agent = await manager.create_agent(
        name=data.name,
        description=data.description,
        system_prompt=data.system_prompt,
        model=data.model,
        allowed_tools=data.allowed_tools,
        allowed_skills=data.allowed_skills,
        risk_level_max=data.risk_level_max,
        auto_approve_tools=data.auto_approve_tools,
    )
    return _agent_to_dict(agent)


@router.put("/{agent_id}")
async def update_agent(
    agent_id: str, data: AgentUpdate, db: AsyncSession = Depends(get_db)
):
    """Agent bearbeiten"""
    manager = AgentManager(db)
    updates = data.model_dump(exclude_unset=True)
    agent = await manager.update_agent(agent_id, **updates)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent nicht gefunden")
    return _agent_to_dict(agent)


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Agent loeschen"""
    manager = AgentManager(db)
    deleted = await manager.delete_agent(agent_id)
    if not deleted:
        raise HTTPException(
            status_code=400, detail="Agent nicht gefunden oder ist der Default-Agent"
        )
    return {"status": "deleted"}
