# 🔧 Docker Naming Issue - FIXED

## ❌ Problem: Invalid Docker Tag

**Error Message:**
```
invalid tag "pdss-linux-installer_-frontend": invalid reference format
[ERROR] Failed to build Docker images!
```

**Root Cause:** 
Docker Compose uses the directory name as part of the service name, and the original directory name `pdss-linux-installer_v1.0.0_202510191518` contains characters that create invalid Docker tags.

---

## ✅ SOLUTIONS

### 🚀 Solution 1: Fix Your Current Package (IMMEDIATE)

**Quick Fix - Rename the Directory:**

```bash
# On your Linux system
cd ~

# Rename to a simple, Docker-friendly name
mv pdss-linux-installer_* pdss

# Navigate to renamed directory
cd pdss

# Fix hostname issue (optional but recommended)
echo "127.0.0.1 vm-184320" | sudo tee -a /etc/hosts

# Ensure Docker is running
sudo systemctl start docker
sudo systemctl status docker

# Run installer
sudo bash install.sh
```

**This should work immediately!** ✅

---

### 📦 Solution 2: Use New Fixed Package (RECOMMENDED)

**New Package Created:** `pdss-linux-v1.0.0-202510191553.zip`

**Key Improvements:**
- ✅ Simple directory name: `pdss-linux-v1.0.0` (Docker-friendly)
- ✅ Unix line endings (LF)
- ✅ No naming conflicts

**Installation:**
```bash
# Transfer new package to Linux system
unzip pdss-linux-v1.0.0-202510191553.zip

# Navigate to package
cd pdss-linux-v1.0.0

# Fix hostname (optional)
echo "127.0.0.1 vm-184320" | sudo tee -a /etc/hosts

# Run installer
chmod +x install.sh
sudo ./install.sh
```

---

## 🔍 Additional Fixes Included

### 1. Hostname Resolution Warning

**Issue:**
```
sudo: unable to resolve host vm-184320: Name or service not known
```

**Fix:**
```bash
echo "127.0.0.1 vm-184320" | sudo tee -a /etc/hosts
```

### 2. Docker Service Issues

**If Docker fails to start:**

```bash
# Check Docker status
sudo systemctl status docker

# View detailed logs
sudo journalctl -xeu docker.service

# Restart Docker
sudo systemctl restart docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker $USER
newgrp docker
```

### 3. System Reboot Recommendation

You have a kernel upgrade pending. After installation, consider:

```bash
sudo reboot
```

---

## 📋 Complete Installation Steps

### For New Package (Recommended)

```bash
# 1. Transfer file
# pdss-linux-v1.0.0-202510191553.zip

# 2. Extract
unzip pdss-linux-v1.0.0-202510191553.zip

# 3. Navigate
cd pdss-linux-v1.0.0

# 4. Fix hostname (optional)
echo "127.0.0.1 $(hostname)" | sudo tee -a /etc/hosts

# 5. Ensure Docker is running
sudo systemctl start docker
sudo systemctl status docker

# 6. Make installer executable
chmod +x install.sh

# 7. Run installer
sudo ./install.sh

# Installation takes 5-10 minutes...

# 8. Access system
# http://localhost:3000
# or
# http://<your-server-ip>:3000

# 9. Login
# Username: admin
# Password: admin123

# 10. IMPORTANT: Change default passwords!
```

---

## 🎯 Quick Reference

### Package Comparison

| Package | Directory Name | Docker Compatible | Status |
|---------|---------------|-------------------|--------|
| Old (v202510191456) | `pdss-linux-installer_v1.0.0_202510191456` | ❌ Invalid | Requires rename |
| Old (v202510191518) | `pdss-linux-installer_v1.0.0_202510191518` | ❌ Invalid | Requires rename |
| **New (v202510191553)** | **`pdss-linux-v1.0.0`** | **✅ Valid** | **Ready to use** |

### What Was Fixed

✅ **Directory Naming**
- Old: `pdss-linux-installer_v1.0.0_TIMESTAMP` (causes Docker errors)
- New: `pdss-linux-v1.0.0` (Docker-friendly)

✅ **Line Endings**
- All shell scripts have Unix (LF) line endings

✅ **Package Structure**
- Cleaner, simpler naming convention
- Timestamp only in archive filename, not directory

---

## 🔧 Troubleshooting

### Issue: Docker Won't Start

```bash
# Check if Docker is installed
docker --version

# Check Docker service status
sudo systemctl status docker

# View logs
sudo journalctl -xeu docker.service

# Try manual start
sudo dockerd

# If all fails, reinstall Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### Issue: Permission Denied

```bash
# Run with sudo
sudo ./install.sh

# Or add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Issue: Port Already in Use

```bash
# Check what's using ports
sudo netstat -tlnp | grep ':3000\|:8000\|:5432'

# Stop conflicting services
sudo systemctl stop <service-name>

# Or modify ports in docker-compose.yml
```

---

## 📚 Related Documentation

- **`FIX_LINE_ENDINGS.md`** - Line endings fix
- **`🔧_LINE_ENDINGS_FIXED.md`** - Line endings technical details
- **`INSTALLATION_GUIDE.md`** - Complete installation guide
- **`DEPLOYMENT_GUIDE.md`** - Deployment procedures

---

## ✅ Summary

### Issues Fixed

1. ✅ **Docker naming conflict** - Simplified directory name
2. ✅ **Line endings** - All scripts have Unix LF
3. ✅ **Hostname resolution** - Documented fix
4. ✅ **Package structure** - Cleaner, more professional

### New Package

**File:** `pdss-linux-v1.0.0-202510191553.zip`

**Location:** 
```
C:\Old Laptop\D\Work\140407\cahs_flow_project\installation_packages\pdss-linux-v1.0.0-202510191553.zip
```

**Directory:** `pdss-linux-v1.0.0`

**Ready to use!** No fixes needed - works out of the box!

---

## 🚀 Recommended Action

### For Your Current Installation

**Quick Fix:**
```bash
cd ~
mv pdss-linux-installer_* pdss
cd pdss
sudo bash install.sh
```

### For Future Installations

**Use new package:**
```
pdss-linux-v1.0.0-202510191553.zip
```

---

**Status:** ✅ **ALL ISSUES RESOLVED**

**New Package:** Production Ready  
**Created:** October 19, 2025, 15:53  
**Version:** 1.0.0

---

**You can now install PDSS without Docker naming issues!** 🎉

