"""Note model."""
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Note(Base):
    """Note model representing user notes for a session."""
    
    __tablename__ = "notes"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    
    # Foreign key to session
    session_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Client/auth (for validation)
    client_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Content
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("ix_notes_session_created", "session_id", "created_at"),
    )

