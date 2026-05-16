"""create analysis_sessions table

Revision ID: 002
Revises: 001
Create Date: 2026-05-16

Creates: analysis_sessions
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
        sa.Column("audio_filename", sa.String(length=255), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("num_speakers", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("transcript_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("vocabulary_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("fluency_score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="complete"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_sessions_user_id", "analysis_sessions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_analysis_sessions_user_id", table_name="analysis_sessions")
    op.drop_table("analysis_sessions")
