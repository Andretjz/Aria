# Gate 10 — Billing: Automatic Payment Methods + 14-Day Free Trial

**Date:** 2026-05-17
**Agent:** Anna_Auth (post-Phase 9 billing hardening)
**Branch:** `main`
**Verdict:** APPROVED

---

## Context

Phase 9 shipped with `payment_method_types=["card"]` (cards only) and no free trial.
This gate adds:

1. **Automatic payment methods** — Stripe determines accepted methods from dashboard config (Visa, Mastercard, Apple Pay, Google Pay, SEPA, iDEAL, etc.) instead of hard-coding card-only.
2. **14-day free trial** — required credit card upfront via `payment_method_collection="always"`; no charge until day 15. Complies with German §355 BGB / EU 14-day withdrawal right: the trial window is the cooling-off window.
3. **Correct trial status** — webhook `checkout.session.completed` now sets `status="trialing"` when `payment_status == "no_payment_required"` (trial), and `status="active"` when `payment_status == "paid"` (direct upgrade). Previously always hardcoded `"active"`.

### German Law Note
§355 BGB gives EU consumers a 14-day withdrawal right from **contract conclusion** (= trial start, when user agrees to subscription terms). The free trial covers this window; no payment is taken during it. By day 15 (first charge), the right has expired. Users can cancel any time during the trial via the Stripe Billing Portal; they keep access until trial ends.

---

## Checklist

### Billing Router (`aria/backend/modules/billing/router.py`)
- [x] `payment_method_types=["card"]` removed — Stripe automatic payment methods active
- [x] `payment_method_collection="always"` — credit card required upfront for trial signup
- [x] `subscription_data={"trial_period_days": 14}` — 14-day free trial on Pro checkout
- [x] `_handle_checkout_completed`: sets `status="trialing"` when `payment_status == "no_payment_required"`, `status="active"` when `payment_status == "paid"`
- [x] Log line updated to include `status` field

### Tests (`aria/backend/tests/test_billing_phase9.py`) — 4 new tests
- [x] `test_checkout_completed_trialing_sets_trialing_status` — webhook with `payment_status=no_payment_required` → `status=trialing`
- [x] `test_checkout_completed_paid_sets_active_status` — webhook with `payment_status=paid` → `status=active`
- [x] `test_trialing_pro_user_is_pro` — `UserSubscription.is_pro` is True for `plan=pro, status=trialing`
- [x] `test_checkout_session_has_trial_and_no_card_restriction` — mocked Stripe call confirms `trial_period_days=14`, `payment_method_collection=always`, no `payment_method_types`

### Gate 10 Tests
- [x] pytest 277/277 passed (273 existing + 4 new), 0 failed

```
backend/tests/test_billing_phase9.py::TestTrialAndPaymentMethods::test_checkout_completed_trialing_sets_trialing_status PASSED
backend/tests/test_billing_phase9.py::TestTrialAndPaymentMethods::test_checkout_completed_paid_sets_active_status        PASSED
backend/tests/test_billing_phase9.py::TestTrialAndPaymentMethods::test_trialing_pro_user_is_pro                         PASSED
backend/tests/test_billing_phase9.py::TestTrialAndPaymentMethods::test_checkout_session_has_trial_and_no_card_restriction PASSED
277 passed in 10.52s
```

---

## Decisions Locked

- **14 days globally** — not geo-targeted; simplest and legally sufficient for EU/Germany. The trial IS the cooling-off period.
- **Automatic payment methods** — zero code change needed to add SEPA/iDEAL/Apple Pay in future; just enable them in Stripe dashboard.
- **`payment_method_collection="always"`** — ensures a valid card/SEPA is on file before trial starts; avoids free rides with no payment method on record.
- **`trialing` status detection via `payment_status`** — avoids an extra Stripe API call to look up subscription status; `no_payment_required` is the canonical Stripe signal for a trial checkout.

---

## Files Modified

```
aria/backend/modules/billing/router.py       — automatic payments, 14-day trial, trialing status fix
aria/backend/tests/test_billing_phase9.py    — 4 new tests in TestTrialAndPaymentMethods
aria/CLAUDE.md                               — to be updated post-commit
aria/.claude/gates/gate-10.md               — this file
```

---

## Pending (not in this gate)

- Google OAuth (Google/GitHub login) — deferred until GOOGLE_OAUTH_CLIENT_ID is provisioned in .env
- Apple Sign-In — not implemented; requires new infrastructure
- Supabase migration via Alembic — blocked on Windows IPv6 DNS issue; will auto-apply on Fly.io deploy or can be run via Docker
