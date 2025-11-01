# Creating Production Package - Server IP: 193.162.129.58

## ✅ What's Configured

The package creator now automatically configures the package for **production deployment** on server **193.162.129.58**:

### Automatic Production Settings:

1. **Environment**: `production` (not development)
2. **Debug Mode**: `false` (disabled for security)
3. **API URL**: `http://193.162.129.58:8000` (production server IP)
4. **CORS Origins**: `http://193.162.129.58:3000,http://localhost:3000` (specific origins, no wildcard)

### Security Features:

✅ Production environment mode  
✅ Debug disabled  
✅ Specific CORS origins (not wildcard *)  
✅ Correct API URL for external browser access

## 📦 Creating the Package

### On Windows:

```powershell
cd installation_packages
powershell -ExecutionPolicy Bypass -File create_unified_deployment_packages.ps1
```

### What Happens:

1. ✅ Copies all application files
2. ✅ **Automatically configures docker-compose.yml for production:**
   - Sets `ENVIRONMENT=production`
   - Sets `DEBUG=false`
   - Sets `REACT_APP_API_URL=http://193.162.129.58:8000`
   - Sets `ALLOWED_ORIGINS=http://193.162.129.58:3000,http://localhost:3000`
3. ✅ Verifies all critical settings are correct
4. ✅ Creates both Linux and Windows packages

### Package Output:

```
pdss-linux-v1.0.1_TIMESTAMP/
├── install.sh
├── docker-compose.yml  ✅ Production configured
├── backend/
├── frontend/
└── scripts/

pdss-windows-v1.0.1_TIMESTAMP/
├── INSTALL.bat
├── docker-compose.yml  ✅ Production configured
├── backend/
├── frontend/
└── scripts/
```

## 🔍 Verification During Creation

The script verifies:

✅ `REACT_APP_API_URL` contains `193.162.129.58`  
✅ `ALLOWED_ORIGINS` contains `193.162.129.58:3000`  
✅ `ENVIRONMENT=production` (not development)  
✅ `DEBUG=false` (not true)  
✅ Backend config.py includes `get_allowed_origins()` method  
✅ Backend main.py uses `get_allowed_origins()`

## 📋 Post-Installation Steps

After installing the package, you should:

### 1. Change SECRET_KEY (CRITICAL):

```bash
# Generate secure key
openssl rand -hex 32

# Edit docker-compose.yml
nano docker-compose.yml

# Replace:
SECRET_KEY=your-secret-key-change-in-production-please-use-strong-key
# With:
SECRET_KEY=<your-generated-key>
```

### 2. Change Database Password:

```bash
# Edit docker-compose.yml
# Update:
POSTGRES_PASSWORD=<strong-password>
DATABASE_URL=postgresql://postgres:<strong-password>@postgres:5432/procurement_dss
```

### 3. Restart Services:

```bash
docker-compose down
docker-compose up -d
```

### 4. Verify Configuration:

```bash
# Check environment variables
docker exec pdss-backend-1 printenv | grep -E "ENVIRONMENT|DEBUG|ALLOWED_ORIGINS"
docker exec pdss-frontend-1 printenv REACT_APP_API_URL

# Test backend
curl http://193.162.129.58:8000/health

# Test CORS
curl -v -H "Origin: http://193.162.129.58:3000" \
     http://193.162.129.58:8000/health | grep -i "access-control"
```

## ⚠️ Important Notes

1. **Server IP is Hardcoded**: The package is specifically configured for `193.162.129.58`
2. **If Deploying to Different Server**: You'll need to manually update `docker-compose.yml` with the new IP
3. **Security**: Remember to change `SECRET_KEY` and database passwords after installation
4. **Firewall**: Ensure ports 3000 and 8000 are open (but NOT 5432 - database should be internal only)

## 🎯 Expected Configuration

After installation, `docker-compose.yml` should contain:

```yaml
backend:
  environment:
    - ENVIRONMENT=production
    - DEBUG=false
    - ALLOWED_ORIGINS=http://193.162.129.58:3000,http://localhost:3000

frontend:
  environment:
    - REACT_APP_API_URL=http://193.162.129.58:8000
```

This ensures:
- ✅ Browser can access frontend at `http://193.162.129.58:3000`
- ✅ Frontend API calls go to `http://193.162.129.58:8000`
- ✅ Backend allows CORS from the correct origin
- ✅ Production security settings are enabled

