@echo off
cd /d "%~dp0\.."
echo ========================================================================
echo   PDSS Uninstaller
echo ========================================================================
echo.
echo WARNING: This will remove all PDSS containers and data
echo.
set /p CONFIRM="Are you sure? Type 'YES' to confirm: "
if not "%CONFIRM%"=="YES" (
    echo Uninstall cancelled.
    pause
    exit /b 0
)
echo.
echo Stopping and removing containers...
docker-compose down -v
echo.
echo PDSS has been uninstalled.
echo Note: Installation files are still present.
echo You can safely delete this folder to complete removal.
echo.
pause
