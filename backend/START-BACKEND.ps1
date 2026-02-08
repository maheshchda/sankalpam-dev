# Sankalpam Backend Server Startup Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting Sankalpam Backend Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to backend directory
$backendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $backendDir

Write-Host "Current directory: $backendDir" -ForegroundColor Gray
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "Starting uvicorn server..." -ForegroundColor Yellow
Write-Host "Backend will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

