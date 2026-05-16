"""Pydantic schemas for the flashcards module.

Request and response models for the SM-2 spaced repetition endpoints.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, field_validator


class VocabItem(BaseModel):
    """A single vocabulary item used to seed a flashcard."""

    word: str
    cefr_level: str | None = None
    definition: str | None = None
    example_sentence: str | None = None


class FlashcardRead(BaseModel):
    """A single flashcard record."""

    id: uuid.UUID
    deck_id: uuid.UUID
    word: str
    cefr_level: str | None
    definition: str | None
    example_sentence: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FlashcardReviewRead(BaseModel):
    """SM-2 review state for a single card."""

    id: uuid.UUID
    flashcard_id: uuid.UUID
    ease_factor: float
    interval: int
    repetitions: int
    next_review: date
    last_reviewed: date | None

    model_config = {"from_attributes": True}


class FlashcardDeckRead(BaseModel):
    """A flashcard deck record."""

    id: uuid.UUID
    name: str
    source_language: str
    target_language: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FlashcardDueRead(BaseModel):
    """A card that is due for review, bundled with its SM-2 state."""

    card: FlashcardRead
    review: FlashcardReviewRead


class GenerateRequest(BaseModel):
    """Request body for POST /flashcards/generate."""

    deck_name: str = "My Vocabulary Deck"
    source_language: str = "en"
    target_language: str = "en"
    vocabulary: list[VocabItem]


class GenerateResponse(BaseModel):
    """Response from POST /flashcards/generate."""

    deck: FlashcardDeckRead
    cards_created: int
    cards: list[FlashcardRead]


class ReviewRequest(BaseModel):
    """Request body for POST /flashcards/review."""

    flashcard_id: uuid.UUID
    quality: int

    @field_validator("quality")
    @classmethod
    def validate_quality(cls, v: int) -> int:
        if not (0 <= v <= 5):
            raise ValueError("quality must be between 0 and 5")
        return v


class StatsRead(BaseModel):
    """Learning statistics response."""

    total_cards: int
    cards_due: int
    cards_mastered: int
