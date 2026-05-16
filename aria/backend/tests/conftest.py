"""pytest fixtures shared across all backend tests."""
from __future__ import annotations

import os
import pathlib

# Must be set BEFORE any aria.backend imports so Settings() picks them up
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("STT_BACKEND", "local")
os.environ.setdefault("LLM_BACKEND", "ollama")
os.environ.setdefault("TTS_BACKEND", "piper")
os.environ.setdefault("DIAR_BACKEND", "local")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("HF_TOKEN", "fake-hf-token-for-tests")

# Use a file-based SQLite for tests.  File-path SQLite works with async
# aiosqlite; NullPool avoids connection-pool state between tests.
_TEST_DB_PATH = pathlib.Path(__file__).parent / "aria_test.db"
_TEST_DB_URL = f"sqlite+aiosqlite:///{_TEST_DB_PATH.as_posix()}"
os.environ.setdefault("DATABASE_URL", _TEST_DB_URL)

# Remove any stale DB (and journal/WAL files) so every session starts clean
for _suf in ("", "-journal", "-wal", "-shm"):
    pathlib.Path(str(_TEST_DB_PATH) + _suf).unlink(missing_ok=True)

from sqlalchemy import create_engine as _sync_create_engine  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

import aria.backend.database as _db  # noqa: E402

# Patch the async engine used by the app
_test_engine = create_async_engine(_TEST_DB_URL, poolclass=NullPool)
_db.engine = _test_engine
_db.AsyncSessionFactory = async_sessionmaker(
    _test_engine, class_=AsyncSession, expire_on_commit=False
)

# Create tables synchronously (avoids async event-loop lifecycle issues with
# aiosqlite daemon threads between asyncio.run() and pytest-asyncio loops).
# A plain sqlite3 engine for table creation; the app uses the async engine.
import aria.backend.modules.analysis.models  # noqa: F401, E402 — registers with Base
import aria.backend.modules.auth.models  # noqa: F401, E402
import aria.backend.modules.billing.models  # noqa: F401, E402
import aria.backend.modules.conversation.models  # noqa: F401, E402
import aria.backend.modules.flashcards.models  # noqa: F401, E402

_sync_engine = _sync_create_engine(f"sqlite:///{_TEST_DB_PATH}")
_db.Base.metadata.create_all(_sync_engine)
_sync_engine.dispose()

import uuid as _uuid  # noqa: E402

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402


# ── Shared mock user (used by authed_client) ──────────────────────────────────

class _MockUser:
    """Minimal user object that satisfies FastAPI-Users current_active_user."""

    id = _uuid.UUID("00000000-0000-0000-0000-000000000001")
    email = "test@aria.dev"
    is_active = True
    is_superuser = False
    is_verified = True


MOCK_USER = _MockUser()


@pytest_asyncio.fixture
async def client():
    """Unauthenticated async HTTP test client — use for auth tests and health checks."""
    from aria.backend.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def authed_client():
    """Authenticated async HTTP test client — auth injected, quotas bypassed.

    Overrides current_active_user with MOCK_USER and disables Free-tier quota
    dependencies so that endpoint-behavior tests don't accumulate session counts
    and hit limits. Use for all non-quota module endpoint tests.
    """
    from aria.backend.main import app
    from aria.backend.modules.auth.users import current_active_user
    from aria.backend.modules.billing.dependencies import (
        check_daily_analysis,
        check_daily_conversations,
        check_flashcard_limit,
    )

    _overrides = {
        current_active_user: lambda: MOCK_USER,
        check_daily_analysis: lambda: None,
        check_daily_conversations: lambda: None,
        check_flashcard_limit: lambda: None,
    }
    for dep, fn in _overrides.items():
        app.dependency_overrides[dep] = fn
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    for dep in _overrides:
        app.dependency_overrides.pop(dep, None)


@pytest_asyncio.fixture
async def quota_authed_client():
    """Authenticated async HTTP test client — auth injected, quotas enforced.

    Use only for TestFreeQuotaEnforcement tests that specifically verify
    that Free-tier limits block requests at the correct threshold.
    """
    from aria.backend.main import app
    from aria.backend.modules.auth.users import current_active_user

    app.dependency_overrides[current_active_user] = lambda: MOCK_USER
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.pop(current_active_user, None)
