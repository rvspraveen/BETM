"""
SQLAlchemy async engine + session factory.
Also provides a helper to run pgvector extension setup.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.core.config import settings


engine = create_async_engine(
    settings.database_url,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create tables and enable pgvector extension."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        from app.models import base  # noqa: F401 — registers all models
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("""
            ALTER TABLE document_chunks
            ADD COLUMN IF NOT EXISTS section VARCHAR(512)
        """))
        await conn.execute(text("""
            ALTER TABLE document_chunks
            ADD COLUMN IF NOT EXISTS tags JSON
        """))
        await conn.execute(text("""
            ALTER TABLE document_chunks
            ADD COLUMN IF NOT EXISTS metadata JSON
        """))
