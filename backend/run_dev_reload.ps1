# Development server startup script (with auto-reload) for Windows PowerShell
#
# Use this when actively editing backend code and you want hot reload.
# For stable mobile testing on port 8000, prefer: .\run_dev.ps1

Write-Host "Starting Quran Notes Backend (Development Mode, Reload)..." -ForegroundColor Green

# Activate virtual environment
if (Test-Path .venv) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "Virtual environment not found. Please run setup first." -ForegroundColor Red
    exit 1
}

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "Warning: .env file not found. Copy env.example to .env and configure OPENAI_API_KEY." -ForegroundColor Yellow
}

Write-Host "Starting Uvicorn server (reload)..." -ForegroundColor Green
Write-Host "API will be available at: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "API docs will be available at: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Ensure DB schema is up to date (prevents 500s after adding columns)
Write-Host "Applying database migrations (alembic upgrade head)..." -ForegroundColor Yellow
alembic upgrade head

# Only watch backend/app to avoid reload loops from data/uploads writes
uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000


