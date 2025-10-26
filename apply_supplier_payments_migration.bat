@echo off
echo Applying supplier payments table migration...

REM Set environment variables
set PGPASSWORD=your_password_here
set PGHOST=localhost
set PGPORT=5432
set PGDATABASE=procurement_dss
set PGUSER=postgres

REM Apply the migration
psql -h %PGHOST% -p %PGPORT% -U %PGUSER% -d %PGDATABASE% -f backend/add_supplier_payments_table.sql

if %ERRORLEVEL% EQU 0 (
    echo Migration applied successfully!
) else (
    echo Migration failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo Supplier payments table created successfully!
pause
