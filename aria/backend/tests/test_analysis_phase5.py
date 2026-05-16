"""Gate 5 tests — Alice_Analysis (Phase 5).

Covers: comprehension quiz generation, grammar spotlight generation,
voice blueprints, extended pipeline, extended analyze endpoint,
grammar deficits endpoint, and text practice upload endpoint.
All tests run without GPU or Ollama.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_speaker_segment(text="Hello world", start=0.0, end=2.0, speaker="SPEAKER_00", lang="en"):
    from aria.backend.modules.analysis.pipeline import SpeakerSegment
    return SpeakerSegment(text=text, start=start, end=end, speaker=speaker, language=lang)


def _make_quiz_json():
    return json.dumps([
        {
            "question": "What did the speaker mention?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct": 0,
            "explanation": "The speaker said hello.",
        }
    ])


def _make_grammar_json():
    return json.dumps([
        {
            "rule": "Past tense formation",
            "example": "I goed to the store",
            "correction": "I went to the store",
            "frequency": 2,
        }
    ])


def _make_llm_quiz_response():
    return json.dumps([
        {
            "question": "What topic was discussed?",
            "options": ["Topic A", "Topic B", "Topic C", "Topic D"],
            "correct": 1,
            "explanation": "The transcript covered topic B.",
        }
    ])


def _make_llm_grammar_response():
    return json.dumps([
        {
            "rule": "Subject-verb agreement",
            "example": "He go to the store",
            "correction": "He goes to the store",
            "frequency": 3,
        }
    ])


def _make_llm_text_analysis_response():
    return json.dumps({
        "detected_language": "en",
        "vocabulary": [
            {"word": "ubiquitous", "cefr_level": "C1", "definition": "present everywhere"},
        ],
        "quiz": [
            {
                "question": "What does ubiquitous mean?",
                "options": ["Rare", "Present everywhere", "Unknown", "Temporary"],
                "correct": 1,
                "explanation": "Ubiquitous means present everywhere.",
            }
        ],
        "grammar_spotlights": [
            {
                "rule": "Passive voice",
                "example": "The ball was kicked",
                "correction": "Correct usage",
                "frequency": 1,
            }
        ],
    })


# ── TestQuizModule ─────────────────────────────────────────────────────────────

class TestQuizModule:
    """analysis/quiz.py — LLM-driven quiz generation."""

    def test_quiz_module_importable(self):
        from aria.backend.modules.analysis.quiz import generate_quiz
        assert callable(generate_quiz)

    @pytest.mark.asyncio
    async def test_quiz_returns_list_from_llm(self):
        from aria.backend.modules.analysis.quiz import generate_quiz
        llm = AsyncMock()
        llm.generate_complete = AsyncMock(return_value=_make_llm_quiz_response())
        result = await generate_quiz("Hello world, this is a test.", "en", llm)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["question"] == "What topic was discussed?"
        assert len(result[0]["options"]) == 4
        assert result[0]["correct"] == 1

    @pytest.mark.asyncio
    async def test_quiz_empty_transcript_returns_empty(self):
        from aria.backend.modules.analysis.quiz import generate_quiz
        llm = AsyncMock()
        result = await generate_quiz("", "en", llm)
        assert result == []
        llm.generate_complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_quiz_whitespace_only_returns_empty(self):
        from aria.backend.modules.analysis.quiz import generate_quiz
        llm = AsyncMock()
        result = await generate_quiz("   \n\t  ", "en", llm)
        assert result == []

    @pytest.mark.asyncio
    async def test_quiz_llm_error_returns_empty(self):
        from aria.backend.modules.analysis.quiz import generate_quiz
        llm = AsyncMock()
        llm.generate_complete = AsyncMock(side_effect=RuntimeError("LLM offline"))
        result = await generate_quiz("Some transcript text here.", "en", llm)
        assert result == []

    @pytest.mark.asyncio
    async def test_quiz_invalid_json_returns_empty(self):
        from aria.backend.modules.analysis.quiz import generate_quiz
        llm = AsyncMock()
        llm.generate_complete = AsyncMock(return_value="not json at all")
        result = await generate_quiz("Some transcript text here.", "en", llm)
        assert result == []

    @pytest.mark.asyncio
    async def test_quiz_missing_options_skips_item(self):
        from aria.backend.modules.analysis.quiz import generate_quiz
        llm = AsyncMock()
        bad = json.dumps([{"question": "Q?", "options": ["A", "B"], "correct": 0, "explanation": ""}])
        llm.generate_complete = AsyncMock(return_value=bad)
        result = await generate_quiz("Transcript.", "en", llm)
        assert result == []


# ── TestGrammarModule ─────────────────────────────────────────────────────────

class TestGrammarModule:
    """analysis/grammar.py — LLM-driven grammar spotlight generation."""

    def test_grammar_module_importable(self):
        from aria.backend.modules.analysis.grammar import generate_grammar_spotlight
        assert callable(generate_grammar_spotlight)

    @pytest.mark.asyncio
    async def test_grammar_returns_list_from_llm(self):
        from aria.backend.modules.analysis.grammar import generate_grammar_spotlight
        llm = AsyncMock()
        llm.generate_complete = AsyncMock(return_value=_make_llm_grammar_response())
        result = await generate_grammar_spotlight("He go to the store.", "en", llm)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["rule"] == "Subject-verb agreement"
        assert result[0]["frequency"] == 3

    @pytest.mark.asyncio
    async def test_grammar_empty_transcript_returns_empty(self):
        from aria.backend.modules.analysis.grammar import generate_grammar_spotlight
        llm = AsyncMock()
        result = await generate_grammar_spotlight("", "en", llm)
        assert result == []
        llm.generate_complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_grammar_llm_error_returns_empty(self):
        from aria.backend.modules.analysis.grammar import generate_grammar_spotlight
        llm = AsyncMock()
        llm.generate_complete = AsyncMock(side_effect=RuntimeError("LLM offline"))
        result = await generate_grammar_spotlight("I goed to the store.", "en", llm)
        assert result == []

    @pytest.mark.asyncio
    async def test_grammar_invalid_json_returns_empty(self):
        from aria.backend.modules.analysis.grammar import generate_grammar_spotlight
        llm = AsyncMock()
        llm.generate_complete = AsyncMock(return_value="not json")
        result = await generate_grammar_spotlight("Transcript.", "en", llm)
        assert result == []

    @pytest.mark.asyncio
    async def test_grammar_capped_at_five_items(self):
        from aria.backend.modules.analysis.grammar import generate_grammar_spotlight
        llm = AsyncMock()
        many = json.dumps([
            {"rule": f"Rule {i}", "example": "ex", "correction": "cor", "frequency": 1}
            for i in range(10)
        ])
        llm.generate_complete = AsyncMock(return_value=many)
        result = await generate_grammar_spotlight("Transcript.", "en", llm)
        assert len(result) <= 5


# ── TestVoiceBlueprint ────────────────────────────────────────────────────────

class TestVoiceBlueprint:
    """analysis/voice_blueprint.py — statistical voice blueprint computation."""

    def test_voice_blueprint_importable(self):
        from aria.backend.modules.analysis.voice_blueprint import compute_voice_blueprints
        assert callable(compute_voice_blueprints)

    def test_voice_blueprint_empty_segments_returns_empty(self):
        from aria.backend.modules.analysis.voice_blueprint import compute_voice_blueprints
        result = compute_voice_blueprints([])
        assert result == []

    def test_voice_blueprint_single_speaker(self):
        from aria.backend.modules.analysis.voice_blueprint import compute_voice_blueprints
        segs = [_make_speaker_segment("Hello world", 0.0, 2.0, "SPEAKER_00")]
        result = compute_voice_blueprints(segs)
        assert len(result) == 1
        assert result[0]["speaker"] == "SPEAKER_00"

    def test_voice_blueprint_wpm_calculation(self):
        from aria.backend.modules.analysis.voice_blueprint import compute_voice_blueprints
        # 60 words in 60 seconds → 60 WPM
        words = " ".join(["word"] * 60)
        segs = [_make_speaker_segment(words, 0.0, 60.0, "SPEAKER_00")]
        result = compute_voice_blueprints(segs)
        assert result[0]["tempo_wpm"] == pytest.approx(60.0, abs=0.1)

    def test_voice_blueprint_filler_word_detection(self):
        from aria.backend.modules.analysis.voice_blueprint import compute_voice_blueprints
        segs = [_make_speaker_segment("um uh like you know basically", 0.0, 5.0, "SPEAKER_00")]
        result = compute_voice_blueprints(segs)
        assert result[0]["filler_word_count"] >= 3

    def test_voice_blueprint_vocabulary_richness(self):
        from aria.backend.modules.analysis.voice_blueprint import compute_voice_blueprints
        # All unique words → richness = 1.0
        segs = [_make_speaker_segment("alpha beta gamma delta", 0.0, 4.0, "SPEAKER_00")]
        result = compute_voice_blueprints(segs)
        assert result[0]["vocabulary_richness"] == pytest.approx(1.0)

    def test_voice_blueprint_repetition_lowers_richness(self):
        from aria.backend.modules.analysis.voice_blueprint import compute_voice_blueprints
        # "word word word word" → 1 unique / 4 total = 0.25
        segs = [_make_speaker_segment("word word word word", 0.0, 4.0, "SPEAKER_00")]
        result = compute_voice_blueprints(segs)
        assert result[0]["vocabulary_richness"] == pytest.approx(0.25)

    def test_voice_blueprint_multiple_speakers(self):
        from aria.backend.modules.analysis.voice_blueprint import compute_voice_blueprints
        segs = [
            _make_speaker_segment("Hello there", 0.0, 2.0, "SPEAKER_00"),
            _make_speaker_segment("Good morning", 2.0, 4.0, "SPEAKER_01"),
        ]
        result = compute_voice_blueprints(segs)
        assert len(result) == 2
        speakers = {bp["speaker"] for bp in result}
        assert speakers == {"SPEAKER_00", "SPEAKER_01"}

    def test_voice_blueprint_zero_duration_segment_handled(self):
        from aria.backend.modules.analysis.voice_blueprint import compute_voice_blueprints
        segs = [_make_speaker_segment("Hello", 0.0, 0.0, "SPEAKER_00")]
        result = compute_voice_blueprints(segs)
        assert result[0]["tempo_wpm"] == 0.0

    def test_voice_blueprint_schema_keys_present(self):
        from aria.backend.modules.analysis.voice_blueprint import compute_voice_blueprints
        segs = [_make_speaker_segment("test", 0.0, 1.0, "SPEAKER_00")]
        result = compute_voice_blueprints(segs)
        assert "speaker" in result[0]
        assert "tempo_wpm" in result[0]
        assert "filler_word_count" in result[0]
        assert "vocabulary_richness" in result[0]


# ── TestExtendedPipeline ──────────────────────────────────────────────────────

class TestExtendedPipeline:
    """PipelineResult dataclass has Phase 5 fields with correct defaults."""

    def test_pipeline_result_has_quiz_field(self):
        from aria.backend.modules.analysis.pipeline import PipelineResult
        import dataclasses
        fields = {f.name for f in dataclasses.fields(PipelineResult)}
        assert "quiz" in fields

    def test_pipeline_result_has_grammar_field(self):
        from aria.backend.modules.analysis.pipeline import PipelineResult
        import dataclasses
        fields = {f.name for f in dataclasses.fields(PipelineResult)}
        assert "grammar_spotlights" in fields

    def test_pipeline_result_has_blueprints_field(self):
        from aria.backend.modules.analysis.pipeline import PipelineResult
        import dataclasses
        fields = {f.name for f in dataclasses.fields(PipelineResult)}
        assert "voice_blueprints" in fields

    def test_pipeline_result_defaults_to_empty_lists(self):
        from aria.backend.modules.analysis.pipeline import PipelineResult
        result = PipelineResult(
            segments=[],
            language="en",
            duration_seconds=1.0,
            num_speakers=1,
            fluency_score=None,
        )
        assert result.quiz == []
        assert result.grammar_spotlights == []
        assert result.voice_blueprints == []

    @pytest.mark.asyncio
    async def test_pipeline_run_includes_quiz(self, tmp_path):
        import io
        import struct
        import wave
        from unittest.mock import AsyncMock
        from aria.backend.modules.analysis.pipeline import AnalysisPipeline
        from aria.backend.services.interfaces import (
            DiarizationResult, TranscriptResult, TranscriptSegment,
        )

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(struct.pack("<160h", *([0] * 160)))
        audio = tmp_path / "test.wav"
        audio.write_bytes(buf.getvalue())

        stt = AsyncMock()
        stt.transcribe_file = AsyncMock(return_value=TranscriptResult(
            segments=[TranscriptSegment("Hello world", 0.0, 1.0, language="en")],
            language="en",
            duration_seconds=1.0,
        ))
        diar = AsyncMock()
        diar.diarise = AsyncMock(return_value=DiarizationResult(segments=[], num_speakers=1))
        llm = AsyncMock()
        # First call → fluency/vocab; second → quiz; third → grammar
        llm.generate_complete = AsyncMock(side_effect=[
            json.dumps({"fluency_score": 0.7, "vocabulary": ["hello"]}),
            _make_llm_quiz_response(),
            _make_llm_grammar_response(),
        ])

        pipeline = AnalysisPipeline(stt=stt, diarization=diar, llm=llm)
        result = await pipeline.run(audio, "en")

        assert isinstance(result.quiz, list)
        assert isinstance(result.grammar_spotlights, list)
        assert isinstance(result.voice_blueprints, list)
        assert len(result.quiz) == 1
        assert len(result.grammar_spotlights) == 1
        assert len(result.voice_blueprints) == 1  # one speaker


# ── TestExtendedAnalysisEndpoint ──────────────────────────────────────────────

class TestExtendedAnalysisEndpoint:
    """POST /api/v1/sessions/analyze returns Phase 5 fields."""

    @pytest_asyncio.fixture
    async def client_with_phase5_pipeline(self):
        from aria.backend.main import app
        from aria.backend.modules.analysis.router import get_pipeline
        from aria.backend.modules.analysis.pipeline import AnalysisPipeline, PipelineResult, SpeakerSegment
        from httpx import ASGITransport, AsyncClient

        mock_pipeline = AsyncMock(spec=AnalysisPipeline)
        mock_pipeline.run = AsyncMock(return_value=PipelineResult(
            segments=[SpeakerSegment(text="Hello", start=0.0, end=1.0, speaker="SPEAKER_00", language="en")],
            language="en",
            duration_seconds=1.0,
            num_speakers=1,
            fluency_score=0.8,
            vocabulary=["hello"],
            quiz=[{
                "question": "What was said?",
                "options": ["A", "B", "C", "D"],
                "correct": 0,
                "explanation": "Hello was said.",
            }],
            grammar_spotlights=[{
                "rule": "Past tense",
                "example": "I goed",
                "correction": "I went",
                "frequency": 1,
            }],
            voice_blueprints=[{
                "speaker": "SPEAKER_00",
                "tempo_wpm": 60.0,
                "filler_word_count": 0,
                "vocabulary_richness": 1.0,
            }],
        ))

        app.dependency_overrides[get_pipeline] = lambda: mock_pipeline
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac, mock_pipeline
        app.dependency_overrides.pop(get_pipeline, None)

    def _make_wav(self):
        import io
        import struct
        import wave
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(struct.pack("<160h", *([0] * 160)))
        return buf.getvalue()

    @pytest.mark.asyncio
    async def test_analyze_response_has_quiz_field(self, client_with_phase5_pipeline):
        ac, _ = client_with_phase5_pipeline
        resp = await ac.post(
            "/api/v1/sessions/analyze",
            files={"audio": ("test.wav", self._make_wav(), "audio/wav")},
        )
        assert resp.status_code == 200
        assert "quiz" in resp.json()

    @pytest.mark.asyncio
    async def test_analyze_response_has_grammar_spotlights_field(self, client_with_phase5_pipeline):
        ac, _ = client_with_phase5_pipeline
        resp = await ac.post(
            "/api/v1/sessions/analyze",
            files={"audio": ("test.wav", self._make_wav(), "audio/wav")},
        )
        assert resp.status_code == 200
        assert "grammar_spotlights" in resp.json()

    @pytest.mark.asyncio
    async def test_analyze_response_has_voice_blueprints_field(self, client_with_phase5_pipeline):
        ac, _ = client_with_phase5_pipeline
        resp = await ac.post(
            "/api/v1/sessions/analyze",
            files={"audio": ("test.wav", self._make_wav(), "audio/wav")},
        )
        assert resp.status_code == 200
        assert "voice_blueprints" in resp.json()

    @pytest.mark.asyncio
    async def test_analyze_response_quiz_is_list(self, client_with_phase5_pipeline):
        ac, _ = client_with_phase5_pipeline
        resp = await ac.post(
            "/api/v1/sessions/analyze",
            files={"audio": ("test.wav", self._make_wav(), "audio/wav")},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json()["quiz"], list)
        assert len(resp.json()["quiz"]) == 1

    @pytest.mark.asyncio
    async def test_analyze_response_quiz_question_schema(self, client_with_phase5_pipeline):
        ac, _ = client_with_phase5_pipeline
        resp = await ac.post(
            "/api/v1/sessions/analyze",
            files={"audio": ("test.wav", self._make_wav(), "audio/wav")},
        )
        assert resp.status_code == 200
        quiz = resp.json()["quiz"]
        assert len(quiz) == 1
        q = quiz[0]
        assert "question" in q
        assert "options" in q
        assert "correct" in q
        assert "explanation" in q
        assert len(q["options"]) == 4

    @pytest.mark.asyncio
    async def test_analyze_response_grammar_spotlights_schema(self, client_with_phase5_pipeline):
        ac, _ = client_with_phase5_pipeline
        resp = await ac.post(
            "/api/v1/sessions/analyze",
            files={"audio": ("test.wav", self._make_wav(), "audio/wav")},
        )
        assert resp.status_code == 200
        gs = resp.json()["grammar_spotlights"]
        assert len(gs) == 1
        assert "rule" in gs[0]
        assert "example" in gs[0]
        assert "correction" in gs[0]
        assert "frequency" in gs[0]

    @pytest.mark.asyncio
    async def test_analyze_response_voice_blueprints_schema(self, client_with_phase5_pipeline):
        ac, _ = client_with_phase5_pipeline
        resp = await ac.post(
            "/api/v1/sessions/analyze",
            files={"audio": ("test.wav", self._make_wav(), "audio/wav")},
        )
        assert resp.status_code == 200
        vb = resp.json()["voice_blueprints"]
        assert len(vb) == 1
        assert "speaker" in vb[0]
        assert "tempo_wpm" in vb[0]
        assert "filler_word_count" in vb[0]
        assert "vocabulary_richness" in vb[0]

    @pytest.mark.asyncio
    async def test_analyze_empty_quiz_when_pipeline_returns_empty(self, client):
        from aria.backend.main import app
        from aria.backend.modules.analysis.router import get_pipeline
        from aria.backend.modules.analysis.pipeline import AnalysisPipeline, PipelineResult, SpeakerSegment
        from httpx import ASGITransport, AsyncClient

        mock_pipeline = AsyncMock(spec=AnalysisPipeline)
        mock_pipeline.run = AsyncMock(return_value=PipelineResult(
            segments=[SpeakerSegment(text="Hi", start=0.0, end=1.0, speaker="SPEAKER_00", language="en")],
            language="en",
            duration_seconds=1.0,
            num_speakers=1,
            fluency_score=None,
        ))
        app.dependency_overrides[get_pipeline] = lambda: mock_pipeline
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            import io
            import struct
            import wave
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16000)
                wf.writeframes(struct.pack("<160h", *([0] * 160)))
            resp = await ac.post(
                "/api/v1/sessions/analyze",
                files={"audio": ("t.wav", buf.getvalue(), "audio/wav")},
            )
        app.dependency_overrides.pop(get_pipeline, None)
        assert resp.status_code == 200
        assert resp.json()["quiz"] == []
        assert resp.json()["grammar_spotlights"] == []
        assert resp.json()["voice_blueprints"] == []


# ── TestGrammarDeficitsEndpoint ───────────────────────────────────────────────

class TestGrammarDeficitsEndpoint:
    """GET /api/v1/grammar/deficits — aggregate grammar errors."""

    @pytest.mark.asyncio
    async def test_deficits_returns_200(self, client):
        resp = await client.get("/api/v1/grammar/deficits")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_deficits_returns_list(self, client):
        resp = await client.get("/api/v1/grammar/deficits")
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_deficits_ignores_null_grammar_json(self, client):
        from aria.backend.database import AsyncSessionFactory
        from aria.backend.modules.analysis.models import AnalysisSession

        # Insert a session with NULL grammar_json — should not affect deficits count
        async with AsyncSessionFactory() as db:
            session = AnalysisSession(
                audio_filename="no_grammar.wav",
                language="en",
                duration_seconds=5.0,
                num_speakers=1,
                transcript_json="[]",
                vocabulary_json="[]",
                grammar_json=None,
            )
            db.add(session)
            await db.commit()

        resp = await client.get("/api/v1/grammar/deficits")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # NULL grammar_json sessions must not introduce empty-rule entries
        for entry in data:
            assert entry["rule"] != ""
            assert entry["total_frequency"] > 0

    @pytest.mark.asyncio
    async def test_deficits_aggregates_across_sessions(self, client):
        from aria.backend.database import AsyncSessionFactory
        from aria.backend.modules.analysis.models import AnalysisSession

        grammar_data = json.dumps([
            {"rule": "Past tense", "example": "I goed", "correction": "I went", "frequency": 3},
            {"rule": "Article usage", "example": "a apple", "correction": "an apple", "frequency": 1},
        ])

        async with AsyncSessionFactory() as db:
            session = AnalysisSession(
                audio_filename="test.wav",
                language="en",
                duration_seconds=10.0,
                num_speakers=1,
                transcript_json="[]",
                vocabulary_json="[]",
                grammar_json=grammar_data,
            )
            db.add(session)
            await db.commit()

        resp = await client.get("/api/v1/grammar/deficits")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        rules = [d["rule"] for d in data]
        assert "Past tense" in rules

    @pytest.mark.asyncio
    async def test_deficits_ordered_by_frequency(self, client):
        from aria.backend.database import AsyncSessionFactory
        from aria.backend.modules.analysis.models import AnalysisSession

        grammar_data = json.dumps([
            {"rule": "Rare rule", "example": "ex", "correction": "cor", "frequency": 1},
            {"rule": "Common rule", "example": "ex", "correction": "cor", "frequency": 10},
        ])

        async with AsyncSessionFactory() as db:
            session = AnalysisSession(
                audio_filename="order_test.wav",
                language="en",
                duration_seconds=5.0,
                num_speakers=1,
                transcript_json="[]",
                vocabulary_json="[]",
                grammar_json=grammar_data,
            )
            db.add(session)
            await db.commit()

        resp = await client.get("/api/v1/grammar/deficits")
        assert resp.status_code == 200
        data = resp.json()
        if len(data) >= 2:
            # First entry should have higher frequency
            frequencies = [d["total_frequency"] for d in data]
            assert frequencies == sorted(frequencies, reverse=True)

    @pytest.mark.asyncio
    async def test_deficits_limited_to_five(self, client):
        from aria.backend.database import AsyncSessionFactory
        from aria.backend.modules.analysis.models import AnalysisSession

        grammar_data = json.dumps([
            {"rule": f"Rule {i}", "example": "ex", "correction": "cor", "frequency": i + 1}
            for i in range(10)
        ])

        async with AsyncSessionFactory() as db:
            session = AnalysisSession(
                audio_filename="many_rules.wav",
                language="en",
                duration_seconds=5.0,
                num_speakers=1,
                transcript_json="[]",
                vocabulary_json="[]",
                grammar_json=grammar_data,
            )
            db.add(session)
            await db.commit()

        resp = await client.get("/api/v1/grammar/deficits")
        assert resp.status_code == 200
        assert len(resp.json()) <= 5

    @pytest.mark.asyncio
    async def test_deficits_response_schema(self, client):
        from aria.backend.database import AsyncSessionFactory
        from aria.backend.modules.analysis.models import AnalysisSession

        async with AsyncSessionFactory() as db:
            session = AnalysisSession(
                audio_filename="schema_test.wav",
                language="en",
                duration_seconds=5.0,
                num_speakers=1,
                transcript_json="[]",
                vocabulary_json="[]",
                grammar_json=json.dumps([
                    {"rule": "Schema rule", "example": "ex", "correction": "cor", "frequency": 2}
                ]),
            )
            db.add(session)
            await db.commit()

        resp = await client.get("/api/v1/grammar/deficits")
        assert resp.status_code == 200
        data = resp.json()
        if data:
            d = data[0]
            assert "rule" in d
            assert "total_frequency" in d
            assert "example" in d


# ── TestTextPracticeEndpoint ──────────────────────────────────────────────────

class TestTextPracticeEndpoint:
    """POST /api/v1/text-practice/upload — text document analysis."""

    @pytest_asyncio.fixture
    async def client_with_mocks(self):
        from aria.backend.main import app
        from aria.backend.modules.text_practice.router import get_text_llm, get_text_translation
        from httpx import ASGITransport, AsyncClient

        mock_llm = AsyncMock()
        mock_llm.generate_complete = AsyncMock(return_value=_make_llm_text_analysis_response())

        mock_translation = AsyncMock()
        mock_translation.translate = AsyncMock(return_value="Übersetzter Text.")

        app.dependency_overrides[get_text_llm] = lambda: mock_llm
        app.dependency_overrides[get_text_translation] = lambda: mock_translation

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac, mock_llm, mock_translation

        app.dependency_overrides.pop(get_text_llm, None)
        app.dependency_overrides.pop(get_text_translation, None)

    @pytest.mark.asyncio
    async def test_text_upload_no_file_returns_422(self, client):
        resp = await client.post("/api/v1/text-practice/upload")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_text_upload_unsupported_format_returns_422(self, client_with_mocks):
        ac, _, _ = client_with_mocks
        resp = await ac.post(
            "/api/v1/text-practice/upload",
            files={"document": ("file.mp4", b"video content", "video/mp4")},
            data={"target_lang": "de"},
        )
        assert resp.status_code == 422
        assert "Unsupported format" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_text_upload_too_large_returns_413(self, client_with_mocks):
        ac, _, _ = client_with_mocks
        big = b"x" * (11 * 1024 * 1024)
        resp = await ac.post(
            "/api/v1/text-practice/upload",
            files={"document": ("big.txt", big, "text/plain")},
            data={"target_lang": "de"},
        )
        assert resp.status_code == 413

    @pytest.mark.asyncio
    async def test_text_upload_txt_returns_200(self, client_with_mocks):
        ac, _, _ = client_with_mocks
        txt = b"This is a sample English text for language practice."
        resp = await ac.post(
            "/api/v1/text-practice/upload",
            files={"document": ("sample.txt", txt, "text/plain")},
            data={"target_lang": "de"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_text_upload_response_schema_fields(self, client_with_mocks):
        ac, _, _ = client_with_mocks
        txt = b"This is a sample English text."
        resp = await ac.post(
            "/api/v1/text-practice/upload",
            files={"document": ("sample.txt", txt, "text/plain")},
            data={"target_lang": "de"},
        )
        assert resp.status_code == 200
        body = resp.json()
        for field in ("detected_language", "translated_text", "vocabulary", "quiz", "grammar_spotlights"):
            assert field in body, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_text_upload_vocabulary_is_list(self, client_with_mocks):
        ac, _, _ = client_with_mocks
        txt = b"The quick brown fox."
        resp = await ac.post(
            "/api/v1/text-practice/upload",
            files={"document": ("sample.txt", txt, "text/plain")},
            data={"target_lang": "de"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json()["vocabulary"], list)

    @pytest.mark.asyncio
    async def test_text_upload_vocabulary_item_schema(self, client_with_mocks):
        ac, _, _ = client_with_mocks
        txt = b"Ubiquitous means present everywhere."
        resp = await ac.post(
            "/api/v1/text-practice/upload",
            files={"document": ("sample.txt", txt, "text/plain")},
            data={"target_lang": "de"},
        )
        assert resp.status_code == 200
        vocab = resp.json()["vocabulary"]
        assert len(vocab) >= 1
        item = vocab[0]
        assert "word" in item
        assert "cefr_level" in item
        assert "definition" in item

    @pytest.mark.asyncio
    async def test_text_upload_quiz_is_list(self, client_with_mocks):
        ac, _, _ = client_with_mocks
        txt = b"This is a test document."
        resp = await ac.post(
            "/api/v1/text-practice/upload",
            files={"document": ("sample.txt", txt, "text/plain")},
            data={"target_lang": "de"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json()["quiz"], list)

    @pytest.mark.asyncio
    async def test_text_upload_translation_called(self, client_with_mocks):
        ac, mock_llm, mock_translation = client_with_mocks
        txt = b"Hello, this is English text."
        resp = await ac.post(
            "/api/v1/text-practice/upload",
            files={"document": ("sample.txt", txt, "text/plain")},
            data={"target_lang": "de"},
        )
        assert resp.status_code == 200
        mock_translation.translate.assert_called_once()

    @pytest.mark.asyncio
    async def test_text_upload_same_lang_skips_translation(self, client_with_mocks):
        ac, mock_llm, mock_translation = client_with_mocks
        # LLM will return detected_language="en", target_lang="en" → no translation
        txt = b"Hello world in English."
        resp = await ac.post(
            "/api/v1/text-practice/upload",
            files={"document": ("sample.txt", txt, "text/plain")},
            data={"target_lang": "en"},
        )
        assert resp.status_code == 200
        mock_translation.translate.assert_not_called()

    @pytest.mark.asyncio
    async def test_text_upload_llm_failure_still_returns_200(self, client_with_mocks):
        ac, mock_llm, mock_translation = client_with_mocks
        mock_llm.generate_complete = AsyncMock(side_effect=RuntimeError("LLM offline"))
        txt = b"Some text content."
        resp = await ac.post(
            "/api/v1/text-practice/upload",
            files={"document": ("sample.txt", txt, "text/plain")},
            data={"target_lang": "de"},
        )
        # LLM failure → empty analysis, but endpoint still returns 200
        assert resp.status_code == 200
        body = resp.json()
        assert body["vocabulary"] == []
        assert body["quiz"] == []
