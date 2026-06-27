"""Base storage interface."""
from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageProvider(ABC):
    """Abstract base class for storage providers."""
    
    @abstractmethod
    async def save_upload(
        self,
        session_id: str,
        filename: str,
        file_content: BinaryIO,
    ) -> str:
        """
        Save uploaded file to storage.
        
        Args:
            session_id: Session ID for organizing storage
            filename: Original filename
            file_content: File content as binary stream
            
        Returns:
            Path or URL to the stored file
        """
        pass
    
    @abstractmethod
    def get_file_path(self, session_id: str, filename: str) -> str:
        """
        Get the full path to a stored file.
        
        Args:
            session_id: Session ID
            filename: Filename
            
        Returns:
            Full path to the file
        """
        pass
    
    @abstractmethod
    def delete_session_files(self, session_id: str) -> None:
        """
        Delete all files for a session.
        
        Args:
            session_id: Session ID
        """
        pass

