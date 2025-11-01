#!/bin/bash
# Verify and fix CORS configuration

echo "============================================================================"
echo "  PDSS - CORS Verification and Fix"
echo "============================================================================"
echo ""

CONTAINER_NAME="pdss-backend-1"

echo "[1/4] Checking current config.py..."
docker exec "$CONTAINER_NAME" cat /app/app/config.py | grep -A 2 "allowed_origins"
echo ""

echo "[2/4] Checking if config was loaded correctly..."
docker exec "$CONTAINER_NAME" python -c "
try:
    from app.config import settings
    print('allowed_origins value:', settings.allowed_origins)
    if hasattr(settings, 'get_allowed_origins'):
        print('get_allowed_origins() result:', settings.get_allowed_origins())
    else:
        print('get_allowed_origins method: NOT FOUND')
except Exception as e:
    print('Error:', e)
    import traceback
    traceback.print_exc()
"
echo ""

echo "[3/4] Checking main.py CORS configuration..."
docker exec "$CONTAINER_NAME" cat /app/app/main.py | grep -A 5 "CORSMiddleware"
echo ""

echo "[4/4] Applying comprehensive fix..."
docker exec "$CONTAINER_NAME" python << 'PYTHONEOF'
import sys
import re

config_path = "/app/app/config.py"
main_path = "/app/app/main.py"

# Fix config.py
print("Fixing config.py...")
with open(config_path, 'r') as f:
    config_content = f.read()

# Backup
with open(config_path + ".backup2", 'w') as f:
    f.write(config_content)

# Multiple replacement strategies
original_content = config_content

# Strategy 1: Replace the exact pattern
config_content = re.sub(
    r'allowed_origins:\s*list\[str\]\s*=\s*\[.*?\]',
    "allowed_origins: list[str] = ['*']",
    config_content,
    flags=re.DOTALL
)

# Strategy 2: If that didn't work, try simpler
if config_content == original_content:
    config_content = config_content.replace(
        'allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]',
        "allowed_origins: list[str] = ['*']"
    )

# Strategy 3: Even simpler
if config_content == original_content:
    config_content = re.sub(
        r'"http://localhost:3000",\s*"http://127\.0\.0\.1:3000"',
        "'*'",
        config_content
    )

if config_content != original_content:
    with open(config_path, 'w') as f:
        f.write(config_content)
    print("✓ config.py patched successfully")
else:
    print("⚠ config.py already patched or pattern not found")
    print("Current content around allowed_origins:")
    for line in original_content.split('\n'):
        if 'allowed_origins' in line:
            print(f"  {line}")

# Fix main.py to ensure it uses the right method
print("\nFixing main.py...")
with open(main_path, 'r') as f:
    main_content = f.read()

# Backup
with open(main_path + ".backup2", 'w') as f:
    f.write(main_content)

# Add get_allowed_origins method if it doesn't exist in Settings class
if "def get_allowed_origins" not in main_content:
    # Check if config has it
    if "def get_allowed_origins" not in config_content:
        # Add method to config.py
        print("Adding get_allowed_origins method to config.py...")
        # Insert before "settings = Settings()"
        if "settings = Settings()" in config_content:
            insert_pos = config_content.rfind("settings = Settings()")
            method_code = '''
    def get_allowed_origins(self) -> list[str]:
        """Get allowed origins, supporting wildcard"""
        if isinstance(self.allowed_origins, list) and len(self.allowed_origins) == 1 and self.allowed_origins[0] == '*':
            return ['*']
        return self.allowed_origins if self.allowed_origins else ['*']
'''
            # Find the class definition end
            lines = config_content.split('\n')
            new_lines = []
            in_class = False
            for i, line in enumerate(lines):
                new_lines.append(line)
                if line.strip().startswith('class Settings'):
                    in_class = True
                if in_class and (line.strip() == '' and i > 0 and 'class' not in lines[i-1] and 'def' not in lines[i-1]) and 'Config' not in lines[i+1] if i+1 < len(lines) else False:
                    # Insert before Config class
                    if 'class Config' in lines[i+1] if i+1 < len(lines) else False:
                        new_lines.append(method_code)
            config_content = '\n'.join(new_lines)
            
            # Simple approach: just add before "class Config"
            if "class Config" in config_content:
                config_content = config_content.replace(
                    "class Config:",
                    method_code + "\n    class Config:"
                )
            
            with open(config_path, 'w') as f:
                f.write(config_content)

# Update main.py to use get_allowed_origins if it exists, or use allowed_origins directly
print("Updating main.py CORS middleware...")
original_main = main_content

# Replace with method call if method exists
if "def get_allowed_origins" in config_content:
    main_content = re.sub(
        r'allow_origins\s*=\s*settings\.allowed_origins[,\s]*',
        "allow_origins=settings.get_allowed_origins(),\n    ",
        main_content
    )
    
    # Also try direct replace
    if main_content == original_main:
        main_content = main_content.replace(
            "allow_origins=settings.allowed_origins",
            "allow_origins=settings.get_allowed_origins()"
        )
else:
    # Just ensure it uses settings.allowed_origins directly
    print("Using direct allowed_origins access")

if main_content != original_main:
    with open(main_path, 'w') as f:
        f.write(main_content)
    print("✓ main.py updated")
else:
    print("⚠ main.py already correct or no changes needed")

print("\n✓ Configuration files updated")
print("✓ Ready to restart backend")
PYTHONEOF

echo ""
echo "Restarting backend..."
docker-compose restart backend

echo ""
echo "Waiting for backend to start..."
sleep 3

echo ""
echo "Testing CORS headers..."
curl -v -X OPTIONS \
     -H "Origin: http://193.162.129.58:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     http://localhost:8000/health 2>&1 | grep -i "access-control"

echo ""
echo "============================================================================"
echo "  Done! Refresh your browser."
echo "============================================================================"

