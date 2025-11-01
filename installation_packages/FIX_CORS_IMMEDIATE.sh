#!/bin/bash
# Immediate fix for CORS issue - patches backend config in running container
# Run this on your server where the containers are running

set -e

echo "============================================================================"
echo "  PDSS - Immediate CORS Fix"
echo "============================================================================"
echo ""

CONTAINER_NAME="pdss-backend-1"

# Check if container exists
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "[ERROR] Backend container '$CONTAINER_NAME' is not running!"
    echo "[INFO] Try: docker-compose restart backend"
    exit 1
fi

echo "[1/3] Checking current CORS configuration..."
docker exec "$CONTAINER_NAME" python -c "
from app.config import settings
print('Current allowed_origins:', settings.allowed_origins)
print('get_allowed_origins() result:', settings.get_allowed_origins() if hasattr(settings, 'get_allowed_origins') else 'Method not found')
" 2>/dev/null || echo "[WARNING] Could not read current config"

echo ""
echo "[2/3] Patching backend config.py to allow all origins..."
echo ""

# Create patch script
PATCH_SCRIPT=$(cat <<'EOF'
import sys
import os

config_path = "/app/app/config.py"

# Read current config
with open(config_path, 'r') as f:
    content = f.read()

# Check if already patched
if "allowed_origins = ['*']" in content or '"*"' in content:
    print("[INFO] Config already allows all origins")
    sys.exit(0)

# Simple patch: replace the allowed_origins line with wildcard
if "allowed_origins" in content:
    # Method 1: Replace list with ['*']
    import re
    # Pattern to find allowed_origins list assignment
    pattern = r"allowed_origins\s*[=:]\s*\[[^\]]*\]"
    replacement = "allowed_origins = ['*']"
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        # Backup original
        with open(config_path + ".backup", 'w') as f:
            f.write(content)
        
        # Write patched version
        with open(config_path, 'w') as f:
            f.write(new_content)
        
        print("[OK] Config patched successfully")
        print("[INFO] Backup saved to: /app/app/config.py.backup")
    else:
        # Fallback: Just add a function to return ['*']
        if "def get_allowed_origins" not in content:
            # Add method before settings = Settings()
            insert_pos = content.find("settings = Settings()")
            if insert_pos > 0:
                method = """
    def get_allowed_origins(self):
        return ['*']
"""
                new_content = content[:insert_pos] + method + content[insert_pos:]
                with open(config_path + ".backup", 'w') as f:
                    f.write(content)
                with open(config_path, 'w') as f:
                    f.write(new_content)
                print("[OK] Added get_allowed_origins method")
        else:
            print("[INFO] get_allowed_origins method already exists")
else:
    print("[ERROR] Could not find allowed_origins in config")
    sys.exit(1)
EOF
)

# Apply patch
docker exec "$CONTAINER_NAME" python -c "$PATCH_SCRIPT"

echo ""
echo "[3/3] Updating main.py to use get_allowed_origins (if needed)..."
echo ""

# Patch main.py
MAIN_PATCH=$(cat <<'EOF'
import sys

main_path = "/app/app/main.py"

with open(main_path, 'r') as f:
    content = f.read()

# Check if already using get_allowed_origins
if "settings.get_allowed_origins()" in content:
    print("[INFO] main.py already uses get_allowed_origins()")
    sys.exit(0)

# Replace settings.allowed_origins with settings.get_allowed_origins()
if "settings.allowed_origins" in content:
    new_content = content.replace("allow_origins=settings.allowed_origins", "allow_origins=settings.get_allowed_origins()")
    
    if new_content != content:
        with open(main_path + ".backup", 'w') as f:
            f.write(content)
        with open(main_path, 'w') as f:
            f.write(new_content)
        print("[OK] main.py patched successfully")
    else:
        print("[WARNING] Could not patch main.py")
else:
    print("[INFO] No changes needed to main.py")
EOF
)

docker exec "$CONTAINER_NAME" python -c "$MAIN_PATCH"

echo ""
echo "============================================================================"
echo "  Restarting backend to apply changes..."
echo "============================================================================"
echo ""

docker-compose restart backend

echo ""
echo "[OK] Backend restarted"
echo ""
echo "Verification:"
echo "1. Check backend logs: docker logs $CONTAINER_NAME --tail 20"
echo "2. Test CORS: curl -H 'Origin: http://193.162.129.58:3000' http://localhost:8000/health"
echo "3. Refresh your browser"
echo ""

