"""
Axon by NeuroVexon - Database Setup
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    connect_args={"timeout": 30},  # Wait up to 30s for locks
)


# Enable WAL mode for concurrent read/write support
@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()


async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def init_db():
    """Initialize database tables and run lightweight migrations"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Auto-add missing columns for SQLite (no ALTER COLUMN support)
        await conn.run_sync(_auto_migrate_columns)


def _auto_migrate_columns(conn):
    """Add missing columns to existing tables (SQLite-compatible)"""
    from sqlalchemy import inspect, text

    inspector = inspect(conn)
    for table in Base.metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue
        existing = {c["name"] for c in inspector.get_columns(table.name)}
        for col in table.columns:
            if col.name not in existing:
                col_type = col.type.compile(conn.dialect)
                nullable = "NULL" if col.nullable else "NOT NULL"
                default = ""
                if col.default is not None and col.default.is_scalar:
                    default = f" DEFAULT {col.default.arg!r}"
                conn.execute(
                    text(
                        f"ALTER TABLE {table.name} ADD COLUMN {col.name} {col_type} {nullable}{default}"
                    )
                )


async def get_db() -> AsyncSession:
    """Dependency for getting database session"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
