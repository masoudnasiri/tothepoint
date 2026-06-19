# Complete Data Wipe Script - Preserve Users and Decision Factor Weights Only
# This script safely removes all operational data while preserving system configuration

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  COMPLETE DATA WIPE - PRESERVE USERS & WEIGHTS" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Check if PostgreSQL container is running
Write-Host "Checking PostgreSQL container status..." -ForegroundColor Yellow
$containerStatus = docker ps --filter "name=cahs_flow_project-postgres-1" --format "table {{.Status}}"
if ($containerStatus -notmatch "Up") {
    Write-Host "ERROR: PostgreSQL container is not running!" -ForegroundColor Red
    Write-Host "Please start the platform first with: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "PostgreSQL container is running ✓" -ForegroundColor Green
Write-Host ""

# Show current data counts before wipe
Write-Host "Current data counts before wipe:" -ForegroundColor Yellow
$sqlQuery = @"
SELECT 
    'users' as table_name, count(*) as count FROM users 
UNION ALL 
SELECT 'decision_factor_weights', count(*) FROM decision_factor_weights 
UNION ALL 
SELECT 'projects', count(*) FROM projects 
UNION ALL 
SELECT 'procurement_options', count(*) FROM procurement_options 
UNION ALL 
SELECT 'finalized_decisions', count(*) FROM finalized_decisions 
UNION ALL 
SELECT 'suppliers', count(*) FROM suppliers 
ORDER BY table_name;
"@
docker exec cahs_flow_project-postgres-1 psql -U postgres -d procurement_dss -c $sqlQuery

Write-Host ""
Write-Host "WARNING: This will permanently delete ALL operational data!" -ForegroundColor Red
Write-Host "Only users and decision_factor_weights will be preserved." -ForegroundColor Red
Write-Host ""

# Confirmation prompt
$confirmation = Read-Host "Are you sure you want to proceed? Type 'YES' to confirm"
if ($confirmation -ne "YES") {
    Write-Host "Operation cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Executing data wipe..." -ForegroundColor Yellow

# Execute the SQL script
try {
    docker exec -i cahs_flow_project-postgres-1 psql -U postgres -d procurement_dss < backend/complete_data_wipe_preserve_users_weights.sql
    
    Write-Host ""
    Write-Host "===============================================" -ForegroundColor Green
    Write-Host "  DATA WIPE COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "===============================================" -ForegroundColor Green
    Write-Host ""
    
    # Show final data counts
    Write-Host "Final data counts after wipe:" -ForegroundColor Green
    $finalQuery = @"
    SELECT 
        'users' as preserved_table, 
        count(*) as record_count 
    FROM users 
    UNION ALL 
    SELECT 
        'decision_factor_weights' as preserved_table, 
        count(*) as record_count 
    FROM decision_factor_weights
    UNION ALL
    SELECT 
        'projects' as wiped_table, 
        count(*) as record_count 
    FROM projects
    UNION ALL
    SELECT 
        'procurement_options' as wiped_table, 
        count(*) as record_count 
    FROM procurement_options
    UNION ALL
    SELECT 
        'finalized_decisions' as wiped_table, 
        count(*) as record_count 
    FROM finalized_decisions
    ORDER BY preserved_table, wiped_table;
    "@
    docker exec cahs_flow_project-postgres-1 psql -U postgres -d procurement_dss -c $finalQuery
    
    Write-Host ""
    Write-Host "✓ Users and decision factor weights preserved" -ForegroundColor Green
    Write-Host "✓ All operational data removed" -ForegroundColor Green
    Write-Host "✓ Database sequences reset" -ForegroundColor Green
    Write-Host "✓ Platform ready for fresh data entry" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Restart the backend container to clear any cached data" -ForegroundColor White
    Write-Host "2. Create new projects and items" -ForegroundColor White
    Write-Host "3. Add suppliers through the Suppliers management page" -ForegroundColor White
    Write-Host "4. Create procurement options" -ForegroundColor White
    
} catch {
    Write-Host ""
    Write-Host "ERROR: Data wipe failed!" -ForegroundColor Red
    Write-Host "Error details: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check the PostgreSQL container logs:" -ForegroundColor Yellow
    Write-Host "docker logs cahs_flow_project-postgres-1" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "Data wipe completed successfully!" -ForegroundColor Green
