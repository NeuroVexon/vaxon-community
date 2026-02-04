"""
Axon by NeuroVexon - Settings API Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import json

from db.database import get_db
from db.models import Settings
from core.config import settings as app_settings, LLMProvider
from llm.router import llm_router

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    llm_provider: Optional[str] = None
    theme: Optional[str] = None
    system_prompt: Optional[str] = None


@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Get current settings"""
    result = await db.execute(select(Settings))
    db_settings = {s.key: s.value for s in result.scalars().all()}

    return {
        "app_name": app_settings.app_name,
        "app_version": app_settings.app_version,
        "llm_provider": db_settings.get("llm_provider", app_settings.llm_provider.value),
        "theme": db_settings.get("theme", "dark"),
        "system_prompt": db_settings.get("system_prompt", ""),
        "available_providers": [p.value for p in LLMProvider]
    }


@router.put("")
async def update_settings(
    update: SettingsUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update settings"""
    updates = update.model_dump(exclude_none=True)

    for key, value in updates.items():
        result = await db.execute(
            select(Settings).where(Settings.key == key)
        )
        setting = result.scalar_one_or_none()

        if setting:
            setting.value = str(value)
        else:
            setting = Settings(key=key, value=str(value))
            db.add(setting)

    await db.commit()
    return {"status": "updated", "changes": updates}


@router.get("/health")
async def health_check():
    """Check health of all LLM providers"""
    provider_health = await llm_router.health_check_all()

    return {
        "status": "healthy",
        "app_name": app_settings.app_name,
        "version": app_settings.app_version,
        "providers": provider_health
    }
