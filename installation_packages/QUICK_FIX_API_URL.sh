#!/bin/bash
# Quick fix script to set REACT_APP_API_URL for existing installation
# Run this in your installation directory (~/pdss)

set -e

echo "============================================================================"
echo "  PDSS - Quick Fix: Frontend Backend Connection"
echo "============================================================================"
echo ""

# Get server IP from docker-compose port mapping or prompt user
BACKEND_PORT=8000
echo "Detecting backend URL..."

# Try to get external IP from docker-compose or use localhost
if command -v docker >/dev/null 2>&1 && docker ps | grep -q pdss-backend; then
    # Get host IP from first interface (excluding loopback)
    HOST_IP=$(ip route get 8.8.8.8 2>/dev/null | grep -oP 'src \K\S+' || echo "localhost")
    if [ "$HOST_IP" != "localhost" ]; then
        BACKEND_URL="http://${HOST_IP}:${BACKEND_PORT}"
        echo "[INFO] Detected server IP: $HOST_IP"
    else
        BACKEND_URL="http://localhost:${BACKEND_PORT}"
        echo "[INFO] Using localhost (for local access)"
    fi
else
    echo "[WARNING] Docker containers not running. Using default localhost."
    BACKEND_URL="http://localhost:${BACKEND_PORT}"
fi

echo "[INFO] Backend URL will be: $BACKEND_URL"
echo ""
read -p "Press Enter to use this URL, or type a different URL: " USER_URL
if [ ! -z "$USER_URL" ]; then
    BACKEND_URL="$USER_URL"
fi

echo ""
echo "[1/3] Updating docker-compose.yml..."

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "[ERROR] docker-compose.yml not found in current directory!"
    echo "[INFO] Current directory: $(pwd)"
    exit 1
fi

# Create backup
cp docker-compose.yml docker-compose.yml.backup

# Check if REACT_APP_API_URL already exists in frontend environment
if grep -q "REACT_APP_API_URL" docker-compose.yml; then
    # Update existing REACT_APP_API_URL
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|REACT_APP_API_URL=.*|REACT_APP_API_URL=${BACKEND_URL}|" docker-compose.yml
    else
        # Linux
        sed -i "s|REACT_APP_API_URL=.*|REACT_APP_API_URL=${BACKEND_URL}|" docker-compose.yml
    fi
    echo "[OK] Updated existing REACT_APP_API_URL"
else
    # Add REACT_APP_API_URL to frontend environment
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "/CHOKIDAR_USEPOLLING=true/a\\
      - REACT_APP_API_URL=${BACKEND_URL}" docker-compose.yml
    else
        # Linux
        sed -i "/CHOKIDAR_USEPOLLING=true/a      - REACT_APP_API_URL=${BACKEND_URL}" docker-compose.yml
    fi
    echo "[OK] Added REACT_APP_API_URL to docker-compose.yml"
fi

echo ""
echo "[2/3] Restarting frontend container..."

# Restart frontend with new environment variable
docker-compose stop frontend
docker-compose up -d frontend

# Wait a moment for container to start
sleep 3

echo ""
echo "[3/3] Verifying configuration..."

# Verify environment variable is set
if docker exec pdss-frontend-1 printenv REACT_APP_API_URL >/dev/null 2>&1; then
    CURRENT_VALUE=$(docker exec pdss-frontend-1 printenv REACT_APP_API_URL)
    echo "[OK] REACT_APP_API_URL is set: $CURRENT_VALUE"
else
    echo "[WARNING] REACT_APP_API_URL not found in container"
    echo "[INFO] Container may need a full rebuild. Run: docker-compose up -d --build frontend"
fi

echo ""
echo "============================================================================"
echo "  Fix Applied!"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "1. Open browser and check the console (F12)"
echo "2. Look for: 'API Base URL: $BACKEND_URL'"
echo "3. If you see errors, check backend logs: docker logs pdss-backend-1"
echo "4. To test backend connectivity: curl $BACKEND_URL/health"
echo ""
echo "If the frontend was built (not using npm start), rebuild it:"
echo "  docker-compose up -d --build frontend"
echo ""

