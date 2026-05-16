# Aria — Conversational Language Learning Platform

Practice any of 5 languages (German, English, Spanish, French, Italian) through live AI conversation, spaced repetition flashcards, grammar workshops, and deep audio analysis.

[![CI](https://github.com/Andretjz/Aria/actions/workflows/ci.yml/badge.svg)](https://github.com/Andretjz/Aria/actions)

## What Aria Does

| Module | Description |
|---|---|
| 💬 Live Conversation | Speak → real-time STT → Aria responds → TTS voice → post-session analysis |
| 📊 Session Analysis | 6-pass pipeline: transcript, speaker ID, grammar heatmap, 10-question quiz, fluency score |
| 🃏 Flashcards | SM-2 spaced repetition — auto-populated from session vocabulary |
| 📄 Text Practice | Upload PDF/TXT/DOCX → translation → vocabulary quiz → grammar patterns |
| 🔧 Grammar Workshop | Aggregated deficit tracking across sessions → targeted exercises |
| 👤 Auth & Accounts | Optional account — app fully usable anonymously |

## Quick Start (Dev)

```bash
git clone https://github.com/Andretjz/Aria.git && cd Aria/aria
cp .env.example .env            # fill in HF_TOKEN at minimum
ollama pull llama3.1:8b
docker compose -f docker-compose.dev.yml up
# → http://localhost:5173 (frontend)
# → http://localhost:8000/api/health (backend)
```

## Tech Stack

**Backend**: FastAPI + Uvicorn · SQLAlchemy 2.x async · Alembic · Redis · FastAPI-Users

**Frontend**: React 18 + TypeScript · Vite · Zustand · shadcn/ui · Tailwind CSS · Recharts

**Dev ML**: faster-whisper (STT) · Ollama llama3.1:8b (LLM) · Piper TTS · pyannote (diarization)

**Prod ML**: Gladia WebSocket STT · Claude Haiku/Sonnet API · ElevenLabs TTS · Helsinki-NLP translation

**Infrastructure**: Fly.io (backend) · Vercel (frontend) · Supabase (PostgreSQL) · Upstash (Redis) · Cloudflare R2 (audio)

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full system diagram and data flows.
See [docs/adr/](docs/adr/) for all architectural decisions (ADR-001 through ADR-010).

## Development

See [docs/development.md](docs/development.md) for prerequisites, setup, and testing instructions.

## Configuration

See [docs/configuration.md](docs/configuration.md) for all environment variables.

## Languages Supported

**Target languages** (full curriculum, CEFR vocabulary, grammar rules): 🇩🇪 German · 🇬🇧 English · 🇪🇸 Spanish · 🇫🇷 French · 🇮🇹 Italian

**Input languages** (any language Deepgram/Whisper recognises — 40+ in production)

## License

MIT
