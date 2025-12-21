@echo off
echo ============================================================
echo TOR UNVEIL - Real-Time Traffic Analysis Setup
echo ============================================================
echo.

echo Step 1: Starting main application (Docker)...
docker-compose up -d
if errorlevel 1 (
    echo ERROR: Failed to start Docker containers
    pause
    exit /b 1
)
echo ✓ Main application started
echo.

echo Step 2: Waiting for backend to be ready...
timeout /t 10 /nobreak >nul
echo ✓ Backend should be ready
echo.

echo Step 3: Starting honeypot server...
echo.
echo IMPORTANT: In a separate terminal, run:
echo    cd backend
echo    python honeypot_server.py
echo.
echo Step 4: Expose with ngrok (in another terminal):
echo    ngrok http 5000
echo.
echo Step 5: Access ngrok URL via Tor Browser
echo.
echo ============================================================
echo Services Running:
echo - Frontend:  http://localhost:3000
echo - Backend:   http://localhost:8000
echo - Honeypot:  http://localhost:5000 (after manual start)
echo ============================================================
echo.
echo Press Ctrl+C to view logs, or close to continue...
docker-compose logs -f
