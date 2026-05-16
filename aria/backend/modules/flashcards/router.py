"""Flashcards module router — SM-2 spaced repetition API."""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aria.backend.database import get_db
from aria.backend.modules.flashcards.models import Flashcard, FlashcardDeck, FlashcardReview
from aria.backend.modules.flashcards.schemas import (
    FlashcardDeckRead,
    FlashcardDueRead,
    FlashcardRead,
    FlashcardReviewRead,
    GenerateRequest,
    GenerateResponse,
    ReviewRequest,
    StatsRead,
)

router = APIRouter()

DB = Annotated[AsyncSession, Depends(get_db)]


def apply_sm2(review: FlashcardReview, quality: int) -> None:
    """Apply the SM-2 algorithm to update a card's review state in-place.

    quality 0-2 = forgot; quality 3-5 = remembered.
    ease_factor is bounded below at 1.3 per the SM-2 spec.
    """
    if quality >= 3:
        if review.repetitions == 0:
            interval = 1
        elif review.repetitions == 1:
            interval = 6
        else:
            interval = round(review.interval * review.ease_factor)
        review.repetitions += 1
        ef = review.ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        review.ease_factor = max(1.3, ef)
        review.interval = interval
    else:
        review.repetitions = 0
        review.interval = 1

    review.last_reviewed = date.today()
    review.next_review = date.today() + timedelta(days=review.interval)


@router.get("/due", response_model=list[FlashcardDueRead])
async def get_due(db: DB) -> list[FlashcardDueRead]:
    """Return all cards whose next_review date is today or earlier."""
    today = date.today()
    result = await db.execute(
        select(Flashcard, FlashcardReview)
        .join(FlashcardReview, FlashcardReview.flashcard_id == Flashcard.id)
        .where(FlashcardReview.next_review <= today)
        .order_by(FlashcardReview.next_review)
    )
    return [
        FlashcardDueRead(
            card=FlashcardRead.model_validate(card),
            review=FlashcardReviewRead.model_validate(rev),
        )
        for card, rev in result.all()
    ]


@router.post("/review", response_model=FlashcardReviewRead)
async def submit_review(body: ReviewRequest, db: DB) -> FlashcardReviewRead:
    """Submit a SM-2 quality rating for a card and update its review schedule."""
    row = await db.execute(
        select(FlashcardReview).where(FlashcardReview.flashcard_id == body.flashcard_id)
    )
    review = row.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard not found")
    apply_sm2(review, body.quality)
    await db.commit()
    await db.refresh(review)
    return FlashcardReviewRead.model_validate(review)


@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_cards(body: GenerateRequest, db: DB) -> GenerateResponse:
    """Create a deck and flashcards from a vocabulary list."""
    deck = FlashcardDeck(
        name=body.deck_name,
        source_language=body.source_language,
        target_language=body.target_language,
    )
    db.add(deck)
    await db.flush()

    cards: list[Flashcard] = []
    for item in body.vocabulary:
        card = Flashcard(
            deck_id=deck.id,
            word=item.word,
            cefr_level=item.cefr_level,
            definition=item.definition,
            example_sentence=item.example_sentence,
        )
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
        cards.append(card)

    await db.commit()
    await db.refresh(deck)
    for card in cards:
        await db.refresh(card)

    return GenerateResponse(
        deck=FlashcardDeckRead.model_validate(deck),
        cards_created=len(cards),
        cards=[FlashcardRead.model_validate(c) for c in cards],
    )


@router.get("/stats", response_model=StatsRead)
async def get_stats(db: DB) -> StatsRead:
    """Return aggregate learning statistics."""
    today = date.today()

    total = (await db.execute(select(func.count()).select_from(Flashcard))).scalar() or 0
    due = (
        await db.execute(
            select(func.count())
            .select_from(FlashcardReview)
            .where(FlashcardReview.next_review <= today)
        )
    ).scalar() or 0
    mastered = (
        await db.execute(
            select(func.count())
            .select_from(FlashcardReview)
            .where(FlashcardReview.interval >= 21)
        )
    ).scalar() or 0

    return StatsRead(total_cards=total, cards_due=due, cards_mastered=mastered)
