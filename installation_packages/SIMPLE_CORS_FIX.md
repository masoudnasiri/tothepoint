# Simple CORS Fix - Quick Instructions

## Problem
Backend code doesn't have the updated CORS configuration, and `ALLOWED_ORIGINS` environment variable isn't set.

## Quick Fix (Choose One Method)

### Method 1: Edit config.py directly in container (FASTEST)

```bash
cd ~/pdss

# Enter the backend container
docker exec -it pdss-backend-1 sh

# Edit config.py
vi /app/app/config.py
# OR use nano if vi is not available:
nano /app/app/config.py

# Find the line with allowed_origins (around line 19)
# Change from:
#   allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
# To:
#   allowed_origins: list[str] = ["*"]

# Save and exit
# In vi: Press ESC, type :wq, press Enter
# In nano: Press Ctrl+X, then Y, then Enter

# Exit container
exit

# Restart backend
docker-compose restart backend
```

### Method 2: Copy-paste patch script

```bash
cd ~/pdss

# Create a simple Python script to patch the config
docker exec pdss-backend-1 python << 'PYTHON_EOF'
config_path = "/app/app/config.py"
with open(config_path, 'r') as f:
    content = f.read()

# Simple replace
content = content.replace(
    'allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]',
    'allowed_origins: list[str] = ["*"]'
)

# Backup
with open(config_path + ".backup", 'w') as f:
    with open(config_path, 'r') as orig:
        f.write(orig.read())

# Write patched version
with open(config_path, 'w') as f:
    f.write(content)

print("Config patched! Restart backend: docker-compose restart backend")
PYTHON_EOF

# Restart backend
docker-compose restart backend
```

### Method 3: Use sed (if container has it)

```bash
cd ~/pdss

docker exec pdss-backend-1 sh -c "
cp /app/app/config.py /app/app/config.py.backup
sed -i \"s|allowed_origins: list\[str\] = \[.*\]|allowed_origins: list[str] = ['*']|g\" /app/app/config.py
"

docker-compose restart backend
```

### Method 4: Use the automated fix script

```bash
cd ~/pdss

# Download and run the fix script
# (You can copy FIX_CORS_IMMEDIATE.sh from the installation_packages folder)
chmod +x FIX_CORS_IMMEDIATE.sh
./FIX_CORS_IMMEDIATE.sh
```

## Verification

After applying any method:

```bash
# Test CORS headers
curl -v -H "Origin: http://193.162.129.58:3000" \
     http://localhost:8000/health 2>&1 | grep -i "access-control"

# Check backend logs
docker logs pdss-backend-1 --tail 20
```

You should see `access-control-allow-origin: *` in the response headers.

Then refresh your browser - CORS errors should be gone!

## If Still Not Working

1. **Check config was actually updated:**
   ```bash
   docker exec pdss-backend-1 cat /app/app/config.py | grep allowed_origins
   ```

2. **Try full restart:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

3. **Check if backend code changes took effect:**
   ```bash
   docker exec pdss-backend-1 python -c "from app.config import settings; print('Origins:', settings.allowed_origins)"
   ```

