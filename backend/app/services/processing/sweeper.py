"""In-process sweeper to recover stuck sessions.

This runs inside the FastAPI process (no external worker/queue) and periodically:
- finds sessions stuck in uploaded/processing beyond a threshold
- resets and re-enqueues processing, or marks failed if too old
"""

import asyncio
from datetime import timedelta

from app.core.config import settings
from app.core.logging import get_logger, kv
from app.db.session import SessionLocal
from app.models.session import Session as SessionModel
from app.services.processing.pipeline import process_session
from app.utils.time import ensure_utc, utc_now

logger = get_logger(__name__)


async def sweep_once() -> int:
    """
    Sweep once and schedule processing for recovered sessions.

    Returns the count of sessions recovered (reset/enqueued or failed).
    """
    threshold_minutes = int(getattr(settings, "stuck_threshold_minutes", 45) or 45)
    max_age_minutes = int(getattr(settings, "stuck_max_age_minutes", 120) or 120)

    now = utc_now()
    threshold = timedelta(minutes=threshold_minutes)
    max_age = timedelta(minutes=max_age_minutes)

    db = SessionLocal()
    try:
        candidates = (
            db.query(SessionModel)
            .filter(SessionModel.status.in_(("uploaded", "processing")))
            .order_by(SessionModel.created_at.asc())
            .all()
        )

        recovered = 0
        to_enqueue: list[tuple[str, str]] = []
        for s in candidates:
            last = s.processing_updated_at or s.created_at
            if last is None:
                last = s.created_at
            if last is None:
                continue

            idle = now - ensure_utc(last)
            total_age = now - ensure_utc(s.created_at) if s.created_at else idle

            if idle < threshold:
                continue

            if total_age >= max_age:
                s.status = "failed"
                s.error_message = "Processing timed out - tap retry."
                s.processing_updated_at = now
                recovered += 1
                logger.warning(
                    f"event=sweeper_fail {kv(session_id=s.id, idle=str(idle), age=str(total_age))}"
                )
                continue

            # Reset to uploaded/queued and re-enqueue. Keep partial outputs; pipeline will resume.
            s.status = "uploaded"
            s.processing_step = "queued"
            s.progress_pct = 0
            s.error_message = None
            s.last_error_step = None
            s.processing_updated_at = now
            recovered += 1
            logger.info(
                f"event=sweeper_reset {kv(session_id=s.id, idle=str(idle), age=str(total_age))}"
            )
            to_enqueue.append((s.id, s.client_id))

        if recovered:
            db.commit()
            # Only enqueue after commit so the processor sees the updated state.
            for session_id, client_id in to_enqueue:
                asyncio.create_task(process_session(session_id, client_id))
        return recovered
    finally:
        db.close()


async def sweeper_loop() -> None:
    """Run the sweeper forever until cancelled."""
    interval_seconds = int(getattr(settings, "sweeper_interval_seconds", 300) or 300)
    logger.info(
        "Sweeper started "
        f"(enabled={getattr(settings, 'sweeper_enabled', True)} "
        f"interval_s={interval_seconds} "
        f"stuck_threshold_min={getattr(settings, 'stuck_threshold_minutes', 45)} "
        f"stuck_max_age_min={getattr(settings, 'stuck_max_age_minutes', 120)})"
    )
    try:
        while True:
            try:
                recovered = await sweep_once()
                if recovered:
                    logger.info(f"sweeper_recovered={recovered}")
            except Exception as e:
                logger.error(f"Sweeper iteration failed: {e}", exc_info=True)
            await asyncio.sleep(max(5, interval_seconds))
    except asyncio.CancelledError:
        logger.info("Sweeper cancelled; exiting")
        raise


