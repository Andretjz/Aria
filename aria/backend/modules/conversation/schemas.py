"""Pydantic schemas for the conversation module.

ConversationSessionCreate  — request body for POST /api/v1/conversations/
ConversationSessionRead    — response for session creation and GET
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


SUPPORTED_LANGUAGES = {"de", "en", "es", "fr", "it"}


class ConversationSessionCreate(BaseModel):
    language: str = "en"

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language '{v}'. Supported: {', '.join(sorted(SUPPORTED_LANGUAGES))}"
            )
        return v


class ConversationSessionRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    created_at: datetime
    language: str
    status: str
    turn_count: int
    ended_at: datetime | None = None
