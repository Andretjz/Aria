"""create flashcard tables

Revision ID: 005
Revises: 004
Create Date: 2026-05-16

Creates: flashcard_decks, flashcards, flashcard_reviews
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "flashcard_decks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_language", sa.String(length=10), nullable=False, server_default="en"),
        sa.Column("target_language", sa.String(length=10), nullable=False, server_default="en"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_flashcard_decks_user_id", "flashcard_decks", ["user_id"])

    op.create_table(
        "flashcards",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("deck_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
        sa.Column("word", sa.String(length=255), nullable=False),
        sa.Column("cefr_level", sa.String(length=5), nullable=True),
        sa.Column("definition", sa.String(length=1000), nullable=True),
        sa.Column("example_sentence", sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(["deck_id"], ["flashcard_decks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_flashcards_deck_id", "flashcards", ["deck_id"])

    op.create_table(
        "flashcard_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("flashcard_id", sa.Uuid(), nullable=False),
        sa.Column("ease_factor", sa.Float(), nullable=False, server_default="2.5"),
        sa.Column("interval", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("repetitions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_review", sa.Date(), nullable=False),
        sa.Column("last_reviewed", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["flashcard_id"], ["flashcards.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("flashcard_id", name="uq_flashcard_reviews_flashcard_id"),
    )
    op.create_index("ix_flashcard_reviews_flashcard_id", "flashcard_reviews", ["flashcard_id"])


def downgrade() -> None:
    op.drop_index("ix_flashcard_reviews_flashcard_id", table_name="flashcard_reviews")
    op.drop_table("flashcard_reviews")
    op.drop_index("ix_flashcards_deck_id", table_name="flashcards")
    op.drop_table("flashcards")
    op.drop_index("ix_flashcard_decks_user_id", table_name="flashcard_decks")
    op.drop_table("flashcard_decks")
