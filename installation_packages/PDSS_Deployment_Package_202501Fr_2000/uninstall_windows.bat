@echo off
REM ========================================================================
REM  Procurement Decision Support System - Windows Uninstaller
REM ========================================================================

echo.
echo ========================================================================
echo   PROCUREMENT DECISION SUPPORT SYSTEM
echo   Windows Uninstallation Wizard
echo ========================================================================
echo.
echo WARNING: This will remove all data and containers!
echo.
set /p CONFIRM="Are you sure you want to uninstall? (yes/no): "

if /i not "%CONFIRM%"=="yes" (
    echo Uninstallation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/5] Stopping all containers...
docker-compose down
echo [OK] Containers stopped
echo.

echo [2/5] Removing volumes (including database)...
docker-compose down -v
echo [OK] Volumes removed
echo.

echo [3/5] Removing Docker images...
set /p REMOVE_IMAGES="Remove Docker images? (yes/no): "
if /i "%REMOVE_IMAGES%"=="yes" (
    docker rmi cahs_flow_project-backend cahs_flow_project-frontend >nul 2>&1
    echo [OK] Images removed
) else (
    echo [SKIP] Images kept
)
echo.

echo [4/5] Removing desktop shortcuts...
del "%USERPROFILE%\Desktop\Start PDSS.bat" >nul 2>&1
del "%USERPROFILE%\Desktop\Stop PDSS.bat" >nul 2>&1
echo [OK] Shortcuts removed
echo.

echo [5/5] Cleanup complete
echo.

echo ========================================================================
echo   UNINSTALLATION COMPLETE!
echo ========================================================================
echo.
echo The platform has been removed from your system.
echo.
echo To completely clean up Docker:
echo   docker system prune -a
echo.
echo Note: The installation files are still in this folder.
echo You can delete this folder manually if no longer needed.
echo.
pause

