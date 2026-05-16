"""Conversation module router — WebSocket and REST endpoints.

WebSocket: /ws/v1/conversation/{session_id}
REST:      /api/v1/conversations/

Full implementation by Carlos_Conversation in Phase 4.
Sam_Architect provides the skeleton so main.py can import without error.
"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.post(
    "/",
    summary="Create a new conversation session",
    description=(
        "Creates a new conversation session. Returns a session_id used to "
        "connect the WebSocket at /ws/v1/conversation/{session_id}."
    ),
    responses={
        201: {"description": "Session created, session_id returned"},
        401: {"description": "Unauthenticated (anonymous sessions allowed in dev)"},
    },
)
async def create_session():
    """Create a conversation session and return its ID.

    Returns:
        Dict with session_id (UUID) and metadata.
    """
    # Carlos_Conversation (Phase 4) implements this.
    return {"detail": "Not implemented — Phase 4 (Carlos_Conversation)"}


@router.websocket("/ws/{session_id}")
async def conversation_websocket(session_id: str, ws: WebSocket):
    """WebSocket endpoint for live conversation.

    Full turn cycle: audio → VAD → STT → LLM → TTS → audio.
    Protocol documented in docs/modules/conversation.md.
    Implemented by Carlos_Conversation in Phase 4.
    """
    await ws.accept()
    await ws.send_json({"error": "Not implemented — Phase 4 (Carlos_Conversation)"})
    await ws.close()
