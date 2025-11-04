#!/bin/bash
# Script to run the invoice amount precision migration on Linux

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Navigate to project directory
cd "$PROJECT_DIR"

# Run the migration
cat backend/increase_invoice_amount_precision.sql | docker-compose exec -T postgres psql -U postgres -d procurement_dss

echo "Migration completed!"

