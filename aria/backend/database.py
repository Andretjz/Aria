"""SQLAlchemy async engine and session factory.

All database access goes through get_db() — never create sessions directly.
Alembic uses the sync URL (DATABASE_URL with asyncpg swapped for psycopg2)
in migrations/env.py.
"""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from aria.backend.core.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session per request.

    Yields:
        An async SQLAlchemy session that is closed after the request.
    """
    async with AsyncSessionFactory() as session:
        yield session


async def create_tables() -> None:
    """Create all tables defined in ORM models (dev convenience — use Alembic in prod).

    Note:
        In production, tables are managed by Alembic migrations.
        This function is called during app startup in DEBUG mode only.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

