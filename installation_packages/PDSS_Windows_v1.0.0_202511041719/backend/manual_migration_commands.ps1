# Manual Migration Commands for Enhanced Supplier Management System
# Run these commands one by one in PowerShell or Command Prompt

Write-Host "=== Enhanced Supplier Management System Migration ===" -ForegroundColor Green
Write-Host ""

# Step 1: Check if Docker is running
Write-Host "Step 1: Check if Docker is running..." -ForegroundColor Yellow
docker ps

# Step 2: Check if PostgreSQL container is running
Write-Host "Step 2: Check if PostgreSQL container is running..." -ForegroundColor Yellow
docker exec -it procurement_dss_db psql --version

# Step 3: Copy migration script to container
Write-Host "Step 3: Copy migration script to container..." -ForegroundColor Yellow
docker cp create_enhanced_supplier_tables.sql procurement_dss_db:/tmp/create_enhanced_supplier_tables.sql

# Step 4: Apply migration
Write-Host "Step 4: Apply migration..." -ForegroundColor Yellow
docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -f /tmp/create_enhanced_supplier_tables.sql

# Step 5: Verify tables were created
Write-Host "Step 5: Verify tables were created..." -ForegroundColor Yellow
docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "\dt suppliers*"

# Step 6: Check sample data
Write-Host "Step 6: Check sample data..." -ForegroundColor Yellow
docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "SELECT COUNT(*) as supplier_count FROM suppliers;"
docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "SELECT COUNT(*) as contact_count FROM supplier_contacts;"
docker exec -it procurement_dss_db psql -U procurement_dss_user -d procurement_dss_db -c "SELECT COUNT(*) as document_count FROM supplier_documents;"

# Step 7: Cleanup
Write-Host "Step 7: Cleanup..." -ForegroundColor Yellow
docker exec -it procurement_dss_db rm -f /tmp/create_enhanced_supplier_tables.sql

Write-Host ""
Write-Host "✅ Migration completed! Next steps:" -ForegroundColor Green
Write-Host "1. docker-compose restart backend" -ForegroundColor Cyan
Write-Host "2. docker-compose restart frontend" -ForegroundColor Cyan
Write-Host "3. mkdir -p uploads/supplier_documents" -ForegroundColor Cyan
Write-Host "4. Test at /suppliers" -ForegroundColor Cyan
