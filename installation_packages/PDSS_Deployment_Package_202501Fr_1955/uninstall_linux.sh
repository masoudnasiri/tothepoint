#!/bin/bash
################################################################################
#  Procurement Decision Support System - Linux Uninstaller
################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "========================================================================"
echo "  PROCUREMENT DECISION SUPPORT SYSTEM"
echo "  Linux Uninstallation Wizard"
echo "========================================================================"
echo ""
echo -e "${RED}WARNING: This will remove all data and containers!${NC}"
echo ""
read -p "Are you sure you want to uninstall? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo ""
echo "[1/6] Stopping all containers..."
docker-compose down
echo -e "${GREEN}[OK]${NC} Containers stopped"
echo ""

echo "[2/6] Removing volumes (including database)..."
docker-compose down -v
echo -e "${GREEN}[OK]${NC} Volumes removed"
echo ""

echo "[3/6] Removing Docker images..."
read -p "Remove Docker images? (yes/no): " REMOVE_IMAGES
if [ "$REMOVE_IMAGES" == "yes" ]; then
    docker rmi cahs_flow_project-backend cahs_flow_project-frontend 2>/dev/null || true
    echo -e "${GREEN}[OK]${NC} Images removed"
else
    echo -e "${YELLOW}[SKIP]${NC} Images kept"
fi
echo ""

echo "[4/6] Removing management scripts..."
rm -f "$HOME/start-pdss.sh"
rm -f "$HOME/stop-pdss.sh"
rm -f "$HOME/logs-pdss.sh"
echo -e "${GREEN}[OK]${NC} Scripts removed"
echo ""

echo "[5/6] Removing desktop shortcuts..."
rm -f "$HOME/Desktop/start-pdss.desktop"
rm -f "$HOME/Desktop/stop-pdss.desktop"
echo -e "${GREEN}[OK]${NC} Shortcuts removed"
echo ""

echo "[6/6] Cleanup complete"
echo ""

echo "========================================================================"
echo "  UNINSTALLATION COMPLETE!"
echo "========================================================================"
echo ""
echo "The platform has been removed from your system."
echo ""
echo "To completely clean up Docker:"
echo "  docker system prune -a"
echo ""
echo "Note: The installation files are still in this folder."
echo "You can delete this folder manually if no longer needed."
echo ""

