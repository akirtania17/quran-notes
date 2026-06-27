"""Session model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Session(Base):
    """Session model representing an audio recording session."""
    
    __tablename__ = "sessions"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    
    # Client/auth
    client_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Metadata
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Audio
    audio_path: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Processing status
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="uploaded")
    processing_step: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    progress_pct: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Processing reliability/observability
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error_step: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    
    # Languages
    source_language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    target_language: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # AI outputs
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    translation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary_bullets_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    # Automatic Ayah linking (Arabic-only MVP)
    matched_surah: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    matched_ayah: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    matched_ayah_text_ar: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    matched_confidence_pct: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    matched_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    matched_candidates_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Stickiness features
    bookmarked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Indexes
    __table_args__ = (
        Index("ix_sessions_client_created", "client_id", "created_at"),
        Index("ix_sessions_status", "status"),
    )

