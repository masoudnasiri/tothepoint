@echo off
REM System Requirements Check for Procurement DSS

echo ========================================
echo   Procurement DSS System Check
echo ========================================
echo.

echo Checking system requirements...
echo.

REM Check Windows version
echo [1/6] Checking Windows version...
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
echo Windows Version: %VERSION%

REM Check if Windows 10/11
echo %VERSION% | findstr /R "^10\." >nul
if %errorlevel% equ 0 goto :check_win10
echo %VERSION% | findstr /R "^11\." >nul
if %errorlevel% equ 0 goto :check_ok
echo WARNING: Windows 10 or 11 recommended for best compatibility
goto :check_ram

:check_win10
echo Windows 10 detected - checking build...
for /f "tokens=3" %%i in ('reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v CurrentBuild') do set BUILD=%%i
echo Build: %BUILD%
if %BUILD% LSS 19041 (
    echo WARNING: Windows 10 build 19041+ recommended for Docker Desktop
)
goto :check_ram

:check_ok
echo Windows 11 detected - OK

:check_ram
echo.
echo [2/6] Checking available RAM...
for /f "skip=1" %%p in ('wmic computersystem get TotalPhysicalMemory') do (
    if not "%%p"=="" (
        set /a RAM_GB=%%p/1024/1024/1024
        echo Total RAM: !RAM_GB! GB
        if !RAM_GB! LSS 4 (
            echo WARNING: At least 4GB RAM recommended for Docker Desktop
        ) else (
            echo RAM: OK
        )
        goto :check_docker
    )
)

:check_docker
echo.
echo [3/6] Checking Docker Desktop...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker Desktop: NOT INSTALLED
    echo Please install from: https://www.docker.com/products/docker-desktop
    goto :check_ports
) else (
    echo Docker Desktop: INSTALLED
    docker --version
)

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker Status: NOT RUNNING
    echo Please start Docker Desktop
) else (
    echo Docker Status: RUNNING
)

:check_ports
echo.
echo [4/6] Checking port availability...
netstat -an | findstr ":3000" >nul
if %errorlevel% equ 0 (
    echo Port 3000: IN USE
) else (
    echo Port 3000: AVAILABLE
)

netstat -an | findstr ":8000" >nul
if %errorlevel% equ 0 (
    echo Port 8000: IN USE
) else (
    echo Port 8000: AVAILABLE
)

netstat -an | findstr ":5432" >nul
if %errorlevel% equ 0 (
    echo Port 5432: IN USE
) else (
    echo Port 5432: AVAILABLE
)

:check_wsl
echo.
echo [5/6] Checking WSL...
wsl --status >nul 2>&1
if %errorlevel% neq 0 (
    echo WSL: NOT AVAILABLE
    echo WSL 2 is recommended for Docker Desktop
) else (
    echo WSL: AVAILABLE
    wsl --status
)

:check_virtualization
echo.
echo [6/6] Checking virtualization...
systeminfo | findstr /i "virtualization" >nul
if %errorlevel% neq 0 (
    echo Virtualization: CHECK BIOS SETTINGS
) else (
    systeminfo | findstr /i "virtualization"
)

echo.
echo ========================================
echo   System Check Complete
echo ========================================
echo.
echo If all checks passed, you can run: setup-windows.bat
echo.
pause
