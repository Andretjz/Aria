"""extend analysis_sessions with Phase 5 columns

Revision ID: 004
Revises: 003
Create Date: 2026-05-16

Adds: quiz_json, grammar_json, voice_blueprints_json (all nullable Text)
to the analysis_sessions table. Pre-Phase-5 sessions keep NULL for all three.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("analysis_sessions", sa.Column("quiz_json", sa.Text(), nullable=True))
    op.add_column("analysis_sessions", sa.Column("grammar_json", sa.Text(), nullable=True))
    op.add_column("analysis_sessions", sa.Column("voice_blueprints_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("analysis_sessions", "voice_blueprints_json")
    op.drop_column("analysis_sessions", "grammar_json")
    op.drop_column("analysis_sessions", "quiz_json")
