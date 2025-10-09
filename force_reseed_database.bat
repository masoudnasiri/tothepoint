@echo off
REM Force reseed database with mock data (DESTROYS ALL EXISTING DATA!)

echo ================================================================
echo   ⚠️  WARNING: DESTRUCTIVE OPERATION!
echo ================================================================
echo.
echo This script will DELETE ALL existing data and reseed with mock data:
echo   - All users (except what's in seed)
echo   - All projects
echo   - All finalized decisions
echo   - All optimization runs
echo   - All budget data
echo   - All cashflow events
echo   - EVERYTHING!
echo.
echo ================================================================
echo   USE THIS ONLY FOR:
echo ================================================================
echo   1. Fresh development environment setup
echo   2. Resetting to demo data for testing
echo   3. Fixing corrupted database
echo.
echo   DO NOT USE if you have real data you want to keep!
echo.
echo ================================================================
echo.

set /p CONFIRM1="Type 'DELETE ALL MY DATA' to confirm (case-sensitive): "

if not "%CONFIRM1%"=="DELETE ALL MY DATA" (
    echo.
    echo ✅ Cancelled - Your data is safe!
    pause
    exit /b 0
)

echo.
echo ⚠️  ARE YOU ABSOLUTELY SURE?
echo.
set /p CONFIRM2="Type 'YES I AM SURE' to proceed: "

if not "%CONFIRM2%"=="YES I AM SURE" (
    echo.
    echo ✅ Cancelled - Your data is safe!
    pause
    exit /b 0
)

echo.
echo ================================================================
echo   FORCE RESEEDING - DELETING ALL DATA
echo ================================================================
echo.

REM Create Python script to force reseed
echo import asyncio > temp_force_reseed.py
echo from app.seed_data import clear_all_data, seed_comprehensive_data >> temp_force_reseed.py
echo from app.database import AsyncSessionLocal >> temp_force_reseed.py
echo. >> temp_force_reseed.py
echo async def force_reseed(): >> temp_force_reseed.py
echo     async with AsyncSessionLocal() as db: >> temp_force_reseed.py
echo         print("Clearing all data...") >> temp_force_reseed.py
echo         await clear_all_data(db) >> temp_force_reseed.py
echo         print("Data cleared!") >> temp_force_reseed.py
echo     print("Reseeding...") >> temp_force_reseed.py
echo     await seed_comprehensive_data() >> temp_force_reseed.py
echo     print("Reseed complete!") >> temp_force_reseed.py
echo. >> temp_force_reseed.py
echo if __name__ == "__main__": >> temp_force_reseed.py
echo     asyncio.run(force_reseed()) >> temp_force_reseed.py

REM Copy to container and execute
docker cp temp_force_reseed.py cahs_flow_project-backend-1:/app/temp_force_reseed.py

echo Running force reseed...
docker-compose exec backend python temp_force_reseed.py

REM Cleanup
del temp_force_reseed.py
docker-compose exec backend rm /app/temp_force_reseed.py

if %errorlevel% equ 0 (
    echo.
    echo ================================================================
    echo   ✅ RESEED COMPLETE!
    echo ================================================================
    echo.
    echo Database has been reset to mock/demo data.
    echo.
    echo Default Users:
    echo   Admin:       admin / admin123
    echo   Finance:     finance1 / finance123
    echo   PM:          pm1 / pm123
    echo   Procurement: proc1 / proc123
    echo.
    echo Restart the backend to apply:
    echo   docker-compose restart backend
    echo.
) else (
    echo.
    echo ❌ Reseed failed - Check error messages above
)

pause

