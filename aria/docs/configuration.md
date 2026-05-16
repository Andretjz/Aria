# Aria — Configuration Reference

_Last updated: 2026-05-16 by Sam_Architect_

All configuration is managed through environment variables defined in `aria/backend/core/config.py` (Pydantic Settings). Copy `.env.example` to `.env` and fill in your values.

## Required (Dev Minimum)

| Variable | Type | Default | Description |
|---|---|---|---|
| `HF_TOKEN` | str | `""` | HuggingFace token for pyannote/3.1 diarization model download |

## Required (Production)

| Variable | Type | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | str | Claude API key (LLM_BACKEND=claude) |
| `GLADIA_API_KEY` | str | Gladia streaming STT (STT_BACKEND=gladia) |
| `DEEPGRAM_API_KEY` | str | Deepgram batch STT + fallback (STT_BACKEND=deepgram) |
| `ELEVENLABS_API_KEY` | str | ElevenLabs TTS for Pro users (TTS_BACKEND=elevenlabs) |
| `SECRET_KEY` | str | JWT signing secret — `openssl rand -hex 32` |
| `DATABASE_URL` | str | PostgreSQL connection string (Supabase) |
| `REDIS_URL` | str | Upstash serverless Redis URL |

## Service Backend Selection

| Variable | Values | Default | Description |
|---|---|---|---|
| `STT_BACKEND` | `local` / `deepgram` / `gladia` | `local` | STT provider |
| `LLM_BACKEND` | `ollama` / `claude` | `ollama` | LLM provider |
| `TTS_BACKEND` | `piper` / `elevenlabs` / `openai` | `piper` | TTS provider |
| `DIAR_BACKEND` | `local` / `deepgram` / `gladia` | `local` | Diarization provider |

## Feature Flags

| Variable | Type | Default | Description |
|---|---|---|---|
| `FEATURE_ELEVENLABS_TTS` | bool | `false` | Enable ElevenLabs for Pro users |
| `FEATURE_GRAMMAR_WORKSHOP` | bool | `true` | Grammar Workshop module |
| `FEATURE_TEXT_UPLOAD` | bool | `true` | Text Practice (Module 4) |
| `FEATURE_FLASHCARDS` | bool | `true` | Flashcards module |
| `FEATURE_SESSION_REPLAY` | bool | `false` | Pro: session audio replay |
| `FEATURE_TEAM_DASHBOARD` | bool | `false` | Enterprise: team dashboard |

## Environment Files

| File | Purpose |
|---|---|
| `.env` | Local development overrides (not committed) |
| `.env.example` | Template with all variables documented (committed) |

## Dev vs Production Settings

```bash
# .env.development (used by Docker Compose)
STT_BACKEND=local
LLM_BACKEND=ollama
TTS_BACKEND=piper
DIAR_BACKEND=local
OLLAMA_URL=http://host.docker.internal:11434

# .env.production (used by Fly.io secrets)
STT_BACKEND=gladia
STT_FALLBACK=deepgram
LLM_BACKEND=claude
TTS_BACKEND=elevenlabs
DIAR_BACKEND=gladia
```
