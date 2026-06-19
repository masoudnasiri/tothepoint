#!/bin/bash

# Phase 2 Data Migration Execution Script for Linux
# Executes all Phase 2 data migration scripts in order with validation
#
# Usage:
#   ./run_phase2_data_migration.sh [--skip-validation]
#   or
#   bash run_phase2_data_migration.sh [--skip-validation]
#
# Environment Variables:
#   PGHOST - PostgreSQL host (default: localhost)
#   PGPORT - PostgreSQL port (default: 5432)
#   PGDATABASE - Database name (default: procurement_dss)
#   PGUSER - PostgreSQL user (default: postgres)
#   PGPASSWORD - PostgreSQL password (optional, will prompt if not set)
#   DATABASE_URL - Full connection string (overrides above if set)
#   USE_DOCKER - Set to 'true' to use Docker exec method (auto-detected if Docker available)
#   DOCKER_CONTAINER - Docker container name (default: postgres)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Database connection settings
PGHOST=${PGHOST:-localhost}
PGPORT=${PGPORT:-5432}
PGDATABASE=${PGDATABASE:-procurement_dss}
PGUSER=${PGUSER:-postgres}

# Docker settings (if using Docker)
DOCKER_CONTAINER=${DOCKER_CONTAINER:-postgres}
USE_DOCKER=${USE_DOCKER:-false}

# Script directory (where migrations are located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATION_DIR="${SCRIPT_DIR}"

# Parse arguments
SKIP_VALIDATION=false
if [[ "$1" == "--skip-validation" ]]; then
    SKIP_VALIDATION=true
fi

# Track results
SUCCESSFUL=()
SKIPPED=()
FAILED=()

# Function to print colored output
print_info() {
    echo -e "${CYAN}$1${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

print_gray() {
    echo -e "${GRAY}$1${NC}"
}

# Function to check if Docker is available and container is running
check_docker() {
    if command -v docker > /dev/null 2>&1; then
        # Check exact match first
        if docker ps --format '{{.Names}}' | grep -q "^${DOCKER_CONTAINER}$"; then
            return 0
        fi
        # Check if container name contains "postgres" (for Docker Compose naming like pdss-postgres-1)
        if [ "$DOCKER_CONTAINER" = "postgres" ]; then
            if docker ps --format '{{.Names}}' | grep -q "postgres"; then
                # Find the actual container name
                actual_container=$(docker ps --format '{{.Names}}' | grep "postgres" | head -n1)
                if [ -n "$actual_container" ]; then
                    DOCKER_CONTAINER="$actual_container"
                    print_info "Auto-detected Docker container: $DOCKER_CONTAINER"
                    return 0
                fi
            fi
        fi
    fi
    return 1
}

# Function to check database connection
check_connection() {
    print_info "Checking database connection..."
    
    # Auto-detect Docker if connection fails and Docker is available
    if [ "$USE_DOCKER" != "true" ] && check_docker; then
        print_info "Detected Docker container '$DOCKER_CONTAINER'. Trying Docker connection..."
        USE_DOCKER=true
    fi
    
    if [ "$USE_DOCKER" = "true" ]; then
        # Try Docker connection
        if docker exec "$DOCKER_CONTAINER" psql -U "$PGUSER" -d "$PGDATABASE" -c "SELECT version();" > /dev/null 2>&1; then
            print_success "✓ Connected to Docker container '$DOCKER_CONTAINER'"
            return 0
        else
            print_error "✗ Failed to connect via Docker container '$DOCKER_CONTAINER'"
            print_info "Trying direct connection as fallback..."
        fi
    fi
    
    if [ -n "$DATABASE_URL" ]; then
        psql "$DATABASE_URL" -c "SELECT version();" > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            print_success "✓ Connected using DATABASE_URL"
            return 0
        fi
    else
        export PGPASSWORD=${PGPASSWORD:-}
        psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "SELECT version();" > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            print_success "✓ Connected to $PGHOST:$PGPORT/$PGDATABASE as $PGUSER"
            return 0
        fi
    fi
    
    print_error "✗ Failed to connect to database"
    print_info "Connection attempts:"
    if [ "$USE_DOCKER" = "true" ]; then
        print_gray "  - Docker container '$DOCKER_CONTAINER'"
    fi
    if [ -n "$DATABASE_URL" ]; then
        print_gray "  - DATABASE_URL"
    else
        print_gray "  - $PGHOST:$PGPORT/$PGDATABASE as $PGUSER"
    fi
    return 1
}

# Function to execute SQL file
execute_migration() {
    local file=$1
    local task_num=$2
    local description=$3
    
    print_warning "Task $task_num: $description"
    print_gray "  File: $file"
    
    # Check if file exists
    if [ ! -f "$file" ]; then
        print_warning "  ⚠️  SKIPPED: File not found"
        SKIPPED+=("$task_num:$file")
        echo ""
        return 2
    fi
    
    # Execute migration
    if [ "$USE_DOCKER" = "true" ]; then
        # Use stdin redirection with stderr suppressed (NOTICE messages go to stderr)
        # Capture exit code separately
        docker exec -i "$DOCKER_CONTAINER" psql -U "$PGUSER" -d "$PGDATABASE" < "$file" > /dev/null 2>/dev/null
        result=$?
    elif [ -n "$DATABASE_URL" ]; then
        psql "$DATABASE_URL" -f "$file" > /dev/null 2>/dev/null
        result=$?
    else
        export PGPASSWORD=${PGPASSWORD:-}
        psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -f "$file" > /dev/null 2>/dev/null
        result=$?
    fi
    
    if [ $result -eq 0 ]; then
        print_success "  ✓ SUCCESS"
        SUCCESSFUL+=("$task_num:$file")
        return 0
    else
        print_error "  ✗ FAILED"
        FAILED+=("$task_num:$file")
        return 1
    fi
}

# Main execution
main() {
    print_info "=== Phase 2 Data Migration Execution ==="
    print_info "Starting migrations at $(date '+%Y-%m-%d %H:%M:%S')"
    if [ "$SKIP_VALIDATION" = "true" ]; then
        print_warning "Validation script will be skipped"
    fi
    echo ""
    
    # Check database connection
    if ! check_connection; then
        print_error "Cannot proceed without database connection"
        exit 1
    fi
    
    echo ""
    
    # Task 2.0: Create migration audit tables
    if execute_migration "$MIGRATION_DIR/create_migration_audit_tables.sql" "2.0" "Create migration audit tables"; then
        echo ""
    else
        print_error "⚠️  STOPPING: Migration failed. Please fix errors before continuing."
        exit 1
    fi
    
    # Task 2.1: Create FULL packages for project items
    if execute_migration "$MIGRATION_DIR/create_full_packages_for_project_items.sql" "2.1" "Create FULL packages for project items"; then
        echo ""
    else
        print_error "⚠️  STOPPING: Migration failed. Please fix errors before continuing."
        exit 1
    fi
    
    # Task 2.2: Populate package subitems
    if execute_migration "$MIGRATION_DIR/populate_package_subitems.sql" "2.2" "Populate package subitems"; then
        echo ""
    else
        print_error "⚠️  STOPPING: Migration failed. Please fix errors before continuing."
        exit 1
    fi
    
    # Task 2.3: Link procurement options to packages
    if execute_migration "$MIGRATION_DIR/link_procurement_options_to_packages.sql" "2.3" "Link procurement options to packages"; then
        echo ""
    else
        print_error "⚠️  STOPPING: Migration failed. Please fix errors before continuing."
        exit 1
    fi
    
    # Task 2.4: Link finalized decisions to packages
    if execute_migration "$MIGRATION_DIR/link_finalized_decisions_to_packages.sql" "2.4" "Link finalized decisions to packages"; then
        echo ""
    else
        print_error "⚠️  STOPPING: Migration failed. Please fix errors before continuing."
        exit 1
    fi
    
    # Task 2.5: Link delivery options to packages
    if execute_migration "$MIGRATION_DIR/link_delivery_options_to_packages.sql" "2.5" "Link delivery options to packages"; then
        echo ""
    else
        print_error "⚠️  STOPPING: Migration failed. Please fix errors before continuing."
        exit 1
    fi
    
    # Task 2.6: Normalize supplier names to IDs
    if execute_migration "$MIGRATION_DIR/normalize_supplier_names_to_ids.sql" "2.6" "Normalize supplier names to IDs"; then
        echo ""
    else
        print_error "⚠️  STOPPING: Migration failed. Please fix errors before continuing."
        exit 1
    fi
    
    # Task 2.7: Link financial records to packages
    if execute_migration "$MIGRATION_DIR/link_financial_records_to_packages.sql" "2.7" "Link financial records to packages"; then
        echo ""
    else
        print_error "⚠️  STOPPING: Migration failed. Please fix errors before continuing."
        exit 1
    fi
    
    # Task 2.8: Validate Phase 2 migration
    if [ "$SKIP_VALIDATION" = "false" ]; then
        if execute_migration "$MIGRATION_DIR/validate_phase2_migration.sql" "2.8" "Validate Phase 2 migration"; then
            echo ""
        else
            print_warning "⚠️  Validation script failed, but data migration may have succeeded. Review manually."
            echo ""
        fi
    else
        print_warning "Task 2.8: Validate Phase 2 migration"
        print_gray "  SKIPPED (--skip-validation flag set)"
        SKIPPED+=("2.8:validate_phase2_migration.sql")
        echo ""
    fi
    
    # Final summary
    print_info "=== Migration Summary ==="
    print_info "Completed at $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    print_success "SUCCESSFUL: ${#SUCCESSFUL[@]}"
    for item in "${SUCCESSFUL[@]}"; do
        IFS=':' read -r task file <<< "$item"
        print_success "  ✓ Task $task: $file"
    done
    
    echo ""
    
    if [ ${#SKIPPED[@]} -gt 0 ]; then
        print_warning "SKIPPED: ${#SKIPPED[@]}"
        for item in "${SKIPPED[@]}"; do
            IFS=':' read -r task file <<< "$item"
            print_warning "  ⊘ Task $task: $file"
        done
        echo ""
    fi
    
    if [ ${#FAILED[@]} -gt 0 ]; then
        print_error "FAILED: ${#FAILED[@]}"
        for item in "${FAILED[@]}"; do
            IFS=':' read -r task file <<< "$item"
            print_error "  ✗ Task $task: $file"
        done
        echo ""
        print_error "⚠️  Manual follow-up required before Phase 3"
        exit 1
    else
        print_success "✅ All migrations completed successfully!"
        print_info ""
        print_info "Next steps:"
        print_info "  1. Review migration_audit_log table for execution details"
        print_info "  2. Review migration_unmatched_suppliers table for manual supplier resolution"
        print_info "  3. Run validation queries from PHASE2_MIGRATION_BLUEPRINT.md Section 4"
        print_info "  4. Proceed to Phase 3 (Feature Flag Rollout)"
    fi
}

# Run main function
main

