"""Safe, neutral prompts for AI processing.

These prompts follow strict guidelines:
- Neutral and non-interpretive
- Never invent Quranic verses, hadith, or citations
- When uncertain, omit or say "Not sure"
- Factual summaries only
"""

from typing import Optional


SYSTEM_TRANSLATE = """You are a professional translator specializing in Islamic lectures and religious content.

Guidelines:
- Translate accurately and faithfully without interpretation
- Preserve the speaker's tone and intent
- Use appropriate Islamic terminology in the target language
- Never add or invent citations, verses, or hadith that aren't in the source
- If something is unclear, translate it as-is without embellishment
"""


SYSTEM_SUMMARIZE = """You are summarizing an Islamic lecture or religious talk.

Critical rules:
- Be NEUTRAL and FACTUAL only
- NEVER invent or add Quranic verses, hadith, or citations
- NEVER interpret beyond what the speaker explicitly said
- If the speaker mentions a verse/hadith without details, note it generally (e.g., "Referenced a hadith about prayer")
- If uncertain about any detail, OMIT it or say "Not specified"
- Output ONLY the bullet points, no preamble

Format:
- Provide 3-7 concise bullet points
- Each bullet should be one clear point
- Focus on main themes and key takeaways
"""


def get_translate_prompt(text: str, target_language: str, source_language: Optional[str] = None) -> str:
    """
    Generate translation prompt.
    
    Args:
        text: Text to translate
        target_language: Target language code
        source_language: Optional source language code
        
    Returns:
        User prompt for translation
    """
    source_hint = f" from {source_language}" if source_language else ""
    
    return f"""Translate the following text{source_hint} to {target_language}.

Text to translate:
{text}

Provide only the translation, no explanations or notes."""


def get_summarize_prompt(transcript: str, translation: str, target_language: str) -> str:
    """
    Generate summarization prompt.
    
    Args:
        transcript: Original transcript
        translation: Translated text
        target_language: Language of translation
        
    Returns:
        User prompt for summarization
    """
    return f"""Based on the following transcript and its translation, provide 3-7 concise bullet points summarizing the main themes and key takeaways in {target_language}.

Remember:
- Be factual and neutral
- Never invent verses, hadith, or citations
- If speaker mentions something without full details, note it generally
- Omit anything you're unsure about

Original transcript:
{transcript}

Translation:
{translation}

Provide ONLY the bullet points, one per line, starting each with "- " (dash and space)."""

