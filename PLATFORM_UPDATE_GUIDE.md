# 🔄 Platform Update Guide

## Overview

This guide explains how to update your deployed PDSS platform with the latest code changes.

---

## 🐛 What Was Fixed

### Critical Bug Fix: Password Change Not Working

**Issue:** User password changes were not being saved.

**Root Cause:** The `UserUpdate` schema didn't include a password field, and the update function didn't hash passwords.

**Fix Applied:**
1. ✅ Added `password` field to `UserUpdate` schema in `backend/app/schemas.py`
2. ✅ Updated `update_user` function in `backend/app/crud.py` to properly hash passwords
3. ✅ Password changes now work correctly

### Security Improvement: Removed Default Credentials from Documentation

**Change:** Removed exposed default passwords from:
- ✅ `start.sh` - Linux startup script
- ✅ `start.bat` - Windows startup script  
- ✅ `README.md` - Main readme
- ✅ `SETUP.md` - Setup guide
- ✅ `WINDOWS_SETUP.md` - Windows setup guide

Now displays security warnings instead of actual passwords.

---

## 📦 Update Methods

### Method 1: Automated Update (Recommended)

Use the provided update scripts to automatically apply changes.

### Method 2: Manual Update

Manually copy files and rebuild containers.

---

## 🚀 Method 1: Automated Update

### For Linux/Ubuntu Server

**Step 1: Prepare Update Files**

On your development machine, create the update package:

```bash
# Create update directory
mkdir -p update_files/backend/app
mkdir -p update_files/frontend

# Copy updated backend files
cp backend/app/schemas.py update_files/backend/app/
cp backend/app/crud.py update_files/backend/app/

# If you have frontend changes, copy them too
# cp -r frontend/src/* update_files/frontend/src/

# Create archive
tar -czf pdss-update-$(date +%Y%m%d).tar.gz update_files/

# Also copy the update script
cp update-deployed-platform.sh pdss-update-script.sh
chmod +x pdss-update-script.sh
```

**Step 2: Transfer to Server**

```bash
# Transfer files to server (from your development machine)
scp pdss-update-$(date +%Y%m%d).tar.gz root@193.162.129.58:~
scp pdss-update-script.sh root@193.162.129.58:~
```

**Step 3: Run Update on Server**

```bash
# On your server
cd ~

# Extract update files
tar -xzf pdss-update-*.tar.gz

# Make update script executable
chmod +x pdss-update-script.sh

# Run update
sudo ./pdss-update-script.sh
```

The script will:
- ✅ Automatically find your deployment directory
- ✅ Create backups (database + code)
- ✅ Stop the platform
- ✅ Apply updates
- ✅ Rebuild Docker images
- ✅ Restart the platform
- ✅ Verify everything is running

**Expected Output:**
```
============================================================================
  PDSS Platform Update Script
============================================================================

[OK] Found deployment at: /root/pdss
[OK] Platform is running
[OK] Update files found
[OK] Backup created
[OK] Docker is running
[OK] Available space: 50G

... (update process) ...

============================================================================
  UPDATE COMPLETE!
============================================================================

✓ Platform updated successfully
✓ Backup saved to: ~/pdss_backups
✓ All services running

Access your platform:
  URL: http://193.162.129.58:3000
```

---

### For Windows Server

**Step 1: Prepare Update Files**

On your development machine:

```cmd
REM Create update directory
mkdir update_files\backend\app
mkdir update_files\frontend

REM Copy updated backend files
copy backend\app\schemas.py update_files\backend\app\
copy backend\app\crud.py update_files\backend\app\

REM Create ZIP
powershell Compress-Archive -Path update_files -DestinationPath pdss-update.zip

REM Copy update script
copy update-deployed-platform.bat pdss-update-script.bat
```

**Step 2: Transfer to Server**

Transfer these files to your server:
- `pdss-update.zip`
- `pdss-update-script.bat`

**Step 3: Run Update on Server**

```cmd
REM Extract update files
powershell Expand-Archive pdss-update.zip

REM Run update script as Administrator
Right-click pdss-update-script.bat
Select "Run as Administrator"
```

---

## 🔧 Method 2: Manual Update

### For Linux

```bash
# 1. Navigate to deployment directory
cd ~/pdss  # or ~/pdss-linux-v1.0.0

# 2. Create backup
mkdir -p ~/pdss_backups
docker-compose exec -T db pg_dump -U postgres procurement_dss > ~/pdss_backups/backup_$(date +%Y%m%d).sql
tar -czf ~/pdss_backups/code_backup_$(date +%Y%m%d).tar.gz backend/ frontend/

# 3. Stop platform
docker-compose down

# 4. Update backend files
# Copy your updated files to:
# - backend/app/schemas.py
# - backend/app/crud.py

# For example, if you have update files in ~/update_files:
cp ~/update_files/backend/app/schemas.py backend/app/
cp ~/update_files/backend/app/crud.py backend/app/

# 5. Rebuild Docker images
docker-compose build --no-cache

# 6. Start platform
docker-compose up -d

# 7. Verify
docker-compose ps
docker-compose logs -f
```

### For Windows

```cmd
REM 1. Navigate to deployment directory
cd %USERPROFILE%\pdss

REM 2. Create backup
mkdir %USERPROFILE%\pdss_backups
docker-compose exec -T db pg_dump -U postgres procurement_dss > %USERPROFILE%\pdss_backups\backup.sql
powershell Compress-Archive -Path backend,frontend -DestinationPath %USERPROFILE%\pdss_backups\code_backup.zip

REM 3. Stop platform
docker-compose down

REM 4. Update backend files
REM Copy your updated files to:
REM - backend\app\schemas.py
REM - backend\app\crud.py

copy path\to\updated\schemas.py backend\app\
copy path\to\updated\crud.py backend\app\

REM 5. Rebuild Docker images
docker-compose build --no-cache

REM 6. Start platform
docker-compose up -d

REM 7. Verify
docker-compose ps
docker-compose logs -f
```

---

## ✅ Verify Update

### Check Services are Running

```bash
docker-compose ps

# Should show:
# NAME                STATUS
# pdss-db-1          Up
# pdss-backend-1     Up  
# pdss-frontend-1    Up
```

### Test Password Change

1. Login as admin
2. Go to User Management
3. Edit admin user
4. Change password
5. Click Save
6. Logout
7. Login with new password
8. ✅ Should work!

### Check Logs

```bash
# View all logs
docker-compose logs -f

# View backend logs only
docker-compose logs backend -f

# Check for errors
docker-compose logs | grep -i error
```

---

## 🔄 Rollback (If Needed)

If something goes wrong, you can rollback to the previous version.

### Linux Rollback

```bash
cd ~/pdss

# Stop current version
docker-compose down

# Restore code from backup
cd ~
tar -xzf pdss_backups/code_backup_YYYYMMDD_HHMMSS.tar.gz
cp -r backend frontend ~/pdss/

# Rebuild and restart
cd ~/pdss
docker-compose build --no-cache
docker-compose up -d

# Restore database if needed
cat ~/pdss_backups/db_backup_YYYYMMDD_HHMMSS.sql | docker-compose exec -T db psql -U postgres procurement_dss
```

### Windows Rollback

```cmd
cd %USERPROFILE%\pdss

REM Stop current version
docker-compose down

REM Restore code from backup
powershell Expand-Archive %USERPROFILE%\pdss_backups\code_backup_YYYYMMDD.zip -DestinationPath .

REM Rebuild and restart
docker-compose build --no-cache
docker-compose up -d

REM Restore database if needed
type %USERPROFILE%\pdss_backups\db_backup_YYYYMMDD.sql | docker-compose exec -T db psql -U postgres procurement_dss
```

---

## 📋 Update Checklist

Before updating:
- [ ] Backup database
- [ ] Backup current code
- [ ] Note current version/state
- [ ] Inform users of maintenance window

During update:
- [ ] Stop platform
- [ ] Apply code changes
- [ ] Rebuild Docker images
- [ ] Start platform
- [ ] Check logs for errors

After update:
- [ ] Verify all services running
- [ ] Test password change functionality
- [ ] Test critical features
- [ ] Inform users platform is back online

---

## 📝 What Changed

### Files Updated

1. **`backend/app/schemas.py`**
   - Added `password` field to `UserUpdate` schema
   - Allows password changes via API

2. **`backend/app/crud.py`**
   - Updated `update_user` function
   - Now properly hashes passwords before saving
   - Converts `password` to `password_hash`

3. **Documentation Files** (start.sh, start.bat, README.md, etc.)
   - Removed exposed default passwords
   - Added security warnings
   - Improved security posture

### New Files Added

1. **`update-deployed-platform.sh`** - Linux update script
2. **`update-deployed-platform.bat`** - Windows update script
3. **`PLATFORM_UPDATE_GUIDE.md`** - This guide

---

## 🆘 Troubleshooting

### Update Script Can't Find Deployment

**Issue:** Script says "Could not find PDSS deployment directory"

**Solution:**
```bash
# Manually specify directory when prompted
# Or edit the script and set DEPLOY_DIR manually
```

### Containers Won't Start After Update

**Issue:** `docker-compose ps` shows "Exit" status

**Solution:**
```bash
# Check logs
docker-compose logs

# Look for specific errors
docker-compose logs backend
docker-compose logs frontend

# Try rebuilding
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Password Change Still Not Working

**Issue:** Password change doesn't save

**Solution:**
```bash
# Verify files were actually updated
cat backend/app/schemas.py | grep -A 5 "class UserUpdate"

# Should show password field

# Check backend logs
docker-compose logs backend | grep -i password

# Rebuild backend specifically
docker-compose build backend --no-cache
docker-compose up -d backend
```

### Database Backup Failed

**Issue:** Backup command gives error

**Solution:**
```bash
# Make sure platform is running
docker-compose up -d

# Try backup again
docker-compose exec -T db pg_dump -U postgres procurement_dss > backup.sql

# Check if database is accessible
docker-compose exec db psql -U postgres -c "SELECT 1"
```

---

## 🎯 Quick Update Commands

**For most users, just run these:**

### Linux
```bash
# Transfer update files to server
scp -r update_files update-deployed-platform.sh root@193.162.129.58:~

# On server
chmod +x update-deployed-platform.sh
sudo ./update-deployed-platform.sh
```

### Windows
```cmd
REM Transfer files to server, then:
Right-click update-deployed-platform.bat
Run as Administrator
```

---

## 📞 Support

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Verify files were updated: `cat backend/app/schemas.py`
3. Try rebuilding: `docker-compose build --no-cache`
4. Review this guide's troubleshooting section
5. Rollback if necessary (see Rollback section)

---

**Update Date:** October 19, 2025  
**Version:** 1.0.1  
**Status:** ✅ Ready for deployment

---

**Your platform can now be updated easily and safely!** 🚀

