@echo off
REM Windows Setup Script for Procurement DSS

echo ========================================
echo   Procurement DSS Windows Setup
echo ========================================
echo.

REM Check if Docker Desktop is installed
echo Checking Docker Desktop installation...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Docker Desktop is not installed or not in PATH
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop
    echo.
    echo After installation:
    echo 1. Start Docker Desktop
    echo 2. Wait for it to fully start (green icon in system tray)
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo Docker Desktop found: 
docker --version

REM Check if Docker is running
echo.
echo Checking if Docker is running...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Docker is not running
    echo.
    echo Please:
    echo 1. Start Docker Desktop
    echo 2. Wait for it to fully start (green icon in system tray)
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo Docker is running successfully!

REM Check available ports
echo.
echo Checking if required ports are available...
netstat -an | findstr ":3000" >nul
if %errorlevel% equ 0 (
    echo WARNING: Port 3000 is already in use
)

netstat -an | findstr ":8000" >nul
if %errorlevel% equ 0 (
    echo WARNING: Port 8000 is already in use
)

netstat -an | findstr ":5432" >nul
if %errorlevel% equ 0 (
    echo WARNING: Port 5432 is already in use
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Your system is ready to run Procurement DSS
echo.
echo To start the system, run: start.bat
echo To stop the system, run: stop.bat
echo.
echo If you encounter any issues:
echo 1. Make sure Docker Desktop is running
echo 2. Check that ports 3000, 8000, 5432 are available
echo 3. Run 'docker-compose logs' to check for errors
echo.
pause
