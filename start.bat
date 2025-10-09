@echo off
REM Procurement DSS Startup Script for Windows
REM SAFE VERSION - Preserves all data

echo ========================================
echo  Procurement DSS - Enhanced OR-Tools
echo  SAFE Start (Data Preserved)
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo X Error: Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo X Error: docker-compose is not available. Please ensure Docker Desktop is properly installed.
    pause
    exit /b 1
)

echo + Docker is running
echo.

REM Check if containers are already running
docker-compose ps | findstr "Up" >nul 2>&1
if %errorlevel% equ 0 (
    echo ! Containers are already running
    echo.
    docker-compose ps
    echo.
    echo Do you want to restart? (This preserves all data)
    set /p RESTART="Restart services? (yes/no): "
    if not "%RESTART%"=="yes" (
        echo.
        echo Services already running. Opening browser...
        timeout /t 2 >nul
        start http://localhost:3000
        pause
        exit /b 0
    )
    echo.
    echo Restarting services (data preserved)...
    docker-compose restart
) else (
    echo Starting services (data preserved)...
    docker-compose up -d
)

REM Wait for services to be ready
echo.
echo Waiting for services to initialize...
timeout /t 10 /nobreak >nul

REM Check if services are running
echo.
echo Service Status:
docker-compose ps

echo.
echo ========================================
echo   Procurement DSS is Running!
echo ========================================
echo.
echo Access Points:
echo   Frontend:         http://localhost:3000
echo   Backend API:      http://localhost:8000
echo   API Docs:         http://localhost:8000/docs
echo   Advanced Optim:   http://localhost:3000/optimization-enhanced
echo.
echo Login Credentials:
echo   Admin:       admin / admin123        (Full Access)
echo   Finance:     finance1 / finance123   (Full Access)
echo   PM:          pm1 / pm123             (Revenue Only)
echo   Procurement: proc1 / proc123         (Payments Only)
echo.
echo Useful Commands:
echo   View logs:      docker-compose logs -f backend
echo   Stop system:    stop.bat
echo   Backup data:    backup_database.bat
echo   Check status:   docker-compose ps
echo.
echo Opening browser in 3 seconds...
timeout /t 3 >nul
start http://localhost:3000
echo.
pause
