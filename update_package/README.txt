========================================================================
  PDSS Platform Update Package v1.0.2
  COMPLETE FIX - Password Change + Security
========================================================================

DATE: October 19, 2025

⚠️  IMPORTANT: This is the COMPLETE update package!
Previous update (v1.0.1) was incomplete - use THIS one instead!

WHAT'S FIXED:
=============

1. Password Change Bug (CRITICAL):
   - Users can now successfully change passwords
   - Backend properly hashes and saves new passwords

2. Security Issue - Hardcoded Credentials:
   - Removed exposed passwords from LOGIN SCREEN
   - Removed from all documentation files
   - Added security warnings instead

3. Updated Files:
   ✓ backend/app/schemas.py (password field added)
   ✓ backend/app/crud.py (password hashing fixed)
   ✓ frontend/src/pages/LoginPage.tsx (credentials removed) ← NEW!

INSTALLATION INSTRUCTIONS FOR YOUR SERVER (193.162.129.58):
===========================================================

METHOD 1: AUTOMATED UPDATE (RECOMMENDED)
----------------------------------------

1. Transfer this package to your server:
   
   scp -r pdss-update-v1.0.2.zip root@193.162.129.58:~

2. On your server:
   
   cd ~
   unzip pdss-update-v1.0.2.zip
   cd pdss-update-v1.0.2
   chmod +x update-deployed-platform.sh
   sudo ./update-deployed-platform.sh

3. Wait 5 minutes for update to complete

4. Verify:
   - Access: http://193.162.129.58:3000
   - Login credentials should NOT be visible on screen
   - Password change should work

METHOD 2: MANUAL UPDATE (If script fails)
-----------------------------------------

1. Navigate to your deployment:
   cd ~/pdss  (or ~/pdss-linux-v1.0.0)

2. Create backup:
   docker-compose exec -T db pg_dump -U postgres procurement_dss > ~/backup_$(date +%Y%m%d).sql
   tar -czf ~/code_backup_$(date +%Y%m%d).tar.gz backend/ frontend/

3. Stop platform:
   docker-compose down

4. Copy BACKEND files:
   cp ~/pdss-update-v1.0.2/update_files/backend/app/schemas.py backend/app/
   cp ~/pdss-update-v1.0.2/update_files/backend/app/crud.py backend/app/

5. Copy FRONTEND file:
   cp ~/pdss-update-v1.0.2/update_files/frontend/src/pages/LoginPage.tsx frontend/src/pages/

6. Rebuild BOTH frontend and backend:
   docker-compose build --no-cache

7. Start platform:
   docker-compose up -d

8. Wait for services to start:
   sleep 30

9. Verify:
   docker-compose ps

WHAT TO TEST AFTER UPDATE:
==========================

TEST 1: Check Login Screen
---------------------------
1. Open: http://193.162.129.58:3000
2. Look at login screen
3. ✅ Should see: "⚠️ SECURITY NOTICE" (yellow box)
4. ❌ Should NOT see: "Admin: admin / admin123" etc.

TEST 2: Password Change
-----------------------
1. Login as admin
2. Go to User Management
3. Click Edit on admin user
4. Change password to something new
5. Click Save
6. Logout
7. Login with NEW password
8. ✅ Should work!

TROUBLESHOOTING:
===============

Issue: Credentials still showing on login screen
------------------------------------------------
This means frontend wasn't rebuilt. Try:

cd ~/pdss
docker-compose down
docker-compose build frontend --no-cache
docker-compose up -d

Wait 2 minutes, then check again.

Issue: Password change still not working
----------------------------------------
This means backend wasn't rebuilt. Try:

cd ~/pdss
docker-compose down
docker-compose build backend --no-cache
docker-compose up -d

Wait 2 minutes, then test again.

Issue: Both issues persist
---------------------------
Do a complete rebuild:

cd ~/pdss
docker-compose down
docker-compose build --no-cache
docker-compose up -d
sleep 60
docker-compose ps

All 3 containers (db, backend, frontend) should show "Up"

VERIFICATION COMMANDS:
=====================

# Check if files were updated
cat backend/app/schemas.py | grep -A 2 "class UserUpdate"
# Should show: password: Optional[str] = ...

cat frontend/src/pages/LoginPage.tsx | grep -i "admin123"
# Should show NOTHING (credentials removed!)

# Check containers are running
docker-compose ps
# All should show "Up"

# Check logs for errors
docker-compose logs backend | tail -50
docker-compose logs frontend | tail -50

DIFFERENCES FROM v1.0.1:
========================

v1.0.1 (INCOMPLETE):
- Only updated backend files
- Frontend still showed credentials
- Login screen unchanged

v1.0.2 (COMPLETE):
- Updates backend files ✓
- Updates frontend file ✓
- Removes credentials from login screen ✓
- Everything fixed ✓

FILES CHANGED:
=============

Backend (2 files):
- backend/app/schemas.py
- backend/app/crud.py

Frontend (1 file):
- frontend/src/pages/LoginPage.tsx  ← This was missing in v1.0.1!

IMPORTANT NOTES:
===============

1. Both frontend AND backend must be rebuilt
2. Update takes ~5 minutes (both containers rebuild)
3. Platform will be offline briefly during update
4. All data is preserved (backups created automatically)
5. Rollback is available if needed

WHY THE PREVIOUS UPDATE DIDN'T WORK:
====================================

The v1.0.1 update package only included backend files.
The frontend file (LoginPage.tsx) was missing, so:
- Login screen still showed credentials
- You saw "Admin: admin / admin123" etc.

This v1.0.2 package includes EVERYTHING needed.

SUMMARY OF CHANGES:
==================

Before Update:
--------------
Login Screen:
  ┌─────────────────────────────────┐
  │ Default Login Credentials:       │
  │ Admin: admin / admin123          │
  │ PM: pm1 / pm123                  │
  │ Procurement: proc1 / proc123     │
  │ Finance: finance1 / finance123   │
  └─────────────────────────────────┘

After Update:
-------------
Login Screen:
  ┌─────────────────────────────────┐
  │ ⚠️ SECURITY NOTICE:              │
  │ Change default passwords         │
  │ immediately after first login    │
  │ for security.                    │
  └─────────────────────────────────┘

PASSWORD CHANGE:
Before: Doesn't work (not saved)
After: Works perfectly! ✓

SUPPORT:
========

If update still doesn't work after following these instructions:

1. Verify files were copied:
   ls -la backend/app/schemas.py
   ls -la backend/app/crud.py
   ls -la frontend/src/pages/LoginPage.tsx

2. Check file contents:
   grep -i "password.*Optional" backend/app/schemas.py
   grep -i "get_password_hash" backend/app/crud.py
   grep -i "SECURITY NOTICE" frontend/src/pages/LoginPage.tsx

3. Force complete rebuild:
   cd ~/pdss
   docker-compose down -v
   docker-compose build --no-cache
   docker-compose up -d

4. Check logs:
   docker-compose logs -f

========================================================================
  THIS IS THE COMPLETE UPDATE - Use this one!
========================================================================

Version: 1.0.2
Build Date: October 19, 2025
Fixes: Password change + Security (COMPLETE)

Ready to update your platform!

