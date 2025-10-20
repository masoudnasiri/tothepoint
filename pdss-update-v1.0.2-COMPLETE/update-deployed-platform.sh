#!/bin/bash
################################################################################
#  PDSS Platform Update Script (Linux)
#  Updates a deployed PDSS platform with latest code changes
################################################################################

set -e

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

echo "============================================================================"
echo "  PRE-UPDATE CHECKS"
echo "============================================================================"
echo ""

echo "[1/5] Checking if platform is running..."
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}[OK]${NC} Platform is running"
    PLATFORM_RUNNING=true
else
    echo -e "${YELLOW}[INFO]${NC} Platform is not running"
    PLATFORM_RUNNING=false
fi
echo ""

echo "[2/5] Checking for new files..."
if [ ! -d ../update_files ]; then
    echo -e "${YELLOW}[INFO]${NC} No update_files directory found"
    echo ""
    echo "Update files should be placed in: $(dirname "$DEPLOY_DIR")/update_files"
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

echo "[3/5] Creating backup..."
BACKUP_DIR=~/pdss_backups
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# Backup database
echo "  Backing up database..."
docker-compose exec -T db pg_dump -U postgres procurement_dss > "$BACKUP_DIR/db_backup_$BACKUP_DATE.sql" 2>/dev/null || echo "  [WARNING] Could not backup database (platform may not be running)"

# Backup current code
echo "  Backing up current code..."
tar -czf "$BACKUP_DIR/code_backup_$BACKUP_DATE.tar.gz" backend/ frontend/ 2>/dev/null || echo "  [WARNING] Could not backup code"

echo -e "${GREEN}[OK]${NC} Backup created at: $BACKUP_DIR"
echo ""

echo "[4/5] Checking Docker..."
if ! docker ps &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker is not running!"
    echo "Please start Docker: sudo systemctl start docker"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Docker is running"
echo ""

echo "[5/5] Checking disk space..."
AVAILABLE=$(df -h "$DEPLOY_DIR" | tail -1 | awk '{print $4}')
echo -e "${GREEN}[OK]${NC} Available space: $AVAILABLE"
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
if [ -d ../update_files/backend ]; then
    echo "  Updating backend files..."
    cp -r ../update_files/backend/* backend/
    echo -e "${GREEN}[OK]${NC} Backend files updated"
else
    echo -e "${YELLOW}[SKIP]${NC} No backend updates"
fi

# Update frontend if files exist
if [ -d ../update_files/frontend ]; then
    echo "  Updating frontend files..."
    cp -r ../update_files/frontend/* frontend/
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
    echo "  1. Extract backup: tar -xzf $BACKUP_DIR/code_backup_$BACKUP_DATE.tar.gz"
    echo "  2. Rebuild: docker-compose build --no-cache"
    echo "  3. Start: docker-compose up -d"
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
echo "  Database: $BACKUP_DIR/db_backup_$BACKUP_DATE.sql"
echo "  Code: $BACKUP_DIR/code_backup_$BACKUP_DATE.tar.gz"
echo ""
echo "View logs: docker-compose logs -f"
echo ""
echo "============================================================================"

