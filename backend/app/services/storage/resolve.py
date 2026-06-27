"""Helpers to resolve stored audio references into local file paths for processing."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Callable, Tuple

import boto3
from botocore.config import Config as BotoConfig
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.logging import get_logger
from app.services.storage.s3_compat import parse_s3_ref

logger = get_logger(__name__)


def _ensure_tmp_dir() -> Path:
    tmp_dir = Path(getattr(settings, "tmp_dir", "./data/tmp") or "./data/tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir


def _s3_client():
    endpoint_url = (settings.s3_endpoint_url or "").strip()
    access_key_id = (settings.s3_access_key_id or "").strip()
    secret_access_key = (settings.s3_secret_access_key or "").strip()
    region = (settings.s3_region or "auto").strip() or "auto"

    if not endpoint_url or not access_key_id or not secret_access_key:
        raise RuntimeError(
            "S3 storage not configured. Set S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, and S3_SECRET_ACCESS_KEY."
        )

    boto_cfg = BotoConfig(signature_version="s3v4")
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region,
        config=boto_cfg,
    )


async def resolve_audio_to_local_path(audio_ref: str) -> Tuple[str, Callable[[], None]]:
    """
    Resolve an audio reference into a local file path suitable for `open()` during processing.

    Returns:
      (local_path, cleanup_fn)

    - local storage: audio_ref is treated as a local path (relative paths are resolved against cwd).
    - r2/s3 storage: audio_ref is expected to be an s3://... or r2://... ref and is downloaded
      into TMP_DIR.
    """
    ref = (audio_ref or "").strip()
    if not ref:
        raise ValueError("audio_ref is empty")

    # Local path case (default)
    if not (ref.startswith("s3://") or ref.startswith("r2://")):
        p = Path(ref)
        # Resolve relative to current working directory (backend folder when running via scripts).
        return str(p.resolve()), (lambda: None)

    # Remote case: download to TMP_DIR
    loc = parse_s3_ref(ref)
    tmp_dir = _ensure_tmp_dir()
    ext = Path(loc.key).suffix or ".bin"
    tmp_path = tmp_dir / f"audio_{uuid.uuid4().hex}{ext}"

    client = _s3_client()

    def _download() -> None:
        client.download_file(loc.bucket, loc.key, str(tmp_path))

    await run_in_threadpool(_download)
    logger.info("Downloaded audio ref to temp file", extra={"ref": ref, "tmp_path": str(tmp_path)})

    def _cleanup() -> None:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            # Best-effort cleanup; ignore.
            pass

    return str(tmp_path), _cleanup


