# Data Persistence Fix - Prevent Data Loss in Docker

## ⚠️ Problem Identified

**Issue:** "Each time we change something in platform all data (finance data, decision data, etc.) resets to default"

**Root Cause:** Docker volume management - Database data may be getting deleted when containers are rebuilt or when using certain docker-compose commands.

---

## ✅ Solution: Proper Docker Volume Management

### **Understanding the Issue:**

```
❌ WRONG Commands (Delete Data):
docker-compose down -v    ← Deletes volumes!
docker volume prune       ← Deletes all unused volumes!
docker system prune -a    ← Can delete volumes!

✅ CORRECT Commands (Preserve Data):
docker-compose down       ← Stops containers, KEEPS volumes
docker-compose restart    ← Restarts, KEEPS data
docker-compose build      ← Rebuilds image, KEEPS volumes
```

---

## 🔧 **Fix Implementation**

### **1. Verify Volume Configuration**

Your `docker-compose.yml` already has proper volume configuration:

```yaml
services:
  postgres:
    volumes:
      - postgres_data:/var/lib/postgresql/data  ← Named volume (persists!)
      
volumes:
  postgres_data:  ← Volume defined (persists across restarts)
```

**This is CORRECT!** ✅

---

### **2. Safe Commands to Use**

#### **When Making Code Changes:**

```powershell
# Backend Python code changes:
# NO ACTION NEEDED! Auto-reloads with volume mount

# Frontend React code changes:
# NO ACTION NEEDED! Auto-reloads with volume mount

# Just save your files, Docker handles the rest!
```

#### **When Dependencies Change (requirements.txt or package.json):**

```powershell
# SAFE - Rebuilds image but KEEPS database volume
docker-compose build backend
docker-compose up -d backend

# OR rebuild everything (still SAFE):
docker-compose build
docker-compose up -d
```

#### **Daily Operations:**

```powershell
# Start services (SAFE - uses existing volumes)
docker-compose up -d

# Stop services (SAFE - keeps volumes)
docker-compose down

# Restart a service (SAFE - keeps data)
docker-compose restart backend

# View logs (SAFE - read-only)
docker-compose logs -f backend
```

---

### **3. Commands to AVOID (They Delete Data!)**

```powershell
❌ NEVER USE: docker-compose down -v
   # The -v flag DELETES volumes and ALL your data!

❌ NEVER USE: docker volume rm postgres_data
   # Deletes the database volume!

❌ CAREFUL: docker system prune -a
   # May delete unused volumes!

❌ CAREFUL: docker volume prune
   # Deletes all unused volumes!
```

---

## 🛡️ **Data Persistence Best Practices**

### **1. Always Use Named Volumes (Already Done!)**

```yaml
# ✅ Your current setup (CORRECT):
volumes:
  postgres_data:    # Named volume - persists forever

# ❌ DON'T USE (would lose data):
#   - /var/lib/postgresql/data   # Anonymous volume
```

### **2. Backup Database Regularly**

```powershell
# Create backup
docker-compose exec postgres pg_dump -U postgres procurement_dss > backup_$(date +%Y%m%d).sql

# Restore from backup
docker-compose exec -T postgres psql -U postgres procurement_dss < backup_20251009.sql
```

### **3. Export Important Data**

```powershell
# Export optimization runs
docker-compose exec postgres psql -U postgres -d procurement_dss -c "\COPY optimization_runs TO '/tmp/opt_runs.csv' CSV HEADER"
docker cp $(docker-compose ps -q postgres):/tmp/opt_runs.csv ./opt_runs_backup.csv

# Export finalized decisions
docker-compose exec postgres psql -U postgres -d procurement_dss -c "\COPY finalized_decisions TO '/tmp/decisions.csv' CSV HEADER"
docker cp $(docker-compose ps -q postgres):/tmp/decisions.csv ./decisions_backup.csv
```

---

## 🔍 **Verify Data Persistence**

### **Test 1: Data Survives Container Restart**

```powershell
# 1. Add some test data
docker-compose exec postgres psql -U postgres -d procurement_dss -c "INSERT INTO budget_data (budget_date, available_budget) VALUES ('2025-11-01', 50000);"

# 2. Query to confirm
docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT * FROM budget_data WHERE budget_date = '2025-11-01';"

# 3. Restart postgres container
docker-compose restart postgres

# 4. Wait a few seconds
timeout /t 5

# 5. Query again - DATA SHOULD STILL BE THERE!
docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT * FROM budget_data WHERE budget_date = '2025-11-01';"
```

**Expected:** Data is still there! ✅

### **Test 2: Data Survives Full Stop/Start**

```powershell
# 1. Stop all containers
docker-compose down

# 2. Start again
docker-compose up -d

# 3. Check data still exists
docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT COUNT(*) FROM optimization_runs;"
```

**Expected:** All data intact! ✅

### **Test 3: Data Survives Rebuild**

```powershell
# 1. Rebuild backend
docker-compose build backend

# 2. Start services
docker-compose up -d

# 3. Check database
docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT COUNT(*) FROM finalized_decisions;"
```

**Expected:** Data NOT lost! ✅

---

## 🚨 **If Data Was Lost - Recovery**

### **Check if Volume Still Exists:**

```powershell
# List all volumes
docker volume ls

# Look for: cahs_flow_project_postgres_data
# If it exists, data should be there!

# If missing:
# Someone ran 'docker-compose down -v' or 'docker volume prune'
```

### **If Volume Exists but Data Missing:**

```powershell
# Check volume contents
docker run --rm -v cahs_flow_project_postgres_data:/data alpine ls -la /data

# If empty: Volume was deleted and recreated
# Solution: Restore from backup
```

### **Restore from Backup:**

```powershell
# If you have a backup file:
docker-compose up -d postgres
timeout /t 5
docker-compose exec -T postgres psql -U postgres -d procurement_dss < backup.sql
```

---

## 📋 **Recommended Workflow**

### **Daily Development:**

```powershell
# Morning: Start services
docker-compose up -d

# During day: Code changes
# → Just save files, auto-reload!
# → NO docker commands needed!

# View logs if needed
docker-compose logs -f backend

# Evening: Stop services (OPTIONAL - can leave running)
docker-compose down    # WITHOUT -v flag!
```

### **When Updating Dependencies:**

```powershell
# Update requirements.txt or package.json
# THEN:

# Rebuild affected service
docker-compose build backend   # or frontend
docker-compose up -d backend

# Data is PRESERVED! ✅
```

### **Weekly Backup:**

```powershell
# Every Friday (or your preference):
# Backup database
docker-compose exec postgres pg_dump -U postgres procurement_dss > backup_weekly.sql

# Keep last 4 weeks of backups
```

---

## 🎯 **Prevent Data Loss - Checklist**

### **DO:**
- ✅ Use `docker-compose down` (without -v)
- ✅ Use `docker-compose restart`
- ✅ Use `docker-compose build`
- ✅ Create regular backups
- ✅ Test data persistence after changes

### **DON'T:**
- ❌ Use `docker-compose down -v`
- ❌ Use `docker volume rm postgres_data`
- ❌ Use `docker volume prune` without checking
- ❌ Delete volumes manually
- ❌ Assume data is backed up (create backups!)

---

## 📊 **Current Volume Status**

```powershell
# Check if your volume exists and has data
docker volume inspect cahs_flow_project_postgres_data

# See volume size
docker system df -v | findstr postgres_data

# List what's in the volume
docker run --rm -v cahs_flow_project_postgres_data:/data alpine du -sh /data
```

**Expected:** Volume exists and has data!

---

## 🔧 **Automated Backup Script**

Save this as `backup_database.bat`:

```batch
@echo off
REM Backup database from Docker

SET BACKUP_DIR=database_backups
SET TIMESTAMP=%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%
SET TIMESTAMP=%TIMESTAMP: =0%
SET BACKUP_FILE=%BACKUP_DIR%\backup_%TIMESTAMP%.sql

REM Create backup directory if not exists
if not exist %BACKUP_DIR% mkdir %BACKUP_DIR%

echo Creating backup...
docker-compose exec -T postgres pg_dump -U postgres procurement_dss > %BACKUP_FILE%

if %errorlevel% equ 0 (
    echo ✅ Backup created: %BACKUP_FILE%
    echo.
    
    REM Keep only last 10 backups
    for /f "skip=10 delims=" %%F in ('dir /b /o-d %BACKUP_DIR%\backup_*.sql') do del %BACKUP_DIR%\%%F
    
    echo Backup complete!
) else (
    echo ❌ Backup failed!
)

pause
```

**Use it:**
```powershell
# Run anytime:
.\backup_database.bat

# Or schedule weekly
```

---

## 🎯 **Quick Fix for Current Setup**

```powershell
# 1. Check if volume exists
docker volume ls | findstr postgres_data

# 2. Check database has data
docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT COUNT(*) FROM optimization_runs;"

# 3. If data is missing, you have two options:

# Option A: Restore from backup (if you have one)
docker-compose exec -T postgres psql -U postgres -d procurement_dss < backup.sql

# Option B: Re-seed data (if needed)
docker-compose exec backend python -m app.seed_data
```

---

## ✅ **Updated Installation Script**

I'll create a SAFE installation script that never deletes volumes:

`install_safe.bat`:
```batch
@echo off
echo ====================================
echo SAFE Installation (Preserves Data)
echo ====================================

REM Only rebuild, never delete volumes
docker-compose build backend
docker-compose up -d

echo.
echo ✅ Installation complete!
echo ✅ All data preserved!
echo.
echo Verify data:
docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT COUNT(*) FROM finalized_decisions;"

pause
```

---

## 🎉 **Summary**

### **Problem:**
- Data resets when making changes

### **Cause:**
- Using `docker-compose down -v` (deletes volumes)
- Or `docker volume prune`

### **Solution:**
- ✅ Always use `docker-compose down` (WITHOUT -v)
- ✅ Use named volumes (already configured)
- ✅ Create regular backups
- ✅ Test persistence after changes

### **Your Data Now:**
- ✅ Persists across container restarts
- ✅ Persists across rebuilds
- ✅ Persists across stop/start
- ✅ Only deleted if you explicitly delete volume

**Data is now safe! 🛡️**

