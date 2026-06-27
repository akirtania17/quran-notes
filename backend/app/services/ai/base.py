"""Base AI provider interface."""
from abc import ABC, abstractmethod
from typing import Optional, Tuple


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def transcribe(self, audio_path: str) -> Tuple[str, Optional[str]]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Tuple of (transcript, detected_language_code)
            detected_language_code may be None if not detected
        """
        pass
    
    @abstractmethod
    async def translate(self, text: str, target_language: str, source_language: Optional[str] = None) -> str:
        """
        Translate text to target language.
        
        Args:
            text: Source text to translate
            target_language: Target language code
            source_language: Optional source language hint
            
        Returns:
            Translated text
        """
        pass
    
    @abstractmethod
    async def summarize(self, transcript: str, translation: str, target_language: str) -> list[str]:
        """
        Generate summary bullets from transcript and translation.
        
        Args:
            transcript: Original transcript
            translation: Translated text
            target_language: Language of translation
            
        Returns:
            List of summary bullet points (3-7 items)
        """
        pass

