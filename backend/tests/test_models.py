"""Test database models."""
import pytest
from datetime import datetime

from app.models.session import Session
from app.models.note import Note
from app.models.highlight import Highlight
from app.utils.ids import generate_ulid_like_id
from app.utils.time import utc_now


def test_session_model_creation():
    """Test Session model can be instantiated."""
    session_id = generate_ulid_like_id("sess")
    session = Session(
        id=session_id,
        client_id="test-client-123",
        title="Test Session",
        created_at=utc_now(),
        duration_seconds=120,
        audio_path="data/uploads/test.m4a",
        status="uploaded",
        target_language="en",
        bookmarked=False,
    )
    
    assert session.id == session_id
    assert session.client_id == "test-client-123"
    assert session.title == "Test Session"
    assert session.status == "uploaded"
    assert session.target_language == "en"
    assert session.bookmarked is False


def test_note_model_creation():
    """Test Note model can be instantiated."""
    note_id = generate_ulid_like_id("note")
    session_id = generate_ulid_like_id("sess")
    
    note = Note(
        id=note_id,
        session_id=session_id,
        client_id="test-client-123",
        text="This is a test note",
        created_at=utc_now(),
    )
    
    assert note.id == note_id
    assert note.session_id == session_id
    assert note.client_id == "test-client-123"
    assert note.text == "This is a test note"


def test_highlight_model_creation():
    """Test Highlight model can be instantiated."""
    hl_id = generate_ulid_like_id("hl")
    session_id = generate_ulid_like_id("sess")

    hl = Highlight(
        id=hl_id,
        session_id=session_id,
        text="A highlight",
        created_at=utc_now(),
    )

    assert hl.id == hl_id
    assert hl.session_id == session_id
    assert hl.text == "A highlight"


def test_generate_ulid_like_id():
    """Test ID generation."""
    session_id = generate_ulid_like_id("sess")
    assert session_id.startswith("sess_")
    assert len(session_id) > 10
    
    note_id = generate_ulid_like_id("note")
    assert note_id.startswith("note_")
    
    # IDs should be unique
    id1 = generate_ulid_like_id("test")
    id2 = generate_ulid_like_id("test")
    assert id1 != id2

