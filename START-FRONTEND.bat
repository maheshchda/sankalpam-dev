@echo off
echo ========================================
echo   Starting Frontend Server
echo ========================================
echo.

cd /d "C:\Projects\sankalpam-dev\frontend"

echo Clearing cache...
if exist .next rmdir /s /q .next

echo.
echo Starting npm run dev...
echo.
echo Wait for "Ready in X seconds" message
echo Then open: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo.

npm run dev

pause

