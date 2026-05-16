"""Pydantic schemas for the text practice module."""
from __future__ import annotations

from pydantic import BaseModel


class CEFRVocabItem(BaseModel):
    """A vocabulary item with CEFR proficiency level."""

    word: str
    cefr_level: str
    definition: str


class TextQuizQuestion(BaseModel):
    """A comprehension quiz question with four answer options."""

    question: str
    options: list[str]
    correct: int
    explanation: str


class TextGrammarSpotlight(BaseModel):
    """A grammar pattern identified in the text."""

    rule: str
    example: str
    correction: str
    frequency: int


class TextPracticeRead(BaseModel):
    """Complete result returned from POST /api/v1/text-practice/upload."""

    detected_language: str
    translated_text: str
    vocabulary: list[CEFRVocabItem]
    quiz: list[TextQuizQuestion]
    grammar_spotlights: list[TextGrammarSpotlight]
