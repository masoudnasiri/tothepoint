#!/bin/bash
################################################################################
#  Create Deployment Package for PDSS - IMPROVED VERSION
#  This script creates a complete package for deployment
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "========================================================================"
echo "  Creating Deployment Package - IMPROVED VERSION"
echo "========================================================================"
echo ""

PACKAGE_NAME="PDSS_Deployment_Package"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="${PACKAGE_NAME}_${TIMESTAMP}"

echo "[1/8] Creating package directory..."
mkdir -p "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/backend"
mkdir -p "$OUTPUT_DIR/frontend"
mkdir -p "$OUTPUT_DIR/docs"

echo "[2/8] Copying backend files..."
cp -r ../backend/* "$OUTPUT_DIR/backend/" 2>/dev/null || true
find "$OUTPUT_DIR/backend" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$OUTPUT_DIR/backend" -type f -name "*.pyc" -delete 2>/dev/null || true

echo "[3/8] Copying frontend files..."
cp -r ../frontend/src "$OUTPUT_DIR/frontend/"
cp -r ../frontend/public "$OUTPUT_DIR/frontend/"
cp ../frontend/package.json "$OUTPUT_DIR/frontend/"
cp ../frontend/package-lock.json "$OUTPUT_DIR/frontend/" 2>/dev/null || true
cp ../frontend/Dockerfile "$OUTPUT_DIR/frontend/"

echo "[4/8] Building frontend for production..."
cd "$OUTPUT_DIR/frontend"
if command -v npm &> /dev/null; then
    echo "Building React frontend for production..."
    npm install --production
    npm run build
    echo "Frontend built successfully!"
else
    echo -e "${YELLOW}[WARNING] npm not found. Frontend will be built during Docker deployment.${NC}"
fi
cd - > /dev/null

echo "[5/8] Copying Docker configuration..."
cp ../docker-compose.yml "$OUTPUT_DIR/"
cp ../backend/Dockerfile "$OUTPUT_DIR/backend/"

echo "[6/8] Copying documentation..."
# Copy from project root if exists, otherwise from installation_packages
cp ../README.md "$OUTPUT_DIR/docs/" 2>/dev/null || cp README.md "$OUTPUT_DIR/docs/" 2>/dev/null || true
cp ../USER_GUIDE.md "$OUTPUT_DIR/docs/" 2>/dev/null || cp USER_GUIDE.md "$OUTPUT_DIR/docs/" 2>/dev/null || true
cp ../COMPLETE_SYSTEM_DOCUMENTATION.md "$OUTPUT_DIR/docs/" 2>/dev/null || cp COMPLETE_SYSTEM_DOCUMENTATION.md "$OUTPUT_DIR/docs/" 2>/dev/null || true

echo "[7/8] Copying installation scripts..."
cp install_windows.bat "$OUTPUT_DIR/"
cp install_linux.sh "$OUTPUT_DIR/"
cp uninstall_windows.bat "$OUTPUT_DIR/"
cp uninstall_linux.sh "$OUTPUT_DIR/"
cp config_template.env "$OUTPUT_DIR/.env.example"

# Copy documentation files from installation_packages directory
cp README.md "$OUTPUT_DIR/" 2>/dev/null || true
cp QUICK_START.md "$OUTPUT_DIR/" 2>/dev/null || true
cp INSTALLATION_GUIDE.md "$OUTPUT_DIR/" 2>/dev/null || true
cp SYSTEM_REQUIREMENTS.md "$OUTPUT_DIR/" 2>/dev/null || true

echo "[8/8] Creating deployment verification script..."
cat > "$OUTPUT_DIR/verify_deployment.sh" << 'EOF'
#!/bin/bash
echo "Verifying deployment package..."
echo ""

# Check critical files
echo "Checking critical files:"
files=(
    "docker-compose.yml"
    "backend/Dockerfile"
    "frontend/Dockerfile"
    "backend/requirements.txt"
    "frontend/package.json"
    "install_linux.sh"
    "install_windows.bat"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file - MISSING!"
    fi
done

echo ""
echo "Checking Docker Compose services:"
if grep -q "postgres:" docker-compose.yml; then
    echo "✅ PostgreSQL service configured"
else
    echo "❌ PostgreSQL service missing"
fi

if grep -q "backend:" docker-compose.yml; then
    echo "✅ Backend service configured"
else
    echo "❌ Backend service missing"
fi

if grep -q "frontend:" docker-compose.yml; then
    echo "✅ Frontend service configured"
else
    echo "❌ Frontend service missing"
fi

echo ""
echo "Deployment package verification complete!"
EOF

chmod +x "$OUTPUT_DIR/verify_deployment.sh"

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
echo "Package contents:"
echo "├── backend/          (FastAPI application)"
echo "├── frontend/         (React application)"
echo "├── docs/            (Documentation)"
echo "├── docker-compose.yml"
echo "├── install_linux.sh"
echo "├── install_windows.bat"
echo "├── .env.example"
echo "└── verify_deployment.sh"
echo ""
echo "Next steps:"
echo "1. Copy the entire '$OUTPUT_DIR' folder to target server"
echo "2. Run: ./verify_deployment.sh (to check package integrity)"
echo "3. On Windows: Run install_windows.bat as Administrator"
echo "4. On Linux: Run sudo ./install_linux.sh"
echo ""
echo -e "${GREEN}Package is ready for deployment!${NC}"
echo "========================================================================"
