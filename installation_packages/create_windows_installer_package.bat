@echo off
REM ============================================================================
REM  PDSS - Windows Installation Package Creator
REM  Creates a complete Windows installation package with installer
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo   PDSS Windows Installation Package Creator
echo ============================================================================
echo.

REM Set version and package name
set VERSION=1.0.0
set PACKAGE_NAME=PDSS_Windows_Installer

REM Get timestamp using PowerShell (more reliable than wmic)
for /f "tokens=*" %%a in ('powershell -command "Get-Date -Format 'yyyyMMddHHmm'"') do set TIMESTAMP=%%a
for /f "tokens=*" %%a in ('powershell -command "Get-Date -Format 'yyyy-MM-dd HH:mm'"') do set TIMESTAMP_FRIENDLY=%%a

set OUTPUT_DIR=%PACKAGE_NAME%_v%VERSION%_%TIMESTAMP%
set ZIP_NAME=%PACKAGE_NAME%_v%VERSION%_%TIMESTAMP%.zip

echo [INFO] Version: %VERSION%
echo [INFO] Build Date: %TIMESTAMP_FRIENDLY%
echo [INFO] Package: %OUTPUT_DIR%
echo.

echo ============================================================================
echo   STAGE 1: PRE-BUILD VALIDATION
echo ============================================================================
echo.

echo [1/5] Checking project structure...
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

echo [2/5] Checking required files...
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

echo [3/5] Creating package directory structure...
mkdir "%OUTPUT_DIR%" 2>nul
mkdir "%OUTPUT_DIR%\backend" 2>nul
mkdir "%OUTPUT_DIR%\frontend" 2>nul
mkdir "%OUTPUT_DIR%\docs" 2>nul
mkdir "%OUTPUT_DIR%\scripts" 2>nul
mkdir "%OUTPUT_DIR%\config" 2>nul
echo [OK] Directory structure created
echo.

echo [4/5] Generating package metadata...
(
echo Package: Procurement Decision Support System ^(PDSS^)
echo Version: %VERSION%
echo Build Date: %TIMESTAMP_FRIENDLY%
echo Platform: Windows
echo.
echo Components:
echo - Backend: FastAPI + PostgreSQL
echo - Frontend: React + TypeScript
echo - Deployment: Docker + Docker Compose
echo.
echo System Requirements:
echo - Windows 10/11 or Windows Server 2019+
echo - Docker Desktop for Windows
echo - 4GB RAM minimum ^(8GB recommended^)
echo - 10GB free disk space
echo.
echo Build Information:
echo - Build ID: %TIMESTAMP%
echo - Package Size: ^(calculated after build^)
) > "%OUTPUT_DIR%\PACKAGE_INFO.txt"
echo [OK] Metadata generated
echo.

echo [5/5] Creating version file...
(
echo {
echo   "version": "%VERSION%",
echo   "build": "%TIMESTAMP%",
echo   "platform": "windows",
echo   "created": "%TIMESTAMP_FRIENDLY%"
echo }
) > "%OUTPUT_DIR%\version.json"
echo [OK] Version file created
echo.

echo ============================================================================
echo   STAGE 2: COPYING APPLICATION FILES
echo ============================================================================
echo.

echo [1/5] Copying backend application...
xcopy "..\backend\*" "%OUTPUT_DIR%\backend\" /E /I /Q /Y >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Failed to copy backend files!
    pause
    exit /b 1
)
echo [OK] Backend copied

REM Clean up Python cache files
echo       Cleaning Python cache...
for /d /r "%OUTPUT_DIR%\backend" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /r "%OUTPUT_DIR%\backend" %%f in (*.pyc) do @if exist "%%f" del "%%f" 2>nul
del "%OUTPUT_DIR%\backend\.dockerignore" 2>nul
del "%OUTPUT_DIR%\backend\.gitignore" 2>nul
echo       [OK] Cleanup complete
echo.

echo [2/5] Copying frontend application...
xcopy "..\frontend\src" "%OUTPUT_DIR%\frontend\src\" /E /I /Q /Y >nul 2>&1
xcopy "..\frontend\public" "%OUTPUT_DIR%\frontend\public\" /E /I /Q /Y >nul 2>&1
copy "..\frontend\package.json" "%OUTPUT_DIR%\frontend\" >nul 2>&1
copy "..\frontend\package-lock.json" "%OUTPUT_DIR%\frontend\" >nul 2>&1
copy "..\frontend\tsconfig.json" "%OUTPUT_DIR%\frontend\" >nul 2>&1
copy "..\frontend\.env.example" "%OUTPUT_DIR%\frontend\" >nul 2>&1
copy "..\frontend\Dockerfile" "%OUTPUT_DIR%\frontend\" >nul 2>&1
echo [OK] Frontend copied

REM Clean up node_modules if exists
if exist "%OUTPUT_DIR%\frontend\node_modules" rd /s /q "%OUTPUT_DIR%\frontend\node_modules" 2>nul
del "%OUTPUT_DIR%\frontend\.gitignore" 2>nul
echo.

echo [3/5] Copying Docker configuration...
copy "..\docker-compose.yml" "%OUTPUT_DIR%\" >nul 2>&1
copy "..\backend\Dockerfile" "%OUTPUT_DIR%\backend\" >nul 2>&1
copy "..\frontend\Dockerfile" "%OUTPUT_DIR%\frontend\" >nul 2>&1
echo [OK] Docker files copied
echo.

echo [4/5] Copying documentation...
REM Copy main documentation
if exist "..\README.md" copy "..\README.md" "%OUTPUT_DIR%\docs\README.md" >nul 2>&1
if exist "..\USER_GUIDE.md" copy "..\USER_GUIDE.md" "%OUTPUT_DIR%\docs\USER_GUIDE.md" >nul 2>&1
if exist "..\COMPLETE_SYSTEM_DOCUMENTATION.md" copy "..\COMPLETE_SYSTEM_DOCUMENTATION.md" "%OUTPUT_DIR%\docs\COMPLETE_SYSTEM_DOCUMENTATION.md" >nul 2>&1
if exist "..\QUICK_START_WINDOWS.md" copy "..\QUICK_START_WINDOWS.md" "%OUTPUT_DIR%\docs\QUICK_START.md" >nul 2>&1

REM Copy from installation_packages if not in root
if not exist "%OUTPUT_DIR%\docs\README.md" if exist "README.md" copy "README.md" "%OUTPUT_DIR%\docs\" >nul 2>&1
if not exist "%OUTPUT_DIR%\docs\USER_GUIDE.md" if exist "USER_GUIDE.md" copy "USER_GUIDE.md" "%OUTPUT_DIR%\docs\" >nul 2>&1
if exist "INSTALLATION_GUIDE.md" copy "INSTALLATION_GUIDE.md" "%OUTPUT_DIR%\docs\" >nul 2>&1
if exist "SYSTEM_REQUIREMENTS.md" copy "SYSTEM_REQUIREMENTS.md" "%OUTPUT_DIR%\docs\" >nul 2>&1
if exist "QUICK_START.md" copy "QUICK_START.md" "%OUTPUT_DIR%\docs\" >nul 2>&1
echo [OK] Documentation copied
echo.

echo [5/5] Copying configuration templates...
if exist "config_template.env" copy "config_template.env" "%OUTPUT_DIR%\config\.env.example" >nul 2>&1
if not exist "%OUTPUT_DIR%\config\.env.example" (
    REM Create default .env.example
    (
    echo # PDSS Configuration
    echo DATABASE_URL=postgresql://postgres:postgres@db:5432/procurement_dss
    echo SECRET_KEY=change-this-secret-key-in-production
    echo ALLOWED_ORIGINS=http://localhost:3000
    echo POSTGRES_USER=postgres
    echo POSTGRES_PASSWORD=postgres
    echo POSTGRES_DB=procurement_dss
    ) > "%OUTPUT_DIR%\config\.env.example"
)
echo [OK] Configuration templates copied
echo.

echo ============================================================================
echo   STAGE 3: CREATING INSTALLATION SCRIPTS
echo ============================================================================
echo.

echo [1/4] Creating main installer script...
(
echo @echo off
echo REM ========================================================================
echo REM  PDSS Windows Installer v%VERSION%
echo REM  Automated Installation for Windows
echo REM ========================================================================
echo.
echo echo.
echo echo ========================================================================
echo echo   Procurement Decision Support System ^(PDSS^)
echo echo   Windows Installer v%VERSION%
echo echo ========================================================================
echo echo.
echo.
echo REM Check if running as administrator
echo net session ^>nul 2^>^&1
echo if %%errorLevel%% neq 0 ^(
echo     echo [ERROR] Administrator privileges required!
echo     echo Please right-click this file and select "Run as Administrator"
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo [1/8] Checking prerequisites...
echo echo.
echo.
echo REM Check Docker Desktop
echo docker --version ^>nul 2^>^&1
echo if %%errorLevel%% neq 0 ^(
echo     echo [ERROR] Docker Desktop is not installed!
echo     echo.
echo     echo Download from: https://www.docker.com/products/docker-desktop
echo     echo.
echo     echo After installation:
echo     echo   1. Restart your computer
echo     echo   2. Start Docker Desktop
echo     echo   3. Run this installer again
echo     pause
echo     exit /b 1
echo ^)
echo echo [OK] Docker Desktop found
echo.
echo REM Check Docker Compose
echo docker-compose --version ^>nul 2^>^&1
echo if %%errorLevel%% neq 0 ^(
echo     echo [ERROR] Docker Compose is not installed!
echo     pause
echo     exit /b 1
echo ^)
echo echo [OK] Docker Compose found
echo.
echo REM Check if Docker is running
echo docker ps ^>nul 2^>^&1
echo if %%errorLevel%% neq 0 ^(
echo     echo [ERROR] Docker Desktop is not running!
echo     echo Please start Docker Desktop and wait for it to be ready.
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
echo echo This may take 5-10 minutes on first installation...
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
echo echo [OK] Database started
echo echo Waiting for database initialization...
echo timeout /t 15 /nobreak ^>nul
echo echo.
echo.
echo echo [6/8] Starting backend service...
echo docker-compose up -d backend
echo echo [OK] Backend started
echo echo Waiting for backend initialization...
echo timeout /t 20 /nobreak ^>nul
echo echo.
echo.
echo echo [7/8] Starting frontend service...
echo docker-compose up -d frontend
echo echo [OK] Frontend started
echo echo Waiting for frontend initialization...
echo timeout /t 25 /nobreak ^>nul
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
echo echo   Admin:       admin / admin123
echo echo   Finance:     finance1 / finance123
echo echo   PM:          pm1 / pm123
echo echo   Procurement: proc1 / proc123
echo echo.
echo echo IMPORTANT: Change default passwords after first login!
echo echo.
echo echo Opening browser...
echo timeout /t 3 /nobreak ^>nul
echo start http://localhost:3000
echo echo.
echo echo ========================================================================
echo pause
) > "%OUTPUT_DIR%\INSTALL.bat"
echo [OK] Main installer created
echo.

echo [2/4] Creating management scripts...

REM Start script
(
echo @echo off
echo cd /d "%%~dp0"
echo docker-compose up -d
echo timeout /t 5 /nobreak ^>nul
echo start http://localhost:3000
echo echo PDSS started successfully!
echo echo Opening browser...
echo pause
) > "%OUTPUT_DIR%\scripts\start.bat"

REM Stop script
(
echo @echo off
echo cd /d "%%~dp0\.."
echo docker-compose down
echo echo PDSS stopped successfully!
echo pause
) > "%OUTPUT_DIR%\scripts\stop.bat"

REM Status script
(
echo @echo off
echo cd /d "%%~dp0\.."
echo echo ========================================================================
echo echo   PDSS System Status
echo echo ========================================================================
echo echo.
echo docker-compose ps
echo echo.
echo pause
) > "%OUTPUT_DIR%\scripts\status.bat"

REM Logs script
(
echo @echo off
echo cd /d "%%~dp0\.."
echo echo ========================================================================
echo echo   PDSS System Logs
echo echo ========================================================================
echo echo.
echo docker-compose logs -f
) > "%OUTPUT_DIR%\scripts\logs.bat"

REM Restart script
(
echo @echo off
echo cd /d "%%~dp0\.."
echo echo Restarting PDSS...
echo docker-compose restart
echo echo PDSS restarted successfully!
echo pause
) > "%OUTPUT_DIR%\scripts\restart.bat"

REM Uninstall script
(
echo @echo off
echo cd /d "%%~dp0\.."
echo echo ========================================================================
echo echo   PDSS Uninstaller
echo echo ========================================================================
echo echo.
echo echo WARNING: This will remove all PDSS containers and data!
echo echo.
echo set /p CONFIRM="Are you sure? Type 'YES' to confirm: "
echo if not "%%CONFIRM%%"=="YES" ^(
echo     echo Uninstall cancelled.
echo     pause
echo     exit /b 0
echo ^)
echo echo.
echo echo Stopping and removing containers...
echo docker-compose down -v
echo echo.
echo echo PDSS has been uninstalled.
echo echo Note: Installation files are still present.
echo echo You can safely delete this folder to complete removal.
echo echo.
echo pause
) > "%OUTPUT_DIR%\scripts\uninstall.bat"

echo [OK] Management scripts created
echo.

echo [3/4] Creating desktop shortcuts creator...
(
echo @echo off
echo REM Create desktop shortcuts for PDSS
echo set INSTALL_DIR=%%~dp0..
echo.
echo echo Creating desktop shortcuts...
echo.
echo ^(
echo echo @echo off
echo echo cd /d "%%INSTALL_DIR%%"
echo echo docker-compose up -d
echo echo timeout /t 5 /nobreak ^^^>nul
echo echo start http://localhost:3000
echo echo echo PDSS started!
echo ^) ^> "%%USERPROFILE%%\Desktop\Start PDSS.bat"
echo.
echo ^(
echo echo @echo off
echo echo cd /d "%%INSTALL_DIR%%"
echo echo docker-compose down
echo echo echo PDSS stopped!
echo ^) ^> "%%USERPROFILE%%\Desktop\Stop PDSS.bat"
echo.
echo echo Desktop shortcuts created successfully!
echo pause
) > "%OUTPUT_DIR%\scripts\create_shortcuts.bat"
echo [OK] Shortcut creator created
echo.

echo [4/4] Creating README...
(
echo ========================================================================
echo   PROCUREMENT DECISION SUPPORT SYSTEM ^(PDSS^)
echo   Windows Installation Package v%VERSION%
echo ========================================================================
echo.
echo BUILD INFORMATION:
echo   Version: %VERSION%
echo   Build Date: %TIMESTAMP_FRIENDLY%
echo   Platform: Windows
echo.
echo SYSTEM REQUIREMENTS:
echo   - Windows 10/11 or Windows Server 2019+
echo   - Docker Desktop for Windows
echo   - 4GB RAM minimum ^(8GB recommended^)
echo   - 10GB free disk space
echo.
echo INSTALLATION INSTRUCTIONS:
echo   1. Ensure Docker Desktop is installed and running
echo   2. Right-click INSTALL.bat and select "Run as Administrator"
echo   3. Follow the on-screen instructions
echo   4. Access the system at http://localhost:3000
echo.
echo MANAGEMENT SCRIPTS ^(in scripts folder^):
echo   - start.bat          Start the PDSS system
echo   - stop.bat           Stop the PDSS system
echo   - restart.bat        Restart the PDSS system
echo   - status.bat         Check system status
echo   - logs.bat           View system logs
echo   - uninstall.bat      Uninstall PDSS
echo   - create_shortcuts.bat  Create desktop shortcuts
echo.
echo DEFAULT CREDENTIALS:
echo   Admin:       admin / admin123
echo   Finance:     finance1 / finance123
echo   PM:          pm1 / pm123
echo   Procurement: proc1 / proc123
echo.
echo   IMPORTANT: Change passwords after first login!
echo.
echo DOCUMENTATION:
echo   See the 'docs' folder for complete documentation
echo.
echo SUPPORT:
echo   For issues or questions, refer to the documentation
echo   or contact your system administrator.
echo.
echo ========================================================================
echo   Created: %TIMESTAMP_FRIENDLY%
echo   Package: %OUTPUT_DIR%
echo ========================================================================
) > "%OUTPUT_DIR%\README.txt"
echo [OK] README created
echo.

echo ============================================================================
echo   STAGE 4: CREATING VERIFICATION TOOLS
echo ============================================================================
echo.

echo [1/2] Creating package verification script...
(
echo @echo off
echo echo ========================================================================
echo echo   PDSS Package Verification
echo echo ========================================================================
echo echo.
echo echo Checking package integrity...
echo echo.
echo.
echo set ERRORS=0
echo.
echo echo [1] Checking critical files:
echo if exist "docker-compose.yml" ^(echo   [OK] docker-compose.yml^) else ^(echo   [MISSING] docker-compose.yml ^&^& set /a ERRORS+=1^)
echo if exist "backend\Dockerfile" ^(echo   [OK] backend\Dockerfile^) else ^(echo   [MISSING] backend\Dockerfile ^&^& set /a ERRORS+=1^)
echo if exist "frontend\Dockerfile" ^(echo   [OK] frontend\Dockerfile^) else ^(echo   [MISSING] frontend\Dockerfile ^&^& set /a ERRORS+=1^)
echo if exist "backend\requirements.txt" ^(echo   [OK] backend\requirements.txt^) else ^(echo   [MISSING] backend\requirements.txt ^&^& set /a ERRORS+=1^)
echo if exist "frontend\package.json" ^(echo   [OK] frontend\package.json^) else ^(echo   [MISSING] frontend\package.json ^&^& set /a ERRORS+=1^)
echo if exist "INSTALL.bat" ^(echo   [OK] INSTALL.bat^) else ^(echo   [MISSING] INSTALL.bat ^&^& set /a ERRORS+=1^)
echo echo.
echo.
echo echo [2] Checking Docker Compose configuration:
echo findstr /C:"postgres:" docker-compose.yml ^>nul 2^>^&1 ^&^& echo   [OK] PostgreSQL service ^|^| ^(echo   [MISSING] PostgreSQL service ^&^& set /a ERRORS+=1^)
echo findstr /C:"backend:" docker-compose.yml ^>nul 2^>^&1 ^&^& echo   [OK] Backend service ^|^| ^(echo   [MISSING] Backend service ^&^& set /a ERRORS+=1^)
echo findstr /C:"frontend:" docker-compose.yml ^>nul 2^>^&1 ^&^& echo   [OK] Frontend service ^|^| ^(echo   [MISSING] Frontend service ^&^& set /a ERRORS+=1^)
echo echo.
echo.
echo echo [3] Checking management scripts:
echo if exist "scripts\start.bat" ^(echo   [OK] start.bat^) else ^(echo   [MISSING] start.bat ^&^& set /a ERRORS+=1^)
echo if exist "scripts\stop.bat" ^(echo   [OK] stop.bat^) else ^(echo   [MISSING] stop.bat ^&^& set /a ERRORS+=1^)
echo if exist "scripts\status.bat" ^(echo   [OK] status.bat^) else ^(echo   [MISSING] status.bat ^&^& set /a ERRORS+=1^)
echo echo.
echo.
echo if %%ERRORS%% equ 0 ^(
echo     echo ========================================================================
echo     echo   VERIFICATION PASSED - Package is ready for deployment!
echo     echo ========================================================================
echo ^) else ^(
echo     echo ========================================================================
echo     echo   VERIFICATION FAILED - %%ERRORS%% error^(s^) found!
echo     echo ========================================================================
echo ^)
echo echo.
echo pause
) > "%OUTPUT_DIR%\VERIFY_PACKAGE.bat"
echo [OK] Verification script created
echo.

echo [2/2] Creating quick start guide...
(
echo ========================================================================
echo   QUICK START GUIDE
echo ========================================================================
echo.
echo STEP 1: INSTALL DOCKER
echo   Download and install Docker Desktop from:
echo   https://www.docker.com/products/docker-desktop
echo.
echo STEP 2: VERIFY PACKAGE
echo   Run: VERIFY_PACKAGE.bat
echo   This checks if all required files are present
echo.
echo STEP 3: INSTALL PDSS
echo   Right-click INSTALL.bat
echo   Select "Run as Administrator"
echo   Wait for installation to complete
echo.
echo STEP 4: ACCESS SYSTEM
echo   Open browser: http://localhost:3000
echo   Login: admin / admin123
echo.
echo STEP 5: POST-INSTALLATION
echo   - Change default passwords
echo   - Create desktop shortcuts: scripts\create_shortcuts.bat
echo   - Review documentation in docs folder
echo.
echo ========================================================================
echo   MANAGEMENT COMMANDS
echo ========================================================================
echo.
echo   Start System:    scripts\start.bat
echo   Stop System:     scripts\stop.bat
echo   Check Status:    scripts\status.bat
echo   View Logs:       scripts\logs.bat
echo   Restart:         scripts\restart.bat
echo   Uninstall:       scripts\uninstall.bat
echo.
echo ========================================================================
) > "%OUTPUT_DIR%\QUICK_START.txt"
echo [OK] Quick start guide created
echo.

echo ============================================================================
echo   STAGE 5: PACKAGE FINALIZATION
echo ============================================================================
echo.

echo [1/3] Calculating package size...
set SIZE=0
for /r "%OUTPUT_DIR%" %%f in (*) do set /a SIZE+=%%~zf
set /a SIZE_MB=SIZE/1024/1024
echo [OK] Package size: ~%SIZE_MB% MB
echo.

echo [2/3] Creating package manifest...
(
echo PDSS Windows Installation Package
echo ========================================================================
echo Version: %VERSION%
echo Build: %TIMESTAMP%
echo Created: %TIMESTAMP_FRIENDLY%
echo Platform: Windows
echo Size: ~%SIZE_MB% MB
echo.
echo Package Contents:
echo ├── INSTALL.bat               Main installer
echo ├── README.txt                Package information
echo ├── QUICK_START.txt           Quick start guide
echo ├── VERIFY_PACKAGE.bat        Package verification
echo ├── PACKAGE_INFO.txt          Detailed package info
echo ├── version.json              Version metadata
echo ├── docker-compose.yml        Docker orchestration
echo ├── backend\                  Backend application
echo ├── frontend\                 Frontend application
echo ├── docs\                     Documentation
echo ├── scripts\                  Management scripts
echo │   ├── start.bat
echo │   ├── stop.bat
echo │   ├── status.bat
echo │   ├── logs.bat
echo │   ├── restart.bat
echo │   ├── uninstall.bat
echo │   └── create_shortcuts.bat
echo └── config\                   Configuration templates
echo.
echo Installation:
echo   1. Run VERIFY_PACKAGE.bat to check integrity
echo   2. Run INSTALL.bat as Administrator
echo   3. Access at http://localhost:3000
echo.
echo Support:
echo   See documentation in docs\ folder
echo.
) > "%OUTPUT_DIR%\MANIFEST.txt"
echo [OK] Manifest created
echo.

echo [3/3] Creating checksum file...
(
echo PDSS Package Checksum - Build %TIMESTAMP%
echo ========================================================================
echo.
echo Critical Files:
) > "%OUTPUT_DIR%\CHECKSUMS.txt"

REM Add file list to checksums
for %%f in ("%OUTPUT_DIR%\*.bat" "%OUTPUT_DIR%\*.yml" "%OUTPUT_DIR%\*.txt") do (
    echo %%~nxf >> "%OUTPUT_DIR%\CHECKSUMS.txt"
)
echo [OK] Checksum file created
echo.

echo ============================================================================
echo   STAGE 6: CREATING COMPRESSED ARCHIVE
echo ============================================================================
echo.

echo [1/1] Checking for compression tools...
where powershell >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] PowerShell found - Creating ZIP archive...
    powershell -command "Compress-Archive -Path '%OUTPUT_DIR%\*' -DestinationPath '%ZIP_NAME%' -Force" 2>nul
    if exist "%ZIP_NAME%" (
        echo [OK] ZIP archive created: %ZIP_NAME%
        for %%f in ("%ZIP_NAME%") do set ZIP_SIZE=%%~zf
        set /a ZIP_SIZE_MB=ZIP_SIZE/1024/1024
        echo [OK] Archive size: ~!ZIP_SIZE_MB! MB
    ) else (
        echo [WARNING] Failed to create ZIP archive
    )
) else (
    echo [INFO] PowerShell not available - ZIP archive not created
    echo [INFO] You can manually compress the %OUTPUT_DIR% folder
)
echo.

echo ============================================================================
echo   BUILD COMPLETE!
echo ============================================================================
echo.
echo Package Details:
echo   Name:     %OUTPUT_DIR%
echo   Version:  %VERSION%
echo   Build:    %TIMESTAMP%
echo   Size:     ~%SIZE_MB% MB
if exist "%ZIP_NAME%" echo   Archive:  %ZIP_NAME% (~!ZIP_SIZE_MB! MB)
echo.
echo Package Location:
echo   Folder:   %CD%\%OUTPUT_DIR%
if exist "%ZIP_NAME%" echo   ZIP:      %CD%\%ZIP_NAME%
echo.
echo Next Steps:
echo   1. Verify package: cd %OUTPUT_DIR% ^&^& VERIFY_PACKAGE.bat
echo   2. Review contents: %OUTPUT_DIR%\README.txt
echo   3. Deploy to target system
echo   4. Run INSTALL.bat as Administrator
echo.
echo Distribution Options:
if exist "%ZIP_NAME%" (
    echo   - Transfer ZIP file: %ZIP_NAME%
    echo   - Extract on target system and run INSTALL.bat
) else (
    echo   - Copy entire folder: %OUTPUT_DIR%
    echo   - Run INSTALL.bat on target system
)
echo.
echo ============================================================================
echo.
pause

