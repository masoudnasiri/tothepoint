@echo off
REM Procurement DSS Stop Script for Windows
REM SAFE VERSION - Preserves all data

echo ========================================
echo  Procurement DSS - Stop Services
echo  SAFE Stop (Data Preserved)
echo ========================================
echo.

REM Check if containers are running
docker-compose ps | findstr "Up" >nul 2>&1
if %errorlevel% neq 0 (
    echo ! No containers are running
    echo.
    docker-compose ps
    echo.
    echo Services are already stopped.
    pause
    exit /b 0
)

echo Current Status:
docker-compose ps
echo.

REM Ask for confirmation
set /p CONFIRM="Stop all services? Data will be preserved. (yes/no): "

if not "%CONFIRM%"=="yes" (
    echo.
    echo Stop cancelled. Services still running.
    pause
    exit /b 0
)

echo.
echo Stopping services (preserving all data)...
echo.

REM SAFE STOP - Does NOT delete volumes
docker-compose down

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   Services Stopped Successfully!
    echo ========================================
    echo.
    echo + All containers stopped
    echo + Database volume PRESERVED
    echo + All data intact (optimization runs, decisions, etc.)
    echo.
    echo Your data is safe in Docker volume: cahs_flow_project_postgres_data
    echo.
    echo To restart:
    echo   start.bat
    echo.
    echo To backup database:
    echo   backup_database.bat
    echo.
    echo To permanently delete ALL data (CAUTION!):
    echo   docker-compose down -v
    echo   ^(Only use this if you want to reset everything^)
    echo.
) else (
    echo.
    echo X Error stopping services
    echo   Check Docker Desktop is running
)

pause

