# Gate 3 — Pipeline: STT, Diarization, Speaker Assignment, LLM Analysis

**Date:** 2026-05-16
**Agent:** Pete_Pipeline
**Branch:** `phase-3/pete-pipeline`
**Verdict:** APPROVED

---

## Checklist

### Provider Implementations
- [x] `FasterWhisperSTTService` — full implementation in `stt_whisper.py`; lazy model load, GPU/CPU, word timestamps, `transcribe_file` + `transcribe_stream`
- [x] `OllamaLLMService` — full implementation in `llm_ollama.py`; streaming via `/api/chat`, `is_available()` health check
- [x] `PyannoteService` — full implementation in `diarization_pyannote.py`; lazy pipeline load, GPU optional, `flush_gpu()` in `finally`
- [x] `ClaudeLLMService` — full implementation in `llm_claude.py`; Anthropic streaming with `cache_control` on system prompts

### Pipeline Orchestration (`modules/analysis/pipeline.py`)
- [x] `SpeakerSegment` — dataclass with `to_dict()` (text, start, end, speaker, language)
- [x] `PipelineResult` — dataclass with all pipeline outputs (segments, language, duration, num_speakers, fluency_score, vocabulary)
- [x] `AnalysisPipeline.__init__` — dependency-injected (stt, diarization, llm); testable without GPU
- [x] `AnalysisPipeline._assign_speakers()` — static max-overlap join: for each STT segment, finds diarization turn with greatest time overlap; defaults to `SPEAKER_00` when no diarization
- [x] `AnalysisPipeline._analyse_with_llm()` — asks LLM for `fluency_score` (0.0–1.0) + `vocabulary` list; direct `json.loads` first (avoids `parse_json_from_llm` array-first bias), falls back to recovery parser; soft-fails with `(None, [])` on any error
- [x] `AnalysisPipeline.run()` — 4-pass orchestration: STT (hard fail) → diarization (soft fail → single speaker) → speaker assignment → LLM analysis (soft fail)

### Analysis ORM Model (`modules/analysis/models.py`)
- [x] `AnalysisSession(Base)` — `analysis_sessions` table; id (UUID PK), user_id (nullable FK → user CASCADE), created_at, audio_filename, language, duration_seconds, num_speakers, transcript_json (Text), vocabulary_json (Text), fluency_score (nullable Float), status
- [x] `user_id` nullable — anonymous analysis allowed in dev; auth enforcement deferred to Phase 9

### Pydantic Schemas (`modules/analysis/schemas.py`)
- [x] `SpeakerSegmentRead` — text, start, end, speaker, language
- [x] `AnalysisSessionRead` — full response schema; `from_attributes=True` for ORM compatibility

### Analysis Endpoint (`modules/analysis/router.py`)
- [x] `POST /api/v1/sessions/analyze` — replaces 501 stub; returns `AnalysisSessionRead`
- [x] File size check (413 if > `MAX_UPLOAD_SIZE_MB`)
- [x] Extension validation against `SUPPORTED_EXTENSIONS` (422 for unsupported formats)
- [x] Temp file write → `pipeline.run()` → temp file cleanup in `finally`
- [x] `AnalysisSession` persisted to DB after successful run
- [x] `get_pipeline()` FastAPI dependency — overridable via `app.dependency_overrides` in tests
- [x] STTError/AudioFormatError translated to HTTP 500

### Database Migration
- [x] `002_create_analysis_tables.py` — creates `analysis_sessions` with all columns, FK to `user.id` (CASCADE), index on `user_id`; `downgrade()` implemented

### Test Infrastructure
- [x] `conftest.py` updated — `HF_TOKEN=fake-hf-token-for-tests` added so `get_diarization_service()` resolves in tests without real HuggingFace token; `aria.backend.modules.analysis.models` imported to register `AnalysisSession` with `Base.metadata`
- [x] Gate 1 + Gate 2 tests (36/36) still pass unmodified

### Gate 3 Tests
- [x] pytest 70/70 passed, 0 failed

```
tests/test_pipeline.py::TestProviders::test_faster_whisper_importable              PASSED
tests/test_pipeline.py::TestProviders::test_faster_whisper_supported_extensions    PASSED
tests/test_pipeline.py::TestProviders::test_faster_whisper_lazy_loads_model        PASSED
tests/test_pipeline.py::TestProviders::test_ollama_importable                      PASSED
tests/test_pipeline.py::TestProviders::test_ollama_default_args                    PASSED
tests/test_pipeline.py::TestProviders::test_ollama_is_available_returns_false_without_server PASSED
tests/test_pipeline.py::TestProviders::test_pyannote_importable                    PASSED
tests/test_pipeline.py::TestProviders::test_pyannote_lazy_loads_pipeline           PASSED
tests/test_pipeline.py::TestProviders::test_claude_llm_importable                  PASSED
tests/test_pipeline.py::TestSpeakerAssignment::test_single_speaker_single_segment  PASSED
tests/test_pipeline.py::TestSpeakerAssignment::test_two_speakers_assigned_correctly PASSED
tests/test_pipeline.py::TestSpeakerAssignment::test_empty_diarization_defaults_to_speaker_00 PASSED
tests/test_pipeline.py::TestSpeakerAssignment::test_empty_transcript_returns_empty PASSED
tests/test_pipeline.py::TestSpeakerAssignment::test_max_overlap_wins               PASSED
tests/test_pipeline.py::TestSpeakerAssignment::test_segment_to_dict               PASSED
tests/test_pipeline.py::TestPipelineRun::test_run_success                          PASSED
tests/test_pipeline.py::TestPipelineRun::test_run_assigns_speaker_to_segment      PASSED
tests/test_pipeline.py::TestPipelineRun::test_diarization_error_falls_back_to_single_speaker PASSED
tests/test_pipeline.py::TestPipelineRun::test_llm_error_returns_none_fluency       PASSED
tests/test_pipeline.py::TestPipelineRun::test_llm_invalid_json_returns_none_fluency PASSED
tests/test_pipeline.py::TestPipelineRun::test_empty_transcript_skips_llm          PASSED
tests/test_pipeline.py::TestAnalyzeEndpoint::test_analyze_no_file_returns_422     PASSED
tests/test_pipeline.py::TestAnalyzeEndpoint::test_analyze_unsupported_format_returns_422 PASSED
tests/test_pipeline.py::TestAnalyzeEndpoint::test_analyze_file_too_large_returns_413 PASSED
tests/test_pipeline.py::TestAnalyzeEndpoint::test_analyze_valid_wav_returns_200   PASSED
tests/test_pipeline.py::TestAnalyzeEndpoint::test_analyze_response_schema         PASSED
tests/test_pipeline.py::TestAnalyzeEndpoint::test_analyze_session_stored_in_db   PASSED
tests/test_pipeline.py::TestAnalyzeEndpoint::test_analyze_pipeline_called_with_language PASSED
tests/test_pipeline.py::TestVRAM::test_flush_gpu_does_not_raise                   PASSED
tests/test_pipeline.py::TestVRAM::test_vram_free_returns_float                    PASSED
tests/test_pipeline.py::TestVRAM::test_vram_total_returns_float                   PASSED
tests/test_pipeline.py::TestVRAM::test_gpu_info_schema                            PASSED
tests/test_pipeline.py::TestVRAM::test_flush_gpu_stable_across_calls              PASSED
tests/test_pipeline.py::TestVRAM::test_pyannote_calls_flush_gpu_on_diarization_error PASSED
70 passed in 7.77s
```

---

## Bugs Fixed During Phase 3

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| `fluency_score` always `None` in pipeline tests | `parse_json_from_llm` matches embedded `["vocab", "list"]` array via its array-first regex before finding the outer JSON object | Added direct `json.loads` attempt before falling back to `parse_json_from_llm` in `_analyse_with_llm` |
| `ConfigurationError: HF_TOKEN required` on endpoint tests using real `client` | `get_pipeline()` dependency resolved even for requests that fail validation (422) — calls `get_diarization_service()` which checks HF_TOKEN | Added `HF_TOKEN=fake-hf-token-for-tests` to conftest; `PyannoteService` is lazy-loaded so fake token is never used |

---

## Decisions Locked

- **4-pass pipeline order**: STT (hard fail) → diarization (soft fail → single speaker) → speaker assignment (static, no model) → LLM analysis (soft fail → `None` fluency)
- **Speaker assignment**: max-overlap join between STT segments and diarization turns; `O(N×M)` acceptable at session scale
- **LLM JSON parsing**: direct `json.loads` first to avoid `parse_json_from_llm` array heuristic; `parse_json_from_llm` kept as fallback for malformed Ollama output
- **AnalysisSession user_id**: nullable FK — anonymous analysis in dev; Phase 9 enforces billing per session
- **get_pipeline dependency**: non-cached FastAPI dependency; underlying services are `lru_cache`'d in factory; full override via `app.dependency_overrides` in tests
- **Alice_Analysis Phase 5** extends `AnalysisSessionRead` and the pipeline with comprehension quiz, grammar spotlight, and voice blueprints

---

## API Endpoints (new this phase)

```
POST /api/v1/sessions/analyze    → LIVE — upload audio → speaker-labelled transcript + fluency + vocab
```

## Next Phase

| Agent | Branch | Scope |
|-------|--------|-------|
| Carlos_Conversation | `phase-4/carlos-conversation` | WebSocket live conversation, VAD, turn detection, real-time STT→LLM→TTS cycle |
