# Enhanced Supplier Management System Migration using Docker
# PowerShell version for better compatibility

Write-Host "Applying Enhanced Supplier Management System Migration using Docker..." -ForegroundColor Green
Write-Host ""

# Step 1: Check if Docker is running
Write-Host "Step 1: Checking if Docker is running..." -ForegroundColor Yellow
try {
    $dockerCheck = docker ps 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not running"
    }
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 2: Check if PostgreSQL container is running
Write-Host "Step 2: Checking if PostgreSQL container is running..." -ForegroundColor Yellow
try {
    $pgCheck = docker exec -it procurement_dss_db psql --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL container is not running"
    }
    Write-Host "✅ PostgreSQL container is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: PostgreSQL container is not running. Please start the platform first with:" -ForegroundColor Red
    Write-Host "docker-compose up -d" -ForegroundColor Cyan
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 3: Backup existing tables
Write-Host "Step 3: Backing up existing supplier tables (if they exist)..." -ForegroundColor Yellow
docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS supplier_documents_backup CASCADE;" 2>$null
docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS supplier_contacts_backup CASCADE;" 2>$null
docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS suppliers_backup CASCADE;" 2>$null

docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "CREATE TABLE suppliers_backup AS SELECT * FROM suppliers;" 2>$null
docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "CREATE TABLE supplier_contacts_backup AS SELECT * FROM supplier_contacts;" 2>$null
docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "CREATE TABLE supplier_documents_backup AS SELECT * FROM supplier_documents;" 2>$null

# Step 4: Copy migration script to container
Write-Host "Step 4: Copying migration script to container..." -ForegroundColor Yellow
docker cp create_enhanced_supplier_tables.sql procurement_dss_db:/tmp/create_enhanced_supplier_tables.sql

# Step 5: Apply migration
Write-Host "Step 5: Applying enhanced supplier tables migration..." -ForegroundColor Yellow
$migrationResult = docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -f /tmp/create_enhanced_supplier_tables.sql

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error applying migration. Restoring from backup..." -ForegroundColor Red
    
    docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS supplier_documents CASCADE;"
    docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS supplier_contacts CASCADE;"
    docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS suppliers CASCADE;"
    
    docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "CREATE TABLE suppliers AS SELECT * FROM suppliers_backup;" 2>$null
    docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "CREATE TABLE supplier_contacts AS SELECT * FROM supplier_contacts_backup;" 2>$null
    docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "CREATE TABLE supplier_documents AS SELECT * FROM supplier_documents_backup;" 2>$null
    
    Write-Host "❌ Migration failed. Please check the error messages above." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit $LASTEXITCODE
} else {
    Write-Host "✅ Step 6: Migration applied successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Step 7: Verify tables
    Write-Host "Step 7: Verifying enhanced supplier tables..." -ForegroundColor Yellow
    docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "\dt suppliers*"
    Write-Host ""
    
    # Step 8: Check sample data
    Write-Host "Step 8: Checking sample data..." -ForegroundColor Yellow
    docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "SELECT COUNT(*) as supplier_count FROM suppliers;"
    docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "SELECT COUNT(*) as contact_count FROM supplier_contacts;"
    docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "SELECT COUNT(*) as document_count FROM supplier_documents;"
    Write-Host ""
    
    # Step 9: Cleanup
    Write-Host "Step 9: Cleaning up backup tables..." -ForegroundColor Yellow
    docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS supplier_documents_backup CASCADE;"
    docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS supplier_contacts_backup CASCADE;"
    docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "DROP TABLE IF EXISTS suppliers_backup CASCADE;"
    
    Write-Host "Step 10: Cleaning up migration file..." -ForegroundColor Yellow
    docker exec -it procurement_dss_db rm -f /tmp/create_enhanced_supplier_tables.sql
    Write-Host ""
    
    Write-Host "🎉 Enhanced Supplier Management System Migration Completed Successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 What was implemented:" -ForegroundColor Cyan
    Write-Host "   - Comprehensive supplier profiles with all business information" -ForegroundColor White
    Write-Host "   - Multi-level contact management system" -ForegroundColor White
    Write-Host "   - Document compliance tracking" -ForegroundColor White
    Write-Host "   - Performance metrics and rating system" -ForegroundColor White
    Write-Host "   - Social media integration" -ForegroundColor White
    Write-Host "   - Multi-language support" -ForegroundColor White
    Write-Host "   - Complete audit trail" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
    Write-Host "   1. Restart the backend service: docker-compose restart backend" -ForegroundColor White
    Write-Host "   2. Restart the frontend service: docker-compose restart frontend" -ForegroundColor White
    Write-Host "   3. Create upload directory: mkdir -p uploads/supplier_documents" -ForegroundColor White
    Write-Host "   4. Test the enhanced supplier management system at /suppliers" -ForegroundColor White
    Write-Host ""
}

Read-Host "Press Enter to exit"
