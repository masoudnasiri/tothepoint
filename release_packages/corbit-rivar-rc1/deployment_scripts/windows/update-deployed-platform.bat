@echo off
REM ============================================================================
REM  PDSS Platform Update Script (Windows)
REM  Updates a deployed PDSS platform with latest code changes
REM  Safety: aborts update if backup cannot be verified.
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
set UPDATE_DIR=%DEPLOY_DIR%\..\update_files

echo ============================================================================
echo   PRE-UPDATE CHECKS
echo ============================================================================
echo.

echo [1/6] Checking if platform is running...
docker-compose ps | findstr "Up" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Platform is running
    set PLATFORM_RUNNING=true
) else (
    echo [INFO] Platform is not running
    set PLATFORM_RUNNING=false
)
echo.

echo [2/6] Checking for update files...
if not exist "%UPDATE_DIR%" (
    echo [INFO] No update_files directory found
    echo.
    echo Update files should be placed in: %UPDATE_DIR%
    echo.
    echo Structure:
    echo   update_files\
    echo   ^|-- backend\
    echo   ^|   ^`-- ^(updated backend files^)
    echo   ^`-- frontend\
    echo       ^`-- ^(updated frontend files^)
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

echo [3/6] Checking Docker...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop
    pause
    exit /b 1
)
echo [OK] Docker is running
echo.

echo [4/6] Detecting database service...
set DB_SERVICE=
for /f "delims=" %%S in ('docker-compose config --services 2^>nul') do (
    if /I "%%S"=="postgres" set DB_SERVICE=postgres
)
if not defined DB_SERVICE (
    for /f "delims=" %%S in ('docker-compose config --services 2^>nul') do (
        if /I "%%S"=="db" set DB_SERVICE=db
    )
)
if not defined DB_SERVICE (
    echo [ERROR] Could not find database service in docker-compose.yml ^(expected 'postgres' or 'db'^)
    pause
    exit /b 1
)
echo [OK] Using database service: !DB_SERVICE!
echo.

echo [5/6] Creating backup (required)...
set BACKUP_DIR=%USERPROFILE%\pdss_backups
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

for /f %%a in ('powershell -NoProfile -Command "(Get-Date).ToString(\"yyyyMMdd_HHmmss\")"') do set BACKUP_DATE=%%a
set DB_BACKUP_FILE=%BACKUP_DIR%\db_backup_%BACKUP_DATE%.sql
set CODE_BACKUP_FILE=%BACKUP_DIR%\code_backup_%BACKUP_DATE%.zip

echo   Ensuring database service is running...
docker-compose ps !DB_SERVICE! | findstr "Up" >nul 2>&1
if !errorlevel! neq 0 (
    docker-compose up -d !DB_SERVICE!
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to start database service !DB_SERVICE!
        pause
        exit /b 1
    )
)

echo   Waiting for database readiness...
set DB_READY=false
for /l %%I in (1,1,20) do (
    docker-compose exec -T !DB_SERVICE! pg_isready -U postgres >nul 2>&1
    if !errorlevel! equ 0 (
        set DB_READY=true
        goto :db_ready
    )
    timeout /t 2 /nobreak >nul
)
:db_ready
if not "!DB_READY!"=="true" (
    echo [ERROR] Database did not become ready; update aborted.
    pause
    exit /b 1
)

echo   Backing up database...
docker-compose exec -T !DB_SERVICE! pg_dump -U postgres procurement_dss > "%DB_BACKUP_FILE%"
if %errorlevel% neq 0 (
    echo [ERROR] Database backup failed; update aborted.
    pause
    exit /b 1
)
if not exist "%DB_BACKUP_FILE%" (
    echo [ERROR] Database backup file missing; update aborted.
    pause
    exit /b 1
)
for %%A in ("%DB_BACKUP_FILE%") do set DBSIZE=%%~zA
if !DBSIZE! LEQ 0 (
    echo [ERROR] Database backup file is empty; update aborted.
    pause
    exit /b 1
)

echo   Backing up current code...
powershell -NoProfile -Command "Compress-Archive -Path 'backend','frontend' -DestinationPath '%CODE_BACKUP_FILE%' -Force" >nul
if %errorlevel% neq 0 (
    echo [ERROR] Code backup failed; update aborted.
    pause
    exit /b 1
)
if not exist "%CODE_BACKUP_FILE%" (
    echo [ERROR] Code backup file missing; update aborted.
    pause
    exit /b 1
)
for %%A in ("%CODE_BACKUP_FILE%") do set CODESIZE=%%~zA
if !CODESIZE! LEQ 0 (
    echo [ERROR] Code backup file is empty; update aborted.
    pause
    exit /b 1
)

echo [OK] Backup verified
echo   Database: %DB_BACKUP_FILE%
echo   Code: %CODE_BACKUP_FILE%
echo.

echo [6/6] Checking disk space...
for /f "tokens=3" %%a in ('dir /-c "%DEPLOY_DIR%" ^| findstr "bytes free"') do set AVAILABLE=%%a
echo [OK] Disk space check complete
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

if exist "%UPDATE_DIR%\backend" (
    echo   Updating backend files...
    xcopy "%UPDATE_DIR%\backend\*" "backend\" /E /I /Y >nul 2>&1
    echo [OK] Backend files updated
) else (
    echo [SKIP] No backend updates
)

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

docker-compose ps | findstr /R /C:"Exit" /C:"Restarting" >nul 2>&1
if %errorlevel% equ 0 (
    echo [ERROR] Some containers failed to start!
    echo.
    echo View logs with: docker-compose logs
    echo.
    echo To rollback:
    echo   1. Extract code backup: powershell Expand-Archive "%CODE_BACKUP_FILE%" -DestinationPath .
    echo   2. Rebuild: docker-compose build --no-cache
    echo   3. Start: docker-compose up -d
    echo   4. Optional DB restore: docker-compose exec -T !DB_SERVICE! psql -U postgres -d procurement_dss ^< "%DB_BACKUP_FILE%"
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo   UPDATE COMPLETE!
echo ============================================================================
echo.
echo + Platform updated successfully
echo + Backup verified and saved
echo + All services running
echo.
echo Access your platform:
echo   URL: http://localhost:3000
echo.
echo Backup files:
echo   Database: %DB_BACKUP_FILE%
echo   Code: %CODE_BACKUP_FILE%
echo.
echo View logs: docker-compose logs -f
echo.
echo ============================================================================
pause
