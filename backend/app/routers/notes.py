"""Notes router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_client_id
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.note import Note
from app.models.session import Session as SessionModel
from app.schemas.note import NoteCreate, NoteResponse, NoteListResponse
from app.utils.ids import generate_note_id
from app.utils.time import utc_now

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["notes"])


@router.post("/sessions/{session_id}/notes", response_model=NoteResponse, status_code=201)
async def create_note(
    session_id: str,
    note_data: NoteCreate,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    """
    Create a new note for a session.
    
    Args:
        session_id: Session ID
        note_data: Note creation data
        client_id: Client ID from header
        db: Database session
        
    Returns:
        Created note
    """
    # Verify session exists and belongs to this client
    session = (
        db.query(SessionModel)
        .filter(
            SessionModel.id == session_id,
            SessionModel.client_id == client_id,
        )
        .first()
    )
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    # Create note
    note = Note(
        id=generate_note_id(),
        session_id=session_id,
        client_id=client_id,
        text=note_data.text,
        created_at=utc_now(),
    )
    
    try:
        db.add(note)
        db.commit()
        db.refresh(note)
        
        logger.info(f"Created note {note.id} for session {session_id}")
        
        return NoteResponse.from_orm(note)
        
    except Exception as e:
        logger.error(f"Failed to create note: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create note"
        )


@router.get("/sessions/{session_id}/notes", response_model=NoteListResponse)
async def list_notes(
    session_id: str,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    """
    List all notes for a session.
    
    Args:
        session_id: Session ID
        client_id: Client ID from header
        db: Database session
        
    Returns:
        List of notes
    """
    # Verify session exists and belongs to this client
    session = (
        db.query(SessionModel)
        .filter(
            SessionModel.id == session_id,
            SessionModel.client_id == client_id,
        )
        .first()
    )
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    # Query notes for this session
    notes = (
        db.query(Note)
        .filter(
            Note.session_id == session_id,
            Note.client_id == client_id,
        )
        .order_by(Note.created_at.desc())
        .all()
    )
    
    # Convert to response models
    items = [NoteResponse.from_orm(n) for n in notes]
    
    return NoteListResponse(items=items)

