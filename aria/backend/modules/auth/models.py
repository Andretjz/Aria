"""Auth ORM models — User, OAuthAccount, UserPreferences, UserSession."""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from fastapi_users.db import SQLAlchemyBaseOAuthAccountTableUUID, SQLAlchemyBaseUserTableUUID
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from aria.backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLAlchemyBaseUserTableUUID, Base):
    """Core user record — extended by FastAPI-Users base (id, email, hashed_password, flags)."""


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    """OAuth provider tokens linked to a User."""

    # Override base user_id to add FK + cascade
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )


class UserPreferences(Base):
    """Per-user language settings (1:1 with User, created on registration)."""

    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    input_lang: Mapped[str] = mapped_column(String(10), default="en")
    target_lang: Mapped[str] = mapped_column(String(10), default="de")
    feedback_lang: Mapped[str] = mapped_column(String(10), default="en")
    ui_lang: Mapped[str] = mapped_column(String(10), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class UserSession(Base):
    """Refresh token store — one row per active login session."""

    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    # SHA-256 of the raw token; raw token is sent to client, never stored
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    @staticmethod
    def make_token() -> tuple[str, str]:
        """Return (raw_token, token_hash). Store hash; send raw to client."""
        raw = secrets.token_urlsafe(32)
        return raw, hashlib.sha256(raw.encode()).hexdigest()
