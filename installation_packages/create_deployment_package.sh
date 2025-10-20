#!/bin/bash
################################################################################
#  Create Deployment Package for PDSS
#  This script creates a complete package for deployment
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "========================================================================"
echo "  Creating Deployment Package"
echo "========================================================================"
echo ""

PACKAGE_NAME="PDSS_Deployment_Package"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="${PACKAGE_NAME}_${TIMESTAMP}"

echo "[1/6] Creating package directory..."
mkdir -p "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/backend"
mkdir -p "$OUTPUT_DIR/frontend"
mkdir -p "$OUTPUT_DIR/docs"

echo "[2/6] Copying backend files..."
cp -r ../backend/* "$OUTPUT_DIR/backend/" 2>/dev/null || true
find "$OUTPUT_DIR/backend" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$OUTPUT_DIR/backend" -type f -name "*.pyc" -delete 2>/dev/null || true

echo "[3/6] Copying frontend files..."
cp -r ../frontend/src "$OUTPUT_DIR/frontend/"
cp -r ../frontend/public "$OUTPUT_DIR/frontend/"
cp ../frontend/package.json "$OUTPUT_DIR/frontend/"
cp ../frontend/package-lock.json "$OUTPUT_DIR/frontend/" 2>/dev/null || true
cp ../frontend/Dockerfile "$OUTPUT_DIR/frontend/"

echo "[4/6] Copying Docker configuration..."
cp ../docker-compose.yml "$OUTPUT_DIR/"
cp ../backend/Dockerfile "$OUTPUT_DIR/backend/"

echo "[5/6] Copying documentation..."
cp ../README.md "$OUTPUT_DIR/docs/" 2>/dev/null || true
cp ../USER_GUIDE.md "$OUTPUT_DIR/docs/" 2>/dev/null || true
cp ../COMPLETE_SYSTEM_DOCUMENTATION.md "$OUTPUT_DIR/docs/" 2>/dev/null || true
cp ../*COMMERCIAL*.md "$OUTPUT_DIR/docs/" 2>/dev/null || true

echo "[6/6] Copying installation scripts..."
cp install_windows.bat "$OUTPUT_DIR/"
cp install_linux.sh "$OUTPUT_DIR/"
cp uninstall_windows.bat "$OUTPUT_DIR/"
cp uninstall_linux.sh "$OUTPUT_DIR/"
cp README.md "$OUTPUT_DIR/"
cp QUICK_START.md "$OUTPUT_DIR/"
cp INSTALLATION_GUIDE.md "$OUTPUT_DIR/"
cp SYSTEM_REQUIREMENTS.md "$OUTPUT_DIR/"
cp config_template.env "$OUTPUT_DIR/.env.example"

# Make scripts executable
chmod +x "$OUTPUT_DIR/install_linux.sh"
chmod +x "$OUTPUT_DIR/uninstall_linux.sh"

echo ""
echo "========================================================================"
echo "  Package Created Successfully!"
echo "========================================================================"
echo ""
echo -e "${GREEN}Package location: $OUTPUT_DIR${NC}"
echo ""
echo "Next steps:"
echo "1. Copy the entire '$OUTPUT_DIR' folder to target server"
echo "2. On Windows: Run install_windows.bat as Administrator"
echo "3. On Linux: Run sudo ./install_linux.sh"
echo ""
echo "Package is ready for deployment!"
echo "========================================================================"

