# Fix CORS (Cross-Origin Resource Sharing) Issue

## Problem
Browser shows CORS error:
```
Access to XMLHttpRequest at 'http://193.162.129.58:8000/projects/' from origin 'http://193.162.129.58:3000' 
has been blocked by CORS policy: Response to preflight request doesn't pass access control check: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Root Cause
Backend CORS configuration only allows `localhost:3000`, but frontend is accessed from `193.162.129.58:3000`.

## Solution Applied

The backend configuration has been updated to:
1. Allow wildcard (`*`) origins in development mode by default
2. Support `ALLOWED_ORIGINS` environment variable for custom configuration
3. Properly parse comma-separated origins from environment

## Fix for Existing Installation

### Option 1: Quick Fix - Set Environment Variable (Recommended)

Run on your server:

```bash
cd ~/pdss

# Edit docker-compose.yml to add ALLOWED_ORIGINS
nano docker-compose.yml

# Find the "backend:" section and add this line under environment:
#   - ALLOWED_ORIGINS=*

# Restart backend
docker-compose restart backend

# Verify CORS is working
curl -H "Origin: http://193.162.129.58:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     http://193.162.129.58:8000/projects/
```

### Option 2: Update Code Files

If you have the updated code files:

```bash
cd ~/pdss

# Copy updated config.py and main.py
# (from your development directory)

# Rebuild backend
docker-compose up -d --build backend

# Check logs
docker logs pdss-backend-1 --tail 20
```

### Option 3: Manual Update (No Code Changes Needed)

Edit `docker-compose.yml` and add to backend environment:

```yaml
backend:
  environment:
    - ALLOWED_ORIGINS=*
    # ... other environment variables
```

Then restart:
```bash
docker-compose restart backend
```

## Verification

After applying the fix:

1. **Check backend logs** for CORS configuration:
   ```bash
   docker logs pdss-backend-1 --tail 50 | grep -i cors
   ```

2. **Test CORS headers**:
   ```bash
   curl -I -H "Origin: http://193.162.129.58:3000" \
        http://193.162.129.58:8000/health
   ```

3. **Check browser console** - CORS errors should be gone

4. **Test API call** in browser:
   ```javascript
   fetch('http://193.162.129.58:8000/api/projects/')
     .then(r => r.json())
     .then(console.log)
   ```

## Production Configuration

For production, **DO NOT use `*`**. Set specific origins:

```yaml
backend:
  environment:
    - ENVIRONMENT=production
    - ALLOWED_ORIGINS=http://yourdomain.com,https://yourdomain.com
```

## Troubleshooting

### If CORS errors persist:

1. **Verify environment variable is set**:
   ```bash
   docker exec pdss-backend-1 printenv ALLOWED_ORIGINS
   ```

2. **Check backend is reading the config**:
   ```bash
   docker exec pdss-backend-1 python -c "from app.config import settings; print(settings.get_allowed_origins())"
   ```

3. **Check backend logs for errors**:
   ```bash
   docker logs pdss-backend-1 --tail 100
   ```

4. **Restart backend completely**:
   ```bash
   docker-compose stop backend
   docker-compose up -d backend
   ```

