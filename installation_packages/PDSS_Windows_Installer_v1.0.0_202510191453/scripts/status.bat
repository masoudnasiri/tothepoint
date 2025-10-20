@echo off
cd /d "%~dp0\.."
echo ========================================================================
echo   PDSS System Status
echo ========================================================================
echo.
docker-compose ps
echo.
pause
