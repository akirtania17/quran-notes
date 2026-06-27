"""OpenAI implementation of AI provider."""
import os
from typing import Optional, Tuple

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import get_logger, kv
from app.services.ai.base import AIProvider
from app.services.ai.prompts import (
    SYSTEM_TRANSLATE,
    SYSTEM_SUMMARIZE,
    get_translate_prompt,
    get_summarize_prompt,
)

logger = get_logger(__name__)

TRANSCRIBE_TIMEOUT_S = 900.0
TRANSLATE_TIMEOUT_S = 180.0
SUMMARIZE_TIMEOUT_S = 180.0
OPENAI_MAX_RETRIES = 2


class OpenAIProvider(AIProvider):
    """OpenAI-based AI provider for transcription, translation, and summarization."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key (defaults to settings)
        """
        self.api_key = api_key or settings.openai_api_key
        # Keep a conservative default timeout; override per-call for long operations.
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=30.0,
            max_retries=OPENAI_MAX_RETRIES,
        )
        
        # Model configuration
        self.transcribe_model = settings.openai_model_transcribe
        self.translate_model = settings.openai_model_translate
        self.summarize_model = settings.openai_model_summarize
    
    async def transcribe(self, audio_path: str) -> Tuple[str, Optional[str]]:
        """
        Transcribe audio using OpenAI Whisper.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Tuple of (transcript, detected_language_code)
        """
        logger.info(f"event=openai_transcribe_start {kv(audio_path=audio_path)}")
        
        try:
            with open(audio_path, "rb") as audio_file:
                response = await self.client.audio.transcriptions.create(
                    model=self.transcribe_model,
                    file=audio_file,
                    response_format="verbose_json",  # Get language detection
                    timeout=TRANSCRIBE_TIMEOUT_S,
                )
            
            transcript = response.text
            detected_language = getattr(response, "language", None)
            
            logger.info(
                f"event=openai_transcribe_ok {kv(chars=len(transcript), language=detected_language)}"
            )
            
            return transcript, detected_language
            
        except Exception as e:
            logger.error(f"event=openai_transcribe_error {kv(error=str(e))}", exc_info=True)
            raise Exception(str(e))
    
    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> str:
        """
        Translate text using GPT model.
        
        Args:
            text: Source text
            target_language: Target language code
            source_language: Optional source language hint
            
        Returns:
            Translated text
        """
        logger.info(
            f"event=openai_translate_start {kv(chars=len(text), source_language=source_language or 'auto', target_language=target_language)}"
        )
        
        try:
            user_prompt = get_translate_prompt(text, target_language, source_language)
            
            response = await self.client.chat.completions.create(
                model=self.translate_model,
                messages=[
                    {"role": "system", "content": SYSTEM_TRANSLATE},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,  # Low temperature for consistent translation
                timeout=TRANSLATE_TIMEOUT_S,
            )
            
            translation = response.choices[0].message.content.strip()
            
            logger.info(f"event=openai_translate_ok {kv(chars=len(translation))}")
            
            return translation
            
        except Exception as e:
            logger.error(f"event=openai_translate_error {kv(error=str(e))}", exc_info=True)
            raise Exception(str(e))
    
    async def summarize(
        self,
        transcript: str,
        translation: str,
        target_language: str
    ) -> list[str]:
        """
        Generate summary bullets using GPT model.
        
        Args:
            transcript: Original transcript
            translation: Translated text
            target_language: Language for summary
            
        Returns:
            List of summary bullet points
        """
        logger.info(f"event=openai_summarize_start {kv(target_language=target_language)}")
        
        try:
            user_prompt = get_summarize_prompt(transcript, translation, target_language)
            
            response = await self.client.chat.completions.create(
                model=self.summarize_model,
                messages=[
                    {"role": "system", "content": SYSTEM_SUMMARIZE},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.5,  # Slightly higher for natural summaries
                timeout=SUMMARIZE_TIMEOUT_S,
            )
            
            summary_text = response.choices[0].message.content.strip()
            
            # Parse bullets from response
            # Expected format: "- Bullet 1\n- Bullet 2\n..."
            bullets = []
            for line in summary_text.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    bullets.append(line[2:])  # Remove "- " prefix
                elif line.startswith("* "):
                    bullets.append(line[2:])  # Support "* " format too
                elif line and not line.startswith("#"):  # Skip empty and headers
                    # If line doesn't have bullet, but has content, include it
                    bullets.append(line)
            
            # Ensure we have 3-7 bullets
            if len(bullets) < 3:
                logger.warning(f"Too few bullets generated: {len(bullets)}")
                # Pad with a note if necessary
                while len(bullets) < 3:
                    bullets.append("(No additional points)")
            elif len(bullets) > 7:
                logger.warning(f"Too many bullets generated: {len(bullets)}, truncating")
                bullets = bullets[:7]
            
            logger.info(f"event=openai_summarize_ok {kv(bullets=len(bullets))}")
            
            return bullets
            
        except Exception as e:
            logger.error(f"event=openai_summarize_error {kv(error=str(e))}", exc_info=True)
            raise Exception(str(e))


# Global provider instance
openai_provider = OpenAIProvider()

