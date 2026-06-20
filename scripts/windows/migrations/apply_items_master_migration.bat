@echo off
REM Apply Items Master migration - Create master catalog and migrate existing data

echo ========================================
echo  ITEMS MASTER MIGRATION
echo ========================================
echo.
echo This migration will:
echo   1. Create 'items_master' table
echo   2. Migrate existing items to master catalog
echo   3. Add 'master_item_id' to project_items
echo   4. Link existing project items to master
echo.
echo This is SAFE - All existing data will be preserved!
echo.
echo IMPORTANT: This is a MAJOR database change.
echo Please ensure you have a backup before proceeding.
echo.

set /p CONFIRM="Apply Items Master migration? (yes/no): "

if not "%CONFIRM%"=="yes" (
    echo Migration cancelled.
    pause
    exit /b 0
)

echo.
echo Applying migration...
echo.

REM Copy migration file to container and execute
docker cp backend\create_items_master_migration.sql cahs_flow_project-postgres-1:/tmp/items_master_migration.sql

docker-compose exec postgres psql -U postgres -d procurement_dss -f /tmp/items_master_migration.sql

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo  Migration Completed Successfully!
    echo ========================================
    echo.
    echo ✅ items_master table created
    echo ✅ Existing items migrated to master
    echo ✅ master_item_id column added to project_items
    echo ✅ Existing project items linked to master
    echo ✅ All data preserved
    echo.
    echo Next steps:
    echo   1. Restart backend: docker-compose restart backend
    echo   2. Check API docs: http://localhost:8000/docs
    echo   3. Look for /items-master endpoints
    echo.
) else (
    echo.
    echo ❌ Migration failed
    echo    Check database connection and try again
    echo.
)

pause

