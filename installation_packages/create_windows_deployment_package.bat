@echo off
REM ============================================================================
REM  PDSS - Windows Deployment Package Creator (Improved)
REM  Creates a complete Windows deployment package with all necessary files
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo   PDSS Windows Deployment Package Creator
echo ============================================================================
echo.

set VERSION=1.0.0
for /f "tokens=*" %%a in ('powershell -command "Get-Date -Format 'yyyyMMddHHmm'"') do set TIMESTAMP=%%a
for /f "tokens=*" %%a in ('powershell -command "Get-Date -Format 'yyyy-MM-dd HH:mm'"') do set TIMESTAMP_FRIENDLY=%%a

set PACKAGE_NAME=PDSS_Windows_v%VERSION%
set OUTPUT_DIR=%PACKAGE_NAME%_%TIMESTAMP%
set ZIP_NAME=%PACKAGE_NAME%_%TIMESTAMP%.zip

echo [INFO] Version: %VERSION%
echo [INFO] Build Date: %TIMESTAMP_FRIENDLY%
echo [INFO] Package: %OUTPUT_DIR%
echo.

echo ============================================================================
echo   STAGE 1: VALIDATION
echo ============================================================================
echo.

echo [1/3] Checking project structure...
if not exist "..\backend" (
    echo [ERROR] Backend directory not found!
    pause
    exit /b 1
)
if not exist "..\frontend" (
    echo [ERROR] Frontend directory not found!
    pause
    exit /b 1
)
if not exist "..\docker-compose.yml" (
    echo [ERROR] docker-compose.yml not found!
    pause
    exit /b 1
)
echo [OK] Project structure validated
echo.

echo [2/3] Checking required files...
if not exist "..\backend\requirements.txt" (
    echo [ERROR] Backend requirements.txt not found!
    pause
    exit /b 1
)
if not exist "..\frontend\package.json" (
    echo [ERROR] Frontend package.json not found!
    pause
    exit /b 1
)
echo [OK] Required files found
echo.

echo [3/3] Creating package directory...
if exist "%OUTPUT_DIR%" rd /s /q "%OUTPUT_DIR%"
mkdir "%OUTPUT_DIR%" 2>nul
mkdir "%OUTPUT_DIR%\backend" 2>nul
mkdir "%OUTPUT_DIR%\frontend" 2>nul
mkdir "%OUTPUT_DIR%\docs" 2>nul
mkdir "%OUTPUT_DIR%\scripts" 2>nul
mkdir "%OUTPUT_DIR%\config" 2>nul
echo [OK] Directory structure created
echo.

echo ============================================================================
echo   STAGE 2: COPYING FILES
echo ============================================================================
echo.

echo [1/4] Copying backend application...
xcopy "..\backend\*" "%OUTPUT_DIR%\backend\" /E /I /Q /Y >nul 2>&1
for /d /r "%OUTPUT_DIR%\backend" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /r "%OUTPUT_DIR%\backend" %%f in (*.pyc) do @if exist "%%f" del "%%f" 2>nul
echo [OK] Backend copied and cleaned
echo.

echo [2/4] Copying frontend application...
xcopy "..\frontend\src" "%OUTPUT_DIR%\frontend\src\" /E /I /Q /Y >nul 2>&1
xcopy "..\frontend\public" "%OUTPUT_DIR%\frontend\public\" /E /I /Q /Y >nul 2>&1
copy "..\frontend\package.json" "%OUTPUT_DIR%\frontend\" >nul 2>&1
copy "..\frontend\package-lock.json" "%OUTPUT_DIR%\frontend\" >nul 2>&1
copy "..\frontend\tsconfig.json" "%OUTPUT_DIR%\frontend\" >nul 2>&1
copy "..\frontend\Dockerfile" "%OUTPUT_DIR%\frontend\" >nul 2>&1
if exist "%OUTPUT_DIR%\frontend\node_modules" rd /s /q "%OUTPUT_DIR%\frontend\node_modules" 2>nul
echo [OK] Frontend copied
echo.

echo [3/4] Copying Docker configuration...
copy "..\docker-compose.yml" "%OUTPUT_DIR%\" >nul 2>&1
copy "..\backend\Dockerfile" "%OUTPUT_DIR%\backend\" >nul 2>&1
echo [OK] Docker files copied
echo.

echo [4/4] Copying documentation and config...
if exist "..\README.md" copy "..\README.md" "%OUTPUT_DIR%\docs\README.md" >nul 2>&1
if exist "config_template.env" (
    copy "config_template.env" "%OUTPUT_DIR%\config\.env.example" >nul 2>&1
) else (
    (
    echo # PDSS Configuration
    echo DATABASE_URL=postgresql://postgres:postgres@db:5432/procurement_dss
    echo SECRET_KEY=change-this-secret-key-in-production
    echo ALLOWED_ORIGINS=http://localhost:3000
    echo POSTGRES_USER=postgres
    echo POSTGRES_PASSWORD=postgres123
    echo POSTGRES_DB=procurement_dss
    ) > "%OUTPUT_DIR%\config\.env.example"
)
echo [OK] Documentation and config copied
echo.

echo ============================================================================
echo   STAGE 3: CREATING INSTALLER
echo ============================================================================
echo.

echo [1/2] Creating Windows installer script...
(
echo @echo off
echo REM ========================================================================
echo REM  PDSS Windows Installer v%VERSION%
echo REM ========================================================================
echo.
echo echo.
echo echo ========================================================================
echo echo   Procurement Decision Support System ^(PDSS^)
echo echo   Windows Installer v%VERSION%
echo echo ========================================================================
echo echo.
echo.
echo net session ^>nul 2^>^&1
echo if %%errorLevel%% neq 0 ^(
echo     echo [ERROR] Administrator privileges required!
echo     echo Please right-click and select "Run as Administrator"
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo [1/8] Checking prerequisites...
echo docker --version ^>nul 2^>^&1
echo if %%errorLevel%% neq 0 ^(
echo     echo [ERROR] Docker Desktop is not installed!
echo     echo Download from: https://www.docker.com/products/docker-desktop
echo     pause
echo     exit /b 1
echo ^)
echo echo [OK] Docker Desktop found
echo.
echo docker ps ^>nul 2^>^&1
echo if %%errorLevel%% neq 0 ^(
echo     echo [ERROR] Docker Desktop is not running!
echo     pause
echo     exit /b 1
echo ^)
echo echo [OK] Docker is running
echo echo.
echo.
echo echo [2/8] Configuring environment...
echo if not exist ".env" ^(
echo     copy "config\.env.example" ".env" ^>nul 2^>^&1
echo     echo [OK] Configuration file created
echo ^) else ^(
echo     echo [OK] Using existing configuration
echo ^)
echo echo.
echo.
echo echo [3/8] Stopping any existing containers...
echo docker-compose down ^>nul 2^>^&1
echo echo [OK] Cleanup complete
echo echo.
echo.
echo echo [4/8] Building Docker images...
echo echo This may take 5-10 minutes...
echo docker-compose build
echo if %%errorLevel%% neq 0 ^(
echo     echo [ERROR] Failed to build Docker images!
echo     pause
echo     exit /b 1
echo ^)
echo echo [OK] Images built successfully
echo echo.
echo.
echo echo [5/8] Starting database...
echo docker-compose up -d db
echo timeout /t 15 /nobreak ^>nul
echo echo [OK] Database started
echo echo.
echo.
echo echo [6/8] Starting backend service...
echo docker-compose up -d backend
echo timeout /t 20 /nobreak ^>nul
echo echo [OK] Backend started
echo echo.
echo.
echo echo [7/8] Starting frontend service...
echo docker-compose up -d frontend
echo timeout /t 25 /nobreak ^>nul
echo echo [OK] Frontend started
echo echo.
echo.
echo echo [8/8] Verifying installation...
echo docker-compose ps
echo echo.
echo.
echo echo ========================================================================
echo echo   INSTALLATION COMPLETE!
echo echo ========================================================================
echo echo.
echo echo Access URL: http://localhost:3000
echo echo.
echo echo Default Login Credentials:
echo echo   Admin: admin / admin123
echo echo   Finance: finance1 / finance123
echo echo   PM: pm1 / pm123
echo echo   Procurement: proc1 / proc123
echo echo.
echo timeout /t 3 /nobreak ^>nul
echo start http://localhost:3000
echo pause
) > "%OUTPUT_DIR%\INSTALL.bat"
echo [OK] Installer created
echo.

echo [2/2] Creating management scripts...
(
echo @echo off
echo cd /d "%%~dp0\.."
echo docker-compose up -d
echo timeout /t 5 /nobreak ^>nul
echo start http://localhost:3000
echo echo PDSS started successfully!
echo pause
) > "%OUTPUT_DIR%\scripts\start.bat"

(
echo @echo off
echo cd /d "%%~dp0\.."
echo docker-compose down
echo echo PDSS stopped successfully!
echo pause
) > "%OUTPUT_DIR%\scripts\stop.bat"

(
echo @echo off
echo cd /d "%%~dp0\.."
echo echo ========================================================================
echo echo   PDSS System Status
echo echo ========================================================================
echo docker-compose ps
echo pause
) > "%OUTPUT_DIR%\scripts\status.bat"

(
echo @echo off
echo cd /d "%%~dp0\.."
echo echo Restarting PDSS...
echo docker-compose restart
echo echo PDSS restarted successfully!
echo pause
) > "%OUTPUT_DIR%\scripts\restart.bat"

echo [OK] Management scripts created
echo.

echo ============================================================================
echo   STAGE 4: FINALIZATION
echo ============================================================================
echo.

echo [1/3] Creating README...
(
echo ========================================================================
echo   PROCUREMENT DECISION SUPPORT SYSTEM ^(PDSS^)
echo   Windows Deployment Package v%VERSION%
echo ========================================================================
echo.
echo BUILD INFORMATION:
echo   Version: %VERSION%
echo   Build Date: %TIMESTAMP_FRIENDLY%
echo.
echo SYSTEM REQUIREMENTS:
echo   - Windows 10/11 or Windows Server 2019+
echo   - Docker Desktop for Windows
echo   - 4GB RAM minimum ^(8GB recommended^)
echo   - 10GB free disk space
echo.
echo INSTALLATION:
echo   1. Ensure Docker Desktop is installed and running
echo   2. Right-click INSTALL.bat and select "Run as Administrator"
echo   3. Follow the on-screen instructions
echo   4. Access: http://localhost:3000
echo.
echo MANAGEMENT SCRIPTS:
echo   scripts\start.bat      - Start PDSS
echo   scripts\stop.bat       - Stop PDSS
echo   scripts\status.bat     - Check status
echo   scripts\restart.bat     - Restart PDSS
echo.
echo DEFAULT CREDENTIALS:
echo   Admin: admin / admin123
echo   Finance: finance1 / finance123
echo   PM: pm1 / pm123
echo   Procurement: proc1 / proc123
echo.
echo ========================================================================
) > "%OUTPUT_DIR%\README.txt"
echo [OK] README created
echo.

echo [2/3] Creating ZIP archive...
powershell -command "Compress-Archive -Path '%OUTPUT_DIR%\*' -DestinationPath '%ZIP_NAME%' -Force" 2>nul
if exist "%ZIP_NAME%" (
    echo [OK] ZIP archive created: %ZIP_NAME%
) else (
    echo [WARNING] Failed to create ZIP archive
)
echo.

echo [3/3] Finalizing...
echo [OK] Package creation complete
echo.

echo ============================================================================
echo   BUILD COMPLETE!
echo ============================================================================
echo.
echo Package: %OUTPUT_DIR%
echo ZIP: %ZIP_NAME%
echo.
echo Next Steps:
echo   1. Transfer package to Windows server
echo   2. Extract if using ZIP
echo   3. Right-click INSTALL.bat and select "Run as Administrator"
echo.
pause

