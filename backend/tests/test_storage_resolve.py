import asyncio
from pathlib import Path

import pytest

from app.services.storage.resolve import resolve_audio_to_local_path


def test_resolve_local_path_returns_absolute(tmp_path: Path):
    p = tmp_path / "audio.m4a"
    p.write_bytes(b"test")

    local, cleanup = asyncio.run(resolve_audio_to_local_path(str(p)))
    try:
        assert Path(local).is_absolute()
        assert Path(local).exists()
    finally:
        cleanup()


def test_resolve_local_relative_path_resolves(tmp_path: Path, monkeypatch):
    # Make cwd deterministic
    monkeypatch.chdir(tmp_path)
    rel = Path("data/uploads/sess_x/audio.m4a")
    rel.parent.mkdir(parents=True, exist_ok=True)
    rel.write_bytes(b"test")

    local, cleanup = asyncio.run(resolve_audio_to_local_path(str(rel)))
    try:
        assert Path(local).is_absolute()
        assert Path(local) == (tmp_path / rel).resolve()
        assert Path(local).exists()
    finally:
        cleanup()


