@echo off
REM Apply database migration to add bunch management columns

echo ========================================
echo  Database Migration - Add Bunch Columns
echo ========================================
echo.

echo This will add bunch_id and bunch_name columns to finalized_decisions table.
echo This is SAFE - no data will be lost!
echo.

set /p CONFIRM="Apply migration? (yes/no): "

if not "%CONFIRM%"=="yes" (
    echo Migration cancelled.
    pause
    exit /b 0
)

echo.
echo Applying migration...
echo.

REM Copy migration file to container and execute
docker cp backend\add_bunch_columns_migration.sql cahs_flow_project-postgres-1:/tmp/migration.sql

docker-compose exec postgres psql -U postgres -d procurement_dss -f /tmp/migration.sql

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo  Migration Completed Successfully!
    echo ========================================
    echo.
    echo + bunch_id column added
    echo + bunch_name column added
    echo + Index created
    echo + All existing data preserved
    echo.
    echo You can now use bunch management features!
    echo.
) else (
    echo.
    echo X Migration failed
    echo   Check database connection and try again
)

pause

