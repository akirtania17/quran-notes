import asyncio

import pytest

from app.core.config import settings
from app.models.session import Session as SessionModel
from app.utils.time import utc_now


def _minimal_quran_surahs():
    # 1-based surah list, each surah is a 1-based ayah list
    return [
        [],  # dummy 0
        [
            "",  # dummy 0
            "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ",
        ],
        [
            "",
            "قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ",
            "قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ",
        ],
    ]


def test_match_ayah_exact(monkeypatch):
    from app.services.ayah_linking import matcher

    # Ensure caches don't leak across tests
    matcher.load_quran_arabic.cache_clear()
    matcher._build_index.cache_clear()

    monkeypatch.setattr(matcher, "load_quran_arabic", lambda: _minimal_quran_surahs(), raising=True)
    matcher._build_index.cache_clear()

    res = matcher.match_ayah("الحمد لله رب العالمين")
    assert res.matched is not None
    assert (res.matched.surah, res.matched.ayah) == (1, 1)
    assert "ٱلْحَمْدُ" in res.matched.text_ar
    assert res.matched.score_pct >= 60


def test_match_ayah_partial(monkeypatch):
    from app.services.ayah_linking import matcher

    matcher.load_quran_arabic.cache_clear()
    matcher._build_index.cache_clear()

    monkeypatch.setattr(matcher, "load_quran_arabic", lambda: _minimal_quran_surahs(), raising=True)
    matcher._build_index.cache_clear()

    res = matcher.match_ayah("الحمد لله", min_chars=2)
    # input is short, but should still generally match due to containment + ngrams
    assert res.matched is not None
    assert (res.matched.surah, res.matched.ayah) == (1, 1)


def test_match_ayah_ambiguous_returns_candidates(monkeypatch):
    from app.services.ayah_linking import matcher

    matcher.load_quran_arabic.cache_clear()
    matcher._build_index.cache_clear()

    monkeypatch.setattr(matcher, "load_quran_arabic", lambda: _minimal_quran_surahs(), raising=True)
    matcher._build_index.cache_clear()

    # Shared prefix should produce multiple plausible candidates.
    res = matcher.match_ayah("قل اعوذ برب", min_chars=2, min_score=0.0)
    assert len(res.candidates) >= 2
    assert { (c.surah, c.ayah) for c in res.candidates[:2] } == {(2, 1), (2, 2)}


@pytest.mark.parametrize("text", ["", "hello world", "12345"])
def test_match_ayah_non_arabic_or_empty_returns_none(text, monkeypatch):
    from app.services.ayah_linking import matcher

    # Should short-circuit before touching dataset.
    res = matcher.match_ayah(text)
    assert res.matched is None
    assert res.candidates == []


def test_pipeline_sets_ayah_linking_fields(test_db, monkeypatch):
    """
    Validate pipeline integration stores ayah linking results and still completes.
    """
    monkeypatch.setattr(settings, "openai_api_key", "test-key", raising=False)

    import app.services.processing.pipeline as pipeline
    from app.services.ai.openai_provider import openai_provider
    from app.services.ayah_linking.matcher import AyahCandidate, AyahMatchResult

    async def translate_ok(*args, **kwargs):
        return "translated"

    async def summarize_ok(*args, **kwargs):
        return ["a"]

    monkeypatch.setattr(openai_provider, "translate", translate_ok, raising=True)
    monkeypatch.setattr(openai_provider, "summarize", summarize_ok, raising=True)

    def fake_match_ayah(transcript: str):
        return AyahMatchResult(
            matched=AyahCandidate(surah=1, ayah=1, score_pct=88, text_ar="ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ"),
            candidates=[
                AyahCandidate(surah=1, ayah=1, score_pct=88, text_ar="ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ"),
                AyahCandidate(surah=1, ayah=2, score_pct=52, text_ar="(alt)"),
            ],
            method="test",
        )

    monkeypatch.setattr(pipeline, "match_ayah", fake_match_ayah, raising=True)

    db = test_db()
    try:
        s = SessionModel(
            id="sess_test_ayah_link",
            client_id="test-client",
            title="AyahLink",
            created_at=utc_now(),
            duration_seconds=10,
            audio_path="ignored.m4a",
            status="uploaded",
            target_language="en",
            transcript="الحمد لله رب العالمين",
            source_language="ar",
            translation=None,
            summary_bullets_json=None,
            matched_method=None,
        )
        db.add(s)
        db.commit()
    finally:
        db.close()

    asyncio.run(pipeline.process_session("sess_test_ayah_link", "test-client"))

    db = test_db()
    try:
        s2 = db.query(SessionModel).filter(SessionModel.id == "sess_test_ayah_link").first()
        assert s2 is not None
        assert s2.status == "complete"
        assert s2.matched_surah == 1
        assert s2.matched_ayah == 1
        assert s2.matched_confidence_pct == 88
        assert s2.matched_method == "test"
        assert s2.matched_candidates_json is not None and "score_pct" in s2.matched_candidates_json
    finally:
        db.close()


