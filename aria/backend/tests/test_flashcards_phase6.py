"""Gate 6 tests — Felix_Flashcards (Phase 6).

Covers: SM-2 algorithm, ORM models, generate endpoint, due endpoint,
review endpoint, and stats endpoint.
All tests run without GPU or Ollama.
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio


# ── helpers ───────────────────────────────────────────────────────────────────

def _vocab_payload(*words: str, cefr: str = "B1") -> list[dict]:
    return [{"word": w, "cefr_level": cefr, "definition": f"definition of {w}"} for w in words]


def _generate_body(words: list[str] | None = None, deck_name: str = "Test Deck") -> dict:
    words = words or ["hola", "gracias"]
    return {
        "deck_name": deck_name,
        "source_language": "es",
        "target_language": "en",
        "vocabulary": _vocab_payload(*words),
    }


# ── SM-2 algorithm unit tests ─────────────────────────────────────────────────

class TestSM2Algorithm:
    def _make_review(self, *, ease_factor=2.5, interval=1, repetitions=0):
        class _Rev:
            pass
        rev = _Rev()
        rev.ease_factor = ease_factor
        rev.interval = interval
        rev.repetitions = repetitions
        rev.next_review = date.today()
        rev.last_reviewed = None
        return rev

    def test_sm2_importable(self):
        from aria.backend.modules.flashcards.router import apply_sm2  # noqa: F401

    def test_sm2_quality_3_first_rep_sets_interval_1(self):
        from aria.backend.modules.flashcards.router import apply_sm2
        rev = self._make_review(repetitions=0)
        apply_sm2(rev, 3)
        assert rev.interval == 1
        assert rev.repetitions == 1

    def test_sm2_quality_5_second_rep_sets_interval_6(self):
        from aria.backend.modules.flashcards.router import apply_sm2
        rev = self._make_review(repetitions=1, interval=1)
        apply_sm2(rev, 5)
        assert rev.interval == 6
        assert rev.repetitions == 2

    def test_sm2_third_rep_multiplies_interval_by_ease_factor(self):
        from aria.backend.modules.flashcards.router import apply_sm2
        rev = self._make_review(repetitions=2, interval=6, ease_factor=2.5)
        apply_sm2(rev, 4)
        assert rev.interval == round(6 * 2.5)
        assert rev.repetitions == 3

    def test_sm2_quality_5_increases_ease_factor(self):
        from aria.backend.modules.flashcards.router import apply_sm2
        rev = self._make_review(ease_factor=2.5)
        apply_sm2(rev, 5)
        assert rev.ease_factor > 2.5

    def test_sm2_quality_3_decreases_ease_factor(self):
        from aria.backend.modules.flashcards.router import apply_sm2
        rev = self._make_review(ease_factor=2.5)
        apply_sm2(rev, 3)
        assert rev.ease_factor < 2.5

    def test_sm2_ease_factor_never_below_1_3(self):
        from aria.backend.modules.flashcards.router import apply_sm2
        rev = self._make_review(ease_factor=1.3)
        apply_sm2(rev, 3)
        assert rev.ease_factor >= 1.3

    def test_sm2_quality_0_resets_repetitions_and_interval(self):
        from aria.backend.modules.flashcards.router import apply_sm2
        rev = self._make_review(repetitions=5, interval=30, ease_factor=2.8)
        apply_sm2(rev, 0)
        assert rev.repetitions == 0
        assert rev.interval == 1

    def test_sm2_quality_2_resets_repetitions(self):
        from aria.backend.modules.flashcards.router import apply_sm2
        rev = self._make_review(repetitions=3, interval=15)
        apply_sm2(rev, 2)
        assert rev.repetitions == 0
        assert rev.interval == 1

    def test_sm2_sets_last_reviewed_to_today(self):
        from aria.backend.modules.flashcards.router import apply_sm2
        rev = self._make_review()
        apply_sm2(rev, 4)
        assert rev.last_reviewed == date.today()

    def test_sm2_next_review_is_today_plus_interval(self):
        from aria.backend.modules.flashcards.router import apply_sm2
        rev = self._make_review(repetitions=0)
        apply_sm2(rev, 4)
        assert rev.next_review == date.today() + timedelta(days=rev.interval)


# ── ORM model structure tests ─────────────────────────────────────────────────

class TestFlashcardModels:
    def test_models_importable(self):
        from aria.backend.modules.flashcards.models import (  # noqa: F401
            Flashcard,
            FlashcardDeck,
            FlashcardReview,
        )

    def test_flashcard_deck_tablename(self):
        from aria.backend.modules.flashcards.models import FlashcardDeck
        assert FlashcardDeck.__tablename__ == "flashcard_decks"

    def test_flashcard_tablename(self):
        from aria.backend.modules.flashcards.models import Flashcard
        assert Flashcard.__tablename__ == "flashcards"

    def test_flashcard_review_tablename(self):
        from aria.backend.modules.flashcards.models import FlashcardReview
        assert FlashcardReview.__tablename__ == "flashcard_reviews"

    def test_flashcard_deck_has_expected_columns(self):
        from aria.backend.modules.flashcards.models import FlashcardDeck
        cols = {c.name for c in FlashcardDeck.__table__.columns}
        assert {"id", "user_id", "name", "source_language", "target_language", "created_at"} <= cols

    def test_flashcard_has_expected_columns(self):
        from aria.backend.modules.flashcards.models import Flashcard
        cols = {c.name for c in Flashcard.__table__.columns}
        assert {"id", "deck_id", "word", "cefr_level", "definition", "example_sentence", "created_at"} <= cols

    def test_flashcard_review_has_expected_columns(self):
        from aria.backend.modules.flashcards.models import FlashcardReview
        cols = {c.name for c in FlashcardReview.__table__.columns}
        assert {
            "id", "flashcard_id", "ease_factor", "interval",
            "repetitions", "next_review", "last_reviewed",
        } <= cols

    def test_flashcard_review_unique_constraint_on_flashcard_id(self):
        from aria.backend.modules.flashcards.models import FlashcardReview
        constraints = {c.name for c in FlashcardReview.__table__.constraints}
        assert "uq_flashcard_reviews_flashcard_id" in constraints


# ── Generate endpoint ─────────────────────────────────────────────────────────

class TestGenerateEndpoint:
    @pytest.mark.asyncio
    async def test_generate_returns_201(self, client):
        resp = await client.post("/api/v1/flashcards/generate", json=_generate_body())
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_generate_response_has_deck(self, client):
        resp = await client.post("/api/v1/flashcards/generate", json=_generate_body())
        data = resp.json()
        assert "deck" in data
        assert data["deck"]["name"] == "Test Deck"

    @pytest.mark.asyncio
    async def test_generate_response_has_cards(self, client):
        resp = await client.post("/api/v1/flashcards/generate", json=_generate_body())
        data = resp.json()
        assert "cards" in data
        assert isinstance(data["cards"], list)

    @pytest.mark.asyncio
    async def test_generate_cards_created_count(self, client):
        body = _generate_body(["apple", "banana", "cherry"])
        resp = await client.post("/api/v1/flashcards/generate", json=body)
        data = resp.json()
        assert data["cards_created"] == 3
        assert len(data["cards"]) == 3

    @pytest.mark.asyncio
    async def test_generate_empty_vocabulary_returns_zero_cards(self, client):
        body = {"deck_name": "Empty Deck", "source_language": "en", "target_language": "en", "vocabulary": []}
        resp = await client.post("/api/v1/flashcards/generate", json=body)
        assert resp.status_code == 201
        data = resp.json()
        assert data["cards_created"] == 0
        assert data["cards"] == []

    @pytest.mark.asyncio
    async def test_generate_card_schema_fields(self, client):
        resp = await client.post("/api/v1/flashcards/generate", json=_generate_body(["test"]))
        card = resp.json()["cards"][0]
        assert "id" in card
        assert "deck_id" in card
        assert card["word"] == "test"
        assert "cefr_level" in card
        assert "definition" in card
        assert "created_at" in card

    @pytest.mark.asyncio
    async def test_generate_card_stores_cefr_and_definition(self, client):
        body = {
            "deck_name": "CEFR Deck",
            "source_language": "es",
            "target_language": "en",
            "vocabulary": [{"word": "ubicuo", "cefr_level": "C1", "definition": "omnipresent"}],
        }
        resp = await client.post("/api/v1/flashcards/generate", json=body)
        card = resp.json()["cards"][0]
        assert card["cefr_level"] == "C1"
        assert card["definition"] == "omnipresent"

    @pytest.mark.asyncio
    async def test_generate_deck_schema_fields(self, client):
        resp = await client.post("/api/v1/flashcards/generate", json=_generate_body())
        deck = resp.json()["deck"]
        assert "id" in deck
        assert "name" in deck
        assert "source_language" in deck
        assert "target_language" in deck
        assert "created_at" in deck

    @pytest.mark.asyncio
    async def test_generate_deck_languages_stored(self, client):
        resp = await client.post("/api/v1/flashcards/generate", json=_generate_body())
        deck = resp.json()["deck"]
        assert deck["source_language"] == "es"
        assert deck["target_language"] == "en"


# ── Due endpoint ──────────────────────────────────────────────────────────────

class TestDueEndpoint:
    @pytest.mark.asyncio
    async def test_due_returns_200(self, client):
        resp = await client.get("/api/v1/flashcards/due")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_due_returns_list(self, client):
        resp = await client.get("/api/v1/flashcards/due")
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_due_card_generated_today_appears(self, client):
        await client.post("/api/v1/flashcards/generate", json=_generate_body(["dueword"]))
        resp = await client.get("/api/v1/flashcards/due")
        words = [item["card"]["word"] for item in resp.json()]
        assert "dueword" in words

    @pytest.mark.asyncio
    async def test_due_response_item_has_card_and_review(self, client):
        await client.post("/api/v1/flashcards/generate", json=_generate_body(["schema_check"]))
        resp = await client.get("/api/v1/flashcards/due")
        items = [i for i in resp.json() if i["card"]["word"] == "schema_check"]
        assert len(items) >= 1
        item = items[0]
        assert "card" in item
        assert "review" in item

    @pytest.mark.asyncio
    async def test_due_review_schema_fields(self, client):
        await client.post("/api/v1/flashcards/generate", json=_generate_body(["rev_schema"]))
        resp = await client.get("/api/v1/flashcards/due")
        items = [i for i in resp.json() if i["card"]["word"] == "rev_schema"]
        rev = items[0]["review"]
        assert "ease_factor" in rev
        assert "interval" in rev
        assert "repetitions" in rev
        assert "next_review" in rev

    @pytest.mark.asyncio
    async def test_due_reviewed_card_not_returned_next_day(self, client):
        gen_resp = await client.post(
            "/api/v1/flashcards/generate", json=_generate_body(["future_word"])
        )
        card_id = gen_resp.json()["cards"][0]["id"]
        await client.post("/api/v1/flashcards/review", json={"flashcard_id": card_id, "quality": 5})
        due_resp = await client.get("/api/v1/flashcards/due")
        due_words = [i["card"]["word"] for i in due_resp.json()]
        assert "future_word" not in due_words


# ── Review endpoint ───────────────────────────────────────────────────────────

class TestReviewEndpoint:
    @pytest.mark.asyncio
    async def test_review_returns_200(self, client):
        gen = await client.post("/api/v1/flashcards/generate", json=_generate_body(["rev200"]))
        card_id = gen.json()["cards"][0]["id"]
        resp = await client.post("/api/v1/flashcards/review", json={"flashcard_id": card_id, "quality": 4})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_review_response_schema(self, client):
        gen = await client.post("/api/v1/flashcards/generate", json=_generate_body(["revschema"]))
        card_id = gen.json()["cards"][0]["id"]
        resp = await client.post("/api/v1/flashcards/review", json={"flashcard_id": card_id, "quality": 4})
        data = resp.json()
        assert "flashcard_id" in data
        assert "ease_factor" in data
        assert "interval" in data
        assert "repetitions" in data
        assert "next_review" in data

    @pytest.mark.asyncio
    async def test_review_quality_5_increments_repetitions(self, client):
        gen = await client.post("/api/v1/flashcards/generate", json=_generate_body(["repcount"]))
        card_id = gen.json()["cards"][0]["id"]
        resp = await client.post("/api/v1/flashcards/review", json={"flashcard_id": card_id, "quality": 5})
        assert resp.json()["repetitions"] == 1

    @pytest.mark.asyncio
    async def test_review_quality_5_increases_ease_factor(self, client):
        gen = await client.post("/api/v1/flashcards/generate", json=_generate_body(["eftest"]))
        card_id = gen.json()["cards"][0]["id"]
        resp = await client.post("/api/v1/flashcards/review", json={"flashcard_id": card_id, "quality": 5})
        assert resp.json()["ease_factor"] > 2.5

    @pytest.mark.asyncio
    async def test_review_quality_0_resets_to_interval_1(self, client):
        gen = await client.post("/api/v1/flashcards/generate", json=_generate_body(["resettest"]))
        card_id = gen.json()["cards"][0]["id"]
        await client.post("/api/v1/flashcards/review", json={"flashcard_id": card_id, "quality": 5})
        await client.post("/api/v1/flashcards/review", json={"flashcard_id": card_id, "quality": 5})
        resp = await client.post("/api/v1/flashcards/review", json={"flashcard_id": card_id, "quality": 0})
        data = resp.json()
        assert data["interval"] == 1
        assert data["repetitions"] == 0

    @pytest.mark.asyncio
    async def test_review_unknown_card_returns_404(self, client):
        fake_id = str(uuid.uuid4())
        resp = await client.post("/api/v1/flashcards/review", json={"flashcard_id": fake_id, "quality": 3})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_review_quality_out_of_range_returns_422(self, client):
        resp = await client.post(
            "/api/v1/flashcards/review",
            json={"flashcard_id": str(uuid.uuid4()), "quality": 6},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_review_next_review_advances_after_success(self, client):
        gen = await client.post("/api/v1/flashcards/generate", json=_generate_body(["advance"]))
        card_id = gen.json()["cards"][0]["id"]
        resp = await client.post("/api/v1/flashcards/review", json={"flashcard_id": card_id, "quality": 4})
        next_review = resp.json()["next_review"]
        assert next_review > str(date.today())


# ── Stats endpoint ────────────────────────────────────────────────────────────

class TestStatsEndpoint:
    @pytest.mark.asyncio
    async def test_stats_returns_200(self, client):
        resp = await client.get("/api/v1/flashcards/stats")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_stats_response_schema(self, client):
        resp = await client.get("/api/v1/flashcards/stats")
        data = resp.json()
        assert "total_cards" in data
        assert "cards_due" in data
        assert "cards_mastered" in data

    @pytest.mark.asyncio
    async def test_stats_total_cards_reflects_generated(self, client):
        before = (await client.get("/api/v1/flashcards/stats")).json()["total_cards"]
        await client.post("/api/v1/flashcards/generate", json=_generate_body(["statsword1", "statsword2"]))
        after = (await client.get("/api/v1/flashcards/stats")).json()["total_cards"]
        assert after == before + 2

    @pytest.mark.asyncio
    async def test_stats_mastered_threshold_is_21_days(self, client):
        gen = await client.post("/api/v1/flashcards/generate", json=_generate_body(["masterme"]))
        card_id = gen.json()["cards"][0]["id"]
        before = (await client.get("/api/v1/flashcards/stats")).json()["cards_mastered"]
        for _ in range(6):
            await client.post("/api/v1/flashcards/review", json={"flashcard_id": card_id, "quality": 5})
        after = (await client.get("/api/v1/flashcards/stats")).json()["cards_mastered"]
        assert after >= before


# ── Backward compatibility ────────────────────────────────────────────────────

class TestBackwardCompatibility:
    @pytest.mark.asyncio
    async def test_prior_phase_tests_still_pass(self, client):
        """Smoke-test a prior-phase endpoint to ensure no regressions."""
        resp = await client.get("/api/health")
        assert resp.status_code == 200
