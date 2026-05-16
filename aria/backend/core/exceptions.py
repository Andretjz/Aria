"""Aria exception hierarchy.

All custom exceptions extend AriaError so callers can catch the base class
when they don't need to distinguish between subtypes.
"""
from __future__ import annotations


class AriaError(Exception):
    """Base exception for all Aria application errors."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.detail = detail


# ── Service layer ────────────────────────────────────────────────────────────

class STTError(AriaError):
    """Raised when speech-to-text processing fails."""


class LLMError(AriaError):
    """Raised when a large-language-model call fails or returns unusable output."""


class TTSError(AriaError):
    """Raised when text-to-speech synthesis fails."""


class DiarizationError(AriaError):
    """Raised when speaker diarization fails."""


class TranslationError(AriaError):
    """Raised when translation fails."""


# ── Audio pipeline ───────────────────────────────────────────────────────────

class PipelineError(AriaError):
    """Raised when the 6-pass analysis pipeline encounters an unrecoverable error."""


class AudioFormatError(AriaError):
    """Raised when an uploaded audio file has an unsupported format or is corrupt."""


class FileTooLargeError(AriaError):
    """Raised when an uploaded file exceeds the configured size limit."""


# ── Auth / user ──────────────────────────────────────────────────────────────

class AuthError(AriaError):
    """Raised for authentication and authorisation failures."""


class UserNotFoundError(AriaError):
    """Raised when a referenced user does not exist."""


# ── Module-level ─────────────────────────────────────────────────────────────

class SessionNotFoundError(AriaError):
    """Raised when a referenced conversation session does not exist."""


class FlashcardError(AriaError):
    """Raised for flashcard and SM-2 algorithm errors."""


class GrammarError(AriaError):
    """Raised for grammar workshop errors."""


# ── Infrastructure ───────────────────────────────────────────────────────────

class StorageError(AriaError):
    """Raised when R2 / local file storage operations fail."""


class DatabaseError(AriaError):
    """Raised for unexpected database errors not handled by SQLAlchemy."""


class ConfigurationError(AriaError):
    """Raised when required environment variables are missing or invalid."""
