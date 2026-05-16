"""Service factory — the only place .env is read for provider selection.

Business logic imports from this module via FastAPI Depends(), never directly
from providers/. Swapping a provider = changing one .env variable.

See ADR-003 for the adapter pattern rationale.
"""
from __future__ import annotations

from functools import lru_cache

from aria.backend.core.config import settings
from aria.backend.core.exceptions import ConfigurationError
from aria.backend.services.interfaces import (
    DiarizationService,
    LLMService,
    STTService,
    TTSService,
    TranslationService,
)


# ── STT ──────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_stt_service() -> STTService:
    """Return the configured STT service instance.

    Reads STT_BACKEND from settings. Caches the instance for the process lifetime.

    Returns:
        A concrete STTService implementation.

    Raises:
        ConfigurationError: If STT_BACKEND has an unsupported value.
    """
    match settings.STT_BACKEND:
        case "local":
            from aria.backend.services.providers.stt_whisper import FasterWhisperSTTService
            return FasterWhisperSTTService(
                model=settings.WHISPER_MODEL,
                device=settings.WHISPER_DEVICE,
                compute_type=settings.WHISPER_COMPUTE_TYPE,
            )
        case "deepgram":
            from aria.backend.services.providers.stt_deepgram import DeepgramSTTService
            if not settings.DEEPGRAM_API_KEY:
                raise ConfigurationError("DEEPGRAM_API_KEY is required when STT_BACKEND=deepgram")
            return DeepgramSTTService(api_key=settings.DEEPGRAM_API_KEY)
        case "gladia":
            from aria.backend.services.providers.stt_gladia import GladiaSTTService
            if not settings.GLADIA_API_KEY:
                raise ConfigurationError("GLADIA_API_KEY is required when STT_BACKEND=gladia")
            return GladiaSTTService(api_key=settings.GLADIA_API_KEY)
        case _:
            raise ConfigurationError(f"Unknown STT_BACKEND: {settings.STT_BACKEND!r}")


# ── LLM ──────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    """Return the configured LLM service instance.

    Reads LLM_BACKEND from settings.

    Returns:
        A concrete LLMService implementation.

    Raises:
        ConfigurationError: If LLM_BACKEND has an unsupported value.
    """
    match settings.LLM_BACKEND:
        case "ollama":
            from aria.backend.services.providers.llm_ollama import OllamaLLMService
            return OllamaLLMService(
                base_url=settings.OLLAMA_URL,
                model=settings.OLLAMA_MODEL,
            )
        case "claude":
            from aria.backend.services.providers.llm_claude import ClaudeLLMService
            if not settings.ANTHROPIC_API_KEY:
                raise ConfigurationError("ANTHROPIC_API_KEY is required when LLM_BACKEND=claude")
            return ClaudeLLMService(
                api_key=settings.ANTHROPIC_API_KEY,
                model=settings.CLAUDE_HAIKU_MODEL,
            )
        case _:
            raise ConfigurationError(f"Unknown LLM_BACKEND: {settings.LLM_BACKEND!r}")


# ── TTS ──────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_tts_service() -> TTSService:
    """Return the configured TTS service instance.

    Reads TTS_BACKEND from settings.

    Returns:
        A concrete TTSService implementation.

    Raises:
        ConfigurationError: If TTS_BACKEND has an unsupported value.
    """
    match settings.TTS_BACKEND:
        case "piper":
            from aria.backend.services.providers.tts_piper import PiperTTSService
            return PiperTTSService(voice_dir=settings.PIPER_VOICE_DIR)
        case "elevenlabs":
            from aria.backend.services.providers.tts_elevenlabs import ElevenLabsTTSService
            if not settings.ELEVENLABS_API_KEY:
                raise ConfigurationError("ELEVENLABS_API_KEY is required when TTS_BACKEND=elevenlabs")
            return ElevenLabsTTSService(api_key=settings.ELEVENLABS_API_KEY)
        case "openai":
            from aria.backend.services.providers.tts_openai import OpenAITTSService
            if not settings.OPENAI_API_KEY:
                raise ConfigurationError("OPENAI_API_KEY is required when TTS_BACKEND=openai")
            return OpenAITTSService(api_key=settings.OPENAI_API_KEY)
        case _:
            raise ConfigurationError(f"Unknown TTS_BACKEND: {settings.TTS_BACKEND!r}")


# ── Diarization ───────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_diarization_service() -> DiarizationService:
    """Return the configured diarization service instance.

    Reads DIAR_BACKEND from settings.

    Returns:
        A concrete DiarizationService implementation.

    Raises:
        ConfigurationError: If DIAR_BACKEND has an unsupported value.
    """
    match settings.DIAR_BACKEND:
        case "local":
            from aria.backend.services.providers.diarization_pyannote import PyannoteService
            if not settings.HF_TOKEN:
                raise ConfigurationError("HF_TOKEN is required when DIAR_BACKEND=local")
            return PyannoteService(hf_token=settings.HF_TOKEN)
        case "deepgram":
            from aria.backend.services.providers.diarization_deepgram import DeepgramDiarizationService
            if not settings.DEEPGRAM_API_KEY:
                raise ConfigurationError("DEEPGRAM_API_KEY is required when DIAR_BACKEND=deepgram")
            return DeepgramDiarizationService(api_key=settings.DEEPGRAM_API_KEY)
        case "gladia":
            from aria.backend.services.providers.diarization_deepgram import DeepgramDiarizationService
            # Gladia includes diarization in its STT response; this path uses
            # the DeepgramDiarizationService as a direct fallback for uploaded files.
            if not settings.DEEPGRAM_API_KEY:
                raise ConfigurationError("DEEPGRAM_API_KEY is required as fallback when DIAR_BACKEND=gladia")
            return DeepgramDiarizationService(api_key=settings.DEEPGRAM_API_KEY)
        case _:
            raise ConfigurationError(f"Unknown DIAR_BACKEND: {settings.DIAR_BACKEND!r}")


# ── Translation ───────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_translation_service() -> TranslationService:
    """Return the configured translation service instance.

    Reads TRANSLATION_BACKEND from settings.

    Returns:
        A concrete TranslationService implementation.

    Raises:
        ConfigurationError: If TRANSLATION_BACKEND has an unsupported value.
    """
    match settings.TRANSLATION_BACKEND:
        case "helsinki":
            from aria.backend.services.providers.translation_helsinki import HelsinkiTranslationService
            return HelsinkiTranslationService()
        case "deepl":
            from aria.backend.services.providers.translation_deepl import DeepLTranslationService
            return DeepLTranslationService()
        case _:
            raise ConfigurationError(
                f"Unknown TRANSLATION_BACKEND: {settings.TRANSLATION_BACKEND!r}"
            )

