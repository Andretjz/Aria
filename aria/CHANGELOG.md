# Changelog

All notable changes to Aria are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Semantic versioning: MAJOR.MINOR.PATCH.

## [Unreleased]

### Added (Phase 1 — Sam_Architect)

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
