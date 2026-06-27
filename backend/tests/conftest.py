from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.base import Base


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


