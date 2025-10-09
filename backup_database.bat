@echo off
REM Backup database from Docker PostgreSQL container

SET BACKUP_DIR=database_backups
SET TIMESTAMP=%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%
SET TIMESTAMP=%TIMESTAMP: =0%
SET BACKUP_FILE=%BACKUP_DIR%\backup_%TIMESTAMP%.sql

REM Create backup directory if not exists
if not exist %BACKUP_DIR% mkdir %BACKUP_DIR%

echo ====================================
echo Database Backup Utility
echo ====================================
echo.

echo Creating backup...
docker-compose exec -T postgres pg_dump -U postgres procurement_dss > %BACKUP_FILE%

if %errorlevel% equ 0 (
    echo + Backup created: %BACKUP_FILE%
    
    REM Get file size
    for %%A in (%BACKUP_FILE%) do set FILESIZE=%%~zA
    echo + Backup size: %FILESIZE% bytes
    echo.
    
    REM Keep only last 10 backups to save space
    echo Cleaning old backups (keeping last 10)...
    for /f "skip=10 delims=" %%F in ('dir /b /o-d %BACKUP_DIR%\backup_*.sql 2^>nul') do (
        del %BACKUP_DIR%\%%F
        echo   Deleted old backup: %%F
    )
    
    echo.
    echo ====================================
    echo + Backup Complete!
    echo ====================================
    echo.
    echo To restore this backup:
    echo   docker-compose exec -T postgres psql -U postgres -d procurement_dss ^< %BACKUP_FILE%
    echo.
) else (
    echo ====================================
    echo X Backup Failed!
    echo ====================================
    echo.
    echo Possible issues:
    echo   1. Docker containers not running
    echo   2. Database connection failed
    echo.
    echo Try:
    echo   docker-compose up -d postgres
    echo   timeout /t 5
    echo   Then run this script again
)

pause

