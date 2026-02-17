"""
Axon by NeuroVexon - Embedding & Cosine Similarity Tests

Tests for cosine_similarity and EmbeddingProvider behavior.
"""

import pytest

try:
    from agent.embeddings import cosine_similarity, EmbeddingProvider
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False

pytestmark = pytest.mark.skipif(not HAS_EMBEDDINGS, reason="agent.embeddings not available")


class TestCosineSimilarity:
    """Tests for cosine similarity computation"""

    def test_identical_vectors(self):
        a = [1.0, 2.0, 3.0]
        result = cosine_similarity(a, a)
        assert abs(result - 1.0) < 1e-5

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        result = cosine_similarity(a, b)
        assert abs(result) < 1e-5

    def test_opposite_vectors(self):
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        result = cosine_similarity(a, b)
        assert abs(result - (-1.0)) < 1e-5

    def test_similar_vectors(self):
        a = [1.0, 1.0, 0.0]
        b = [1.0, 1.0, 0.1]
        result = cosine_similarity(a, b)
        assert result > 0.9  # Very similar

    def test_zero_vector_returns_zero(self):
        a = [0.0, 0.0, 0.0]
        b = [1.0, 2.0, 3.0]
        result = cosine_similarity(a, b)
        assert result == 0.0

    def test_both_zero_vectors(self):
        a = [0.0, 0.0]
        b = [0.0, 0.0]
        result = cosine_similarity(a, b)
        assert result == 0.0

    def test_high_dimensional(self):
        """Test with typical embedding dimensions"""
        a = [float(i) / 768 for i in range(768)]
        b = [float(i + 1) / 768 for i in range(768)]
        result = cosine_similarity(a, b)
        assert 0.0 < result <= 1.0

    def test_negative_values(self):
        a = [-1.0, -2.0, 3.0]
        b = [1.0, 2.0, -3.0]
        result = cosine_similarity(a, b)
        assert result < 0  # Opposite direction


class TestEmbeddingProvider:
    """Tests for EmbeddingProvider"""

    def test_default_model(self):
        provider = EmbeddingProvider()
        assert provider.model == "nomic-embed-text"

    def test_custom_model(self):
        provider = EmbeddingProvider(model="mxbai-embed-large")
        assert provider.model == "mxbai-embed-large"

    def test_initial_state(self):
        provider = EmbeddingProvider()
        assert provider._available is None
        assert provider._checked_at == 0

    def test_reset_cache(self):
        provider = EmbeddingProvider()
        provider._available = True
        provider._checked_at = 999

        provider.reset_cache()

        assert provider._available is None
        assert provider._checked_at == 0

    @pytest.mark.asyncio
    async def test_embed_returns_none_when_unavailable(self):
        provider = EmbeddingProvider()
        provider._available = False
        provider._checked_at = float("inf")  # Prevent re-check

        result = await provider.embed("test text")
        assert result is None

    @pytest.mark.asyncio
    async def test_embed_batch_returns_nones_when_unavailable(self):
        provider = EmbeddingProvider()
        provider._available = False
        provider._checked_at = float("inf")

        results = await provider.embed_batch(["text1", "text2", "text3"])
        assert len(results) == 3
        assert all(r is None for r in results)
