# 📦 **Installation Package - Complete Index**

## 📁 **Package Contents:**

```
installation_packages/
├── README.md                    # Overview and quick instructions
├── QUICK_START.md              # 3-step installation guide
├── INSTALLATION_GUIDE.md       # Detailed installation instructions
├── SYSTEM_REQUIREMENTS.md      # Hardware/software requirements
├── config_template.env         # Configuration template
│
├── install_windows.bat         # Windows installer (Run as Admin)
├── uninstall_windows.bat       # Windows uninstaller
│
├── install_linux.sh            # Linux installer (chmod +x first)
└── uninstall_linux.sh          # Linux uninstaller
```

---

## 🚀 **Quick Start:**

### **Windows (2 Steps):**
1. Install Docker Desktop
2. Run `install_windows.bat` as Administrator

### **Linux (2 Steps):**
1. Install Docker + Docker Compose
2. Run `sudo ./install_linux.sh`

**Done in 15 minutes!** ⏱️

---

## 📖 **Documentation Files:**

### **1. README.md**
- **Purpose:** Package overview
- **Content:** Installation options, troubleshooting, management
- **Read First:** ✅ Start here

### **2. QUICK_START.md**
- **Purpose:** Fastest way to install
- **Content:** 3-step guide for both platforms
- **For:** Users who want quick installation

### **3. INSTALLATION_GUIDE.md**
- **Purpose:** Complete installation instructions
- **Content:** Detailed steps, verification, troubleshooting
- **For:** Users who want detailed guidance

### **4. SYSTEM_REQUIREMENTS.md**
- **Purpose:** Hardware/software specifications
- **Content:** Minimum/recommended specs, performance data
- **For:** Planning and capacity assessment

### **5. config_template.env**
- **Purpose:** Configuration template
- **Content:** All configurable parameters
- **For:** Advanced users, production deployment

---

## 🛠️ **Installer Files:**

### **Windows Installers:**

#### **install_windows.bat**
- **Purpose:** Automated Windows installation
- **Requirements:** Administrator privileges
- **Duration:** 10-15 minutes
- **Creates:** Desktop shortcuts, management scripts
- **Features:**
  - ✅ Checks prerequisites
  - ✅ Builds Docker images
  - ✅ Starts all services
  - ✅ Creates shortcuts
  - ✅ Opens browser automatically

#### **uninstall_windows.bat**
- **Purpose:** Complete removal
- **Requirements:** Administrator privileges
- **Duration:** 2-3 minutes
- **Removes:** Containers, volumes, shortcuts

---

### **Linux Installers:**

#### **install_linux.sh**
- **Purpose:** Automated Linux installation
- **Requirements:** sudo access
- **Duration:** 10-15 minutes
- **Creates:** Management scripts, desktop shortcuts
- **Features:**
  - ✅ Checks prerequisites
  - ✅ Installs Docker Compose if missing
  - ✅ Builds Docker images
  - ✅ Starts all services
  - ✅ Creates management scripts
  - ✅ Opens browser automatically

#### **uninstall_linux.sh**
- **Purpose:** Complete removal
- **Requirements:** sudo access
- **Duration:** 2-3 minutes
- **Removes:** Containers, volumes, scripts, shortcuts

---

## 📊 **What Gets Installed:**

### **Docker Containers:**
1. **PostgreSQL Database** (Port 5432)
   - Stores all application data
   - Persistent volume for data retention
   - Automatic initialization with sample data

2. **FastAPI Backend** (Port 8000)
   - REST API server
   - OR-Tools optimization engine
   - Authentication & authorization
   - Business logic

3. **React Frontend** (Port 3000)
   - User interface
   - Material-UI components
   - Interactive dashboards
   - Charts and visualizations

### **Desktop Shortcuts (Windows):**
- `Start PDSS.bat` - One-click start
- `Stop PDSS.bat` - One-click stop

### **Management Scripts (Linux):**
- `~/start-pdss.sh` - Start platform
- `~/stop-pdss.sh` - Stop platform
- `~/logs-pdss.sh` - View logs

---

## 🎯 **Installation Options:**

### **Option 1: Standard Installation (Recommended)**
- Uses installers provided
- Automatic setup
- Desktop shortcuts
- Sample data included
- **Best for:** Most users

### **Option 2: Manual Installation**
```bash
# Clone or extract project
cd project_folder

# Start services
docker-compose up -d

# Access
http://localhost:3000
```
- **Best for:** Developers, advanced users

### **Option 3: Custom Configuration**
1. Copy `config_template.env` to project root as `.env`
2. Edit configuration
3. Run installer
- **Best for:** Production deployment

---

## 🔐 **Security Considerations:**

### **Development/Testing:**
- ✅ Default passwords OK
- ✅ HTTP OK
- ✅ Local access only

### **Production Deployment:**
- ⚠️ Change all default passwords
- ⚠️ Enable HTTPS (reverse proxy)
- ⚠️ Configure firewall
- ⚠️ Regular backups
- ⚠️ Monitor logs
- ⚠️ Update regularly

---

## 📈 **Performance Optimization:**

### **For Better Performance:**

#### **Increase Docker Resources:**

**Windows:**
1. Docker Desktop → Settings → Resources
2. Memory: 8GB → 16GB
3. CPUs: 2 → 4
4. Swap: 1GB → 2GB
5. Apply & Restart

**Linux:**
```bash
# Check current resources
docker stats

# No limits on Linux by default
# Ensure host has sufficient resources
```

#### **Database Tuning:**
Edit `docker-compose.yml`:
```yaml
db:
  environment:
    - POSTGRES_SHARED_BUFFERS=2GB
    - POSTGRES_WORK_MEM=50MB
    - POSTGRES_MAINTENANCE_WORK_MEM=512MB
```

---

## 🌐 **Network Configuration:**

### **Access from Other Computers:**

#### **Windows:**
1. Windows Defender Firewall → Advanced Settings
2. Inbound Rules → New Rule
3. Port: 3000, TCP, Allow
4. Access: `http://<your-ip>:3000`

#### **Linux:**
```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 3000/tcp

# firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --reload

# Access: http://<your-ip>:3000
```

---

## 💾 **Backup & Restore:**

### **Backup Database:**

**Windows:**
```cmd
docker-compose exec db pg_dump -U postgres procurement_dss > backup.sql
```

**Linux:**
```bash
docker-compose exec db pg_dump -U postgres procurement_dss > backup.sql
```

### **Restore Database:**

**Both:**
```bash
docker-compose exec -T db psql -U postgres procurement_dss < backup.sql
```

---

## 🔄 **Maintenance:**

### **Update Platform:**
```bash
# Stop platform
docker-compose down

# Pull latest changes (if using git)
git pull

# Rebuild and restart
docker-compose up -d --build
```

### **Clean Up Docker:**
```bash
# Remove unused images/containers
docker system prune

# Remove everything (WARNING: removes all Docker data)
docker system prune -a --volumes
```

### **View Resource Usage:**
```bash
docker stats
```

---

## 📋 **Installation Checklist:**

### **Before Installation:**
- [ ] System meets minimum requirements
- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] Docker running
- [ ] Ports 3000, 8000, 5432 available
- [ ] Administrator/sudo access
- [ ] 20GB+ free disk space

### **During Installation:**
- [ ] Installer runs without errors
- [ ] All 3 containers start
- [ ] No error messages in logs
- [ ] Browser opens automatically

### **After Installation:**
- [ ] Can access http://localhost:3000
- [ ] Can login with admin/admin123
- [ ] Dashboard loads
- [ ] Can view projects
- [ ] Can run optimization
- [ ] Analytics dashboard works
- [ ] Shortcuts created
- [ ] Passwords changed

---

## 🎉 **Installation Complete!**

Your Procurement Decision Support System is now ready to use!

**Next Steps:**
1. ✅ Change default passwords
2. ✅ Review sample data
3. ✅ Run test optimization
4. ✅ Explore analytics
5. ✅ Read user guide

**Enjoy optimizing your procurement!** 🚀

