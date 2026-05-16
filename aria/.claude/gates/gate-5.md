# Gate 5 — Analysis: Comprehension Quiz, Grammar Spotlight, Voice Blueprints, Text Practice

**Date:** 2026-05-16
**Agent:** Alice_Analysis
**Branch:** `phase-5/alice-analysis`
**Verdict:** APPROVED

---

## Checklist

### Comprehension Quiz (`modules/analysis/quiz.py`)
- [x] `generate_quiz` — async function; LLM generates exactly 3 multiple-choice questions from transcript
- [x] Empty/whitespace transcript → returns `[]` immediately without calling LLM
- [x] LLM failure (exception) → returns `[]` (soft failure)
- [x] Invalid JSON from LLM → returns `[]`
- [x] Malformed items (wrong options count) → skipped; only well-formed items returned
- [x] System prompt enforces 4-option structure with 0-based `correct` index

### Grammar Spotlight (`modules/analysis/grammar.py`)
- [x] `generate_grammar_spotlight` — async function; LLM identifies top grammar patterns/errors
- [x] Empty transcript → returns `[]` immediately
- [x] LLM failure → returns `[]` (soft failure)
- [x] Result capped at 5 items regardless of LLM output
- [x] Each item: `rule`, `example`, `correction`, `frequency`

### Voice Blueprints (`modules/analysis/voice_blueprint.py`)
- [x] `compute_voice_blueprints` — pure Python, no LLM, no GPU
- [x] Groups segments by speaker; returns one blueprint per unique speaker, sorted
- [x] `tempo_wpm` = (word_count / total_duration) * 60; 0.0 for zero-duration segments
- [x] `filler_word_count` — counts single-word and bigram fillers across 5 languages (de/en/es/fr/it)
- [x] `vocabulary_richness` = unique_word_count / total_word_count; 0.0 for empty
- [x] Empty segments list → returns `[]`
- [x] Circular import prevented via `TYPE_CHECKING` guard on `SpeakerSegment` import

### Extended AnalysisSession ORM (`modules/analysis/models.py`)
- [x] `quiz_json` — nullable Text; stores JSON list of quiz question dicts
- [x] `grammar_json` — nullable Text; stores JSON list of grammar spotlight dicts
- [x] `voice_blueprints_json` — nullable Text; stores JSON list of voice blueprint dicts
- [x] All three nullable — pre-Phase-5 sessions keep NULL; no migration data backfill needed

### Extended Pydantic Schemas (`modules/analysis/schemas.py`)
- [x] `QuizQuestion` — question, options (list[str] len 4), correct (int), explanation
- [x] `GrammarSpotlight` — rule, example, correction, frequency (int)
- [x] `VoiceBlueprint` — speaker, tempo_wpm (float), filler_word_count (int), vocabulary_richness (float)
- [x] `AnalysisSessionRead` — extended with `quiz`, `grammar_spotlights`, `voice_blueprints` (all default `[]`)
- [x] Backward compatible — existing Phase 3 response schema tests still pass

### Extended AnalysisPipeline (`modules/analysis/pipeline.py`)
- [x] `PipelineResult` — extended with `quiz`, `grammar_spotlights`, `voice_blueprints` (all default `[]`)
- [x] Existing `PipelineResult` instantiations without new fields get empty lists — no breaking changes
- [x] Pass 5a: `generate_quiz` called after Pass 4 LLM analysis
- [x] Pass 5b: `generate_grammar_spotlight` called after Pass 5a
- [x] Pass 6: `compute_voice_blueprints` called last (pure Python, always succeeds)
- [x] Pass 5 uses lazy imports inside `run()` to avoid circular dependency
- [x] All Pass 5-6 failures are soft — never raise, return empty lists

### Extended Analysis Router (`modules/analysis/router.py`)
- [x] Persists `quiz_json`, `grammar_json`, `voice_blueprints_json` to `AnalysisSession` (None if empty)
- [x] Returns `QuizQuestion`, `GrammarSpotlight`, `VoiceBlueprint` lists in `AnalysisSessionRead`
- [x] Handles NULL JSON columns with `json.loads(col or "[]")` fallback

### Grammar Deficits Endpoint (`modules/grammar/router.py`)
- [x] `GET /api/v1/grammar/deficits` — queries all `analysis_sessions` with non-NULL `grammar_json`
- [x] Aggregates by `rule` (sums `frequency` across sessions)
- [x] Returns top-5 sorted by descending `total_frequency`
- [x] Sessions with NULL `grammar_json` are skipped gracefully
- [x] Malformed JSON in `grammar_json` columns skipped without crashing
- [x] `GrammarDeficitRead` schema: `rule`, `total_frequency`, `example` (nullable)
- [x] `get_exercises/{rule_id}` remains stub — Phase 6+ scope

### Grammar Schemas (`modules/grammar/schemas.py`)
- [x] New file — `GrammarDeficitRead(BaseModel)` with aggregated deficit fields

### Text Practice Endpoint (`modules/text_practice/router.py`)
- [x] `POST /api/v1/text-practice/upload` — replaces Phase 1 stub
- [x] File size limit: 10 MB (413 on exceed)
- [x] Supported formats: `.txt`, `.pdf`, `.docx` (422 for others)
- [x] Text extraction: `.txt` → UTF-8 decode; `.pdf` → pypdf; `.docx` → python-docx
- [x] LLM single call returns: `detected_language`, `vocabulary` (CEFR-ranked), `quiz`, `grammar_spotlights`
- [x] Translation: `TranslationService.translate(text, detected_lang, target_lang)`; skipped when `detected_lang == target_lang`
- [x] LLM failure → returns 200 with empty lists (soft failure)
- [x] Translation failure → returns 200 with empty `translated_text` (soft failure)
- [x] `get_text_llm()` and `get_text_translation()` FastAPI deps — overridable in tests
- [x] Document text truncated to 8,000 chars before LLM call

### Text Practice Schemas (`modules/text_practice/schemas.py`)
- [x] `CEFRVocabItem` — word, cefr_level, definition
- [x] `TextQuizQuestion` — question, options, correct, explanation
- [x] `TextGrammarSpotlight` — rule, example, correction, frequency
- [x] `TextPracticeRead` — detected_language, translated_text, vocabulary, quiz, grammar_spotlights
- [x] Module-local copies (no cross-module imports — ADR-010 compliance)

### Database Migration
- [x] `004_extend_analysis_tables.py` — adds `quiz_json`, `grammar_json`, `voice_blueprints_json` (all nullable Text) to `analysis_sessions`; `downgrade()` implemented

### Dependencies
- [x] `pypdf==5.4.0` added to `requirements.txt` — PDF text extraction
- [x] `python-docx==1.1.2` added to `requirements.txt` — DOCX text extraction

### Test Infrastructure
- [x] Gate 1 + Gate 2 + Gate 3 + Gate 4 tests (113/113) still pass unmodified
- [x] `AnalysisSessionRead` extension is backward-compatible (new fields default to `[]`)
- [x] Phase 5 tests use dependency overrides (`get_pipeline`, `get_text_llm`, `get_text_translation`) for all LLM/pipeline calls — no real Ollama required

### Gate 5 Tests
- [x] pytest 167/167 passed (54 new + 113 existing), 0 failed

```
tests/test_analysis_phase5.py::TestQuizModule::test_quiz_module_importable                             PASSED
tests/test_analysis_phase5.py::TestQuizModule::test_quiz_returns_list_from_llm                        PASSED
tests/test_analysis_phase5.py::TestQuizModule::test_quiz_empty_transcript_returns_empty               PASSED
tests/test_analysis_phase5.py::TestQuizModule::test_quiz_whitespace_only_returns_empty                PASSED
tests/test_analysis_phase5.py::TestQuizModule::test_quiz_llm_error_returns_empty                      PASSED
tests/test_analysis_phase5.py::TestQuizModule::test_quiz_invalid_json_returns_empty                   PASSED
tests/test_analysis_phase5.py::TestQuizModule::test_quiz_missing_options_skips_item                   PASSED
tests/test_analysis_phase5.py::TestGrammarModule::test_grammar_module_importable                       PASSED
tests/test_analysis_phase5.py::TestGrammarModule::test_grammar_returns_list_from_llm                  PASSED
tests/test_analysis_phase5.py::TestGrammarModule::test_grammar_empty_transcript_returns_empty          PASSED
tests/test_analysis_phase5.py::TestGrammarModule::test_grammar_llm_error_returns_empty                PASSED
tests/test_analysis_phase5.py::TestGrammarModule::test_grammar_invalid_json_returns_empty             PASSED
tests/test_analysis_phase5.py::TestGrammarModule::test_grammar_capped_at_five_items                   PASSED
tests/test_analysis_phase5.py::TestVoiceBlueprint::test_voice_blueprint_importable                    PASSED
tests/test_analysis_phase5.py::TestVoiceBlueprint::test_voice_blueprint_empty_segments_returns_empty  PASSED
tests/test_analysis_phase5.py::TestVoiceBlueprint::test_voice_blueprint_single_speaker                PASSED
tests/test_analysis_phase5.py::TestVoiceBlueprint::test_voice_blueprint_wpm_calculation               PASSED
tests/test_analysis_phase5.py::TestVoiceBlueprint::test_voice_blueprint_filler_word_detection         PASSED
tests/test_analysis_phase5.py::TestVoiceBlueprint::test_voice_blueprint_vocabulary_richness           PASSED
tests/test_analysis_phase5.py::TestVoiceBlueprint::test_voice_blueprint_repetition_lowers_richness    PASSED
tests/test_analysis_phase5.py::TestVoiceBlueprint::test_voice_blueprint_multiple_speakers             PASSED
tests/test_analysis_phase5.py::TestVoiceBlueprint::test_voice_blueprint_zero_duration_segment_handled PASSED
tests/test_analysis_phase5.py::TestVoiceBlueprint::test_voice_blueprint_schema_keys_present           PASSED
tests/test_analysis_phase5.py::TestExtendedPipeline::test_pipeline_result_has_quiz_field              PASSED
tests/test_analysis_phase5.py::TestExtendedPipeline::test_pipeline_result_has_grammar_field           PASSED
tests/test_analysis_phase5.py::TestExtendedPipeline::test_pipeline_result_has_blueprints_field        PASSED
tests/test_analysis_phase5.py::TestExtendedPipeline::test_pipeline_result_defaults_to_empty_lists     PASSED
tests/test_analysis_phase5.py::TestExtendedPipeline::test_pipeline_run_includes_quiz                  PASSED
tests/test_analysis_phase5.py::TestExtendedAnalysisEndpoint::test_analyze_response_has_quiz_field     PASSED
tests/test_analysis_phase5.py::TestExtendedAnalysisEndpoint::test_analyze_response_has_grammar_spotlights_field PASSED
tests/test_analysis_phase5.py::TestExtendedAnalysisEndpoint::test_analyze_response_has_voice_blueprints_field   PASSED
tests/test_analysis_phase5.py::TestExtendedAnalysisEndpoint::test_analyze_response_quiz_is_list       PASSED
tests/test_analysis_phase5.py::TestExtendedAnalysisEndpoint::test_analyze_response_quiz_question_schema         PASSED
tests/test_analysis_phase5.py::TestExtendedAnalysisEndpoint::test_analyze_response_grammar_spotlights_schema    PASSED
tests/test_analysis_phase5.py::TestExtendedAnalysisEndpoint::test_analyze_response_voice_blueprints_schema      PASSED
tests/test_analysis_phase5.py::TestExtendedAnalysisEndpoint::test_analyze_empty_quiz_when_pipeline_returns_empty PASSED
tests/test_analysis_phase5.py::TestGrammarDeficitsEndpoint::test_deficits_returns_200                 PASSED
tests/test_analysis_phase5.py::TestGrammarDeficitsEndpoint::test_deficits_returns_list                PASSED
tests/test_analysis_phase5.py::TestGrammarDeficitsEndpoint::test_deficits_ignores_null_grammar_json   PASSED
tests/test_analysis_phase5.py::TestGrammarDeficitsEndpoint::test_deficits_aggregates_across_sessions  PASSED
tests/test_analysis_phase5.py::TestGrammarDeficitsEndpoint::test_deficits_ordered_by_frequency        PASSED
tests/test_analysis_phase5.py::TestGrammarDeficitsEndpoint::test_deficits_limited_to_five             PASSED
tests/test_analysis_phase5.py::TestGrammarDeficitsEndpoint::test_deficits_response_schema             PASSED
tests/test_analysis_phase5.py::TestTextPracticeEndpoint::test_text_upload_no_file_returns_422         PASSED
tests/test_analysis_phase5.py::TestTextPracticeEndpoint::test_text_upload_unsupported_format_returns_422        PASSED
tests/test_analysis_phase5.py::TestTextPracticeEndpoint::test_text_upload_too_large_returns_413       PASSED
tests/test_analysis_phase5.py::TestTextPracticeEndpoint::test_text_upload_txt_returns_200             PASSED
tests/test_analysis_phase5.py::TestTextPracticeEndpoint::test_text_upload_response_schema_fields      PASSED
tests/test_analysis_phase5.py::TestTextPracticeEndpoint::test_text_upload_vocabulary_is_list          PASSED
tests/test_analysis_phase5.py::TestTextPracticeEndpoint::test_text_upload_vocabulary_item_schema      PASSED
tests/test_analysis_phase5.py::TestTextPracticeEndpoint::test_text_upload_quiz_is_list                PASSED
tests/test_analysis_phase5.py::TestTextPracticeEndpoint::test_text_upload_translation_called          PASSED
tests/test_analysis_phase5.py::TestTextPracticeEndpoint::test_text_upload_same_lang_skips_translation PASSED
tests/test_analysis_phase5.py::TestTextPracticeEndpoint::test_text_upload_llm_failure_still_returns_200         PASSED
54 passed in 0.61s
```

---

## Bugs Fixed During Phase 5

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| `AttributeError: module 'inspect' has no attribute 'fields'` | Used `inspect.fields()` instead of `dataclasses.fields()` | Changed to `dataclasses.fields(PipelineResult)` |
| `test_deficits_empty_when_no_sessions_have_grammar` failed due to test ordering | pytest runs tests alphabetically within a class; `test_deficits_aggregates_across_sessions` ('a') ran before `test_deficits_empty` ('e') and inserted DB rows | Replaced brittle "empty DB" assertion with `test_deficits_ignores_null_grammar_json` which creates a NULL-grammar session and verifies it produces no empty-rule deficit entries |
| Circular import: `voice_blueprint.py` ↔ `pipeline.py` | `voice_blueprint.py` imported `SpeakerSegment` from `pipeline.py`; `pipeline.py` imports `compute_voice_blueprints` from `voice_blueprint.py` | Added `TYPE_CHECKING` guard in `voice_blueprint.py`; with `from __future__ import annotations`, the annotation is a lazy string at runtime |

---

## Decisions Locked

- **Pass 5 LLM calls**: Two separate calls (quiz + grammar) rather than one batched call — simpler prompts, better structured output; batching deferred to Phase 6+ optimisation
- **Voice blueprints algorithm**: Pure-Python statistics (tempo WPM, filler count, type-token ratio) from transcript segments; no raw audio feature extraction (prosody, pitch, formants) — sufficient for dev; richer analysis deferred to Phase 7+
- **Grammar deficits scope**: No user filtering in Phase 5 (aggregates ALL sessions); Phase 9 auth enforcement will add `user_id` filter
- **Text document truncation**: Documents truncated to 8,000 chars before LLM call — covers typical articles; chunked processing deferred to Phase 6+
- **ADR-010 compliance**: `TextPracticeRead`, `TextQuizQuestion`, `TextGrammarSpotlight` defined in `modules/text_practice/schemas.py` (not imported from `modules/analysis/schemas.py`) to maintain module isolation
- **Flashcard integration**: Text practice adds vocabulary to user deck deferred to Felix_Flashcards (Phase 6) — the `vocabulary` list in `TextPracticeRead` is the handoff point

---

## API Endpoints (new/changed this phase)

```
POST /api/v1/sessions/analyze              → EXTENDED — now returns quiz, grammar_spotlights, voice_blueprints
GET  /api/v1/grammar/deficits              → LIVE — aggregated top-5 grammar rules across all sessions
POST /api/v1/text-practice/upload         → LIVE — PDF/TXT/DOCX → translation, CEFR vocab, quiz, grammar
```

## Next Phase

| Agent | Branch | Scope |
|-------|--------|-------|
| Felix_Flashcards | `phase-6/felix-flashcards` | SM-2 spaced repetition; `Flashcard`, `FlashcardDeck`, `FlashcardReview` ORM; due/review/generate endpoints; flashcard creation from analysis vocabulary |
