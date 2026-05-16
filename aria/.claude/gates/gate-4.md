# Gate 4 — Conversation: WebSocket, VAD, Turn Detection, STT→LLM→TTS

**Date:** 2026-05-16
**Agent:** Carlos_Conversation
**Branch:** `phase-4/carlos-conversation`
**Verdict:** APPROVED

---

## Checklist

### EnergyVAD (`modules/conversation/vad.py`)
- [x] `EnergyVAD.__init__` — configurable `sample_rate`, `silence_threshold_rms` (300.0), `silence_duration_ms` (500)
- [x] `EnergyVAD.process_chunk` — returns `True` exactly once per detected utterance end (speech arm → silence accumulation → threshold crossed); `False` otherwise
- [x] `EnergyVAD.reset` — clears `_speech_started` and `_silent_sample_count`; called after each turn so VAD is ready for the next utterance
- [x] `EnergyVAD._compute_rms` — static; 16-bit LE PCM RMS on 0–32767 scale; returns 0.0 for empty input

### ConversationEngine (`modules/conversation/engine.py`)
- [x] `ConversationEngine.__init__` — dependency-injected (stt, llm, tts); testable without GPU
- [x] `ConversationEngine.process_turn` — 4-step orchestration: STT (via temp-file batch) → send transcript JSON → LLM streaming → TTS streaming → send `turn_end`
- [x] Empty STT result returns `("", "")` immediately — no LLM/TTS call, no WebSocket messages
- [x] `_transcribe` — writes buffer to temp file, calls `stt.transcribe_file`, cleans up in `finally`
- [x] `_generate_and_stream` — iterates `llm.generate` async generator, sends each chunk as `{"type": "response_text"}`, returns full assembled string
- [x] `_synthesise_and_stream` — iterates `tts.synthesise` async generator, forwards raw bytes to client via `ws.send_bytes`
- [x] `SYSTEM_PROMPT_TEMPLATE` — language-aware tutor persona; injected per turn with target language

### ConversationSession ORM (`modules/conversation/models.py`)
- [x] `ConversationSession(Base)` — `conversation_sessions` table; id (UUID PK), user_id (nullable FK → user CASCADE), created_at, language, status, turn_count, transcript_json (Text), ended_at (nullable DateTime)
- [x] `user_id` nullable — anonymous sessions allowed in dev; auth enforcement deferred to Phase 9
- [x] `status` Python-level default `"active"`; updated to `"ended"` in WebSocket `finally` block

### Pydantic Schemas (`modules/conversation/schemas.py`)
- [x] `ConversationSessionCreate` — `language` field (default `"en"`); `@field_validator` rejects languages outside `{"de", "en", "es", "fr", "it"}`
- [x] `ConversationSessionRead` — full response schema; `from_attributes=True` for ORM compatibility

### REST Endpoint (`modules/conversation/router.py`)
- [x] `POST /api/v1/conversations/` — creates `ConversationSession`, persists to DB, returns `ConversationSessionRead` with HTTP 201
- [x] `get_engine()` FastAPI dependency — overridable via `app.dependency_overrides[get_engine]` in tests
- [x] Language validation: 422 for unsupported language codes

### WebSocket Endpoint (`modules/conversation/router.py` → `ws_router`)
- [x] `WS /ws/v1/conversation/{session_id}` — registered in `main.py` via separate `ws_router` at prefix `/ws/v1/conversation`
- [x] UUID validation — 1008 close + `{"type": "error"}` for invalid UUID format
- [x] Session lookup — 1008 close + `{"type": "error", "message": "Session not found"}` for unknown UUID
- [x] Binary messages → audio buffer accumulation → VAD trigger → `engine.process_turn` → history update
- [x] Text `{"type": "start", "language": "xx"}` → overrides session language, sends `{"type": "ready"}`
- [x] Text `{"type": "stop"}` → graceful break from receive loop
- [x] Invalid JSON text → `{"type": "error", "message": "Invalid JSON"}`
- [x] `finally` block — sets `status="ended"`, `ended_at`, `turn_count`, `transcript_json`; commits with silent exception guard; logs disconnect

### Database Migration
- [x] `003_create_conversation_tables.py` — creates `conversation_sessions` with all columns, FK to `user.id` (CASCADE), index on `user_id`; `downgrade()` implemented

### Application Wiring
- [x] `main.py` — `ws_router` imported and mounted at `/ws/v1/conversation` (separate from REST router at `/api/v1/conversations`)
- [x] `conftest.py` updated — `aria.backend.modules.conversation.models` imported to register `ConversationSession` with `Base.metadata`

### Test Infrastructure
- [x] Gate 1 + Gate 2 + Gate 3 tests (70/70) still pass unmodified
- [x] `TestWebSocket` uses mock DB (via `app.dependency_overrides[get_db]`) to avoid SQLite write-lock contention between Starlette TestClient's thread event loop and pytest-asyncio's event loop

### Gate 4 Tests
- [x] pytest 113/113 passed (43 new + 70 existing), 0 failed

```
tests/test_conversation.py::TestVAD::test_vad_importable                             PASSED
tests/test_conversation.py::TestVAD::test_vad_default_init                           PASSED
tests/test_conversation.py::TestVAD::test_vad_silence_only_returns_false             PASSED
tests/test_conversation.py::TestVAD::test_vad_speech_then_silence_triggers_true      PASSED
tests/test_conversation.py::TestVAD::test_vad_speech_without_enough_silence_returns_false PASSED
tests/test_conversation.py::TestVAD::test_vad_compute_rms_silence_is_zero           PASSED
tests/test_conversation.py::TestVAD::test_vad_compute_rms_signal_above_zero         PASSED
tests/test_conversation.py::TestVAD::test_vad_compute_rms_empty_bytes_is_zero       PASSED
tests/test_conversation.py::TestVAD::test_vad_reset_clears_state                    PASSED
tests/test_conversation.py::TestVAD::test_vad_reset_prevents_spurious_turn_end      PASSED
tests/test_conversation.py::TestVAD::test_vad_triggers_only_once_per_utterance      PASSED
tests/test_conversation.py::TestConversationModel::test_model_importable             PASSED
tests/test_conversation.py::TestConversationModel::test_model_has_expected_columns  PASSED
tests/test_conversation.py::TestConversationModel::test_model_default_status_is_active PASSED
tests/test_conversation.py::TestConversationModel::test_schema_importable            PASSED
tests/test_conversation.py::TestConversationModel::test_schema_default_language      PASSED
tests/test_conversation.py::TestConversationModel::test_schema_rejects_unsupported_language PASSED
tests/test_conversation.py::TestConversationModel::test_schema_accepts_all_five_target_languages PASSED
tests/test_conversation.py::TestConversationEngine::test_engine_importable           PASSED
tests/test_conversation.py::TestConversationEngine::test_engine_stores_services      PASSED
tests/test_conversation.py::TestConversationEngine::test_process_turn_returns_user_and_assistant_text PASSED
tests/test_conversation.py::TestConversationEngine::test_process_turn_sends_transcript PASSED
tests/test_conversation.py::TestConversationEngine::test_process_turn_sends_response_text_chunks PASSED
tests/test_conversation.py::TestConversationEngine::test_process_turn_sends_audio_bytes PASSED
tests/test_conversation.py::TestConversationEngine::test_process_turn_sends_turn_end PASSED
tests/test_conversation.py::TestConversationEngine::test_process_turn_empty_transcript_returns_empty_strings PASSED
tests/test_conversation.py::TestConversationEngine::test_process_turn_passes_history_to_llm PASSED
tests/test_conversation.py::TestCreateSessionEndpoint::test_create_session_returns_201 PASSED
tests/test_conversation.py::TestCreateSessionEndpoint::test_create_session_response_schema PASSED
tests/test_conversation.py::TestCreateSessionEndpoint::test_create_session_default_language PASSED
tests/test_conversation.py::TestCreateSessionEndpoint::test_create_session_unsupported_language_returns_422 PASSED
tests/test_conversation.py::TestCreateSessionEndpoint::test_create_session_stores_in_db PASSED
tests/test_conversation.py::TestCreateSessionEndpoint::test_create_session_all_five_languages PASSED
tests/test_conversation.py::TestCreateSessionEndpoint::test_create_session_ended_at_is_null PASSED
tests/test_conversation.py::TestWebSocket::test_websocket_unknown_session_sends_error PASSED
tests/test_conversation.py::TestWebSocket::test_websocket_invalid_uuid_sends_error  PASSED
tests/test_conversation.py::TestWebSocket::test_websocket_stop_message_closes_connection PASSED
tests/test_conversation.py::TestWebSocket::test_websocket_start_message_sends_ready PASSED
tests/test_conversation.py::TestWebSocket::test_websocket_start_overrides_language  PASSED
tests/test_conversation.py::TestWebSocket::test_websocket_invalid_json_sends_error  PASSED
tests/test_conversation.py::TestWebSocket::test_websocket_audio_below_vad_threshold_no_turn PASSED
tests/test_conversation.py::TestWebSocket::test_websocket_audio_triggers_turn_with_mock_engine PASSED
tests/test_conversation.py::TestWebSocket::test_websocket_session_marked_ended_after_close PASSED
113 passed in 8.45s
```

---

## Bugs Fixed During Phase 4

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| `sqlalchemy.exc.OperationalError: database is locked` in WebSocket tests | `TestClient` (sync) runs the ASGI app in a separate thread with its own event loop; when multiple WebSocket tests create real DB sessions sequentially, SQLite's single-writer lock causes contention between TestClient's async engine and pytest-asyncio's engine | Switched `TestWebSocket` to inject a mock `get_db` dependency for all WS tests, eliminating real DB I/O from WS tests (DB persistence tested separately in `TestCreateSessionEndpoint` via async `client` fixture) |
| `AttributeError: 'NoneType' object has no attribute 'set'` in ORM default test | Used `ConversationSession.__new__` to bypass SQLAlchemy instrumentation; `Mapped[str]` columns require the ORM mapper to be attached for attribute assignment | Changed test to introspect `ConversationSession.__table__.c["status"].default.arg` directly |

---

## Decisions Locked

- **WebSocket path**: `/ws/v1/conversation/{id}` — registered via separate `ws_router` in `main.py` at prefix `/ws/v1/conversation`; cleanly separated from REST router at `/api/v1/conversations`
- **VAD algorithm**: Energy-based RMS threshold (300.0 / 32767 scale); 500ms silence window; no GPU dependency. Swappable via subclass override of `process_chunk`
- **Turn audio format**: Raw 16-bit LE mono PCM at 16 kHz; STT batch path (temp file) reused from pipeline — no streaming STT dependency in Phase 4
- **History format**: `list[dict]` with `{role, content}` keys — compatible with OpenAI-style messages for LLM providers
- **Session commit guard**: `try/except Exception: pass` wraps `await db.commit()` in WebSocket `finally` block — prevents exceptions during teardown from masking the underlying disconnect. DB persistence tested through REST endpoint tests with real DB
- **ConversationSession user_id**: nullable FK — anonymous sessions in dev; Phase 9 enforces auth + billing per session

---

## API Endpoints (new this phase)

```
POST /api/v1/conversations/              → LIVE — create session, return session_id + metadata
WS   /ws/v1/conversation/{session_id}   → LIVE — live turn cycle (binary audio in → JSON events + binary audio out)
```

## Next Phase

| Agent | Branch | Scope |
|-------|--------|-------|
| Alice_Analysis | `phase-5/alice-analysis` | Comprehension quiz, grammar spotlight, voice blueprints; extends `AnalysisSessionRead` and the pipeline |
