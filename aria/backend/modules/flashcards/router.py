"""Flashcards module router — SM-2 spaced repetition API.

Full implementation by Felix_Flashcards in Phase 5.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/due",
    summary="Get cards due for review",
    description="Returns flashcards due today, ordered by SM-2 priority. Requires authentication.",
)
async def get_due():
    return {"detail": "Not implemented — Phase 5 (Felix_Flashcards)"}


@router.post(
    "/review",
    summary="Submit a card review",
    description="Submit user rating (0-5) for a card. Updates SM-2 interval and ease factor.",
)
async def submit_review():
    return {"detail": "Not implemented — Phase 5 (Felix_Flashcards)"}


@router.post(
    "/generate",
    summary="Generate flashcards from session vocabulary",
    description=(
        "Auto-generates flashcard cards from the 20 hardest words in a session. "
        "Each card includes: word, phonetic, TTS audio, definition, usage example, "
        "mnemonic, etymology, and 3 learning-style tips."
    ),
)
async def generate_cards():
    return {"detail": "Not implemented — Phase 5 (Felix_Flashcards)"}


@router.get(
    "/stats",
    summary="Get learning statistics",
    description="Returns retention rate, streak, cards mastered, and daily progress.",
)
async def get_stats():
    return {"detail": "Not implemented — Phase 5 (Felix_Flashcards)"}
