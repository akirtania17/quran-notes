import asyncio
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.base import Base
from app.models.session import Session as SessionModel
from app.utils.time import utc_now


@pytest.fixture()
def test_db(monkeypatch, tmp_path: Path):
    """
    Provide an isolated in-memory DB and patch SessionLocal in modules that use it.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Ensure models are imported/registered
    from app.models.note import Note  # noqa: F401

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Patch SessionLocal in modules that instantiate DB sessions directly
    import app.db.session as db_session_module
    import app.services.processing.pipeline as pipeline_module
    import app.services.processing.sweeper as sweeper_module

    monkeypatch.setattr(db_session_module, "SessionLocal", TestingSessionLocal, raising=True)
    monkeypatch.setattr(pipeline_module, "SessionLocal", TestingSessionLocal, raising=True)
    monkeypatch.setattr(sweeper_module, "SessionLocal", TestingSessionLocal, raising=True)

    # Override FastAPI dependency
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Isolate upload storage path
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"), raising=False)
    from app.services.storage.local_fs import storage

    storage.base_dir = Path(settings.upload_dir).absolute()
    storage.base_dir.mkdir(parents=True, exist_ok=True)

    # Disable infinite-loop sweeper for tests (it is also guarded in app startup)
    monkeypatch.setattr(settings, "sweeper_enabled", False, raising=False)

    yield TestingSessionLocal

    app.dependency_overrides.clear()


def test_upload_too_large_returns_413(test_db, monkeypatch):
    # Make limit tiny for test
    monkeypatch.setattr(settings, "max_upload_mb", 1, raising=False)

    client = TestClient(app)
    audio_bytes = b"a" * (2 * 1024 * 1024)  # 2MB

    resp = client.post(
        "/v1/sessions",
        data={"title": "Test", "target_language": "en", "duration_seconds": "10"},
        files={"audio": ("audio.m4a", audio_bytes, "audio/mp4")},
        headers={"X-Client-Id": "test-client"},
    )
    assert resp.status_code == 413
    data = resp.json()
    # Either FastAPI's detail or our compatibility key
    assert "detail" in data or "error" in data


def test_pipeline_resume_skips_transcribe(test_db, monkeypatch):
    # Ensure pipeline doesn't fail fast on missing key
    monkeypatch.setattr(settings, "openai_api_key", "test-key", raising=False)

    import app.services.processing.pipeline as pipeline
    from app.services.ai.openai_provider import openai_provider

    called = {"transcribe": 0}

    async def transcribe_fail(*args, **kwargs):
        called["transcribe"] += 1
        raise AssertionError("transcribe should not be called when transcript exists")

    async def translate_ok(*args, **kwargs):
        return "translated"

    async def summarize_ok(*args, **kwargs):
        return ["a", "b", "c"]

    monkeypatch.setattr(openai_provider, "transcribe", transcribe_fail, raising=True)
    monkeypatch.setattr(openai_provider, "translate", translate_ok, raising=True)
    monkeypatch.setattr(openai_provider, "summarize", summarize_ok, raising=True)

    db = test_db()
    try:
        s = SessionModel(
            id="sess_test_resume",
            client_id="test-client",
            title="Resume",
            created_at=utc_now(),
            duration_seconds=10,
            audio_path="ignored.m4a",
            status="uploaded",
            target_language="en",
            transcript="hello",
            source_language="ar",
            translation=None,
            summary_bullets_json=None,
        )
        db.add(s)
        db.commit()
    finally:
        db.close()

    asyncio.run(pipeline.process_session("sess_test_resume", "test-client"))

    db = test_db()
    try:
        s2 = db.query(SessionModel).filter(SessionModel.id == "sess_test_resume").first()
        assert s2 is not None
        assert s2.status == "complete"
        assert s2.transcript == "hello"
        assert s2.translation == "translated"
        assert s2.summary_bullets_json is not None
        assert called["transcribe"] == 0
    finally:
        db.close()


def test_pipeline_lease_skips_when_fresh(test_db, monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "test-key", raising=False)
    monkeypatch.setattr(settings, "processing_lease_minutes", 10, raising=False)

    import app.services.processing.pipeline as pipeline
    from app.services.ai.openai_provider import openai_provider

    async def should_not_run(*args, **kwargs):
        raise AssertionError("OpenAI calls should not happen due to lease skip")

    monkeypatch.setattr(openai_provider, "transcribe", should_not_run, raising=True)
    monkeypatch.setattr(openai_provider, "translate", should_not_run, raising=True)
    monkeypatch.setattr(openai_provider, "summarize", should_not_run, raising=True)

    db = test_db()
    try:
        s = SessionModel(
            id="sess_test_lease",
            client_id="test-client",
            title="Lease",
            created_at=utc_now(),
            duration_seconds=10,
            audio_path="ignored.m4a",
            status="processing",
            processing_step="transcribing",
            progress_pct=15,
            processing_started_at=utc_now(),
            processing_updated_at=utc_now(),
            attempt_count=0,
            target_language="en",
        )
        db.add(s)
        db.commit()
    finally:
        db.close()

    asyncio.run(pipeline.process_session("sess_test_lease", "test-client"))

    db = test_db()
    try:
        s2 = db.query(SessionModel).filter(SessionModel.id == "sess_test_lease").first()
        assert s2 is not None
        assert s2.attempt_count == 0  # lease skip occurs before increment
        assert s2.status == "processing"
    finally:
        db.close()


def test_sweeper_resets_stale_session_and_enqueues(test_db, monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "test-key", raising=False)
    monkeypatch.setattr(settings, "stuck_threshold_minutes", 30, raising=False)
    monkeypatch.setattr(settings, "stuck_max_age_minutes", 120, raising=False)

    import app.services.processing.sweeper as sweeper

    scheduled: list[tuple[str, str]] = []
    created_coros = []

    async def fake_process_session(session_id: str, client_id: str):
        scheduled.append((session_id, client_id))

    monkeypatch.setattr(sweeper, "process_session", fake_process_session, raising=True)
    # Intercept create_task so we can deterministically assert enqueuing without relying
    # on the event loop continuing after asyncio.run() returns.
    def fake_create_task(coro):
        created_coros.append(coro)
        return coro

    monkeypatch.setattr(sweeper.asyncio, "create_task", fake_create_task, raising=True)

    db = test_db()
    try:
        s = SessionModel(
            id="sess_test_sweeper",
            client_id="test-client",
            title="Sweeper",
            created_at=utc_now() - timedelta(minutes=90),
            duration_seconds=10,
            audio_path="ignored.m4a",
            status="processing",
            processing_step="transcribing",
            progress_pct=15,
            processing_started_at=utc_now() - timedelta(minutes=90),
            processing_updated_at=utc_now() - timedelta(minutes=60),
            attempt_count=1,
            target_language="en",
        )
        db.add(s)
        db.commit()
    finally:
        db.close()

    recovered = asyncio.run(sweeper.sweep_once())
    assert recovered == 1

    assert len(created_coros) == 1
    asyncio.run(created_coros[0])
    assert ("sess_test_sweeper", "test-client") in scheduled

    db = test_db()
    try:
        s2 = db.query(SessionModel).filter(SessionModel.id == "sess_test_sweeper").first()
        assert s2 is not None
        assert s2.status == "uploaded"
        assert s2.processing_step == "queued"
        assert s2.progress_pct == 0
    finally:
        db.close()


