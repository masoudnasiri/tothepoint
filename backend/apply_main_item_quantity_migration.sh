#!/bin/bash
#
# Migration Script: Add main_item_quantity column to procurement_packages table
# This script applies the migration to add the main_item_quantity column
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATION_FILE="${SCRIPT_DIR}/add_main_item_quantity_column.sql"
LOG_FILE="${SCRIPT_DIR}/migration_main_item_quantity.log"

# Database connection parameters
# Can be set via environment variables or defaults
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-procurement_dss}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"

# Docker support
DOCKER_CONTAINER="${DOCKER_CONTAINER:-}"
USE_DOCKER="${USE_DOCKER:-false}"

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if migration file exists
    if [ ! -f "$MIGRATION_FILE" ]; then
        print_error "Migration file not found: $MIGRATION_FILE"
        exit 1
    fi
    
    # Check if psql is available (if not using Docker)
    if [ "$USE_DOCKER" != "true" ] && [ -z "$DOCKER_CONTAINER" ]; then
        if ! command -v psql &> /dev/null; then
            print_error "psql command not found. Please install PostgreSQL client or use Docker."
            exit 1
        fi
    fi
    
    # Check if Docker is available and container exists (if using Docker)
    if [ "$USE_DOCKER" = "true" ] || [ -n "$DOCKER_CONTAINER" ]; then
        if ! command -v docker &> /dev/null; then
            print_error "docker command not found. Please install Docker or use direct psql connection."
            exit 1
        fi
        
        # Auto-detect container if not specified
        if [ -z "$DOCKER_CONTAINER" ]; then
            DOCKER_CONTAINER=$(docker ps --format "{{.Names}}" | grep -i postgres | head -n1)
            if [ -z "$DOCKER_CONTAINER" ]; then
                print_error "No PostgreSQL container found. Please set DOCKER_CONTAINER environment variable."
                exit 1
            fi
            print_info "Auto-detected Docker container: $DOCKER_CONTAINER"
        fi
        
        # Verify container is running
        if ! docker ps --format "{{.Names}}" | grep -q "^${DOCKER_CONTAINER}$"; then
            print_error "Docker container '$DOCKER_CONTAINER' is not running."
            exit 1
        fi
    fi
    
    print_info "Prerequisites check passed ✓"
}

# Function to execute migration via Docker
execute_migration_docker() {
    print_info "Applying migration via Docker container: $DOCKER_CONTAINER"
    
    # Copy migration file to container
    docker cp "$MIGRATION_FILE" "${DOCKER_CONTAINER}:/tmp/add_main_item_quantity_column.sql"
    
    # Execute migration
    if docker exec "$DOCKER_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -f /tmp/add_main_item_quantity_column.sql >> "$LOG_FILE" 2>&1; then
        print_info "Migration applied successfully ✓"
        
        # Cleanup
        docker exec "$DOCKER_CONTAINER" rm -f /tmp/add_main_item_quantity_column.sql
        
        return 0
    else
        print_error "Migration failed. Check log file: $LOG_FILE"
        return 1
    fi
}

# Function to execute migration via direct psql
execute_migration_direct() {
    print_info "Applying migration via direct psql connection"
    print_info "Connecting to: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
    
    # Set PGPASSWORD if provided
    if [ -n "$DB_PASSWORD" ]; then
        export PGPASSWORD="$DB_PASSWORD"
    fi
    
    # Execute migration
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$MIGRATION_FILE" >> "$LOG_FILE" 2>&1; then
        print_info "Migration applied successfully ✓"
        unset PGPASSWORD
        return 0
    else
        print_error "Migration failed. Check log file: $LOG_FILE"
        unset PGPASSWORD
        return 1
    fi
}

# Function to verify migration
verify_migration() {
    print_info "Verifying migration..."
    
    local verify_query="SELECT column_name, data_type, is_nullable, column_default 
                        FROM information_schema.columns 
                        WHERE table_name = 'procurement_packages' 
                        AND column_name = 'main_item_quantity';"
    
    if [ "$USE_DOCKER" = "true" ] || [ -n "$DOCKER_CONTAINER" ]; then
        local result=$(docker exec "$DOCKER_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c "$verify_query" 2>/dev/null | tr -d ' ')
        if [ -n "$result" ] && [ "$result" != "" ]; then
            print_info "Verification passed: Column 'main_item_quantity' exists ✓"
            docker exec "$DOCKER_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "$verify_query"
            return 0
        else
            print_warning "Column verification returned empty result"
            return 1
        fi
    else
        if [ -n "$DB_PASSWORD" ]; then
            export PGPASSWORD="$DB_PASSWORD"
        fi
        local result=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "$verify_query" 2>/dev/null | tr -d ' ')
        unset PGPASSWORD
        if [ -n "$result" ] && [ "$result" != "" ]; then
            print_info "Verification passed: Column 'main_item_quantity' exists ✓"
            if [ -n "$DB_PASSWORD" ]; then
                export PGPASSWORD="$DB_PASSWORD"
            fi
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$verify_query"
            unset PGPASSWORD
            return 0
        else
            print_warning "Column verification returned empty result"
            return 1
        fi
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "  Add main_item_quantity Column Migration"
    echo "=========================================="
    echo ""
    
    # Initialize log file
    echo "Migration started at: $(date)" > "$LOG_FILE"
    echo "Migration file: $MIGRATION_FILE" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    
    # Check prerequisites
    check_prerequisites
    
    # Execute migration
    print_info "Starting migration..."
    if [ "$USE_DOCKER" = "true" ] || [ -n "$DOCKER_CONTAINER" ]; then
        if ! execute_migration_docker; then
            print_error "Migration failed!"
            exit 1
        fi
    else
        if ! execute_migration_direct; then
            print_error "Migration failed!"
            exit 1
        fi
    fi
    
    # Verify migration
    if verify_migration; then
        print_info "Migration completed successfully!"
        echo ""
        print_info "Summary:"
        echo "  - Column 'main_item_quantity' added to 'procurement_packages' table"
        echo "  - Column type: INTEGER"
        echo "  - Nullable: YES"
        echo "  - Default: 0"
        echo ""
        print_info "Log file: $LOG_FILE"
    else
        print_warning "Migration may have completed, but verification failed."
        print_warning "Please check the database manually."
        exit 1
    fi
}

# Run main function
main "$@"

