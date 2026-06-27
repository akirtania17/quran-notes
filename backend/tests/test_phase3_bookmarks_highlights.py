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
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Ensure models are imported/registered
    from app.models.note import Note  # noqa: F401
    from app.models.highlight import Highlight  # noqa: F401

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Patch SessionLocal in modules that instantiate DB sessions directly
    import app.db.session as db_session_module
    import app.services.processing.pipeline as pipeline_module
    import app.services.processing.sweeper as sweeper_module

    monkeypatch.setattr(db_session_module, "SessionLocal", TestingSessionLocal, raising=True)
    monkeypatch.setattr(pipeline_module, "SessionLocal", TestingSessionLocal, raising=True)
    monkeypatch.setattr(sweeper_module, "SessionLocal", TestingSessionLocal, raising=True)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Disable infinite-loop sweeper for tests (also guarded in app startup)
    monkeypatch.setattr(settings, "sweeper_enabled", False, raising=False)

    yield TestingSessionLocal

    app.dependency_overrides.clear()


def test_bookmark_patch_updates_session(test_db):
    db = test_db()
    try:
        s = SessionModel(
            id="sess_test_bookmark",
            client_id="test-client",
            title="Bookmark",
            created_at=utc_now(),
            duration_seconds=10,
            audio_path="ignored.m4a",
            status="uploaded",
            target_language="en",
            bookmarked=False,
        )
        db.add(s)
        db.commit()
    finally:
        db.close()

    client = TestClient(app)
    resp = client.patch(
        "/v1/sessions/sess_test_bookmark",
        json={"bookmarked": True},
        headers={"X-Client-Id": "test-client"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "sess_test_bookmark"
    assert data["bookmarked"] is True

    db = test_db()
    try:
        s2 = db.query(SessionModel).filter(SessionModel.id == "sess_test_bookmark").first()
        assert s2 is not None
        assert s2.bookmarked is True
    finally:
        db.close()


def test_highlights_create_list_delete(test_db):
    db = test_db()
    try:
        s = SessionModel(
            id="sess_test_highlights",
            client_id="test-client",
            title="Highlights",
            created_at=utc_now(),
            duration_seconds=10,
            audio_path="ignored.m4a",
            status="uploaded",
            target_language="en",
        )
        db.add(s)
        db.commit()
    finally:
        db.close()

    client = TestClient(app)

    create = client.post(
        "/v1/sessions/sess_test_highlights/highlights",
        json={"text": "bismillah"},
        headers={"X-Client-Id": "test-client"},
    )
    assert create.status_code == 201
    created = create.json()
    assert created["session_id"] == "sess_test_highlights"
    assert created["text"] == "bismillah"
    assert "id" in created

    hl_id = created["id"]

    listed = client.get(
        "/v1/sessions/sess_test_highlights/highlights",
        headers={"X-Client-Id": "test-client"},
    )
    assert listed.status_code == 200
    items = listed.json()
    assert isinstance(items, list)
    assert any(x["id"] == hl_id for x in items)

    deleted = client.delete(
        f"/v1/sessions/sess_test_highlights/highlights/{hl_id}",
        headers={"X-Client-Id": "test-client"},
    )
    assert deleted.status_code == 200
    assert deleted.json().get("ok") is True

    listed2 = client.get(
        "/v1/sessions/sess_test_highlights/highlights",
        headers={"X-Client-Id": "test-client"},
    )
    assert listed2.status_code == 200
    assert all(x["id"] != hl_id for x in listed2.json())


