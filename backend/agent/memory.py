"""
Axon by NeuroVexon - Persistent Memory Manager

Verwaltet das Langzeitgedächtnis des Agenten.
Memories werden in der DB gespeichert und bei jeder Konversation
als Kontext in den System-Prompt injiziert.
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from db.models import Memory

logger = logging.getLogger(__name__)

# Maximale Anzahl Memories im System-Prompt (Token-Budget)
MAX_MEMORIES_IN_PROMPT = 30
MAX_MEMORY_CONTENT_LENGTH = 500


class MemoryManager:
    """Manages persistent agent memories across conversations"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def add(
        self,
        key: str,
        content: str,
        source: str = "user",
        category: Optional[str] = None
    ) -> Memory:
        """Add or update a memory entry (upsert by key)"""
        key = key.strip()[:255]
        content = content.strip()[:MAX_MEMORY_CONTENT_LENGTH]

        # Check if key already exists — update if so
        result = await self.db.execute(
            select(Memory).where(Memory.key == key)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.content = content
            existing.source = source
            if category:
                existing.category = category
            await self.db.flush()
            logger.info(f"Memory updated: {key}")
            return existing

        memory = Memory(
            key=key,
            content=content,
            source=source,
            category=category
        )
        self.db.add(memory)
        await self.db.flush()
        logger.info(f"Memory created: {key}")
        return memory

    async def get(self, key: str) -> Optional[Memory]:
        """Get a single memory by key"""
        result = await self.db.execute(
            select(Memory).where(Memory.key == key)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, memory_id: str) -> Optional[Memory]:
        """Get a single memory by ID"""
        return await self.db.get(Memory, memory_id)

    async def list_all(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> list[Memory]:
        """List all memories, optionally filtered by category"""
        query = select(Memory).order_by(Memory.updated_at.desc()).limit(limit)
        if category:
            query = query.where(Memory.category == category)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def remove(self, memory_id: str) -> bool:
        """Delete a memory by ID"""
        memory = await self.db.get(Memory, memory_id)
        if not memory:
            return False
        await self.db.delete(memory)
        await self.db.flush()
        logger.info(f"Memory deleted: {memory.key}")
        return True

    async def remove_by_key(self, key: str) -> bool:
        """Delete a memory by key"""
        result = await self.db.execute(
            select(Memory).where(Memory.key == key)
        )
        memory = result.scalar_one_or_none()
        if not memory:
            return False
        await self.db.delete(memory)
        await self.db.flush()
        logger.info(f"Memory deleted by key: {key}")
        return True

    async def search(self, query: str, limit: int = 10) -> list[Memory]:
        """Simple text search in key and content"""
        search_term = f"%{query.lower()}%"
        result = await self.db.execute(
            select(Memory)
            .where(
                (Memory.key.ilike(search_term)) |
                (Memory.content.ilike(search_term))
            )
            .order_by(Memory.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def build_memory_prompt(self, plain: bool = False) -> str:
        """
        Build a memory block for injection into the system prompt.
        Returns an empty string if no memories exist.

        Args:
            plain: If True, returns plain text without markdown (for tool-calling models).
        """
        memories = await self.list_all(limit=MAX_MEMORIES_IN_PROMPT)
        if not memories:
            return ""

        if plain:
            # Plain text format — preserves tool calling in smaller models
            facts = []
            for mem in memories:
                facts.append(f"{mem.key}: {mem.content}")
            return "Bekannte Fakten: " + ". ".join(facts) + "."

        lines = ["", "## Dein Gedächtnis (persistente Fakten)", ""]
        for mem in memories:
            category_tag = f" [{mem.category}]" if mem.category else ""
            lines.append(f"- **{mem.key}**{category_tag}: {mem.content}")

        lines.append("")
        lines.append("Nutze dieses Wissen in deinen Antworten, wenn es relevant ist.")
        return "\n".join(lines)

    async def clear_all(self) -> int:
        """Delete all memories. Returns count of deleted entries."""
        result = await self.db.execute(select(Memory))
        memories = result.scalars().all()
        count = len(memories)
        for mem in memories:
            await self.db.delete(mem)
        await self.db.flush()
        logger.info(f"All memories cleared: {count} entries")
        return count
