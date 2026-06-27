# Mobile App Setup Script for Windows
# Run this from the apps/mobile directory

Write-Host "Quran Notes Mobile - Setup" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Check Node.js
Write-Host "Checking Node.js installation..." -ForegroundColor Yellow
$nodeVersion = node --version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Node.js not found. Please install Node.js 18+ from https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Check npm
Write-Host "Checking npm installation..." -ForegroundColor Yellow
$npmVersion = npm --version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ npm found: $npmVersion" -ForegroundColor Green
} else {
    Write-Host "✗ npm not found" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green

# Check for .env file
Write-Host ""
Write-Host "Checking environment configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env file found" -ForegroundColor Green
} else {
    Write-Host "⚠ .env file not found" -ForegroundColor Yellow
    Write-Host "  Please create .env file with:" -ForegroundColor Yellow
    Write-Host "  EXPO_PUBLIC_API_BASE_URL=http://YOUR_LOCAL_IP:8000" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Find your local IP with: ipconfig" -ForegroundColor Yellow
    Write-Host "  Look for 'IPv4 Address' under your active network adapter" -ForegroundColor Yellow
}

# Create placeholder assets if they don't exist
Write-Host ""
Write-Host "Note: You'll need to add placeholder images to assets/ directory:" -ForegroundColor Yellow
Write-Host "  - icon.png (1024x1024)" -ForegroundColor Cyan
Write-Host "  - splash.png" -ForegroundColor Cyan
Write-Host "  - adaptive-icon.png" -ForegroundColor Cyan
Write-Host "  - favicon.png" -ForegroundColor Cyan
Write-Host "  Expo will use defaults if these are missing" -ForegroundColor Yellow

Write-Host ""
Write-Host "Setup complete! 🎉" -ForegroundColor Green
Write-Host ""
Write-Host "To start the development server, run:" -ForegroundColor Yellow
Write-Host "  npm start" -ForegroundColor Cyan
Write-Host ""
Write-Host "Then scan the QR code with Expo Go app on your iPhone" -ForegroundColor Yellow

