"""Billing module router — Stripe subscriptions (Phase 9 Anna_Auth).

GET  /api/v1/billing/subscription  → current plan + status
POST /api/v1/billing/checkout      → create Stripe checkout session (Free→Pro)
POST /api/v1/billing/portal        → create Stripe billing portal session
POST /api/v1/billing/webhook       → Stripe webhook handler (no user auth)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aria.backend.core.config import settings
from aria.backend.core.logging import get_logger
from aria.backend.database import get_db
from aria.backend.modules.auth.models import User
from aria.backend.modules.auth.users import current_active_user
from aria.backend.modules.billing.dependencies import get_or_create_subscription
from aria.backend.modules.billing.models import UserSubscription
from aria.backend.modules.billing.schemas import (
    CheckoutResponse,
    PortalResponse,
    SubscriptionRead,
)

log = get_logger(__name__)
router = APIRouter()

# Stripe pro price ID — set in Stripe dashboard + wired via env var or hardcoded placeholder
_PRO_PRICE_ID = "price_pro_monthly"  # override in production via Stripe dashboard


@router.get(
    "/subscription",
    response_model=SubscriptionRead,
    summary="Get current subscription status",
)
async def get_subscription(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionRead:
    """Return the authenticated user's current plan and Stripe subscription state."""
    sub = await get_or_create_subscription(current_user.id, db)
    return SubscriptionRead.from_orm_or_default(sub)


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    summary="Create Stripe checkout session for Pro upgrade",
    responses={
        200: {"description": "Checkout URL returned"},
        503: {"description": "Stripe not configured"},
    },
)
async def create_checkout(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    """Create a Stripe Checkout Session for upgrading to Pro.

    Returns a checkout_url the frontend redirects to.
    Returns 503 when STRIPE_SECRET_KEY is not configured.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Payment processing is not configured. Contact support.",
        )

    import stripe  # type: ignore[import]

    stripe.api_key = settings.STRIPE_SECRET_KEY

    sub = await get_or_create_subscription(current_user.id, db)

    # Get or create Stripe customer
    if sub.stripe_customer_id:
        customer_id = sub.stripe_customer_id
    else:
        customer = stripe.Customer.create(email=current_user.email)
        customer_id = customer["id"]
        sub.stripe_customer_id = customer_id
        await db.commit()

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": _PRO_PRICE_ID, "quantity": 1}],
        mode="subscription",
        success_url="https://aria-backend.fly.dev/api/v1/billing/subscription",
        cancel_url="https://aria-backend.fly.dev/api/v1/billing/subscription",
        metadata={"user_id": str(current_user.id)},
    )

    log.info("checkout_session_created", user_id=str(current_user.id))
    return CheckoutResponse(checkout_url=session["url"])


@router.post(
    "/portal",
    response_model=PortalResponse,
    summary="Create Stripe billing portal session",
    responses={
        200: {"description": "Portal URL returned"},
        400: {"description": "No Stripe customer linked to this account"},
        503: {"description": "Stripe not configured"},
    },
)
async def create_portal(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PortalResponse:
    """Create a Stripe Customer Portal session for managing the subscription."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Payment processing is not configured.",
        )

    sub = await get_or_create_subscription(current_user.id, db)
    if not sub.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No billing account linked. Create a subscription first.",
        )

    import stripe  # type: ignore[import]

    stripe.api_key = settings.STRIPE_SECRET_KEY

    portal_session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url="https://aria-backend.fly.dev/api/v1/billing/subscription",
    )

    log.info("portal_session_created", user_id=str(current_user.id))
    return PortalResponse(portal_url=portal_session["url"])


@router.post(
    "/webhook",
    summary="Stripe webhook handler",
    description="Receives Stripe subscription lifecycle events and updates user plan.",
    status_code=200,
)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle Stripe webhook events.

    Verifies the Stripe signature when STRIPE_WEBHOOK_SECRET is set.
    Handles: checkout.session.completed, customer.subscription.updated,
             customer.subscription.deleted.
    """
    payload = await request.body()

    if settings.STRIPE_WEBHOOK_SECRET:
        import stripe  # type: ignore[import]

        stripe.api_key = settings.STRIPE_SECRET_KEY
        sig_header = request.headers.get("stripe-signature", "")
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except Exception as exc:
            log.warning("webhook_signature_invalid", error=str(exc))
            raise HTTPException(status_code=400, detail="Invalid webhook signature.")
    else:
        try:
            event = json.loads(payload)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON payload.")

    event_type = event.get("type") if isinstance(event, dict) else getattr(event, "type", "")
    data_object = (
        event.get("data", {}).get("object", {})
        if isinstance(event, dict)
        else event["data"]["object"]
    )

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(data_object, db)
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(data_object, db)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(data_object, db)
    else:
        log.info("webhook_event_ignored", event_type=event_type)

    return {"received": True}


async def _handle_checkout_completed(data: dict, db: AsyncSession) -> None:
    customer_id = data.get("customer")
    subscription_id = data.get("subscription")
    user_id_str = (data.get("metadata") or {}).get("user_id")

    if not user_id_str or not customer_id:
        log.warning("checkout_completed_missing_metadata", data=data)
        return

    import uuid
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        return

    result = await db.execute(
        select(UserSubscription).where(UserSubscription.user_id == user_id)
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        sub = UserSubscription(user_id=user_id)
        db.add(sub)

    sub.plan = "pro"
    sub.status = "active"
    sub.stripe_customer_id = customer_id
    sub.stripe_subscription_id = subscription_id
    sub.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    log.info("subscription_activated", user_id=user_id_str)


async def _handle_subscription_updated(data: dict, db: AsyncSession) -> None:
    stripe_sub_id = data.get("id")
    new_status = data.get("status", "active")
    period_end_ts = data.get("current_period_end")

    if not stripe_sub_id:
        return

    result = await db.execute(
        select(UserSubscription).where(
            UserSubscription.stripe_subscription_id == stripe_sub_id
        )
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        return

    sub.status = new_status
    if new_status in ("canceled", "unpaid"):
        sub.plan = "free"
    if period_end_ts:
        sub.current_period_end = datetime.fromtimestamp(period_end_ts, tz=timezone.utc)
    sub.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    log.info("subscription_updated", stripe_sub_id=stripe_sub_id, status=new_status)


async def _handle_subscription_deleted(data: dict, db: AsyncSession) -> None:
    stripe_sub_id = data.get("id")
    if not stripe_sub_id:
        return

    result = await db.execute(
        select(UserSubscription).where(
            UserSubscription.stripe_subscription_id == stripe_sub_id
        )
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        return

    sub.plan = "free"
    sub.status = "canceled"
    sub.stripe_subscription_id = None
    sub.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    log.info("subscription_canceled", user_id=str(sub.user_id))
