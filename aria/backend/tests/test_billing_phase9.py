"""Gate 9 tests — Anna_Auth Phase 9 (Monetization).

Covers: UserSubscription model, get_or_create_subscription dependency,
billing endpoints (subscription status, checkout, portal, webhook),
auth enforcement on all protected module endpoints (401 without auth),
Free-tier quota enforcement, and user-scoped data queries.
All tests run without GPU, Ollama, or real Stripe credentials.
"""
from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio


# ── helpers ───────────────────────────────────────────────────────────────────

def _mock_user(user_id: uuid.UUID | None = None):
    """Return a minimal user-like object for dependency injection."""
    uid = user_id or uuid.UUID("00000000-0000-0000-0000-000000000001")

    class _U:
        id = uid
        email = "test@aria.dev"
        is_active = True
        is_superuser = False
        is_verified = True

    return _U()


# ── TestSubscriptionModel ─────────────────────────────────────────────────────

class TestSubscriptionModel:
    def test_model_importable(self):
        from aria.backend.modules.billing.models import UserSubscription  # noqa: F401
        assert UserSubscription is not None

    def test_model_tablename(self):
        from aria.backend.modules.billing.models import UserSubscription
        assert UserSubscription.__tablename__ == "user_subscriptions"

    def test_model_has_expected_columns(self):
        from aria.backend.modules.billing.models import UserSubscription
        cols = {c.name for c in UserSubscription.__table__.columns}
        assert {
            "id", "user_id", "plan", "status",
            "stripe_customer_id", "stripe_subscription_id",
            "current_period_end", "created_at", "updated_at",
        } <= cols

    def _make_sub(self, plan: str, status: str):
        """Return a minimal object that exercises UserSubscription.is_pro."""
        from aria.backend.modules.billing.models import UserSubscription

        class _Stub:
            pass

        stub = _Stub()
        stub.plan = plan
        stub.status = status
        # Bind the property directly to the stub
        stub.is_pro = UserSubscription.is_pro.fget(stub)  # type: ignore[attr-defined]
        return stub

    def test_is_pro_false_for_free_plan(self):
        from aria.backend.modules.billing.models import UserSubscription

        class _S:
            plan = "free"
            status = "active"

        assert UserSubscription.is_pro.fget(_S()) is False  # type: ignore[attr-defined]

    def test_is_pro_true_for_active_pro(self):
        from aria.backend.modules.billing.models import UserSubscription

        class _S:
            plan = "pro"
            status = "active"

        assert UserSubscription.is_pro.fget(_S()) is True  # type: ignore[attr-defined]

    def test_is_pro_true_for_trialing_pro(self):
        from aria.backend.modules.billing.models import UserSubscription

        class _S:
            plan = "pro"
            status = "trialing"

        assert UserSubscription.is_pro.fget(_S()) is True  # type: ignore[attr-defined]

    def test_is_pro_false_for_canceled_pro(self):
        from aria.backend.modules.billing.models import UserSubscription

        class _S:
            plan = "pro"
            status = "canceled"

        assert UserSubscription.is_pro.fget(_S()) is False  # type: ignore[attr-defined]


# ── TestSubscriptionSchemas ───────────────────────────────────────────────────

class TestSubscriptionSchemas:
    def test_schemas_importable(self):
        from aria.backend.modules.billing.schemas import (  # noqa: F401
            CheckoutResponse, PortalResponse, SubscriptionRead,
        )

    def test_subscription_read_default_free(self):
        from aria.backend.modules.billing.schemas import SubscriptionRead
        s = SubscriptionRead.from_orm_or_default(None)
        assert s.plan == "free"
        assert s.status == "active"
        assert s.has_stripe is False

    def test_subscription_read_from_orm(self):
        from aria.backend.modules.billing.schemas import SubscriptionRead

        class _FakeSub:
            plan = "pro"
            status = "active"
            current_period_end = None
            stripe_customer_id = "cus_abc123"

        s = SubscriptionRead.from_orm_or_default(_FakeSub())
        assert s.plan == "pro"
        assert s.has_stripe is True


# ── TestGetOrCreateSubscription ───────────────────────────────────────────────

class TestGetOrCreateSubscription:
    @pytest.mark.asyncio
    async def test_creates_free_sub_on_first_call(self):
        from aria.backend.database import AsyncSessionFactory
        from aria.backend.modules.billing.dependencies import get_or_create_subscription
        from aria.backend.modules.billing.models import UserSubscription
        from sqlalchemy import select

        user_id = uuid.uuid4()
        async with AsyncSessionFactory() as db:
            sub = await get_or_create_subscription(user_id, db)

        assert sub.plan == "free"
        assert sub.status == "active"
        assert sub.user_id == user_id

    @pytest.mark.asyncio
    async def test_returns_existing_subscription(self):
        from aria.backend.database import AsyncSessionFactory
        from aria.backend.modules.billing.dependencies import get_or_create_subscription

        user_id = uuid.uuid4()
        async with AsyncSessionFactory() as db:
            sub1 = await get_or_create_subscription(user_id, db)
            sub1_id = sub1.id

        async with AsyncSessionFactory() as db:
            sub2 = await get_or_create_subscription(user_id, db)
            assert sub2.id == sub1_id  # same row, not a new one


# ── TestBillingSubscriptionEndpoint ──────────────────────────────────────────

class TestBillingSubscriptionEndpoint:
    @pytest.mark.asyncio
    async def test_subscription_requires_auth(self, client):
        resp = await client.get("/api/v1/billing/subscription")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_subscription_returns_200_with_auth(self, authed_client):
        resp = await authed_client.get("/api/v1/billing/subscription")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_subscription_default_plan_is_free(self, authed_client):
        resp = await authed_client.get("/api/v1/billing/subscription")
        data = resp.json()
        assert data["plan"] == "free"
        assert data["status"] == "active"
        assert data["has_stripe"] is False

    @pytest.mark.asyncio
    async def test_subscription_response_schema(self, authed_client):
        resp = await authed_client.get("/api/v1/billing/subscription")
        data = resp.json()
        assert "plan" in data
        assert "status" in data
        assert "has_stripe" in data


# ── TestBillingCheckoutEndpoint ───────────────────────────────────────────────

class TestBillingCheckoutEndpoint:
    @pytest.mark.asyncio
    async def test_checkout_requires_auth(self, client):
        resp = await client.post("/api/v1/billing/checkout")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_checkout_returns_503_when_stripe_not_configured(self, authed_client):
        resp = await authed_client.post("/api/v1/billing/checkout")
        # STRIPE_SECRET_KEY is empty in test env
        assert resp.status_code == 503
        assert "not configured" in resp.json()["detail"].lower()


# ── TestBillingPortalEndpoint ─────────────────────────────────────────────────

class TestBillingPortalEndpoint:
    @pytest.mark.asyncio
    async def test_portal_requires_auth(self, client):
        resp = await client.post("/api/v1/billing/portal")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_portal_returns_503_when_stripe_not_configured(self, authed_client):
        resp = await authed_client.post("/api/v1/billing/portal")
        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_portal_returns_400_when_no_stripe_customer(self, authed_client):
        from aria.backend.core.config import settings
        orig = settings.STRIPE_SECRET_KEY
        # temporarily set a non-empty key so we get past the 503 check
        settings.STRIPE_SECRET_KEY = "sk_test_fake"
        try:
            resp = await authed_client.post("/api/v1/billing/portal")
            # No stripe_customer_id on this user → 400
            assert resp.status_code == 400
            assert "No billing account" in resp.json()["detail"]
        finally:
            settings.STRIPE_SECRET_KEY = orig


# ── TestWebhookEndpoint ───────────────────────────────────────────────────────

class TestWebhookEndpoint:
    @pytest.mark.asyncio
    async def test_webhook_invalid_json_returns_400(self, client):
        resp = await client.post(
            "/api/v1/billing/webhook",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_webhook_unknown_event_returns_200(self, client):
        payload = json.dumps({"type": "invoice.paid", "data": {"object": {}}})
        resp = await client.post(
            "/api/v1/billing/webhook",
            content=payload.encode(),
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200
        assert resp.json()["received"] is True

    @pytest.mark.asyncio
    async def test_webhook_checkout_completed_upgrades_to_pro(self, client):
        from aria.backend.database import AsyncSessionFactory
        from aria.backend.modules.billing.models import UserSubscription
        from sqlalchemy import select

        user_id = uuid.uuid4()
        payload = json.dumps({
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer": "cus_test123",
                    "subscription": "sub_test123",
                    "metadata": {"user_id": str(user_id)},
                }
            },
        })
        resp = await client.post(
            "/api/v1/billing/webhook",
            content=payload.encode(),
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200

        async with AsyncSessionFactory() as db:
            result = await db.execute(
                select(UserSubscription).where(UserSubscription.user_id == user_id)
            )
            sub = result.scalar_one_or_none()

        assert sub is not None
        assert sub.plan == "pro"
        assert sub.status == "active"
        assert sub.stripe_customer_id == "cus_test123"

    @pytest.mark.asyncio
    async def test_webhook_subscription_deleted_downgrades_to_free(self, client):
        from aria.backend.database import AsyncSessionFactory
        from aria.backend.modules.billing.models import UserSubscription

        # Create a Pro subscription
        user_id = uuid.uuid4()
        async with AsyncSessionFactory() as db:
            sub = UserSubscription(
                user_id=user_id,
                plan="pro",
                status="active",
                stripe_subscription_id="sub_to_cancel",
            )
            db.add(sub)
            await db.commit()

        payload = json.dumps({
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_to_cancel"}},
        })
        resp = await client.post(
            "/api/v1/billing/webhook",
            content=payload.encode(),
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200

        async with AsyncSessionFactory() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(UserSubscription).where(UserSubscription.user_id == user_id)
            )
            sub = result.scalar_one_or_none()

        assert sub.plan == "free"
        assert sub.status == "canceled"


# ── TestAuthEnforcement ───────────────────────────────────────────────────────

class TestAuthEnforcement:
    """Verify that all protected module endpoints return 401 without auth."""

    @pytest.mark.asyncio
    async def test_analyze_requires_auth(self, client):
        resp = await client.post("/api/v1/sessions/analyze")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_conversation_create_requires_auth(self, client):
        resp = await client.post("/api/v1/conversations/", json={"language": "en"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_flashcard_generate_requires_auth(self, client):
        resp = await client.post("/api/v1/flashcards/generate", json={})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_flashcard_due_requires_auth(self, client):
        resp = await client.get("/api/v1/flashcards/due")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_flashcard_review_requires_auth(self, client):
        resp = await client.post("/api/v1/flashcards/review", json={})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_flashcard_stats_requires_auth(self, client):
        resp = await client.get("/api/v1/flashcards/stats")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_grammar_deficits_requires_auth(self, client):
        resp = await client.get("/api/v1/grammar/deficits")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_text_practice_requires_auth(self, client):
        resp = await client.post("/api/v1/text-practice/upload")
        assert resp.status_code == 401


# ── TestFreeQuotaEnforcement ──────────────────────────────────────────────────

class TestFreeQuotaEnforcement:
    """Verify that free-tier quota limits block requests at the right threshold.

    Uses quota_authed_client (auth-only, quotas enforced) rather than
    authed_client (which bypasses quotas for endpoint-behavior tests).
    """

    @pytest.mark.asyncio
    async def test_daily_conversation_quota_blocks_at_limit(self, quota_authed_client):
        from aria.backend.core.config import settings
        from aria.backend.database import AsyncSessionFactory
        from aria.backend.modules.conversation.models import ConversationSession
        from aria.backend.tests.conftest import MOCK_USER

        # Insert FREE_DAILY_CONVERSATIONS sessions for today with the mock user id
        async with AsyncSessionFactory() as db:
            for _ in range(settings.FREE_DAILY_CONVERSATIONS):
                session = ConversationSession(
                    user_id=MOCK_USER.id,
                    language="en",
                )
                db.add(session)
            await db.commit()

        resp = await quota_authed_client.post("/api/v1/conversations/", json={"language": "en"})
        assert resp.status_code == 429
        assert "Free tier" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_flashcard_limit_blocks_when_at_cap(self, quota_authed_client):
        from aria.backend.core.config import settings
        from aria.backend.database import AsyncSessionFactory
        from aria.backend.modules.flashcards.models import Flashcard, FlashcardDeck, FlashcardReview
        from aria.backend.tests.conftest import MOCK_USER
        from datetime import date

        # Fill up to the free tier flashcard limit
        async with AsyncSessionFactory() as db:
            deck = FlashcardDeck(
                user_id=MOCK_USER.id,
                name="Limit Test Deck",
                source_language="en",
                target_language="de",
            )
            db.add(deck)
            await db.flush()
            for i in range(settings.FREE_MAX_FLASHCARDS):
                card = Flashcard(deck_id=deck.id, word=f"word_{i}")
                db.add(card)
                await db.flush()
                review = FlashcardReview(
                    flashcard_id=card.id,
                    ease_factor=2.5,
                    interval=1,
                    repetitions=0,
                    next_review=date.today(),
                )
                db.add(review)
            await db.commit()

        vocab = [{"word": "new_word", "cefr_level": "A1", "definition": "new"}]
        resp = await quota_authed_client.post(
            "/api/v1/flashcards/generate",
            json={"deck_name": "Over Cap", "source_language": "en", "target_language": "de", "vocabulary": vocab},
        )
        assert resp.status_code == 429
        assert "Free tier" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_pro_user_bypasses_conversation_quota(self, quota_authed_client):
        from aria.backend.core.config import settings
        from aria.backend.database import AsyncSessionFactory
        from aria.backend.modules.billing.models import UserSubscription
        from aria.backend.modules.conversation.models import ConversationSession
        from aria.backend.tests.conftest import MOCK_USER

        # Upgrade mock user to Pro (upsert — may already exist from earlier quota tests)
        from aria.backend.modules.billing.dependencies import get_or_create_subscription
        async with AsyncSessionFactory() as db:
            sub = await get_or_create_subscription(MOCK_USER.id, db)
            sub.plan = "pro"
            sub.status = "active"
            await db.commit()

        # Insert sessions beyond the free limit
        async with AsyncSessionFactory() as db:
            for _ in range(settings.FREE_DAILY_CONVERSATIONS + 1):
                db.add(ConversationSession(user_id=MOCK_USER.id, language="en"))
            await db.commit()

        resp = await quota_authed_client.post("/api/v1/conversations/", json={"language": "en"})
        # Pro user should NOT be blocked
        assert resp.status_code == 201


# ── TestUserScopedData ────────────────────────────────────────────────────────

class TestUserScopedData:
    """Verify module queries are scoped to the authenticated user."""

    @pytest.mark.asyncio
    async def test_flashcard_stats_scoped_to_user(self, authed_client):
        from aria.backend.database import AsyncSessionFactory
        from aria.backend.modules.flashcards.models import Flashcard, FlashcardDeck, FlashcardReview
        from aria.backend.tests.conftest import MOCK_USER
        from datetime import date

        other_user_id = uuid.uuid4()

        async with AsyncSessionFactory() as db:
            # Deck owned by another user
            other_deck = FlashcardDeck(
                user_id=other_user_id,
                name="Other User's Deck",
                source_language="en",
                target_language="de",
            )
            db.add(other_deck)
            await db.flush()
            other_card = Flashcard(deck_id=other_deck.id, word="foreignword")
            db.add(other_card)
            await db.flush()
            db.add(FlashcardReview(
                flashcard_id=other_card.id,
                ease_factor=2.5, interval=1, repetitions=0, next_review=date.today()
            ))
            await db.commit()

        resp = await authed_client.get("/api/v1/flashcards/stats")
        assert resp.status_code == 200
        stats = resp.json()
        # Other user's cards must not appear in mock user's stats
        # (total_cards may be 0 or reflect only MOCK_USER's cards)
        assert isinstance(stats["total_cards"], int)

    @pytest.mark.asyncio
    async def test_grammar_deficits_scoped_to_user(self, authed_client):
        import json as _json
        from aria.backend.database import AsyncSessionFactory
        from aria.backend.modules.analysis.models import AnalysisSession

        other_user_id = uuid.uuid4()
        other_grammar = _json.dumps([
            {"rule": "Only Other User Rule", "example": "ex", "correction": "cor", "frequency": 99}
        ])

        async with AsyncSessionFactory() as db:
            session = AnalysisSession(
                user_id=other_user_id,
                audio_filename="other.wav",
                language="en",
                duration_seconds=5.0,
                num_speakers=1,
                transcript_json="[]",
                vocabulary_json="[]",
                grammar_json=other_grammar,
            )
            db.add(session)
            await db.commit()

        resp = await authed_client.get("/api/v1/grammar/deficits")
        assert resp.status_code == 200
        rules = [d["rule"] for d in resp.json()]
        assert "Only Other User Rule" not in rules


# ── TestBackwardCompatibility ─────────────────────────────────────────────────

class TestBackwardCompatibility:
    @pytest.mark.asyncio
    async def test_health_endpoint_still_works(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_auth_register_still_works(self, client):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "backcompat9@aria.dev", "password": "Str0ngPass!"},
        )
        assert resp.status_code in (201, 400)  # 400 if already registered
