"""Note schemas for request/response validation."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    """Request schema for creating a note."""
    
    text: str = Field(..., min_length=1, max_length=10000)


class NoteResponse(BaseModel):
    """Note response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    session_id: str
    text: str
    created_at: datetime


class NoteListResponse(BaseModel):
    """Note list response."""
    
    items: list[NoteResponse]

