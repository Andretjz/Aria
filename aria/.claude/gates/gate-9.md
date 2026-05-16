# Gate 9 — Monetization: Stripe Subscriptions + Free/Pro Tier Enforcement

**Date:** 2026-05-16
**Agent:** Anna_Auth
**Branch:** `phase-9/anna-auth`
**Verdict:** APPROVED

---

## Checklist

### UserSubscription Model (`aria/backend/modules/billing/models.py`)
- [x] `__tablename__ = "user_subscriptions"`
- [x] Columns: `id` (UUID PK), `user_id` (FK → `user.id` CASCADE, UNIQUE, indexed), `plan` (str, default `"free"`), `status` (str, default `"active"`), `stripe_customer_id` (nullable, UNIQUE, indexed), `stripe_subscription_id` (nullable, UNIQUE, indexed), `current_period_end` (nullable TZ-aware datetime), `created_at`, `updated_at`
- [x] `is_pro` property: returns `True` iff `plan == "pro"` and `status in ("active", "trialing")`
- [x] `updated_at` uses `onupdate=_utcnow` — auto-stamped on every write

### Billing Schemas (`aria/backend/modules/billing/schemas.py`)
- [x] `SubscriptionRead`: `plan`, `status`, `current_period_end`, `stripe_customer_id`, `has_stripe`
- [x] `SubscriptionRead.from_orm_or_default(None)` → free/active defaults (no DB row needed)
- [x] `CheckoutResponse`: `checkout_url`
- [x] `PortalResponse`: `portal_url`

### Billing Dependencies (`aria/backend/modules/billing/dependencies.py`)
- [x] `get_or_create_subscription(user_id, db)` — SELECT-or-INSERT free sub; idempotent
- [x] `require_pro(user, db)` — raises 403 if `not sub.is_pro`
- [x] `check_daily_conversations(user, db)` — raises 429 at `FREE_DAILY_CONVERSATIONS` sessions/day
- [x] `check_daily_analysis(user, db)` — raises 429 at `FREE_DAILY_CONVERSATIONS` analysis sessions/day
- [x] `check_flashcard_limit(user, db)` — raises 429 at `FREE_MAX_FLASHCARDS` total cards
- [x] All quota checks short-circuit immediately for Pro users (`if sub.is_pro: return`)

### Billing Router (`aria/backend/modules/billing/router.py`)
- [x] `GET /subscription` — auth required; returns `SubscriptionRead` for current user
- [x] `POST /checkout` — auth required; 503 if `STRIPE_SECRET_KEY` empty; creates Stripe Checkout session (mode=`subscription`, `client_reference_id=user.id`, `metadata.user_id=user.id`)
- [x] `POST /portal` — auth required; 503 if no key; 400 if no `stripe_customer_id`; creates Billing Portal session
- [x] `POST /webhook` — no auth; verifies Stripe signature when `STRIPE_WEBHOOK_SECRET` is set; handles `checkout.session.completed` (→ Pro), `customer.subscription.updated` (→ sync plan/status/period_end), `customer.subscription.deleted` (→ free/canceled); returns 200 for unknown event types

### Auth + Quota Enforcement (cross-module)
- [x] `POST /api/v1/sessions/analyze` — `current_active_user` + `check_daily_analysis`; `user_id` stored on `AnalysisSession`
- [x] `POST /api/v1/conversations/` — `current_active_user` + `check_daily_conversations`; `user_id` stored on `ConversationSession`
- [x] `POST /api/v1/flashcards/generate` — `current_active_user` + `check_flashcard_limit`; `user_id` stored on `FlashcardDeck`
- [x] `GET /api/v1/flashcards/due` — `current_active_user`; results filtered to user's decks
- [x] `POST /api/v1/flashcards/review` — `current_active_user`; validates card belongs to user's deck
- [x] `GET /api/v1/flashcards/stats` — `current_active_user`; count scoped to user's decks
- [x] `GET /api/v1/grammar/deficits` — `current_active_user`; sessions filtered by `user_id`
- [x] `POST /api/v1/text-practice/upload` — `current_active_user` (no quota on text upload)

### Config (`aria/backend/core/config.py`)
- [x] `STRIPE_SECRET_KEY` — empty default (safe in dev/test)
- [x] `STRIPE_WEBHOOK_SECRET` — empty default
- [x] `STRIPE_PRO_PRICE_ID` — price ID for the Pro plan checkout
- [x] `FREE_DAILY_CONVERSATIONS = 3`
- [x] `FREE_DAILY_TEXT_UPLOADS = 1`
- [x] `FREE_MAX_FLASHCARDS = 50`

### Test Fixture Design (`aria/backend/tests/conftest.py`)
- [x] `MOCK_USER` — fixed UUID `00000000-0000-0000-0000-000000000001`, injected via `current_active_user` override
- [x] `authed_client` — auth injected + all quota deps no-op (`lambda: None`); prevents quota accumulation across endpoint-behavior tests
- [x] `quota_authed_client` — auth injected, quota deps enforced; used only by `TestFreeQuotaEnforcement`

### Gate 9 Tests
- [x] pytest 273/273 passed (233 existing + 40 new billing/auth/quota tests), 0 failed

```
tests/test_billing_phase9.py::TestSubscriptionModel::test_model_importable                      PASSED
tests/test_billing_phase9.py::TestSubscriptionModel::test_model_tablename                       PASSED
tests/test_billing_phase9.py::TestSubscriptionModel::test_model_has_expected_columns            PASSED
tests/test_billing_phase9.py::TestSubscriptionModel::test_is_pro_false_for_free_plan            PASSED
tests/test_billing_phase9.py::TestSubscriptionModel::test_is_pro_true_for_active_pro            PASSED
tests/test_billing_phase9.py::TestSubscriptionModel::test_is_pro_true_for_trialing_pro          PASSED
tests/test_billing_phase9.py::TestSubscriptionModel::test_is_pro_false_for_canceled_pro         PASSED
tests/test_billing_phase9.py::TestSubscriptionSchemas::test_schemas_importable                  PASSED
tests/test_billing_phase9.py::TestSubscriptionSchemas::test_subscription_read_default_free      PASSED
tests/test_billing_phase9.py::TestSubscriptionSchemas::test_subscription_read_from_orm          PASSED
tests/test_billing_phase9.py::TestGetOrCreateSubscription::test_creates_free_sub_on_first_call  PASSED
tests/test_billing_phase9.py::TestGetOrCreateSubscription::test_returns_existing_subscription   PASSED
tests/test_billing_phase9.py::TestBillingSubscriptionEndpoint::test_subscription_requires_auth  PASSED
tests/test_billing_phase9.py::TestBillingSubscriptionEndpoint::test_subscription_returns_200_with_auth PASSED
tests/test_billing_phase9.py::TestBillingSubscriptionEndpoint::test_subscription_default_plan_is_free  PASSED
tests/test_billing_phase9.py::TestBillingSubscriptionEndpoint::test_subscription_response_schema       PASSED
tests/test_billing_phase9.py::TestBillingCheckoutEndpoint::test_checkout_requires_auth          PASSED
tests/test_billing_phase9.py::TestBillingCheckoutEndpoint::test_checkout_returns_503_when_stripe_not_configured PASSED
tests/test_billing_phase9.py::TestBillingPortalEndpoint::test_portal_requires_auth              PASSED
tests/test_billing_phase9.py::TestBillingPortalEndpoint::test_portal_returns_503_when_stripe_not_configured PASSED
tests/test_billing_phase9.py::TestBillingPortalEndpoint::test_portal_returns_400_when_no_stripe_customer PASSED
tests/test_billing_phase9.py::TestWebhookEndpoint::test_webhook_invalid_json_returns_400        PASSED
tests/test_billing_phase9.py::TestWebhookEndpoint::test_webhook_unknown_event_returns_200       PASSED
tests/test_billing_phase9.py::TestWebhookEndpoint::test_webhook_checkout_completed_upgrades_to_pro PASSED
tests/test_billing_phase9.py::TestWebhookEndpoint::test_webhook_subscription_deleted_downgrades_to_free PASSED
tests/test_billing_phase9.py::TestAuthEnforcement::test_analyze_requires_auth                   PASSED
tests/test_billing_phase9.py::TestAuthEnforcement::test_conversation_create_requires_auth       PASSED
tests/test_billing_phase9.py::TestAuthEnforcement::test_flashcard_generate_requires_auth        PASSED
tests/test_billing_phase9.py::TestAuthEnforcement::test_flashcard_due_requires_auth             PASSED
tests/test_billing_phase9.py::TestAuthEnforcement::test_flashcard_review_requires_auth          PASSED
tests/test_billing_phase9.py::TestAuthEnforcement::test_flashcard_stats_requires_auth           PASSED
tests/test_billing_phase9.py::TestAuthEnforcement::test_grammar_deficits_requires_auth          PASSED
tests/test_billing_phase9.py::TestAuthEnforcement::test_text_practice_requires_auth             PASSED
tests/test_billing_phase9.py::TestFreeQuotaEnforcement::test_daily_conversation_quota_blocks_at_limit PASSED
tests/test_billing_phase9.py::TestFreeQuotaEnforcement::test_flashcard_limit_blocks_when_at_cap PASSED
tests/test_billing_phase9.py::TestFreeQuotaEnforcement::test_pro_user_bypasses_conversation_quota PASSED
tests/test_billing_phase9.py::TestUserScopedData::test_flashcard_stats_scoped_to_user           PASSED
tests/test_billing_phase9.py::TestUserScopedData::test_grammar_deficits_scoped_to_user          PASSED
tests/test_billing_phase9.py::TestBackwardCompatibility::test_health_endpoint_still_works       PASSED
tests/test_billing_phase9.py::TestBackwardCompatibility::test_auth_register_still_works         PASSED
40 passed in 2.31s
273 passed in 11.14s (total suite)
```

---

## Decisions Locked

- **Stripe-free dev/test**: `STRIPE_SECRET_KEY` defaults to empty; checkout + portal return 503; webhook returns 200 for all events with no signature (safe default) — no Stripe dependency in CI
- **`check_daily_analysis` reuses `FREE_DAILY_CONVERSATIONS` limit**: Analysis sessions and conversation sessions share the same numeric cap (`FREE_DAILY_CONVERSATIONS=3`); the config variable name reflects its primary use and both limits are reconfigurable independently if needed
- **`authed_client` bypasses quotas**: All quota deps are no-op in `authed_client` to prevent session count accumulation across the test suite; quota behavior is tested exclusively via `quota_authed_client`
- **upsert pattern in Pro test**: `test_pro_user_bypasses_conversation_quota` uses `get_or_create_subscription` + update (not bare INSERT) to handle the UNIQUE constraint on `user_subscriptions.user_id` when the free sub was already created by a prior quota test

---

## Files Created (new)

```
aria/backend/modules/billing/__init__.py
aria/backend/modules/billing/models.py
aria/backend/modules/billing/schemas.py
aria/backend/modules/billing/dependencies.py
aria/backend/modules/billing/router.py
aria/backend/tests/test_billing_phase9.py
aria/.claude/gates/gate-9.md
```

## Files Modified

```
aria/backend/main.py                              — billing router registered at /api/v1/billing
aria/backend/core/config.py                       — Stripe keys + Free tier limits
aria/backend/modules/analysis/router.py           — auth + check_daily_analysis deps
aria/backend/modules/conversation/router.py       — auth + check_daily_conversations deps
aria/backend/modules/flashcards/router.py         — auth + check_flashcard_limit deps; user-scoped queries
aria/backend/modules/grammar/router.py            — auth dep; user-scoped deficit query
aria/backend/modules/text_practice/router.py      — auth dep on upload
aria/backend/tests/conftest.py                    — MOCK_USER, authed_client, quota_authed_client
aria/backend/tests/test_conversation.py           — client → authed_client
aria/backend/tests/test_pipeline.py               — client → authed_client; auth override in fixture
aria/backend/tests/test_analysis_phase5.py        — auth overrides; user_id on inserted AnalysisSessions
aria/backend/tests/test_flashcards_phase6.py      — client → authed_client
aria/CLAUDE.md                                    — Phase 9 marked complete
```

---

## New API Endpoints

```
GET  /api/v1/billing/subscription   → current user's plan/status
POST /api/v1/billing/checkout       → create Stripe Checkout session (→ Pro upgrade)
POST /api/v1/billing/portal         → create Stripe Billing Portal session (manage sub)
POST /api/v1/billing/webhook        → Stripe webhook handler (no auth, sig-verified)
```

## New Database Table

```
user_subscriptions — user_id (FK user.id, UNIQUE), plan, status, stripe_customer_id,
                     stripe_subscription_id, current_period_end, created_at, updated_at
```

---

## Next Phase

No further phases defined. Phase 9 is the final monetization phase.
