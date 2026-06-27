"""Ayah matching (Arabic-only MVP).

This matcher is designed for:
- Fast candidate retrieval using character n-gram inverted index
- Robust reranking using multiple fuzzy similarity signals
- Returning confidence + top alternatives for trust-building UX
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any, Optional

from app.services.ayah_linking.normalize import arabic_tokens, char_ngrams, contains_arabic, normalize_arabic


@dataclass(frozen=True)
class AyahRef:
    surah: int
    ayah: int


@dataclass(frozen=True)
class AyahCandidate:
    surah: int
    ayah: int
    score_pct: int
    text_ar: str


@dataclass(frozen=True)
class AyahMatchResult:
    matched: Optional[AyahCandidate]
    candidates: list[AyahCandidate]
    method: str


def _data_path() -> str:
    # backend/app/services/ayah_linking/matcher.py -> backend/app/data/quran_arabic.json
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "..", "data", "quran_arabic.json"))


@lru_cache(maxsize=1)
def load_quran_arabic() -> list[list[str]]:
    """
    Returns a 1-based list of surahs, each a 1-based list of ayah texts.
    Index 0 is a dummy placeholder for easier indexing.
    """
    path = _data_path()
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Quran Arabic dataset not found at {path}. "
            f"Run backend/scripts/build_quran_arabic.py to generate it."
        )

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    surahs = payload.get("surahs")
    if not isinstance(surahs, list) or len(surahs) < 2:
        raise ValueError("Invalid quran_arabic.json: expected payload.surahs list")

    return surahs


@lru_cache(maxsize=1)
def _build_index() -> dict[str, Any]:
    """
    Builds an in-memory inverted index for fast candidate retrieval.

    Returns dict with:
    - verses: list of {ref, text_ar, norm, grams, tokens}
    - inv: dict[gram] -> list[int] verse_idx
    """
    surahs = load_quran_arabic()
    verses: list[dict[str, Any]] = []
    inv: dict[str, list[int]] = {}

    for s in range(1, len(surahs)):
        surah = surahs[s]
        if not isinstance(surah, list):
            continue
        for a in range(1, len(surah)):
            text_ar = surah[a]
            if not isinstance(text_ar, str) or not text_ar.strip():
                continue
            norm = normalize_arabic(text_ar)
            grams = char_ngrams(norm, 3)
            toks = set(arabic_tokens(norm))

            idx = len(verses)
            verses.append(
                {
                    "ref": AyahRef(surah=s, ayah=a),
                    "text_ar": text_ar,
                    "norm": norm,
                    "grams": grams,
                    "tokens": toks,
                }
            )
            for g in grams:
                inv.setdefault(g, []).append(idx)

    return {"verses": verses, "inv": inv}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    if union == 0:
        return 0.0
    return inter / union


def _token_overlap_ratio(input_tokens: set[str], verse_tokens: set[str]) -> float:
    if not input_tokens or not verse_tokens:
        return 0.0
    return len(input_tokens & verse_tokens) / max(len(input_tokens), 1)


def _sequence_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    # difflib is fine for reranking a small candidate set
    return SequenceMatcher(None, a, b).ratio()


def match_ayah(
    transcript: str,
    *,
    max_candidates: int = 50,
    top_k: int = 5,
    min_chars: int = 12,
    min_score: float = 0.35,
) -> AyahMatchResult:
    """
    Match a transcript (expected Arabic) to the closest Quran ayah.

    Returns best match + alternatives with confidence scores.
    """
    method = "char3gram+seq+tokens"
    if not transcript or not contains_arabic(transcript):
        return AyahMatchResult(matched=None, candidates=[], method=method)

    input_norm = normalize_arabic(transcript)
    if len(input_norm.replace(" ", "")) < min_chars:
        return AyahMatchResult(matched=None, candidates=[], method=method)

    input_grams = char_ngrams(input_norm, 3)
    input_tokens = set(arabic_tokens(input_norm))

    idx = _build_index()
    inv: dict[str, list[int]] = idx["inv"]
    verses: list[dict[str, Any]] = idx["verses"]

    # Candidate retrieval by gram hit counts
    hit_counts: dict[int, int] = {}
    for g in input_grams:
        for v_idx in inv.get(g, []):
            hit_counts[v_idx] = hit_counts.get(v_idx, 0) + 1

    if not hit_counts:
        return AyahMatchResult(matched=None, candidates=[], method=method)

    # Select top-N by raw hit counts for reranking
    candidate_idxs = sorted(hit_counts.keys(), key=lambda i: hit_counts[i], reverse=True)[:max_candidates]

    scored: list[tuple[float, int]] = []
    for v_idx in candidate_idxs:
        v = verses[v_idx]
        verse_norm: str = v["norm"]
        verse_grams: set[str] = v["grams"]
        verse_tokens: set[str] = v["tokens"]

        j = _jaccard(input_grams, verse_grams)
        t = _token_overlap_ratio(input_tokens, verse_tokens)
        s = _sequence_ratio(input_norm, verse_norm)

        # Boost when input is contained in verse (partial recitation support)
        if input_norm and verse_norm and input_norm.replace(" ", "") in verse_norm.replace(" ", ""):
            s = max(s, min(1.0, len(input_norm.replace(" ", "")) / max(len(verse_norm.replace(" ", "")), 1)))

        score = 0.5 * s + 0.3 * j + 0.2 * t
        scored.append((score, v_idx))

    scored.sort(key=lambda x: x[0], reverse=True)

    candidates: list[AyahCandidate] = []
    for score, v_idx in scored[:top_k]:
        v = verses[v_idx]
        ref: AyahRef = v["ref"]
        text_ar: str = v["text_ar"]
        candidates.append(
            AyahCandidate(
                surah=ref.surah,
                ayah=ref.ayah,
                score_pct=int(round(max(0.0, min(1.0, score)) * 100)),
                text_ar=text_ar,
            )
        )

    best = candidates[0] if candidates else None
    if best is None or (scored[0][0] if scored else 0.0) < min_score:
        # Too low confidence: return candidates (for debugging) but no matched verse.
        return AyahMatchResult(matched=None, candidates=candidates, method=method)

    return AyahMatchResult(matched=best, candidates=candidates, method=method)


