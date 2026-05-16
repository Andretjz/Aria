"""Conversation module router — WebSocket and REST endpoints.

REST:      POST /api/v1/conversations/          → create session, return session_id
WebSocket: WS   /ws/v1/conversation/{id}        → live turn cycle (audio in, audio out)

The two routers are intentionally separate so main.py can mount them at
different path prefixes without coupling REST and WebSocket routing.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from aria.backend.core.logging import get_logger
from aria.backend.database import get_db
from aria.backend.modules.conversation.engine import ConversationEngine
from aria.backend.modules.conversation.models import ConversationSession
from aria.backend.modules.conversation.schemas import (
    ConversationSessionCreate,
    ConversationSessionRead,
)
from aria.backend.modules.conversation.vad import EnergyVAD
from aria.backend.services.factory import get_llm_service, get_stt_service, get_tts_service

log = get_logger(__name__)

# ── REST router ───────────────────────────────────────────────────────────────

router = APIRouter()


def get_engine() -> ConversationEngine:
    """FastAPI dependency — returns a ConversationEngine backed by current .env providers.

    Overridden in tests via app.dependency_overrides[get_engine].
    """
    return ConversationEngine(
        stt=get_stt_service(),
        llm=get_llm_service(),
        tts=get_tts_service(),
    )


@router.post(
    "/",
    response_model=ConversationSessionRead,
    status_code=201,
    summary="Create a new conversation session",
    description=(
        "Creates a new conversation session for the given target language. "
        "Returns a session_id to use when connecting the WebSocket at "
        "WS /ws/v1/conversation/{session_id}."
    ),
    responses={
        201: {"description": "Session created; connect WebSocket with returned session_id"},
        422: {"description": "Unsupported language code"},
    },
)
async def create_session(
    body: ConversationSessionCreate,
    db: AsyncSession = Depends(get_db),
) -> ConversationSessionRead:
    """Create a conversation session and persist it to the database.

    Args:
        body: Language selection for the practice session.
        db: Injected async database session.

    Returns:
        ConversationSessionRead with the new session_id and metadata.
    """
    session = ConversationSession(language=body.language)
    db.add(session)
    await db.commit()
    await db.refresh(session)

    log.info("session_created", session_id=str(session.id), language=session.language)
    return ConversationSessionRead.model_validate(session)


# ── WebSocket router ──────────────────────────────────────────────────────────

ws_router = APIRouter()


@ws_router.websocket("/{session_id}")
async def conversation_websocket(
    session_id: str,
    ws: WebSocket,
    engine: ConversationEngine = Depends(get_engine),
    db: AsyncSession = Depends(get_db),
) -> None:
    """WebSocket endpoint for live conversation.

    Protocol:
        Client → server (text JSON):
            {"type": "start", "language": "en"}   — optional config before audio
            {"type": "stop"}                       — graceful close

        Client → server (binary):
            Raw 16-bit LE mono PCM at 16 kHz, any chunk size.
            EnergyVAD detects turn-end from silence.

        Server → client (text JSON):
            {"type": "ready", "session_id": "...", "language": "en"}
            {"type": "transcript", "text": "...", "is_final": true}
            {"type": "response_text", "text": "..."}   — streamed LLM chunks
            {"type": "turn_end"}
            {"type": "error", "message": "..."}

        Server → client (binary):
            TTS audio bytes (format depends on TTS_BACKEND: WAV for Piper,
            MP3 for ElevenLabs/OpenAI).

    Args:
        session_id: UUID of a ConversationSession row created via POST /api/v1/conversations/.
        ws: Incoming WebSocket connection.
        engine: Injected ConversationEngine (overridable in tests).
        db: Injected async database session.
    """
    await ws.accept()

    # Validate session exists
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        await ws.send_json({"type": "error", "message": "Invalid session_id format"})
        await ws.close(code=1008)
        return

    session = await db.get(ConversationSession, sid)
    if session is None:
        await ws.send_json({"type": "error", "message": "Session not found"})
        await ws.close(code=1008)
        return

    vad = EnergyVAD()
    audio_buffer = bytearray()
    history: list[dict] = []
    language = session.language

    log.info("ws_connected", session_id=session_id, language=language)

    try:
        while True:
            data = await ws.receive()

            if data["type"] == "websocket.disconnect":
                break

            if data.get("bytes"):
                chunk: bytes = data["bytes"]
                audio_buffer.extend(chunk)

                if vad.process_chunk(chunk) and len(audio_buffer) > 0:
                    try:
                        user_text, assistant_text = await engine.process_turn(
                            bytes(audio_buffer), language, history, ws
                        )
                        if user_text:
                            history.append({"role": "user", "content": user_text})
                            history.append({"role": "assistant", "content": assistant_text})
                    except Exception as exc:
                        log.error("turn_error", error=str(exc), session_id=session_id)
                        await ws.send_json({"type": "error", "message": str(exc)})
                    finally:
                        audio_buffer.clear()
                        vad.reset()

            elif data.get("text"):
                try:
                    msg = json.loads(data["text"])
                except json.JSONDecodeError:
                    await ws.send_json({"type": "error", "message": "Invalid JSON"})
                    continue

                msg_type = msg.get("type")
                if msg_type == "start":
                    language = msg.get("language", language)
                    await ws.send_json(
                        {"type": "ready", "session_id": session_id, "language": language}
                    )
                elif msg_type == "stop":
                    break

    except WebSocketDisconnect:
        pass
    finally:
        session.status = "ended"
        session.ended_at = datetime.now(tz=timezone.utc)
        session.turn_count = len(history) // 2
        session.transcript_json = json.dumps(history)
        try:
            await db.commit()
        except Exception:
            pass
        log.info(
            "ws_disconnected",
            session_id=session_id,
            turns=session.turn_count,
        )
