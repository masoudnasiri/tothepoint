# 🚀 **Deployment Package Guide**

## 📦 **Creating Deployment Package:**

### **On Development Machine:**

**Windows:**
```cmd
cd installation_packages
create_deployment_package.bat
```

**Linux:**
```bash
cd installation_packages
chmod +x create_deployment_package.sh
./create_deployment_package.sh
```

**Output:**
```
PDSS_Deployment_Package_20251010_1930/
├── backend/              (Complete backend code)
├── frontend/             (Complete frontend code)
├── docs/                 (Documentation)
├── docker-compose.yml    (Docker configuration)
├── .env.example          (Configuration template)
├── install_windows.bat   (Windows installer)
├── install_linux.sh      (Linux installer)
├── uninstall_windows.bat
├── uninstall_linux.sh
├── README.md
├── QUICK_START.md
├── INSTALLATION_GUIDE.md
└── SYSTEM_REQUIREMENTS.md
```

---

## 📤 **Transferring to Server:**

### **Method 1: USB Drive / External Storage**
```
1. Copy entire package folder to USB drive
2. Connect to server
3. Copy folder to server location
```

### **Method 2: Network Transfer (SCP)**
```bash
# From development machine to server
scp -r PDSS_Deployment_Package_* user@server:/opt/pdss/
```

### **Method 3: FTP/SFTP**
```
Use FileZilla or WinSCP
Upload entire package folder
```

### **Method 4: Cloud Storage**
```
1. Zip the package folder
2. Upload to Google Drive / Dropbox / OneDrive
3. Download on server
4. Extract
```

---

## 🖥️ **Server Installation:**

### **Windows Server:**

#### **Step 1: Prerequisites**
1. Install Docker Desktop for Windows
   - Download: https://www.docker.com/products/docker-desktop
   - Requires Windows Server 2019+ or Windows 10/11
2. Restart server after Docker installation

#### **Step 2: Deploy Package**
```cmd
# Navigate to package folder
cd C:\PDSS\PDSS_Deployment_Package_*

# Run installer as Administrator
install_windows.bat
```

#### **Step 3: Verify**
```cmd
docker-compose ps
# Should show 3 running containers
```

#### **Step 4: Access**
```
http://localhost:3000
or
http://<server-ip>:3000
```

---

### **Linux Server:**

#### **Step 1: Prerequisites**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### **Step 2: Deploy Package**
```bash
# Navigate to package folder
cd /opt/pdss/PDSS_Deployment_Package_*

# Make installer executable
chmod +x install_linux.sh

# Run installer
sudo ./install_linux.sh
```

#### **Step 3: Verify**
```bash
docker-compose ps
# Should show 3 running containers
```

#### **Step 4: Access**
```
http://localhost:3000
or
http://<server-ip>:3000
```

---

## 🔐 **Post-Deployment Security:**

### **1. Change Default Passwords:**
```
Login as admin → User Management → Edit each user → Change password
```

### **2. Configure Firewall:**

**Windows Server:**
```cmd
# Open Windows Firewall
# Add inbound rule for port 3000
netsh advfirewall firewall add rule name="PDSS" dir=in action=allow protocol=TCP localport=3000
```

**Linux Server:**
```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 3000/tcp

# firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --reload
```

### **3. Enable HTTPS (Production):**

**Option A: Use Nginx Reverse Proxy**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Option B: Use Caddy (Automatic HTTPS)**
```
your-domain.com {
    reverse_proxy localhost:3000
}
```

### **4. Set Up Backups:**

**Automated Backup Script (Linux):**
```bash
#!/bin/bash
# Save as /opt/pdss/backup.sh

BACKUP_DIR="/backups/pdss"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T db pg_dump -U postgres procurement_dss > "$BACKUP_DIR/db_backup_$DATE.sql"

# Backup uploaded files (if any)
# tar -czf "$BACKUP_DIR/files_backup_$DATE.tar.gz" ./uploads

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/db_backup_$DATE.sql"
```

**Add to crontab:**
```bash
# Run daily at 2 AM
0 2 * * * /opt/pdss/backup.sh
```

---

## 🌐 **Network Configuration:**

### **Access from Client Computers:**

#### **1. Find Server IP:**

**Windows:**
```cmd
ipconfig
```

**Linux:**
```bash
ip addr show
# or
hostname -I
```

#### **2. Configure Firewall (see above)**

#### **3. Access from Clients:**
```
http://<server-ip>:3000

Example:
http://192.168.1.100:3000
```

### **DNS Configuration (Optional):**

**Add DNS record:**
```
pdss.yourcompany.com → <server-ip>
```

**Access:**
```
http://pdss.yourcompany.com:3000
```

---

## 🔄 **Updating Deployed System:**

### **Method 1: Replace Package**
```bash
# Stop current system
docker-compose down

# Replace with new package
cd /opt/pdss
rm -rf old_package
cp -r new_package/* ./

# Restart
./install_linux.sh
```

### **Method 2: Git Pull (if using git)**
```bash
cd /opt/pdss
git pull
docker-compose down
docker-compose up -d --build
```

---

## 📊 **Monitoring:**

### **Check System Status:**
```bash
# Container status
docker-compose ps

# Resource usage
docker stats

# Logs
docker-compose logs -f

# Specific service logs
docker-compose logs backend -f
```

### **Health Checks:**
```bash
# Backend API health
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000

# Database
docker-compose exec db psql -U postgres -c "SELECT 1"
```

---

## 🛠️ **Maintenance:**

### **Restart Services:**
```bash
docker-compose restart
```

### **Rebuild After Code Changes:**
```bash
docker-compose down
docker-compose up -d --build
```

### **Clear All Data (Reset):**
```bash
docker-compose down -v
docker-compose up -d
# Database will be recreated with sample data
```

### **View Database:**
```bash
docker-compose exec db psql -U postgres procurement_dss
```

---

## 📋 **Deployment Checklist:**

### **Pre-Deployment:**
- [ ] Package created successfully
- [ ] Package transferred to server
- [ ] Docker installed on server
- [ ] Docker Compose installed
- [ ] Ports 3000, 8000, 5432 available
- [ ] Firewall configured
- [ ] Backup strategy planned

### **During Deployment:**
- [ ] Installer runs without errors
- [ ] All 3 containers start
- [ ] No errors in logs
- [ ] Can access from localhost
- [ ] Can access from client machines

### **Post-Deployment:**
- [ ] Default passwords changed
- [ ] Firewall rules applied
- [ ] HTTPS configured (if production)
- [ ] Backup script set up
- [ ] Monitoring configured
- [ ] Users trained
- [ ] Documentation provided

---

## 🎯 **Production Deployment Best Practices:**

### **1. Use Environment Variables:**
```bash
# Create .env file from template
cp .env.example .env

# Edit with production values
nano .env
```

### **2. Enable Logging:**
```yaml
# In docker-compose.yml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### **3. Resource Limits:**
```yaml
# In docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### **4. Health Checks:**
```yaml
# In docker-compose.yml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 📞 **Support:**

### **Common Issues:**

**Issue: Port conflicts**
```bash
# Change ports in docker-compose.yml
ports:
  - "8080:3000"  # Frontend on 8080 instead of 3000
```

**Issue: Out of memory**
```bash
# Increase Docker memory limit
# Or add more RAM to server
```

**Issue: Slow performance**
```bash
# Check resources
docker stats

# Optimize database
docker-compose exec db psql -U postgres -c "VACUUM ANALYZE"
```

---

## ✅ **Deployment Complete!**

Your Procurement Decision Support System is now deployed and running on the server!

**Access:** `http://<server-ip>:3000`
**Login:** `admin` / `admin123`

**Remember to:**
1. ✅ Change default passwords
2. ✅ Configure backups
3. ✅ Set up monitoring
4. ✅ Enable HTTPS for production

**System is ready for production use!** 🎉

