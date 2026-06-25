# Run ZeroHarm AI Backend
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ZeroHarm AI - Backend Server" -ForegroundColor Cyan
Write-Host "  Industrial Safety Intelligence Platform" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
$pythonCmd = "python"
try {
    & $pythonCmd --version | Out-Null
} catch {
    $pythonCmd = "python3"
    try {
        & $pythonCmd --version | Out-Null
    } catch {
        Write-Host "ERROR: Python not found" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Using: $($pythonCmd)" -ForegroundColor Green

# Install dependencies
Write-Host "`n[1/3] Installing dependencies..." -ForegroundColor Yellow
$requirements = Join-Path $PSScriptRoot "..\backend\requirements.txt"
if (Test-Path $requirements) {
    & $pythonCmd -m pip install -r $requirements -q
    Write-Host "  Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  Skipping (requirements.txt not found)" -ForegroundColor Yellow
}

# Change to backend directory
$backendDir = Join-Path $PSScriptRoot "..\backend"
Set-Location $backendDir

# Start the server
Write-Host "`n[2/3] Starting API server on http://localhost:8000 ..." -ForegroundColor Yellow
Write-Host "`n[3/3] WebSocket endpoint: ws://localhost:8000/ws" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Server is running!" -ForegroundColor Green
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  Press Ctrl+C to stop" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

& $pythonCmd -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
