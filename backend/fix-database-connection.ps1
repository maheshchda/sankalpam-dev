# Fix Database Connection for Sankalpam Backend
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Fix Database Connection" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$DB_NAME = "sankalpam_db"
$DB_USER = "sankalpam_user"
$DB_PASSWORD = "sankalpam_password"
$DB_HOST = "localhost"
$DB_PORT = "5432"

Write-Host "This script will help fix the database connection issue." -ForegroundColor Yellow
Write-Host ""
Write-Host "You need to run SQL commands as the PostgreSQL admin user." -ForegroundColor Cyan
Write-Host ""
Write-Host "Option 1: Using psql command line" -ForegroundColor Green
Write-Host "  1. Open a new PowerShell window" -ForegroundColor White
Write-Host "  2. Run: psql -U postgres -d postgres" -ForegroundColor White
Write-Host "  3. Enter your postgres password when prompted" -ForegroundColor White
Write-Host "  4. Run these SQL commands:" -ForegroundColor White
Write-Host ""
Write-Host "     CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" -ForegroundColor Yellow
Write-Host "     CREATE DATABASE $DB_NAME OWNER $DB_USER;" -ForegroundColor Yellow
Write-Host "     GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" -ForegroundColor Yellow
Write-Host ""
Write-Host "  5. Type \q to exit psql" -ForegroundColor White
Write-Host ""
Write-Host "Option 2: Using pgAdmin (if installed)" -ForegroundColor Green
Write-Host "  1. Open pgAdmin" -ForegroundColor White
Write-Host "  2. Connect to your PostgreSQL server" -ForegroundColor White
Write-Host "  3. Right-click on 'Login/Group Roles' -> Create -> Login/Group Role" -ForegroundColor White
Write-Host "  4. Set name: $DB_USER, password: $DB_PASSWORD" -ForegroundColor White
Write-Host "  5. Right-click on 'Databases' -> Create -> Database" -ForegroundColor White
Write-Host "  6. Set name: $DB_NAME, owner: $DB_USER" -ForegroundColor White
Write-Host ""
Write-Host "After fixing the database, try starting the backend again:" -ForegroundColor Cyan
Write-Host "  cd backend" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host ""
