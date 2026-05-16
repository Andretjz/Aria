# Aria — Local Development Guide

_Last updated: 2026-05-16 by Sam_Architect_

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | python.org |
| Node.js | 20+ | nodejs.org |
| Docker Desktop | Latest | docker.com |
| NVIDIA GPU drivers | Latest | nvidia.com |
| CUDA Toolkit | 12.1+ | developer.nvidia.com |
| Ollama | Latest | ollama.ai |
| GitHub CLI | Latest | cli.github.com |

## First-time Setup

```bash
# 1. Clone the repo
git clone https://github.com/Andretjz/Aria.git
cd Aria/aria

# 2. Pull the Ollama model (dev LLM)
ollama pull llama3.1:8b

# 3. Copy env template and fill in your tokens
cp .env.example .env
# Edit .env: set HF_TOKEN (required for pyannote diarization)

# 4. Start Docker Compose (backend + frontend + Redis + Postgres)
docker compose -f docker-compose.dev.yml up

# 5. Verify health
curl http://localhost:8000/api/health
```

## Running Tests

```bash
# Backend unit tests (no GPU required)
cd aria/backend
pip install -r requirements.txt
pytest tests/ -v --cov=. --cov-report=term-missing

# Frontend tests
cd aria/frontend
npm install
npm run test:run

# Audio integration test (inside running backend container)
docker exec -it aria-backend bash
curl -X POST http://localhost:8000/api/v1/sessions/analyze \
  -F "audio=@/test-audio/Trimmed/6_5min_trimmed.m4a" \
  -F "language=de" -F "context=interview" \
  -F "hf_token=${HF_TOKEN}" \
  --max-time 180 | python3 -m json.tool | head -80
```

## VRAM Budget (RTX 4070 Ti — 12GB)

| Model | VRAM | Notes |
|---|---|---|
| faster-whisper large-v3-turbo | ~3.0 GB | Dev STT |
| LLaMA 3.1 8B Q4_K_M (Ollama) | ~5.0 GB | Dev LLM |
| SpeechBrain wav2vec2-IEMOCAP | ~0.5 GB | Dev tone |
| Silero VAD | ~0.1 GB | Dev VAD |
| pyannote diarization | ~1.1 GB | Released after Pass 2 |
| CUDA overhead | ~0.8 GB | Always |
| **Peak total** | **~10.5 GB** | Within 12GB ✓ |

## Environment Variables

See [docs/configuration.md](configuration.md) for the full reference.

## Branching

- `main` — protected, CI must pass, only merges via PR after Claude APPROVED
- `phase-{N}/{agent-name}` — one branch per agent per phase
- Never commit directly to `main`

## Commit Format

```
feat(scaffold): initialize FastAPI app with health endpoint and CORS
```

Scopes: `scaffold`, `auth`, `pipeline`, `conversation`, `analysis`, `flashcards`, `frontend`, `devops`, `qa`, `cloud`
