"""Abstract service interfaces — the adapter pattern boundary.

Every external dependency (STT, LLM, TTS, diarization, translation) is
represented here as an abstract base class. Concrete implementations live in
services/providers/. Swapping a provider = changing one .env variable.
No business logic imports a concrete provider class directly.

See ADR-003 for the adapter pattern rationale.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, AsyncIterator

if TYPE_CHECKING:
    pass


# ── Result types ─────────────────────────────────────────────────────────────

class TranscriptSegment:
    """A single transcribed segment with timing and speaker info."""

    __slots__ = ("text", "start", "end", "speaker", "language")

    def __init__(
        self,
        text: str,
        start: float,
        end: float,
        speaker: str = "UNKNOWN",
        language: str = "auto",
    ) -> None:
        self.text = text
        self.start = start
        self.end = end
        self.speaker = speaker
        self.language = language

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "start": self.start,
            "end": self.end,
            "speaker": self.speaker,
            "language": self.language,
        }


class TranscriptResult:
    """Full transcription result from a batch file transcription."""

    __slots__ = ("segments", "language", "duration_seconds")

    def __init__(
        self,
        segments: list[TranscriptSegment],
        language: str,
        duration_seconds: float,
    ) -> None:
        self.segments = segments
        self.language = language
        self.duration_seconds = duration_seconds

    @property
    def full_text(self) -> str:
        return " ".join(s.text for s in self.segments)


class DiarizationSegment:
    """A speaker-labelled time span from diarization."""

    __slots__ = ("speaker", "start", "end")

    def __init__(self, speaker: str, start: float, end: float) -> None:
        self.speaker = speaker
        self.start = start
        self.end = end


class DiarizationResult:
    """Full diarization result for an audio file."""

    __slots__ = ("segments", "num_speakers")

    def __init__(
        self,
        segments: list[DiarizationSegment],
        num_speakers: int,
    ) -> None:
        self.segments = segments
        self.num_speakers = num_speakers


# ── Abstract base classes ─────────────────────────────────────────────────────

class STTService(ABC):
    """Speech-to-text: real-time streaming and batch file transcription.

    See ADR-001 for provider selection rationale.
    Dev: FasterWhisperSTTService (local GPU).
    Prod primary: GladiaSTTService (GDPR-native, 100+ languages).
    Prod fallback: DeepgramSTTService (Nova-3, best per-language WER).
    """

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_chunks: AsyncIterator[bytes],
        language: str = "auto",
    ) -> AsyncIterator[str]:
        """Stream audio chunks and yield partial transcript strings.

        Args:
            audio_chunks: Raw PCM audio bytes, 200ms chunks, 16kHz mono.
            language: BCP-47 language code or "auto" for provider detection.

        Yields:
            Partial transcript strings as the STT provider returns them.

        Raises:
            STTError: If the provider connection drops or returns an error.
        """
        ...

    @abstractmethod
    async def transcribe_file(
        self,
        path: Path,
        language: str = "auto",
    ) -> TranscriptResult:
        """Transcribe a complete audio file (batch mode).

        Args:
            path: Absolute path to the audio file.
            language: BCP-47 language code or "auto" for auto-detection.

        Returns:
            TranscriptResult with segments, detected language, and duration.

        Raises:
            STTError: If transcription fails.
            AudioFormatError: If the file format is unsupported.
        """
        ...


class LLMService(ABC):
    """Large language model: streaming text generation.

    See ADR-002 for model routing rationale.
    Dev: OllamaLLMService (llama3.1:8b local GPU).
    Prod: ClaudeLLMService (Haiku for speed, Sonnet for quality).
    """

    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Generate a streaming text response.

        Args:
            messages: List of message dicts with "role" and "content" keys.
            system: Optional system prompt string.
            max_tokens: Maximum tokens to generate.

        Yields:
            Text chunks as the model produces them.

        Raises:
            LLMError: If the model call fails or times out.
        """
        ...

    async def generate_complete(
        self,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a complete (non-streaming) response.

        Convenience wrapper over generate() that collects all chunks.

        Args:
            messages: List of message dicts with "role" and "content" keys.
            system: Optional system prompt string.
            max_tokens: Maximum tokens to generate.

        Returns:
            The complete generated text string.

        Raises:
            LLMError: If the model call fails or times out.
        """
        chunks: list[str] = []
        async for chunk in await self.generate(messages, system, max_tokens):
            chunks.append(chunk)
        return "".join(chunks)


class TTSService(ABC):
    """Text-to-speech: streaming audio synthesis.

    Dev: PiperTTSService (offline CPU, all 5 languages).
    Prod Pro: ElevenLabsTTSService (highest voice quality, streaming).
    Prod Free: OpenAITTSService (cheaper, acceptable quality).
    """

    @abstractmethod
    async def synthesise(
        self,
        text: str,
        language: str = "en",
        voice_id: str | None = None,
    ) -> AsyncIterator[bytes]:
        """Synthesise text to audio, yielding bytes chunks for streaming.

        Args:
            text: The text to synthesise.
            language: BCP-47 language code for voice selection.
            voice_id: Provider-specific voice ID; None = use default voice.

        Yields:
            Raw audio bytes (format depends on provider; typically MP3 or PCM).

        Raises:
            TTSError: If synthesis fails.
        """
        ...


class DiarizationService(ABC):
    """Speaker diarization for uploaded audio files.

    Dev: PyannoteService (local GPU).
    Prod: GladiaDiarizationService (built-in with STT, no separate call).
    """

    @abstractmethod
    async def diarise(
        self,
        path: Path,
        num_speakers: int = 0,
    ) -> DiarizationResult:
        """Identify speaker segments in an audio file.

        Args:
            path: Absolute path to the audio file.
            num_speakers: Expected number of speakers; 0 = auto-detect.

        Returns:
            DiarizationResult with speaker-labelled time spans.

        Raises:
            DiarizationError: If diarization fails.
        """
        ...


class TranslationService(ABC):
    """Text translation between language pairs.

    Dev + Prod: HelsinkiTranslationService (Helsinki-NLP opus-mt, CPU, offline).
    Prod optional: DeepLTranslationService (higher quality, API cost).
    See ADR-009 for language architecture rationale.
    """

    @abstractmethod
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """Translate text from source_lang to target_lang.

        Args:
            text: Input text to translate.
            source_lang: BCP-47 source language code (e.g. "de").
            target_lang: BCP-47 target language code (e.g. "en").

        Returns:
            Translated text string.

        Raises:
            TranslationError: If translation fails or the language pair is
                unsupported.
        """
        ...
