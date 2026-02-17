"""
Axon by NeuroVexon - Test Configuration & Shared Fixtures
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, patch

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from db.database import Base

# Check if embeddings module exists (v2.0 with semantic search)
try:
    import agent.embeddings  # noqa: F401

    HAS_EMBEDDINGS_MODULE = True
except ImportError:
    HAS_EMBEDDINGS_MODULE = False


@pytest.fixture
async def db_engine():
    """Create an in-memory SQLite engine for testing"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db(db_engine):
    """Create an async database session for testing"""
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_embedding():
    """Mock the embedding provider to avoid Ollama dependency.
    Only patches if the embeddings module exists (v2.0+)."""
    if HAS_EMBEDDINGS_MODULE:
        with patch("agent.memory.embedding_provider") as mock:
            mock.embed = AsyncMock(return_value=None)
            mock.is_available = AsyncMock(return_value=False)
            yield mock
    else:
        yield None


@pytest.fixture
def client():
    """Create FastAPI test client"""
    from fastapi.testclient import TestClient
    from main import app

    return TestClient(app)
