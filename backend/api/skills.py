"""
Axon by NeuroVexon - Skills API Endpoints

CRUD + Approval für das Skills-System.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from db.database import get_db
from db.models import Skill
from agent.skill_loader import SkillLoader, compute_file_hash

router = APIRouter(prefix="/skills", tags=["skills"])


class SkillApproval(BaseModel):
    approved: bool


class SkillToggle(BaseModel):
    enabled: bool


@router.get("")
async def list_skills(db: AsyncSession = Depends(get_db)):
    """Alle Skills auflisten (inkl. Scan nach neuen)"""
    loader = SkillLoader(db)
    await loader.scan_skills_dir()
    await db.commit()

    result = await db.execute(select(Skill).order_by(Skill.name))
    skills = result.scalars().all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "display_name": s.display_name,
            "description": s.description,
            "version": s.version,
            "author": s.author,
            "enabled": s.enabled,
            "approved": s.approved,
            "risk_level": s.risk_level,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        }
        for s in skills
    ]


@router.get("/{skill_id}")
async def get_skill(skill_id: str, db: AsyncSession = Depends(get_db)):
    """Einzelnen Skill abrufen"""
    skill = await db.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill nicht gefunden")

    return {
        "id": skill.id,
        "name": skill.name,
        "display_name": skill.display_name,
        "description": skill.description,
        "file_path": skill.file_path,
        "file_hash": skill.file_hash,
        "version": skill.version,
        "author": skill.author,
        "enabled": skill.enabled,
        "approved": skill.approved,
        "risk_level": skill.risk_level,
        "created_at": skill.created_at.isoformat(),
        "updated_at": skill.updated_at.isoformat(),
    }


@router.post("/{skill_id}/approve")
async def approve_skill(
    skill_id: str, data: SkillApproval, db: AsyncSession = Depends(get_db)
):
    """Skill genehmigen oder Genehmigung widerrufen"""
    skill = await db.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill nicht gefunden")

    # Bei Approval: Hash nochmal prüfen
    if data.approved:
        try:
            current_hash = compute_file_hash(skill.file_path)
        except FileNotFoundError:
            raise HTTPException(status_code=400, detail="Skill-Datei nicht gefunden")

        skill.file_hash = current_hash
        skill.approved = True
        skill.enabled = True
    else:
        skill.approved = False
        skill.enabled = False

    await db.commit()
    return {"status": "approved" if data.approved else "revoked", "skill": skill.name}


@router.post("/{skill_id}/toggle")
async def toggle_skill(
    skill_id: str, data: SkillToggle, db: AsyncSession = Depends(get_db)
):
    """Skill aktivieren/deaktivieren (nur wenn approved)"""
    skill = await db.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill nicht gefunden")

    if data.enabled and not skill.approved:
        raise HTTPException(
            status_code=400, detail="Skill muss zuerst genehmigt werden"
        )

    skill.enabled = data.enabled
    await db.commit()
    return {"status": "enabled" if data.enabled else "disabled", "skill": skill.name}


@router.delete("/{skill_id}")
async def delete_skill(skill_id: str, db: AsyncSession = Depends(get_db)):
    """Skill aus der DB entfernen (Datei bleibt)"""
    skill = await db.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill nicht gefunden")

    await db.delete(skill)
    await db.commit()
    return {"status": "deleted", "skill": skill.name}


@router.post("/scan")
async def scan_skills(db: AsyncSession = Depends(get_db)):
    """Manueller Scan des Skills-Verzeichnisses"""
    loader = SkillLoader(db)
    found = await loader.scan_skills_dir()
    await db.commit()
    return {"found": len(found), "skills": found}
