@echo off
echo ========================================
echo Applying is_finalized Migration
echo ========================================
echo.

echo Step 1: Adding is_finalized column to procurement_options...
docker exec -i cahs_flow_project-postgres-1 psql -U postgres -d procurement_dss < add_is_finalized_migration.sql

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Migration failed!
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Migration completed successfully!
echo.
echo Step 2: Restarting backend to apply changes...
docker-compose restart backend

echo.
echo ========================================
echo ✅ All Done!
echo ========================================
echo.
echo The is_finalized feature is now active:
echo - Procurement team can mark options as finalized
echo - Only finalized options will be used in optimization
echo - Budget analysis uses all options (finalized or not)
echo.
pause

