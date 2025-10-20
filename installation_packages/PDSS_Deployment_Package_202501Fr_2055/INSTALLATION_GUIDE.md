# 📦 **Complete Installation Guide**

## 📋 **Table of Contents:**

1. [Windows Installation](#windows-installation)
2. [Linux Installation](#linux-installation)
3. [Verification](#verification)
4. [First Login](#first-login)
5. [Troubleshooting](#troubleshooting)
6. [Uninstallation](#uninstallation)

---

## 🪟 **Windows Installation:**

### **Prerequisites:**

#### **Install Docker Desktop:**
1. Download from: https://www.docker.com/products/docker-desktop
2. Run installer (`Docker Desktop Installer.exe`)
3. Follow installation wizard
4. **Restart your computer** (required!)
5. Start Docker Desktop
6. Wait for "Docker Desktop is running" in system tray

#### **Verify Docker:**
```cmd
docker --version
docker-compose --version
docker ps
```
All commands should work without errors.

---

### **Installation Steps:**

#### **Step 1: Download Installation Package**
- Extract `installation_packages` folder to desired location
- Example: `C:\PDSS\`

#### **Step 2: Run Installer**
1. Navigate to installation folder
2. Right-click `install_windows.bat`
3. Select **"Run as Administrator"**
4. Wait for installation (10-15 minutes)

#### **Step 3: Installation Progress**
```
[1/8] Checking prerequisites...
[2/8] Stopping any existing containers...
[3/8] Building Docker images... (5-10 minutes)
[4/8] Starting database...
[5/9] Starting backend service...
[6/8] Starting frontend service...
[7/8] Verifying installation...
[8/8] Creating desktop shortcuts...
```

#### **Step 4: Automatic Browser Launch**
- Browser opens automatically to http://localhost:3000
- If not, open manually

---

## 🐧 **Linux Installation:**

### **Prerequisites:**

#### **Install Docker (Ubuntu/Debian):**
```bash
# Update package index
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Apply group membership
newgrp docker

# Verify
docker --version
```

#### **Install Docker (CentOS/RHEL):**
```bash
# Install Docker
sudo yum install -y docker

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER

# Verify
docker --version
```

#### **Install Docker Compose:**
```bash
# Download
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker-compose --version
```

---

### **Installation Steps:**

#### **Step 1: Download Installation Package**
```bash
# Extract to desired location
cd /opt
sudo mkdir pdss
cd pdss
# Copy installation_packages here
```

#### **Step 2: Make Installer Executable**
```bash
chmod +x install_linux.sh
```

#### **Step 3: Run Installer**
```bash
sudo ./install_linux.sh
```

#### **Step 4: Installation Progress**
```
[1/9] Checking prerequisites...
[2/9] Stopping any existing containers...
[3/9] Building Docker images... (5-10 minutes)
[4/9] Starting database...
[5/9] Starting backend service...
[6/9] Starting frontend service...
[7/9] Verifying installation...
[8/9] Creating management scripts...
[9/9] Creating desktop shortcuts...
```

#### **Step 5: Access Platform**
```bash
# Browser opens automatically
# Or open manually: http://localhost:3000
```

---

## ✅ **Verification:**

### **Check All Services Running:**

**Windows:**
```cmd
docker-compose ps
```

**Linux:**
```bash
docker-compose ps
```

**Expected Output:**
```
NAME                           STATUS
cahs_flow_project-backend-1    Up
cahs_flow_project-db-1         Up
cahs_flow_project-frontend-1   Up
```

### **Check Logs:**

**Windows:**
```cmd
docker-compose logs backend
docker-compose logs frontend
```

**Linux:**
```bash
~/logs-pdss.sh
# Or
docker-compose logs -f
```

### **Test Access:**
1. Open browser: http://localhost:3000
2. Should see login page
3. Login with: `admin` / `admin123`
4. Should see dashboard

---

## 🔐 **First Login:**

### **Step 1: Login as Admin**
```
URL: http://localhost:3000
Username: admin
Password: admin123
```

### **Step 2: Change Default Passwords**
1. Go to **User Management**
2. Edit each user
3. Change passwords
4. Save changes

### **Step 3: Explore Sample Data**
- **10 Projects** - IT company projects
- **310 Items** - Comprehensive procurement items
- **143 Options** - Supplier options
- **Budget Data** - 12 months of budgets

### **Step 4: Run Test Optimization**
1. Go to **Advanced Optimization**
2. Select projects
3. Choose strategy
4. Run optimization
5. View results

### **Step 5: Check Analytics**
1. Go to **Analytics & Forecast**
2. Select a project
3. Explore 3 tabs (EVA, Cash Flow, Risk)
4. Try Portfolio View (All Projects)

---

## 🛠️ **Troubleshooting:**

### **Issue 1: Port Already in Use**

**Symptoms:**
```
Error: Bind for 0.0.0.0:3000 failed: port is already allocated
```

**Solution (Windows):**
```cmd
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Solution (Linux):**
```bash
sudo lsof -i :3000
sudo kill -9 <PID>
```

---

### **Issue 2: Docker Not Running**

**Symptoms:**
```
Cannot connect to the Docker daemon
```

**Solution (Windows):**
- Start Docker Desktop manually
- Wait for "Docker Desktop is running"

**Solution (Linux):**
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

---

### **Issue 3: Permission Denied (Linux)**

**Symptoms:**
```
Got permission denied while trying to connect to Docker daemon
```

**Solution:**
```bash
sudo usermod -aG docker $USER
newgrp docker
# Or logout and login again
```

---

### **Issue 4: Build Fails**

**Symptoms:**
```
Error: failed to solve: process "/bin/sh -c npm install" did not complete
```

**Solution:**
```bash
# Clear Docker cache
docker system prune -a
# Retry installation
```

---

### **Issue 5: Out of Memory**

**Symptoms:**
```
Container killed (OOMKilled)
```

**Solution (Windows):**
1. Docker Desktop → Settings → Resources
2. Increase Memory to 8GB+
3. Apply & Restart

**Solution (Linux):**
```bash
# Check available memory
free -h
# Increase swap if needed
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

### **Issue 6: Frontend Not Loading**

**Symptoms:**
- Backend works (http://localhost:8000/docs)
- Frontend shows blank page

**Solution:**
```bash
# Rebuild frontend
docker-compose up -d --build frontend
# Wait 2 minutes
# Clear browser cache (Ctrl+Shift+R)
```

---

## 🗑️ **Uninstallation:**

### **Windows:**
1. Run `uninstall_windows.bat` as Administrator
2. Confirm removal
3. Delete installation folder
4. Delete desktop shortcuts (if any remain)

### **Linux:**
```bash
sudo ./uninstall_linux.sh
# Delete installation folder
sudo rm -rf /opt/pdss
```

### **Complete Docker Cleanup:**
```bash
# Remove all unused Docker resources
docker system prune -a --volumes

# WARNING: This removes ALL Docker data, not just PDSS!
```

---

## 🔄 **Updating:**

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

## 📞 **Getting Help:**

### **Check Logs:**

**Windows:**
```cmd
docker-compose logs backend --tail=100
docker-compose logs frontend --tail=100
```

**Linux:**
```bash
~/logs-pdss.sh
```

### **Restart Services:**

**Windows:**
```cmd
Stop PDSS.bat
Start PDSS.bat
```

**Linux:**
```bash
~/stop-pdss.sh
~/start-pdss.sh
```

### **Reset Database:**
```bash
docker-compose down -v
docker-compose up -d
# Database will be recreated with sample data
```

---

## 📊 **Post-Installation Checklist:**

- [ ] All 3 containers running (db, backend, frontend)
- [ ] Can access http://localhost:3000
- [ ] Can login with admin/admin123
- [ ] Dashboard loads correctly
- [ ] Can view projects
- [ ] Can run optimization
- [ ] Analytics dashboard works
- [ ] Desktop shortcuts created
- [ ] Default passwords changed
- [ ] Firewall configured (if needed)

---

## 🎉 **Success!**

If all checklist items are complete, your installation is successful!

**Access:** http://localhost:3000
**Login:** admin / admin123

**Enjoy your Procurement Decision Support System!** 🚀

