# Changelog

All notable changes to Aria are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Semantic versioning: MAJOR.MINOR.PATCH.

## [Unreleased]

### Added (Gate 10 — Anna_Auth: billing hardening, 2026-05-17)

- Automatic payment methods — removed `payment_method_types=["card"]` hard-code; Stripe dashboard now controls accepted methods (Visa, Mastercard, Apple Pay, Google Pay, SEPA, iDEAL, etc.)
- 14-day free trial on Pro checkout — `subscription_data={"trial_period_days": 14}`; credit card required upfront via `payment_method_collection="always"`; complies with German §355 BGB EU 14-day withdrawal right
- Correct `trialing` status — `checkout.session.completed` webhook now sets `status="trialing"` when `payment_status == "no_payment_required"`, `status="active"` when `payment_status == "paid"`; `UserSubscription.is_pro` returns `True` for both `active` and `trialing` Pro plans
- 4 new billing tests: `TestTrialAndPaymentMethods` class (277/277 passing)
- Fly.io Linux deployment — resolves Supabase IPv6 DNS issue that blocked Windows; Alembic migrations applied against Supabase PostgreSQL; `user_subscriptions` table created in production

### Fixed (Gate 10)

- `parselmouth==0.4.4` → `praat-parselmouth==0.4.4` in `requirements.txt` (wrong PyPI package name; correct Praat voice analysis library preserved for future voice feature)
- FastAPI 0.115.x compatibility: `POST /logout` and `DELETE /me` decorators now use `response_model=None` to satisfy strict 204-no-body assertion introduced in FastAPI 0.115.4

---

### Added (Gate 9 — Anna_Auth: Stripe monetization, 2026-05-16)

- `UserSubscription` ORM model (`user_subscriptions` table) — `plan` (free/pro), `status`, `stripe_customer_id`, `stripe_subscription_id`, `current_period_end`, `is_pro` property (True for active/trialing Pro)
- Billing endpoints: `GET /api/v1/billing/subscription`, `POST /api/v1/billing/checkout`, `POST /api/v1/billing/portal`, `POST /api/v1/billing/webhook`
- Stripe Checkout session (mode=subscription) for Free→Pro upgrade; Stripe Billing Portal for subscription management
- Webhook handler: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted` — all signature-verified when `STRIPE_WEBHOOK_SECRET` set
- Auth enforcement across all modules — `current_active_user` dependency added to every protected endpoint
- Free-tier quota guards: `check_daily_conversations` (3/day), `check_daily_analysis` (3/day), `check_flashcard_limit` (50 cards); all no-op for Pro users
- User-scoped queries — flashcard stats/due/review, grammar deficits, conversation and analysis sessions now filtered by `user_id`
- Config: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `FREE_DAILY_CONVERSATIONS=3`, `FREE_DAILY_TEXT_UPLOADS=1`, `FREE_MAX_FLASHCARDS=50`
- Test fixtures: `MOCK_USER`, `authed_client` (quota bypassed), `quota_authed_client` (quota enforced); 40 new billing/auth/quota tests (273/273 passing)

---

### Added (Gate 8 — Dmitri_DevOps: cloud deployment, 2026-05-16)

- Production Dockerfile (`aria/backend/Dockerfile`) — `python:3.11-slim`, CPU-only, non-root `aria` user, ffmpeg + libsndfile1 + curl, `EXPOSE 8000`, health check targeting `/api/health`
- `fly.toml` — Frankfurt region (`fra`), 2 shared CPUs / 4 GB RAM, HTTPS enforced, auto-stop/start machines, `min_machines_running=1`, health check at `/api/health`
- `frontend/vercel.json` — `/api/*` proxy rewrite to Fly.io backend (same-origin cookies), SPA fallback, security headers (X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy)
- `VITE_WS_URL` env var in `src/api/conversation.ts` — WebSocket connects directly to `wss://aria-backend.fly.dev` in production (Vercel cannot proxy WebSocket)
- CD workflow (`.github/workflows/deploy.yml`) — push-to-main trigger, `flyctl deploy` + Vercel CLI, `smoke-test` job checks `/api/health`, `needs: deploy-backend` ordering
- Locust load test (`aria/locustfile.py`) — `AriaUser` tasks: health (×3), get_me (×3), flashcard_stats (×2), due_cards (×2), grammar_deficits (×1); p95 < 5 s at 10 users
- 19 new deployment tests (233/233 passing)

---

### Added (Gate 7 — Fiona_Frontend: full React/TypeScript UI, 2026-05-16)

- Typed API client layer (`src/api/`) — `client.ts`, `auth.ts`, `analysis.ts`, `conversation.ts`, `flashcards.ts`, `grammar.ts`, `textPractice.ts`; all types match backend Pydantic schemas
- Zustand stores — `authStore.ts` (user, loading), `conversationStore.ts` (sessionId, language, messages, status)
- Navigation and layout — `Nav.tsx` (7 links, active-link highlight, lucide-react icons), `Layout.tsx` (max-width container)
- Full page implementations: `HomePage` (hero + 6-module card grid), `AuthPage` (sign-in/register tabs, HttpOnly cookie auth), `AnalysisPage` (file upload, transcript, quiz, grammar spotlights, voice blueprints), `ConversationPage` (5-language selector, WebSocket state machine, chat list), `GrammarPage` (deficits list), `TextPracticePage` (PDF/TXT/DOCX upload, CEFR vocab badges, quiz), `FlashcardsPage` (SM-2 card flip, quality 0–5 buttons, stats bar)
- Accessibility — all interactive elements ≥ 44 px, `aria-label` on all controls, `aria-live="polite"` on conversation list, `role="alert"` for errors
- `@testing-library/jest-dom` added to devDependencies (was missing from Phase 1 scaffold)
- 70 vitest frontend tests (70/70 passing)

---

### Added (Gate 6 — Felix_Flashcards: SM-2 spaced repetition, 2026-05-16)

- `FlashcardDeck`, `Flashcard`, `FlashcardReview` ORM models (`flashcard_decks`, `flashcards`, `flashcard_reviews` tables); `FlashcardReview` has `UniqueConstraint("flashcard_id")` — one SM-2 state per card
- SM-2 algorithm (`apply_sm2`) — quality 0–5, ease factor (min 1.3), intervals: 1 → 6 → `interval × ease_factor`; resets on quality < 3
- Flashcard endpoints: `POST /api/v1/flashcards/generate` (201, creates deck + cards + SM-2 init), `GET /api/v1/flashcards/due` (cards with `next_review ≤ today`), `POST /api/v1/flashcards/review` (SM-2 update, 404 on unknown card), `GET /api/v1/flashcards/stats` (total, due, mastered ≥ 21-day interval)
- Alembic migration `005_create_flashcard_tables.py`
- 47 new flashcard tests (214/214 passing)

---

### Added (Gate 5 — Alice_Analysis: comprehension quiz, grammar spotlight, voice blueprints, text practice, 2026-05-16)

- Comprehension quiz generator (`modules/analysis/quiz.py`) — LLM produces 3 multiple-choice questions per transcript; soft-fails to `[]` on empty input or LLM error
- Grammar spotlight (`modules/analysis/grammar.py`) — LLM identifies top-5 grammar patterns; capped at 5 items
- Voice blueprints (`modules/analysis/voice_blueprint.py`) — pure Python, per-speaker: `tempo_wpm`, `filler_word_count` (5 languages), `vocabulary_richness` (type-token ratio)
- Extended `AnalysisSession` columns: `quiz_json`, `grammar_json`, `voice_blueprints_json` (all nullable, backward-compatible)
- Extended `AnalysisSessionRead` schema: `quiz`, `grammar_spotlights`, `voice_blueprints` (all default `[]`)
- 6-pass pipeline: STT → diarization → speaker assignment → LLM fluency/vocab → quiz → grammar → voice blueprints (passes 5–6 soft-fail)
- `GET /api/v1/grammar/deficits` — aggregates top-5 grammar rules by frequency across all sessions; skips NULL/malformed rows
- `POST /api/v1/text-practice/upload` — PDF/TXT/DOCX (10 MB limit); PyPDF + python-docx extraction; LLM returns detected language, CEFR vocabulary, quiz, grammar spotlights; DeepL translation (skipped for same-language)
- Alembic migration `004_extend_analysis_tables.py`; dependencies: `pypdf==5.4.0`, `python-docx==1.1.2`
- 54 new analysis/text-practice tests (167/167 passing)

---

### Added (Gate 4 — Carlos_Conversation: WebSocket, VAD, turn detection, 2026-05-16)

- `EnergyVAD` — RMS-based voice activity detection (threshold 300.0 / 32767 scale, 500 ms silence window); `process_chunk` returns `True` exactly once per utterance end; `reset()` called after each turn
- `ConversationEngine` — dependency-injected (stt, llm, tts); `process_turn`: STT (temp-file batch) → send transcript JSON → LLM streaming → TTS streaming → send `turn_end`
- `ConversationSession` ORM model (`conversation_sessions` table) — `language`, `status`, `turn_count`, `transcript_json`, `ended_at`
- REST endpoint: `POST /api/v1/conversations/` — creates session (201); language validation (de/en/es/fr/it)
- WebSocket endpoint: `WS /ws/v1/conversation/{session_id}` — binary audio accumulation → VAD trigger → turn cycle; text control messages (`start`, `stop`); UUID validation; graceful `finally` teardown
- Alembic migration `003_create_conversation_tables.py`
- 43 new conversation tests; `TestWebSocket` uses mock DB to avoid SQLite write-lock contention (213/213 passing with prior phases)

---

### Added (Gate 3 — Pete_Pipeline: STT, diarization, speaker assignment, LLM analysis, 2026-05-16)

- `FasterWhisperSTTService` — lazy model load, GPU/CPU, word timestamps, `transcribe_file` + `transcribe_stream`
- `OllamaLLMService` — streaming via `/api/chat`, `is_available()` health check
- `PyannoteService` — lazy pipeline load, GPU optional, `flush_gpu()` in `finally`
- `ClaudeLLMService` — Anthropic streaming with `cache_control` on system prompts
- `AnalysisPipeline` — dependency-injected; 4-pass: STT (hard fail) → diarization (soft fail → single speaker) → max-overlap speaker assignment → LLM fluency+vocab (soft fail)
- `AnalysisSession` ORM model (`analysis_sessions` table) — `audio_filename`, `language`, `duration_seconds`, `num_speakers`, `transcript_json`, `vocabulary_json`, `fluency_score`
- `POST /api/v1/sessions/analyze` — file-size (413) + extension (422) validation; temp-file pipeline; persists `AnalysisSession`; `get_pipeline()` dependency overridable in tests
- Alembic migration `002_create_analysis_tables.py`
- 34 new pipeline tests (70/70 passing with prior phases)

---

### Added (Gate 2 — Anna_Auth: JWT auth, user model, GDPR endpoints, 2026-05-16)

- `User`, `OAuthAccount`, `UserPreferences`, `UserSession` ORM models; all FK constraints use `ondelete="CASCADE"`
- FastAPI-Users setup — `CookieTransport` (`aria_access` HttpOnly, 15 min JWT), rotating refresh token (`aria_refresh` HttpOnly, 7 days, path-scoped to `/api/v1/auth`), `UserManager.on_after_register` creates default `UserPreferences`
- Auth endpoints: `POST /register` (201), `POST /login` (JWT + refresh cookie, `UserWithPreferencesRead`), `POST /logout` (revoke session, clear cookies, 204), `POST /refresh` (token rotation), `GET /me`, `PATCH /me/preferences`, `GET /me/export` (GDPR Art. 20), `DELETE /me` (GDPR Art. 17, DB-cascade delete)
- Security: dual-token pattern; refresh tokens stored as SHA-256 hash only; uniform 401 for unknown email and wrong password (no enumeration); `is_active` check on every request
- Alembic migration `001_create_auth_tables.py` — `user`, `oauth_account`, `user_preferences`, `user_sessions`
- Test infrastructure: file-based SQLite (`aria_test.db`) + `NullPool` for async; synchronous table creation avoids aiosqlite daemon-thread lock conflict
- 24 new auth tests (36/36 passing with Phase 1)

---

### Added (Gate 1 — Sam_Architect)

- Monorepo structure: `aria/backend/` + `aria/frontend/`
- Docker Compose dev stack (backend, frontend, Redis, Postgres) with test-audio volume mount
- FastAPI skeleton with health endpoint (`GET /api/health`)
- All 6 module routers registered with `/api/v1/` prefix (stubs — implementations in later phases)
- SQLAlchemy 2.x async engine + Alembic migration config
- React 18 + TypeScript + Vite frontend scaffold with all 6 module pages (stubs)
- GitHub Actions CI: lint → pytest → vitest → Docker build
- `core/config.py` — all env vars typed, documented (Pydantic Settings)
- `core/constants.py` — ported from Transcribit v6: STOP_WORDS, NAME_BLOCKLIST, NAME_PATTERNS, ENGLISH_IN_GERMAN
- `core/exceptions.py` — AriaError hierarchy (STTError, LLMError, TTSError, etc.)
- `core/logging.py` — structured JSON logging (structlog), console output in DEBUG
- `core/gpu.py` — flush_gpu(), vram_free_gb(), gpu_info() ported from Transcribit
- `core/llm_utils.py` — parse_json_from_llm() ported from Transcribit
- `services/interfaces.py` — abstract base classes: STTService, LLMService, TTSService, DiarizationService, TranslationService
- `services/factory.py` — .env-driven provider factory (ADR-003)
- All provider stubs: FasterWhisperSTTService, DeepgramSTTService, OllamaLLMService, ClaudeLLMService, PiperTTSService, ElevenLabsTTSService, OpenAITTSService, PyannoteService, DeepgramDiarizationService, HelsinkiTranslationService, DeepLTranslationService
- ADR-001 through ADR-010
- docs/architecture.md, docs/development.md, docs/configuration.md
- CONTRIBUTING.md, README.md, .env.example, CLAUDE.md
- Tailwind CSS config with Aria design tokens (Syne + JetBrains Mono fonts, colour palette)

## [0.0.0] — 2026-05-16

- Initial repo created: Andretjz/Aria (public)
- Main branch protected (CI required: ci/pytest, ci/vitest)
- Phase 1 branch created: phase-1/sam-architect
