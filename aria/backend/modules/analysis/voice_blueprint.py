"""Voice blueprint computation — Pass 6 of the analysis pipeline.

Pure-Python statistical analysis of speaker segments: no GPU, no LLM.
Computes per-speaker tempo, filler-word count, and vocabulary richness.
"""
from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aria.backend.modules.analysis.pipeline import SpeakerSegment

# Common filler words across all five target languages
_FILLER_WORDS: frozenset[str] = frozenset({
    # English
    "um", "uh", "like", "basically", "literally", "actually", "well",
    "so", "right", "okay", "ok", "you", "know",
    # German
    "äh", "ähm", "ne", "nä", "quasi", "eigentlich", "irgendwie", "sozusagen",
    # French
    "euh", "ben", "voilà", "bon", "alors",
    # Spanish
    "bueno", "pues", "este",
    # Italian
    "allora", "cioè", "tipo", "vabbè",
})

# Multi-word fillers (checked against joined word pairs)
_FILLER_BIGRAMS: frozenset[str] = frozenset({
    "you know", "o sea", "c'est", "je veux",
})


def compute_voice_blueprints(segments: list[SpeakerSegment]) -> list[dict]:
    """Compute per-speaker voice statistics from transcript segments.

    Args:
        segments: Speaker-labelled transcript segments from the pipeline.

    Returns:
        List of voice blueprint dicts, one per unique speaker, sorted by speaker label.
    """
    if not segments:
        return []

    speaker_segs: dict[str, list[SpeakerSegment]] = defaultdict(list)
    for seg in segments:
        speaker_segs[seg.speaker].append(seg)

    result = []
    for speaker in sorted(speaker_segs):
        segs = speaker_segs[speaker]
        all_words: list[str] = []
        total_duration = 0.0

        for seg in segs:
            words = seg.text.lower().split()
            all_words.extend(words)
            duration = seg.end - seg.start
            if duration > 0:
                total_duration += duration

        word_count = len(all_words)
        tempo_wpm = (word_count / total_duration * 60.0) if total_duration > 0 else 0.0

        # Filler word count: strip punctuation from each word before checking
        stripped = [w.strip(",.!?;:\"'()[]") for w in all_words]
        filler_count = sum(1 for w in stripped if w in _FILLER_WORDS)
        # Also check bigrams
        for i in range(len(stripped) - 1):
            if f"{stripped[i]} {stripped[i + 1]}" in _FILLER_BIGRAMS:
                filler_count += 1

        unique_words = set(stripped)
        vocab_richness = len(unique_words) / word_count if word_count > 0 else 0.0

        result.append({
            "speaker": speaker,
            "tempo_wpm": round(tempo_wpm, 2),
            "filler_word_count": filler_count,
            "vocabulary_richness": round(vocab_richness, 4),
        })

    return result
