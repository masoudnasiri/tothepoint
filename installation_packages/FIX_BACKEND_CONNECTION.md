# Fix Backend Connection Issue

## Problem
Frontend is making requests to `http://193.162.129.58:3000/` instead of the backend on port 8000, causing 500 errors.

## Root Cause
The `REACT_APP_API_URL` environment variable is not set in the frontend Docker container.

## Solution

### Option 1: Update docker-compose.yml and Restart (Recommended)

1. **Edit docker-compose.yml** in your installation directory:
   ```yaml
   frontend:
     build: ./frontend
     ports:
       - "3000:3000"
     environment:
       - CHOKIDAR_USEPOLLING=true
       - REACT_APP_API_URL=http://backend:8000  # ADD THIS LINE
   ```

2. **Restart the frontend container**:
   ```bash
   cd ~/pdss
   docker-compose restart frontend
   # OR rebuild if needed:
   docker-compose up -d --build frontend
   ```

3. **Verify the environment variable is set**:
   ```bash
   docker exec pdss-frontend-1 printenv | grep REACT_APP_API_URL
   ```

### Option 2: Quick Fix Without Rebuilding

If you can't modify docker-compose.yml, you can set the environment variable directly:

```bash
# Stop frontend
docker-compose stop frontend

# Remove and recreate with environment variable
docker rm pdss-frontend-1
docker run -d \
  --name pdss-frontend-1 \
  --network pdss_procurement_network \
  -p 3000:3000 \
  -e CHOKIDAR_USEPOLLING=true \
  -e REACT_APP_API_URL=http://backend:8000 \
  -v "$(pwd)/frontend:/app" \
  -v /app/node_modules \
  pdss-frontend npm start
```

### Option 3: Set API URL for External Access

If accessing from a browser outside Docker network, use the server's IP:

```bash
# In docker-compose.yml, change to:
REACT_APP_API_URL=http://193.162.129.58:8000
# OR use server's hostname if available
REACT_APP_API_URL=http://your-server-ip:8000
```

**Note**: When using external IP, ensure:
- Backend port 8000 is accessible from your network
- Firewall allows connections on port 8000
- CORS is configured in backend to allow your frontend origin

### Verification

After applying the fix:

1. **Check backend is accessible**:
   ```bash
   curl http://backend:8000/health
   # OR from host machine:
   curl http://localhost:8000/health
   ```

2. **Check frontend environment**:
   ```bash
   docker exec pdss-frontend-1 printenv REACT_APP_API_URL
   ```

3. **Check browser console** - should now show:
   ```
   API Base URL: http://backend:8000
   ```
   Instead of:
   ```
   API Base URL: (using proxy from package.json)
   ```

4. **Test API call** - In browser console, try:
   ```javascript
   fetch('http://193.162.129.58:8000/api/projects/')
     .then(r => r.json())
     .then(console.log)
   ```

## Troubleshooting

### If still getting 500 errors after fix:

1. **Check backend logs**:
   ```bash
   docker logs pdss-backend-1 --tail 50
   ```

2. **Check backend health**:
   ```bash
   docker exec pdss-backend-1 curl http://localhost:8000/health
   ```

3. **Check database connection**:
   ```bash
   docker exec pdss-backend-1 python -c "from app.database import engine; print('DB OK')"
   ```

4. **Verify CORS settings** in backend:
   - Check `backend/app/main.py` for CORS configuration
   - Should allow origins including your frontend URL

## For Deployment Package Update

The root `docker-compose.yml` has been updated with `REACT_APP_API_URL`. New packages will include this fix automatically.

