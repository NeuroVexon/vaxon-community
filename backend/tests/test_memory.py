"""
Axon by NeuroVexon - Memory Manager Tests

Tests for MemoryManager: CRUD operations, search, prompt building, serialization.
"""

import pytest

from agent.memory import MemoryManager, MAX_MEMORY_CONTENT_LENGTH

# Embedding serialization only available with v2.0 embeddings
try:
    from agent.memory import _serialize_embedding, _deserialize_embedding
    HAS_EMBEDDING_SERIALIZATION = True
except ImportError:
    HAS_EMBEDDING_SERIALIZATION = False


@pytest.mark.skipif(not HAS_EMBEDDING_SERIALIZATION, reason="Embedding serialization not available")
class TestEmbeddingSerialization:
    """Tests for embedding serialization/deserialization"""

    def test_roundtrip(self):
        original = [0.1, 0.2, 0.3, 0.4, 0.5]
        serialized = _serialize_embedding(original)
        deserialized = _deserialize_embedding(serialized)

        assert len(deserialized) == len(original)
        for a, b in zip(original, deserialized):
            assert abs(a - b) < 1e-6

    def test_empty_list(self):
        serialized = _serialize_embedding([])
        deserialized = _deserialize_embedding(serialized)
        assert deserialized == []

    def test_serialized_size(self):
        embedding = [0.0] * 768  # Typical embedding dimension
        serialized = _serialize_embedding(embedding)
        assert len(serialized) == 768 * 4  # 4 bytes per float32

    def test_negative_values(self):
        original = [-1.0, -0.5, 0.0, 0.5, 1.0]
        result = _deserialize_embedding(_serialize_embedding(original))
        for a, b in zip(original, result):
            assert abs(a - b) < 1e-6


class TestMemoryManagerCRUD:
    """Tests for MemoryManager CRUD operations"""

    @pytest.mark.asyncio
    async def test_add_memory(self, db, mock_embedding):
        manager = MemoryManager(db)
        mem = await manager.add("Python", "Lieblings-Sprache", category="Technik")

        assert mem.key == "Python"
        assert mem.content == "Lieblings-Sprache"
        assert mem.category == "Technik"
        assert mem.source == "user"

    @pytest.mark.asyncio
    async def test_add_memory_upsert(self, db, mock_embedding):
        manager = MemoryManager(db)
        mem1 = await manager.add("Name", "Alice")
        mem2 = await manager.add("Name", "Bob")

        # Same key should update, not create new
        assert mem1.id == mem2.id
        assert mem2.content == "Bob"

    @pytest.mark.asyncio
    async def test_add_memory_truncates_content(self, db, mock_embedding):
        manager = MemoryManager(db)
        long_content = "x" * (MAX_MEMORY_CONTENT_LENGTH + 100)
        mem = await manager.add("Test", long_content)

        assert len(mem.content) <= MAX_MEMORY_CONTENT_LENGTH

    @pytest.mark.asyncio
    async def test_add_memory_truncates_key(self, db, mock_embedding):
        manager = MemoryManager(db)
        long_key = "k" * 300
        mem = await manager.add(long_key, "value")

        assert len(mem.key) <= 255

    @pytest.mark.asyncio
    async def test_get_by_key(self, db, mock_embedding):
        manager = MemoryManager(db)
        await manager.add("Server", "Hetzner 78.46.106.190")

        found = await manager.get("Server")
        assert found is not None
        assert found.content == "Hetzner 78.46.106.190"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, db, mock_embedding):
        manager = MemoryManager(db)
        found = await manager.get("Nicht-vorhanden")
        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_id(self, db, mock_embedding):
        manager = MemoryManager(db)
        mem = await manager.add("Test", "Wert")

        found = await manager.get_by_id(mem.id)
        assert found is not None
        assert found.key == "Test"

    @pytest.mark.asyncio
    async def test_list_all(self, db, mock_embedding):
        manager = MemoryManager(db)
        await manager.add("A", "Eins")
        await manager.add("B", "Zwei")
        await manager.add("C", "Drei")

        all_memories = await manager.list_all()
        assert len(all_memories) == 3

    @pytest.mark.asyncio
    async def test_list_all_with_category_filter(self, db, mock_embedding):
        manager = MemoryManager(db)
        await manager.add("Python", "Sprache", category="Technik")
        await manager.add("Name", "Max", category="Persoenlich")
        await manager.add("FastAPI", "Framework", category="Technik")

        technik = await manager.list_all(category="Technik")
        assert len(technik) == 2

    @pytest.mark.asyncio
    async def test_list_all_with_limit(self, db, mock_embedding):
        manager = MemoryManager(db)
        for i in range(10):
            await manager.add(f"Key-{i}", f"Value-{i}")

        limited = await manager.list_all(limit=3)
        assert len(limited) == 3

    @pytest.mark.asyncio
    async def test_remove_by_id(self, db, mock_embedding):
        manager = MemoryManager(db)
        mem = await manager.add("Loeschbar", "Weg damit")

        result = await manager.remove(mem.id)
        assert result is True

        found = await manager.get("Loeschbar")
        assert found is None

    @pytest.mark.asyncio
    async def test_remove_nonexistent_id(self, db, mock_embedding):
        manager = MemoryManager(db)
        result = await manager.remove("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_by_key(self, db, mock_embedding):
        manager = MemoryManager(db)
        await manager.add("Loeschbar", "Weg damit")

        result = await manager.remove_by_key("Loeschbar")
        assert result is True

        found = await manager.get("Loeschbar")
        assert found is None

    @pytest.mark.asyncio
    async def test_clear_all(self, db, mock_embedding):
        manager = MemoryManager(db)
        await manager.add("A", "1")
        await manager.add("B", "2")
        await manager.add("C", "3")

        count = await manager.clear_all()
        assert count == 3

        remaining = await manager.list_all()
        assert len(remaining) == 0


class TestMemorySearch:
    """Tests for memory search (ILIKE fallback without embeddings)"""

    @pytest.mark.asyncio
    async def test_ilike_search_by_key(self, db, mock_embedding):
        manager = MemoryManager(db)
        await manager.add("Python Version", "3.11")
        await manager.add("Node Version", "20")

        results = await manager.search("Python")
        assert len(results) >= 1
        assert any(m.key == "Python Version" for m in results)

    @pytest.mark.asyncio
    async def test_ilike_search_by_content(self, db, mock_embedding):
        manager = MemoryManager(db)
        await manager.add("Server", "Hetzner in Deutschland")
        await manager.add("Domain", "neurovexon.com")

        results = await manager.search("Hetzner")
        assert len(results) >= 1
        assert results[0].key == "Server"

    @pytest.mark.asyncio
    async def test_search_no_results(self, db, mock_embedding):
        manager = MemoryManager(db)
        await manager.add("Python", "3.11")

        results = await manager.search("Kubernetes")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_case_insensitive(self, db, mock_embedding):
        manager = MemoryManager(db)
        await manager.add("FASTAPI", "Web Framework")

        results = await manager.search("fastapi")
        assert len(results) >= 1


class TestMemoryPrompt:
    """Tests for memory prompt building"""

    @pytest.mark.asyncio
    async def test_build_prompt_empty(self, db, mock_embedding):
        manager = MemoryManager(db)
        prompt = await manager.build_memory_prompt()
        assert prompt == ""

    @pytest.mark.asyncio
    async def test_build_prompt_markdown(self, db, mock_embedding):
        manager = MemoryManager(db)
        await manager.add("Python", "Lieblings-Sprache", category="Technik")

        prompt = await manager.build_memory_prompt()
        assert "Ged" in prompt and "chtnis" in prompt  # Works with both ä and ae
        assert "**Python**" in prompt
        assert "[Technik]" in prompt
        assert "Lieblings-Sprache" in prompt

    @pytest.mark.asyncio
    async def test_build_prompt_plain(self, db, mock_embedding):
        manager = MemoryManager(db)
        await manager.add("Server", "Hetzner")

        prompt = await manager.build_memory_prompt(plain=True)
        assert "Bekannte Fakten:" in prompt
        assert "Server: Hetzner" in prompt
        assert "**" not in prompt  # No markdown
