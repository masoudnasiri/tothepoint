# Production Configuration - Server IP: 193.162.129.58

## 🔒 Production Settings Applied

This package is configured for production deployment on server **193.162.129.58**.

### Environment Variables Configured

#### Backend Service:
```yaml
ENVIRONMENT=production          # Production mode (not development)
DEBUG=false                     # Disable debug mode for security
ALLOWED_ORIGINS=http://193.162.129.58:3000,http://localhost:3000  # Specific origins only (no wildcard)
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/procurement_dss
SECRET_KEY=your-secret-key-change-in-production-please-use-strong-key  # ⚠️ CHANGE THIS!
```

#### Frontend Service:
```yaml
REACT_APP_API_URL=http://193.162.129.58:8000  # Production server IP
CHOKIDAR_USEPOLLING=true                       # File watching for development mode
```

### Security Considerations

✅ **Production Environment**: `ENVIRONMENT=production`  
✅ **Debug Disabled**: `DEBUG=false`  
✅ **Specific CORS Origins**: Only allows `http://193.162.129.58:3000` and `localhost:3000`  
✅ **Correct API URL**: Frontend points to production server IP

⚠️ **IMPORTANT - Manual Changes Required:**

1. **Change SECRET_KEY** (Critical for Security):
   ```bash
   # Generate a secure random key
   openssl rand -hex 32
   
   # Edit docker-compose.yml and replace:
   SECRET_KEY=<generated-key-here>
   ```

2. **Change Database Password**:
   ```bash
   # Edit docker-compose.yml and update:
   POSTGRES_PASSWORD=<strong-password>
   DATABASE_URL=postgresql://postgres:<strong-password>@postgres:5432/procurement_dss
   ```

3. **Change Default User Passwords**:
   - Login after first installation
   - Change all default passwords immediately
   - Default users: admin, pmo, finance, etc.

### Access URLs

- **Frontend**: `http://193.162.129.58:3000`
- **Backend API**: `http://193.162.129.58:8000`
- **Backend Health**: `http://193.162.129.58:8000/health`
- **Database**: `localhost:5432` (internal Docker network only)

### Firewall Configuration

Ensure these ports are open:

```bash
# Frontend
sudo ufw allow 3000/tcp

# Backend API
sudo ufw allow 8000/tcp

# Database (internal only - should NOT be exposed externally)
# Port 5432 should be blocked externally for security
```

### Network Configuration

- **Internal Docker Network**: Services communicate via `procurement_network`
- **External Access**: Browser connects to `http://193.162.129.58:3000`
- **API Calls**: Browser makes requests to `http://193.162.129.58:8000`

### Verification Steps

After installation:

```bash
# 1. Check environment variables
docker exec pdss-backend-1 printenv | grep -E "ENVIRONMENT|DEBUG|ALLOWED_ORIGINS"
docker exec pdss-frontend-1 printenv | grep REACT_APP_API_URL

# 2. Test backend health
curl http://193.162.129.58:8000/health

# 3. Test CORS headers
curl -v -H "Origin: http://193.162.129.58:3000" \
     http://193.162.129.58:8000/health 2>&1 | grep -i "access-control"

# 4. Verify containers are running
docker-compose ps
```

### Expected Results

```bash
# Environment check should show:
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=http://193.162.129.58:3000,http://localhost:3000
REACT_APP_API_URL=http://193.162.129.58:8000

# CORS header should include:
access-control-allow-origin: http://193.162.129.58:3000
```

### Troubleshooting

#### If CORS errors persist:

1. **Verify ALLOWED_ORIGINS**:
   ```bash
   docker exec pdss-backend-1 printenv ALLOWED_ORIGINS
   # Should show: http://193.162.129.58:3000,http://localhost:3000
   ```

2. **Restart backend**:
   ```bash
   docker-compose restart backend
   ```

#### If API calls fail:

1. **Verify REACT_APP_API_URL**:
   ```bash
   docker exec pdss-frontend-1 printenv REACT_APP_API_URL
   # Should show: http://193.162.129.58:8000
   ```

2. **Test backend connectivity**:
   ```bash
   curl http://193.162.129.58:8000/health
   ```

3. **Restart frontend**:
   ```bash
   docker-compose restart frontend
   ```

### Important Notes

- ⚠️ **This configuration is for server IP `193.162.129.58` specifically**
- ⚠️ **If deploying to a different server, update the IP in docker-compose.yml**
- ⚠️ **For HTTPS, additional configuration is required (reverse proxy, SSL certificates)**
- ⚠️ **Database should NEVER be exposed externally**

