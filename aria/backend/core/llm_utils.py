"""LLM output utilities — ported from Transcribit v6.

parse_json_from_llm() is the single source of truth for extracting JSON from
LLM responses across all passes. It handles markdown fences, truncated arrays,
trailing commas, and partial objects.
"""
from __future__ import annotations

import json
import re

from aria.backend.core.logging import get_logger

log = get_logger(__name__)


def parse_json_from_llm(text: str | None) -> list | dict | None:
    """Robustly extract JSON from an LLM response string.

    Handles: markdown fences, extra surrounding text, truncated arrays,
    trailing commas, and partial objects caused by token limits.

    Args:
        text: Raw LLM output string, possibly wrapped in markdown fences.

    Returns:
        Parsed Python list or dict, or None if no valid JSON could be extracted.
    """
    if not text:
        return None

    clean = re.sub(r"```(?:json)?|```", "", text).strip()

    # 1. Try clean well-formed array
    m = re.search(r"\[.*\]", clean, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    # 2. Array truncated mid-stream — recovery before object match so we don't
    # return just the first element when the array is incomplete.
    m = re.search(r"\[.*", clean, re.DOTALL)
    if m:
        fragment = m.group(0)
        fragment = re.sub(r",\s*\{[^}]*$", "", fragment)
        fragment = re.sub(r",\s*$", "", fragment.rstrip())
        if not fragment.endswith("]"):
            fragment += "]"
        try:
            return json.loads(fragment)
        except json.JSONDecodeError:
            pass

    # 3. Try clean well-formed object
    m = re.search(r"\{.*\}", clean, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    # 4. Line-by-line extraction — recover {"id":N,"speaker":"X"} objects
    items: list[dict] = []
    for line in clean.split("\n"):
        m = re.search(r'"id"\s*:\s*(\d+).*?"speaker"\s*:\s*"([^"]+)"', line)
        if m:
            items.append({"id": int(m.group(1)), "speaker": m.group(2)})
            continue
        m = re.search(r'"speaker"\s*:\s*"([^"]+)".*?"id"\s*:\s*(\d+)', line)
        if m:
            items.append({"id": int(m.group(2)), "speaker": m.group(1)})

    if items:
        log.warning("llm_json_recovered_via_line_extraction", count=len(items))
        return items

    log.error("llm_json_parse_failed", raw_length=len(text))
    return None


def build_system_prompt_suffix(feedback_lang: str, feedback_lang_name: str) -> str:
    """Return the language-enforcement suffix appended to every LLM system prompt.

    Args:
        feedback_lang: BCP-47 language code (e.g. "de", "en", "fr").
        feedback_lang_name: Human-readable name in English (e.g. "German").

    Returns:
        Instruction string that forces the LLM to respond in the user's
        feedback language across all output fields.
    """
    return (
        f"\n\nIMPORTANT: Deliver ALL feedback, corrections, grammar explanations, "
        f"quiz questions, and hints in {feedback_lang_name} (language code: {feedback_lang}). "
        f"Do not switch languages mid-response. "
        f"Do not include any user audio content in this response. "
        f"Do not train on or store user data."
    )

