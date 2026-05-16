"""Central configuration — all env vars typed, documented, and validated here.

Every new env var must be added here with an inline comment describing its
purpose, type, and default. See docs/configuration.md for the full reference.
"""
from __future__ import annotations

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────
    APP_NAME: str = "Aria"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── API Keys ────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""           # Claude API key (prod LLM)
    DEEPGRAM_API_KEY: str = ""            # Deepgram STT key (prod STT live+batch)
    GLADIA_API_KEY: str = ""              # Gladia STT key (primary prod STT, GDPR-native)
    ELEVENLABS_API_KEY: str = ""          # ElevenLabs TTS key (Pro users)
    OPENAI_API_KEY: str = ""              # OpenAI TTS key (Free user fallback)
    HF_TOKEN: str = ""                    # HuggingFace token (pyannote diarization)
    STRIPE_SECRET_KEY: str = ""           # Stripe API key (Phase 9 monetization)
    STRIPE_WEBHOOK_SECRET: str = ""       # Stripe webhook signing secret

    # ── Service backend selection (.env switch — no code change required) ───
    STT_BACKEND: Literal["local", "deepgram", "gladia"] = "local"
    STT_FALLBACK: Literal["deepgram", "none"] = "deepgram"   # fallback if primary STT down
    LLM_BACKEND: Literal["ollama", "claude"] = "ollama"
    TTS_BACKEND: Literal["piper", "elevenlabs", "openai"] = "piper"
    DIAR_BACKEND: Literal["local", "deepgram", "gladia"] = "local"
    TRANSLATION_BACKEND: Literal["helsinki", "deepl"] = "helsinki"

    # ── Local ML model settings (dev only) ─────────────────────────
    WHISPER_MODEL: str = "large-v3-turbo"   # faster-whisper model name
    WHISPER_COMPUTE_TYPE: str = "float16"   # float16 (GPU) or int8 (CPU)
    WHISPER_DEVICE: str = "cuda"            # cuda or cpu
    OLLAMA_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    PIPER_VOICE_DIR: str = "/opt/piper/voices"  # directory containing .onnx voice files

    # ── Claude API (prod LLM) ───────────────────────────────────────
    CLAUDE_HAIKU_MODEL: str = "claude-haiku-4-5-20251001"   # fast, cheap — conversation + analysis
    CLAUDE_SONNET_MODEL: str = "claude-sonnet-4-6"           # quality — gate reviews
    CLAUDE_OPUS_MODEL: str = "claude-opus-4-7"               # highest — gate approvals

    # ── Database ────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./aria_dev.db"   # dev: SQLite
    # prod: postgresql+asyncpg://user:pass@host/aria (Supabase)

    # ── Redis ───────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"   # dev: local Redis; prod: Upstash URL

    # ── Auth ────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15        # JWT access token lifetime
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7           # Rotating refresh token lifetime
    GOOGLE_OAUTH_CLIENT_ID: str = ""
    GOOGLE_OAUTH_CLIENT_SECRET: str = ""
    GITHUB_OAUTH_CLIENT_ID: str = ""
    GITHUB_OAUTH_CLIENT_SECRET: str = ""

    # ── File uploads ────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 50                 # Hard limit enforced at route layer
    ALLOWED_AUDIO_EXTENSIONS: list[str] = [".mp3", ".m4a", ".wav", ".ogg", ".flac", ".webm"]
    ALLOWED_TEXT_EXTENSIONS: list[str] = [".pdf", ".txt", ".docx"]

    # ── Audio storage (opt-in session replay) ───────────────────────
    R2_ACCOUNT_ID: str = ""           # Cloudflare R2 account (audio replay storage)
    R2_ACCESS_KEY: str = ""
    R2_SECRET_KEY: str = ""
    R2_BUCKET: str = "aria-audio"
    AUDIO_RETENTION_DAYS: int = 30   # AES-256 encrypted; auto-deleted after this

    # ── Rate limiting ───────────────────────────────────────────────
    RATE_LIMIT_AUTH_PER_MIN: int = 10     # auth endpoint requests per IP per minute
    RATE_LIMIT_API_PER_MIN: int = 60      # general API requests per IP per minute

    # ── Feature flags (toggle via .env — no code changes) ──────────
    FEATURE_ELEVENLABS_TTS: bool = False      # default: OpenAI TTS; Pro enables ElevenLabs
    FEATURE_GRAMMAR_WORKSHOP: bool = True
    FEATURE_TEXT_UPLOAD: bool = True
    FEATURE_FLASHCARDS: bool = True
    FEATURE_SESSION_REPLAY: bool = False      # Pro feature — opt-in audio recording
    FEATURE_TEAM_DASHBOARD: bool = False      # Enterprise feature

    # ── Audio pipeline tuning ───────────────────────────────────────
    SAMPLE_RATE: int = 16000
    COLD_START_SECONDS: int = 60             # seconds of audio used for cold-start embeddings
    COLD_THRESHOLD: float = 0.45            # cosine similarity threshold for cold-start assignment
    MIN_SEGMENT_SAMPLES: int = 8000
    MIN_EMBED_DURATION: float = 1.5         # minimum segment duration for embedding
    NAME_CONFIDENCE_THRESHOLD: int = 2      # minimum name evidence score for auto-assignment
    EMBED_THRESHOLD: float = 0.50           # cosine similarity threshold for speaker matching

    # ── Conversation ────────────────────────────────────────────────
    MAX_CONVERSATION_MINUTES: int = 10       # Pro tier max; Free tier capped at 3
    FREE_DAILY_CONVERSATIONS: int = 3
    FREE_DAILY_TEXT_UPLOADS: int = 1
    FREE_MAX_FLASHCARDS: int = 50


settings = Settings()
