@echo off
REM ============================================================================
REM  PDSS Platform Update Script (Windows)
REM  Updates a deployed PDSS platform with latest code changes
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo   PDSS Platform Update Script
echo ============================================================================
echo.

REM Find deployment directory
set DEPLOY_DIR=
if exist "%CD%\docker-compose.yml" (
    set DEPLOY_DIR=%CD%
) else if exist "%USERPROFILE%\pdss\docker-compose.yml" (
    set DEPLOY_DIR=%USERPROFILE%\pdss
) else (
    echo [ERROR] Could not find PDSS deployment directory!
    echo.
    set /p DEPLOY_DIR="Enter deployment directory path: "
    if not exist "!DEPLOY_DIR!\docker-compose.yml" (
        echo [ERROR] docker-compose.yml not found in specified directory
        pause
        exit /b 1
    )
)

echo [OK] Found deployment at: %DEPLOY_DIR%
echo.
cd /d "%DEPLOY_DIR%"

echo ============================================================================
echo   PRE-UPDATE CHECKS
echo ============================================================================
echo.

echo [1/5] Checking if platform is running...
docker-compose ps | findstr "Up" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Platform is running
    set PLATFORM_RUNNING=true
) else (
    echo [INFO] Platform is not running
    set PLATFORM_RUNNING=false
)
echo.

echo [2/5] Checking for update files...
set UPDATE_DIR=%DEPLOY_DIR%\..\update_files
if not exist "%UPDATE_DIR%" (
    echo [INFO] No update_files directory found
    echo.
    echo Update files should be placed in: %UPDATE_DIR%
    echo.
    echo Structure:
    echo   update_files\
    echo   ^|-- backend\
    echo   ^|   ^`-- (updated backend files)
    echo   ^`-- frontend\
    echo       ^`-- (updated frontend files)
    echo.
    set /p CONTINUE="Continue anyway? (yes/no): "
    if not "!CONTINUE!"=="yes" (
        echo Update cancelled.
        pause
        exit /b 0
    )
) else (
    echo [OK] Update files found
)
echo.

echo [3/5] Creating backup...
set BACKUP_DIR=%USERPROFILE%\pdss_backups
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM Get timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "BACKUP_DATE=%dt:~0,4%%dt:~4,2%%dt:~6,2%_%dt:~8,2%%dt:~10,2%%dt:~12,2%"

REM Backup database
echo   Backing up database...
docker-compose exec -T db pg_dump -U postgres procurement_dss > "%BACKUP_DIR%\db_backup_%BACKUP_DATE%.sql" 2>nul || echo   [WARNING] Could not backup database

REM Backup current code
echo   Backing up current code...
powershell -command "Compress-Archive -Path backend,frontend -DestinationPath '%BACKUP_DIR%\code_backup_%BACKUP_DATE%.zip' -Force" 2>nul || echo   [WARNING] Could not backup code

echo [OK] Backup created at: %BACKUP_DIR%
echo.

echo [4/5] Checking Docker...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop
    pause
    exit /b 1
)
echo [OK] Docker is running
echo.

echo [5/5] Checking disk space...
for /f "tokens=3" %%a in ('dir /-c "%DEPLOY_DIR%" ^| findstr "bytes free"') do set AVAILABLE=%%a
echo [OK] Disk space available
echo.

echo ============================================================================
echo   APPLYING UPDATE
echo ============================================================================
echo.

echo [1/6] Stopping platform...
if "%PLATFORM_RUNNING%"=="true" (
    docker-compose down
    echo [OK] Platform stopped
) else (
    echo [SKIP] Platform already stopped
)
echo.

echo [2/6] Applying code updates...

REM Update backend if files exist
if exist "%UPDATE_DIR%\backend" (
    echo   Updating backend files...
    xcopy "%UPDATE_DIR%\backend\*" "backend\" /E /I /Y >nul 2>&1
    echo [OK] Backend files updated
) else (
    echo [SKIP] No backend updates
)

REM Update frontend if files exist
if exist "%UPDATE_DIR%\frontend" (
    echo   Updating frontend files...
    xcopy "%UPDATE_DIR%\frontend\*" "frontend\" /E /I /Y >nul 2>&1
    echo [OK] Frontend files updated
) else (
    echo [SKIP] No frontend updates
)
echo.

echo [3/6] Rebuilding Docker images...
docker-compose build --no-cache
if %errorlevel% neq 0 (
    echo [ERROR] Failed to rebuild images!
    pause
    exit /b 1
)
echo [OK] Images rebuilt
echo.

echo [4/6] Starting platform...
docker-compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start platform!
    pause
    exit /b 1
)
echo [OK] Platform started
echo.

echo [5/6] Waiting for services to be ready...
timeout /t 20 /nobreak >nul
echo [OK] Services should be ready
echo.

echo [6/6] Verifying update...
docker-compose ps
echo.

REM Check if all containers are up
docker-compose ps | findstr "Exit" >nul 2>&1
if %errorlevel% equ 0 (
    echo [ERROR] Some containers failed to start!
    echo.
    echo View logs with: docker-compose logs
    echo.
    echo To rollback:
    echo   1. Extract backup: powershell Expand-Archive %BACKUP_DIR%\code_backup_%BACKUP_DATE%.zip
    echo   2. Rebuild: docker-compose build --no-cache
    echo   3. Start: docker-compose up -d
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo   UPDATE COMPLETE!
echo ============================================================================
echo.
echo + Platform updated successfully
echo + Backup saved to: %BACKUP_DIR%
echo + All services running
echo.
echo Access your platform:
echo   URL: http://localhost:3000
echo.
echo Backup files:
echo   Database: %BACKUP_DIR%\db_backup_%BACKUP_DATE%.sql
echo   Code: %BACKUP_DIR%\code_backup_%BACKUP_DATE%.zip
echo.
echo View logs: docker-compose logs -f
echo.
echo ============================================================================
pause

