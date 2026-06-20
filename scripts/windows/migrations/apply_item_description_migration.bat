@echo off
REM Apply database migration to add description and file attachment columns to project_items

echo ========================================
echo  Database Migration - Add Item Description and File Attachment
echo ========================================
echo.

echo This will add the following columns to project_items table:
echo   - description (TEXT)
echo   - file_path (VARCHAR 500)
echo   - file_name (VARCHAR 255)
echo.
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
docker cp backend\add_item_description_file_columns.sql cahs_flow_project-postgres-1:/tmp/migration.sql

docker-compose exec postgres psql -U postgres -d procurement_dss -f /tmp/migration.sql

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo  Migration Completed Successfully!
    echo ========================================
    echo.
    echo + description column added
    echo + file_path column added
    echo + file_name column added
    echo + Index created
    echo + All existing data preserved
    echo.
    echo You can now add descriptions and attach files to project items!
    echo.
) else (
    echo.
    echo X Migration failed
    echo   Check database connection and try again
)

pause

