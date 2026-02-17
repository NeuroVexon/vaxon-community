"""
Axon by NeuroVexon - Memory API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from db.database import get_db
from agent.memory import MemoryManager

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryCreate(BaseModel):
    key: str
    content: str
    source: str = "user"
    category: Optional[str] = None


class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    category: Optional[str] = None


class MemoryResponse(BaseModel):
    id: str
    key: str
    content: str
    source: str
    category: Optional[str]
    created_at: str
    updated_at: str


@router.get("")
async def list_memories(
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Alle Memories auflisten, optional mit Kategorie-Filter oder Suche"""
    manager = MemoryManager(db)

    if search:
        memories = await manager.search(search, limit=limit)
    else:
        memories = await manager.list_all(category=category, limit=limit)

    return [
        {
            "id": m.id,
            "key": m.key,
            "content": m.content,
            "source": m.source,
            "category": m.category,
            "created_at": m.created_at.isoformat(),
            "updated_at": m.updated_at.isoformat(),
        }
        for m in memories
    ]


@router.post("")
async def create_memory(data: MemoryCreate, db: AsyncSession = Depends(get_db)):
    """Memory erstellen oder aktualisieren (Upsert nach key)"""
    if not data.key.strip():
        raise HTTPException(status_code=400, detail="Key darf nicht leer sein")
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Content darf nicht leer sein")

    manager = MemoryManager(db)
    memory = await manager.add(
        key=data.key, content=data.content, source=data.source, category=data.category
    )
    await db.commit()

    return {
        "id": memory.id,
        "key": memory.key,
        "content": memory.content,
        "source": memory.source,
        "category": memory.category,
        "created_at": memory.created_at.isoformat(),
        "updated_at": memory.updated_at.isoformat(),
    }


@router.get("/{memory_id}")
async def get_memory(memory_id: str, db: AsyncSession = Depends(get_db)):
    """Einzelnes Memory abrufen"""
    manager = MemoryManager(db)
    memory = await manager.get_by_id(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory nicht gefunden")

    return {
        "id": memory.id,
        "key": memory.key,
        "content": memory.content,
        "source": memory.source,
        "category": memory.category,
        "created_at": memory.created_at.isoformat(),
        "updated_at": memory.updated_at.isoformat(),
    }


@router.put("/{memory_id}")
async def update_memory(
    memory_id: str, data: MemoryUpdate, db: AsyncSession = Depends(get_db)
):
    """Memory aktualisieren"""
    manager = MemoryManager(db)
    memory = await manager.get_by_id(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory nicht gefunden")

    if data.content is not None:
        memory.content = data.content.strip()[:500]
    if data.category is not None:
        memory.category = data.category

    await db.commit()

    return {
        "id": memory.id,
        "key": memory.key,
        "content": memory.content,
        "source": memory.source,
        "category": memory.category,
        "created_at": memory.created_at.isoformat(),
        "updated_at": memory.updated_at.isoformat(),
    }


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, db: AsyncSession = Depends(get_db)):
    """Memory löschen"""
    manager = MemoryManager(db)
    deleted = await manager.remove(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory nicht gefunden")
    await db.commit()
    return {"status": "deleted"}


@router.delete("")
async def clear_all_memories(db: AsyncSession = Depends(get_db)):
    """Alle Memories löschen"""
    manager = MemoryManager(db)
    count = await manager.clear_all()
    await db.commit()
    return {"status": "cleared", "count": count}
