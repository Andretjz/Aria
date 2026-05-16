"""Service interface and constant tests — Gate 1 baseline.

These tests verify the adapter pattern scaffold is importable and correctly
structured, without requiring any external services (GPU, Ollama, etc.).
"""
from __future__ import annotations

import pytest


def test_interfaces_importable():
    """All abstract service interfaces must be importable without error."""
    from aria.backend.services.interfaces import (
        STTService,
        LLMService,
        TTSService,
        DiarizationService,
        TranslationService,
        TranscriptResult,
        TranscriptSegment,
        DiarizationResult,
        DiarizationSegment,
    )
    assert STTService is not None
    assert LLMService is not None


def test_factory_importable():
    """The service factory must be importable without error."""
    from aria.backend.services.factory import (
        get_stt_service,
        get_llm_service,
        get_tts_service,
        get_diarization_service,
        get_translation_service,
    )
    assert callable(get_stt_service)
    assert callable(get_llm_service)


def test_core_constants_importable():
    """Core constants ported from Transcribit must be importable."""
    from aria.backend.core.constants import (
        STOP_WORDS,
        NAME_BLOCKLIST,
        NAME_PATTERNS,
        ENGLISH_IN_GERMAN,
        TARGET_LANGUAGES,
    )
    assert "ich" in STOP_WORDS
    assert "i" in STOP_WORDS
    assert "psychologin" in NAME_BLOCKLIST
    assert "de" in NAME_PATTERNS
    assert "meeting" in ENGLISH_IN_GERMAN
    assert set(TARGET_LANGUAGES.keys()) == {"de", "en", "es", "fr", "it"}


def test_parse_json_from_llm_clean():
    """parse_json_from_llm() must handle clean JSON objects and arrays."""
    from aria.backend.core.llm_utils import parse_json_from_llm

    # Clean JSON object
    result = parse_json_from_llm('{"key": "value"}')
    assert result == {"key": "value"}

    # Clean JSON array
    result = parse_json_from_llm('[{"id": 1, "speaker": "Alice"}]')
    assert result == [{"id": 1, "speaker": "Alice"}]


def test_parse_json_from_llm_markdown_fence():
    """parse_json_from_llm() must strip markdown code fences."""
    from aria.backend.core.llm_utils import parse_json_from_llm

    text = '```json\n{"status": "ok"}\n```'
    result = parse_json_from_llm(text)
    assert result == {"status": "ok"}


def test_parse_json_from_llm_truncated():
    """parse_json_from_llm() must handle truncated arrays gracefully."""
    from aria.backend.core.llm_utils import parse_json_from_llm

    truncated = '[{"id": 1, "speaker": "Alice"}, {"id": 2, "speaker":'
    result = parse_json_from_llm(truncated)
    assert result is not None
    assert isinstance(result, list)
    assert len(result) >= 1


def test_parse_json_from_llm_none():
    """parse_json_from_llm() must return None for empty/None input."""
    from aria.backend.core.llm_utils import parse_json_from_llm

    assert parse_json_from_llm(None) is None
    assert parse_json_from_llm("") is None


def test_gpu_helpers_importable():
    """GPU helpers must be importable and work without CUDA."""
    from aria.backend.core.gpu import flush_gpu, vram_free_gb, gpu_info

    flush_gpu()  # must not raise, even without CUDA
    free = vram_free_gb()
    assert isinstance(free, float)
    info = gpu_info()
    assert "available" in info
    assert isinstance(info["available"], bool)


def test_exceptions_hierarchy():
    """All Aria exceptions must inherit from AriaError."""
    from aria.backend.core.exceptions import (
        AriaError, STTError, LLMError, TTSError,
        DiarizationError, TranslationError, PipelineError,
        AuthError, SessionNotFoundError,
    )
    for exc_cls in [STTError, LLMError, TTSError, DiarizationError,
                    TranslationError, PipelineError, AuthError, SessionNotFoundError]:
        assert issubclass(exc_cls, AriaError)

