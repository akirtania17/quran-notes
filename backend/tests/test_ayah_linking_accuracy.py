import random


def _iter_ayat(surahs):
    """
    surahs: 1-based list of surahs, each a 1-based list of ayah texts.
    yields (surah, ayah, text_ar)
    """
    for s in range(1, len(surahs)):
        surah = surahs[s]
        if not isinstance(surah, list):
            continue
        for a in range(1, len(surah)):
            t = surah[a]
            if isinstance(t, str) and t.strip():
                yield (s, a, t)


def _noisify(text: str, rng: random.Random) -> str:
    """
    Apply very small, deterministic noise (intentionally mild):
    - insert 1 extra space
    - drop 1 character
    """
    t = text
    if len(t) > 30:
        i = rng.randint(1, len(t) - 2)
        t = t[:i] + " " + t[i:]

    if len(t) > 20:
        i = rng.randint(1, len(t) - 2)
        t = t[:i] + t[i + 1 :]
    return t


def _make_partial(text: str, rng: random.Random, *, min_len: int = 30, max_len: int = 70) -> str:
    t = text.replace("\n", " ").strip()
    if len(t) <= min_len:
        return t
    span = rng.randint(min_len, min(max_len, len(t)))
    start = rng.randint(0, max(0, len(t) - span))
    return t[start : start + span].strip()


def test_ayah_linking_golden_accuracy_synthetic():
    """
    Synthetic “proven” test:
    - Sample ayat from the real dataset
    - Generate exact + longer-partial + minor-noise inputs
    - Assert Top-1 >= 85% and Top-5 >= 95%

    Note: This only “proves” explicit/near-explicit matching under mild noise.
    It does NOT validate implicit references/paraphrases.
    """
    # Important: other tests monkeypatch and exercise the matcher with a tiny dataset.
    # Because the matcher uses lru_cache for both dataset loading and the inverted index,
    # we must clear caches here to ensure this accuracy test evaluates against the real
    # bundled dataset.
    from app.services.ayah_linking import matcher

    matcher.load_quran_arabic.cache_clear()
    matcher._build_index.cache_clear()

    surahs = matcher.load_quran_arabic()
    all_ayat = list(_iter_ayat(surahs))
    assert len(all_ayat) >= 6000  # sanity: should be full Quran

    rng = random.Random(1337)

    # Keep this fast and deterministic.
    # 120 base ayat -> 3 cases each => 360 matcher runs (still quick).
    sample_n = 120
    sample = rng.sample(all_ayat, sample_n)

    cases = []
    for (s, a, text_ar) in sample:
        cases.append((s, a, text_ar, "exact"))
        cases.append((s, a, _make_partial(text_ar, rng), "partial"))
        cases.append((s, a, _noisify(_make_partial(text_ar, rng), rng), "partial_noise"))

    top1_ok = 0
    top5_ok = 0
    total = 0
    no_match = 0

    for (s, a, inp, kind) in cases:
        res = matcher.match_ayah(inp)
        total += 1

        if res.matched is None:
            no_match += 1
            # Still allow Top-5 credit if candidates include the truth
            if any((c.surah, c.ayah) == (s, a) for c in res.candidates[:5]):
                top5_ok += 1
            continue

        if (res.matched.surah, res.matched.ayah) == (s, a):
            top1_ok += 1
            top5_ok += 1
            continue

        if any((c.surah, c.ayah) == (s, a) for c in res.candidates[:5]):
            top5_ok += 1

    top1 = top1_ok / max(total, 1)
    top5 = top5_ok / max(total, 1)

    # MVP “balanced” thresholds
    assert top1 >= 0.85, f"Top-1 accuracy too low: {top1:.3f} (no_match={no_match}/{total})"
    assert top5 >= 0.95, f"Top-5 accuracy too low: {top5:.3f} (no_match={no_match}/{total})"


