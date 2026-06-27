"""Storage services.

Exports a single `storage` instance selected by settings.
"""

from app.core.config import settings

storage_backend = (getattr(settings, "storage_backend", "local") or "local").strip().lower()

if storage_backend in ("local", "disk", "filesystem", "fs"):
    # Reuse the module-level singleton so tests/fixtures that patch it keep working.
    from app.services.storage.local_fs import storage as local_storage

    storage = local_storage
elif storage_backend in ("r2", "s3"):
    from app.services.storage.s3_compat import S3CompatStorage

    storage = S3CompatStorage()
else:
    raise RuntimeError(f"Unsupported STORAGE_BACKEND: {storage_backend}")

__all__ = ["storage"]

