"""Audio analysis pipeline — Pete_Pipeline (Phase 3) + Alice_Analysis (Phase 5).

Orchestrates a 6-pass pipeline:
  Pass 1: faster-whisper STT (transcribe_file) — segments + detected language
  Pass 2: pyannote diarization (diarise) — speaker-turn timeline
  Pass 3: Speaker assignment — max-overlap join between STT and diarization
  Pass 4: Ollama LLM — fluency score + vocabulary list
  Pass 5: Ollama LLM — comprehension quiz (5a) + grammar spotlight (5b)
  Pass 6: Pure-Python — per-speaker voice blueprints (tempo, fillers, richness)

LLM failures are soft: the pipeline returns empty lists rather than raising.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from aria.backend.core.exceptions import DiarizationError
from aria.backend.core.llm_utils import parse_json_from_llm
from aria.backend.core.logging import get_logger
from aria.backend.services.interfaces import (
    DiarizationResult,
    DiarizationSegment,
    DiarizationService,
    LLMService,
    STTService,
    TranscriptSegment,
)

log = get_logger(__name__)

_ANALYSIS_SYSTEM = (
    "You are a language learning assistant. Given a transcript, return a JSON object with:\n"
    '  "fluency_score": float 0.0–1.0 (1.0 = native-level fluency)\n'
    '  "vocabulary": list of up to 10 key vocabulary items from the transcript\n'
    "Return only valid JSON — no markdown, no explanation."
)


@dataclass
class SpeakerSegment:
    """Transcript segment with speaker label merged from diarization."""

    text: str
    start: float
    end: float
    speaker: str
    language: str

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "start": self.start,
            "end": self.end,
            "speaker": self.speaker,
            "language": self.language,
        }


@dataclass
class PipelineResult:
    """Complete output of a single AnalysisPipeline.run() call."""

    segments: list[SpeakerSegment]
    language: str
    duration_seconds: float
    num_speakers: int
    fluency_score: float | None
    vocabulary: list[str] = field(default_factory=list)
    # Phase 5 extensions
    quiz: list[dict] = field(default_factory=list)
    grammar_spotlights: list[dict] = field(default_factory=list)
    voice_blueprints: list[dict] = field(default_factory=list)


class AnalysisPipeline:
    """Orchestrates 6-pass audio analysis pipeline.

    Instantiated once per request via FastAPI dependency injection.

    Args:
        stt: Concrete STTService implementation.
        diarization: Concrete DiarizationService implementation.
        llm: Concrete LLMService implementation.
    """

    def __init__(
        self,
        stt: STTService,
        diarization: DiarizationService,
        llm: LLMService,
    ) -> None:
        self._stt = stt
        self._diarization = diarization
        self._llm = llm

    @staticmethod
    def _assign_speakers(
        transcript_segments: list[TranscriptSegment],
        diarization_segments: list[DiarizationSegment],
    ) -> list[SpeakerSegment]:
        """Assign speaker labels to transcript segments via max-overlap join.

        For each STT segment we find the diarization turn with the greatest
        time overlap and adopt its speaker label. Segments with no overlapping
        diarization turn default to "SPEAKER_00".
        """
        result: list[SpeakerSegment] = []
        for seg in transcript_segments:
            best_speaker = "SPEAKER_00"
            best_overlap = 0.0
            for diar in diarization_segments:
                overlap = min(seg.end, diar.end) - max(seg.start, diar.start)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = diar.speaker
            result.append(
                SpeakerSegment(
                    text=seg.text,
                    start=seg.start,
                    end=seg.end,
                    speaker=best_speaker,
                    language=seg.language,
                )
            )
        return result

    async def _analyse_with_llm(
        self,
        transcript_text: str,
        language: str,
    ) -> tuple[float | None, list[str]]:
        """Ask the LLM for a fluency score and key vocabulary items.

        Returns (None, []) on any LLM failure so the pipeline can still
        complete without blocking on Ollama availability.
        """
        if not transcript_text.strip():
            return None, []

        messages = [
            {
                "role": "user",
                "content": (
                    f"Language: {language}\n\nTranscript:\n{transcript_text}\n\n"
                    "Return the JSON analysis."
                ),
            }
        ]
        try:
            raw = await self._llm.generate_complete(
                messages, system=_ANALYSIS_SYSTEM, max_tokens=512
            )
            # Try direct parse first — parse_json_from_llm's array-first heuristic
            # would match embedded vocabulary lists before the outer object.
            import json as _json
            try:
                clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
                parsed = _json.loads(clean)
            except (_json.JSONDecodeError, AttributeError):
                parsed = parse_json_from_llm(raw)
            if not isinstance(parsed, dict):
                return None, []
            fluency = parsed.get("fluency_score")
            vocab = parsed.get("vocabulary", [])
            fluency = float(fluency) if fluency is not None else None
            vocab = [str(v) for v in vocab] if isinstance(vocab, list) else []
            return fluency, vocab
        except Exception as exc:
            log.warning("llm_analysis_failed", error=str(exc))
            return None, []

    async def run(
        self,
        path: Path,
        language: str = "auto",
    ) -> PipelineResult:
        """Run the full 6-pass analysis pipeline on an audio file.

        Args:
            path: Absolute path to the audio file (already validated).
            language: BCP-47 code or "auto" for faster-whisper detection.

        Returns:
            PipelineResult with speaker-labelled segments and all LLM analysis.

        Raises:
            STTError: If transcription fails — no result available.
        """
        log.info("pipeline_start", path=str(path), language=language)

        # Pass 1: STT — hard failure if this fails
        transcript = await self._stt.transcribe_file(path, language)
        log.info(
            "pipeline_stt_done",
            segments=len(transcript.segments),
            language=transcript.language,
            duration=transcript.duration_seconds,
        )

        # Pass 2: Diarization — soft failure (default to single speaker)
        try:
            diarization = await self._diarization.diarise(path)
            log.info(
                "pipeline_diar_done",
                speakers=diarization.num_speakers,
                turns=len(diarization.segments),
            )
        except DiarizationError as exc:
            log.warning("pipeline_diar_failed_using_single_speaker", error=str(exc))
            diarization = DiarizationResult(segments=[], num_speakers=1)

        # Pass 3: Speaker assignment
        speaker_segments = self._assign_speakers(
            transcript.segments, diarization.segments
        )

        # Pass 4: LLM analysis — soft failure
        fluency, vocabulary = await self._analyse_with_llm(
            transcript.full_text, transcript.language
        )
        log.info("pipeline_llm_done", fluency=fluency, vocab_count=len(vocabulary))

        # Pass 5: Comprehension quiz + grammar spotlight — soft failure
        from aria.backend.modules.analysis.quiz import generate_quiz
        from aria.backend.modules.analysis.grammar import generate_grammar_spotlight

        quiz = await generate_quiz(transcript.full_text, transcript.language, self._llm)
        grammar_spotlights = await generate_grammar_spotlight(
            transcript.full_text, transcript.language, self._llm
        )
        log.info(
            "pipeline_pass5_done",
            quiz_questions=len(quiz),
            grammar_rules=len(grammar_spotlights),
        )

        # Pass 6: Voice blueprints — pure Python, no failure path
        from aria.backend.modules.analysis.voice_blueprint import compute_voice_blueprints

        voice_blueprints = compute_voice_blueprints(speaker_segments)
        log.info("pipeline_pass6_done", blueprints=len(voice_blueprints))

        return PipelineResult(
            segments=speaker_segments,
            language=transcript.language,
            duration_seconds=transcript.duration_seconds,
            num_speakers=diarization.num_speakers or 1,
            fluency_score=fluency,
            vocabulary=vocabulary,
            quiz=quiz,
            grammar_spotlights=grammar_spotlights,
            voice_blueprints=voice_blueprints,
        )
