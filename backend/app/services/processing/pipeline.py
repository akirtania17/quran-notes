"""Processing pipeline for session audio processing."""
import json
import time
from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger, kv
from app.db.session import SessionLocal
from app.models.session import Session as SessionModel
from app.services.ayah_linking.matcher import match_ayah
from app.services.ai.openai_provider import openai_provider
from app.services.storage.resolve import resolve_audio_to_local_path
from app.utils.time import ensure_utc, utc_now

logger = get_logger(__name__)


def _step_progress(step: str) -> int:
    if step == "transcribing":
        return 15
    if step == "ayah_linking":
        return 35
    if step == "translating":
        return 55
    if step == "summarizing":
        return 80
    if step == "complete":
        return 100
    return 0


def _next_step(session: SessionModel) -> str:
    """
    Determine the next step needed for this session, allowing safe resume.
    """
    if session.transcript is None or len(session.transcript.strip()) == 0:
        return "transcribing"
    # Ayah linking is considered "done" once we have attempted it (matched_method set),
    # even if no confident match was found.
    if getattr(session, "matched_method", None) is None:
        return "ayah_linking"
    if session.translation is None or len(session.translation.strip()) == 0:
        return "translating"
    if session.summary_bullets_json is None or len(session.summary_bullets_json.strip()) == 0:
        return "summarizing"
    return "complete"


async def process_session(session_id: str, client_id: str) -> None:
    """
    Process a session: transcribe → translate → summarize.
    
    This function is designed to run as a background task.
    It updates the session status as it progresses.
    
    Args:
        session_id: Session ID to process
        client_id: Client ID for validation
    """
    logger.info(f"Starting processing for session {session_id}")
    
    # Create a new DB session for this background task
    db = SessionLocal()
    
    try:
        # Fetch the session
        session = (
            db.query(SessionModel)
            .filter(
                SessionModel.id == session_id,
                SessionModel.client_id == client_id,
            )
            .first()
        )
        
        if not session:
            logger.error(f"Session {session_id} not found for client {client_id}")
            return

        # Fail fast with a clear error if OpenAI isn't configured
        api_key = (settings.openai_api_key or "").strip()
        if not api_key or api_key.lower() == "changeme":
            session.status = "failed"
            session.processing_step = session.processing_step or "queued"
            session.progress_pct = session.progress_pct if session.progress_pct is not None else 0
            session.error_message = "OpenAI API key not configured. Create backend/.env and set OPENAI_API_KEY=your_key."
            db.commit()
            logger.error("OpenAI API key not configured; session marked as failed")
            return

        # If already complete, do nothing.
        if session.status == "complete":
            logger.info(f"Session {session_id} already complete; skipping processing")
            return

        # Simple lease: avoid duplicate concurrent processing.
        lease_minutes = int(getattr(settings, "processing_lease_minutes", 10) or 10)
        if (
            session.status == "processing"
            and getattr(session, "processing_updated_at", None) is not None
        ):
            age = utc_now() - ensure_utc(session.processing_updated_at)
            if age < timedelta(minutes=lease_minutes):
                logger.info(
                    f"event=lease_skip {kv(session_id=session_id, lease_minutes=lease_minutes, age=str(age))}"
                )
                return
        
        # Track attempts / heartbeat
        session.attempt_count = int(getattr(session, "attempt_count", 0) or 0) + 1
        if getattr(session, "processing_started_at", None) is None:
            session.processing_started_at = utc_now()
        session.processing_updated_at = utc_now()

        # Determine the next step and publish it before executing.
        step = _next_step(session)
        session.status = "processing" if step != "complete" else "complete"
        session.processing_step = step
        session.progress_pct = _step_progress(step)
        session.error_message = None
        session.last_error_step = None
        db.commit()

        if step == "complete":
            logger.info(f"Session {session_id} already has all outputs; marked complete")
            return

        transcript = session.transcript
        detected_language: Optional[str] = session.source_language
        translation = session.translation

        # Step 1: Transcribe (only if missing)
        if _next_step(session) == "transcribing":
            try:
                logger.info(f"event=step_start {kv(session_id=session_id, step='transcribing', attempt=session.attempt_count)}")
                t0 = time.perf_counter()
                session.processing_step = "transcribing"
                session.progress_pct = _step_progress("transcribing")
                session.processing_updated_at = utc_now()
                db.commit()
                local_audio_path, cleanup = await resolve_audio_to_local_path(session.audio_path)
                try:
                    transcript, detected_language = await openai_provider.transcribe(local_audio_path)
                finally:
                    cleanup()
                session.transcript = transcript
                session.source_language = detected_language
                session.processing_updated_at = utc_now()
                db.commit()
                logger.info(
                    f"event=step_ok {kv(session_id=session_id, step='transcribing', elapsed_s=f'{time.perf_counter()-t0:.2f}', lang=detected_language)}"
                )
            except Exception as e:
                session.last_error_step = "transcribing"
                session.processing_updated_at = utc_now()
                db.commit()
                raise Exception(f"Transcription failed: {str(e)}")

        # Step 2: Translate (only if missing)
        if transcript is None or len((transcript or "").strip()) == 0:
            raise Exception("Cannot translate without transcript")

        # Step 1.5: Ayah linking (Arabic-only; safe to skip if no match)
        if _next_step(session) == "ayah_linking":
            try:
                logger.info(f"event=step_start {kv(session_id=session_id, step='ayah_linking', attempt=session.attempt_count)}")
                t0 = time.perf_counter()
                session.processing_step = "ayah_linking"
                session.progress_pct = _step_progress("ayah_linking")
                session.processing_updated_at = utc_now()
                db.commit()

                result = match_ayah(transcript)

                if result.matched is not None:
                    session.matched_surah = result.matched.surah
                    session.matched_ayah = result.matched.ayah
                    session.matched_ayah_text_ar = result.matched.text_ar
                    session.matched_confidence_pct = result.matched.score_pct
                else:
                    session.matched_surah = None
                    session.matched_ayah = None
                    session.matched_ayah_text_ar = None
                    session.matched_confidence_pct = None

                session.matched_method = result.method
                session.matched_candidates_json = json.dumps(
                    [
                        {
                            "surah": c.surah,
                            "ayah": c.ayah,
                            "score_pct": c.score_pct,
                            "text_ar": c.text_ar,
                        }
                        for c in result.candidates
                    ]
                )
                session.processing_updated_at = utc_now()
                db.commit()

                logger.info(
                    f"event=step_ok {kv(session_id=session_id, step='ayah_linking', elapsed_s=f'{time.perf_counter()-t0:.2f}', matched=bool(result.matched))}"
                )
            except Exception as e:
                session.last_error_step = "ayah_linking"
                session.processing_updated_at = utc_now()
                db.commit()
                raise Exception(f"Ayah linking failed: {str(e)}")

        if _next_step(session) == "translating":
            try:
                logger.info(f"event=step_start {kv(session_id=session_id, step='translating', attempt=session.attempt_count)}")
                t0 = time.perf_counter()
                session.processing_step = "translating"
                session.progress_pct = _step_progress("translating")
                session.processing_updated_at = utc_now()
                db.commit()
                translation = await openai_provider.translate(
                    text=transcript,
                    target_language=session.target_language,
                    source_language=detected_language,
                )
                session.translation = translation
                session.processing_updated_at = utc_now()
                db.commit()
                logger.info(
                    f"event=step_ok {kv(session_id=session_id, step='translating', elapsed_s=f'{time.perf_counter()-t0:.2f}')}"
                )
            except Exception as e:
                session.last_error_step = "translating"
                session.processing_updated_at = utc_now()
                db.commit()
                raise Exception(f"Translation failed: {str(e)}")

        # Step 3: Summarize (only if missing)
        if translation is None or len((translation or "").strip()) == 0:
            raise Exception("Cannot summarize without translation")

        if _next_step(session) == "summarizing":
            try:
                logger.info(f"event=step_start {kv(session_id=session_id, step='summarizing', attempt=session.attempt_count)}")
                t0 = time.perf_counter()
                session.processing_step = "summarizing"
                session.progress_pct = _step_progress("summarizing")
                session.processing_updated_at = utc_now()
                db.commit()
                summary_bullets = await openai_provider.summarize(
                    transcript=transcript,
                    translation=translation,
                    target_language=session.target_language,
                )
                session.summary_bullets_json = json.dumps(summary_bullets)
                session.processing_updated_at = utc_now()
                db.commit()
                logger.info(
                    f"event=step_ok {kv(session_id=session_id, step='summarizing', elapsed_s=f'{time.perf_counter()-t0:.2f}', bullets=len(summary_bullets))}"
                )
            except Exception as e:
                session.last_error_step = "summarizing"
                session.processing_updated_at = utc_now()
                db.commit()
                raise Exception(f"Summarization failed: {str(e)}")

        # Finalize
        session.status = "complete"
        session.processing_step = "complete"
        session.progress_pct = 100
        session.processing_updated_at = utc_now()
        session.error_message = None
        session.last_error_step = None
        db.commit()
        logger.info(f"event=complete {kv(session_id=session_id)}")
        
    except Exception as e:
        logger.error(
            f"Processing failed for session {session_id}: {e}",
            exc_info=True
        )
        
        # Update session with error
        try:
            session = (
                db.query(SessionModel)
                .filter(
                    SessionModel.id == session_id,
                    SessionModel.client_id == client_id,
                )
                .first()
            )
            
            if session:
                session.status = "failed"
                # Store a user-friendly error message (avoid exposing internal details)
                error_msg = str(e)
                if len(error_msg) > 500:
                    error_msg = error_msg[:500] + "..."
                session.error_message = error_msg
                session.processing_updated_at = utc_now()
                db.commit()
                logger.info(f"Session {session_id} marked as failed")
        except Exception as db_error:
            logger.error(
                f"Failed to update error status for {session_id}: {db_error}",
                exc_info=True
            )
    
    finally:
        db.close()


def process_session_sync(session_id: str, client_id: str) -> None:
    """
    Synchronous wrapper for process_session.
    
    This is needed because FastAPI BackgroundTasks doesn't directly support
    async functions in all cases.
    
    Args:
        session_id: Session ID to process
        client_id: Client ID for validation
    """
    import asyncio
    
    # Create and run event loop for the async function
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        elif loop.is_running():
            # If loop is already running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # No event loop in current thread, create new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(process_session(session_id, client_id))
    finally:
        # Only close if we created a new loop
        if not loop.is_running():
            loop.close()

