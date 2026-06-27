"""Sessions router."""
import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.config import settings
from app.core.dependencies import get_client_id
from app.core.errors import QuranNotesException, UploadTooLargeError
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.session import Session as SessionModel
from app.schemas.session import SessionResponse, SessionListResponse, SessionUpdateRequest
from app.services.processing import process_session_sync
from app.services.storage import storage
from app.utils.ids import generate_session_id
from app.utils.time import ensure_utc, utc_now

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["sessions"])


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    request: Request,
    background_tasks: BackgroundTasks,
    title: str = Form(..., min_length=1, max_length=500),
    target_language: str = Form(..., min_length=2, max_length=10),
    duration_seconds: Optional[int] = Form(None),
    audio: UploadFile = File(...),
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    """
    Create a new session with audio upload.
    
    Args:
        title: Session title
        target_language: Target language code for translation
        duration_seconds: Optional recording duration
        audio: Audio file upload
        client_id: Client ID from header
        db: Database session
        background_tasks: FastAPI background tasks
        
    Returns:
        Created session
    """
    # Best-effort early rejection for clearly too-large requests. For multipart uploads, the
    # Content-Length includes form overhead, so we allow a small buffer.
    try:
        content_length = request.headers.get("content-length")
        if content_length:
            max_bytes = int(getattr(settings, "max_upload_bytes", 0) or 0)
            if max_bytes and int(content_length) > max_bytes + (2 * 1024 * 1024):
                raise HTTPException(
                    status_code=413,
                    detail=f"Audio file too large. Max is {settings.max_upload_mb} MB.",
                )
    except Exception:
        # Ignore header parsing issues; streaming enforcement still applies.
        pass

    # Validate audio file
    allowed_exts = {".m4a", ".mp3", ".wav", ".aac", ".ogg", ".flac", ".mp4", ".webm"}
    filename_lower = (audio.filename or "").lower()
    ext = ("." + filename_lower.rsplit(".", 1)[-1]) if "." in filename_lower else ""
    content_type_ok = bool(audio.content_type and audio.content_type.startswith("audio/"))
    ext_ok = ext in allowed_exts
    if not (content_type_ok or ext_ok):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio file type: {audio.content_type or 'unknown'}"
        )
    
    # Generate session ID
    session_id = generate_session_id()
    
    try:
        # Save audio file to storage
        audio_filename = f"audio{get_file_extension(audio.filename or 'audio.m4a')}"
        audio_path = await storage.save_upload(
            session_id=session_id,
            filename=audio_filename,
            file_content=audio.file,
        )
        
        # Create session in database
        session = SessionModel(
            id=session_id,
            client_id=client_id,
            title=title,
            created_at=utc_now(),
            duration_seconds=duration_seconds,
            audio_path=audio_path,
            status="uploaded",
            processing_step="queued",
            progress_pct=0,
            processing_started_at=None,
            processing_updated_at=utc_now(),
            attempt_count=0,
            last_error_step=None,
            target_language=target_language,
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Created session {session_id} for client {client_id}")
        
        # Trigger background processing
        background_tasks.add_task(process_session_sync, session_id, client_id)
        
        # Return response - use dict to avoid pydantic validation issues
        return SessionResponse(
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
            summary_bullets=None,
            error_message=session.error_message,
            bookmarked=getattr(session, "bookmarked", False),
        )
        
    except UploadTooLargeError as e:
        logger.warning(f"Upload too large for session {session_id}: {e}")
        db.rollback()
        try:
            storage.delete_session_files(session_id)
        except Exception:
            pass
        raise HTTPException(status_code=413, detail=str(e))
    except QuranNotesException as e:
        # Preserve custom status codes/messages (e.g., empty upload) rather than treating
        # them as generic 500s.
        logger.warning(f"Session creation failed (expected): {e}")
        db.rollback()
        try:
            storage.delete_session_files(session_id)
        except Exception:
            pass
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to create session: {e}", exc_info=True)
        db.rollback()
        # Cleanup storage on failure
        try:
            storage.delete_session_files(session_id)
        except Exception:
            pass
        # Return more detailed error in dev mode
        from app.core.config import settings
        detail = f"Failed to create session: {str(e)}" if settings.env == "dev" else "Failed to create session"
        raise HTTPException(
            status_code=500,
            detail=detail
        )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    offset: int = 0,
    limit: int = 20,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    """
    List sessions for the authenticated client.
    
    Args:
        offset: Pagination offset
        limit: Number of items to return (max 100)
        client_id: Client ID from header
        db: Database session
        
    Returns:
        Paginated list of sessions
    """
    # Limit max page size
    limit = min(limit, 100)
    
    # Query sessions for this client
    query = (
        db.query(SessionModel)
        .filter(SessionModel.client_id == client_id)
        .order_by(SessionModel.created_at.desc())
    )
    
    # Get one extra to determine if there are more results
    sessions = query.offset(offset).limit(limit + 1).all()
    
    # Check if there are more results
    has_more = len(sessions) > limit
    if has_more:
        sessions = sessions[:limit]
        next_offset = offset + limit
    else:
        next_offset = None
    
    # Convert to response models
    items = [SessionResponse.from_orm_model(s) for s in sessions]
    
    return SessionListResponse(items=items, next_offset=next_offset)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    """
    Get a specific session by ID.
    
    Args:
        session_id: Session ID
        client_id: Client ID from header
        db: Database session
        
    Returns:
        Session details
    """
    # Query session with client_id validation
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
    
    return SessionResponse.from_orm_model(session)


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    payload: SessionUpdateRequest,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    """
    Partially update a session (MVP: bookmarking).
    """
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

    changed = False
    if payload.bookmarked is not None:
        session.bookmarked = bool(payload.bookmarked)
        changed = True

    if changed:
        db.commit()
        db.refresh(session)

    return SessionResponse.from_orm_model(session)


@router.post("/sessions/{session_id}/bookmark", response_model=SessionResponse)
async def set_session_bookmark(
    session_id: str,
    payload: SessionUpdateRequest,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    """
    Set session bookmark state.

    This exists in addition to PATCH /sessions/{id} for compatibility with clients/environments
    that don't reliably support PATCH.
    """
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

    if payload.bookmarked is None:
        raise HTTPException(status_code=400, detail="bookmarked is required")

    session.bookmarked = bool(payload.bookmarked)
    db.commit()
    db.refresh(session)
    return SessionResponse.from_orm_model(session)


@router.post("/sessions/{session_id}/retry")
async def retry_session_processing(
    session_id: str,
    background_tasks: BackgroundTasks,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    """
    Retry processing for a failed session.
    
    Args:
        session_id: Session ID
        background_tasks: FastAPI background tasks
        client_id: Client ID from header
        db: Database session
        
    Returns:
        Success response
    """
    # Query session with client_id validation
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
    
    # Allow retry for failed or uploaded sessions (uploaded can get stuck if the server
    # restarts before the background task runs).
    if session.status not in ("failed", "uploaded", "processing"):
        raise HTTPException(status_code=400, detail="Can only retry uploaded, processing, or failed sessions")

    # If it's actively processing (fresh heartbeat), don't stomp on the running work.
    if session.status == "processing" and getattr(session, "processing_updated_at", None) is not None:
        lease_minutes = int(getattr(settings, "processing_lease_minutes", 10) or 10)
        age_seconds = (utc_now() - ensure_utc(session.processing_updated_at)).total_seconds()
        if age_seconds < lease_minutes * 60:
            raise HTTPException(
                status_code=400,
                detail="Session is currently processing. Please wait a moment and try again.",
            )
    
    # Reset session to uploaded state
    session.status = "uploaded"
    session.error_message = None
    session.processing_step = "queued"
    session.progress_pct = 0
    session.processing_updated_at = utc_now()
    session.last_error_step = None
    db.commit()
    
    logger.info(f"Retrying session {session_id}")
    
    # Trigger background processing
    background_tasks.add_task(process_session_sync, session_id, client_id)
    
    return {"ok": True}


def get_file_extension(filename: str) -> str:
    """
    Extract file extension from filename.
    
    Args:
        filename: Original filename
        
    Returns:
        File extension with dot (e.g., '.m4a')
    """
    if "." in filename:
        return "." + filename.rsplit(".", 1)[-1]
    return ".m4a"  # Default extension


@router.post("/dev/sessions/recover-stuck")
async def recover_stuck_sessions(
    background_tasks: BackgroundTasks,
    threshold_minutes: int = 30,
    action: str = "reset",
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    Dev-only: recover sessions that appear stuck in uploaded/processing.

    - action=reset: resets to uploaded/queued and re-enqueues processing
    - action=fail: marks as failed with a user-friendly message
    """
    if settings.env != "dev":
        raise HTTPException(status_code=404, detail="Not found")

    threshold_minutes = max(1, min(int(threshold_minutes), 24 * 60))
    limit = max(1, min(int(limit), 200))
    action = (action or "").strip().lower()
    if action not in ("reset", "fail"):
        raise HTTPException(status_code=400, detail="Invalid action. Use reset or fail.")

    cutoff = datetime.utcnow() - timedelta(minutes=threshold_minutes)

    stuck_query = (
        db.query(SessionModel)
        .filter(SessionModel.status.in_(("uploaded", "processing")))
        .filter(
            or_(
                # Older rows (pre-heartbeat columns) fall back to created_at
                (SessionModel.processing_updated_at.is_(None) & (SessionModel.created_at < cutoff)),
                (SessionModel.processing_updated_at.is_not(None) & (SessionModel.processing_updated_at < cutoff)),
            )
        )
        .order_by(SessionModel.created_at.asc())
        .limit(limit)
    )
    stuck = stuck_query.all()

    recovered_ids: list[str] = []
    for s in stuck:
        if action == "fail":
            s.status = "failed"
            s.error_message = "Processing timed out - tap retry."
            s.processing_updated_at = utc_now()
            recovered_ids.append(s.id)
            continue

        # reset
        s.status = "uploaded"
        s.processing_step = "queued"
        s.progress_pct = 0
        s.error_message = None
        s.processing_started_at = None
        s.processing_updated_at = utc_now()
        s.last_error_step = None
        recovered_ids.append(s.id)
        background_tasks.add_task(process_session_sync, s.id, s.client_id)

    db.commit()

    return {"ok": True, "count": len(recovered_ids), "session_ids": recovered_ids, "action": action}

