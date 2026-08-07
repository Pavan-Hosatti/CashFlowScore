# CashFlowScore — Event Pipeline Demo Launcher
# Run this from the project root:  .\scripts\start_demo.ps1
# Opens http://localhost:8002/demo in your browser once the API is up.

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "  CashFlowScore Event Pipeline Demo" -ForegroundColor Cyan
Write-Host "  ─────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# 1. Docker
Write-Host "  [1/4] Starting Docker services (Redpanda · TimescaleDB · Redis)..." -ForegroundColor Yellow
Push-Location $ProjectRoot
try {
    docker compose up -d 2>&1 | Out-Null
    Write-Host "        Docker services started." -ForegroundColor Green
} catch {
    Write-Host "        Docker not running — pipeline will use in-memory mode." -ForegroundColor DarkYellow
}
Pop-Location

# 2. Install Python deps
Write-Host "  [2/4] Checking Python dependencies..." -ForegroundColor Yellow
$venvPip = Join-Path $ProjectRoot "..\\.venv\\Scripts\\pip.exe"
if (Test-Path $venvPip) {
    & $venvPip install -q -r "$ProjectRoot\requirements.txt"
} else {
    pip install -q -r "$ProjectRoot\requirements.txt" 2>&1 | Out-Null
}
Write-Host "        Dependencies ready." -ForegroundColor Green

# 3. Seed demo data
Write-Host "  [3/4] Seeding demo data (75 businesses, 6 months of events)..." -ForegroundColor Yellow
$pythonExe = Join-Path $ProjectRoot "..\\.venv\\Scripts\\python.exe"
if (-not (Test-Path $pythonExe)) { $pythonExe = "python" }
& $pythonExe -m scripts.demo_seed 2>&1 | Out-Null
Write-Host "        Demo data seeded." -ForegroundColor Green

# 4. Start API
Write-Host "  [4/4] Starting event pipeline API on http://localhost:8002 ..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  ┌─────────────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "  │  Live demo:   http://localhost:8002/demo            │" -ForegroundColor Cyan
Write-Host "  │  API docs:    http://localhost:8002/docs            │" -ForegroundColor Cyan
Write-Host "  │  Status:      http://localhost:8002/pipeline-status │" -ForegroundColor Cyan
Write-Host "  └─────────────────────────────────────────────────────┘" -ForegroundColor Cyan
Write-Host ""

Start-Process "http://localhost:8002/demo"
& $pythonExe -m uvicorn app.api:app --host 0.0.0.0 --port 8002 --reload --app-dir "$ProjectRoot"
