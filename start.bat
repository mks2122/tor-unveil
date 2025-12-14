@echo off
echo ========================================
echo TOR - Unveil: Starting Application
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/4] Docker is running...
echo.

REM Stop any existing containers
echo [2/4] Stopping existing containers...
docker-compose down >nul 2>&1

echo [3/4] Building and starting services...
echo This may take a few minutes on first run...
echo.
docker-compose up -d --build

if %errorlevel% neq 0 (
    echo [ERROR] Failed to start services!
    echo Check the error messages above.
    pause
    exit /b 1
)

echo.
echo [4/4] Services started successfully!
echo.
echo ========================================
echo Application URLs:
echo ========================================
echo Frontend:  http://localhost:3000
echo Backend:   http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo ========================================
echo.
echo Waiting for services to be ready (30 seconds)...
timeout /t 30 /nobreak >nul

echo.
echo Opening dashboard in browser...
start http://localhost:3000

echo.
echo ========================================
echo Application is ready!
echo ========================================
echo.
echo To view logs:    docker-compose logs -f
echo To stop:         docker-compose down
echo To restart:      docker-compose restart
echo.
pause
