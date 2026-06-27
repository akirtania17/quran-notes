## Quran Arabic dataset for Ayah linking

This directory contains `quran_arabic.json`, a bundled Quran Arabic text dataset used by the backend Ayah-linking matcher.

### How to generate

From repo root:

```bash
python backend/scripts/build_quran_arabic.py
```

### Source

The generator currently downloads `quran-uthmani` from `api.alquran.cloud` and stores it locally for matching.


