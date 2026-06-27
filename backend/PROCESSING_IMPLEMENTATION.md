# Background Processing Implementation

## Overview

This document describes the implementation of the OpenAI AI provider and background processing pipeline for the Quran Notes backend.

## Components Implemented

### 1. AI Provider Interface (`app/services/ai/base.py`)

Abstract base class defining the contract for AI providers:
- `transcribe(audio_path)` → (transcript, detected_language)
- `translate(text, target_language, source_language)` → translation
- `summarize(transcript, translation, target_language)` → list of bullets

### 2. OpenAI Provider (`app/services/ai/openai_provider.py`)

Implementation using OpenAI's APIs:
- **Transcription**: Uses Whisper model with language detection
- **Translation**: Uses GPT-4o-mini with low temperature (0.3) for consistency
- **Summarization**: Uses GPT-4o-mini with moderate temperature (0.5) for natural output

Features:
- Async/await pattern for non-blocking operations
- Comprehensive error handling and logging
- Configurable models via environment variables
- Automatic bullet point parsing (supports both "- " and "* " formats)
- Enforces 3-7 bullet constraint

### 3. Safe Prompts (`app/services/ai/prompts.py`)

Carefully crafted prompts following strict safety guidelines:

**Translation System Prompt**:
- Faithful translation without interpretation
- Preserves speaker's tone and intent
- Never adds invented content
- Uses appropriate Islamic terminology

**Summarization System Prompt**:
- Neutral and factual only
- Explicitly forbids inventing verses/hadith/citations
- Instructions to omit uncertain details
- Clear output format requirements

### 4. Processing Pipeline (`app/services/processing/pipeline.py`)

Background processing orchestration:

**Status Flow**:
1. `uploaded` → Initial state after file upload
2. `processing` → Set when background task starts
3. `complete` → Set when all AI steps succeed
4. `failed` → Set if any step fails (with error_message)

**Pipeline Steps**:
1. Fetch session from database
2. Determine the **next missing step** (resume support)
3. Update status to "processing" and publish `processing_step` + `progress_pct`
4. Transcribe audio (only if transcript is missing)
5. Translate transcript (only if translation is missing)
6. Generate 3-7 summary bullets (only if summary is missing)
7. Update session with all results and mark "complete"
8. On error: mark "failed" with user-friendly error message

**Implementation Details**:
- Uses separate database session for background task
- Comprehensive error handling at each step
- Error messages truncated to 500 chars
- Proper cleanup with try/except/finally
- Synchronous wrapper for FastAPI BackgroundTasks compatibility
- Resumable/idempotent: retries continue from the next missing step without redoing completed work
- Lease protection: avoids duplicate concurrent processing via `PROCESSING_LEASE_MINUTES` + `processing_updated_at`

### 5. Stuck-session Sweeper (`app/services/processing/sweeper.py`)

In-process periodic recovery for sessions stuck in `uploaded`/`processing`:

- If a session is stale beyond `STUCK_THRESHOLD_MINUTES`, it is reset to `uploaded/queued` and processing is re-enqueued.
- If the session is too old (`STUCK_MAX_AGE_MINUTES`), it is marked `failed` with a user-friendly message.

### 6. Integration (`app/routers/sessions.py`)

Updated session endpoints:
- `POST /v1/sessions`: Triggers background processing after upload
- `POST /v1/sessions/{id}/retry`: Resets failed sessions and retries processing

## Configuration

Environment variables (from `.env`):
```env
OPENAI_API_KEY=your-key-here
OPENAI_MODEL_TRANSCRIBE=whisper-1
OPENAI_MODEL_TRANSLATE=gpt-4o-mini
OPENAI_MODEL_SUMMARIZE=gpt-4o-mini
PROCESSING_LEASE_MINUTES=10
SWEEPER_ENABLED=true
SWEEPER_INTERVAL_SECONDS=300
STUCK_THRESHOLD_MINUTES=45
STUCK_MAX_AGE_MINUTES=120
```

## Error Handling

- Each AI step wrapped in try/except
- Specific error messages for each step (e.g., "Transcription failed: ...")
- Database errors caught separately
- All errors logged with full stack traces
- User-facing error messages sanitized (max 500 chars)

## Usage

The processing pipeline runs automatically:

1. **Upload**: Client uploads audio → session created with status "uploaded"
2. **Processing**: Background task starts → status changes to "processing"
3. **Completion**: AI steps complete → status changes to "complete" with results
4. **Polling**: Client polls `GET /v1/sessions/{id}` to check status

If processing fails:
- Status set to "failed"
- Error message stored in session
- Client can retry via `POST /v1/sessions/{id}/retry`

## Safety Features

Following the plan's strict guidelines:
- ✅ Neutral, non-interpretive prompts
- ✅ Never invents Quranic verses, hadith, or citations
- ✅ Omits uncertain details rather than guessing
- ✅ Factual summaries only
- ✅ Clear instructions to AI not to embellish

## Testing

To test the implementation:
1. Ensure OPENAI_API_KEY is set in `.env`
2. Start the server: `uvicorn app.main:app --reload`
3. Upload an audio file via `POST /v1/sessions`
4. Poll the session status: `GET /v1/sessions/{id}`
5. Verify transcript, translation, and summary appear when status is "complete"

## Future Improvements (Not in MVP)

- Real job queue (RQ/Celery) for better reliability
- Retry logic with exponential backoff
- Progress tracking (e.g., "Transcribing...", "Translating...")
- Support for multiple AI providers
- Caching/memoization for repeated content

