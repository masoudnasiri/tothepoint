# Updated Scripts Guide - Safe Docker Operations

## 🎯 **All Scripts Updated for Data Safety**

Your batch scripts have been updated to use **SAFE** Docker commands that **NEVER** delete your data.

---

## 📋 **Updated Scripts**

### **1. start.bat** - ✅ SAFE START

**What's New:**
- ✅ Checks if containers already running (avoids unnecessary restart)
- ✅ Uses `docker-compose restart` if already running
- ✅ Uses `docker-compose up -d` for first start
- ✅ **NEVER uses `docker-compose down -v`**
- ✅ Shows enhanced info (Advanced Optimization link, role permissions)
- ✅ Auto-opens browser
- ✅ Displays useful commands

**How to Use:**
```powershell
# Just double-click or run:
start.bat

# It will:
# 1. Check Docker is running
# 2. Start services (or restart if already running)
# 3. Show status
# 4. Open browser to http://localhost:3000
# 5. Display login credentials with permission levels
```

**Data Safety:** ✅ **100% SAFE - Data always preserved**

---

### **2. stop.bat** - ✅ SAFE STOP

**What's New:**
- ✅ Asks for confirmation before stopping
- ✅ Shows current container status
- ✅ Uses `docker-compose down` (WITHOUT -v)
- ✅ Confirms data is preserved
- ✅ Shows volume name for reference
- ✅ Warns about dangerous command (down -v)

**How to Use:**
```powershell
# Double-click or run:
stop.bat

# It will:
# 1. Show current status
# 2. Ask for confirmation
# 3. Stop containers (preserves data)
# 4. Confirm data is safe
# 5. Show restart command
```

**Data Safety:** ✅ **100% SAFE - Data always preserved**

---

### **3. check-status.bat** - ✅ ENHANCED

**What's New:**
- ✅ Shows container status
- ✅ Verifies database connection
- ✅ Counts data in all tables
- ✅ Checks NetworkX and OR-Tools installed
- ✅ Verifies all 4 solvers available
- ✅ Shows volume health
- ✅ Displays disk usage

**How to Use:**
```powershell
# Anytime you want to check system:
check-status.bat

# Or use the original (now enhanced):
check-system.bat
```

**Shows:**
```
[1/7] Checking Docker... + Running
[2/7] Checking docker-compose... + Available
[3/7] Checking containers... + All running
[4/7] Checking database... + Connected
[5/7] Checking data... Shows counts for all tables
[6/7] Checking OR-Tools... + NetworkX, OR-Tools ready
[7/7] Checking solvers... + CP-SAT, GLOP, CBC, SCIP
```

---

### **4. backup_database.bat** - ✅ NEW!

**What It Does:**
- ✅ Creates timestamped backup of entire database
- ✅ Saves to `database_backups/` folder
- ✅ Keeps last 10 backups (auto-cleanup)
- ✅ Shows backup file size
- ✅ Displays restore command

**How to Use:**
```powershell
# Create backup:
backup_database.bat

# Creates file like:
# database_backups/backup_20251009_1430.sql
```

**When to Use:**
- Before major changes
- Weekly (recommended)
- Before testing new features
- Before updating dependencies

---

### **5. restore_database.bat** - ✅ NEW!

**What It Does:**
- ✅ Lists all available backups
- ✅ Lets you select which backup to restore
- ✅ Asks for confirmation (safety!)
- ✅ Restores selected backup
- ✅ Restarts backend automatically

**How to Use:**
```powershell
# Restore from backup:
restore_database.bat

# Follow prompts:
# 1. See list of available backups
# 2. Enter filename (or press Enter for latest)
# 3. Confirm restoration
# 4. Wait for restore to complete
```

**When to Use:**
- If data was accidentally lost
- To revert to previous state
- For testing rollback procedures
- Monthly restore test (verify backups work)

---

## 🔄 **Updated Workflow**

### **Daily Routine:**

```powershell
# Morning:
start.bat              # Starts everything, opens browser

# During day:
# → Make code changes, files auto-reload
# → No Docker commands needed!

# Check system:
check-status.bat       # Verify everything running

# Evening (optional):
stop.bat               # Stops containers, preserves data
# OR just leave running!
```

### **Weekly Maintenance:**

```powershell
# Friday:
backup_database.bat    # Create weekly backup

# Check health:
check-status.bat       # Verify system healthy

# View data counts:
# → Already shown in check-status!
```

### **Monthly:**

```powershell
# Test restore procedure:
restore_database.bat   # Practice recovery

# Clean old backups:
# → Automatic! Keeps last 10
```

---

## 🎯 **Script Comparison**

| Script | Old Behavior | New Behavior |
|--------|--------------|--------------|
| **start.bat** | Always `down` then `up --build` | Smart: restart if running, up -d if not |
| **stop.bat** | Just `down` | Confirms, shows status, explains data safety |
| **check-system.bat** | Basic status | 7-point health check + data counts |
| **backup_database.bat** | ❌ Didn't exist | ✅ NEW - Automated backups |
| **restore_database.bat** | ❌ Didn't exist | ✅ NEW - Easy restore |
| **check-status.bat** | ❌ Didn't exist | ✅ NEW - Enhanced status |

---

## ✅ **Safety Features in New Scripts**

### **start.bat Safety:**
```
✅ Checks if already running → Avoids unnecessary rebuild
✅ Uses restart if running → Faster, safer
✅ Uses up -d if not running → No volume deletion
✅ Never uses down -v → Data always safe
✅ Shows data preservation message → User confidence
```

### **stop.bat Safety:**
```
✅ Asks for confirmation → Prevents accidents
✅ Shows current status → User knows what's stopping
✅ Uses down (no -v) → Volumes preserved
✅ Confirms data safe → Peace of mind
✅ Shows dangerous command → Education
```

### **Backup Scripts Safety:**
```
✅ Automated timestamping → Never overwrite
✅ Retention policy → Keeps last 10
✅ Confirmation required → No accidents
✅ File size shown → Verify backup quality
```

---

## 🚀 **Quick Start with New Scripts**

```powershell
# 1. Start system (SAFE - preserves data)
start.bat

# 2. Check everything is healthy
check-status.bat

# 3. Create your first backup
backup_database.bat

# 4. Make some changes, restart safely
stop.bat
start.bat
# → Data still there!

# 5. Verify data preserved
check-status.bat
# → Should show same data counts
```

---

## 📊 **What Each Script Shows**

### **start.bat Output:**
```
========================================
 Procurement DSS - Enhanced OR-Tools
 SAFE Start (Data Preserved)
========================================

+ Docker is running

Starting services (data preserved)...
Waiting for services to initialize...

Service Status:
backend    Up  0.0.0.0:8000->8000/tcp
frontend   Up  0.0.0.0:3000->3000/tcp
postgres   Up  0.0.0.0:5432->5432/tcp

========================================
  Procurement DSS is Running!
========================================

Access Points:
  Frontend:         http://localhost:3000
  Advanced Optim:   http://localhost:3000/optimization-enhanced

Login Credentials:
  Admin:       admin / admin123        (Full Access)
  Finance:     finance1 / finance123   (Full Access)
  PM:          pm1 / pm123             (Revenue Only)
  Procurement: proc1 / proc123         (Payments Only)

Opening browser in 3 seconds...
```

### **check-status.bat Output:**
```
========================================
 Procurement DSS - System Status
========================================

Container Status:
backend    Up  0.0.0.0:8000->8000/tcp
frontend   Up  0.0.0.0:3000->3000/tcp
postgres   Up  0.0.0.0:5432->5432/tcp

========================================
+ Services are RUNNING

Database Status:
Database Connected

Data Verification:
Optimization Runs: 5
Finalized Decisions: 125
Projects: 10
Budget Periods: 12

Volume Status:
+ Database volume EXISTS (data is safe)
```

### **backup_database.bat Output:**
```
====================================
Database Backup Utility
====================================

Creating backup...
+ Backup created: database_backups\backup_20251009_1430.sql
+ Backup size: 524288 bytes

Cleaning old backups (keeping last 10)...

====================================
+ Backup Complete!
====================================

To restore this backup:
  docker-compose exec -T postgres psql -U postgres -d procurement_dss < backup_20251009_1430.sql
```

---

## 🎯 **Migration from Old Scripts**

### **If You Were Using Old Scripts:**

**Old way (potentially dangerous):**
```powershell
# Old start.bat:
docker-compose down       # Stops containers
docker-compose up --build -d

# Problem: Rebuilds every time (slow, unnecessary)
```

**New way (safe and smart):**
```powershell
# New start.bat:
# Already running? → Restart (fast, safe)
# Not running? → Up -d (safe)

# Benefits:
# ✅ Faster restarts
# ✅ Data always preserved
# ✅ Smart detection
```

---

## 📋 **All Available Scripts**

| Script | Purpose | Data Safety | When to Use |
|--------|---------|-------------|-------------|
| **start.bat** | Start services | ✅ SAFE | Every morning |
| **stop.bat** | Stop services | ✅ SAFE | End of day (optional) |
| **check-status.bat** | System health | ✅ SAFE | Anytime |
| **check-system.bat** | Enhanced health | ✅ SAFE | Detailed check |
| **backup_database.bat** | Create backup | ✅ SAFE | Weekly, before changes |
| **restore_database.bat** | Restore backup | ⚠️  Replaces data | If data lost |
| **logs.bat** | View logs | ✅ SAFE | Debugging |
| **reset.bat** | Full reset | ❌ DELETES DATA | Only for testing |
| **install_ortools_enhancements_docker.bat** | Install enhancements | ✅ SAFE | Once |

---

## ⚠️ **Important Reminders**

### **NEVER Run These Manually:**
```powershell
❌ docker-compose down -v
❌ docker volume rm cahs_flow_project_postgres_data
❌ docker volume prune
```

### **ALWAYS Use Safe Scripts:**
```powershell
✅ start.bat         # Starts safely
✅ stop.bat          # Stops safely
✅ backup_database.bat   # Protects data
```

### **When in Doubt:**
```powershell
# Check what will happen:
check-status.bat

# Backup first:
backup_database.bat

# Then proceed:
start.bat
```

---

## 🎉 **Summary**

**Updated Scripts:**
- ✅ `start.bat` - SAFE start with smart detection
- ✅ `stop.bat` - SAFE stop with confirmation
- ✅ `check-system.bat` - Enhanced health check
- ✅ `check-status.bat` - NEW comprehensive status
- ✅ `backup_database.bat` - NEW automated backup
- ✅ `restore_database.bat` - NEW easy restore

**Key Improvements:**
- ✅ Data preservation guaranteed
- ✅ User confirmations added
- ✅ Status information enhanced
- ✅ Backup/restore system created
- ✅ Educational messages included
- ✅ Role permissions displayed

**Your scripts are now:**
- 🛡️ **Safe** - Never accidentally delete data
- 🚀 **Smart** - Detect state and act accordingly
- 📊 **Informative** - Show detailed status
- 🔄 **Reliable** - Consistent behavior
- 📚 **Educational** - Teach best practices

---

## 🚀 **Use Them Now!**

```powershell
# Start your system:
start.bat

# Check health:
check-status.bat

# Create backup:
backup_database.bat

# Stop when needed:
stop.bat
```

**Your data is now protected! 🛡️**

