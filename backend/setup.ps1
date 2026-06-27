# Setup script for Quran Notes Backend (Windows PowerShell)

Write-Host "Setting up Quran Notes Backend..." -ForegroundColor Green

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "Found: $pythonVersion" -ForegroundColor Cyan

# Create virtual environment
if (-not (Test-Path .venv)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Create .env if it doesn't exist
if (-not (Test-Path .env)) {
    if (Test-Path env.example) {
        Write-Host "Creating .env file from env.example..." -ForegroundColor Yellow
        Copy-Item env.example .env
    } else {
        Write-Host "env.example not found; creating a minimal .env..." -ForegroundColor Yellow
        @(
            "OPENAI_API_KEY=your_key_here",
            "ENV=dev",
            "PORT=8000"
        ) | Set-Content -Path .env -Encoding UTF8
    }

    Write-Host "Please edit .env and configure your settings (especially OPENAI_API_KEY)." -ForegroundColor Yellow
} else {
    Write-Host ".env file already exists." -ForegroundColor Green
}

# Create data directory
if (-not (Test-Path data)) {
    Write-Host "Creating data directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path data
}

if (-not (Test-Path data/uploads)) {
    Write-Host "Creating uploads directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path data/uploads
}

# Run migrations
Write-Host "Running database migrations..." -ForegroundColor Yellow
alembic upgrade head

# Run tests
Write-Host "Running tests..." -ForegroundColor Yellow
pytest -v

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env and configure your settings" -ForegroundColor White
Write-Host "2. Run: .\run_dev.ps1 to start the development server" -ForegroundColor White
Write-Host ""

