"""Arabic text normalization helpers for Ayah matching."""

from __future__ import annotations

import re

# Arabic diacritics / tashkeel
_AR_DIACRITICS_RE = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)

_AR_PUNCT_RE = re.compile(r"[^\u0600-\u06FF\s]")
_WHITESPACE_RE = re.compile(r"\s+")


def contains_arabic(text: str) -> bool:
    if not text:
        return False
    return bool(re.search(r"[\u0600-\u06FF]", text))


def normalize_arabic(text: str) -> str:
    """
    Normalize Arabic text for fuzzy matching.

    - Strip diacritics/tashkeel
    - Remove tatweel
    - Normalize common letter variants (أ/إ/آ → ا, ى → ي, ؤ → و, ئ → ي)
    - Remove non-Arabic punctuation/symbols
    - Collapse whitespace
    """
    if not text:
        return ""

    t = text
    t = t.replace("\u0640", "")  # tatweel
    t = _AR_DIACRITICS_RE.sub("", t)

    # Normalize letter variants
    t = (
        t.replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ٱ", "ا")
        .replace("ى", "ي")
        .replace("ؤ", "و")
        .replace("ئ", "ي")
    )

    # Optional normalizations that sometimes help; keep conservative for MVP.
    # t = t.replace("ة", "ه")

    t = _AR_PUNCT_RE.sub(" ", t)
    t = _WHITESPACE_RE.sub(" ", t).strip()
    return t


def arabic_tokens(text: str) -> list[str]:
    t = normalize_arabic(text)
    if not t:
        return []
    return [tok for tok in t.split(" ") if tok]


def char_ngrams(text: str, n: int = 3) -> set[str]:
    t = normalize_arabic(text)
    if not t:
        return set()
    t = t.replace(" ", "")
    if len(t) < n:
        return {t}
    return {t[i : i + n] for i in range(0, len(t) - n + 1)}


