"""Highlights router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_client_id
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.highlight import Highlight
from app.models.session import Session as SessionModel
from app.schemas.highlight import HighlightCreateRequest, HighlightResponse
from app.utils.ids import generate_highlight_id
from app.utils.time import utc_now

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["highlights"])


@router.post("/sessions/{session_id}/highlights", response_model=HighlightResponse, status_code=201)
async def create_highlight(
    session_id: str,
    payload: HighlightCreateRequest,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
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
        raise HTTPException(status_code=404, detail="Session not found")

    highlight = Highlight(
        id=generate_highlight_id(),
        session_id=session_id,
        text=payload.text,
        created_at=utc_now(),
    )

    try:
        db.add(highlight)
        db.commit()
        db.refresh(highlight)
        logger.info(f"Created highlight {highlight.id} for session {session_id}")
        return HighlightResponse.model_validate(highlight)
    except Exception as e:
        logger.error(f"Failed to create highlight: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create highlight")


@router.get("/sessions/{session_id}/highlights", response_model=list[HighlightResponse])
async def list_highlights(
    session_id: str,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
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
        raise HTTPException(status_code=404, detail="Session not found")

    highlights = (
        db.query(Highlight)
        .filter(Highlight.session_id == session_id)
        .order_by(Highlight.created_at.desc())
        .all()
    )
    return [HighlightResponse.model_validate(h) for h in highlights]


@router.delete("/sessions/{session_id}/highlights/{highlight_id}")
async def delete_highlight(
    session_id: str,
    highlight_id: str,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
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
        raise HTTPException(status_code=404, detail="Session not found")

    highlight = (
        db.query(Highlight)
        .filter(
            Highlight.id == highlight_id,
            Highlight.session_id == session_id,
        )
        .first()
    )
    if not highlight:
        raise HTTPException(status_code=404, detail="Highlight not found")

    try:
        db.delete(highlight)
        db.commit()
        return {"ok": True}
    except Exception as e:
        logger.error(f"Failed to delete highlight: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete highlight")


