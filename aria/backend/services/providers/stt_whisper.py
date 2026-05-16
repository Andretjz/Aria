"""Local faster-whisper STT provider — dev only (GPU required).

Used when STT_BACKEND=local. In production, swap to GladiaSTTService or
DeepgramSTTService via the .env file — no code change required.
See ADR-001 for provider selection rationale.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncIterator

from aria.backend.core.exceptions import STTError, AudioFormatError
from aria.backend.core.logging import get_logger
from aria.backend.services.interfaces import STTService, TranscriptResult, TranscriptSegment

log = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".mp3", ".m4a", ".wav", ".ogg", ".flac", ".webm"}


class FasterWhisperSTTService(STTService):
    """faster-whisper backed STT — runs on local GPU during development.

    Args:
        model: Model name (e.g. "large-v3-turbo"). See faster-whisper docs.
        device: "cuda" or "cpu".
        compute_type: "float16" (GPU) or "int8" (CPU).
    """

    def __init__(self, model: str, device: str = "cuda", compute_type: str = "float16") -> None:
        self._model_name = model
        self._device = device
        self._compute_type = compute_type
        self._model = None  # lazy-loaded on first use

    def _load_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                log.info("loading_whisper_model", model=self._model_name, device=self._device)
                self._model = WhisperModel(
                    self._model_name,
                    device=self._device,
                    compute_type=self._compute_type,
                )
                log.info("whisper_model_ready", model=self._model_name)
            except Exception as exc:
                raise STTError(f"Failed to load Whisper model: {exc}") from exc
        return self._model

    async def transcribe_stream(
        self,
        audio_chunks: AsyncIterator[bytes],
        language: str = "auto",
    ) -> AsyncIterator[str]:
        """Stream audio chunks through faster-whisper and yield partial transcripts.

        Args:
            audio_chunks: Raw PCM audio bytes, 200ms chunks, 16kHz mono.
            language: BCP-47 language code or "auto" for auto-detection.

        Yields:
            Partial transcript strings per segment.

        Raises:
            STTError: If Whisper processing fails.

        Note:
            For real-time streaming, production uses Gladia/Deepgram WebSocket.
            This implementation buffers all chunks then transcribes — suitable
            for dev/testing only. See ADR-001.
        """
        import io
        import tempfile
        import wave

        buf = io.BytesIO()
        async for chunk in audio_chunks:
            buf.write(chunk)

        buf.seek(0)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            with wave.open(tmp, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(buf.read())
            tmp_path = Path(tmp.name)

        try:
            result = await self.transcribe_file(tmp_path, language)
            for seg in result.segments:
                yield seg.text
        finally:
            tmp_path.unlink(missing_ok=True)

    async def transcribe_file(
        self,
        path: Path,
        language: str = "auto",
    ) -> TranscriptResult:
        """Transcribe a complete audio file using faster-whisper.

        Args:
            path: Absolute path to the audio file.
            language: BCP-47 language code or "auto" for auto-detection.

        Returns:
            TranscriptResult with word-level segments.

        Raises:
            STTError: If transcription fails.
            AudioFormatError: If the file extension is unsupported.
        """
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise AudioFormatError(f"Unsupported audio format: {path.suffix}")

        model = self._load_model()
        lang_arg = None if language == "auto" else language

        try:
            segments_iter, info = await asyncio.to_thread(
                model.transcribe,
                str(path),
                language=lang_arg,
                word_timestamps=True,
                beam_size=5,
            )

            segments = []
            for seg in segments_iter:
                segments.append(TranscriptSegment(
                    text=seg.text.strip(),
                    start=seg.start,
                    end=seg.end,
                    language=info.language,
                ))

            log.info(
                "whisper_transcription_complete",
                path=str(path),
                language=info.language,
                duration=info.duration,
                segments=len(segments),
            )
            return TranscriptResult(
                segments=segments,
                language=info.language,
                duration_seconds=info.duration,
            )
        except Exception as exc:
            raise STTError(f"Whisper transcription failed: {exc}") from exc

