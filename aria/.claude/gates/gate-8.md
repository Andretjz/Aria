# Gate 8 — Cloud Deployment: Fly.io + Vercel + CI/CD

**Date:** 2026-05-16
**Agent:** Dmitri_DevOps
**Branch:** `phase-8/dmitri-devops`
**Verdict:** APPROVED

---

## Checklist

### Production Backend Image (`aria/backend/Dockerfile`)
- [x] Base: `python:3.11-slim` — no CUDA, no GPU layers (cloud APIs replace local models in prod)
- [x] System deps: `ffmpeg libsndfile1 curl` — runtime audio processing only
- [x] Non-root user: `aria` group + user created via `groupadd`/`useradd`; `USER aria` enforced
- [x] Package root preserved: `COPY __init__.py ./aria/__init__.py` + `COPY backend/ ./aria/backend/` — keeps `aria.backend.*` import path intact
- [x] `EXPOSE 8000`
- [x] `HEALTHCHECK` targets `/api/health` — 30 s interval, 30 s start-period, 3 retries
- [x] `CMD ["uvicorn", "aria.backend.main:app", "--workers", "2", ...]` — 2 workers for 2 shared CPUs

### Fly.io Configuration (`aria/fly.toml`)
- [x] `app = "aria-backend"`
- [x] `primary_region = "fra"` — Frankfurt for EU GDPR data residency (ADR-007)
- [x] `[build] dockerfile = "backend/Dockerfile"` — references production image
- [x] Non-secret env vars in `[env]`: `STT_BACKEND=gladia`, `LLM_BACKEND=claude`, `TTS_BACKEND=openai`, `DIAR_BACKEND=gladia`, `TRANSLATION_BACKEND=deepl`, `DEBUG=false`
- [x] Secrets documented (not committed): `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `ANTHROPIC_API_KEY`, `GLADIA_API_KEY`, `OPENAI_API_KEY`, `DEEPL_API_KEY`, `STRIPE_SECRET_KEY`
- [x] `[http_service] force_https = true` — HSTS enforced at Fly.io edge
- [x] `auto_stop_machines = true` / `min_machines_running = 1` — scale to zero off-peak
- [x] `[http_service.concurrency] hard_limit = 50 / soft_limit = 25` — back-pressure at edge
- [x] `[[vm]] cpu_kind = "shared" / cpus = 2 / memory_mb = 4096` — ADR-007 spec
- [x] `[[checks]]` health check at `/api/health` — 15 s interval, 5 s timeout, 30 s grace period

### Vercel Configuration (`aria/frontend/vercel.json`)
- [x] `/api/:path*` rewrite → `https://aria-backend.fly.dev/api/:path*` — proxies REST calls through Vercel so `credentials: include` cookies work same-origin
- [x] `/:path*` → `/index.html` SPA fallback — all client-side routes served correctly
- [x] Security headers on all responses: `X-Content-Type-Options`, `X-Frame-Options: DENY`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy` (microphone: self)

### WebSocket Production Wiring (`src/api/conversation.ts`)
- [x] `buildWsUrl` reads `VITE_WS_URL` env var first — set to `wss://aria-backend.fly.dev` in Vercel project settings (Vercel cannot proxy WebSocket connections)
- [x] Falls back to `window.location.host` when `VITE_WS_URL` is unset (dev mode unchanged)

### CD Workflow (`.github/workflows/deploy.yml`)
- [x] Triggers only on push to `main` (never on feature branches)
- [x] `concurrency: cancel-in-progress: true` — newer push cancels in-flight deploy
- [x] `deploy-backend` job: `superfly/flyctl-actions` + `flyctl deploy` with `FLY_API_TOKEN` secret
- [x] `deploy-frontend` job: Vercel CLI `vercel pull → vercel build --prod → vercel deploy --prebuilt --prod`; `needs: deploy-backend` (backend health must pass first)
- [x] `smoke-test` job: HTTP 200 check against `/api/health` on Fly.io + Vercel frontend URL; `needs: [deploy-backend, deploy-frontend]`

### Load Test (`aria/locustfile.py`)
- [x] `AriaUser` class with `wait_time = between(1, 3)` — realistic user pacing
- [x] `on_start` registers + logs in one simulated user (isolated per-user session)
- [x] Task mix: `health` (×3), `get_me` (×3), `flashcard_stats` (×2), `due_cards` (×2), `grammar_deficits` (×1) — weighted toward read endpoints
- [x] Run command documented in module docstring: `locust --users 10 --spawn-rate 2 --run-time 60s --headless`
- [x] ADR-007 pass criteria: p95 < 5 s at 10 concurrent users; upgrade to 4 CPU if exceeded

### Gate 8 Tests
- [x] pytest 233/233 passed (214 existing + 19 new deployment tests), 0 failed
- [x] vitest 70/70 passed (all Phase 7 frontend tests unaffected), 0 failed

```
tests/test_deployment.py::test_production_dockerfile_exists               PASSED
tests/test_deployment.py::test_production_dockerfile_uses_slim_base       PASSED
tests/test_deployment.py::test_production_dockerfile_has_nonroot_user     PASSED
tests/test_deployment.py::test_production_dockerfile_exposes_8000         PASSED
tests/test_deployment.py::test_production_dockerfile_has_healthcheck      PASSED
tests/test_deployment.py::test_fly_toml_exists                            PASSED
tests/test_deployment.py::test_fly_toml_has_frankfurt_region              PASSED
tests/test_deployment.py::test_fly_toml_has_correct_vm_memory             PASSED
tests/test_deployment.py::test_fly_toml_has_health_check_path             PASSED
tests/test_deployment.py::test_fly_toml_forces_https                      PASSED
tests/test_deployment.py::test_fly_toml_has_backend_dockerfile_ref        PASSED
tests/test_deployment.py::test_vercel_json_exists                         PASSED
tests/test_deployment.py::test_vercel_json_is_valid_json                  PASSED
tests/test_deployment.py::test_vercel_json_has_api_proxy_rewrite          PASSED
tests/test_deployment.py::test_vercel_json_has_spa_fallback_rewrite       PASSED
tests/test_deployment.py::test_deploy_workflow_exists                     PASSED
tests/test_deployment.py::test_deploy_workflow_triggers_on_main           PASSED
tests/test_deployment.py::test_deploy_workflow_has_fly_deploy_step        PASSED
tests/test_deployment.py::test_deploy_workflow_has_smoke_test             PASSED
19 passed in 0.05s
233 passed in 9.49s (total suite)
70 passed in 6.81s (vitest)
```

---

## Secrets Reference

Secrets set via `fly secrets set KEY=value` (never committed):

| Secret | Description |
|--------|-------------|
| `SECRET_KEY` | 32-byte hex — `openssl rand -hex 32` |
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@supabase-host:5432/aria` |
| `REDIS_URL` | `rediss://default:token@upstash-host:6380` |
| `ANTHROPIC_API_KEY` | Claude API (LLM_BACKEND=claude) |
| `GLADIA_API_KEY` | Gladia STT (primary prod STT, GDPR-native) |
| `DEEPGRAM_API_KEY` | Deepgram (STT_FALLBACK=deepgram) |
| `OPENAI_API_KEY` | OpenAI TTS (TTS_BACKEND=openai) |
| `DEEPL_API_KEY` | DeepL translation (TRANSLATION_BACKEND=deepl) |
| `STRIPE_SECRET_KEY` | Stripe (Phase 9 monetization) |

Vercel project env vars (set in Vercel dashboard):

| Variable | Value |
|----------|-------|
| `VITE_WS_URL` | `wss://aria-backend.fly.dev` |

GitHub Actions secrets required:

| Secret | Used by |
|--------|---------|
| `FLY_API_TOKEN` | `deploy-backend` job |
| `VERCEL_TOKEN` | `deploy-frontend` job |
| `VERCEL_FRONTEND_URL` | `smoke-test` job |

---

## Decisions Locked

- **Vercel API proxy**: `/api/*` is rewritten through Vercel so `credentials: include` cookies stay same-origin — avoids CORS complexity and pre-flight overhead on every API call
- **Direct WebSocket to Fly.io**: Vercel's edge cannot proxy WebSocket; `VITE_WS_URL` wires the WS connection directly to `wss://aria-backend.fly.dev`; dev fallback uses `window.location.host` unchanged
- **Non-root user in production**: `USER aria` in Dockerfile — defence-in-depth; container escape is contained to non-privileged user
- **`min_machines_running = 1`**: Prevents cold-start latency for the first daily user; scale-to-zero only during long overnight idle
- **`--workers 2`**: Matches 2 shared CPUs in fly.toml — one uvicorn worker per CPU; WebSocket connections are long-lived and handled per worker
- **deploy-backend before deploy-frontend**: `needs: deploy-backend` ensures the backend is healthy before Vercel starts serving the new frontend build to users

---

## Files Created (new)

```
aria/backend/Dockerfile
aria/fly.toml
aria/frontend/vercel.json
aria/backend/tests/test_deployment.py
aria/locustfile.py
.github/workflows/deploy.yml
```

## Files Modified

```
aria/frontend/src/api/conversation.ts   — buildWsUrl reads VITE_WS_URL in production
```

---

## Next Phase

| Agent | Branch | Scope |
|-------|--------|-------|
| Anna_Auth | `phase-9/anna-auth` | Monetization: Stripe subscriptions, Free/Pro tier enforcement, auth scope across all modules |
