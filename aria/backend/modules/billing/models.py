"""Billing ORM model — UserSubscription (Phase 9 Anna_Auth).

One row per user, created on first billing action (or lazily on quota check).
Defaults to plan="free", status="active".
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from aria.backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserSubscription(Base):
    """Subscription state for a user — plan (free/pro) + Stripe identifiers."""

    __tablename__ = "user_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    # "free" | "pro"
    plan: Mapped[str] = mapped_column(String(20), nullable=False, default="free")
    # "active" | "trialing" | "past_due" | "canceled"
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    @property
    def is_pro(self) -> bool:
        return self.plan == "pro" and self.status in ("active", "trialing")
