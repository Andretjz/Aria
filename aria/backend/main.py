"""Aria FastAPI application entry point.

All routers are registered here with versioned prefixes (/api/v1/).
WebSocket routes use /ws/v1/ prefix. Breaking changes add /api/v2/ alongside
v1 (never remove v1 within a major version cycle). See ADR-005.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from aria.backend.core.config import settings
from aria.backend.core.gpu import gpu_info
from aria.backend.core.logging import get_logger

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup + shutdown hooks."""
    log.info(
        "aria_starting",
        version=settings.APP_VERSION,
        stt_backend=settings.STT_BACKEND,
        llm_backend=settings.LLM_BACKEND,
        tts_backend=settings.TTS_BACKEND,
    )

    if settings.DEBUG:
        from aria.backend.database import create_tables
        await create_tables()
        log.info("dev_tables_created")

    gpu = gpu_info()
    if gpu["available"]:
        log.info("gpu_detected", name=gpu["name"], total_gb=gpu["total_gb"])
    else:
        log.info("gpu_not_available", note="CPU mode — production or dev without CUDA")

    yield

    log.info("aria_stopping")


app = FastAPI(
    title="Aria — Conversational Language Learning Platform",
    version=settings.APP_VERSION,
    description=(
        "Aria helps learners practice any of 5 target languages (de/en/es/fr/it) "
        "through live conversation, flashcards, grammar workshops, and audio analysis. "
        "All feedback delivered in the user's preferred language."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health endpoint ───────────────────────────────────────────────────────────

@app.get(
    "/api/health",
    summary="Health check",
    description=(
        "Returns application status, version, active service backends, "
        "and GPU information (dev only). Used by Docker health checks and CI."
    ),
    tags=["system"],
    responses={200: {"description": "Application is healthy"}},
)
async def health() -> JSONResponse:
    """Return health status and environment diagnostics.

    Returns:
        JSON with status, version, backends, and GPU info.
    """
    gpu = gpu_info()

    ollama_status = "not_checked"
    if settings.LLM_BACKEND == "ollama":
        try:
            from aria.backend.services.providers.llm_ollama import OllamaLLMService
            svc = OllamaLLMService(base_url=settings.OLLAMA_URL, model=settings.OLLAMA_MODEL)
            ollama_status = "online" if await svc.is_available() else "offline"
        except Exception:
            ollama_status = "error"

    return JSONResponse({
        "status": "ok",
        "version": settings.APP_VERSION,
        "backends": {
            "stt": settings.STT_BACKEND,
            "llm": settings.LLM_BACKEND,
            "tts": settings.TTS_BACKEND,
            "diarization": settings.DIAR_BACKEND,
        },
        "ollama": ollama_status,
        "gpu": gpu,
        "features": {
            "elevenlabs_tts": settings.FEATURE_ELEVENLABS_TTS,
            "grammar_workshop": settings.FEATURE_GRAMMAR_WORKSHOP,
            "text_upload": settings.FEATURE_TEXT_UPLOAD,
            "flashcards": settings.FEATURE_FLASHCARDS,
            "session_replay": settings.FEATURE_SESSION_REPLAY,
        },
    })


# ── Module routers ────────────────────────────────────────────────────────────
# Each router is wired here. Implementations are in aria/backend/modules/*/router.py.
# API versioning: all routes prefixed /api/v1/. WebSocket at /ws/v1/.

from aria.backend.modules.analysis.router import router as analysis_router
from aria.backend.modules.auth.router import router as auth_router
from aria.backend.modules.conversation.router import router as conversation_router
from aria.backend.modules.conversation.router import ws_router as conversation_ws_router
from aria.backend.modules.flashcards.router import router as flashcard_router
from aria.backend.modules.grammar.router import router as grammar_router
from aria.backend.modules.text_practice.router import router as text_practice_router

app.include_router(auth_router,               prefix="/api/v1/auth",          tags=["auth"])
app.include_router(conversation_router,       prefix="/api/v1/conversations",  tags=["conversation"])
app.include_router(conversation_ws_router,    prefix="/ws/v1/conversation",    tags=["conversation"])
app.include_router(analysis_router,           prefix="/api/v1/sessions",       tags=["analysis"])
app.include_router(flashcard_router,          prefix="/api/v1/flashcards",     tags=["flashcards"])
app.include_router(grammar_router,            prefix="/api/v1/grammar",        tags=["grammar"])
app.include_router(text_practice_router,      prefix="/api/v1/text-practice",  tags=["text-practice"])

