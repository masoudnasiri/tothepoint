#!/bin/bash

# Phase 1 Migration Execution Script for Linux
# Executes all Phase 1 additive migrations in order with validation
#
# Usage:
#   ./execute_phase1_migrations.sh
#   or
#   bash execute_phase1_migrations.sh
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
        # Copy file to container and execute, or use stdin
        docker exec -i "$DOCKER_CONTAINER" psql -U "$PGUSER" -d "$PGDATABASE" < "$file" > /dev/null 2>&1
        result=$?
    elif [ -n "$DATABASE_URL" ]; then
        psql "$DATABASE_URL" -f "$file" > /dev/null 2>&1
        result=$?
    else
        export PGPASSWORD=${PGPASSWORD:-}
        psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -f "$file" > /dev/null 2>&1
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

# Function to run validation query
run_validation() {
    local query=$1
    local description=$2
    
    print_gray "  Running validation: $description"
    
    if [ "$USE_DOCKER" = "true" ]; then
        docker exec "$DOCKER_CONTAINER" psql -U "$PGUSER" -d "$PGDATABASE" -c "$query" 2>&1
    elif [ -n "$DATABASE_URL" ]; then
        psql "$DATABASE_URL" -c "$query" 2>&1
    else
        export PGPASSWORD=${PGPASSWORD:-}
        psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "$query" 2>&1
    fi
}

# Function to check if migration 1.7 already applied
check_migration_1_7() {
    print_gray "  Checking if migration 1.7 already applied..."
    
    local query="SELECT numeric_precision FROM information_schema.columns WHERE table_name = 'delivery_options' AND column_name = 'invoice_amount_per_unit';"
    
    if [ "$USE_DOCKER" = "true" ]; then
        result=$(docker exec "$DOCKER_CONTAINER" psql -U "$PGUSER" -d "$PGDATABASE" -t -c "$query" 2>&1 | tr -d ' ')
    elif [ -n "$DATABASE_URL" ]; then
        result=$(psql "$DATABASE_URL" -t -c "$query" 2>&1 | tr -d ' ')
    else
        export PGPASSWORD=${PGPASSWORD:-}
        result=$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -t -c "$query" 2>&1 | tr -d ' ')
    fi
    
    if echo "$result" | grep -q "18"; then
        print_success "  ✓ Already applied (precision is NUMERIC(18,2))"
        return 0
    else
        return 1
    fi
}

# Main execution
main() {
    print_info "=== Phase 1 Migration Execution ==="
    print_info "Starting migrations at $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # Check database connection
    if ! check_connection; then
        print_error "Cannot proceed without database connection"
        exit 1
    fi
    
    echo ""
    
    # Task 1.1: Create procurement_packages table
    if execute_migration "$MIGRATION_DIR/create_procurement_packages_table.sql" "1.1" "Create procurement_packages table"; then
        run_validation "\d procurement_packages" "Table structure"
        count_query="SELECT COUNT(*) FROM procurement_packages;"
        if [ "$USE_DOCKER" = "true" ]; then
            count=$(docker exec "$DOCKER_CONTAINER" psql -U "$PGUSER" -d "$PGDATABASE" -t -c "$count_query" 2>&1 | tr -d ' ')
        elif [ -n "$DATABASE_URL" ]; then
            count=$(psql "$DATABASE_URL" -t -c "$count_query" 2>&1 | tr -d ' ')
        else
            export PGPASSWORD=${PGPASSWORD:-}
            count=$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -t -c "$count_query" 2>&1 | tr -d ' ')
        fi
        print_success "  Table exists. Current row count: $count"
        echo ""
    else
        print_error "⚠️  STOPPING: Migration failed. Please fix errors before continuing."
        exit 1
    fi
    
    # Task 1.2: Create package_subitems table
    if execute_migration "$MIGRATION_DIR/create_package_subitems_table.sql" "1.2" "Create package_subitems table"; then
        run_validation "\d package_subitems" "Table structure"
        echo ""
    else
        print_error "⚠️  STOPPING: Migration failed. Please fix errors before continuing."
        exit 1
    fi
    
    # Task 1.3: Create package_payments table
    if execute_migration "$MIGRATION_DIR/create_package_payments_table.sql" "1.3" "Create package_payments table"; then
        run_validation "\d package_payments" "Table structure"
        echo ""
    else
        print_error "⚠️  STOPPING: Migration failed. Please fix errors before continuing."
        exit 1
    fi
    
    # Task 1.4: Add package_id columns
    if execute_migration "$MIGRATION_DIR/add_package_id_columns.sql" "1.4" "Add package_id columns"; then
        run_validation "SELECT table_name, column_name, is_nullable FROM information_schema.columns WHERE column_name = 'package_id' ORDER BY table_name;" "package_id columns"
        echo ""
    else
        print_error "⚠️  STOPPING: Migration failed. Please fix errors before continuing."
        exit 1
    fi
    
    # Task 1.5: Make project_item_id nullable in delivery_options
    if execute_migration "$MIGRATION_DIR/make_delivery_options_project_item_nullable.sql" "1.5" "Make project_item_id nullable in delivery_options"; then
        run_validation "SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name = 'delivery_options' AND column_name IN ('project_item_id', 'package_id');" "Nullable columns"
        echo ""
    else
        print_error "⚠️  STOPPING: Migration failed. Please fix errors before continuing."
        exit 1
    fi
    
    # Task 1.6: Add supplier_id to supplier_payments
    if execute_migration "$MIGRATION_DIR/add_supplier_id_to_supplier_payments.sql" "1.6" "Add supplier_id to supplier_payments"; then
        run_validation "SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name = 'supplier_payments' AND column_name = 'supplier_id';" "supplier_id column"
        echo ""
    else
        print_error "⚠️  STOPPING: Migration failed. Please fix errors before continuing."
        exit 1
    fi
    
    # Task 1.7: Increase invoice_amount_per_unit precision
    print_warning "Task 1.7: Increase invoice_amount_per_unit precision"
    print_gray "  File: increase_invoice_amount_precision.sql"
    
    if check_migration_1_7; then
        SKIPPED+=("1.7:increase_invoice_amount_precision.sql")
        echo ""
    else
        if execute_migration "$MIGRATION_DIR/increase_invoice_amount_precision.sql" "1.7" "Increase invoice_amount_per_unit precision"; then
            echo ""
        else
            print_error "⚠️  STOPPING: Migration failed. Please fix errors before continuing."
            exit 1
        fi
    fi
    
    # Task 1.8: Add CHECK constraint to procurement_options
    if execute_migration "$MIGRATION_DIR/add_procurement_options_check_constraint.sql" "1.8" "Add CHECK constraint to procurement_options"; then
        run_validation "SELECT constraint_name FROM information_schema.table_constraints WHERE table_name = 'procurement_options' AND constraint_name = 'check_procurement_option_reference';" "CHECK constraint"
        echo ""
    else
        print_error "⚠️  STOPPING: Migration failed. Please fix errors before continuing."
        exit 1
    fi
    
    # Final validation
    print_info "=== Final Validation ==="
    print_gray "Checking all new tables exist..."
    run_validation "SELECT table_name FROM information_schema.tables WHERE table_name IN ('procurement_packages', 'package_subitems', 'package_payments') ORDER BY table_name;" "New tables"
    
    print_gray "Checking CHECK constraints..."
    run_validation "SELECT table_name, constraint_name FROM information_schema.table_constraints WHERE constraint_name LIKE 'check_%' AND table_name IN ('delivery_options', 'procurement_options', 'supplier_payments') ORDER BY table_name;" "CHECK constraints"
    
    echo ""
    
    # Summary
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
        print_error "⚠️  Manual follow-up required before Phase 2"
        exit 1
    else
        print_success "✅ All migrations completed successfully!"
        print_success "   Ready for Phase 2 (Data Migration)"
    fi
}

# Run main function
main

