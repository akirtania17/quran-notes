"""Local filesystem storage implementation."""
import os
import shutil
from pathlib import Path
from typing import BinaryIO

from app.core.config import settings
from app.core.logging import get_logger
from app.core.errors import UploadTooLargeError, UploadEmptyError
from app.services.storage.base import StorageProvider

logger = get_logger(__name__)


class LocalFileSystemStorage(StorageProvider):
    """Local filesystem storage provider."""
    
    def __init__(self, base_dir: str = None):
        """
        Initialize local filesystem storage.
        
        Args:
            base_dir: Base directory for uploads (defaults to settings.upload_dir)
        """
        self.base_dir = Path(base_dir or settings.upload_dir).absolute()
        self._ensure_base_dir()
    
    def _ensure_base_dir(self) -> None:
        """Ensure base upload directory exists."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Upload directory: {self.base_dir.absolute()}")
    
    def _get_session_dir(self, session_id: str) -> Path:
        """Get directory path for a session."""
        return self.base_dir / session_id
    
    async def save_upload(
        self,
        session_id: str,
        filename: str,
        file_content: BinaryIO,
    ) -> str:
        """
        Save uploaded file to local filesystem.
        
        Args:
            session_id: Session ID for organizing storage
            filename: Original filename
            file_content: File content as binary stream
            
        Returns:
            Relative path to the stored file
        """
        # Create session directory
        session_dir = self._get_session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = session_dir / filename
        
        try:
            with open(file_path, "wb") as f:
                # Read in chunks to handle large files
                total_bytes = 0
                max_bytes = int(getattr(settings, "max_upload_bytes", 0) or 0)
                while chunk := file_content.read(8192):
                    total_bytes += len(chunk)
                    if max_bytes and total_bytes > max_bytes:
                        raise UploadTooLargeError(
                            f"Audio file too large. Max is {settings.max_upload_mb} MB."
                        )
                    f.write(chunk)

            # Treat empty uploads as a validation error (usually recording failure on-device).
            if total_bytes == 0:
                raise UploadEmptyError("Uploaded audio file is empty. Please re-record and try again.")
            
            # Return path as stored (can be used to retrieve file later)
            # Store as relative path to the upload directory
            relative_path = f"{settings.upload_dir}/{session_id}/{filename}"
            # Normalize path separators for consistency
            relative_path = relative_path.replace("\\", "/").replace("./", "")
            logger.info(f"Saved upload: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"Failed to save upload: {e}")
            # Cleanup on failure
            if file_path.exists():
                file_path.unlink()
            raise
    
    def get_file_path(self, session_id: str, filename: str) -> str:
        """
        Get the full path to a stored file.
        
        Args:
            session_id: Session ID
            filename: Filename
            
        Returns:
            Absolute path to the file
        """
        file_path = self._get_session_dir(session_id) / filename
        return str(file_path.absolute())
    
    def delete_session_files(self, session_id: str) -> None:
        """
        Delete all files for a session.
        
        Args:
            session_id: Session ID
        """
        session_dir = self._get_session_dir(session_id)
        
        if session_dir.exists():
            try:
                shutil.rmtree(session_dir)
                logger.info(f"Deleted session files: {session_id}")
            except Exception as e:
                logger.error(f"Failed to delete session files: {e}")


# Global storage instance
storage = LocalFileSystemStorage()

