@echo off
REM Wipe calculated data (optimization results, decisions, cashflow)
REM Keeps: Projects, Procurement Options, Budget Data

echo ================================================================
echo   WIPE CALCULATED DATA
echo ================================================================
echo.
echo This will DELETE:
echo   - All optimization runs and results
echo   - All finalized decisions
echo   - All cashflow events
echo.
echo This will KEEP:
echo   - Users
echo   - Projects, Project Items, Delivery Options
echo   - Procurement Options
echo   - Budget Data
echo   - Decision Factor Weights
echo.
echo This is useful when you want to:
echo   - Start fresh with new optimizations
echo   - Keep your project and procurement setup
echo   - Clear old results without losing base data
echo.
echo ================================================================
echo.

set /p CONFIRM1="Type 'WIPE RESULTS' to confirm (case-sensitive): "

if not "%CONFIRM1%"=="WIPE RESULTS" (
    echo.
    echo ✅ Cancelled - No data deleted
    pause
    exit /b 0
)

echo.
echo ⚠️  ARE YOU SURE?
echo This will delete all optimization results and decisions!
echo.
set /p CONFIRM2="Type 'YES' to proceed: "

if not "%CONFIRM2%"=="YES" (
    echo.
    echo ✅ Cancelled - No data deleted
    pause
    exit /b 0
)

echo.
echo ================================================================
echo   Wiping Calculated Data...
echo ================================================================
echo.

REM Run the wipe script inside backend container
docker-compose exec backend python wipe_calculated_data.py

if %errorlevel% equ 0 (
    echo.
    echo ================================================================
    echo   ✅ CALCULATED DATA WIPED SUCCESSFULLY!
    echo ================================================================
    echo.
    echo Deleted:
    echo   ✅ Optimization runs and results
    echo   ✅ Finalized decisions
    echo   ✅ Cashflow events
    echo.
    echo Kept:
    echo   ✅ Users
    echo   ✅ Projects, Items, Delivery Options
    echo   ✅ Procurement Options
    echo   ✅ Budget Data
    echo.
    echo You can now run fresh optimizations!
    echo.
) else (
    echo.
    echo ❌ Failed to wipe data
    echo   Check error messages above
)

pause

