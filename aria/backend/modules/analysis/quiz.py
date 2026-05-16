"""Comprehension quiz generation — Pass 5a of the analysis pipeline.

Asks the LLM to generate 3 multiple-choice questions from a transcript.
Soft failure: returns an empty list on any LLM or parse error so the
pipeline can complete without blocking on Ollama availability.
"""
from __future__ import annotations

import json

from aria.backend.core.llm_utils import parse_json_from_llm
from aria.backend.core.logging import get_logger
from aria.backend.services.interfaces import LLMService

log = get_logger(__name__)

_QUIZ_SYSTEM = (
    "You are a language learning assessment tool. "
    "Given a transcript, generate exactly 3 comprehension quiz questions.\n\n"
    "Return a JSON array with this exact structure:\n"
    '[\n'
    '  {\n'
    '    "question": "What did the speaker say about X?",\n'
    '    "options": ["Option A", "Option B", "Option C", "Option D"],\n'
    '    "correct": 0,\n'
    '    "explanation": "The speaker stated..."\n'
    '  }\n'
    "]\n"
    "correct is the 0-based index of the right answer in options.\n"
    "Return only valid JSON — no markdown, no explanation."
)


async def generate_quiz(
    transcript_text: str,
    language: str,
    llm: LLMService,
) -> list[dict]:
    """Generate comprehension quiz questions from a transcript.

    Args:
        transcript_text: Full transcript text to analyse.
        language: BCP-47 language code of the transcript.
        llm: Injected LLM service.

    Returns:
        List of quiz question dicts; empty on LLM failure or empty transcript.
    """
    if not transcript_text.strip():
        return []

    messages = [
        {
            "role": "user",
            "content": (
                f"Language: {language}\n\nTranscript:\n{transcript_text}\n\n"
                "Generate 3 comprehension questions."
            ),
        }
    ]
    try:
        raw = await llm.generate_complete(messages, system=_QUIZ_SYSTEM, max_tokens=1024)
        try:
            clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            parsed = json.loads(clean)
        except (json.JSONDecodeError, AttributeError):
            parsed = parse_json_from_llm(raw)
        if not isinstance(parsed, list):
            return []
        result = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            question = str(item.get("question", ""))
            options = item.get("options", [])
            correct = item.get("correct", 0)
            explanation = str(item.get("explanation", ""))
            if question and isinstance(options, list) and len(options) == 4:
                result.append({
                    "question": question,
                    "options": [str(o) for o in options],
                    "correct": int(correct),
                    "explanation": explanation,
                })
        return result
    except Exception as exc:
        log.warning("quiz_generation_failed", error=str(exc))
        return []
