"""Deepgram STT provider — production fallback (Nova-3 batch, Flux live).

Used when STT_BACKEND=deepgram. Primary prod STT is Gladia; Deepgram is the
automatic fallback (3 Gladia errors → switch to Deepgram, logged).
See ADR-001 for provider selection rationale.
"""
from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator

from aria.backend.core.exceptions import STTError, AudioFormatError
from aria.backend.core.logging import get_logger
from aria.backend.services.interfaces import STTService, TranscriptResult, TranscriptSegment

log = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".mp3", ".m4a", ".wav", ".ogg", ".flac", ".webm"}


class DeepgramSTTService(STTService):
    """Deepgram Nova-3 (batch) / Flux (live) STT service.

    Args:
        api_key: Deepgram API key from DEEPGRAM_API_KEY env var.
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from deepgram import DeepgramClient
                self._client = DeepgramClient(self._api_key)
            except ImportError as exc:
                raise STTError("deepgram-sdk not installed. Run: pip install deepgram-sdk") from exc
        return self._client

    async def transcribe_stream(
        self,
        audio_chunks: AsyncIterator[bytes],
        language: str = "auto",
    ) -> AsyncIterator[str]:
        """Stream audio through Deepgram Flux WebSocket and yield partials.

        Args:
            audio_chunks: Raw PCM audio bytes, 200ms chunks, 16kHz mono.
            language: BCP-47 language code or "auto" for Deepgram detection.

        Yields:
            Partial transcript strings from Deepgram interim results.

        Raises:
            STTError: If the Deepgram WebSocket connection fails.

        Note:
            Uses Deepgram's utterance_end event to signal turn completion.
            detect_language=true is set when language="auto".
        """
        try:
            client = self._get_client()
            options = {
                "model": "nova-2",
                "encoding": "linear16",
                "sample_rate": 16000,
                "channels": 1,
                "interim_results": True,
                "utterance_end_ms": 1000,
                "detect_language": language == "auto",
            }
            if language != "auto":
                options["language"] = language

            # Pete_Pipeline (Phase 3) wires the full WebSocket loop here.
            # Sam_Architect provides the stub so the interface is importable.
            raise NotImplementedError(
                "DeepgramSTTService.transcribe_stream implemented by Pete_Pipeline in Phase 3"
            )
        except NotImplementedError:
            raise
        except Exception as exc:
            raise STTError(f"Deepgram stream failed: {exc}") from exc

    async def transcribe_file(
        self,
        path: Path,
        language: str = "auto",
    ) -> TranscriptResult:
        """Transcribe a file via Deepgram Nova-3 batch API.

        Args:
            path: Absolute path to the audio file.
            language: BCP-47 language code or "auto" for detection.

        Returns:
            TranscriptResult with utterance-level segments.

        Raises:
            STTError: If the Deepgram API call fails.
            AudioFormatError: If the file extension is unsupported.
        """
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise AudioFormatError(f"Unsupported audio format: {path.suffix}")

        # Pete_Pipeline (Phase 3) wires the REST call here.
        raise NotImplementedError(
            "DeepgramSTTService.transcribe_file implemented by Pete_Pipeline in Phase 3"
        )

