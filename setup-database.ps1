# PostgreSQL Database Setup Script
# This script helps set up PostgreSQL for Sankalpam

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Sankalpam Database Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is available
$dockerAvailable = $false
try {
    $null = docker --version 2>&1
    $dockerAvailable = $true
    Write-Host "✓ Docker is available" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is NOT installed" -ForegroundColor Yellow
}

# Check if PostgreSQL is running
$postgresRunning = $false
try {
    $null = psql --version 2>&1
    $testConn = psql -U sankalpam_user -d sankalpam_db -h localhost -p 5433 -c "SELECT 1;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        $postgresRunning = $true
        Write-Host "✓ PostgreSQL is running and accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ PostgreSQL connection failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "Setup Options:" -ForegroundColor Yellow
Write-Host ""

if ($dockerAvailable) {
    Write-Host "Option 1: Use Docker (Recommended if Docker is installed)" -ForegroundColor Cyan
    Write-Host "  Run: docker-compose up -d" -ForegroundColor White
    Write-Host ""
}

Write-Host "Option 2: Install PostgreSQL Directly" -ForegroundColor Cyan
Write-Host "  1. Download from: https://www.postgresql.org/download/windows/" -ForegroundColor White
Write-Host "  2. Install with these settings:" -ForegroundColor White
Write-Host "     - Port: 5433" -ForegroundColor Gray
Write-Host "     - Username: sankalpam_user" -ForegroundColor Gray
Write-Host "     - Password: sankalpam_password" -ForegroundColor Gray
Write-Host "     - Database: sankalpam_db" -ForegroundColor Gray
Write-Host ""

if ($dockerAvailable -and -not $postgresRunning) {
    Write-Host "Starting Docker services..." -ForegroundColor Yellow
    cd "C:\Projects\sankalpam-dev"
    docker-compose up -d
    Start-Sleep -Seconds 5
    Write-Host "✓ Docker services started" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next step: Run database migrations" -ForegroundColor Yellow
    Write-Host "  cd backend" -ForegroundColor White
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  alembic upgrade head" -ForegroundColor White
} elseif (-not $postgresRunning) {
    Write-Host "⚠ PostgreSQL is not running" -ForegroundColor Yellow
    Write-Host "Please install PostgreSQL or Docker Desktop first" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "See DATABASE-SETUP.md for detailed instructions" -ForegroundColor Cyan
}

