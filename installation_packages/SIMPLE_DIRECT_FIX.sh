#!/bin/bash
# Simple direct fix - replace allowed_origins with ['*']

echo "Applying simple CORS fix..."

docker exec pdss-backend-1 python << 'PYEOF'
config_file = "/app/app/config.py"

# Read file
with open(config_file, 'r') as f:
    lines = f.readlines()

# Write new version
with open(config_file + ".old", 'w') as f:
    f.writelines(lines)

# Modify lines
new_lines = []
for line in lines:
    if 'allowed_origins' in line and '=' in line and '[' in line:
        # Replace with wildcard
        new_lines.append("    allowed_origins: list[str] = ['*']\n")
    else:
        new_lines.append(line)

# Write modified version
with open(config_file, 'w') as f:
    f.writelines(new_lines)

print("Config file updated!")
PYEOF

echo "Restarting backend..."
docker-compose restart backend

echo ""
echo "Testing CORS (should show access-control-allow-origin header)..."
sleep 2
curl -s -D - -X OPTIONS \
     -H "Origin: http://193.162.129.58:3000" \
     http://localhost:8000/health | head -15

