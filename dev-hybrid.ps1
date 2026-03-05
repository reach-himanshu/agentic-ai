# Ops IQ Hybrid Development Helper
# Run this script to start services locally while infrastructure (Postgres, Weaviate) remains in containers.

Write-Host "--- Starting Ops IQ Hybrid Environment ---" -ForegroundColor Cyan

# 1. Ensure Infrastructure is running (skip if podman not available)
Write-Host "[1/5] Starting Containers (Postgres, t2v-transformers, Weaviate)..."
$podmanPath = Get-Command podman -ErrorAction SilentlyContinue
if ($podmanPath) {
    podman compose up -d postgres t2v-transformers weaviate
}
else {
    Write-Host "  [SKIP] Podman not found in PATH. Containers not started." -ForegroundColor Yellow
    Write-Host "  Please restart your terminal or start containers manually." -ForegroundColor Yellow
}

# 2. Set Environment Variables
$env:DATABASE_URL = "postgresql+asyncpg://opsiq:opsiqpassword@localhost:5433/opsiq_sessions"
$env:WEAVIATE_URL = "http://localhost:8080"

# 3. Clean up existing processes
Write-Host "[2/5] Cleaning up existing ports (8000, 8001, 5173)..."
$ports = 8000, 8001, 5173
foreach ($port in $ports) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($conn in $conns) {
            if ($conn.OwningProcess -and $conn.OwningProcess -ne 0) {
                Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

# 4. Start Services in new Windows (use powershell.exe, not pwsh)
$IIS_PYTHON = "$PSScriptRoot\iis\.venv\Scripts\python.exe"
$LIB_PYTHON = "$PSScriptRoot\librarian\.venv\Scripts\python.exe"

Write-Host "[3/5] Starting IIS Backend (Port 8000)..."
Start-Process powershell -ArgumentList "-NoExit -Command cd '$PSScriptRoot\iis'; & '$IIS_PYTHON' main.py"

Start-Sleep -Seconds 3

Write-Host "[4/5] Starting Librarian Gateway (Port 8001)..."
Start-Process powershell -ArgumentList "-NoExit -Command cd '$PSScriptRoot\librarian'; & '$LIB_PYTHON' main.py"

Start-Sleep -Seconds 2

Write-Host "[5/5] Starting Main Frontend (Port 5173)..."
Start-Process powershell -ArgumentList "-NoExit -Command cd '$PSScriptRoot\frontend'; npm run dev"

Start-Sleep -Seconds 2

Write-Host "--- Local Services Starting ---" -ForegroundColor Green
Write-Host "Assistant UI: http://localhost:5173"
Write-Host "IIS Backend:  http://localhost:8000"
Write-Host "Librarian:    http://localhost:8001"
Write-Host "-------------------------------"

