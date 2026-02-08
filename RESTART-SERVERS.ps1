# Quick restart script for Sankalpam servers
Write-Host "=== RESTARTING SANKKALPAM SERVERS ===" -ForegroundColor Green

# Kill all Node processes
Write-Host "`nStopping all Node.js processes..." -ForegroundColor Yellow
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Clear Next.js cache
Write-Host "`nClearing Next.js cache..." -ForegroundColor Yellow
$frontendPath = "C:\Projects\sankalpam-dev\frontend"
if (Test-Path "$frontendPath\.next") {
    Remove-Item -Recurse -Force "$frontendPath\.next" -ErrorAction SilentlyContinue
    Write-Host "  Cache cleared" -ForegroundColor Green
}

# Start frontend
Write-Host "`nStarting Frontend Server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; Write-Host '=== FRONTEND SERVER ===' -ForegroundColor Green; npm run dev" -WindowStyle Normal

Write-Host "`n✓ Frontend server starting in new window" -ForegroundColor Green
Write-Host "`nWait for 'Ready' message, then:" -ForegroundColor Yellow
Write-Host "  1. Open: http://localhost:3000" -ForegroundColor White
Write-Host "  2. Hard refresh: Ctrl+Shift+R" -ForegroundColor White
Write-Host "`nIf you see errors in the server window, share them!" -ForegroundColor Cyan

