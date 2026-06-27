"""
Build a bundled Quran Arabic dataset for backend Ayah linking.

This script downloads Uthmani Arabic text and writes:
  backend/app/data/quran_arabic.json

Run from repo root:
  python backend/scripts/build_quran_arabic.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request


SRC_URL = "https://api.alquran.cloud/v1/quran/quran-uthmani"


def main() -> int:
    repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    out_dir = os.path.join(repo_root, "app", "data")
    out_path = os.path.join(out_dir, "quran_arabic.json")

    os.makedirs(out_dir, exist_ok=True)

    print(f"Downloading Quran text from: {SRC_URL}")
    with urllib.request.urlopen(SRC_URL, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    payload = json.loads(raw)

    data = payload.get("data") or {}
    surahs = data.get("surahs")
    if not isinstance(surahs, list) or len(surahs) != 114:
        raise RuntimeError("Unexpected API payload shape: data.surahs")

    # Build 1-based arrays for easy indexing
    out_surahs: list[list[str]] = [[]]  # dummy 0
    for s_idx, s in enumerate(surahs, start=1):
        ayahs = s.get("ayahs")
        if not isinstance(ayahs, list):
            raise RuntimeError(f"Unexpected surah shape at {s_idx}")
        ayah_texts: list[str] = [""]  # dummy 0
        for a in ayahs:
            ayah_texts.append(a.get("text", ""))
        out_surahs.append(ayah_texts)

    out = {
        "format": "surahs_1_based",
        "source": "alquran.cloud:quran-uthmani",
        "surahs": out_surahs,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    total_ayat = sum(len(s) - 1 for s in out_surahs[1:])
    print(f"Wrote {out_path} ({total_ayat} ayat)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise


