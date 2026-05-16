"""Analysis session ORM model.

Stores the result of each audio analysis run. One row per uploaded file.
FK to user is nullable — anonymous analysis is allowed in dev; Phase 9 will
enforce auth for cloud storage / session history.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from aria.backend.database import Base


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    audio_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    num_speakers: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # JSON blobs — read with json.loads(); written with json.dumps()
    transcript_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    vocabulary_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    fluency_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="complete")
