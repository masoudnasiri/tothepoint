@echo off
echo Applying Enhanced Supplier Management System Migration using Docker...
echo.

echo Step 1: Checking if Docker is running...
docker ps >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo Step 2: Checking if PostgreSQL container is running...
docker exec -it cahs_flow_project-postgres-1 psql --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: PostgreSQL container is not running. Please start the platform first with:
    echo docker-compose up -d
    pause
    exit /b 1
)

echo Step 3: Backing up existing supplier tables (if they exist)...
docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS supplier_documents_backup CASCADE;" 2>nul
docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS supplier_contacts_backup CASCADE;" 2>nul
docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS suppliers_backup CASCADE;" 2>nul

docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "CREATE TABLE suppliers_backup AS SELECT * FROM suppliers;" 2>nul
docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "CREATE TABLE supplier_contacts_backup AS SELECT * FROM supplier_contacts;" 2>nul
docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "CREATE TABLE supplier_documents_backup AS SELECT * FROM supplier_documents;" 2>nul

echo Step 4: Copying migration script to container...
docker cp create_enhanced_supplier_tables.sql cahs_flow_project-postgres-1:/tmp/create_enhanced_supplier_tables.sql

echo Step 5: Applying enhanced supplier tables migration...
docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -f /tmp/create_enhanced_supplier_tables.sql

if %ERRORLEVEL% NEQ 0 (
    echo Error applying migration. Restoring from backup...
    docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS supplier_documents CASCADE;"
    docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS supplier_contacts CASCADE;"
    docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS suppliers CASCADE;"
    
    docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "CREATE TABLE suppliers AS SELECT * FROM suppliers_backup;" 2>nul
    docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "CREATE TABLE supplier_contacts AS SELECT * FROM supplier_contacts_backup;" 2>nul
    docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "CREATE TABLE supplier_documents AS SELECT * FROM supplier_documents_backup;" 2>nul
    
    echo Migration failed. Please check the error messages above.
    pause
    exit /b %ERRORLEVEL%
) else (
    echo Step 6: Migration applied successfully!
    echo.
    echo Step 7: Verifying enhanced supplier tables...
    docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "\dt suppliers*"
    echo.
    echo Step 8: Checking sample data...
    docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "SELECT COUNT(*) as supplier_count FROM suppliers;"
    docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "SELECT COUNT(*) as contact_count FROM supplier_contacts;"
    docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "SELECT COUNT(*) as document_count FROM supplier_documents;"
    echo.
    echo Step 9: Cleaning up backup tables...
    docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS supplier_documents_backup CASCADE;"
    docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS supplier_contacts_backup CASCADE;"
    docker exec -it cahs_flow_project-postgres-1 psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS suppliers_backup CASCADE;"
    echo.
    echo Step 10: Cleaning up migration file...
    docker exec -it cahs_flow_project-postgres-1 rm -f /tmp/create_enhanced_supplier_tables.sql
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
    echo    4. Test the enhanced supplier management system at /suppliers
    echo.
)

pause
