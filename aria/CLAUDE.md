# Aria — Living Project Context

Last updated by: Sam_Architect on 2026-05-16

## Project State

Phase 1 complete (Sam_Architect scaffold). Gate 1 pending Opus approval.
Phase 2 (Anna_Auth + Pete_Pipeline) not yet started.

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
- [ ] Auth (Anna_Auth — Phase 2)
- [ ] ML pipeline implementations (Pete_Pipeline — Phase 3)
- [ ] Live conversation (Carlos_Conversation — Phase 4)
- [ ] Full analysis + language features (Alice_Analysis — Phase 5)
- [ ] Flashcards SM-2 (Felix_Flashcards — Phase 5)
- [ ] Full frontend UI (Fiona_Frontend — Phase 7)
- [ ] Cloud deployment (Dmitri_DevOps — Phase 8)
- [ ] Monetization (Anna_Auth — Phase 9)

## API Endpoints (current)

```
GET  /api/health                      → status, version, GPU info, Ollama status
POST /api/v1/sessions/analyze         → STUB (Phase 2 Pete, Phase 5 Alice)
POST /api/v1/conversations/           → STUB (Phase 4 Carlos)
WS   /ws/v1/conversation/{id}         → STUB (Phase 4 Carlos)
POST /api/v1/auth/register            → STUB (Phase 2 Anna)
POST /api/v1/auth/login               → STUB (Phase 2 Anna)
GET  /api/v1/auth/me                  → STUB (Phase 2 Anna)
GET  /api/v1/auth/me/export           → STUB (Phase 6 Anna)
DELETE /api/v1/auth/me                → STUB (Phase 6 Anna)
GET  /api/v1/flashcards/due           → STUB (Phase 5 Felix)
POST /api/v1/flashcards/review        → STUB (Phase 5 Felix)
POST /api/v1/flashcards/generate      → STUB (Phase 5 Felix)
GET  /api/v1/grammar/deficits         → STUB (Phase 5 Alice)
POST /api/v1/text-practice/upload     → STUB (Phase 5 Alice)
```

## Database Schema (current)

Tables: none yet (Alembic migrations pending Phase 2)
Pending: User, OAuthAccount, UserSession, UserPreferences (Anna_Auth Phase 2)

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

## Open Questions for Claude (Gate 1)

None — Sam_Architect's scaffold is self-contained. All open questions are Phase 2+ scope.

## Next Agent

Phase 2: Anna_Auth + Pete_Pipeline (same phase, same branch or separate feature branches within phase-2/)
