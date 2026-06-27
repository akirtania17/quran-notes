# Quick Start Guide

## First Time Setup

```powershell
# Run the setup script (installs everything)
.\setup.ps1
```

This will:
- Create virtual environment
- Install dependencies
- Create .env file
- Run database migrations
- Run tests

## Daily Development

```powershell
# Start the development server (stable, recommended)
.\run_dev.ps1
```

For hot reload while editing backend code:

```powershell
.\run_dev_reload.ps1
```

Server will be available at:
- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

## Common Commands

### Run Tests
```powershell
.\.venv\Scripts\Activate.ps1
pytest -v
```

## Storage configuration (Local vs Cloudflare R2)

By default, uploads are stored on **local disk** under `UPLOAD_DIR` (`./data/uploads`).

### Local (default, free)

In `backend/.env`:

```env
STORAGE_BACKEND=local
UPLOAD_DIR=./data/uploads
TMP_DIR=./data/tmp
```

### Cloudflare R2 (S3-compatible)

This makes uploads durable across backend restarts (and across machine restarts, assuming the backend can still reach R2).

In `backend/.env`:

```env
STORAGE_BACKEND=r2
S3_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
S3_BUCKET=<bucket_name>
S3_ACCESS_KEY_ID=<r2_access_key_id>
S3_SECRET_ACCESS_KEY=<r2_secret_access_key>
S3_REGION=auto
S3_PREFIX=
TMP_DIR=./data/tmp
```

Notes:
- Buckets should remain **private** (no public access needed for this MVP phase).
- The backend will **download audio to TMP_DIR** during processing before sending it to OpenAI.
- Pricing: R2 usually stays **$0 at low usage** if you remain within any free-tier limits, but it can cost money for storage/operations if you exceed them. Always confirm current limits/pricing in your Cloudflare dashboard.

### Run Specific Test File
```powershell
.\.venv\Scripts\Activate.ps1
pytest tests/test_health.py -v
```

### Create New Migration
```powershell
.\.venv\Scripts\Activate.ps1
alembic revision --autogenerate -m "Description"
```

### Apply Migrations
```powershell
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

### Check Current Migration
```powershell
.\.venv\Scripts\Activate.ps1
alembic current
```

### Rollback Migration
```powershell
.\.venv\Scripts\Activate.ps1
alembic downgrade -1
```

## Project Structure

```
app/
├── core/          # Configuration, CORS, errors, logging, rate limiting
├── db/            # Database engine and session management
├── models/        # SQLAlchemy models (Session, Note)
├── services/      # Business logic (storage, AI, processing)
├── utils/         # Utilities (ID generation, time)
└── main.py        # FastAPI application entry point
```

## Key Files

- **app/main.py** - FastAPI application
- **app/core/config.py** - Settings (loaded from .env)
- **app/models/session.py** - Session model
- **app/models/note.py** - Note model
- **app/services/storage/local_fs.py** - File storage
- **.env** - Environment configuration (copy from `env.example`)

## Environment Variables

Edit `.env` to configure (copy `env.example` to `.env` first):

```env
# Required
OPENAI_API_KEY=your_key_here

# Optional (have defaults)
ENV=dev
PORT=8000
DATABASE_URL=sqlite:///./data/quran_notes.db
UPLOAD_DIR=./data/uploads
TMP_DIR=./data/tmp
CORS_ORIGINS=http://localhost:19006,http://localhost:8081
RATE_LIMIT_PER_MINUTE=60
MAX_UPLOAD_MB=60

# Storage backend
STORAGE_BACKEND=local

# R2 / S3-compatible settings (when STORAGE_BACKEND=r2)
S3_ENDPOINT_URL=
S3_BUCKET=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
S3_REGION=auto
S3_PREFIX=

# Processing reliability (optional)
PROCESSING_LEASE_MINUTES=10
SWEEPER_ENABLED=true
SWEEPER_INTERVAL_SECONDS=300
STUCK_THRESHOLD_MINUTES=45
STUCK_MAX_AGE_MINUTES=120
```

## Testing the API

### Using curl
```bash
# Health check
curl http://localhost:8000/v1/health

# Root endpoint
curl http://localhost:8000/
```

### Using the browser
Visit http://localhost:8000/docs for interactive API documentation.

## Troubleshooting

### Virtual environment not activating
```powershell
# If you get execution policy error
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Database issues
```powershell
# Delete database and recreate
Remove-Item data\quran_notes.db
alembic upgrade head
```

### Port already in use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F
```

## Next Steps

After backend-core is complete, the next components to implement are:

1. **Schemas** (`app/schemas/`) - Request/response models
2. **AI Services** (`app/services/ai/`) - OpenAI integration
3. **Processing Pipeline** (`app/services/processing/`) - Background jobs
4. **API Routers** (`app/routers/`) - Endpoints for sessions, notes, languages

See `IMPLEMENTATION_SUMMARY.md` for details on what's been implemented.

