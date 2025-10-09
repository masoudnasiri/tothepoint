# 🚀 RUN THIS NOW - Complete Setup Commands

## 🐳 **YOUR SYSTEM RUNS IN DOCKER - USE DOCKER COMMANDS!**

## ⏱️ Total Time: 10 Minutes

---

## 🐳 Step 1: Install in Docker (3 minutes)

**Since your platform runs in Docker, use the Docker installer:**

```powershell
# Navigate to project root
cd "C:\Old Laptop\D\Work\140407\cahs_flow_project"

# Run Docker installer (rebuilds backend container)
.\install_ortools_enhancements_docker.bat
```

**Alternative: Manual Docker Installation**

```powershell
# Navigate to project root
cd "C:\Old Laptop\D\Work\140407\cahs_flow_project"

# Stop containers
docker-compose down

# Rebuild backend (installs networkx from requirements.txt)
docker-compose build backend

# Start all services
docker-compose up -d

# Wait for services to start
timeout /t 10
```

**Expected Output:**
```
==================================
OR-Tools Enhancement Installation
==================================

+ Project root directory detected

Installing Python dependencies...
+ networkx installed successfully

Verifying installation...
+ NetworkX version: 3.2.1
+ OR-Tools verified

==================================
+ Installation Complete!
==================================
```

---

## ✅ Step 2: Test in Docker (2 minutes)

**Run tests inside the backend Docker container:**

```powershell
# Run automated tests in Docker
docker-compose exec backend python test_enhanced_optimization.py
```

**Expected Output:**
```
🧪 Testing Enhanced Optimization Installation

==============================================================
1️⃣ Testing imports...
   ✅ All imports successful
2️⃣ Testing solver availability...
   ✅ CP-SAT available
   ✅ GLOP available
   ✅ CBC available
   ⚠️  SCIP not available (optional)
3️⃣ Testing database connectivity...
   ✅ Database connected
      - Projects: 5
      - Items: 25
      - Procurement Options: 50
      - Budget Periods: 12
4️⃣ Testing optimizer instantiation...
   ✅ Optimizer created successfully
   ✅ Data loaded: 25 items
   ✅ Dependency graph built: 25 nodes
5️⃣ Running quick optimization test...
   ⏳ Running optimization (30s limit)...
   ✅ Optimization completed
      - Status: OPTIMAL
      - Execution time: 18.45s
      - Total cost: $125,450.00
      - Items optimized: 25
      - Proposals generated: 1

==============================================================
📊 TEST SUMMARY
==============================================================
✅ Solvers available: 3/4
   ✅ CP-SAT
   ✅ GLOP
   ✅ CBC
   ⚠️  SCIP

🎉 Installation successful! Core solvers ready.
```

**If all tests pass:** ✅ Continue to Step 3  
**If tests fail:** See [Troubleshooting](#troubleshooting) section

---

## ✅ Step 3: Verify Docker Services (1 minute)

**Your Docker containers should already be running from Step 1:**

```powershell
# Check container status
docker-compose ps
```

**Expected Output:**
```
NAME                    STATUS              PORTS
backend                 running             0.0.0.0:8000->8000/tcp
frontend                running             0.0.0.0:3000->3000/tcp
postgres                running             0.0.0.0:5432->5432/tcp
```

**If not all running:**
```powershell
docker-compose up -d
```

**Optional - View logs:**
```powershell
# Backend logs (see optimization progress)
docker-compose logs -f backend

# All logs
docker-compose logs -f
```

**Open browser to:** `http://localhost:3000`

---

## ✅ Step 4: Test Complete Flow (10 minutes)

### 4.1: Navigate & Login (30 seconds)
```
1. Browser opens to: http://localhost:3000
2. You're redirected to: http://localhost:3000/login
3. Login:
   Username: admin
   Password: [your password]
4. You see dashboard
```

### 4.2: Access Advanced Optimization (30 seconds)
```
1. In sidebar, click: "Advanced Optimization" (🧠 icon)
2. URL changes to: /optimization-enhanced
3. You see:
   - 4 solver cards (CP_SAT, GLOP, SCIP, CBC)
   - "Run Optimization" button
```

### 4.3: Run Your First Optimization (3 minutes)
```
1. Click "Run Optimization" button
2. In dialog, configure:
   ┌────────────────────────────────────┐
   │ Solver Type: CP_SAT               │
   │ Maximum Time Slots: 12            │
   │ Time Limit: 120 seconds ← Change! │
   │ ☑ Generate Multiple Proposals     │
   │ Strategies: (leave empty)         │
   └────────────────────────────────────┘
3. Click "Run Optimization"
4. Wait 2-3 minutes (progress bar shows)
5. Success! ✅
```

### 4.4: Review Proposals (2 minutes)
```
You should see 5 tabs:
┌────────────────────────────────────────────────┐
│ [💰 Lowest Cost]  [🎯 Priority]  [⚡ Fast]    │
│ [📊 Smooth Flow]  [⚖️ Balanced]              │
└────────────────────────────────────────────────┘

Click each tab to compare:
- Total costs
- Decisions tables
- Delivery timelines

Select "Balanced Strategy" for this test
```

### 4.5: Test Edit Feature (1 minute)
```
1. Find any decision row in the table
2. Click ✏️ (Edit icon)
3. In dialog:
   - Change quantity to different value
   - Click "Save Changes"
4. Row now shows "EDITED" badge 🟧
5. See "Has local changes" chip at top
```

### 4.6: Test Add Feature (1 minute)
```
1. Click "Add Item" button (top right)
2. Click "Continue" in dialog
3. In edit dialog:
   - Enter Item Code: TEST-ITEM
   - Enter Item Name: Test Item
   - Select a procurement option
   - Set quantity: 10
   - Set dates
   - Click "Add Item"
4. New row appears with "NEW" badge 🟩
```

### 4.7: Test Remove Feature (30 seconds)
```
1. Click 🗑️ (Delete icon) on any row
2. Click "OK" in confirmation
3. Row disappears
4. "Has local changes" chip updates
```

### 4.8: Save Proposal (1 minute)
```
1. Click "Save Proposal as Decisions" (green button, bottom)
2. Wait ~5 seconds
3. Success message appears:
   "✅ Proposal 'Balanced Strategy' saved with X decisions!"
4. New button appears: "Finalize & Lock Decisions"
```

**Verify in Database:**
```powershell
# New terminal
cd backend
python -c "from app.database import async_session_maker; from app.models import FinalizedDecision; import asyncio; asyncio.run((lambda: async_session_maker()).__call__().__aenter__())"

# Or query directly:
# SELECT COUNT(*) FROM finalized_decisions WHERE status = 'PROPOSED';
```

### 4.9: Finalize Decisions (1 minute)
```
1. Click "Finalize & Lock Decisions" (blue button)
2. Read the confirmation dialog
3. Click "Finalize & Lock"
4. Success message:
   "✅ Successfully locked X decisions!"
5. Button disappears (already finalized)
```

**Verify in Database:**
```sql
SELECT COUNT(*) FROM finalized_decisions WHERE status = 'LOCKED';
-- Should show your decision count
```

### 4.10: Test Previous Runs (30 seconds)
```
1. Click "Previous Runs (1)" button (top)
2. Dialog shows table with your run
3. See:
   - Run timestamp
   - Solver used (CP_SAT)
   - Status (SUCCESS)
   - Items count
   - Total cost
   - Proposals count (5)
4. Click "Close"
```

### 4.11: Verify Exclusion (2 minutes)
```
1. Click "Run Optimization" again
2. Configure and run (same settings)
3. Check backend terminal logs:
   
   Look for:
   "Excluded X locked items from optimization"
   
4. New optimization only processes unlocked items ✅
```

---

## 🎯 What You Just Did

✅ **Installed** NetworkX and verified all solvers  
✅ **Ran** automated tests (all passed)  
✅ **Started** backend and frontend servers  
✅ **Executed** first optimization with CP_SAT  
✅ **Reviewed** all 5 proposals  
✅ **Edited** a decision (local state)  
✅ **Added** a new item (local state)  
✅ **Removed** a decision (local state)  
✅ **Saved** proposal → Created finalized_decisions ✅  
✅ **Finalized** → Locked decisions ✅  
✅ **Verified** previous runs viewable ✅  
✅ **Tested** exclusion logic (locked items not re-optimized) ✅  

**Complete end-to-end flow tested! 🎉**

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: networkx"
```powershell
Solution:
cd backend
pip install networkx==3.2.1
```

### Issue: Test fails at database connection
```powershell
Solution:
1. Check if backend database is running
2. Verify DATABASE_URL in .env or config
3. Try: docker-compose up -d db
```

### Issue: "No optimization runs found"
```powershell
Solution:
This is normal if first time. Run an optimization first.
```

### Issue: Backend won't start
```powershell
Solution:
1. Check port 8000 not in use
2. Activate venv if using one
3. Check requirements all installed: pip install -r requirements.txt
```

### Issue: Frontend shows blank page
```powershell
Solution:
cd frontend
Remove-Item -Recurse -Force node_modules\.cache
npm start
```

---

## 📖 What to Read Next

### Must Read Today:
1. **START_HERE.md** (10 min) - Overview
2. **OR_TOOLS_QUICK_REFERENCE.md** (10 min) - Quick decisions
3. **OPTIMIZATION_FINALIZATION_FLOW.md** (15 min) - Complete flow

### Read This Week:
4. **SOLVER_DEEP_DIVE.md** (1 hour) - Understand solvers
5. **CUSTOM_STRATEGIES_GUIDE.md** (1 hour) - Custom strategies
6. **FIRST_OPTIMIZATION_RUN_GUIDE.md** (30 min) - Detailed walkthrough

---

## 🎯 Quick Commands Reference

### Check if everything is installed:
```powershell
python -c "import networkx, ortools; print('✅ All good!')"
```

### View documentation:
```powershell
type START_HERE.md | more
```

### Start servers (save these commands):
```powershell
# Backend (Terminal 1)
cd "C:\Old Laptop\D\Work\140407\cahs_flow_project\backend"
uvicorn app.main:app --reload

# Frontend (Terminal 2)
cd "C:\Old Laptop\D\Work\140407\cahs_flow_project\frontend"
npm start
```

### Quick database check:
```sql
-- How many optimization runs?
SELECT COUNT(*) FROM optimization_runs;

-- How many finalized decisions?
SELECT status, COUNT(*) FROM finalized_decisions GROUP BY status;

-- Latest run:
SELECT * FROM optimization_runs ORDER BY run_timestamp DESC LIMIT 1;
```

---

## ✅ Success Confirmation

**You're successful if you can:**

- [x] Run `install_ortools_enhancements.bat` without errors
- [x] Run `test_enhanced_optimization.py` and all tests pass
- [x] Start both servers
- [x] Access `/optimization-enhanced` page
- [x] See 4 solver cards
- [x] Run optimization and get 5 proposals
- [x] Edit/Add/Remove items
- [x] Save proposal successfully
- [x] See "Finalize & Lock" button
- [x] Finalize decisions
- [x] View previous runs
- [x] Verify database has data

---

## 🎉 You're Done!

**If all steps completed successfully:**

✅ Your system is fully operational!  
✅ You can now use advanced optimization in production!  
✅ All features are working!  
✅ Data persistence is active!  

**Next:** Start using it for real procurement decisions! 🚀

---

## 📞 Need Help?

**Quick Issues:**
- See troubleshooting section above

**Documentation:**
- `START_HERE.md` - Best starting point
- `OR_TOOLS_QUICK_REFERENCE.md` - Quick answers

**Technical Details:**
- `OPTIMIZATION_FINALIZATION_FLOW.md` - Complete flow
- `VISUAL_WORKFLOW_DIAGRAM.md` - Diagrams
- `COMPLETE_ENHANCEMENT_SUMMARY.md` - Full summary

---

**🎊 Congratulations on completing the setup! Your OR-Tools enhanced procurement system is ready! 🎊**

