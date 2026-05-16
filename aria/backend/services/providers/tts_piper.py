"""Piper TTS provider — dev (offline CPU, all 5 target languages).

Used when TTS_BACKEND=piper. No API key or internet connection required.
In production, swap to ElevenLabsTTSService or OpenAITTSService via .env.
"""
from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator

from aria.backend.core.exceptions import TTSError
from aria.backend.core.logging import get_logger
from aria.backend.services.interfaces import TTSService

log = get_logger(__name__)

# Default voice file names per language (ONNX models in PIPER_VOICE_DIR)
DEFAULT_VOICES: dict[str, str] = {
    "de": "de_DE-thorsten-medium.onnx",
    "en": "en_US-lessac-medium.onnx",
    "es": "es_ES-mls_10246-low.onnx",
    "fr": "fr_FR-mls_1840-low.onnx",
    "it": "it_IT-riccardo-x_low.onnx",
}


class PiperTTSService(TTSService):
    """Piper offline TTS service for local development.

    Args:
        voice_dir: Directory containing .onnx voice model files.
    """

    def __init__(self, voice_dir: str = "/opt/piper/voices") -> None:
        self._voice_dir = Path(voice_dir)

    async def synthesise(
        self,
        text: str,
        language: str = "en",
        voice_id: str | None = None,
    ) -> AsyncIterator[bytes]:
        """Synthesise text to audio via Piper and yield WAV bytes.

        Args:
            text: Text to synthesise.
            language: BCP-47 language code for voice selection.
            voice_id: Override voice filename (relative to voice_dir).
                      None = use DEFAULT_VOICES[language].

        Yields:
            WAV audio bytes in a single chunk.

        Raises:
            TTSError: If synthesis fails or the voice model is missing.
        """
        import asyncio
        import subprocess
        import tempfile

        voice_file = voice_id or DEFAULT_VOICES.get(language, DEFAULT_VOICES["en"])
        voice_path = self._voice_dir / voice_file

        if not voice_path.exists():
            raise TTSError(
                f"Piper voice model not found: {voice_path}. "
                f"Download from https://huggingface.co/rhasspy/piper-voices"
            )

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            proc = await asyncio.create_subprocess_exec(
                "piper",
                "--model", str(voice_path),
                "--output_file", str(tmp_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate(input=text.encode())
            if proc.returncode != 0:
                raise TTSError(f"Piper failed: {stderr.decode()[:200]}")
            yield tmp_path.read_bytes()
        except FileNotFoundError as exc:
            raise TTSError("piper binary not found. Install piper-tts.") from exc
        finally:
            tmp_path.unlink(missing_ok=True)

