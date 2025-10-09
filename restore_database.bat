@echo off
REM Restore database from backup file

SET BACKUP_DIR=database_backups

echo ====================================
echo Database Restore Utility
echo ====================================
echo.

REM Check if backup directory exists
if not exist %BACKUP_DIR% (
    echo X Backup directory not found: %BACKUP_DIR%
    echo   Create a backup first using backup_database.bat
    pause
    exit /b 1
)

REM List available backups
echo Available backups:
echo.
dir /b /o-d %BACKUP_DIR%\backup_*.sql
echo.

REM Ask for backup file
set /p BACKUP_FILE="Enter backup filename (or press Enter for latest): "

REM If no input, use latest backup
if "%BACKUP_FILE%"=="" (
    for /f "delims=" %%F in ('dir /b /o-d %BACKUP_DIR%\backup_*.sql') do (
        set BACKUP_FILE=%%F
        goto :found
    )
)

:found
SET FULL_PATH=%BACKUP_DIR%\%BACKUP_FILE%

if not exist %FULL_PATH% (
    echo X Backup file not found: %FULL_PATH%
    pause
    exit /b 1
)

echo.
echo Selected backup: %FULL_PATH%
echo.
echo ⚠️  WARNING: This will REPLACE all current data!
echo.
set /p CONFIRM="Are you sure you want to restore? (yes/no): "

if not "%CONFIRM%"=="yes" (
    echo Restore cancelled.
    pause
    exit /b 0
)

echo.
echo Restoring database...

REM Drop existing connections
docker-compose exec postgres psql -U postgres -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'procurement_dss' AND pid <> pg_backend_pid();"

REM Drop and recreate database
docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS procurement_dss;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE procurement_dss;"

REM Restore from backup
docker-compose exec -T postgres psql -U postgres -d procurement_dss < %FULL_PATH%

if %errorlevel% equ 0 (
    echo.
    echo ====================================
    echo + Restore Complete!
    echo ====================================
    echo.
    echo Database restored from: %FULL_PATH%
    echo.
    echo Restarting backend to reconnect...
    docker-compose restart backend
    timeout /t 3 >nul
    echo + Backend restarted
    echo.
) else (
    echo.
    echo ====================================
    echo X Restore Failed!
    echo ====================================
    echo Check the backup file and try again.
)

pause

