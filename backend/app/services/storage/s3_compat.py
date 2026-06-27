"""S3-compatible storage implementation (Cloudflare R2, S3, etc.)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO, Optional, Tuple

import boto3
from botocore.config import Config as BotoConfig

from app.core.config import settings
from app.core.logging import get_logger
from app.services.storage.base import StorageProvider

logger = get_logger(__name__)


def _normalize_prefix(prefix: str) -> str:
    p = (prefix or "").strip().strip("/")
    return f"{p}/" if p else ""


def _make_object_key(session_id: str, filename: str) -> str:
    base = _normalize_prefix(getattr(settings, "s3_prefix", "") or "")
    return f"{base}sessions/{session_id}/{filename}"


def _parse_s3_ref(ref: str) -> Tuple[str, str]:
    """
    Parse a storage ref like s3://bucket/key (or r2://bucket/key).
    Returns (bucket, key).
    """
    r = (ref or "").strip()
    if r.startswith("r2://"):
        r = "s3://" + r[len("r2://") :]
    if not r.startswith("s3://"):
        raise ValueError("Not an s3 ref")
    rest = r[len("s3://") :]
    if "/" not in rest:
        raise ValueError("Invalid s3 ref (missing key)")
    bucket, key = rest.split("/", 1)
    if not bucket or not key:
        raise ValueError("Invalid s3 ref")
    return bucket, key


@dataclass(frozen=True)
class S3Location:
    bucket: str
    key: str

    @property
    def ref(self) -> str:
        return f"s3://{self.bucket}/{self.key}"


class S3CompatStorage(StorageProvider):
    """
    Storage provider for S3-compatible APIs (Cloudflare R2 recommended).
    """

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        bucket: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region: Optional[str] = None,
    ):
        self.endpoint_url = (endpoint_url or settings.s3_endpoint_url or "").strip()
        self.bucket = (bucket or settings.s3_bucket or "").strip()
        self.access_key_id = (access_key_id or settings.s3_access_key_id or "").strip()
        self.secret_access_key = (secret_access_key or settings.s3_secret_access_key or "").strip()
        self.region = (region or settings.s3_region or "auto").strip() or "auto"

        if not self.endpoint_url:
            raise ValueError("S3_ENDPOINT_URL is required for S3CompatStorage")
        if not self.bucket:
            raise ValueError("S3_BUCKET is required for S3CompatStorage")
        if not self.access_key_id:
            raise ValueError("S3_ACCESS_KEY_ID is required for S3CompatStorage")
        if not self.secret_access_key:
            raise ValueError("S3_SECRET_ACCESS_KEY is required for S3CompatStorage")

        # Use signature v4; R2 is S3-compatible.
        boto_cfg = BotoConfig(signature_version="s3v4")
        self._client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region,
            config=boto_cfg,
        )

        logger.info(
            "S3CompatStorage configured",
            extra={
                "endpoint_url": self.endpoint_url,
                "bucket": self.bucket,
                "region": self.region,
                "prefix": _normalize_prefix(getattr(settings, "s3_prefix", "") or ""),
            },
        )

    async def save_upload(self, session_id: str, filename: str, file_content: BinaryIO) -> str:
        """
        Upload the stream to S3-compatible storage and return an s3:// ref.
        """
        from starlette.concurrency import run_in_threadpool

        key = _make_object_key(session_id, filename)
        location = S3Location(bucket=self.bucket, key=key)

        def _upload() -> None:
            # Private by default (no ACL). ContentType is optional; we skip it for simplicity.
            self._client.upload_fileobj(file_content, self.bucket, key)

        await run_in_threadpool(_upload)
        logger.info("Saved upload to S3-compatible storage", extra={"ref": location.ref})
        return location.ref

    def get_file_path(self, session_id: str, filename: str) -> str:
        """
        Return an s3:// ref for the stored object.

        NOTE: In cloud mode this is not a local path. Processing should use the resolver
        to download to a temp file before opening.
        """
        key = _make_object_key(session_id, filename)
        return f"s3://{self.bucket}/{key}"

    def delete_session_files(self, session_id: str) -> None:
        """
        Delete all objects for a session under the configured prefix.
        """
        prefix = _make_object_key(session_id, "")  # ends with trailing slash

        def _delete() -> int:
            paginator = self._client.get_paginator("list_objects_v2")
            to_delete = []
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get("Contents", []) or []:
                    key = obj.get("Key")
                    if key:
                        to_delete.append({"Key": key})

            # S3 delete_objects limits 1000 keys per call
            for i in range(0, len(to_delete), 1000):
                chunk = to_delete[i : i + 1000]
                self._client.delete_objects(
                    Bucket=self.bucket,
                    Delete={"Objects": chunk, "Quiet": True},
                )

            return len(to_delete)

        # Interface is sync; run synchronously.
        count = _delete()

        logger.info(
            "Deleted session files from S3-compatible storage",
            extra={"session_id": session_id, "count": count, "prefix": prefix},
        )


def parse_s3_ref(ref: str) -> S3Location:
    bucket, key = _parse_s3_ref(ref)
    return S3Location(bucket=bucket, key=key)


