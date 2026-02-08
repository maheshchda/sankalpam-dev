@echo off
echo ========================================
echo   Restarting Sankalpam Application
echo   (Without Docker)
echo ========================================
echo.

echo Step 1: Checking PostgreSQL...
sc query postgresql-x64-13 >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] PostgreSQL service found
) else (
    echo [X] PostgreSQL service not found
    echo Please make sure PostgreSQL is installed and running
    pause
    exit /b 1
)

echo.
echo Step 2: Starting Backend Server...
echo.
start "Sankalpam Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo.
echo Step 3: Starting Frontend Server...
echo.
start "Sankalpam Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   Application Starting...
echo ========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Two new windows have opened:
echo   - Backend server window
echo   - Frontend server window
echo.
echo Keep both windows open!
echo.
pause


