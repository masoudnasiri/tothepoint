@echo off
echo ============================================================================
echo PDSS DATA RESET AND RESEED
echo ============================================================================
echo.
echo This will wipe all operational data and create fresh test data with:
echo  - USD and Iranian Rial (IRR) currencies
echo  - Realistic IT equipment projects
echo  - Mixed USD/IRR pricing for procurement options
echo.
echo WARNING: This will delete all existing data except the admin user!
echo.
pause

echo.
echo Running reset script...
echo.

python backend\reset_and_reseed_data.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================================
    echo SUCCESS! Data has been reset and reseeded.
    echo ============================================================================
    echo.
    echo Next step: Restart the backend
    echo   docker-compose restart backend
    echo.
    pause
) else (
    echo.
    echo ============================================================================
    echo ERROR! Something went wrong.
    echo ============================================================================
    echo.
    echo Please check the error message above.
    echo.
    pause
)

