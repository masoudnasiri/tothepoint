# ✅ PDSS Platform Update - Version 1.0.1

## 🎯 Summary

**Your PDSS platform has been fixed and is ready to update!**

---

## 🐛 Issues Fixed

### 1. Password Change Not Working (CRITICAL)

**Problem:** When you tried to change user passwords, the changes were not saved.

**Root Cause:** 
- The `UserUpdate` schema was missing the `password` field
- The update function didn't hash passwords properly

**Solution Applied:**
- ✅ Added `password` field to `backend/app/schemas.py`
- ✅ Updated password hashing in `backend/app/crud.py`
- ✅ Password changes now work correctly

### 2. Security Issue: Exposed Default Credentials

**Problem:** Default passwords were visible in documentation and startup scripts.

**Solution Applied:**
- ✅ Removed passwords from `start.sh`
- ✅ Removed passwords from `start.bat`
- ✅ Removed passwords from `README.md`
- ✅ Removed passwords from `SETUP.md`
- ✅ Removed passwords from `WINDOWS_SETUP.md`
- ✅ Added security warnings instead

---

## 📦 What's Included

### Update Package: `pdss-update-v1.0.1.zip`

**Contents:**
```
pdss-update-v1.0.1.zip
├── README.txt                          ← Start here!
├── PLATFORM_UPDATE_GUIDE.md            ← Complete guide
├── QUICK_UPDATE.sh                     ← Quick update for Linux
├── update-deployed-platform.sh         ← Automated Linux updater
├── update-deployed-platform.bat        ← Automated Windows updater
└── update_files/
    └── backend/
        └── app/
            ├── schemas.py              ← Fixed password field
            └── crud.py                 ← Fixed password hashing
```

---

## 🚀 How to Update Your Server (193.162.129.58)

### **Option 1: Quick Update (Recommended)**

**Step 1:** Transfer update package to your server
```bash
# From your Windows machine, transfer to server
scp pdss-update-v1.0.1.zip root@193.162.129.58:~
```

**Step 2:** On your server, extract and run
```bash
# On server (193.162.129.58)
cd ~
unzip pdss-update-v1.0.1.zip
cd pdss-update-v1.0.1
chmod +x QUICK_UPDATE.sh
./QUICK_UPDATE.sh
```

**That's it!** The script handles everything automatically.

---

### **Option 2: Using Update Script Directly**

```bash
# On server
cd ~
unzip pdss-update-v1.0.1.zip
cd pdss-update-v1.0.1
chmod +x update-deployed-platform.sh
sudo ./update-deployed-platform.sh
```

---

### **Option 3: Manual Update**

```bash
# Navigate to your deployment
cd ~/pdss

# Backup
docker-compose exec -T db pg_dump -U postgres procurement_dss > ~/backup.sql

# Stop platform
docker-compose down

# Extract update files
cd ~
unzip pdss-update-v1.0.1.zip

# Copy updated files
cp pdss-update-v1.0.1/update_files/backend/app/schemas.py ~/pdss/backend/app/
cp pdss-update-v1.0.1/update_files/backend/app/crud.py ~/pdss/backend/app/

# Rebuild and restart
cd ~/pdss
docker-compose build --no-cache
docker-compose up -d
```

---

## ✅ After Update - What to Test

### Test Password Change (Most Important!)

1. **Login to platform:**
   ```
   http://193.162.129.58:3000
   Username: admin
   Password: (current password)
   ```

2. **Go to User Management**

3. **Edit admin user**

4. **Change password** to something new

5. **Save changes**

6. **Logout**

7. **Login with new password**

8. **✅ It should work!**

---

## 📊 Update Process

The automated update script will:

1. ✅ **Find your deployment** (`~/pdss` or `~/pdss-linux-v1.0.0`)
2. ✅ **Create backups** (database + code)
3. ✅ **Stop the platform** (brief downtime: 2-5 minutes)
4. ✅ **Apply code updates**
5. ✅ **Rebuild Docker images**
6. ✅ **Restart platform**
7. ✅ **Verify everything is running**

**Expected Downtime:** 2-5 minutes  
**Data Loss:** None (backups created automatically)  
**Rollback:** Available if needed

---

## 🔒 Security Improvements

After this update, your documentation will no longer expose default passwords:

**Before:**
```
Default Login:
  Admin: admin / admin123
  PM: pm1 / pm123
```

**After:**
```
⚠️ IMPORTANT: Change default passwords after first login!
```

This is a **best practice** for production deployments.

---

## 📁 Files Changed

### backend/app/schemas.py

**What changed:**
```python
# OLD - Missing password field
class UserUpdate(BaseModel):
    username: Optional[str] = ...
    role: Optional[str] = ...
    is_active: Optional[bool] = None

# NEW - Password field added
class UserUpdate(BaseModel):
    username: Optional[str] = ...
    password: Optional[str] = Field(None, min_length=6, description="New password")
    role: Optional[str] = ...
    is_active: Optional[bool] = None
```

### backend/app/crud.py

**What changed:**
```python
# OLD - Didn't hash passwords
async def update_user(db, user_id, user_update):
    update_data = user_update.dict(exclude_unset=True)
    # ... directly update without hashing

# NEW - Properly hashes passwords
async def update_user(db, user_id, user_update):
    update_data = user_update.dict(exclude_unset=True)
    
    # Hash password if it's being updated
    if 'password' in update_data and update_data['password']:
        update_data['password_hash'] = get_password_hash(update_data['password'])
        del update_data['password']
    
    # ... update with hashed password
```

---

## 🛡️ Backup & Rollback

### Automatic Backups

The update script automatically creates:
- **Database backup:** `~/pdss_backups/db_backup_TIMESTAMP.sql`
- **Code backup:** `~/pdss_backups/code_backup_TIMESTAMP.tar.gz`

### Rollback if Needed

If something goes wrong:

```bash
cd ~/pdss
docker-compose down

# Restore code
cd ~
tar -xzf pdss_backups/code_backup_TIMESTAMP.tar.gz
cp -r backend frontend ~/pdss/

# Rebuild
cd ~/pdss
docker-compose build --no-cache
docker-compose up -d
```

---

## 📋 Update Checklist

**Before Update:**
- [x] Update package created
- [x] Code fixes tested
- [x] Documentation updated
- [x] Update scripts created
- [ ] Transfer to server
- [ ] Run update

**After Update:**
- [ ] All containers running
- [ ] Test password change
- [ ] Verify no errors in logs
- [ ] Inform users system is updated

---

## 📞 Support Commands

### Check if update worked:

```bash
# Check services are running
docker-compose ps

# Should show all 3 containers "Up"

# Check logs
docker-compose logs -f

# Verify file was updated
cat backend/app/schemas.py | grep -A 3 "class UserUpdate"

# Should show password field
```

### If password change still doesn't work:

```bash
# Rebuild backend specifically
docker-compose build backend --no-cache
docker-compose up -d backend

# Check backend logs
docker-compose logs backend -f
```

---

## 🎯 Quick Reference

**Update Package Location:**
```
C:\Old Laptop\D\Work\140407\cahs_flow_project\pdss-update-v1.0.1.zip
```

**Transfer to Server:**
```bash
scp pdss-update-v1.0.1.zip root@193.162.129.58:~
```

**Run Update:**
```bash
# On server
cd ~
unzip pdss-update-v1.0.1.zip
cd pdss-update-v1.0.1
chmod +x QUICK_UPDATE.sh
./QUICK_UPDATE.sh
```

**Test Password Change:**
```
http://193.162.129.58:3000
→ User Management
→ Edit User
→ Change Password
→ Save
→ Logout
→ Login with new password
→ ✅ Should work!
```

---

## 📚 Documentation

All documentation is included in the update package:

- **README.txt** - Quick start guide
- **PLATFORM_UPDATE_GUIDE.md** - Complete update manual
- **QUICK_UPDATE.sh** - One-command update script

---

## 🎊 Summary

**What You Have:**
- ✅ Fixed password change functionality
- ✅ Improved security (removed exposed passwords)
- ✅ Automated update scripts
- ✅ Complete documentation
- ✅ Backup & rollback procedures
- ✅ Ready-to-deploy update package

**What To Do:**
1. Transfer `pdss-update-v1.0.1.zip` to your server
2. Run the update script
3. Test password change
4. Done!

**Downtime:** ~2-5 minutes  
**Risk:** Very low (backups created automatically)  
**Difficulty:** Easy (automated script)

---

## 🚀 Ready to Update!

Your update package is ready:

**File:** `pdss-update-v1.0.1.zip`  
**Size:** ~50 KB  
**Location:** `C:\Old Laptop\D\Work\140407\cahs_flow_project\`

**Next Step:**
```bash
scp pdss-update-v1.0.1.zip root@193.162.129.58:~
```

**Then on server:**
```bash
cd ~
unzip pdss-update-v1.0.1.zip
cd pdss-update-v1.0.1
./QUICK_UPDATE.sh
```

---

**Update Date:** October 19, 2025  
**Version:** 1.0.1  
**Status:** ✅ Ready for Deployment

**Your platform is ready to be updated!** 🎉

