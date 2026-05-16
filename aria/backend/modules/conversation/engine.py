"""Conversation turn orchestrator — STT → LLM → TTS cycle.

ConversationEngine takes a buffer of accumulated audio (one complete turn,
as determined by EnergyVAD), runs STT to get text, sends it through the LLM
for a response, then synthesises the response via TTS and streams everything
back over the WebSocket.

All three service dependencies are injected so tests can mock any layer
without touching the real providers.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import WebSocket

from aria.backend.core.exceptions import LLMError, STTError, TTSError
from aria.backend.core.logging import get_logger
from aria.backend.services.interfaces import LLMService, STTService, TTSService

log = get_logger(__name__)

SYSTEM_PROMPT_TEMPLATE = (
    "You are Aria, a friendly AI language tutor. "
    "The user is practising {language}. "
    "Respond conversationally in {language}. "
    "Keep replies concise (1–3 sentences). "
    "Gently correct grammar mistakes when you spot them."
)


class ConversationEngine:
    """Orchestrates one full STT → LLM → TTS turn over a WebSocket.

    Args:
        stt: Speech-to-text service (batch transcription used for each turn).
        llm: Language model service (streaming generation).
        tts: Text-to-speech service (streaming synthesis).
    """

    def __init__(self, stt: STTService, llm: LLMService, tts: TTSService) -> None:
        self._stt = stt
        self._llm = llm
        self._tts = tts

    async def process_turn(
        self,
        audio_buffer: bytes,
        language: str,
        history: list[dict],
        ws: WebSocket,
    ) -> tuple[str, str]:
        """Run one complete turn: STT → WS transcript → LLM → TTS → WS audio.

        Sends JSON events and binary audio chunks to the client WebSocket as
        they become available. Callers should append the returned texts to
        `history` and pass the updated list on the next call.

        Args:
            audio_buffer: Raw PCM bytes for the user's utterance (one turn).
            language: BCP-47 target language code (e.g. "en", "de").
            history: Conversation history as list of {role, content} dicts.
            ws: Open WebSocket connection to the client.

        Returns:
            (user_text, assistant_text) — empty strings if STT yielded nothing.

        Raises:
            STTError: If transcription fails unrecoverably.
            LLMError: If the LLM call fails unrecoverably.
            TTSError: If speech synthesis fails unrecoverably.
        """
        # 1. Transcribe accumulated audio
        user_text = await self._transcribe(audio_buffer, language)
        if not user_text:
            return ("", "")

        # 2. Send transcript to client immediately
        await ws.send_json({"type": "transcript", "text": user_text, "is_final": True})

        # 3. Call LLM (streaming) and forward text chunks to client
        messages = list(history) + [{"role": "user", "content": user_text}]
        system = SYSTEM_PROMPT_TEMPLATE.format(language=language)
        assistant_text = await self._generate_and_stream(messages, system, ws)

        # 4. Synthesise TTS and stream audio bytes to client
        await self._synthesise_and_stream(assistant_text, language, ws)

        # 5. Signal turn complete
        await ws.send_json({"type": "turn_end"})

        log.info(
            "turn_complete",
            user_len=len(user_text),
            assistant_len=len(assistant_text),
            language=language,
        )
        return (user_text, assistant_text)

    # ── private helpers ───────────────────────────────────────────────────────

    async def _transcribe(self, audio_buffer: bytes, language: str) -> str:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_buffer)
            tmp_path = Path(tmp.name)
        try:
            result = await self._stt.transcribe_file(tmp_path, language=language)
        finally:
            tmp_path.unlink(missing_ok=True)
        return result.full_text.strip()

    async def _generate_and_stream(
        self,
        messages: list[dict],
        system: str,
        ws: WebSocket,
    ) -> str:
        chunks: list[str] = []
        async for chunk in await self._llm.generate(messages, system=system):
            chunks.append(chunk)
            await ws.send_json({"type": "response_text", "text": chunk})
        return "".join(chunks)

    async def _synthesise_and_stream(
        self,
        text: str,
        language: str,
        ws: WebSocket,
    ) -> None:
        async for audio_chunk in await self._tts.synthesise(text, language=language):
            await ws.send_bytes(audio_chunk)
