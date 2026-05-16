"""Billing Pydantic schemas — Phase 9 (Anna_Auth)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SubscriptionRead(BaseModel):
    plan: str
    status: str
    current_period_end: datetime | None = None
    stripe_customer_id: str | None = None
    has_stripe: bool = False

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_or_default(cls, sub: object | None) -> "SubscriptionRead":
        if sub is None:
            return cls(plan="free", status="active", has_stripe=False)
        return cls(
            plan=sub.plan,  # type: ignore[attr-defined]
            status=sub.status,  # type: ignore[attr-defined]
            current_period_end=sub.current_period_end,  # type: ignore[attr-defined]
            stripe_customer_id=sub.stripe_customer_id,  # type: ignore[attr-defined]
            has_stripe=sub.stripe_customer_id is not None,  # type: ignore[attr-defined]
        )


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalResponse(BaseModel):
    portal_url: str
