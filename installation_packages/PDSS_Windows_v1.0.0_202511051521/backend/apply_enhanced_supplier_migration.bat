@echo off
set PGHOST=localhost
set PGPORT=5432
set PGDATABASE=procurement_dss_db
set PGUSER=procurement_dss_user
set PGPASSWORD=procurement_dss_password

echo Applying Enhanced Supplier Management System Migration...
echo.

echo Step 1: Backing up existing supplier tables (if they exist)...
psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "DROP TABLE IF EXISTS supplier_documents_backup CASCADE;"
psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "DROP TABLE IF EXISTS supplier_contacts_backup CASCADE;"
psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "DROP TABLE IF EXISTS suppliers_backup CASCADE;"

psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "CREATE TABLE suppliers_backup AS SELECT * FROM suppliers;" 2>nul
psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "CREATE TABLE supplier_contacts_backup AS SELECT * FROM supplier_contacts;" 2>nul
psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "CREATE TABLE supplier_documents_backup AS SELECT * FROM supplier_documents;" 2>nul

echo Step 2: Applying enhanced supplier tables migration...
psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -f create_enhanced_supplier_tables.sql

if %ERRORLEVEL% NEQ 0 (
    echo Error applying migration. Restoring from backup...
    psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "DROP TABLE IF EXISTS supplier_documents CASCADE;"
    psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "DROP TABLE IF EXISTS supplier_contacts CASCADE;"
    psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "DROP TABLE IF EXISTS suppliers CASCADE;"
    
    psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "CREATE TABLE suppliers AS SELECT * FROM suppliers_backup;" 2>nul
    psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "CREATE TABLE supplier_contacts AS SELECT * FROM supplier_contacts_backup;" 2>nul
    psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "CREATE TABLE supplier_documents AS SELECT * FROM supplier_documents_backup;" 2>nul
    
    echo Migration failed. Please check the error messages above.
    exit /b %ERRORLEVEL%
) else (
    echo Step 3: Migration applied successfully!
    echo.
    echo Step 4: Verifying enhanced supplier tables...
    psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "\dt suppliers*"
    echo.
    echo Step 5: Checking sample data...
    psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "SELECT COUNT(*) as supplier_count FROM suppliers;"
    psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "SELECT COUNT(*) as contact_count FROM supplier_contacts;"
    psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "SELECT COUNT(*) as document_count FROM supplier_documents;"
    echo.
    echo Step 6: Cleaning up backup tables...
    psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "DROP TABLE IF EXISTS supplier_documents_backup CASCADE;"
    psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "DROP TABLE IF EXISTS supplier_contacts_backup CASCADE;"
    psql -h %PGHOST% -p %PGPORT% -d %PGDATABASE% -U %PGUSER% -c "DROP TABLE IF EXISTS suppliers_backup CASCADE;"
    echo.
    echo ✅ Enhanced Supplier Management System Migration Completed Successfully!
    echo.
    echo 📋 What was implemented:
    echo    - Comprehensive supplier profiles with all business information
    echo    - Multi-level contact management system
    echo    - Document compliance tracking
    echo    - Performance metrics and rating system
    echo    - Social media integration
    echo    - Multi-language support
    echo    - Complete audit trail
    echo.
    echo 🚀 Next Steps:
    echo    1. Restart the backend service: docker-compose restart backend
    echo    2. Restart the frontend service: docker-compose restart frontend
    echo    3. Create upload directory: mkdir -p uploads/supplier_documents
    echo    4. Test the enhanced supplier management system
    echo.
)

pause
