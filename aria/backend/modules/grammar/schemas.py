"""Pydantic schemas for the grammar module."""
from __future__ import annotations

from pydantic import BaseModel


class GrammarDeficitRead(BaseModel):
    """Aggregated grammar deficit across analysis sessions."""

    rule: str
    total_frequency: int
    example: str | None
