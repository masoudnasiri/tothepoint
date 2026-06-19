@echo off
echo Applying Supplier Management System Migration...
echo.

REM Check if PostgreSQL is available
psql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: PostgreSQL psql command not found. Please ensure PostgreSQL is installed and in PATH.
    pause
    exit /b 1
)

REM Set database connection parameters
set DB_HOST=localhost
set DB_PORT=5432
set DB_NAME=procurement_dss
set DB_USER=postgres
set DB_PASSWORD=postgres

echo Connecting to database: %DB_NAME% on %DB_HOST%:%DB_PORT%
echo User: %DB_USER%
echo.

REM Apply the migration
psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -f create_supplier_tables.sql

if %errorlevel% equ 0 (
    echo.
    echo ✅ Supplier Management System migration completed successfully!
    echo.
    echo Created tables:
    echo - suppliers
    echo - supplier_contacts  
    echo - supplier_documents
    echo.
    echo Sample data inserted:
    echo - 5 sample suppliers
    echo - 5 sample contacts
    echo - 5 sample documents
    echo.
    echo Next steps:
    echo 1. Restart the backend service
    echo 2. Test the supplier management functionality
    echo 3. Create uploads/supplier_documents directory
) else (
    echo.
    echo ❌ Migration failed! Please check the error messages above.
    echo.
    echo Common issues:
    echo - Database connection failed
    echo - User doesn't have sufficient permissions
    echo - Tables already exist
    echo.
)

echo.
pause
