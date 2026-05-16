# Aria — Living Project Context

Last updated by: Anna_Auth on 2026-05-16

## Project State

Phase 1 complete (Sam_Architect scaffold). Gate 1 APPROVED.
Phase 2 (Anna_Auth) complete. Gate 2 APPROVED — 36/36 tests.
Phase 3 (Pete_Pipeline) complete. Gate 3 APPROVED — 70/70 tests.
Phase 4 (Carlos_Conversation) complete. Gate 4 APPROVED — 113/113 tests.
Phase 5 (Alice_Analysis) complete. Gate 5 APPROVED — 167/167 tests.
Phase 6 (Felix_Flashcards) complete. Gate 6 APPROVED — 214/214 tests.
Phase 7 (Fiona_Frontend) complete. Gate 7 APPROVED — 70/70 vitest tests.
Phase 8 (Dmitri_DevOps) complete. Gate 8 APPROVED — 233/233 pytest + 70/70 vitest tests.
Phase 9 (Anna_Auth) complete. Gate 9 APPROVED — 273/273 pytest tests.

## What's Been Built

- [x] Andretjz/Aria public repo created, main branch protected
- [x] Monorepo structure: `aria/backend/` + `aria/frontend/`
- [x] Docker Compose dev stack (4 services: backend, frontend, Redis, Postgres)
- [x] Test audio volume mounted read-only at `/test-audio`
- [x] FastAPI skeleton with health endpoint + all module router stubs
- [x] SQLAlchemy async engine + Alembic config
- [x] React 18 + TypeScript + Vite scaffold with all 6 module pages (stubs)
- [x] GitHub Actions CI (lint → pytest → vitest → Docker build)
- [x] `core/config.py` — all env vars typed, documented
- [x] `core/constants.py` — ported from Transcribit v6 (STOP_WORDS, NAME_BLOCKLIST, etc.)
- [x] `core/exceptions.py` — full exception hierarchy
- [x] `core/logging.py` — structured JSON logging (structlog)
- [x] `core/gpu.py` — flush_gpu(), vram_free_gb(), gpu_info()
- [x] `core/llm_utils.py` — parse_json_from_llm() ported from Transcribit
- [x] `services/interfaces.py` — STTService, LLMService, TTSService, DiarizationService, TranslationService (abstract)
- [x] `services/factory.py` — .env-driven provider selection
- [x] All provider stubs (importable; Pete_Pipeline fills implementations in Phase 3)
- [x] ADR-001 through ADR-010
- [x] docs/architecture.md, docs/development.md, docs/configuration.md
- [x] CONTRIBUTING.md, CHANGELOG.md, README.md, .env.example
- [x] Auth (Anna_Auth — Phase 2) — JWT, User model, GDPR endpoints, Gate 2 APPROVED
- [x] ML pipeline (Pete_Pipeline — Phase 3) — STT, diarization, speaker assignment, LLM analysis, Gate 3 APPROVED
- [x] Live conversation (Carlos_Conversation — Phase 4) — WebSocket, VAD, turn detection, STT→LLM→TTS cycle, Gate 4 APPROVED
- [x] Full analysis + language features (Alice_Analysis — Phase 5) — comprehension quiz, grammar spotlight, voice blueprints, grammar deficits, text practice upload, Gate 5 APPROVED
- [x] Flashcards SM-2 (Felix_Flashcards — Phase 6) — SM-2 spaced repetition, flashcard deck/card/review ORM, generate/due/review/stats endpoints, Gate 6 APPROVED
- [x] Full frontend UI (Fiona_Frontend — Phase 7) — React/TypeScript UI for all 6 modules, typed API client layer, Zustand stores, Nav/Layout, 70/70 vitest tests, Gate 7 APPROVED
- [x] Cloud deployment (Dmitri_DevOps — Phase 8) — production Dockerfile (CPU-only/slim), Fly.io (fra, 2 CPU/4 GB), Vercel SPA+proxy, deploy.yml CD workflow, Locust load test, Gate 8 APPROVED
- [x] Monetization (Anna_Auth — Phase 9) — Stripe subscriptions, Free/Pro tier enforcement, auth scope across all modules, Gate 9 APPROVED

## API Endpoints (current)

```
GET  /api/health                      → status, version, GPU info, Ollama status
POST /api/v1/sessions/analyze         → LIVE — upload audio → 6-pass analysis (transcript, fluency, vocab, quiz, grammar, blueprints)
GET  /api/v1/grammar/deficits         → LIVE — top-5 grammar errors aggregated across sessions
POST /api/v1/text-practice/upload     → LIVE — upload PDF/TXT/DOCX → translation, CEFR vocab, quiz, grammar
POST /api/v1/conversations/           → LIVE — create session (Phase 4 Carlos)
WS   /ws/v1/conversation/{id}         → LIVE — live turn cycle (Phase 4 Carlos)
POST /api/v1/auth/register            → LIVE — create account (FastAPI-Users)
POST /api/v1/auth/login               → LIVE — JWT cookie (15 min) + refresh token cookie (7 days)
POST /api/v1/auth/logout              → LIVE — revoke session, clear cookies
POST /api/v1/auth/refresh             → LIVE — rotate refresh token, new access token
GET  /api/v1/auth/me                  → LIVE — current user + language preferences
PATCH /api/v1/auth/me/preferences     → LIVE — update language preferences
GET  /api/v1/auth/me/export           → LIVE — GDPR Article 20 data portability
DELETE /api/v1/auth/me                → LIVE — GDPR Article 17 right to erasure
GET  /api/v1/flashcards/due           → LIVE — cards with next_review <= today, ordered by priority
POST /api/v1/flashcards/review        → LIVE — SM-2 quality rating (0-5), updates interval/ease_factor
POST /api/v1/flashcards/generate      → LIVE — create deck + flashcards from vocabulary list
GET  /api/v1/flashcards/stats         → LIVE — total_cards, cards_due, cards_mastered (interval >= 21)
GET  /api/v1/grammar/exercises/{id}   → STUB (Phase 6+)
GET  /api/v1/billing/subscription     → LIVE — current user's plan/status (Phase 9 Anna_Auth)
POST /api/v1/billing/checkout         → LIVE — create Stripe Checkout session (Pro upgrade)
POST /api/v1/billing/portal           → LIVE — create Stripe Billing Portal session
POST /api/v1/billing/webhook          → LIVE — Stripe webhook handler (sig-verified)
```

## Database Schema (current)

Tables: `user`, `oauth_account`, `user_preferences`, `user_sessions`, `analysis_sessions`, `conversation_sessions`, `flashcard_decks`, `flashcards`, `flashcard_reviews`, `user_subscriptions`
Migrations: `001_create_auth_tables.py`, `002_create_analysis_tables.py`, `003_create_conversation_tables.py`, `004_extend_analysis_tables.py`, `005_create_flashcard_tables.py`

## Environment Variables Required

Minimum for dev: `HF_TOKEN`
Full list: see `aria/.env.example` and `aria/docs/configuration.md`

## Key Decisions Log

- 2026-05-16: STT: Gladia primary (GDPR-native), Deepgram fallback. See ADR-001.
- 2026-05-16: LLM: Ollama (dev), Claude Haiku (prod), Opus for gates. See ADR-002.
- 2026-05-16: Adapter pattern for all external services. See ADR-003.
- 2026-05-16: React + TypeScript over vanilla JS. See ADR-004.
- 2026-05-16: FastAPI over Django/Flask. See ADR-005.
- 2026-05-16: SQLite dev → Supabase PostgreSQL prod. See ADR-006.
- 2026-05-16: Fly.io backend + Vercel frontend. See ADR-007.
- 2026-05-16: SM-2 for spaced repetition (MVP); FSRS deferred. See ADR-008.
- 2026-05-16: Language architecture — any input, 5 targets, independent feedback lang. See ADR-009.
- 2026-05-16: Module isolation boundaries — no cross-module imports. See ADR-010.

## Known Issues / Tech Debt

- Provider stubs in services/providers/ raise NotImplementedError — Pete_Pipeline fills these in Phase 3
- Auth module models.py is empty — Anna_Auth fills these in Phase 2
- Alembic env.py imports auth and flashcard models; both are stubs until Phase 2/5
- structlog dependency must be installed before logging.py can be imported

## Known Issues / Tech Debt (Phase 2 additions)

- `aria_test.db` in `tests/` directory — git-ignored, cleaned up on each test run
- httpx-oauth pinned to 0.15.1 (0.15.2 does not exist on PyPI — requirements.txt corrected)
- OAuth routes (Google, GitHub) not yet implemented — config keys are wired but endpoints are conditional on non-empty CLIENT_ID values

## Known Issues / Tech Debt (Phase 3 additions)

- `analysis_sessions.user_id` is nullable — anonymous sessions allowed in dev; Phase 9 enforces auth + billing per session
- `_analyse_with_llm` uses `json.loads` first, then `parse_json_from_llm` fallback — works correctly but worth consolidating in Phase 5

## Known Issues / Tech Debt (Phase 4 additions)

- `conversation_sessions.user_id` is nullable — anonymous sessions in dev; Phase 9 enforces auth + billing
- VAD is energy-based RMS (no GPU, no Silero); sufficient for dev; swap via `EnergyVAD` subclass in Phase 7+ if needed
- STT uses batch `transcribe_file` per turn (temp-file write + read); streaming STT can be wired via `transcribe_stream` in a future phase
- `TestWebSocket` uses mock DB to avoid SQLite write-lock contention between TestClient thread and pytest-asyncio event loop — real DB persistence is tested only via REST endpoint tests

## Known Issues / Tech Debt (Phase 5 additions)

- `GET /api/v1/grammar/deficits` aggregates across ALL sessions (no user filtering); Phase 9 enforces user-scoped queries once auth is enforced
- Voice blueprints are computed from transcript text (statistical), not raw audio features (prosody, pitch, etc.); upgrade in Phase 7+ if richer voice analysis is needed
- Text practice: `POST /api/v1/text-practice/upload` truncates documents to 8,000 chars before sending to LLM — works for typical articles; long documents need chunking in Phase 6+
- `GET /api/v1/grammar/exercises/{rule_id}` remains a stub — exercises are Phase 6+ scope
- Flashcard deck integration in text practice is deferred to Felix_Flashcards (Phase 6)
- `grammar_json` column is nullable — pre-Phase-5 sessions have NULL; deficits endpoint skips them gracefully
- Pass 5 (quiz + grammar spotlight) makes 2 separate LLM calls per audio analysis; consider batching into one call in Phase 6+ to reduce latency

## Known Issues / Tech Debt (Phase 6 additions)

- `flashcard_decks.user_id` is nullable — anonymous decks in dev; Phase 9 enforces auth + user scoping
- `GET /api/v1/flashcards/due` returns cards for ALL users (no user filtering); Phase 9 adds auth enforcement
- SM-2 ease_factor is never serialised per-user — single review record per card; Phase 9 adds user_id to `flashcard_reviews` when auth is enforced
- Flashcard generation from analysis `vocabulary_json` (list[str]) produces cards with `definition=None`; LLM enrichment deferred to Phase 7+

## Known Issues / Tech Debt (Phase 8 additions)

- Load test (`aria/locustfile.py`) targets the health + read endpoints only; write endpoints (audio upload, text upload, conversation create) require a running ML backend with API keys — excluded from CI load test
- Vercel API proxy adds one extra hop for REST calls; can be eliminated with a custom domain pointing both frontend and `api.` subdomain to respective services (Phase 9+)
- `min_machines_running = 1` prevents full scale-to-zero; revisit after Phase 9 auth enforcement enables per-user session tracking for smarter scale-down

## Known Issues / Tech Debt (Phase 7 additions)

- `@testing-library/jest-dom` was missing from Phase 1 `package.json` — added in Phase 7 devDependencies
- Auth integration is frontend-only (calls API but no token refresh or session persistence on page reload); Phase 9 enforces auth scope across all modules
- Conversation WebSocket uses text-mode only (`type: "text"` JSON frames); voice recording via `MediaRecorder` is wired into the UI skeleton but sending binary audio frames is deferred to Phase 8+
- LLM enrichment for flashcard generation (word → definition via LLM) remains deferred — the generate endpoint accepts `vocabulary: VocabItem[]` but the frontend GenerateDeck UI is not yet exposed; Phase 8 integrates it via the Analysis/TextPractice results flow
- `i18next`/`react-i18next` are in devDependencies from Phase 1 scaffold but not yet wired — UI is English-only; internationalisation deferred to Phase 9

## Next Agent

All phases complete. No further phases defined.
