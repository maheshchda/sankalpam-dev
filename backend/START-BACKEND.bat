@echo off
echo ========================================
echo   Starting Sankalpam Backend Server
echo ========================================
echo.

cd /d "%~dp0"
echo Current directory: %CD%
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting uvicorn server...
echo Backend will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press CTRL+C to stop the server
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause

