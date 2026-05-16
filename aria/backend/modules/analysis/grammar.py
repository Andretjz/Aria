"""Grammar spotlight generation — Pass 5b of the analysis pipeline.

Asks the LLM to identify the top grammar patterns or errors in a transcript.
Soft failure: returns an empty list on any LLM or parse error.
"""
from __future__ import annotations

import json

from aria.backend.core.llm_utils import parse_json_from_llm
from aria.backend.core.logging import get_logger
from aria.backend.services.interfaces import LLMService

log = get_logger(__name__)

_GRAMMAR_SYSTEM = (
    "You are a language learning grammar analyst. "
    "Given a transcript, identify up to 5 grammar patterns or errors.\n\n"
    "Return a JSON array with this exact structure:\n"
    '[\n'
    '  {\n'
    '    "rule": "Past tense formation",\n'
    '    "example": "I goed to the store",\n'
    '    "correction": "I went to the store",\n'
    '    "frequency": 2\n'
    '  }\n'
    "]\n"
    "frequency is how many times this pattern appears in the transcript.\n"
    "Return only valid JSON — no markdown, no explanation."
)


async def generate_grammar_spotlight(
    transcript_text: str,
    language: str,
    llm: LLMService,
) -> list[dict]:
    """Identify grammar patterns and errors in a transcript.

    Args:
        transcript_text: Full transcript text to analyse.
        language: BCP-47 language code of the transcript.
        llm: Injected LLM service.

    Returns:
        List of grammar spotlight dicts; empty on LLM failure or empty transcript.
    """
    if not transcript_text.strip():
        return []

    messages = [
        {
            "role": "user",
            "content": (
                f"Language: {language}\n\nTranscript:\n{transcript_text}\n\n"
                "Identify the top grammar patterns or errors."
            ),
        }
    ]
    try:
        raw = await llm.generate_complete(messages, system=_GRAMMAR_SYSTEM, max_tokens=1024)
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
            rule = str(item.get("rule", ""))
            example = str(item.get("example", ""))
            correction = str(item.get("correction", ""))
            frequency = item.get("frequency", 1)
            if rule:
                result.append({
                    "rule": rule,
                    "example": example,
                    "correction": correction,
                    "frequency": int(frequency),
                })
        return result[:5]
    except Exception as exc:
        log.warning("grammar_spotlight_failed", error=str(exc))
        return []
