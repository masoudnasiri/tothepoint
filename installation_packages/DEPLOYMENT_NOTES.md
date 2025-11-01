# Deployment Package Notes - v1.0.1

## ✅ Included Fixes

This package includes the following critical fixes:

### 1. Frontend API URL Configuration
- **docker-compose.yml**: `REACT_APP_API_URL=http://backend:8000` is set
- Works for Docker internal networking
- **For external access**: See "External Access Configuration" below

### 2. CORS (Cross-Origin Resource Sharing) Fix
- **docker-compose.yml**: `ALLOWED_ORIGINS=*` is set for development
- **backend/app/config.py**: Includes `get_allowed_origins()` method with wildcard support
- **backend/app/main.py**: Uses `settings.get_allowed_origins()` for CORS middleware
- Allows all origins in development mode for flexibility

### 3. Docker Build Improvements
- Pre-pulls base images before build
- Better error messages for network issues
- Connectivity checks

## 📋 Post-Installation Configuration

### External Access (Browser from Different Machine)

If accessing the frontend from a browser on a different machine than the server:

1. **Find your server's IP address:**
   ```bash
   # Linux
   hostname -I | awk '{print $1}'
   # OR
   ip route get 8.8.8.8 | awk '{print $7; exit}'
   
   # Windows
   ipconfig | findstr IPv4
   ```

2. **Update docker-compose.yml:**
   ```yaml
   frontend:
     environment:
       - REACT_APP_API_URL=http://YOUR_SERVER_IP:8000
       # Example: http://193.162.129.58:8000
   ```

3. **Restart frontend:**
   ```bash
   docker-compose restart frontend
   ```

### Production CORS Configuration

For production deployments, **DO NOT use `*`** for `ALLOWED_ORIGINS`. Update `docker-compose.yml`:

```yaml
backend:
  environment:
    - ENVIRONMENT=production
    - ALLOWED_ORIGINS=http://yourdomain.com,https://yourdomain.com
```

Then restart backend:
```bash
docker-compose restart backend
```

## 🔍 Verification

After installation, verify the fixes are working:

```bash
# Check environment variables
docker exec pdss-frontend-1 printenv REACT_APP_API_URL
docker exec pdss-backend-1 printenv ALLOWED_ORIGINS

# Test CORS
curl -v -H "Origin: http://YOUR_FRONTEND_URL" \
     http://YOUR_SERVER_IP:8000/health 2>&1 | grep -i "access-control"

# Check backend logs
docker logs pdss-backend-1 --tail 20
```

## 🐛 Troubleshooting

### Frontend can't connect to backend

1. **Check API URL:**
   ```bash
   docker exec pdss-frontend-1 printenv REACT_APP_API_URL
   ```
   - Should be `http://backend:8000` for Docker internal
   - Should be `http://SERVER_IP:8000` for external browser access

2. **Update REACT_APP_API_URL:**
   - Edit `docker-compose.yml`
   - Change `REACT_APP_API_URL` to match your server IP
   - Restart frontend: `docker-compose restart frontend`

### CORS errors in browser

1. **Check ALLOWED_ORIGINS:**
   ```bash
   docker exec pdss-backend-1 printenv ALLOWED_ORIGINS
   ```
   Should show `*` or your specific origins

2. **Verify backend config:**
   ```bash
   docker exec pdss-backend-1 python -c "from app.config import settings; print(settings.get_allowed_origins())"
   ```

3. **Restart backend:**
   ```bash
   docker-compose restart backend
   ```

### Network connectivity issues

If Docker can't pull images:

1. **Check internet:**
   ```bash
   ping -c 3 registry-1.docker.io
   ```

2. **Pre-pull images manually:**
   ```bash
   docker pull python:3.11-slim
   docker pull node:18-alpine
   docker pull postgres:15-alpine
   ```

3. **Then run installer again**

## 📝 Installation Verification Checklist

- [x] Docker and Docker Compose installed
- [x] All containers started successfully
- [x] Frontend accessible at `http://localhost:3000` (or server IP)
- [x] Backend health check: `curl http://localhost:8000/health`
- [x] No CORS errors in browser console
- [x] API calls working (check Network tab in browser)
- [x] Can login to application

## 🔄 Version History

**v1.0.1** (Current)
- Added REACT_APP_API_URL configuration
- Added ALLOWED_ORIGINS for CORS
- Updated backend config with get_allowed_origins() method
- Improved Docker build error handling

**v1.0.0**
- Initial release

