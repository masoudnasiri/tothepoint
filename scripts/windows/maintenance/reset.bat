@echo off
REM Reset Procurement DSS (removes all data)

echo ========================================
echo   Reset Procurement DSS
echo ========================================
echo.
echo WARNING: This will remove all data including:
echo - Database data
echo - User accounts
echo - Projects and items
echo - Procurement options
echo - Budget data
echo - Optimization results
echo.

set /p confirm="Are you sure you want to reset? (y/N): "
if /i not "%confirm%"=="y" (
    echo Reset cancelled.
    pause
    exit /b 0
)

echo.
echo Stopping and removing all containers and data...
docker-compose down -v

echo.
echo Removing Docker images (optional)...
set /p remove_images="Remove Docker images to free space? (y/N): "
if /i "%remove_images%"=="y" (
    docker-compose down --rmi all
)

echo.
echo ========================================
echo   Reset Complete!
echo ========================================
echo.
echo All data has been removed.
echo To start fresh, run: start.bat
echo.
pause
