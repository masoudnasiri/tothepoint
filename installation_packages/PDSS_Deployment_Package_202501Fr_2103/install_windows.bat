@echo off
REM ========================================================================
REM  Procurement Decision Support System - Windows Installer
REM  One-Click Installation for Windows
REM ========================================================================

echo.
echo ========================================================================
echo   PROCUREMENT DECISION SUPPORT SYSTEM
echo   Windows Installation Wizard
echo ========================================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This installer requires Administrator privileges!
    echo Please right-click and select "Run as Administrator"
    pause
    exit /b 1
)

echo [1/8] Checking prerequisites...
echo.

REM Check Docker Desktop
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Docker Desktop is not installed!
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop
    echo.
    echo After installation:
    echo 1. Restart your computer
    echo 2. Start Docker Desktop
    echo 3. Run this installer again
    pause
    exit /b 1
)

echo [OK] Docker Desktop found
docker-compose --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Docker Compose is not installed!
    pause
    exit /b 1
)
echo [OK] Docker Compose found
echo.

REM Check if Docker is running
docker ps >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Docker Desktop is not running!
    echo.
    echo Please start Docker Desktop and wait for it to be ready.
    echo Then run this installer again.
    pause
    exit /b 1
)
echo [OK] Docker is running
echo.

echo [2/8] Stopping any existing containers...
docker-compose down >nul 2>&1
echo [OK] Cleanup complete
echo.

echo [3/8] Initializing database schema...
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env >nul 2>&1
)
echo [OK] Configuration ready
echo.

echo [4/8] Building Docker images...
echo This may take 5-10 minutes on first installation...
docker-compose build
if %errorLevel% neq 0 (
    echo [ERROR] Failed to build Docker images!
    pause
    exit /b 1
)
echo [OK] Images built successfully
echo.

echo [5/8] Starting database...
docker-compose up -d db
if %errorLevel% neq 0 (
    echo [ERROR] Failed to start database!
    pause
    exit /b 1
)
echo [OK] Database started
echo Waiting for database to be ready...
timeout /t 10 /nobreak >nul
echo.

echo [6/8] Starting backend service...
docker-compose up -d backend
if %errorLevel% neq 0 (
    echo [ERROR] Failed to start backend!
    pause
    exit /b 1
)
echo [OK] Backend started
echo Waiting for backend to be ready...
timeout /t 15 /nobreak >nul
echo.

echo [7/8] Starting frontend service...
docker-compose up -d frontend
if %errorLevel% neq 0 (
    echo [ERROR] Failed to start frontend!
    pause
    exit /b 1
)
echo [OK] Frontend started
echo Waiting for frontend to be ready...
timeout /t 20 /nobreak >nul
echo.

echo [7/8] Verifying installation...
docker-compose ps
echo.

echo [8/8] Creating desktop shortcuts...
REM Create start shortcut
echo @echo off > "%USERPROFILE%\Desktop\Start PDSS.bat"
echo cd /d "%CD%" >> "%USERPROFILE%\Desktop\Start PDSS.bat"
echo docker-compose up -d >> "%USERPROFILE%\Desktop\Start PDSS.bat"
echo timeout /t 5 /nobreak ^>nul >> "%USERPROFILE%\Desktop\Start PDSS.bat"
echo start http://localhost:3000 >> "%USERPROFILE%\Desktop\Start PDSS.bat"
echo echo Platform started! Opening browser... >> "%USERPROFILE%\Desktop\Start PDSS.bat"
echo pause >> "%USERPROFILE%\Desktop\Start PDSS.bat"

REM Create stop shortcut
echo @echo off > "%USERPROFILE%\Desktop\Stop PDSS.bat"
echo cd /d "%CD%" >> "%USERPROFILE%\Desktop\Stop PDSS.bat"
echo docker-compose down >> "%USERPROFILE%\Desktop\Stop PDSS.bat"
echo echo Platform stopped! >> "%USERPROFILE%\Desktop\Stop PDSS.bat"
echo pause >> "%USERPROFILE%\Desktop\Stop PDSS.bat"

echo [OK] Desktop shortcuts created
echo.

echo ========================================================================
echo   INSTALLATION COMPLETE!
echo ========================================================================
echo.
echo The platform is now running at: http://localhost:3000
echo.
echo Default Login Credentials:
echo   Admin:       Username: admin      Password: admin123
echo   Finance:     Username: finance1   Password: finance123
echo   PM:          Username: pm1        Password: pm123
echo   Procurement: Username: proc1      Password: proc123
echo.
echo Desktop Shortcuts Created:
echo   - Start PDSS.bat  (Start the platform)
echo   - Stop PDSS.bat   (Stop the platform)
echo.
echo Opening browser in 5 seconds...
timeout /t 5 /nobreak >nul
start http://localhost:3000
echo.
echo ========================================================================
pause

