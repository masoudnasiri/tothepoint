# 💻 **System Requirements**

## 🪟 **Windows Requirements:**

### **Minimum:**
- **OS:** Windows 10 (64-bit) or Windows 11
- **Processor:** Intel Core i3 or equivalent
- **RAM:** 8GB
- **Disk Space:** 20GB free
- **Software:** Docker Desktop for Windows

### **Recommended:**
- **OS:** Windows 11 Pro
- **Processor:** Intel Core i5 or better
- **RAM:** 16GB
- **Disk Space:** 50GB free (SSD preferred)
- **Software:** Docker Desktop for Windows (latest)

---

## 🐧 **Linux Requirements:**

### **Minimum:**
- **OS:** Ubuntu 20.04, Debian 10, CentOS 7, or RHEL 7 (or newer)
- **Processor:** 2 CPU cores
- **RAM:** 8GB
- **Disk Space:** 20GB free
- **Software:** Docker Engine + Docker Compose

### **Recommended:**
- **OS:** Ubuntu 22.04 LTS or Debian 11
- **Processor:** 4 CPU cores or more
- **RAM:** 16GB
- **Disk Space:** 50GB free (SSD preferred)
- **Software:** Docker Engine (latest) + Docker Compose v2

---

## 🌐 **Network Requirements:**

### **Ports Used:**
- **3000** - Frontend (React app)
- **8000** - Backend API (FastAPI)
- **5432** - PostgreSQL database

### **Firewall:**
- Allow outbound connections (for Docker image downloads)
- Allow inbound on port 3000 (if accessing from other computers)

### **Internet:**
- Required for initial installation (Docker images download)
- Optional after installation (offline operation supported)

---

## 🔧 **Software Dependencies:**

### **Automatically Installed (via Docker):**
- ✅ PostgreSQL 15
- ✅ Python 3.11
- ✅ Node.js 18
- ✅ FastAPI
- ✅ React 18
- ✅ OR-Tools
- ✅ All Python/Node packages

### **You Need to Install:**
- Docker Desktop (Windows) or Docker Engine (Linux)
- Docker Compose
- Web browser (Chrome, Firefox, Edge, Safari)

---

## 📊 **Performance Specifications:**

### **Optimization Performance:**

| Items | RAM Usage | CPU Usage | Time (CP-SAT) |
|-------|-----------|-----------|---------------|
| 50 | 2GB | 50% | 5-10 seconds |
| 100 | 3GB | 70% | 10-20 seconds |
| 300 | 5GB | 90% | 30-60 seconds |
| 500+ | 8GB+ | 100% | 1-3 minutes |

### **Database Performance:**

| Projects | Items | Decisions | DB Size | Query Time |
|----------|-------|-----------|---------|------------|
| 10 | 300 | 500 | 100MB | <100ms |
| 50 | 1,500 | 2,500 | 500MB | <200ms |
| 100 | 3,000 | 5,000 | 1GB | <500ms |
| 500+ | 15,000+ | 25,000+ | 5GB+ | <1s |

---

## 🎯 **Recommended Configurations:**

### **Small Organization (1-10 projects):**
```
CPU: 2 cores
RAM: 8GB
Disk: 20GB
Users: 5-10 concurrent
```

### **Medium Organization (10-50 projects):**
```
CPU: 4 cores
RAM: 16GB
Disk: 50GB
Users: 10-30 concurrent
```

### **Large Organization (50+ projects):**
```
CPU: 8+ cores
RAM: 32GB
Disk: 100GB SSD
Users: 30+ concurrent
Consider: Separate DB server
```

---

## 🌐 **Browser Compatibility:**

### **Fully Supported:**
- ✅ Google Chrome 90+
- ✅ Microsoft Edge 90+
- ✅ Mozilla Firefox 88+
- ✅ Safari 14+

### **Not Supported:**
- ❌ Internet Explorer (any version)
- ❌ Browsers older than 2 years

---

## 🔒 **Security Requirements:**

### **For Production Use:**

1. **Change Default Passwords** ⚠️
2. **Enable HTTPS** (use reverse proxy like Nginx)
3. **Configure Firewall** (restrict port 3000)
4. **Regular Backups** (database + files)
5. **Update Docker Images** (monthly)

### **Optional Enhancements:**
- SSL/TLS certificates
- VPN access
- Two-factor authentication
- Audit logging
- Database encryption

---

## 📈 **Scalability:**

### **Vertical Scaling (Single Server):**
- Up to 100 projects
- Up to 5,000 items
- Up to 50 concurrent users
- Increase RAM/CPU as needed

### **Horizontal Scaling (Multiple Servers):**
- Separate database server
- Multiple backend instances (load balanced)
- Redis cache for analytics
- CDN for frontend assets

---

## 🧪 **Testing Environment:**

### **Minimum for Testing:**
```
CPU: 2 cores
RAM: 4GB
Disk: 10GB
Users: 1-2
```

### **Sample Data Included:**
- 10 IT projects
- 310 procurement items
- 143 supplier options
- 12 months budget data
- Ready for testing!

---

## ⚡ **Quick Specs:**

| Component | Technology | Resource |
|-----------|------------|----------|
| **Frontend** | React 18 + TypeScript | 512MB RAM |
| **Backend** | FastAPI + OR-Tools | 2-4GB RAM |
| **Database** | PostgreSQL 15 | 1-2GB RAM |
| **Total** | Docker Compose | 4-8GB RAM |

---

## ✅ **Pre-Installation Checklist:**

- [ ] OS meets minimum requirements
- [ ] 8GB+ RAM available
- [ ] 20GB+ disk space free
- [ ] Docker installed and running
- [ ] Docker Compose installed
- [ ] Ports 3000, 8000, 5432 available
- [ ] Internet connection (for first install)
- [ ] Administrator/sudo access

---

## 🎉 **Ready to Install?**

**Windows:** Run `install_windows.bat` as Administrator
**Linux:** Run `sudo ./install_linux.sh`

**Installation time: ~15 minutes**

**Questions?** Check `README.md` in this folder!

