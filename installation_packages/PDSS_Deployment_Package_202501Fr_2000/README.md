# 📦 **Procurement Decision Support System - Installation Package**

## 🚀 **One-Click Installation**

This package provides easy installers for both Windows and Linux systems.

---

## 📋 **Prerequisites:**

### **For Windows:**
- Windows 10/11 (64-bit)
- Docker Desktop for Windows
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space

### **For Linux:**
- Ubuntu 20.04+, Debian 10+, CentOS 7+, or RHEL 7+
- Docker Engine
- Docker Compose
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space

---

## 🪟 **Windows Installation:**

### **Step 1: Install Docker Desktop**
1. Download from: https://www.docker.com/products/docker-desktop
2. Run installer
3. Restart computer
4. Start Docker Desktop
5. Wait for "Docker is running" indicator

### **Step 2: Run Installer**
1. Right-click `install_windows.bat`
2. Select **"Run as Administrator"**
3. Wait 10-15 minutes for installation
4. Browser will open automatically

### **Step 3: Login**
```
URL: http://localhost:3000
Admin: admin / admin123
```

### **Desktop Shortcuts Created:**
- `Start PDSS.bat` - Start the platform
- `Stop PDSS.bat` - Stop the platform

---

## 🐧 **Linux Installation:**

### **Step 1: Install Docker (if not installed)**

**Ubuntu/Debian:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

**CentOS/RHEL:**
```bash
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

### **Step 2: Install Docker Compose (if not installed)**
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### **Step 3: Run Installer**
```bash
chmod +x install_linux.sh
sudo ./install_linux.sh
```

### **Step 4: Login**
```
URL: http://localhost:3000
Admin: admin / admin123
```

### **Management Scripts Created:**
- `~/start-pdss.sh` - Start the platform
- `~/stop-pdss.sh` - Stop the platform
- `~/logs-pdss.sh` - View logs

---

## 🔐 **Default User Accounts:**

| Role | Username | Password | Access Level |
|------|----------|----------|--------------|
| **Admin** | admin | admin123 | Full system access |
| **Finance** | finance1 | finance123 | Finance, budgets, analytics |
| **PM** | pm1 | pm123 | Projects, items, optimization |
| **PMO** | pmo1 | pmo123 | All projects oversight |
| **Procurement** | proc1 | proc123 | Procurement options |

**⚠️ IMPORTANT:** Change these passwords after first login!

---

## 📊 **What's Included:**

### **Core Features:**
- ✅ Project Management
- ✅ Item Catalog & Management
- ✅ Procurement Options
- ✅ Budget Management
- ✅ OR-Tools Optimization Engine
- ✅ Multi-Solver Support (CP-SAT, GLOP, MIP)
- ✅ Advanced Optimization Strategies
- ✅ Decision Management
- ✅ Cash Flow Analysis
- ✅ Analytics Dashboard (EVA, Risk, Forecasting)
- ✅ User Management & RBAC
- ✅ Excel Import/Export

### **Technology Stack:**
- **Backend:** FastAPI + PostgreSQL + OR-Tools
- **Frontend:** React + TypeScript + Material-UI
- **Deployment:** Docker + Docker Compose
- **Analytics:** Recharts + Statistical Analysis

---

## 🛠️ **Post-Installation:**

### **Starting the Platform:**

**Windows:**
```
Double-click "Start PDSS.bat" on desktop
```

**Linux:**
```bash
~/start-pdss.sh
```

### **Stopping the Platform:**

**Windows:**
```
Double-click "Stop PDSS.bat" on desktop
```

**Linux:**
```bash
~/stop-pdss.sh
```

### **Viewing Logs:**

**Windows:**
```cmd
cd C:\path\to\installation
docker-compose logs -f
```

**Linux:**
```bash
~/logs-pdss.sh
```

### **Checking Status:**

**Both:**
```bash
docker-compose ps
```

---

## 🔧 **Troubleshooting:**

### **Issue 1: Port Already in Use**
```
Error: Bind for 0.0.0.0:3000 failed: port is already allocated
```

**Solution:**
```bash
# Stop conflicting service
# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux:
sudo lsof -i :3000
sudo kill -9 <PID>
```

### **Issue 2: Docker Not Running**
```
Error: Cannot connect to the Docker daemon
```

**Solution:**
```bash
# Windows: Start Docker Desktop manually
# Linux:
sudo systemctl start docker
```

### **Issue 3: Permission Denied (Linux)**
```
Error: Got permission denied while trying to connect to Docker daemon
```

**Solution:**
```bash
sudo usermod -aG docker $USER
newgrp docker
# Or run installer with sudo
```

### **Issue 4: Out of Memory**
```
Error: Container killed (OOMKilled)
```

**Solution:**
- Increase Docker memory limit to 8GB+
- Windows: Docker Desktop → Settings → Resources
- Linux: Increase system swap space

---

## 📚 **Documentation:**

After installation, check these files in the project root:

- `README.md` - Complete system documentation
- `USER_GUIDE.md` - User manual
- `COMPLETE_SYSTEM_DOCUMENTATION.md` - Technical specs
- `📊_COMMERCIAL_PLATFORM_OVERVIEW.md` - Business overview
- `📊_RISK_ANALYSIS_METHODOLOGY_FOR_REVIEW.md` - Analytics methodology

---

## 🔄 **Updating the Platform:**

### **To Update to Latest Version:**

**Windows:**
```cmd
cd C:\path\to\installation
git pull
docker-compose down
install_windows.bat
```

**Linux:**
```bash
cd /path/to/installation
git pull
sudo ./install_linux.sh
```

---

## 🗑️ **Uninstallation:**

### **Complete Removal:**

**Windows:**
```cmd
cd C:\path\to\installation
docker-compose down -v
docker system prune -a
# Delete installation folder
# Delete desktop shortcuts
```

**Linux:**
```bash
cd /path/to/installation
docker-compose down -v
docker system prune -a
rm -rf ~/start-pdss.sh ~/stop-pdss.sh ~/logs-pdss.sh
rm -rf ~/Desktop/start-pdss.desktop ~/Desktop/stop-pdss.desktop
# Delete installation folder
```

---

## 🌐 **Network Access:**

### **Access from Other Computers:**

**Windows:**
1. Open Windows Firewall
2. Allow port 3000
3. Access from other PCs: `http://<your-ip>:3000`

**Linux:**
```bash
# Open firewall
sudo ufw allow 3000
# Or for firewalld:
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --reload

# Access from other PCs: http://<your-ip>:3000
```

---

## 📞 **Support:**

### **Getting Help:**

1. **Check logs:**
   - Windows: `docker-compose logs backend`
   - Linux: `~/logs-pdss.sh`

2. **Restart services:**
   - Windows: Run `Stop PDSS.bat` then `Start PDSS.bat`
   - Linux: `~/stop-pdss.sh && ~/start-pdss.sh`

3. **Reset database:**
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

---

## ✅ **Installation Checklist:**

- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] Docker running
- [ ] Installer executed successfully
- [ ] All 3 containers running (db, backend, frontend)
- [ ] Browser opens to http://localhost:3000
- [ ] Can login with admin/admin123
- [ ] Desktop shortcuts created
- [ ] Passwords changed from defaults

---

## 🎉 **You're All Set!**

The Procurement Decision Support System is now installed and running!

**Access:** http://localhost:3000
**Login:** admin / admin123

**Enjoy optimizing your procurement decisions!** 🚀

