# Restart Quran Notes backend on port 8000 (Windows PowerShell)
#
# This avoids common "phantom" port states by stopping *real* listeners on 8000
# and then starting the backend in stable mode (no auto-reload).
#
# Usage:
#   cd backend
#   .\restart_backend.ps1

$ErrorActionPreference = "Stop"

function Stop-PortListeners([int]$Port) {
    $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $listeners) {
        Write-Host "No listeners found on port $Port." -ForegroundColor Green
        return
    }

    $pids = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $pids) {
        try {
            $p = Get-Process -Id $procId -ErrorAction Stop
            Write-Host "Stopping PID=$procId Name=$($p.Name) on port $Port..." -ForegroundColor Yellow
            Stop-Process -Id $procId -Force
        } catch {
            Write-Host "Could not stop PID=$procId (may already be gone): $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

Write-Host "Restarting backend on port 8000..." -ForegroundColor Green

# Ensure we run from backend/
if (-not (Test-Path .\app) -or -not (Test-Path .\run_dev.ps1)) {
    Write-Host "Please run this script from the backend directory." -ForegroundColor Red
    exit 1
}

Stop-PortListeners -Port 8000

Write-Host "Starting backend (stable, no reload)..." -ForegroundColor Green
Write-Host "Tip: Health check: http://127.0.0.1:8000/v1/health" -ForegroundColor Cyan
Write-Host ""

# Start in a new PowerShell window so it keeps running
Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-Command", "cd `"$PWD`"; .\\run_dev.ps1"
)


