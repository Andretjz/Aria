"""OpenAI TTS provider — production Free tier fallback.

Used when TTS_BACKEND=openai. Pro users get ElevenLabsTTSService.
"""
from __future__ import annotations

from typing import AsyncIterator

from aria.backend.core.exceptions import TTSError
from aria.backend.core.logging import get_logger
from aria.backend.services.interfaces import TTSService

log = get_logger(__name__)


class OpenAITTSService(TTSService):
    """OpenAI TTS-1 service — Free user fallback in production.

    Args:
        api_key: OpenAI API key from OPENAI_API_KEY env var.
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self._api_key)
            except ImportError as exc:
                raise TTSError("openai package not installed. Run: pip install openai") from exc
        return self._client

    async def synthesise(
        self,
        text: str,
        language: str = "en",
        voice_id: str | None = None,
    ) -> AsyncIterator[bytes]:
        """Synthesise text via OpenAI TTS-1 and yield MP3 bytes.

        Args:
            text: Text to synthesise.
            language: BCP-47 language code (OpenAI TTS-1 is multilingual).
            voice_id: OpenAI voice name override (alloy/echo/fable/onyx/nova/shimmer).
                      None = "nova" (warm, natural).

        Yields:
            MP3 audio bytes.

        Raises:
            TTSError: If the OpenAI API call fails.
        """
        voice = voice_id or "nova"
        client = self._get_client()
        try:
            async with client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="mp3",
            ) as response:
                async for chunk in response.iter_bytes(chunk_size=4096):
                    yield chunk
        except Exception as exc:
            raise TTSError(f"OpenAI TTS failed: {exc}") from exc

