"""Pydantic schemas for the analysis module.

Request and response models for POST /api/v1/sessions/analyze.
Alice_Analysis (Phase 5) will extend AnalysisSessionRead with quiz,
grammar spotlight, and voice blueprint fields.
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

    model_config = {"from_attributes": True}
