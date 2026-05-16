"""ElevenLabs TTS provider — production Pro tier.

Used when TTS_BACKEND=elevenlabs (FEATURE_ELEVENLABS_TTS=true).
Free users fall back to OpenAITTSService. See ADR-002.
"""
from __future__ import annotations

from typing import AsyncIterator

from aria.backend.core.exceptions import TTSError
from aria.backend.core.logging import get_logger
from aria.backend.services.interfaces import TTSService

log = get_logger(__name__)

# ElevenLabs voice IDs for each target language (multilingual v2 model)
DEFAULT_VOICE_IDS: dict[str, str] = {
    "de": "pNInz6obpgDQGcFmaJgB",   # Adam (clear German)
    "en": "21m00Tcm4TlvDq8ikWAM",   # Rachel (warm English)
    "es": "AZnzlk1XvdvUeBnXmlld",   # Domi (Spanish)
    "fr": "ThT5KcBeYPX3keUQqHPh",   # Dorothy (French-friendly)
    "it": "XB0fDUnXU5powFXDhCwa",   # Charlotte (Italian)
}


class ElevenLabsTTSService(TTSService):
    """ElevenLabs streaming TTS for Pro users.

    Args:
        api_key: ElevenLabs API key from ELEVENLABS_API_KEY env var.
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from elevenlabs.client import AsyncElevenLabs
                self._client = AsyncElevenLabs(api_key=self._api_key)
            except ImportError as exc:
                raise TTSError("elevenlabs package not installed. Run: pip install elevenlabs") from exc
        return self._client

    async def synthesise(
        self,
        text: str,
        language: str = "en",
        voice_id: str | None = None,
    ) -> AsyncIterator[bytes]:
        """Synthesise text to audio via ElevenLabs streaming API.

        Args:
            text: Text to synthesise.
            language: BCP-47 language code for voice selection.
            voice_id: ElevenLabs voice ID override. None = language default.

        Yields:
            MP3 audio bytes as ElevenLabs streams them.

        Raises:
            TTSError: If the ElevenLabs API call fails.

        Note:
            Uses the multilingual-v2 model which supports all 5 target languages.
            Buffer-word pattern: if LLM has processing delay, Aria's reply ends
            in "... " to keep TTS flowing naturally.
        """
        vid = voice_id or DEFAULT_VOICE_IDS.get(language, DEFAULT_VOICE_IDS["en"])
        client = self._get_client()
        try:
            audio_stream = await client.generate(
                text=text,
                voice=vid,
                model="eleven_multilingual_v2",
                stream=True,
            )
            async for chunk in audio_stream:
                if chunk:
                    yield chunk
        except Exception as exc:
            raise TTSError(f"ElevenLabs synthesis failed: {exc}") from exc

