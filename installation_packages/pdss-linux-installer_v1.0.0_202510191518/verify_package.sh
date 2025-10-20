#!/bin/bash

echo "========================================================================"
echo "  PDSS Package Verification"
echo "========================================================================"
echo ""
echo "Checking package integrity..."
echo ""

ERRORS=0

echo "[1] Checking critical files:"
files=(
    "docker-compose.yml"
    "backend/Dockerfile"
    "frontend/Dockerfile"
    "backend/requirements.txt"
    "frontend/package.json"
    "install.sh"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  âœ… $file"
    else
        echo "  âŒ $file - MISSING!"
        ((ERRORS++))
    fi
done
echo ""

echo "[2] Checking Docker Compose configuration:"
if grep -q "postgres:" docker-compose.yml 2>/dev/null; then
    echo "  âœ… PostgreSQL service configured"
else
    echo "  âŒ PostgreSQL service missing"
    ((ERRORS++))
fi

if grep -q "backend:" docker-compose.yml 2>/dev/null; then
    echo "  âœ… Backend service configured"
else
    echo "  âŒ Backend service missing"
    ((ERRORS++))
fi

if grep -q "frontend:" docker-compose.yml 2>/dev/null; then
    echo "  âœ… Frontend service configured"
else
    echo "  âŒ Frontend service missing"
    ((ERRORS++))
fi
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "========================================================================"
    echo "  VERIFICATION PASSED - Package is ready for deployment!"
    echo "========================================================================"
    exit 0
else
    echo "========================================================================"
    echo "  VERIFICATION FAILED - $ERRORS error(s) found!"
    echo "========================================================================"
    exit 1
fi