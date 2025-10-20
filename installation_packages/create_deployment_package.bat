@echo off
REM ========================================================================
REM  Create Deployment Package for PDSS - Windows Version
REM  This script creates a complete package for deployment
REM ========================================================================

echo.
echo ========================================================================
echo   Creating Deployment Package - Windows Version
echo ========================================================================
echo.

set PACKAGE_NAME=PDSS_Deployment_Package
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set TIMESTAMP=%YYYY%%MM%%DD%_%HH%%Min%%Sec%
set OUTPUT_DIR=%PACKAGE_NAME%_%TIMESTAMP%

echo [1/8] Creating package directory...
mkdir "%OUTPUT_DIR%" 2>nul
mkdir "%OUTPUT_DIR%\backend" 2>nul
mkdir "%OUTPUT_DIR%\frontend" 2>nul
mkdir "%OUTPUT_DIR%\docs" 2>nul

echo [2/8] Copying backend files...
xcopy "..\backend\*" "%OUTPUT_DIR%\backend\" /E /I /Q /Y >nul 2>&1
REM Remove Python cache files
for /d /r "%OUTPUT_DIR%\backend" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /r "%OUTPUT_DIR%\backend" %%f in (*.pyc) do @if exist "%%f" del "%%f" 2>nul

echo [3/8] Copying frontend files...
xcopy "..\frontend\src" "%OUTPUT_DIR%\frontend\src\" /E /I /Q /Y >nul 2>&1
xcopy "..\frontend\public" "%OUTPUT_DIR%\frontend\public\" /E /I /Q /Y >nul 2>&1
copy "..\frontend\package.json" "%OUTPUT_DIR%\frontend\" >nul 2>&1
copy "..\frontend\package-lock.json" "%OUTPUT_DIR%\frontend\" >nul 2>&1
copy "..\frontend\Dockerfile" "%OUTPUT_DIR%\frontend\" >nul 2>&1

echo [4/8] Checking for Node.js and building frontend...
where node >nul 2>&1
if %errorlevel% equ 0 (
    echo Building React frontend for production...
    cd "%OUTPUT_DIR%\frontend"
    call npm install --production >nul 2>&1
    call npm run build >nul 2>&1
    if %errorlevel% equ 0 (
        echo Frontend built successfully!
    ) else (
        echo [WARNING] Frontend build failed. Will build during Docker deployment.
    )
    cd /d "%~dp0"
) else (
    echo [WARNING] Node.js not found. Frontend will be built during Docker deployment.
)

echo [5/8] Copying Docker configuration...
copy "..\docker-compose.yml" "%OUTPUT_DIR%\" >nul 2>&1
copy "..\backend\Dockerfile" "%OUTPUT_DIR%\backend\" >nul 2>&1

echo [6/8] Copying documentation...
copy "..\README.md" "%OUTPUT_DIR%\docs\" >nul 2>&1
copy "..\USER_GUIDE.md" "%OUTPUT_DIR%\docs\" >nul 2>&1
copy "..\COMPLETE_SYSTEM_DOCUMENTATION.md" "%OUTPUT_DIR%\docs\" >nul 2>&1

REM Copy from installation_packages if not found in root
if not exist "%OUTPUT_DIR%\docs\README.md" copy "README.md" "%OUTPUT_DIR%\docs\" >nul 2>&1
if not exist "%OUTPUT_DIR%\docs\USER_GUIDE.md" copy "USER_GUIDE.md" "%OUTPUT_DIR%\docs\" >nul 2>&1
if not exist "%OUTPUT_DIR%\docs\COMPLETE_SYSTEM_DOCUMENTATION.md" copy "COMPLETE_SYSTEM_DOCUMENTATION.md" "%OUTPUT_DIR%\docs\" >nul 2>&1

echo [7/8] Copying installation scripts...
copy "install_windows.bat" "%OUTPUT_DIR%\" >nul 2>&1
copy "install_linux.sh" "%OUTPUT_DIR%\" >nul 2>&1
copy "uninstall_windows.bat" "%OUTPUT_DIR%\" >nul 2>&1
copy "uninstall_linux.sh" "%OUTPUT_DIR%\" >nul 2>&1
copy "config_template.env" "%OUTPUT_DIR%\.env.example" >nul 2>&1

REM Copy documentation files
copy "README.md" "%OUTPUT_DIR%\" >nul 2>&1
copy "QUICK_START.md" "%OUTPUT_DIR%\" >nul 2>&1
copy "INSTALLATION_GUIDE.md" "%OUTPUT_DIR%\" >nul 2>&1
copy "SYSTEM_REQUIREMENTS.md" "%OUTPUT_DIR%\" >nul 2>&1

echo [8/8] Creating deployment verification script...
(
echo @echo off
echo echo Verifying deployment package...
echo echo.
echo echo Checking critical files:
echo if exist "docker-compose.yml" ^(echo [OK] docker-compose.yml^) else ^(echo [MISSING] docker-compose.yml^)
echo if exist "backend\Dockerfile" ^(echo [OK] backend\Dockerfile^) else ^(echo [MISSING] backend\Dockerfile^)
echo if exist "frontend\Dockerfile" ^(echo [OK] frontend\Dockerfile^) else ^(echo [MISSING] frontend\Dockerfile^)
echo if exist "backend\requirements.txt" ^(echo [OK] backend\requirements.txt^) else ^(echo [MISSING] backend\requirements.txt^)
echo if exist "frontend\package.json" ^(echo [OK] frontend\package.json^) else ^(echo [MISSING] frontend\package.json^)
echo if exist "install_windows.bat" ^(echo [OK] install_windows.bat^) else ^(echo [MISSING] install_windows.bat^)
echo if exist "install_linux.sh" ^(echo [OK] install_linux.sh^) else ^(echo [MISSING] install_linux.sh^)
echo.
echo echo Checking Docker Compose services:
echo findstr /C:"postgres:" docker-compose.yml >nul 2>&1 ^&^& echo [OK] PostgreSQL service configured ^|^| echo [MISSING] PostgreSQL service
echo findstr /C:"backend:" docker-compose.yml >nul 2>&1 ^&^& echo [OK] Backend service configured ^|^| echo [MISSING] Backend service
echo findstr /C:"frontend:" docker-compose.yml >nul 2>&1 ^&^& echo [OK] Frontend service configured ^|^| echo [MISSING] Frontend service
echo.
echo echo Deployment package verification complete!
echo pause
) > "%OUTPUT_DIR%\verify_deployment.bat"

echo.
echo ========================================================================
echo   Package Created Successfully!
echo ========================================================================
echo.
echo Package location: %OUTPUT_DIR%
echo.
echo Package contents:
echo ├── backend\          (FastAPI application)
echo ├── frontend\         (React application)
echo ├── docs\            (Documentation)
echo ├── docker-compose.yml
echo ├── install_windows.bat
echo ├── install_linux.sh
echo ├── .env.example
echo └── verify_deployment.bat
echo.
echo Next steps:
echo 1. Copy the entire '%OUTPUT_DIR%' folder to target server
echo 2. Run: verify_deployment.bat (to check package integrity)
echo 3. On Windows: Run install_windows.bat as Administrator
echo 4. On Linux: Run sudo ./install_linux.sh
echo.
echo Package is ready for deployment!
echo ========================================================================
echo.
pause