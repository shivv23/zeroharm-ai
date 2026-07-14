# Run ZeroHarm AI Frontend
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ZeroHarm AI - Frontend" -ForegroundColor Cyan
Write-Host "  Geospatial Safety Dashboard" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Node.js
try {
    $nodeVersion = node --version
    Write-Host "Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Node.js not found. Install from https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Change to frontend directory
$frontendDir = Join-Path $PSScriptRoot "..\frontend"
Set-Location $frontendDir

# Install dependencies
Write-Host "`n[1/2] Installing frontend dependencies..." -ForegroundColor Yellow
npm install

# Start the development server
Write-Host "`n[2/2] Starting frontend on http://localhost:3000 ..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Frontend is starting!" -ForegroundColor Green
Write-Host "  Open: http://localhost:3000" -ForegroundColor Green
Write-Host "  Make sure backend is running on port 8000" -ForegroundColor Green
Write-Host "  Press Ctrl+C to stop" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

npm start
