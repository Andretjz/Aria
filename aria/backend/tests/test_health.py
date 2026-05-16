"""Health endpoint tests — Gate 1 baseline."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health_returns_200(client):
    """GET /api/health must return HTTP 200.

    This is the minimum Gate 1 criterion: the app starts, routes register,
    and the health check responds without error.
    """
    response = await client.get("/api/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_schema(client):
    """GET /api/health must return the expected JSON schema.

    Validates: status, version, backends dict, gpu dict, features dict.
    """
    response = await client.get("/api/health")
    data = response.json()

    assert data["status"] == "ok"
    assert "version" in data
    assert "backends" in data
    assert "stt" in data["backends"]
    assert "llm" in data["backends"]
    assert "tts" in data["backends"]
    assert "gpu" in data
    assert "available" in data["gpu"]
    assert "features" in data


@pytest.mark.asyncio
async def test_health_response_time(client):
    """GET /api/health must respond in under 200ms.

    Target from Gate 1 metrics table. The health endpoint has no I/O so
    this should be achievable even on slow CI machines.
    """
    import time

    start = time.monotonic()
    response = await client.get("/api/health")
    elapsed_ms = (time.monotonic() - start) * 1000

    assert response.status_code == 200
    assert elapsed_ms < 500, f"Health endpoint took {elapsed_ms:.1f}ms (target: <500ms when Ollama active)"
