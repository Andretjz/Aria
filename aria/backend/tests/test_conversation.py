"""Gate 4 tests — Carlos_Conversation (Phase 4).

Covers: VAD logic, ConversationEngine turn orchestration, ConversationSession
ORM model and schemas, REST create-session endpoint, and WebSocket protocol.
All tests run without GPU, Ollama, or real TTS providers.
"""
from __future__ import annotations

import io
import json
import struct
import uuid
import wave
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_silence_pcm(duration_ms: int = 600, sample_rate: int = 16000) -> bytes:
    """Return PCM bytes of near-silence (amplitude 0)."""
    n = int(sample_rate * duration_ms / 1000)
    return struct.pack(f"<{n}h", *([0] * n))


def _make_speech_pcm(duration_ms: int = 200, sample_rate: int = 16000) -> bytes:
    """Return PCM bytes with high amplitude (simulated speech)."""
    n = int(sample_rate * duration_ms / 1000)
    amplitude = 8000  # well above 300 RMS threshold
    return struct.pack(f"<{n}h", *([amplitude] * n))


def _make_wav_bytes(duration_samples: int = 160, sample_rate: int = 16000) -> bytes:
    """Return minimal valid WAV bytes for engine tests."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{duration_samples}h", *([0] * duration_samples)))
    return buf.getvalue()


def _make_transcript_result(text: str = "Hello world", lang: str = "en", duration: float = 1.0):
    from aria.backend.services.interfaces import TranscriptResult, TranscriptSegment
    return TranscriptResult(
        segments=[TranscriptSegment(text=text, start=0.0, end=duration, language=lang)],
        language=lang,
        duration_seconds=duration,
    )


# ── TestVAD ───────────────────────────────────────────────────────────────────

class TestVAD:
    """EnergyVAD unit tests — no I/O required."""

    def test_vad_importable(self):
        from aria.backend.modules.conversation.vad import EnergyVAD
        assert EnergyVAD is not None

    def test_vad_default_init(self):
        from aria.backend.modules.conversation.vad import EnergyVAD
        vad = EnergyVAD()
        assert vad._sample_rate == 16000
        assert vad._threshold == 300.0

    def test_vad_silence_only_returns_false(self):
        from aria.backend.modules.conversation.vad import EnergyVAD
        vad = EnergyVAD()
        # Pure silence without preceding speech should never trigger
        for _ in range(10):
            result = vad.process_chunk(_make_silence_pcm(100))
            assert result is False

    def test_vad_speech_then_silence_triggers_true(self):
        from aria.backend.modules.conversation.vad import EnergyVAD
        vad = EnergyVAD(silence_duration_ms=200)
        # Feed speech to arm the VAD
        vad.process_chunk(_make_speech_pcm(300))
        # Feed enough silence to cross the 200ms threshold
        result = vad.process_chunk(_make_silence_pcm(250))
        assert result is True

    def test_vad_speech_without_enough_silence_returns_false(self):
        from aria.backend.modules.conversation.vad import EnergyVAD
        vad = EnergyVAD(silence_duration_ms=500)
        vad.process_chunk(_make_speech_pcm(300))
        # Only 100ms silence — not enough
        result = vad.process_chunk(_make_silence_pcm(100))
        assert result is False

    def test_vad_compute_rms_silence_is_zero(self):
        from aria.backend.modules.conversation.vad import EnergyVAD
        rms = EnergyVAD._compute_rms(_make_silence_pcm(100))
        assert rms == 0.0

    def test_vad_compute_rms_signal_above_zero(self):
        from aria.backend.modules.conversation.vad import EnergyVAD
        rms = EnergyVAD._compute_rms(_make_speech_pcm(100))
        assert rms > 300.0

    def test_vad_compute_rms_empty_bytes_is_zero(self):
        from aria.backend.modules.conversation.vad import EnergyVAD
        assert EnergyVAD._compute_rms(b"") == 0.0

    def test_vad_reset_clears_state(self):
        from aria.backend.modules.conversation.vad import EnergyVAD
        vad = EnergyVAD(silence_duration_ms=200)
        vad.process_chunk(_make_speech_pcm(300))
        vad.reset()
        assert vad._speech_started is False
        assert vad._silent_sample_count == 0

    def test_vad_reset_prevents_spurious_turn_end(self):
        from aria.backend.modules.conversation.vad import EnergyVAD
        vad = EnergyVAD(silence_duration_ms=200)
        vad.process_chunk(_make_speech_pcm(300))
        vad.reset()
        # After reset, silence should not trigger a turn-end
        result = vad.process_chunk(_make_silence_pcm(300))
        assert result is False

    def test_vad_triggers_only_once_per_utterance(self):
        from aria.backend.modules.conversation.vad import EnergyVAD
        vad = EnergyVAD(silence_duration_ms=200)
        vad.process_chunk(_make_speech_pcm(300))
        first = vad.process_chunk(_make_silence_pcm(250))
        second = vad.process_chunk(_make_silence_pcm(250))
        assert first is True
        assert second is False  # already reset after first trigger


# ── TestConversationModel ─────────────────────────────────────────────────────

class TestConversationModel:
    """ORM model and schema smoke tests."""

    def test_model_importable(self):
        from aria.backend.modules.conversation.models import ConversationSession
        assert ConversationSession.__tablename__ == "conversation_sessions"

    def test_model_has_expected_columns(self):
        from aria.backend.modules.conversation.models import ConversationSession
        cols = {c.name for c in ConversationSession.__table__.columns}
        assert {"id", "user_id", "created_at", "language", "status",
                "turn_count", "transcript_json", "ended_at"} <= cols

    def test_model_default_status_is_active(self):
        from aria.backend.modules.conversation.models import ConversationSession
        col = ConversationSession.__table__.c["status"]
        assert col.default.arg == "active"

    def test_schema_importable(self):
        from aria.backend.modules.conversation.schemas import (
            ConversationSessionCreate,
            ConversationSessionRead,
        )
        assert ConversationSessionCreate is not None
        assert ConversationSessionRead is not None

    def test_schema_default_language(self):
        from aria.backend.modules.conversation.schemas import ConversationSessionCreate
        body = ConversationSessionCreate()
        assert body.language == "en"

    def test_schema_rejects_unsupported_language(self):
        from pydantic import ValidationError
        from aria.backend.modules.conversation.schemas import ConversationSessionCreate
        with pytest.raises(ValidationError):
            ConversationSessionCreate(language="xx")

    def test_schema_accepts_all_five_target_languages(self):
        from aria.backend.modules.conversation.schemas import ConversationSessionCreate
        for lang in ("de", "en", "es", "fr", "it"):
            body = ConversationSessionCreate(language=lang)
            assert body.language == lang


# ── TestConversationEngine ────────────────────────────────────────────────────

class TestConversationEngine:
    """ConversationEngine with fully mocked STT, LLM, and TTS."""

    def _make_engine(self, transcript_text: str = "Hi there"):
        from aria.backend.modules.conversation.engine import ConversationEngine

        stt = MagicMock()
        stt.transcribe_file = AsyncMock(return_value=_make_transcript_result(transcript_text))

        async def _gen_chunks(*args, **kwargs):
            yield "Hello "
            yield "world"

        llm = MagicMock()
        llm.generate = AsyncMock(return_value=_gen_chunks())

        async def _synth(*args, **kwargs):
            yield b"\x00\x01\x02"

        tts = MagicMock()
        tts.synthesise = AsyncMock(return_value=_synth())

        return ConversationEngine(stt=stt, llm=llm, tts=tts), stt, llm, tts

    def test_engine_importable(self):
        from aria.backend.modules.conversation.engine import ConversationEngine
        assert ConversationEngine is not None

    def test_engine_stores_services(self):
        from aria.backend.modules.conversation.engine import ConversationEngine
        stt, llm, tts = MagicMock(), MagicMock(), MagicMock()
        eng = ConversationEngine(stt=stt, llm=llm, tts=tts)
        assert eng._stt is stt
        assert eng._llm is llm
        assert eng._tts is tts

    @pytest.mark.asyncio
    async def test_process_turn_returns_user_and_assistant_text(self):
        engine, *_ = self._make_engine("Guten Tag")
        ws = MagicMock()
        ws.send_json = AsyncMock()
        ws.send_bytes = AsyncMock()

        user_text, assistant_text = await engine.process_turn(
            _make_wav_bytes(), "de", [], ws
        )
        assert user_text == "Guten Tag"
        assert assistant_text == "Hello world"

    @pytest.mark.asyncio
    async def test_process_turn_sends_transcript(self):
        engine, *_ = self._make_engine("Bonjour")
        ws = MagicMock()
        ws.send_json = AsyncMock()
        ws.send_bytes = AsyncMock()

        await engine.process_turn(_make_wav_bytes(), "fr", [], ws)

        sent_jsons = [call.args[0] for call in ws.send_json.call_args_list]
        transcripts = [m for m in sent_jsons if m.get("type") == "transcript"]
        assert len(transcripts) == 1
        assert transcripts[0]["text"] == "Bonjour"
        assert transcripts[0]["is_final"] is True

    @pytest.mark.asyncio
    async def test_process_turn_sends_response_text_chunks(self):
        engine, *_ = self._make_engine()
        ws = MagicMock()
        ws.send_json = AsyncMock()
        ws.send_bytes = AsyncMock()

        await engine.process_turn(_make_wav_bytes(), "en", [], ws)

        sent_jsons = [call.args[0] for call in ws.send_json.call_args_list]
        text_chunks = [m for m in sent_jsons if m.get("type") == "response_text"]
        assert len(text_chunks) == 2  # "Hello " and "world"
        assert text_chunks[0]["text"] == "Hello "
        assert text_chunks[1]["text"] == "world"

    @pytest.mark.asyncio
    async def test_process_turn_sends_audio_bytes(self):
        engine, *_ = self._make_engine()
        ws = MagicMock()
        ws.send_json = AsyncMock()
        ws.send_bytes = AsyncMock()

        await engine.process_turn(_make_wav_bytes(), "en", [], ws)

        ws.send_bytes.assert_called_once_with(b"\x00\x01\x02")

    @pytest.mark.asyncio
    async def test_process_turn_sends_turn_end(self):
        engine, *_ = self._make_engine()
        ws = MagicMock()
        ws.send_json = AsyncMock()
        ws.send_bytes = AsyncMock()

        await engine.process_turn(_make_wav_bytes(), "en", [], ws)

        sent_jsons = [call.args[0] for call in ws.send_json.call_args_list]
        assert {"type": "turn_end"} in sent_jsons

    @pytest.mark.asyncio
    async def test_process_turn_empty_transcript_returns_empty_strings(self):
        engine, *_ = self._make_engine("")  # STT returns empty text
        ws = MagicMock()
        ws.send_json = AsyncMock()
        ws.send_bytes = AsyncMock()

        user_text, assistant_text = await engine.process_turn(
            _make_wav_bytes(), "en", [], ws
        )
        assert user_text == ""
        assert assistant_text == ""
        ws.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_turn_passes_history_to_llm(self):
        engine, _, llm, _ = self._make_engine()
        ws = MagicMock()
        ws.send_json = AsyncMock()
        ws.send_bytes = AsyncMock()

        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
        await engine.process_turn(_make_wav_bytes(), "en", history, ws)

        call_args = llm.generate.call_args
        messages_arg = call_args[0][0]
        assert messages_arg[0] == {"role": "user", "content": "Hello"}
        assert messages_arg[1] == {"role": "assistant", "content": "Hi!"}
        assert messages_arg[-1]["role"] == "user"


# ── TestCreateSessionEndpoint ─────────────────────────────────────────────────

class TestCreateSessionEndpoint:
    """POST /api/v1/conversations/ — REST endpoint tests."""

    @pytest.mark.asyncio
    async def test_create_session_returns_201(self, authed_client):
        resp = await authed_client.post(
            "/api/v1/conversations/", json={"language": "en"}
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_create_session_response_schema(self, authed_client):
        resp = await authed_client.post(
            "/api/v1/conversations/", json={"language": "de"}
        )
        data = resp.json()
        assert "id" in data
        assert data["language"] == "de"
        assert data["status"] == "active"
        assert data["turn_count"] == 0
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_session_default_language(self, authed_client):
        resp = await authed_client.post("/api/v1/conversations/", json={})
        assert resp.status_code == 201
        assert resp.json()["language"] == "en"

    @pytest.mark.asyncio
    async def test_create_session_unsupported_language_returns_422(self, authed_client):
        resp = await authed_client.post(
            "/api/v1/conversations/", json={"language": "zh"}
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_session_stores_in_db(self, authed_client):
        resp = await authed_client.post(
            "/api/v1/conversations/", json={"language": "es"}
        )
        assert resp.status_code == 201
        session_id = resp.json()["id"]
        assert uuid.UUID(session_id)  # valid UUID

    @pytest.mark.asyncio
    async def test_create_session_all_five_languages(self, authed_client):
        for lang in ("de", "en", "es", "fr", "it"):
            resp = await authed_client.post(
                "/api/v1/conversations/", json={"language": lang}
            )
            assert resp.status_code == 201, f"Failed for language={lang}"
            assert resp.json()["language"] == lang

    @pytest.mark.asyncio
    async def test_create_session_ended_at_is_null(self, authed_client):
        resp = await authed_client.post("/api/v1/conversations/", json={"language": "fr"})
        assert resp.json()["ended_at"] is None


# ── TestWebSocket ─────────────────────────────────────────────────────────────

class TestWebSocket:
    """WebSocket endpoint tests using Starlette TestClient.

    All tests use a mock DB (injected via dependency_overrides) to avoid
    SQLite write-lock contention between the TestClient's async event loop
    and the pytest-asyncio loop. DB persistence is tested in
    TestCreateSessionEndpoint which uses the async httpx client.
    """

    def _make_session(self, language: str = "en"):
        from aria.backend.modules.conversation.models import ConversationSession
        s = ConversationSession()
        s.id = uuid.uuid4()
        s.language = language
        s.status = "active"
        s.turn_count = 0
        s.transcript_json = "[]"
        return s

    def _setup(self, session=None, engine_override=None):
        """Return (TestClient, cleanup_fn) with both DB and engine mocked."""
        from starlette.testclient import TestClient
        from aria.backend.main import app
        from aria.backend.modules.conversation.router import get_engine
        from aria.backend.database import get_db

        if engine_override is not None:
            app.dependency_overrides[get_engine] = lambda: engine_override

        async def _mock_db():
            mock = MagicMock()
            mock.get = AsyncMock(return_value=session)
            mock.add = MagicMock()
            mock.commit = AsyncMock()
            mock.refresh = AsyncMock()
            yield mock

        app.dependency_overrides[get_db] = _mock_db

        def cleanup():
            app.dependency_overrides.pop(get_engine, None)
            app.dependency_overrides.pop(get_db, None)

        return TestClient(app), cleanup

    def test_websocket_unknown_session_sends_error(self):
        tc, cleanup = self._setup(session=None)
        try:
            fake_id = str(uuid.uuid4())
            with tc.websocket_connect(f"/ws/v1/conversation/{fake_id}") as ws:
                msg = ws.receive_json()
                assert msg["type"] == "error"
                assert "not found" in msg["message"].lower()
        finally:
            cleanup()

    def test_websocket_invalid_uuid_sends_error(self):
        tc, cleanup = self._setup(session=None)
        try:
            with tc.websocket_connect("/ws/v1/conversation/not-a-uuid") as ws:
                msg = ws.receive_json()
                assert msg["type"] == "error"
        finally:
            cleanup()

    def test_websocket_stop_message_closes_connection(self):
        session = self._make_session()
        tc, cleanup = self._setup(session=session)
        try:
            with tc.websocket_connect(f"/ws/v1/conversation/{session.id}") as ws:
                ws.send_json({"type": "stop"})
        finally:
            cleanup()

    def test_websocket_start_message_sends_ready(self):
        session = self._make_session("de")
        tc, cleanup = self._setup(session=session)
        try:
            with tc.websocket_connect(f"/ws/v1/conversation/{session.id}") as ws:
                ws.send_json({"type": "start", "language": "de"})
                msg = ws.receive_json()
                assert msg["type"] == "ready"
                assert msg["language"] == "de"
                assert msg["session_id"] == str(session.id)
                ws.send_json({"type": "stop"})
        finally:
            cleanup()

    def test_websocket_start_overrides_language(self):
        session = self._make_session("en")
        tc, cleanup = self._setup(session=session)
        try:
            with tc.websocket_connect(f"/ws/v1/conversation/{session.id}") as ws:
                ws.send_json({"type": "start", "language": "fr"})
                msg = ws.receive_json()
                assert msg["language"] == "fr"
                ws.send_json({"type": "stop"})
        finally:
            cleanup()

    def test_websocket_invalid_json_sends_error(self):
        session = self._make_session()
        tc, cleanup = self._setup(session=session)
        try:
            with tc.websocket_connect(f"/ws/v1/conversation/{session.id}") as ws:
                ws.send_text("not valid json {{")
                msg = ws.receive_json()
                assert msg["type"] == "error"
                assert "json" in msg["message"].lower()
                ws.send_json({"type": "stop"})
        finally:
            cleanup()

    def test_websocket_audio_below_vad_threshold_no_turn(self):
        """Silence-only audio should not trigger a turn (VAD not armed)."""
        session = self._make_session()
        tc, cleanup = self._setup(session=session)
        try:
            with tc.websocket_connect(f"/ws/v1/conversation/{session.id}") as ws:
                ws.send_bytes(_make_silence_pcm(100))
                ws.send_json({"type": "stop"})
        finally:
            cleanup()

    def test_websocket_audio_triggers_turn_with_mock_engine(self):
        """Speech + silence triggers the engine; mock responses forwarded."""
        from aria.backend.modules.conversation.engine import ConversationEngine

        async def _fake_process_turn(audio_buffer, language, history, ws):
            await ws.send_json({"type": "transcript", "text": "Hola", "is_final": True})
            await ws.send_json({"type": "response_text", "text": "Hola!"})
            await ws.send_bytes(b"\x00\x00")
            await ws.send_json({"type": "turn_end"})
            return ("Hola", "Hola!")

        mock_engine = MagicMock(spec=ConversationEngine)
        mock_engine.process_turn = _fake_process_turn

        session = self._make_session("es")
        tc, cleanup = self._setup(session=session, engine_override=mock_engine)
        try:
            with tc.websocket_connect(f"/ws/v1/conversation/{session.id}") as ws:
                ws.send_bytes(_make_speech_pcm(300))
                ws.send_bytes(_make_silence_pcm(600))

                transcript = ws.receive_json()
                assert transcript["type"] == "transcript"
                assert transcript["text"] == "Hola"

                response_text = ws.receive_json()
                assert response_text["type"] == "response_text"

                audio = ws.receive_bytes()
                assert audio == b"\x00\x00"

                turn_end = ws.receive_json()
                assert turn_end["type"] == "turn_end"

                ws.send_json({"type": "stop"})
        finally:
            cleanup()

    def test_websocket_session_marked_ended_after_close(self):
        """Handler sets status='ended' and calls db.commit() in finally block."""
        from aria.backend.modules.conversation.models import ConversationSession
        from aria.backend.main import app
        from aria.backend.database import get_db

        _session = self._make_session("en")
        committed: dict = {}

        async def _mock_db():
            mock = MagicMock()
            mock.get = AsyncMock(return_value=_session)

            async def _capture_commit():
                committed["status"] = _session.status
                committed["turn_count"] = _session.turn_count

            mock.commit = _capture_commit
            yield mock

        app.dependency_overrides[get_db] = _mock_db
        from starlette.testclient import TestClient
        tc = TestClient(app)
        try:
            with tc.websocket_connect(f"/ws/v1/conversation/{_session.id}") as ws:
                ws.send_json({"type": "stop"})
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert committed.get("status") == "ended"
        assert committed.get("turn_count") == 0
