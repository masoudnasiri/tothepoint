@echo off
REM Seed IT Company comprehensive test data

echo ========================================
echo  SEED IT COMPANY DATA
echo ========================================
echo.
echo This will:
echo   1. WIPE ALL existing data
echo   2. Create 10 IT company projects
echo   3. Create 37 IT items in master catalog
echo   4. Create 425+ project items across projects
echo   5. Create 100+ comprehensive procurement options
echo   6. Create 12 months of budget data
echo.
echo Projects will include:
echo   - Datacenter Infrastructure
echo   - Security Camera System
echo   - OCR Document Processing
echo   - Network Upgrades
echo   - Cloud Infrastructure
echo   - Disaster Recovery
echo   - Storage Systems
echo   - Workstation Refresh
echo   - And more!
echo.
echo ⚠️  WARNING: This will DELETE ALL existing data!
echo.

set /p CONFIRM="Proceed with IT company data seeding? (yes/no): "

if not "%CONFIRM%"=="yes" (
    echo Seeding cancelled.
    pause
    exit /b 0
)

echo.
echo 🚀 Starting IT company data seeding...
echo.

docker-compose exec backend python seed_it_company_data.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo  ✅ IT COMPANY DATA SEEDING COMPLETE!
    echo ========================================
    echo.
    echo 🎉 Your platform now has:
    echo    ✅ 10 realistic IT projects
    echo    ✅ 37 IT items in catalog
    echo    ✅ 400+ project items
    echo    ✅ 100+ procurement options
    echo    ✅ 12 months budgets
    echo.
    echo 🔑 Login with:
    echo    admin / admin123
    echo    pm1 / pm123
    echo    finance1 / finance123
    echo    proc1 / proc123
    echo.
    echo 🚀 Ready to test optimization!
    echo.
) else (
    echo.
    echo ❌ Seeding failed
    echo    Check backend logs: docker-compose logs backend
)

pause

