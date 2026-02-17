# Copyright 2026 NeuroVexon UG (haftungsbeschraenkt)
# SPDX-License-Identifier: Apache-2.0
"""
Axon by NeuroVexon - Embedding Provider

Generiert Embeddings ueber Ollama (nomic-embed-text) fuer semantische Memory-Suche.
Fallback: Kein Embedding verfuegbar → ILIKE-Suche wie bisher.
"""

import logging
from typing import Optional
import httpx

from core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """Generates text embeddings via Ollama"""

    def __init__(self, model: str = "nomic-embed-text"):
        self.model = model
        self.base_url = settings.ollama_base_url
        self._available: Optional[bool] = None

    async def is_available(self) -> bool:
        """Check if the embedding model is available in Ollama"""
        if self._available is not None:
            return self._available

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    model_names = [m.get("name", "").split(":")[0] for m in models]
                    self._available = self.model.split(":")[0] in model_names
                else:
                    self._available = False
        except Exception as e:
            logger.debug(f"Embedding model check failed: {e}")
            self._available = False

        if self._available:
            logger.info(f"Embedding model '{self.model}' verfuegbar")
        else:
            logger.info(f"Embedding model '{self.model}' nicht verfuegbar — Fallback auf ILIKE")

        return self._available

    def reset_cache(self):
        """Reset availability cache (z.B. nach Model-Pull)"""
        self._available = None

    async def embed(self, text: str) -> Optional[list[float]]:
        """Generate embedding for a single text. Returns None if unavailable."""
        if not await self.is_available():
            return None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model, "input": text}
                )
                resp.raise_for_status()
                data = resp.json()

                # Ollama /api/embed returns {"embeddings": [[...]]}
                embeddings = data.get("embeddings", [])
                if embeddings and len(embeddings) > 0:
                    return embeddings[0]

                return None
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            return None

    async def embed_batch(self, texts: list[str]) -> list[Optional[list[float]]]:
        """Generate embeddings for multiple texts"""
        if not await self.is_available():
            return [None] * len(texts)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model, "input": texts}
                )
                resp.raise_for_status()
                data = resp.json()

                embeddings = data.get("embeddings", [])
                # Pad with None if some embeddings are missing
                result = []
                for i in range(len(texts)):
                    if i < len(embeddings):
                        result.append(embeddings[i])
                    else:
                        result.append(None)
                return result
        except Exception as e:
            logger.warning(f"Batch embedding failed: {e}")
            return [None] * len(texts)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors using numpy"""
    try:
        import numpy as np
        a_arr = np.array(a, dtype=np.float32)
        b_arr = np.array(b, dtype=np.float32)
        dot = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))
    except ImportError:
        # Fallback ohne numpy
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


# Global singleton
embedding_provider = EmbeddingProvider()
