"""
Axon by NeuroVexon - Persistent Memory Manager

Verwaltet das Langzeitgedaechtnis des Agenten.
Memories werden in der DB gespeichert und bei jeder Konversation
als Kontext in den System-Prompt injiziert.

v2.0: Semantische Suche via Embeddings (Ollama nomic-embed-text).
Fallback auf ILIKE wenn Embeddings nicht verfuegbar.
"""

import logging
import struct
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models import Memory
from agent.embeddings import embedding_provider, cosine_similarity

logger = logging.getLogger(__name__)

# Maximale Anzahl Memories im System-Prompt (Token-Budget)
MAX_MEMORIES_IN_PROMPT = 30
MAX_MEMORY_CONTENT_LENGTH = 500


def _serialize_embedding(embedding: list[float]) -> bytes:
    """Serialize embedding list to bytes (float32)"""
    return struct.pack(f"{len(embedding)}f", *embedding)


def _deserialize_embedding(data: bytes) -> list[float]:
    """Deserialize bytes back to embedding list"""
    count = len(data) // 4  # float32 = 4 bytes
    return list(struct.unpack(f"{count}f", data))


class MemoryManager:
    """Manages persistent agent memories across conversations"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def add(
        self,
        key: str,
        content: str,
        source: str = "user",
        category: Optional[str] = None,
    ) -> Memory:
        """Add or update a memory entry (upsert by key)"""
        key = key.strip()[:255]
        content = content.strip()[:MAX_MEMORY_CONTENT_LENGTH]

        # Generate embedding for the combined key+content
        embed_text = f"{key}: {content}"
        embedding = await embedding_provider.embed(embed_text)
        embedding_bytes = _serialize_embedding(embedding) if embedding else None

        # Check if key already exists — update if so
        result = await self.db.execute(select(Memory).where(Memory.key == key))
        existing = result.scalar_one_or_none()

        if existing:
            existing.content = content
            existing.source = source
            existing.embedding = embedding_bytes
            if category:
                existing.category = category
            await self.db.flush()
            logger.info(f"Memory updated: {key}")
            return existing

        memory = Memory(
            key=key,
            content=content,
            source=source,
            category=category,
            embedding=embedding_bytes,
        )
        self.db.add(memory)
        await self.db.flush()
        logger.info(f"Memory created: {key}")
        return memory

    async def get(self, key: str) -> Optional[Memory]:
        """Get a single memory by key"""
        result = await self.db.execute(select(Memory).where(Memory.key == key))
        return result.scalar_one_or_none()

    async def get_by_id(self, memory_id: str) -> Optional[Memory]:
        """Get a single memory by ID"""
        return await self.db.get(Memory, memory_id)

    async def list_all(
        self, category: Optional[str] = None, limit: int = 100
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
        result = await self.db.execute(select(Memory).where(Memory.key == key))
        memory = result.scalar_one_or_none()
        if not memory:
            return False
        await self.db.delete(memory)
        await self.db.flush()
        logger.info(f"Memory deleted by key: {key}")
        return True

    async def search(self, query: str, limit: int = 10) -> list[Memory]:
        """
        Semantic search via embeddings with ILIKE fallback.

        1. Embed the query
        2. Load all memories with embeddings
        3. Rank by cosine similarity
        4. Fallback to ILIKE if no embeddings available
        """
        # Try semantic search first
        query_embedding = await embedding_provider.embed(query)

        if query_embedding:
            # Load all memories (bei <1000 kein Performance-Problem)
            result = await self.db.execute(select(Memory))
            all_memories = list(result.scalars().all())

            # Score memories with embeddings
            scored = []
            unscored = []
            for mem in all_memories:
                if mem.embedding:
                    mem_embedding = _deserialize_embedding(mem.embedding)
                    score = cosine_similarity(query_embedding, mem_embedding)
                    scored.append((score, mem))
                else:
                    unscored.append(mem)

            if scored:
                # Sort by similarity (highest first)
                scored.sort(key=lambda x: x[0], reverse=True)
                # Filter by minimum threshold
                results = [mem for score, mem in scored if score > 0.3][:limit]

                if results:
                    logger.info(
                        f"Semantic search for '{query}': {len(results)} results (best score: {scored[0][0]:.3f})"
                    )
                    return results

            # If no scored results, try to embed unscored memories lazily
            if unscored:
                logger.info(
                    f"{len(unscored)} memories without embeddings — generating lazily"
                )
                for mem in unscored[:50]:  # Max 50 auf einmal
                    embed_text = f"{mem.key}: {mem.content}"
                    emb = await embedding_provider.embed(embed_text)
                    if emb:
                        mem.embedding = _serialize_embedding(emb)
                await self.db.flush()

                # Retry search after embedding
                return await self._semantic_search(query_embedding, all_memories, limit)

        # Fallback: ILIKE text search
        logger.info(f"Fallback to ILIKE search for: {query}")
        return await self._ilike_search(query, limit)

    async def _semantic_search(
        self, query_embedding: list[float], memories: list[Memory], limit: int
    ) -> list[Memory]:
        """Perform semantic search on a list of memories"""
        scored = []
        for mem in memories:
            if mem.embedding:
                mem_embedding = _deserialize_embedding(mem.embedding)
                score = cosine_similarity(query_embedding, mem_embedding)
                scored.append((score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [mem for score, mem in scored if score > 0.3][:limit]
        return results

    async def _ilike_search(self, query: str, limit: int) -> list[Memory]:
        """Traditional ILIKE text search"""
        search_term = f"%{query.lower()}%"
        result = await self.db.execute(
            select(Memory)
            .where(
                (Memory.key.ilike(search_term)) | (Memory.content.ilike(search_term))
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

        lines = ["", "## Dein Gedaechtnis (persistente Fakten)", ""]
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
