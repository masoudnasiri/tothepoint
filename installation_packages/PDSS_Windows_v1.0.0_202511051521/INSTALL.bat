@echo off
REM ========================================================================
REM  PDSS Windows Installer v1.0.0
REM ========================================================================

echo.
echo ========================================================================
echo   Procurement Decision Support System (PDSS)
echo   Windows Installer v1.0.0
echo ========================================================================
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Administrator privileges required!
    echo Please right-click and select "Run as Administrator"
    pause
    exit /b 1
)

echo [1/8] Checking prerequisites...
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Docker Desktop is not installed!
    echo Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo [OK] Docker Desktop found

docker ps >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Docker Desktop is not running!
    pause
    exit /b 1
)
echo [OK] Docker is running
echo.

echo [2/8] Configuring environment...
if not exist ".env" (
    copy "config\.env.example" ".env" >nul 2>&1
    echo [OK] Configuration file created
) else (
    echo [OK] Using existing configuration
)
echo.

echo [3/8] Stopping any existing containers...
docker-compose down >nul 2>&1
echo [OK] Cleanup complete
echo.

echo [4/8] Building Docker images...
echo This may take 5-10 minutes...
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
timeout /t 15 /nobreak >nul
echo [OK] Database started
echo.

echo [6/8] Starting backend service...
docker-compose up -d backend
timeout /t 20 /nobreak >nul
echo [OK] Backend started
echo.

echo [7/8] Starting frontend service...
docker-compose up -d frontend
timeout /t 25 /nobreak >nul
echo [OK] Frontend started
echo.

echo [8/8] Verifying installation...
docker-compose ps
echo.

echo ========================================================================
echo   INSTALLATION COMPLETE!
echo ========================================================================
echo.
echo Access URL: http://localhost:3000
echo.
echo Default Login Credentials:
echo   Admin: admin / admin123
echo   Finance: finance1 / finance123
echo   PM: pm1 / pm123
echo   Procurement: proc1 / proc123
echo.
echo IMPORTANT: Change default passwords after first login!
echo.
timeout /t 3 /nobreak >nul
start http://localhost:3000
pause
