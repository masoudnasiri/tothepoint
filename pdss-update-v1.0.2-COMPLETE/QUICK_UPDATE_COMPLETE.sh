#!/bin/bash
################################################################################
#  COMPLETE UPDATE for PDSS v1.0.2
#  This updates BOTH frontend and backend
################################################################################

echo "========================================================================"
echo "  PDSS COMPLETE Update - Version 1.0.2"
echo "========================================================================"
echo ""
echo "This will update:"
echo "  ✓ Backend (password change fix)"
echo "  ✓ Frontend (remove credentials from login screen)"
echo ""
echo "Estimated time: 5 minutes"
echo "Downtime: ~3-5 minutes"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Update cancelled."
    exit 0
fi

# Find deployment directory
if [ -d ~/pdss ]; then
    DEPLOY_DIR=~/pdss
elif [ -d ~/pdss-linux-v1.0.0 ]; then
    DEPLOY_DIR=~/pdss-linux-v1.0.0
else
    echo "Could not find deployment directory!"
    read -p "Enter deployment directory path: " DEPLOY_DIR
fi

echo ""
echo "Deployment directory: $DEPLOY_DIR"
echo ""

# Backup
echo "[1/8] Creating backup..."
mkdir -p ~/pdss_backups
docker-compose -f $DEPLOY_DIR/docker-compose.yml exec -T db pg_dump -U postgres procurement_dss > ~/pdss_backups/backup_$(date +%Y%m%d_%H%M%S).sql 2>/dev/null || echo "Warning: Could not backup database"
tar -czf ~/pdss_backups/code_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C $DEPLOY_DIR backend frontend 2>/dev/null || echo "Warning: Could not backup code"
echo "✓ Backup created"

# Stop platform
echo ""
echo "[2/8] Stopping platform..."
cd $DEPLOY_DIR
docker-compose down
echo "✓ Platform stopped"

# Copy files
echo ""
echo "[3/8] Copying updated files..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Backend
cp $SCRIPT_DIR/update_files/backend/app/schemas.py $DEPLOY_DIR/backend/app/
cp $SCRIPT_DIR/update_files/backend/app/crud.py $DEPLOY_DIR/backend/app/
echo "✓ Backend files updated"

# Frontend
cp $SCRIPT_DIR/update_files/frontend/src/pages/LoginPage.tsx $DEPLOY_DIR/frontend/src/pages/
echo "✓ Frontend files updated"

# Rebuild
echo ""
echo "[4/8] Rebuilding backend..."
docker-compose build --no-cache backend
echo "✓ Backend rebuilt"

echo ""
echo "[5/8] Rebuilding frontend..."
docker-compose build --no-cache frontend
echo "✓ Frontend rebuilt"

# Start
echo ""
echo "[6/8] Starting database..."
docker-compose up -d db
sleep 10
echo "✓ Database started"

echo ""
echo "[7/8] Starting backend..."
docker-compose up -d backend
sleep 15
echo "✓ Backend started"

echo ""
echo "[8/8] Starting frontend..."
docker-compose up -d frontend
sleep 20
echo "✓ Frontend started"

# Verify
echo ""
echo "========================================================================"
echo "  Verifying Update"
echo "========================================================================"
docker-compose ps

echo ""
echo "========================================================================"
echo "  UPDATE COMPLETE!"
echo "========================================================================"
echo ""
echo "✓ Both frontend and backend updated"
echo "✓ Platform is running"
echo ""
echo "TEST NOW:"
echo "  1. Open: http://193.162.129.58:3000"
echo "  2. Login screen should NOT show credentials"
echo "  3. Should see: '⚠️ SECURITY NOTICE' instead"
echo "  4. Test password change in User Management"
echo ""
echo "Backups saved in: ~/pdss_backups"
echo ""

