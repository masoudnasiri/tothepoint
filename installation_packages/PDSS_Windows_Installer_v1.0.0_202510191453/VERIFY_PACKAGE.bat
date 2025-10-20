@echo off
echo ========================================================================
echo   PDSS Package Verification
echo ========================================================================
echo.
echo Checking package integrity...
echo.

set ERRORS=0

echo [1] Checking critical files:
if exist "docker-compose.yml" (echo   [OK] docker-compose.yml) else (echo   [MISSING] docker-compose.yml && set /a ERRORS+=1)
if exist "backend\Dockerfile" (echo   [OK] backend\Dockerfile) else (echo   [MISSING] backend\Dockerfile && set /a ERRORS+=1)
if exist "frontend\Dockerfile" (echo   [OK] frontend\Dockerfile) else (echo   [MISSING] frontend\Dockerfile && set /a ERRORS+=1)
if exist "backend\requirements.txt" (echo   [OK] backend\requirements.txt) else (echo   [MISSING] backend\requirements.txt && set /a ERRORS+=1)
if exist "frontend\package.json" (echo   [OK] frontend\package.json) else (echo   [MISSING] frontend\package.json && set /a ERRORS+=1)
if exist "INSTALL.bat" (echo   [OK] INSTALL.bat) else (echo   [MISSING] INSTALL.bat && set /a ERRORS+=1)
echo.

echo [2] Checking Docker Compose configuration:
findstr /C:"postgres:" docker-compose.yml >nul 2>&1 && echo   [OK] PostgreSQL service || (echo   [MISSING] PostgreSQL service && set /a ERRORS+=1)
findstr /C:"backend:" docker-compose.yml >nul 2>&1 && echo   [OK] Backend service || (echo   [MISSING] Backend service && set /a ERRORS+=1)
findstr /C:"frontend:" docker-compose.yml >nul 2>&1 && echo   [OK] Frontend service || (echo   [MISSING] Frontend service && set /a ERRORS+=1)
echo.

echo [3] Checking management scripts:
if exist "scripts\start.bat" (echo   [OK] start.bat) else (echo   [MISSING] start.bat && set /a ERRORS+=1)
if exist "scripts\stop.bat" (echo   [OK] stop.bat) else (echo   [MISSING] stop.bat && set /a ERRORS+=1)
if exist "scripts\status.bat" (echo   [OK] status.bat) else (echo   [MISSING] status.bat && set /a ERRORS+=1)
echo.

if %ERRORS% equ 0 (
    echo ========================================================================
    echo   VERIFICATION PASSED - Package is ready for deployment
    echo ========================================================================
) else (
    echo ========================================================================
    echo   VERIFICATION FAILED - %ERRORS% error(s) found
    echo ========================================================================
)
echo.
pause
