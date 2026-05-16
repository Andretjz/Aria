"""pytest fixtures shared across all backend tests."""
from __future__ import annotations

import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Use in-memory SQLite for all tests — no external DB required
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:////:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("STT_BACKEND", "local")
os.environ.setdefault("LLM_BACKEND", "ollama")
os.environ.setdefault("TTS_BACKEND", "piper")
os.environ.setdefault("DIAR_BACKEND", "local")
os.environ.setdefault("DEBUG", "true")


@pytest_asyncio.fixture
async def client():
    """Async HTTP test client bound to the FastAPI app.

    Yields:
        An httpx.AsyncClient configured with the ASGI transport.
    """
    from aria.backend.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
