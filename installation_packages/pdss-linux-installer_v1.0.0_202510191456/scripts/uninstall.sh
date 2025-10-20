#!/bin/bash
cd "$(dirname "$0")/.."

echo "========================================================================"
echo "  PDSS Uninstaller"
echo "========================================================================"
echo ""
echo "WARNING: This will remove all PDSS containers and data!"
echo ""
read -p "Are you sure? Type 'YES' to confirm: " CONFIRM

if [ "$CONFIRM" != "YES" ]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo ""
echo "Stopping and removing containers..."
docker-compose down -v

echo ""
echo "PDSS has been uninstalled."
echo ""