"""Highlight model."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Highlight(Base):
    """Highlight model representing a snippet of text saved for a session."""

    __tablename__ = "highlights"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    session_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_highlights_session_created", "session_id", "created_at"),
    )


