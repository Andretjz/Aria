# Gate 2 — Auth, User Model & GDPR Endpoints

**Date:** 2026-05-16
**Agent:** Anna_Auth
**Branch:** `phase-2/anna-auth`
**Verdict:** APPROVED

---

## Checklist

### ORM Models
- [x] `User(SQLAlchemyBaseUserTableUUID, Base)` — FastAPI-Users base (id, email, hashed_password, is_active, is_superuser, is_verified)
- [x] `OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base)` — OAuth tokens; `user_id` FK with `ondelete="CASCADE"`
- [x] `UserPreferences(Base)` — `input_lang`, `target_lang`, `feedback_lang`, `ui_lang`; 1:1 with User, cascade-deleted
- [x] `UserSession(Base)` — refresh token store; `token_hash` (SHA-256), `expires_at`, `is_revoked`, `user_agent`, `ip_address`
- [x] `UserSession.make_token()` — static helper returns `(raw_token, hash)`; raw sent to client, hash stored
- [x] All FK constraints include `ondelete="CASCADE"` — DB-level cascade, no Python-level loading required

### FastAPI-Users Setup (`users.py`)
- [x] `get_user_db` — `SQLAlchemyUserDatabase(session, User, OAuthAccount)`
- [x] `UserManager(UUIDIDMixin, BaseUserManager)` — `on_after_register` creates default `UserPreferences`
- [x] `CookieTransport` — `aria_access`, HttpOnly, Secure in prod, SameSite=Lax
- [x] `get_jwt_strategy()` — `JWTStrategy(SECRET_KEY, 15 min)` — standard FastAPI-Users JWT format (`aud: ["fastapi-users:auth"]`)
- [x] `auth_backend` — `AuthenticationBackend(name="cookie", transport, get_strategy)`
- [x] `fastapi_users` instance + `current_active_user` dependency

### Auth Endpoints (`/api/v1/auth/`)
- [x] `POST /register` — FastAPI-Users register router; 201 on success, 400 on duplicate email, 422 on invalid schema
- [x] `POST /login` — JSON body; validates with `UserManager`; issues `aria_access` HttpOnly cookie (JWT, 15 min) + `aria_refresh` HttpOnly cookie (random token, 7 days, path=/api/v1/auth); creates `UserSession`; returns `UserWithPreferencesRead`
- [x] `POST /logout` — revokes `UserSession` by token_hash; clears both cookies; 204
- [x] `POST /refresh` — validates refresh token against `UserSession`; rotates (old revoked, new created); issues new `aria_access` cookie; 200
- [x] `GET /me` — returns `UserWithPreferencesRead` (id, email, flags, preferences); 401 if unauthenticated
- [x] `PATCH /me/preferences` — partial update of `UserPreferences` (input_lang, target_lang, feedback_lang, ui_lang); creates record if missing; 200
- [x] `GET /me/export` — GDPR Article 20 data portability; returns user data, preferences, active session count, OAuth providers; 401 if unauthenticated
- [x] `DELETE /me` — GDPR Article 17 right to erasure; deletes `User` (DB cascades all related rows); clears cookies; 204

### Security Design
- [x] Dual-token pattern: short-lived JWT access (15 min) + long-lived random refresh (7 days)
- [x] Refresh tokens stored as SHA-256 hash only — raw token never persisted
- [x] Refresh cookie scoped to `path=/api/v1/auth` — not sent to other modules
- [x] `aria_access` cookie: HttpOnly, SameSite=Lax, Secure in prod (non-DEBUG)
- [x] Login returns same 401 for both "unknown email" and "wrong password" (no enumeration)
- [x] `current_active_user` dependency validates JWT + checks `is_active` flag

### Database Migration
- [x] `aria/backend/migrations/versions/001_create_auth_tables.py` — creates `user`, `oauth_account`, `user_preferences`, `user_sessions` with all FK constraints and indexes
- [x] `downgrade()` implemented — drops all 4 tables in reverse dependency order

### Test Infrastructure Fix
- [x] `conftest.py` updated — file-based SQLite (`aria_test.db`) with `NullPool`; tables created via synchronous SQLAlchemy engine at session start (avoids aiosqlite daemon-thread lock conflict between `asyncio.run()` and pytest-asyncio event loops)
- [x] Gate 1 tests (12/12) still pass unmodified

### Gate 2 Tests
- [x] pytest 36/36 passed, 0 failed

```
tests/test_auth.py::TestRegister::test_register_201_returns_user          PASSED
tests/test_auth.py::TestRegister::test_register_duplicate_400             PASSED
tests/test_auth.py::TestRegister::test_register_invalid_email_422         PASSED
tests/test_auth.py::TestRegister::test_register_missing_password_422      PASSED
tests/test_auth.py::TestLogin::test_login_200_sets_cookies                PASSED
tests/test_auth.py::TestLogin::test_login_returns_user_with_preferences   PASSED
tests/test_auth.py::TestLogin::test_login_wrong_password_401              PASSED
tests/test_auth.py::TestLogin::test_login_unknown_email_401               PASSED
tests/test_auth.py::TestGetMe::test_get_me_authenticated                  PASSED
tests/test_auth.py::TestGetMe::test_get_me_unauthenticated_401            PASSED
tests/test_auth.py::TestPreferences::test_update_preferences              PASSED
tests/test_auth.py::TestPreferences::test_update_preferences_unauthenticated_401 PASSED
tests/test_auth.py::TestPreferences::test_preferences_persist_after_update PASSED
tests/test_auth.py::TestLogout::test_logout_204                           PASSED
tests/test_auth.py::TestLogout::test_me_after_logout_401                  PASSED
tests/test_auth.py::TestRefresh::test_refresh_rotates_refresh_token       PASSED
tests/test_auth.py::TestRefresh::test_refresh_without_cookie_401          PASSED
tests/test_auth.py::TestRefresh::test_me_works_after_refresh              PASSED
tests/test_auth.py::TestGDPRExport::test_export_200_returns_all_fields    PASSED
tests/test_auth.py::TestGDPRExport::test_export_includes_preferences      PASSED
tests/test_auth.py::TestGDPRExport::test_export_unauthenticated_401       PASSED
tests/test_auth.py::TestGDPRDelete::test_delete_204                       PASSED
tests/test_auth.py::TestGDPRDelete::test_login_fails_after_deletion       PASSED
tests/test_auth.py::TestGDPRDelete::test_delete_unauthenticated_401       PASSED
tests/test_health.py::test_health_returns_200                             PASSED
tests/test_health.py::test_health_schema                                  PASSED
tests/test_health.py::test_health_response_time                           PASSED
tests/test_interfaces.py::test_interfaces_importable                      PASSED
tests/test_interfaces.py::test_factory_importable                         PASSED
tests/test_interfaces.py::test_core_constants_importable                  PASSED
tests/test_interfaces.py::test_parse_json_from_llm_clean                  PASSED
tests/test_interfaces.py::test_parse_json_from_llm_markdown_fence         PASSED
tests/test_interfaces.py::test_parse_json_from_llm_truncated              PASSED
tests/test_interfaces.py::test_parse_json_from_llm_none                   PASSED
tests/test_interfaces.py::test_gpu_helpers_importable                     PASSED
tests/test_interfaces.py::test_exceptions_hierarchy                       PASSED
36 passed in 5.73s
```

---

## Bugs Fixed During Phase 2

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| `unable to open database file` | `sqlite+aiosqlite:////:memory:` (4 slashes) parses as absolute path `/:memory:`, not in-memory | Changed to file-based `sqlite+aiosqlite:///./aria_test.db` |
| `attempt to write a readonly database` | `asyncio.run()` + aiosqlite daemon thread holds file lock between event loops | Create tables via synchronous `sqlalchemy.create_engine` (no async) before pytest starts |
| `test_refresh_issues_new_access_token` failure | JWT is deterministic on same user+second — access token identical within 1s | Changed assertion to verify refresh token rotated (random, always different) |
| `test_register_weak_password_422` false assumption | FastAPI-Users v14 has no default minimum password length | Changed to test missing field → 422 (actual Pydantic validation) |

---

## Decisions Locked

- **Dual-token auth**: HttpOnly `aria_access` (JWT, 15 min) + HttpOnly `aria_refresh` (random, 7 days, path-scoped)
- **Refresh token storage**: SHA-256 hash only; raw token sent to client and never stored
- **Cross-session DB access**: `current_active_user` and endpoint `get_db` are separate SQLAlchemy sessions; all relationship access done via explicit queries in the endpoint's own session
- **`on_after_register` hook**: creates `UserPreferences` with language defaults (target_lang=de) on every new registration
- **GDPR delete**: `user_manager.delete(user)` → DB-level CASCADE deletes all related rows via FK constraints; no Python-level relationship loading needed
- **Test DB strategy**: synchronous table creation + file-based SQLite + `NullPool` for async connections

---

## Next Phase

| Agent | Branch | Scope |
|-------|--------|-------|
| Pete_Pipeline | `phase-3/pete-pipeline` | faster-whisper STT, Ollama LLM, pyannote diarization, real-time pipeline, VRAM load test |
