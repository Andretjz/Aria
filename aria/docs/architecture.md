# Aria — Architecture

_Last updated: 2026-05-16 by Sam_Architect_

## System Overview

Aria is a conversational language learning platform with two deployment phases:

**Phase A — Development** (local GPU): Browser → FastAPI (localhost:8000) → faster-whisper / Ollama / Piper / pyannote
**Phase B — Production** (cloud only): Browser → Vercel (CDN) → Fly.io (FastAPI) → Gladia / Claude API / ElevenLabs / Supabase

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User Device (any)                        │
│  Chrome / Safari / Firefox / Edge — 320px to 2560px        │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS / wss://
┌──────────────────────────▼──────────────────────────────────┐
│              Vercel — React 18 Frontend (global CDN)         │
│  Pages: Home, Conversation, Flashcards, Analysis,           │
│         Grammar, TextPractice, Auth                         │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS / WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│              Fly.io — FastAPI Backend (Frankfurt)            │
│  2 shared CPU / 4GB RAM                                     │
│  ┌─────────────┐  ┌───────────┐  ┌──────────────────────┐  │
│  │ Conversation│  │ Analysis  │  │ Flashcards / Grammar  │  │
│  │   Module    │  │  Module   │  │  / Text Practice      │  │
│  └──────┬──────┘  └─────┬─────┘  └──────────┬───────────┘  │
│         └───────────────┴────────────────────┘              │
│                   Service Layer (adapters)                   │
│  STT: Gladia → Deepgram fallback                           │
│  LLM: Claude Haiku / Sonnet                                │
│  TTS: ElevenLabs (Pro) / OpenAI (Free)                     │
│  Diarization: Gladia built-in                              │
│  Translation: Helsinki-NLP (CPU, offline)                  │
└────┬─────────────────────────────────────────────────────────┘
     │
     ├── Supabase (PostgreSQL 16, Frankfurt)
     ├── Upstash (serverless Redis — session state)
     └── Cloudflare R2 (audio replay — opt-in, 30-day TTL)
```

## Module Boundaries

Each module owns its full vertical slice. See ADR-010 for the isolation rules.

```
aria/backend/
  modules/
    conversation/   — WebSocket session, turn cycle, Aria prompts
    analysis/       — 6-pass pipeline, post-session analysis
    flashcards/     — SM-2 algorithm, card CRUD, deck management
    grammar/        — deficit aggregation, exercise builder
    auth/           — FastAPI-Users, JWT, OAuth2, GDPR endpoints
    text_practice/  — document upload, translation, vocabulary extraction
  services/         — shared adapter layer (STT/LLM/TTS/Diarization/Translation)
  core/             — config, constants, exceptions, logging, gpu, llm_utils
```

## Data Flow — Live Conversation

```
1. Browser captures mic → MediaRecorder → 200ms chunks
2. WebSocket → /ws/v1/conversation/{session_id}
3. Silero VAD detects end-of-turn
4. STTService.transcribe_stream() → partial transcript shown live
5. LLMService.generate() → Aria's response streamed
6. TTSService.synthesise() → audio chunks streamed back
7. Browser plays audio via Web Audio API
8. Session timer expires → ConversationSession.end()
9. Analysis pipeline enqueued → POST /api/v1/sessions/analyze
10. Results returned → analysis screen rendered
```

## Data Flow — Audio Analysis (6 passes)

```
Pass 1: STT — faster-whisper (dev) / Deepgram Nova-3 (prod) → segments
Pass 2: Diarization — pyannote (dev) / Gladia (prod) → speaker labels
Pass 3: Cold-start acoustic — segment_cold_acoustic() → early speaker assignment
Pass 4a: Name resolution — extract_name_evidence() + resolve_names() → speaker names
Pass 4b: LLM correction — build_correction_prompt() → corrected transcript
Pass 5: Voice blueprints — build_voice_blueprints() + detect_denglisch()
Pass 6: Full analysis — build_analysis_prompt() → quiz + grammar + vocabulary
```

## Security Architecture

- JWT access tokens (15 min) + rotating refresh tokens (7 days) in HttpOnly cookies
- CSP + HSTS enforced via Nginx on Fly.io
- Rate limiting: 10 auth req/min per IP (Redis-backed)
- File uploads: MIME validation, 50MB limit, extension whitelist
- GDPR: anonymous mode stores nothing server-side (Redis 24h TTL only)
- Audio: never stored unless opt-in; AES-256 at rest; 30-day auto-delete
- See ADR-003 (adapters), Sasha_Security advisory (Gate 1)

## Technology Stack

See [README.md](../README.md) for the full stack summary.
See [docs/adr/](adr/) for individual architectural decisions.
