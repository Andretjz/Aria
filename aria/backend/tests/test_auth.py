"""Phase 2 (Anna_Auth) — Gate 2 auth endpoint tests.

All tests use a shared in-memory SQLite DB (StaticPool in conftest.py).
Each test uses a unique email to avoid cross-test interference.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REG = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
LOGOUT = "/api/v1/auth/logout"
REFRESH = "/api/v1/auth/refresh"
ME = "/api/v1/auth/me"
PREFS = "/api/v1/auth/me/preferences"
EXPORT = "/api/v1/auth/me/export"
DELETE_ME = "/api/v1/auth/me"

_PASS = "Str0ng!Pass99"


async def _register_and_login(client: AsyncClient, email: str) -> None:
    """Register + login, leaving access + refresh cookies in the client jar."""
    r = await client.post(REG, json={"email": email, "password": _PASS})
    assert r.status_code == 201, r.text
    r = await client.post(LOGIN, json={"email": email, "password": _PASS})
    assert r.status_code == 200, r.text


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegister:
    async def test_register_201_returns_user(self, client: AsyncClient):
        r = await client.post(REG, json={"email": "reg1@example.com", "password": _PASS})
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == "reg1@example.com"
        assert "id" in data
        assert "hashed_password" not in data

    async def test_register_duplicate_400(self, client: AsyncClient):
        payload = {"email": "reg2@example.com", "password": _PASS}
        await client.post(REG, json=payload)
        r = await client.post(REG, json=payload)
        assert r.status_code == 400

    async def test_register_invalid_email_422(self, client: AsyncClient):
        r = await client.post(REG, json={"email": "not-an-email", "password": _PASS})
        assert r.status_code == 422

    async def test_register_missing_password_422(self, client: AsyncClient):
        # Missing required field → Pydantic 422
        r = await client.post(REG, json={"email": "reg3@example.com"})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    async def test_login_200_sets_cookies(self, client: AsyncClient):
        await client.post(REG, json={"email": "login1@example.com", "password": _PASS})
        r = await client.post(LOGIN, json={"email": "login1@example.com", "password": _PASS})
        assert r.status_code == 200
        assert "aria_access" in r.cookies
        assert "aria_refresh" in r.cookies

    async def test_login_returns_user_with_preferences(self, client: AsyncClient):
        await client.post(REG, json={"email": "login2@example.com", "password": _PASS})
        r = await client.post(LOGIN, json={"email": "login2@example.com", "password": _PASS})
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == "login2@example.com"
        # Preferences are created on register
        assert data["preferences"] is not None
        assert data["preferences"]["target_lang"] == "de"

    async def test_login_wrong_password_401(self, client: AsyncClient):
        await client.post(REG, json={"email": "login3@example.com", "password": _PASS})
        r = await client.post(LOGIN, json={"email": "login3@example.com", "password": "wrongpass"})
        assert r.status_code == 401

    async def test_login_unknown_email_401(self, client: AsyncClient):
        r = await client.post(LOGIN, json={"email": "nobody@example.com", "password": _PASS})
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# /me
# ---------------------------------------------------------------------------

class TestGetMe:
    async def test_get_me_authenticated(self, client: AsyncClient):
        await _register_and_login(client, "me1@example.com")
        r = await client.get(ME)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == "me1@example.com"
        assert data["preferences"]["target_lang"] == "de"

    async def test_get_me_unauthenticated_401(self, client: AsyncClient):
        r = await client.get(ME)
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------

class TestPreferences:
    async def test_update_preferences(self, client: AsyncClient):
        await _register_and_login(client, "prefs1@example.com")
        r = await client.patch(PREFS, json={"target_lang": "es", "ui_lang": "de"})
        assert r.status_code == 200
        data = r.json()
        assert data["target_lang"] == "es"
        assert data["ui_lang"] == "de"
        assert data["input_lang"] == "en"   # unchanged default

    async def test_update_preferences_unauthenticated_401(self, client: AsyncClient):
        r = await client.patch(PREFS, json={"target_lang": "fr"})
        assert r.status_code == 401

    async def test_preferences_persist_after_update(self, client: AsyncClient):
        await _register_and_login(client, "prefs2@example.com")
        await client.patch(PREFS, json={"target_lang": "it"})
        r = await client.get(ME)
        assert r.json()["preferences"]["target_lang"] == "it"


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class TestLogout:
    async def test_logout_204(self, client: AsyncClient):
        await _register_and_login(client, "logout1@example.com")
        r = await client.post(LOGOUT)
        assert r.status_code == 204

    async def test_me_after_logout_401(self, client: AsyncClient):
        await _register_and_login(client, "logout2@example.com")
        await client.post(LOGOUT)
        r = await client.get(ME)
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------

class TestRefresh:
    async def test_refresh_rotates_refresh_token(self, client: AsyncClient):
        await _register_and_login(client, "refresh1@example.com")
        old_refresh = client.cookies.get("aria_refresh")
        r = await client.post(REFRESH)
        assert r.status_code == 200
        # Refresh token must change (it's random); access token may be
        # identical within the same second (JWT exp is second-granular)
        new_refresh = client.cookies.get("aria_refresh")
        assert new_refresh is not None
        assert new_refresh != old_refresh

    async def test_refresh_without_cookie_401(self, client: AsyncClient):
        r = await client.post(REFRESH)
        assert r.status_code == 401

    async def test_me_works_after_refresh(self, client: AsyncClient):
        await _register_and_login(client, "refresh2@example.com")
        await client.post(REFRESH)
        r = await client.get(ME)
        assert r.status_code == 200
        assert r.json()["email"] == "refresh2@example.com"


# ---------------------------------------------------------------------------
# GDPR — export
# ---------------------------------------------------------------------------

class TestGDPRExport:
    async def test_export_200_returns_all_fields(self, client: AsyncClient):
        await _register_and_login(client, "gdpr1@example.com")
        r = await client.get(EXPORT)
        assert r.status_code == 200
        data = r.json()
        assert data["user"]["email"] == "gdpr1@example.com"
        assert "preferences" in data
        assert "exported_at" in data
        assert "sessions_count" in data
        assert "oauth_providers" in data

    async def test_export_includes_preferences(self, client: AsyncClient):
        await _register_and_login(client, "gdpr2@example.com")
        await client.patch(PREFS, json={"target_lang": "fr"})
        r = await client.get(EXPORT)
        assert r.status_code == 200
        assert r.json()["preferences"]["target_lang"] == "fr"

    async def test_export_unauthenticated_401(self, client: AsyncClient):
        r = await client.get(EXPORT)
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# GDPR — delete
# ---------------------------------------------------------------------------

class TestGDPRDelete:
    async def test_delete_204(self, client: AsyncClient):
        await _register_and_login(client, "del1@example.com")
        r = await client.delete(DELETE_ME)
        assert r.status_code == 204

    async def test_login_fails_after_deletion(self, client: AsyncClient):
        await _register_and_login(client, "del2@example.com")
        await client.delete(DELETE_ME)
        r = await client.post(LOGIN, json={"email": "del2@example.com", "password": _PASS})
        assert r.status_code == 401

    async def test_delete_unauthenticated_401(self, client: AsyncClient):
        r = await client.delete(DELETE_ME)
        assert r.status_code == 401
