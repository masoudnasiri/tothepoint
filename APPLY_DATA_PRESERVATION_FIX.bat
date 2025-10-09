@echo off
REM Apply Data Preservation Fix - Rebuild backend with safe seeding

echo ================================================================
echo   🔥 DATA PRESERVATION FIX
echo ================================================================
echo.
echo This will apply CRITICAL FIXES that prevent data loss and financial corruption.
echo.
echo WHAT THIS DOES:
echo   1. Stops all services (data in volume is safe)
echo   2. Rebuilds backend with new code
echo   3. Restarts all services
echo   4. Your database data is PRESERVED!
echo.
echo FIXES APPLIED:
echo   FIX #1: Data Preservation
echo   - Backend now checks if database has data
echo   - Only seeds mock data if database is EMPTY
echo   - Your real data is never deleted on restart
echo.
echo   FIX #2: Cashflow Events on Revert
echo   - Cashflow events are cancelled when decisions reverted
echo   - No double-counting in financial reports
echo   - Export excludes cancelled events
echo.
echo This is SAFE - all data in the database volume is preserved!
echo.
echo ================================================================
echo.

set /p CONFIRM="Apply fix now? (yes/no): "

if not "%CONFIRM%"=="yes" (
    echo.
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo ================================================================
echo   Applying Fix...
echo ================================================================
echo.

echo Step 1/3: Stopping services...
docker-compose down

if %errorlevel% neq 0 (
    echo ❌ Failed to stop services
    pause
    exit /b 1
)

echo ✅ Services stopped (data preserved in volume)
echo.

echo Step 2/3: Rebuilding backend with fix...
docker-compose build backend

if %errorlevel% neq 0 (
    echo ❌ Failed to rebuild backend
    pause
    exit /b 1
)

echo ✅ Backend rebuilt with data preservation fix
echo.

echo Step 3/3: Starting services...
docker-compose up -d

if %errorlevel% neq 0 (
    echo ❌ Failed to start services
    pause
    exit /b 1
)

echo ✅ Services started
echo.

echo Waiting for services to initialize...
timeout /t 10 /nobreak >nul

echo.
echo ================================================================
echo   ✅ FIX APPLIED SUCCESSFULLY!
echo ================================================================
echo.
echo Checking if data was preserved...
echo.

docker-compose logs backend | findstr /C:"Database already has data" /C:"Database is empty"

echo.
echo ================================================================
echo   VERIFICATION
echo ================================================================
echo.
echo You should see one of these messages above:
echo.
echo   ✅ "Database already has data - SKIPPING seeding"
echo      ^ This means your data was preserved!
echo.
echo   ✅ "Database is empty - Starting initial seeding"
echo      ^ This is normal for first-time setup
echo.
echo ================================================================
echo   WHAT'S CHANGED
echo ================================================================
echo.
echo BEFORE FIX:
echo   ❌ Every restart deleted all data
echo   ❌ Platform always reset to mock data
echo.
echo AFTER FIX:
echo   ✅ Restarts preserve all data
echo   ✅ Only seeds when database is empty
echo   ✅ Safe to restart anytime!
echo.
echo ================================================================
echo   TEST THE FIX
echo ================================================================
echo.
echo 1. Login to platform: http://localhost:3000
echo 2. Create a test project or decision
echo 3. Restart: docker-compose restart
echo 4. Login again
echo 5. Verify your data still exists ✅
echo.
echo ================================================================
echo   USEFUL COMMANDS
echo ================================================================
echo.
echo Safe restarts (data preserved):
echo   start.bat                  - Start/restart system
echo   stop.bat                   - Stop system
echo   docker-compose restart     - Quick restart
echo.
echo Backup/Restore:
echo   backup_database.bat        - Create backup
echo   restore_database.bat       - Restore from backup
echo.
echo Force reset (DESTRUCTIVE):
echo   force_reseed_database.bat  - Delete all & reseed
echo.
echo ================================================================
echo.
echo System is ready! Opening browser...
timeout /t 3 >nul
start http://localhost:3000
echo.
pause

