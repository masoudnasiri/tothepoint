#!/bin/bash
################################################################################
#  PDSS Platform Update Script (Linux)
#  Updates a deployed PDSS platform with latest code changes
#  Safety: aborts update if backup cannot be verified.
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo "============================================================================"
echo -e "  ${BOLD}PDSS Platform Update Script${NC}"
echo "============================================================================"
echo ""

# Get the deployment directory
if [ -d ~/pdss ]; then
    DEPLOY_DIR=~/pdss
elif [ -d ~/pdss-linux-v1.0.0 ]; then
    DEPLOY_DIR=~/pdss-linux-v1.0.0
else
    echo -e "${RED}[ERROR]${NC} Could not find PDSS deployment directory!"
    echo ""
    echo "Please specify the deployment directory:"
    read -p "Enter path (or press Ctrl+C to cancel): " DEPLOY_DIR
    
    if [ ! -d "$DEPLOY_DIR" ]; then
        echo -e "${RED}[ERROR]${NC} Directory does not exist: $DEPLOY_DIR"
        exit 1
    fi
fi

echo -e "${GREEN}[OK]${NC} Found deployment at: $DEPLOY_DIR"
echo ""

# Change to deployment directory
cd "$DEPLOY_DIR"

# Detect database service name from compose config
DB_SERVICE=""
if docker-compose config --services | grep -qx "postgres"; then
    DB_SERVICE="postgres"
elif docker-compose config --services | grep -qx "db"; then
    DB_SERVICE="db"
else
    echo -e "${RED}[ERROR]${NC} Could not find database service in docker-compose.yml (expected 'postgres' or 'db')."
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Using database service: ${BOLD}${DB_SERVICE}${NC}"
echo ""

UPDATE_DIR="$(cd "$DEPLOY_DIR/.." && pwd)/update_files"

echo "============================================================================"
echo "  PRE-UPDATE CHECKS"
echo "============================================================================"
echo ""

echo "[1/6] Checking if platform is running..."
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}[OK]${NC} Platform is running"
    PLATFORM_RUNNING=true
else
    echo -e "${YELLOW}[INFO]${NC} Platform is not running"
    PLATFORM_RUNNING=false
fi
echo ""

echo "[2/6] Checking for new files..."
if [ ! -d "$UPDATE_DIR" ]; then
    echo -e "${YELLOW}[INFO]${NC} No update_files directory found"
    echo ""
    echo "Update files should be placed in: $UPDATE_DIR"
    echo ""
    echo "Structure:"
    echo "  update_files/"
    echo "  ├── backend/"
    echo "  │   └── (updated backend files)"
    echo "  └── frontend/"
    echo "      └── (updated frontend files)"
    echo ""
    read -p "Do you want to continue anyway? (yes/no): " CONTINUE
    if [ "$CONTINUE" != "yes" ]; then
        echo "Update cancelled."
        exit 0
    fi
else
    echo -e "${GREEN}[OK]${NC} Update files found"
fi
echo ""

echo "[3/6] Checking Docker..."
if ! docker ps &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker is not running!"
    echo "Please start Docker: sudo systemctl start docker"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Docker is running"
echo ""

echo "[4/6] Creating backup (required)..."
BACKUP_DIR=~/pdss_backups
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
DB_BACKUP_FILE="$BACKUP_DIR/db_backup_$BACKUP_DATE.sql"
CODE_BACKUP_FILE="$BACKUP_DIR/code_backup_$BACKUP_DATE.tar.gz"

echo "  Ensuring database service is running..."
if ! docker-compose ps "$DB_SERVICE" | grep -q "Up"; then
    docker-compose up -d "$DB_SERVICE"
fi

echo "  Waiting for database readiness..."
DB_READY=false
for _ in $(seq 1 20); do
    if docker-compose exec -T "$DB_SERVICE" pg_isready -U postgres >/dev/null 2>&1; then
        DB_READY=true
        break
    fi
    sleep 2
done

if [ "$DB_READY" != true ]; then
    echo -e "${RED}[ERROR]${NC} Database service did not become ready; update aborted."
    exit 1
fi

echo "  Backing up database..."
if ! docker-compose exec -T "$DB_SERVICE" pg_dump -U postgres procurement_dss > "$DB_BACKUP_FILE"; then
    echo -e "${RED}[ERROR]${NC} Database backup failed; update aborted."
    exit 1
fi

if [ ! -s "$DB_BACKUP_FILE" ]; then
    echo -e "${RED}[ERROR]${NC} Database backup file is empty; update aborted."
    exit 1
fi

# Backup current code
echo "  Backing up current code..."
if ! tar -czf "$CODE_BACKUP_FILE" backend/ frontend/; then
    echo -e "${RED}[ERROR]${NC} Code backup failed; update aborted."
    exit 1
fi

if [ ! -s "$CODE_BACKUP_FILE" ]; then
    echo -e "${RED}[ERROR]${NC} Code backup file is empty; update aborted."
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Backup verified at: $BACKUP_DIR"
echo ""

echo "[5/6] Checking disk space..."
AVAILABLE=$(df -h "$DEPLOY_DIR" | tail -1 | awk '{print $4}')
echo -e "${GREEN}[OK]${NC} Available space: $AVAILABLE"
echo ""

echo "[6/6] Backup summary"
echo "  Database backup: $DB_BACKUP_FILE"
echo "  Code backup:     $CODE_BACKUP_FILE"
echo -e "${GREEN}[OK]${NC} Backup verification passed"
echo ""

echo "============================================================================"
echo "  APPLYING UPDATE"
echo "============================================================================"
echo ""

echo "[1/6] Stopping platform..."
if [ "$PLATFORM_RUNNING" = true ]; then
    docker-compose down
    echo -e "${GREEN}[OK]${NC} Platform stopped"
else
    echo -e "${YELLOW}[SKIP]${NC} Platform already stopped"
fi
echo ""

echo "[2/6] Applying code updates..."

# Update backend if files exist
if [ -d "$UPDATE_DIR/backend" ] && [ -n "$(ls -A "$UPDATE_DIR/backend" 2>/dev/null)" ]; then
    echo "  Updating backend files..."
    cp -a "$UPDATE_DIR/backend/." backend/
    echo -e "${GREEN}[OK]${NC} Backend files updated"
else
    echo -e "${YELLOW}[SKIP]${NC} No backend updates"
fi

# Update frontend if files exist
if [ -d "$UPDATE_DIR/frontend" ] && [ -n "$(ls -A "$UPDATE_DIR/frontend" 2>/dev/null)" ]; then
    echo "  Updating frontend files..."
    cp -a "$UPDATE_DIR/frontend/." frontend/
    echo -e "${GREEN}[OK]${NC} Frontend files updated"
else
    echo -e "${YELLOW}[SKIP]${NC} No frontend updates"
fi
echo ""

echo "[3/6] Rebuilding Docker images..."
docker-compose build --no-cache
echo -e "${GREEN}[OK]${NC} Images rebuilt"
echo ""

echo "[4/6] Starting platform..."
docker-compose up -d
echo -e "${GREEN}[OK]${NC} Platform started"
echo ""

echo "[5/6] Waiting for services to be ready..."
sleep 20
echo -e "${GREEN}[OK]${NC} Services should be ready"
echo ""

echo "[6/6] Verifying update..."
docker-compose ps
echo ""

# Check if all containers are up
if docker-compose ps | grep -q "Exit"; then
    echo -e "${RED}[ERROR]${NC} Some containers failed to start!"
    echo ""
    echo "View logs with: docker-compose logs"
    echo ""
    echo "To rollback:"
    echo "  1. Extract backup: tar -xzf $CODE_BACKUP_FILE"
    echo "  2. Rebuild: docker-compose build --no-cache"
    echo "  3. Start: docker-compose up -d"
    echo "  4. Optional DB restore: docker-compose exec -T $DB_SERVICE psql -U postgres -d procurement_dss < $DB_BACKUP_FILE"
    exit 1
fi

echo ""
echo "============================================================================"
echo -e "  ${BOLD}UPDATE COMPLETE!${NC}"
echo "============================================================================"
echo ""
echo -e "${GREEN}✓${NC} Platform updated successfully"
echo -e "${GREEN}✓${NC} Backup saved to: $BACKUP_DIR"
echo -e "${GREEN}✓${NC} All services running"
echo ""
echo "Access your platform:"
echo "  URL: http://$(hostname -I | awk '{print $1}'):3000"
echo "  or: http://localhost:3000"
echo ""
echo "Backup files:"
echo "  Database: $DB_BACKUP_FILE"
echo "  Code: $CODE_BACKUP_FILE"
echo ""
echo "View logs: docker-compose logs -f"
echo ""
echo "============================================================================"

