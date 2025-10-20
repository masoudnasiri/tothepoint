# Safe Docker Commands - Never Lose Data Again!

## ✅ **Commands That PRESERVE Your Data**

### **Daily Operations (100% SAFE)**

```powershell
# Start services
docker-compose up -d
# ✅ SAFE - Uses existing volumes

# Stop services
docker-compose down
# ✅ SAFE - Stops containers but KEEPS volumes

# Restart a service
docker-compose restart backend
docker-compose restart frontend
# ✅ SAFE - Just restarts, data unchanged

# View logs
docker-compose logs -f backend
# ✅ SAFE - Read-only

# Check status
docker-compose ps
# ✅ SAFE - Read-only

# Execute commands in container
docker-compose exec backend python test.py
# ✅ SAFE - Runs command, doesn't affect volumes
```

---

### **Code Changes (100% SAFE)**

```powershell
# Backend Python code changes:
# Just save the file - auto-reloads!
# ✅ NO docker command needed
# ✅ Data preserved automatically

# Frontend React code changes:
# Just save the file - auto-reloads!
# ✅ NO docker command needed  
# ✅ Data preserved automatically

# Backend configuration changes (app/config.py):
docker-compose restart backend
# ✅ SAFE - Restarts process, keeps data
```

---

### **Dependency Changes (SAFE if done correctly)**

```powershell
# After changing requirements.txt:
docker-compose build backend
docker-compose up -d backend
# ✅ SAFE - Rebuilds image, KEEPS postgres_data volume

# After changing package.json:
docker-compose build frontend
docker-compose up -d frontend
# ✅ SAFE - Rebuilds image, KEEPS postgres_data volume

# Rebuild everything:
docker-compose build
docker-compose up -d
# ✅ SAFE - All volumes preserved
```

---

## ❌ **Commands That DELETE Your Data**

### **NEVER Use These:**

```powershell
❌ docker-compose down -v
   # The -v flag DELETES ALL VOLUMES including your database!
   # USE: docker-compose down (WITHOUT -v)

❌ docker volume rm cahs_flow_project_postgres_data
   # Directly deletes your database volume!

❌ docker volume prune
   # Deletes ALL unused volumes (may include yours if containers stopped)

❌ docker system prune -a
   # Can delete volumes if used with wrong flags

❌ docker-compose rm -v
   # The -v deletes volumes
```

---

## 🛡️ **Your Safe Installation Commands**

### **Option 1: Update Code (Most Common)**

```powershell
# When you change Python or React code:
# Just save the file!
# Docker auto-reloads via volume mounts
# ✅ Data preserved
```

### **Option 2: Update Dependencies**

```powershell
# When requirements.txt or package.json changes:
docker-compose build backend   # Rebuilds with new dependencies
docker-compose up -d backend   # Starts updated container
# ✅ Data preserved in postgres_data volume
```

### **Option 3: Full Reinstall (Preserving Data)**

```powershell
# Completely rebuild everything but KEEP data:
docker-compose down           # Stop containers (WITHOUT -v!)
docker-compose build --no-cache  # Clean rebuild
docker-compose up -d          # Start fresh containers
# ✅ postgres_data volume untouched, all data preserved!
```

---

## 📦 **Volume Architecture**

```
Your Docker Setup:

┌────────────────────────────────────────┐
│ Docker Container: postgres             │
│ ├─ Runs PostgreSQL                    │
│ ├─ Data Location: /var/lib/postgresql/data
│ │                                      │
│ └─ Mounted Volume: postgres_data ─────┼──┐
└────────────────────────────────────────┘  │
                                            │
                                            ▼
┌────────────────────────────────────────────────┐
│ Docker Volume: cahs_flow_project_postgres_data │
│ ├─ Type: Named volume                         │
│ ├─ Persists independently of containers        │
│ ├─ NOT deleted when container stops           │
│ ├─ NOT deleted with 'docker-compose down'     │
│ ├─ ONLY deleted with explicit volume command  │
│ │                                              │
│ └─ Contains:                                   │
│    ├─ optimization_runs                        │
│    ├─ optimization_results                     │
│    ├─ finalized_decisions                      │
│    ├─ cashflow_events                          │
│    ├─ projects                                 │
│    ├─ project_items                            │
│    ├─ procurement_options                      │
│    └─ budget_data                              │
└────────────────────────────────────────────────┘

When you:
  docker-compose down        → Container stops, volume REMAINS
  docker-compose build       → New image built, volume REMAINS
  docker-compose up -d       → New container, SAME volume attached
  
Result: DATA PERSISTS! ✅
```

---

## 🎯 **Your Updated Workflow**

### **Installation (First Time):**

```powershell
# Use the SAFE installer:
.\install_ortools_enhancements_docker.bat

# This script uses safe commands:
# - docker-compose down (no -v)
# - docker-compose build
# - docker-compose up -d
# ✅ Data preserved if you're reinstalling
```

### **Daily Use:**

```powershell
# Start work:
docker-compose up -d

# Make code changes:
# → Save files, auto-reload

# View logs:
docker-compose logs -f backend

# End of day:
docker-compose down   # ← NO -v flag!
# OR just leave running
```

### **Weekly Maintenance:**

```powershell
# Friday backup:
.\backup_database.bat

# Check volume health:
docker volume inspect cahs_flow_project_postgres_data

# Check data exists:
docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT COUNT(*) FROM optimization_runs;"
```

---

## 🚨 **Emergency: Data Was Lost**

### **Step 1: Check if Volume Exists**

```powershell
docker volume ls | findstr postgres_data
```

**If found:** Data might still be there, just reconnect

**If not found:** Volume was deleted, restore from backup

### **Step 2: Verify Container Connection**

```powershell
# Check volume mount in container
docker-compose exec postgres df -h | findstr postgresql
```

### **Step 3: Restore from Backup**

```powershell
# Use restore script:
.\restore_database.bat

# Follow prompts to select backup file
```

### **Step 4: Prevent Future Loss**

```powershell
# Add this to your routine:
# 1. Daily: Use safe commands only
# 2. Weekly: Run backup_database.bat
# 3. Monthly: Test restore procedure
```

---

## ✅ **Checklist for Data Safety**

**Setup:**
- [x] Named volume configured in docker-compose.yml
- [x] Volume is `postgres_data` (persists)
- [x] Backup scripts created

**Daily Practice:**
- [ ] Use `docker-compose down` (never with -v)
- [ ] Code changes: just save files
- [ ] Dependency changes: build then up -d
- [ ] Never run `docker volume prune`

**Weekly:**
- [ ] Run `backup_database.bat`
- [ ] Verify backups created
- [ ] Test one backup restore (monthly)

---

## 🎉 **Your Data is Now Protected!**

✅ **Named volumes** - Data persists independently  
✅ **Safe commands** - Never accidentally delete  
✅ **Backup scripts** - Regular backups automated  
✅ **Restore procedure** - Quick recovery if needed  
✅ **Best practices** - Documented and clear  

**You will never lose data again! 🛡️**

