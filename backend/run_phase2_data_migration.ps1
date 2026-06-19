# Phase 2 Data Migration Execution Script for Windows PowerShell
# Executes all Phase 2 data migration scripts in order with validation
#
# Usage:
#   .\run_phase2_data_migration.ps1 [-SkipValidation]
#
# Environment Variables:
#   PGHOST - PostgreSQL host (default: localhost)
#   PGPORT - PostgreSQL port (default: 5432)
#   PGDATABASE - Database name (default: procurement_dss)
#   PGUSER - PostgreSQL user (default: postgres)
#   PGPASSWORD - PostgreSQL password (optional, will prompt if not set)
#   DATABASE_URL - Full connection string (overrides above if set)
#   DOCKER_CONTAINER - Docker container name (default: postgres)

param(
    [switch]$SkipValidation = $false
)

$ErrorActionPreference = "Stop"

# Database connection settings
$PGHOST = if ($env:PGHOST) { $env:PGHOST } else { "localhost" }
$PGPORT = if ($env:PGPORT) { $env:PGPORT } else { "5432" }
$PGDATABASE = if ($env:PGDATABASE) { $env:PGDATABASE } else { "procurement_dss" }
$PGUSER = if ($env:PGUSER) { $env:PGUSER } else { "postgres" }
$DOCKER_CONTAINER = if ($env:DOCKER_CONTAINER) { $env:DOCKER_CONTAINER } else { "postgres" }

# Script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$MIGRATION_DIR = $SCRIPT_DIR

# Track results
$SUCCESSFUL = @()
$SKIPPED = @()
$FAILED = @()

# Function to check Docker and auto-detect container
function Test-DockerContainer {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        return $false
    }
    
    # Check exact match first
    $containers = docker ps --format '{{.Names}}' 2>$null
    if ($containers -contains $DOCKER_CONTAINER) {
        return $true
    }
    
    # Auto-detect if default is "postgres"
    if ($DOCKER_CONTAINER -eq "postgres") {
        $postgresContainer = $containers | Where-Object { $_ -like "*postgres*" } | Select-Object -First 1
        if ($postgresContainer) {
            $script:DOCKER_CONTAINER = $postgresContainer
            Write-Host "Auto-detected Docker container: $DOCKER_CONTAINER" -ForegroundColor Cyan
            return $true
        }
    }
    
    return $false
}

# Function to check database connection
function Test-DatabaseConnection {
    Write-Host "Checking database connection..." -ForegroundColor Cyan
    
    # Auto-detect Docker if not explicitly disabled
    if (Test-DockerContainer) {
        try {
            $result = docker exec $DOCKER_CONTAINER psql -U $PGUSER -d $PGDATABASE -c "SELECT version();" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Connected to Docker container '$DOCKER_CONTAINER'" -ForegroundColor Green
                return $true
            }
        } catch {
            # Continue to direct connection
        }
    }
    
    # Try direct connection if DATABASE_URL is set
    if ($env:DATABASE_URL) {
        try {
            $result = psql "$env:DATABASE_URL" -c "SELECT version();" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Connected using DATABASE_URL" -ForegroundColor Green
                return $true
            }
        } catch {
            # Continue
        }
    }
    
    Write-Host "Failed to connect to database" -ForegroundColor Red
    Write-Host "  Connection attempts:" -ForegroundColor Gray
    if ($script:DOCKER_CONTAINER) {
        Write-Host "    - Docker container '$DOCKER_CONTAINER'" -ForegroundColor Gray
    }
    if ($env:DATABASE_URL) {
        Write-Host "    - DATABASE_URL" -ForegroundColor Gray
    } else {
        Write-Host "    - $PGHOST`:$PGPORT/$PGDATABASE as $PGUSER" -ForegroundColor Gray
    }
    return $false
}

# Function to execute SQL file
function Invoke-Migration {
    param(
        [string]$File,
        [string]$TaskNum,
        [string]$Description
    )
    
    Write-Host "Task $TaskNum : $Description" -ForegroundColor Yellow
    Write-Host "  File: $File" -ForegroundColor Gray
    
    if (-not (Test-Path $File)) {
        Write-Host "  SKIPPED: File not found" -ForegroundColor Yellow
        $script:SKIPPED += "$TaskNum`:$File"
        Write-Host ""
        return 2
    }
    
    try {
        $sqlContent = Get-Content -Path $File -Raw
        
        # Use Docker exec with stdin redirection
        # Suppress stderr (NOTICE messages) and only check exit code
        $exitCode = 0
        $errorOccurred = $false
        
        # Temporarily change error action to Continue to avoid stopping on NOTICE messages
        $oldErrorAction = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        
        try {
            if ($script:DOCKER_CONTAINER) {
                if ($env:DATABASE_URL) {
                    $sqlContent | docker exec -i $DOCKER_CONTAINER psql "$env:DATABASE_URL" --quiet 2>$null
                } else {
                    $sqlContent | docker exec -i $DOCKER_CONTAINER psql -U $PGUSER -d $PGDATABASE --quiet 2>$null
                }
                $exitCode = $LASTEXITCODE
            } elseif ($env:DATABASE_URL) {
                $sqlContent | psql "$env:DATABASE_URL" --quiet 2>$null
                $exitCode = $LASTEXITCODE
            } else {
                $sqlContent | psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE --quiet 2>$null
                $exitCode = $LASTEXITCODE
            }
        } catch {
            $errorOccurred = $true
        } finally {
            $ErrorActionPreference = $oldErrorAction
        }
        
        # Only treat non-zero exit code as error
        # PostgreSQL returns 0 for successful operations even with NOTICE messages
        if ($errorOccurred -or $exitCode -ne 0) {
            Write-Host "  FAILED" -ForegroundColor Red
            Write-Host "    Exit code: $exitCode" -ForegroundColor Red
            $script:FAILED += "$TaskNum`:$File"
            return 1
        } else {
            Write-Host "  SUCCESS" -ForegroundColor Green
            $script:SUCCESSFUL += "$TaskNum`:$File"
            return 0
        }
    } catch {
        Write-Host "  FAILED: $_" -ForegroundColor Red
        $script:FAILED += "$TaskNum`:$File"
        return 1
    }
}

# Main execution
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Phase 2 Data Migration Execution" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting migrations at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
if ($SkipValidation) {
    Write-Host "Validation script will be skipped" -ForegroundColor Yellow
}
Write-Host ""

if (-not (Test-DatabaseConnection)) {
    Write-Host "Cannot proceed without database connection" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Execute migrations
$migrations = @(
    @{ File = "create_migration_audit_tables.sql"; Task = "2.0"; Desc = "Create migration audit tables" },
    @{ File = "create_full_packages_for_project_items.sql"; Task = "2.1"; Desc = "Create FULL packages for project items" },
    @{ File = "populate_package_subitems.sql"; Task = "2.2"; Desc = "Populate package subitems" },
    @{ File = "link_procurement_options_to_packages.sql"; Task = "2.3"; Desc = "Link procurement options to packages" },
    @{ File = "link_finalized_decisions_to_packages.sql"; Task = "2.4"; Desc = "Link finalized decisions to packages" },
    @{ File = "link_delivery_options_to_packages.sql"; Task = "2.5"; Desc = "Link delivery options to packages" },
    @{ File = "normalize_supplier_names_to_ids.sql"; Task = "2.6"; Desc = "Normalize supplier names to IDs" },
    @{ File = "link_financial_records_to_packages.sql"; Task = "2.7"; Desc = "Link financial records to packages" },
    @{ File = "validate_phase2_migration.sql"; Task = "2.8"; Desc = "Validate Phase 2 migration" }
)

foreach ($migration in $migrations) {
    $filePath = Join-Path $MIGRATION_DIR $migration.File
    
    if ($migration.Task -eq "2.8" -and $SkipValidation) {
        Write-Host "Task $($migration.Task): $($migration.Desc)" -ForegroundColor Yellow
        Write-Host "  SKIPPED (-SkipValidation flag set)" -ForegroundColor Gray
        $SKIPPED += "$($migration.Task):$($migration.File)"
        Write-Host ""
        continue
    }
    
    $result = Invoke-Migration -File $filePath -TaskNum $migration.Task -Description $migration.Desc
    
    if ($result -eq 1) {
        Write-Host "STOPPING: Migration failed. Please fix errors before continuing." -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
}

# Final summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Migration Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Completed at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host ""

Write-Host "SUCCESSFUL: $($SUCCESSFUL.Count)" -ForegroundColor Green
foreach ($item in $SUCCESSFUL) {
    $parts = $item -split ':'
    Write-Host "  [OK] Task $($parts[0]): $($parts[1])" -ForegroundColor Green
}

Write-Host ""

if ($SKIPPED.Count -gt 0) {
    Write-Host "SKIPPED: $($SKIPPED.Count)" -ForegroundColor Yellow
    foreach ($item in $SKIPPED) {
        $parts = $item -split ':'
        Write-Host "  [SKIP] Task $($parts[0]): $($parts[1])" -ForegroundColor Yellow
    }
    Write-Host ""
}

if ($FAILED.Count -gt 0) {
    Write-Host "FAILED: $($FAILED.Count)" -ForegroundColor Red
    foreach ($item in $FAILED) {
        $parts = $item -split ':'
        Write-Host "  [FAIL] Task $($parts[0]): $($parts[1])" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "WARNING: Manual follow-up required before Phase 3" -ForegroundColor Red
    exit 1
} else {
    Write-Host "All migrations completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Review migration_audit_log table for execution details" -ForegroundColor Gray
    Write-Host "  2. Review migration_unmatched_suppliers table for manual supplier resolution" -ForegroundColor Gray
    Write-Host "  3. Run validation queries from PHASE2_MIGRATION_BLUEPRINT.md Section 4" -ForegroundColor Gray
    Write-Host "  4. Proceed to Phase 3 (Feature Flag Rollout)" -ForegroundColor Gray
}

