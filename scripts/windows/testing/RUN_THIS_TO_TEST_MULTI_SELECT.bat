@echo off
REM Quick test script for Multi-Select Revert feature

echo ================================================================
echo   MULTI-SELECT REVERT - Quick Test Script
echo ================================================================
echo.
echo This script will help you test the new multi-select revert feature
echo.
echo FIXES INCLUDED:
echo   1. Grid import error - FIXED
echo   2. Multi-select checkboxes - ADDED
echo   3. Bulk revert functionality - ADDED
echo.
echo ================================================================
echo.

REM Check if system is running
docker-compose ps | findstr "Up" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] System is running!
    echo.
) else (
    echo [!] System is not running. Starting now...
    echo.
    docker-compose up -d
    timeout /t 5 /nobreak >nul
)

echo ================================================================
echo   TEST INSTRUCTIONS
echo ================================================================
echo.
echo 1. Login Credentials:
echo    - Username: pm1
echo    - Password: password123
echo.
echo 2. Navigate to: Finalized Decisions
echo.
echo 3. Test Steps:
echo    [Step 1] Verify page loads without errors
echo    [Step 2] See checkboxes next to LOCKED decisions
echo    [Step 3] Click 2-3 checkboxes
echo    [Step 4] Verify rows turn blue when selected
echo    [Step 5] Verify toolbar appears showing "X item(s) selected"
echo    [Step 6] Click "Revert Selected" button
echo    [Step 7] Confirm the dialog
echo    [Step 8] Verify success message appears
echo    [Step 9] Verify decisions changed to REVERTED
echo.
echo ================================================================
echo   FEATURES TO TEST
echo ================================================================
echo.
echo [x] Individual Selection - Click checkboxes one by one
echo [x] Select All - Click header checkbox to select all LOCKED
echo [x] Bulk Revert - Select multiple, click "Revert Selected"
echo [x] Visual Feedback - Selected rows turn light blue
echo [x] Smart Disable - Only LOCKED items are selectable
echo.
echo ================================================================
echo.

set /p OPEN="Open browser now? (yes/no): "

if "%OPEN%"=="yes" (
    echo.
    echo Opening browser...
    start http://localhost:3000
    echo.
    echo Browser opened!
    echo Navigate to "Finalized Decisions" and start testing!
) else (
    echo.
    echo Manual access:
    echo Open: http://localhost:3000
    echo Navigate to: Finalized Decisions
)

echo.
echo ================================================================
echo   DOCUMENTATION
echo ================================================================
echo.
echo Read these files for detailed information:
echo   1. 🎉_MULTI_SELECT_REVERT_COMPLETE.md - Quick summary
echo   2. MULTI_SELECT_REVERT_GUIDE.md - Complete technical guide
echo.
echo ================================================================
echo   SYSTEM STATUS
echo ================================================================
echo.

docker-compose ps

echo.
echo ================================================================
echo   Ready to test! Good luck!
echo ================================================================
echo.

pause

