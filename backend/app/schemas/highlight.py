"""Highlight schemas for request/response validation."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HighlightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: str
    session_id: str
    text: str
    created_at: datetime


class HighlightCreateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


