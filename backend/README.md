# Quran Notes Backend

Backend API for the Quran Notes mobile application. Built with FastAPI, SQLAlchemy, and SQLite.

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **Alembic** - Database migrations
- **SQLite** - Lightweight database for MVP
- **OpenAI Integration** - Transcription, translation, and summarization
- **Rate Limiting** - In-memory rate limiting per client
- **CORS** - Configured for mobile app access
- **Local File Storage** - File uploads stored locally

## Project Structure

```
backend/
├── alembic/              # Database migrations
│   ├── versions/         # Migration files
│   └── env.py           # Alembic environment
├── app/
│   ├── core/            # Core configuration
│   │   ├── config.py    # Settings management
│   │   ├── cors.py      # CORS middleware
│   │   ├── errors.py    # Exception handlers
│   │   ├── logging.py   # Logging setup
│   │   └── rate_limit.py # Rate limiting
│   ├── db/              # Database setup
│   │   ├── engine.py    # SQLAlchemy engine
│   │   └── session.py   # Session management
│   ├── models/          # SQLAlchemy models
│   │   ├── base.py      # Base model
│   │   ├── session.py   # Session model
│   │   └── note.py      # Note model
│   ├── services/        # Business logic
│   │   └── storage/     # File storage
│   │       ├── base.py  # Storage interface
│   │       └── local_fs.py # Local filesystem storage
│   ├── utils/           # Utilities
│   │   ├── ids.py       # ID generation
│   │   └── time.py      # Time utilities
│   └── main.py          # FastAPI application
├── data/                # Data directory
│   └── uploads/         # Uploaded audio files
├── tests/               # Test files
├── requirements.txt     # Python dependencies
├── alembic.ini         # Alembic configuration
└── README.md           # This file
```

## Setup

### Prerequisites

- Python 3.11 or higher
- pip

### Installation

1. Create and activate virtual environment:

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create `.env` file from example:

```powershell
Copy-Item env.example .env
```

4. Update `.env` with your configuration:

```env
ENV=dev
HOST=0.0.0.0
PORT=8000

CORS_ORIGINS=http://localhost:19006,http://localhost:8081

DATABASE_URL=sqlite:///./data/quran_notes.db
UPLOAD_DIR=./data/uploads

OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_TRANSLATE=gpt-4o-mini
OPENAI_MODEL_SUMMARIZE=gpt-4o-mini
OPENAI_MODEL_TRANSCRIBE=whisper-1

RATE_LIMIT_PER_MINUTE=60
MAX_UPLOAD_MB=60
```

5. Run database migrations:

```powershell
alembic upgrade head
```

## Running the Server

### Development

```powershell
# Stable (recommended for mobile testing)
.\run_dev.ps1

# Hot reload (use while editing backend code)
.\run_dev_reload.ps1
```

The API will be available at:
- API: http://127.0.0.1:8000
- Interactive docs: http://127.0.0.1:8000/docs
- Alternative docs: http://127.0.0.1:8000/redoc

**Note**: Prefer `127.0.0.1` for local checks on Windows. `localhost` may resolve to IPv6 and can be confusing when debugging.

### Render / Docker deployment
- A production Docker image and entrypoint are provided in `backend/Dockerfile` and `backend/entrypoint.sh`.
- See `docs/OPS_RUNBOOK.md` for Render configuration, required env vars, and health checks.

### Production

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

**Note**: Keep workers at 1 for MVP since we're using BackgroundTasks for processing.

## API Endpoints

### Health Check

```
GET /v1/health
```

Returns server health status.

### Core Endpoints (to be implemented)

- `POST /v1/sessions` - Upload audio session
- `GET /v1/sessions` - List sessions
- `GET /v1/sessions/{id}` - Get session details
- `POST /v1/sessions/{id}/retry` - Retry failed processing
- `POST /v1/sessions/{id}/notes` - Create note
- `GET /v1/sessions/{id}/notes` - List notes
- `GET /v1/languages` - List supported languages

## Authentication

All requests require the `X-Client-Id` header with a unique device identifier (UUID).

Example:
```
X-Client-Id: 550e8400-e29b-41d4-a716-446655440000
```

## Database Migrations

### Create a new migration

```powershell
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations

```powershell
alembic upgrade head
```

### Rollback migration

```powershell
alembic downgrade -1
```

## Testing

```powershell
pytest
```

## Architecture

### Core Components

1. **Config Management** (`app/core/config.py`)
   - Pydantic settings for environment variables
   - Type-safe configuration

2. **CORS** (`app/core/cors.py`)
   - Configured for mobile app origins
   - Allows all methods and headers

3. **Rate Limiting** (`app/core/rate_limit.py`)
   - In-memory sliding window rate limiter
   - Per client_id or IP address
   - Configurable limits

4. **Error Handling** (`app/core/errors.py`)
   - Custom exception classes
   - Consistent error responses
   - Proper HTTP status codes

5. **Database Models** (`app/models/`)
   - Session: Audio recording sessions
   - Note: User notes for sessions
   - Proper indexing for performance

6. **Storage** (`app/services/storage/`)
   - Abstract storage interface
   - Local filesystem implementation
   - Easy to swap for S3/R2 later

### Database Schema

**Sessions Table:**
- `id` - Unique session ID (ULID-like)
- `client_id` - Device identifier
- `title` - Session title
- `created_at` - Creation timestamp
- `duration_seconds` - Audio duration
- `audio_path` - Path to audio file
- `status` - Processing status (uploaded/processing/complete/failed)
- `source_language` - Detected source language
- `target_language` - Target translation language
- `transcript` - Transcribed text
- `translation` - Translated text
- `summary_bullets_json` - JSON array of summary points
- `error_message` - Error message if failed

**Notes Table:**
- `id` - Unique note ID
- `session_id` - Foreign key to sessions
- `client_id` - Device identifier
- `text` - Note content
- `created_at` - Creation timestamp

## Development Notes

### ID Generation

IDs use a ULID-like format: `{prefix}_{timestamp_base36}{random}`

Example: `sess_01J8X9Z2K3M4N5P6Q7R8S9T0`

### Status Flow

1. `uploaded` - Initial state after upload
2. `processing` - AI processing in progress
3. `complete` - Successfully processed
4. `failed` - Processing failed (with error_message)

### Rate Limiting

- Default: 60 requests per minute per client
- Uses sliding window algorithm
- Tracks by client_id or IP address
- Returns 429 when exceeded

## Next Steps

The following components need to be implemented:

1. **AI Services** (`app/services/ai/`)
   - OpenAI provider implementation
   - Transcription, translation, summarization
   - Safe prompts (no hallucinated citations)

2. **Processing Pipeline** (`app/services/processing/`)
   - Background processing orchestration
   - Status updates
   - Error handling

3. **API Routers** (`app/routers/`)
   - Sessions endpoints
   - Notes endpoints
   - Languages endpoint

4. **Schemas** (`app/schemas/`)
   - Request/response models
   - Validation

## License

Private - Quran Notes MVP
