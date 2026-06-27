"""Languages router."""
from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(prefix="/v1", tags=["languages"])


class LanguageItem(BaseModel):
    """Language item."""
    code: str
    label: str


class LanguagesResponse(BaseModel):
    """Languages response."""
    items: list[LanguageItem]


# Supported languages as per plan
SUPPORTED_LANGUAGES = [
    {"code": "en", "label": "English"},
    {"code": "ar", "label": "Arabic"},
    {"code": "fr", "label": "French"},
    {"code": "ur", "label": "Urdu"},
    {"code": "tr", "label": "Turkish"},
    {"code": "id", "label": "Indonesian"},
]


@router.get("/languages", response_model=LanguagesResponse)
async def get_languages():
    """
    Get list of supported languages.
    
    Returns:
        List of language codes and labels
    """
    return LanguagesResponse(items=SUPPORTED_LANGUAGES)

