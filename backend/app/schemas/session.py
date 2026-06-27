"""Session schemas for request/response validation."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SessionResponse(BaseModel):
    """Session response schema."""
    
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    
    id: str
    client_id: str
    title: str
    created_at: datetime
    duration_seconds: Optional[int] = None
    audio_path: str  # Just a string path, not a FilePath
    status: str
    processing_step: Optional[str] = None
    progress_pct: Optional[int] = None
    source_language: Optional[str] = None
    target_language: str
    transcript: Optional[str] = None
    translation: Optional[str] = None
    summary_bullets: Optional[list[str]] = None
    error_message: Optional[str] = None
    bookmarked: bool = False

    # Automatic Ayah linking (Arabic-only MVP)
    matched_surah: Optional[int] = None
    matched_ayah: Optional[int] = None
    matched_ayah_text_ar: Optional[str] = None
    matched_confidence_pct: Optional[int] = None
    matched_method: Optional[str] = None
    matched_candidates: Optional[list[dict]] = None
        
    @classmethod
    def from_orm_model(cls, session):
        """Convert ORM model to response schema."""
        import json
        
        # Parse summary_bullets_json if present
        summary_bullets = None
        if session.summary_bullets_json:
            try:
                summary_bullets = json.loads(session.summary_bullets_json)
            except json.JSONDecodeError:
                summary_bullets = None

        matched_candidates = None
        if getattr(session, "matched_candidates_json", None):
            try:
                matched_candidates = json.loads(session.matched_candidates_json)
            except json.JSONDecodeError:
                matched_candidates = None
        
        return cls(
            id=session.id,
            client_id=session.client_id,
            title=session.title,
            created_at=session.created_at,
            duration_seconds=session.duration_seconds,
            audio_path=session.audio_path,
            status=session.status,
            processing_step=getattr(session, "processing_step", None),
            progress_pct=getattr(session, "progress_pct", None),
            source_language=session.source_language,
            target_language=session.target_language,
            transcript=session.transcript,
            translation=session.translation,
            summary_bullets=summary_bullets,
            error_message=session.error_message,
            bookmarked=getattr(session, "bookmarked", False),
            matched_surah=getattr(session, "matched_surah", None),
            matched_ayah=getattr(session, "matched_ayah", None),
            matched_ayah_text_ar=getattr(session, "matched_ayah_text_ar", None),
            matched_confidence_pct=getattr(session, "matched_confidence_pct", None),
            matched_method=getattr(session, "matched_method", None),
            matched_candidates=matched_candidates,
        )


class SessionListResponse(BaseModel):
    """Paginated session list response."""
    
    items: list[SessionResponse]
    next_offset: Optional[int] = None


class SessionCreateForm(BaseModel):
    """Form data for creating a session (validated from multipart form)."""
    
    title: str = Field(..., min_length=1, max_length=500)
    target_language: str = Field(..., min_length=2, max_length=10)
    duration_seconds: Optional[int] = Field(None, ge=0)


class SessionUpdateRequest(BaseModel):
    """Partial update fields for a session."""

    bookmarked: Optional[bool] = None

