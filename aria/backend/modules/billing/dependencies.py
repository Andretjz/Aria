"""Billing FastAPI dependencies — quota checks and Pro enforcement (Phase 9)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aria.backend.core.config import settings
from aria.backend.database import get_db
from aria.backend.modules.auth.models import User
from aria.backend.modules.auth.users import current_active_user
from aria.backend.modules.billing.models import UserSubscription


async def get_or_create_subscription(
    user_id: uuid.UUID,
    db: AsyncSession,
) -> UserSubscription:
    """Return existing subscription or create a free-tier one."""
    result = await db.execute(
        select(UserSubscription).where(UserSubscription.user_id == user_id)
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        sub = UserSubscription(user_id=user_id, plan="free", status="active")
        db.add(sub)
        await db.commit()
        await db.refresh(sub)
    return sub


async def require_pro(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Raise 403 if user does not have an active Pro subscription."""
    sub = await get_or_create_subscription(current_user.id, db)
    if not sub.is_pro:
        raise HTTPException(
            status_code=403,
            detail="Pro subscription required. Upgrade at /api/v1/billing/checkout.",
        )


def _today_start() -> datetime:
    return datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


async def check_daily_conversations(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Block free-tier users who have hit their daily conversation limit."""
    sub = await get_or_create_subscription(current_user.id, db)
    if sub.is_pro:
        return
    from aria.backend.modules.conversation.models import ConversationSession

    count = (
        await db.execute(
            select(func.count())
            .select_from(ConversationSession)
            .where(
                ConversationSession.user_id == current_user.id,
                ConversationSession.created_at >= _today_start(),
            )
        )
    ).scalar() or 0
    if count >= settings.FREE_DAILY_CONVERSATIONS:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Free tier: {settings.FREE_DAILY_CONVERSATIONS} conversations/day. "
                "Upgrade to Pro for unlimited access."
            ),
        )


async def check_daily_analysis(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Block free-tier users who have hit their daily analysis session limit."""
    sub = await get_or_create_subscription(current_user.id, db)
    if sub.is_pro:
        return
    from aria.backend.modules.analysis.models import AnalysisSession

    count = (
        await db.execute(
            select(func.count())
            .select_from(AnalysisSession)
            .where(
                AnalysisSession.user_id == current_user.id,
                AnalysisSession.created_at >= _today_start(),
            )
        )
    ).scalar() or 0
    if count >= settings.FREE_DAILY_CONVERSATIONS:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Free tier: {settings.FREE_DAILY_CONVERSATIONS} analysis sessions/day. "
                "Upgrade to Pro for unlimited access."
            ),
        )


async def check_flashcard_limit(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Block free-tier users who have reached the flashcard cap."""
    sub = await get_or_create_subscription(current_user.id, db)
    if sub.is_pro:
        return
    from aria.backend.modules.flashcards.models import Flashcard, FlashcardDeck

    count = (
        await db.execute(
            select(func.count())
            .select_from(Flashcard)
            .join(FlashcardDeck, Flashcard.deck_id == FlashcardDeck.id)
            .where(FlashcardDeck.user_id == current_user.id)
        )
    ).scalar() or 0
    if count >= settings.FREE_MAX_FLASHCARDS:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Free tier: {settings.FREE_MAX_FLASHCARDS} flashcards maximum. "
                "Upgrade to Pro for unlimited cards."
            ),
        )
