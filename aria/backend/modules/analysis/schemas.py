"""Pydantic schemas for the analysis module.

Request and response models for POST /api/v1/sessions/analyze.
Extended in Phase 5 (Alice_Analysis) with quiz, grammar spotlight, and voice blueprint fields.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class SpeakerSegmentRead(BaseModel):
    """A single speaker-labelled transcript segment."""

    text: str
    start: float
    end: float
    speaker: str
    language: str


class QuizQuestion(BaseModel):
    """A single comprehension quiz question with four answer options."""

    question: str
    options: list[str]
    correct: int
    explanation: str


class GrammarSpotlight(BaseModel):
    """A grammar pattern or error identified in the transcript."""

    rule: str
    example: str
    correction: str
    frequency: int


class VoiceBlueprint(BaseModel):
    """Per-speaker vocal statistics derived from transcript segments."""

    speaker: str
    tempo_wpm: float
    filler_word_count: int
    vocabulary_richness: float


class AnalysisSessionRead(BaseModel):
    """Complete analysis result returned from POST /api/v1/sessions/analyze."""

    id: uuid.UUID
    created_at: datetime
    audio_filename: str
    language: str
    duration_seconds: float
    num_speakers: int
    segments: list[SpeakerSegmentRead]
    fluency_score: float | None
    vocabulary: list[str]
    status: str

    # Phase 5 extensions
    quiz: list[QuizQuestion] = []
    grammar_spotlights: list[GrammarSpotlight] = []
    voice_blueprints: list[VoiceBlueprint] = []

    model_config = {"from_attributes": True}
