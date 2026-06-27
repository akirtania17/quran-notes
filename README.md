# Quran Notes

Record an Islamic lecture or recitation, then have it transcribed, matched to Quran verses, translated, and summarized by an asynchronous AI pipeline.

## Overview

Quran Notes is a monorepo for a mobile app backed by a Python API. A user records audio on the phone, uploads it, and the backend processes it in the background through a multi-stage pipeline: speech-to-text, Arabic ayah linking, translation, and summarization. The client uploads the file and then polls the API for the result.

This is a batch (record-then-upload-then-process) system. It is NOT real-time or streaming transcription. Nothing is transcribed while the user is recording. Processing starts after the upload completes and runs as a background task on the server.

## How it works

The full flow, from recording to result:

1. **Audio capture (mobile).** The Expo app records audio using `expo-av` and writes it to a local `.m4a` file. The user gives the session a title and picks a target language. There is no live transcription during recording.

2. **Upload.** The app sends the file as a multipart `POST /v1/sessions` request, with the title, target language, optional duration, and an `X-Client-Id` header that identifies the device. The backend validates the file type and size, stores it (local filesystem by default), creates a session row with status `uploaded`, and enqueues a background task. The API returns immediately.

3. **Transcription (Whisper).** The background pipeline (`backend/app/services/processing/pipeline.py`) calls OpenAI Whisper (`whisper-1`) to transcribe the audio and detect the source language. The transcript and detected language are written back to the session.

4. **Arabic ayah linking (local fuzzy matcher).** The transcript is run through a local matcher in `backend/app/services/ayah_linking/` that tries to identify which Quran verse was recited. This step uses no external API. It works only on Arabic text. The algorithm:
   - **Normalization** (`normalize.py`): strips diacritics/tashkeel and tatweel, normalizes letter variants (for example أ/إ/آ/ٱ to ا, ى to ي, ؤ to و, ئ to ي), removes non-Arabic characters, and collapses whitespace.
   - **Candidate retrieval**: every verse in the Arabic Quran dataset is indexed by character 3-grams into an in-memory inverted index. The input transcript is broken into the same 3-grams, and verses are ranked by how many grams they share, keeping the top candidates.
   - **Reranking**: each candidate is scored with a weighted blend of three fuzzy-similarity signals: a `SequenceMatcher` sequence ratio on the normalized strings (weight 0.5), Jaccard overlap of the 3-gram sets (weight 0.3), and token overlap ratio (weight 0.2). A containment boost is applied when the input is a substring of a verse, which supports partial recitations.
   - **Output**: the best match plus the top alternatives, each with a confidence percentage. If the top score is below a threshold, no verse is marked as matched but the candidates are still returned. The chosen verse, confidence, and candidate list are stored on the session.

5. **Translation (GPT-4o-mini).** The transcript is translated into the target language using `gpt-4o-mini`.

6. **Summarization (GPT-4o-mini).** The transcript and translation are summarized into bullet points using `gpt-4o-mini`, stored as JSON on the session.

7. **Client polling.** Throughout processing the backend updates the session `status`, `processing_step`, and `progress_pct`. The mobile app polls `GET /v1/sessions/{id}` (see `apps/mobile/src/hooks/useSessionPolling.ts`) and renders progress, then the transcript, matched ayah, translation, and summary once the status reaches `complete`. Failed runs are marked `failed` with an error message and can be retried via `POST /v1/sessions/{id}/retry`.

The pipeline is resume-safe: each step is skipped if its output already exists, and a short lease prevents duplicate concurrent processing of the same session.

## Architecture

Monorepo with two parts:

- **`apps/mobile/`** — React Native app (Expo, TypeScript). Records audio, uploads sessions, polls for results, and displays them.
- **`backend/`** — FastAPI service (Python). Handles uploads, storage, the processing pipeline, and the database.

Storage and processing model:

- File storage is pluggable. Default is the local filesystem; a Cloudflare R2 / S3-compatible backend is available via configuration.
- Processing runs as a FastAPI `BackgroundTask` in the same process, with status polling rather than a separate worker queue. Run the server with a single worker for this reason.
- No user accounts. The device sends an anonymous `X-Client-Id` (a UUID), and all data is scoped to that client id.

## Tech stack

**Mobile**
- React Native 0.81 + Expo 54, TypeScript
- React Navigation
- Zustand (state)
- AsyncStorage (local persistence, anonymous client id, local gamification)
- expo-av (audio recording), expo-file-system

**Backend**
- FastAPI + Uvicorn
- SQLAlchemy 2 + SQLite
- Alembic (migrations)
- OpenAI Python SDK (Whisper transcription, GPT-4o-mini translation and summarization)
- Local Arabic ayah matcher (n-gram inverted index + difflib similarity, no external service)
- boto3 (optional R2 / S3 storage)
- pytest (tests)

## Setup

### Backend

From `backend/` (Windows PowerShell shown; commands map directly to other shells):

```powershell
cd backend

# Create and activate a virtual environment (Python 3.11+)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create the .env file and set your OpenAI key
Copy-Item env.example .env
# Edit .env and set OPENAI_API_KEY

# Apply database migrations (creates the SQLite schema)
alembic upgrade head

# Run the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Convenience scripts are provided: `.\run_dev.ps1` (stable, runs `alembic upgrade head` then starts Uvicorn) and `.\run_dev_reload.ps1` (same, with hot reload for backend edits). For production, run a single worker: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1`.

Once running:
- API: http://127.0.0.1:8000
- Interactive docs: http://127.0.0.1:8000/docs

### Mobile

```bash
cd apps/mobile
npm install

# Point the app at your backend (copy the example, then edit)
# Set EXPO_PUBLIC_API_BASE_URL to your computer's LAN IP, e.g. http://192.168.1.10:8000

npx expo start
```

Test on a phone with Expo Go: keep the phone and computer on the same Wi-Fi network and scan the QR code from the Expo CLI. The `EXPO_PUBLIC_API_BASE_URL` must use your machine's LAN IP (not `localhost`) so the phone can reach the backend.

## Usage

1. Start the backend and the Expo dev server.
2. Open the app, record a lecture or recitation, give it a title, and choose a target language.
3. Upload. The session appears with a processing status.
4. Wait while the app polls for progress. When processing completes you can view the transcript, the matched Arabic ayah (when one is found) with a confidence score, the translation, and a bullet-point summary.

## Project structure

```
Quran/
├── apps/
│   └── mobile/                 # React Native (Expo, TypeScript) app
│       └── src/
│           ├── api/            # API client and endpoint wrappers
│           ├── components/     # UI components
│           ├── hooks/          # Hooks (e.g. useSessionPolling)
│           ├── navigation/     # React Navigation setup
│           ├── screens/        # Record, Home, SessionDetail, Settings, etc.
│           ├── state/          # Zustand stores
│           ├── storage/        # AsyncStorage helpers
│           └── types/          # TypeScript types
└── backend/
    ├── alembic/                # Migrations
    └── app/
        ├── core/               # Config, CORS, errors, logging, rate limiting
        ├── db/                 # SQLAlchemy engine and session
        ├── models/             # ORM models (Session, Note, ...)
        ├── routers/            # sessions, notes, languages, highlights
        ├── schemas/            # Pydantic request/response models
        ├── services/
        │   ├── ai/             # OpenAI provider and prompts
        │   ├── ayah_linking/   # Arabic verse matcher (matcher.py, normalize.py)
        │   ├── processing/     # Pipeline and stuck-session sweeper
        │   └── storage/        # Local FS and R2/S3 storage backends
        └── data/               # Quran Arabic dataset, uploads
```

## Results

- 28 backend tests passing (pytest), covering ayah-linking behavior and accuracy, core utilities, models, health, storage resolution, and processing-reliability paths. Run them with `pytest` from `backend/`.

## Limitations / notes

- **Not real-time.** Transcription is batch. The user records, uploads, and the backend transcribes asynchronously after the upload. There is no live or streaming transcription.
- **Ayah linking is Arabic-only.** The matcher returns no result for non-Arabic transcripts. It identifies single verses and does not currently segment a transcript into multiple verse references.
- **Mobile UI is a work in progress.** Screens and flows are partial and still being built out.
- **No user accounts.** Identity is an anonymous per-device `X-Client-Id` UUID. There is no login, and data is scoped to that client id.
- **Single-process processing.** Background processing runs in-process with status polling, so the server should run with a single worker. This is an MVP design, not a distributed queue.
```
