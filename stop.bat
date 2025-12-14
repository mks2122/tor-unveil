@echo off
echo ========================================
echo TOR - Unveil: Stopping Application
echo ========================================
echo.

docker-compose down

echo.
echo ========================================
echo Application stopped successfully!
echo ========================================
echo.
echo To remove all data (including database):
echo   docker-compose down -v
echo.
pause
