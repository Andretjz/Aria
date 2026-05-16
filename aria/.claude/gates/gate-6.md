# Gate 6 — Flashcards: SM-2 Spaced Repetition

**Date:** 2026-05-16
**Agent:** Felix_Flashcards
**Branch:** `phase-6/felix-flashcards`
**Verdict:** APPROVED

---

## Checklist

### SM-2 Algorithm (`modules/flashcards/router.py::apply_sm2`)
- [x] `apply_sm2` — public function; updates FlashcardReview state in-place
- [x] quality >= 3: increments `repetitions`; intervals follow 1 → 6 → interval * ease_factor sequence
- [x] quality < 3: resets `repetitions = 0`, `interval = 1`
- [x] `ease_factor` formula: `ef + 0.1 - (5-q) * (0.08 + (5-q) * 0.02)`, clamped to minimum 1.3
- [x] `last_reviewed` set to `date.today()` on every call
- [x] `next_review` set to `date.today() + timedelta(days=interval)`

### ORM Models (`modules/flashcards/models.py`)
- [x] `FlashcardDeck` — `id`, `user_id` (nullable FK → user), `name`, `source_language`, `target_language`, `created_at`
- [x] `Flashcard` — `id`, `deck_id` (FK → flashcard_decks CASCADE), `word`, `cefr_level` (nullable), `definition` (nullable), `example_sentence` (nullable), `created_at`
- [x] `FlashcardReview` — `id`, `flashcard_id` (FK → flashcards CASCADE), `ease_factor` (2.5), `interval` (1), `repetitions` (0), `next_review` (date), `last_reviewed` (nullable date)
- [x] `FlashcardReview` has `UniqueConstraint("flashcard_id")` — one SM-2 state record per card

### Pydantic Schemas (`modules/flashcards/schemas.py`)
- [x] `VocabItem` — word, cefr_level (nullable), definition (nullable), example_sentence (nullable)
- [x] `FlashcardRead` — full card fields with `from_attributes=True`
- [x] `FlashcardReviewRead` — SM-2 state fields with `from_attributes=True`
- [x] `FlashcardDeckRead` — deck fields with `from_attributes=True`
- [x] `FlashcardDueRead` — composite of `card: FlashcardRead` + `review: FlashcardReviewRead`
- [x] `GenerateRequest` — `deck_name`, `source_language`, `target_language`, `vocabulary: list[VocabItem]`
- [x] `GenerateResponse` — `deck`, `cards_created`, `cards`
- [x] `ReviewRequest` — `flashcard_id: UUID`, `quality: int`; validator rejects quality outside 0-5
- [x] `StatsRead` — `total_cards`, `cards_due`, `cards_mastered`
- [x] ADR-010 compliance — no cross-module imports

### Generate Endpoint (`POST /api/v1/flashcards/generate`)
- [x] Returns HTTP 201
- [x] Creates `FlashcardDeck` + `Flashcard` records + `FlashcardReview` (SM-2 init) for each vocab item
- [x] Empty vocabulary → 201 with `cards_created=0`
- [x] `cefr_level`, `definition`, `example_sentence` stored from request
- [x] `next_review` initialised to `date.today()` (immediately due)

### Due Endpoint (`GET /api/v1/flashcards/due`)
- [x] Returns HTTP 200 with list
- [x] Cards with `next_review <= today` are returned; future cards excluded
- [x] Response items have `card` + `review` sub-objects with expected schema fields
- [x] After one successful review (quality >= 3), card's `next_review` advances and card leaves the due list

### Review Endpoint (`POST /api/v1/flashcards/review`)
- [x] Returns HTTP 200 with `FlashcardReviewRead`
- [x] quality=5 increments `repetitions` and increases `ease_factor`
- [x] quality=0 resets `repetitions=0`, `interval=1`
- [x] Unknown `flashcard_id` → 404
- [x] `quality > 5` → 422 (Pydantic validation)
- [x] `next_review` advances to future date after successful review

### Stats Endpoint (`GET /api/v1/flashcards/stats`)
- [x] Returns HTTP 200 with `total_cards`, `cards_due`, `cards_mastered`
- [x] `total_cards` increments when new cards are generated
- [x] `cards_mastered` counts `FlashcardReview.interval >= 21` (21-day threshold)

### Database Migration
- [x] `005_create_flashcard_tables.py` — creates `flashcard_decks`, `flashcards`, `flashcard_reviews` with FK constraints and indexes; `downgrade()` implemented

### Test Infrastructure
- [x] Gate 1–5 tests (167/167) still pass unmodified
- [x] No cross-module imports introduced
- [x] SM-2 unit tests use a plain Python object (not SQLAlchemy `__new__`) to avoid instrumentation issues

### Gate 6 Tests
- [x] pytest 214/214 passed (47 new + 167 existing), 0 failed

```
tests/test_flashcards_phase6.py::TestSM2Algorithm::test_sm2_importable                                    PASSED
tests/test_flashcards_phase6.py::TestSM2Algorithm::test_sm2_quality_3_first_rep_sets_interval_1           PASSED
tests/test_flashcards_phase6.py::TestSM2Algorithm::test_sm2_quality_5_second_rep_sets_interval_6          PASSED
tests/test_flashcards_phase6.py::TestSM2Algorithm::test_sm2_third_rep_multiplies_interval_by_ease_factor  PASSED
tests/test_flashcards_phase6.py::TestSM2Algorithm::test_sm2_quality_5_increases_ease_factor               PASSED
tests/test_flashcards_phase6.py::TestSM2Algorithm::test_sm2_quality_3_decreases_ease_factor               PASSED
tests/test_flashcards_phase6.py::TestSM2Algorithm::test_sm2_ease_factor_never_below_1_3                   PASSED
tests/test_flashcards_phase6.py::TestSM2Algorithm::test_sm2_quality_0_resets_repetitions_and_interval     PASSED
tests/test_flashcards_phase6.py::TestSM2Algorithm::test_sm2_quality_2_resets_repetitions                  PASSED
tests/test_flashcards_phase6.py::TestSM2Algorithm::test_sm2_sets_last_reviewed_to_today                   PASSED
tests/test_flashcards_phase6.py::TestSM2Algorithm::test_sm2_next_review_is_today_plus_interval            PASSED
tests/test_flashcards_phase6.py::TestFlashcardModels::test_models_importable                               PASSED
tests/test_flashcards_phase6.py::TestFlashcardModels::test_flashcard_deck_tablename                        PASSED
tests/test_flashcards_phase6.py::TestFlashcardModels::test_flashcard_tablename                             PASSED
tests/test_flashcards_phase6.py::TestFlashcardModels::test_flashcard_review_tablename                      PASSED
tests/test_flashcards_phase6.py::TestFlashcardModels::test_flashcard_deck_has_expected_columns             PASSED
tests/test_flashcards_phase6.py::TestFlashcardModels::test_flashcard_has_expected_columns                  PASSED
tests/test_flashcards_phase6.py::TestFlashcardModels::test_flashcard_review_has_expected_columns           PASSED
tests/test_flashcards_phase6.py::TestFlashcardModels::test_flashcard_review_unique_constraint_on_flashcard_id PASSED
tests/test_flashcards_phase6.py::TestGenerateEndpoint::test_generate_returns_201                           PASSED
tests/test_flashcards_phase6.py::TestGenerateEndpoint::test_generate_response_has_deck                     PASSED
tests/test_flashcards_phase6.py::TestGenerateEndpoint::test_generate_response_has_cards                    PASSED
tests/test_flashcards_phase6.py::TestGenerateEndpoint::test_generate_cards_created_count                   PASSED
tests/test_flashcards_phase6.py::TestGenerateEndpoint::test_generate_empty_vocabulary_returns_zero_cards   PASSED
tests/test_flashcards_phase6.py::TestGenerateEndpoint::test_generate_card_schema_fields                    PASSED
tests/test_flashcards_phase6.py::TestGenerateEndpoint::test_generate_card_stores_cefr_and_definition       PASSED
tests/test_flashcards_phase6.py::TestGenerateEndpoint::test_generate_deck_schema_fields                    PASSED
tests/test_flashcards_phase6.py::TestGenerateEndpoint::test_generate_deck_languages_stored                 PASSED
tests/test_flashcards_phase6.py::TestDueEndpoint::test_due_returns_200                                     PASSED
tests/test_flashcards_phase6.py::TestDueEndpoint::test_due_returns_list                                    PASSED
tests/test_flashcards_phase6.py::TestDueEndpoint::test_due_card_generated_today_appears                    PASSED
tests/test_flashcards_phase6.py::TestDueEndpoint::test_due_response_item_has_card_and_review               PASSED
tests/test_flashcards_phase6.py::TestDueEndpoint::test_due_review_schema_fields                            PASSED
tests/test_flashcards_phase6.py::TestDueEndpoint::test_due_reviewed_card_not_returned_next_day             PASSED
tests/test_flashcards_phase6.py::TestReviewEndpoint::test_review_returns_200                               PASSED
tests/test_flashcards_phase6.py::TestReviewEndpoint::test_review_response_schema                           PASSED
tests/test_flashcards_phase6.py::TestReviewEndpoint::test_review_quality_5_increments_repetitions          PASSED
tests/test_flashcards_phase6.py::TestReviewEndpoint::test_review_quality_5_increases_ease_factor           PASSED
tests/test_flashcards_phase6.py::TestReviewEndpoint::test_review_quality_0_resets_to_interval_1            PASSED
tests/test_flashcards_phase6.py::TestReviewEndpoint::test_review_unknown_card_returns_404                  PASSED
tests/test_flashcards_phase6.py::TestReviewEndpoint::test_review_quality_out_of_range_returns_422          PASSED
tests/test_flashcards_phase6.py::TestReviewEndpoint::test_review_next_review_advances_after_success        PASSED
tests/test_flashcards_phase6.py::TestStatsEndpoint::test_stats_returns_200                                 PASSED
tests/test_flashcards_phase6.py::TestStatsEndpoint::test_stats_response_schema                             PASSED
tests/test_flashcards_phase6.py::TestStatsEndpoint::test_stats_total_cards_reflects_generated              PASSED
tests/test_flashcards_phase6.py::TestStatsEndpoint::test_stats_mastered_threshold_is_21_days               PASSED
tests/test_flashcards_phase6.py::TestBackwardCompatibility::test_prior_phase_tests_still_pass              PASSED
47 passed in 3.64s
```

---

## Decisions Locked

- **SM-2 over FSRS**: ADR-008 — SM-2 for MVP; FSRS deferred
- **One FlashcardReview per card**: SM-2 state tracked as a single mutable record (not an append-only log) — simpler queries and updates
- **Anonymous decks**: `user_id` nullable on `flashcard_decks`/`FlashcardDeck` — Phase 9 enforces auth scoping
- **mastered threshold = 21 days**: Cards with `interval >= 21` considered mastered; industry-standard heuristic
- **VocabItem not imported from text_practice**: ADR-010 compliance — module-local copy in `flashcards/schemas.py`
- **No LLM enrichment in generate**: The vocabulary handoff from `TextPracticeRead.vocabulary` already contains `word`, `cefr_level`, `definition` — no extra LLM call needed for Phase 6; raw-word enrichment (from analysis sessions) deferred to Phase 7+

---

## API Endpoints (new this phase)

```
POST /api/v1/flashcards/generate      → LIVE — create deck + flashcards from vocabulary list
GET  /api/v1/flashcards/due           → LIVE — cards due today, ordered by next_review
POST /api/v1/flashcards/review        → LIVE — SM-2 quality rating (0-5), updates schedule
GET  /api/v1/flashcards/stats         → LIVE — total_cards, cards_due, cards_mastered
```

## Next Phase

| Agent | Branch | Scope |
|-------|--------|-------|
| Fiona_Frontend | `phase-7/fiona-frontend` | Full React/TypeScript UI for all six modules |
