# 📋 Wipe Calculated Data - Complete Guide

## 🎯 **YOUR REQUEST**

**You Said:**
> "please wipe the calculated data contain optimization results, final decision and cash flow and just let the project data, procurement and finance data be there"

**Status:** ✅ **SCRIPT READY TO USE!**

---

## 📊 **What Gets Wiped vs What Stays**

### **❌ DELETED (Calculated/Results Data):**
```
1. Optimization Runs
   - All optimization_runs records
   - All historical optimization metadata

2. Optimization Results
   - All optimization_results records
   - Individual item selection results

3. Finalized Decisions
   - All finalized_decisions records
   - PROPOSED, LOCKED, and REVERTED decisions

4. Cashflow Events
   - All cashflow_events records
   - Both INFLOW and OUTFLOW events
   - Both FORECAST and ACTUAL events
```

### **✅ KEPT (Base Input Data):**
```
1. Users
   - All user accounts
   - Admin, Finance, PM, Procurement users

2. Projects
   - All projects
   - Project phases
   - Project assignments

3. Project Items
   - All project items
   - Delivery options
   - Item configurations

4. Procurement Options
   - All procurement options
   - Supplier information
   - Payment terms

5. Budget Data
   - All budget records
   - Monthly budget allocations

6. Decision Factor Weights
   - Weight configurations
   - Optimization parameters
```

---

## 🎯 **When to Use This**

### **Use Cases:**

**1. Fresh Start with Same Setup**
```
Scenario: Completed Phase 1, want to optimize Phase 2
         Keep all projects/procurement options
         Delete old results to start fresh

Action: Run wipe script
Result: Can run new optimizations without old data interfering
```

**2. Testing Different Strategies**
```
Scenario: Want to test different optimization strategies
         Keep base data (projects, options, budgets)
         Clear previous results

Action: Run wipe script
Result: Clean slate for new optimization tests
```

**3. Fixing Mistakes**
```
Scenario: Made wrong decisions, want to redo
         Keep project setup
         Clear all decisions and cashflow

Action: Run wipe script
Result: Start decision-making process from scratch
```

**4. New Budget Period**
```
Scenario: New fiscal quarter/month
         Same projects and options
         Clear old financial events

Action: Run wipe script + Update budgets
Result: Fresh financial tracking
```

---

## 🚀 **How to Use**

### **Quick Start:**

```powershell
# Run the wipe script
.\wipe_calculated_data.bat
```

**It will ask for confirmation TWICE:**

```
Step 1: Type 'WIPE RESULTS' (case-sensitive)
Step 2: Type 'YES' to proceed
```

**Then:**
- ✅ Deletes all calculated data
- ✅ Shows count of deleted records
- ✅ Confirms what was kept

---

## 📊 **What Happens - Step by Step**

### **1. Confirmation:**
```
You run: .\wipe_calculated_data.bat

Prompt 1: "Type 'WIPE RESULTS' to confirm"
You type: WIPE RESULTS

Prompt 2: "Type 'YES' to proceed"
You type: YES
```

### **2. Deletion Process:**
```
Script connects to database...

Deleting cashflow_events...
✅ Deleted 150 rows from Cashflow Events

Deleting finalized_decisions...
✅ Deleted 45 rows from Finalized Decisions

Deleting optimization_results...
✅ Deleted 45 rows from Optimization Results

Deleting optimization_runs...
✅ Deleted 5 rows from Optimization Runs

✅ Successfully wiped 245 calculated records!
```

### **3. Verification:**
```
DELETED:
  - All optimization runs and results
  - All finalized decisions
  - All cashflow events

KEPT (Unchanged):
  - Users
  - Projects, Project Items, Delivery Options
  - Procurement Options
  - Budget Data
  - Decision Factor Weights

You can now run fresh optimizations!
```

---

## 🧪 **How to Verify**

### **Before Running Wipe:**

```powershell
# Check counts
docker-compose exec postgres psql -U postgres -d procurement_dss

# Run these queries:
SELECT COUNT(*) FROM optimization_runs;
SELECT COUNT(*) FROM finalized_decisions;
SELECT COUNT(*) FROM cashflow_events;
SELECT COUNT(*) FROM projects;
SELECT COUNT(*) FROM procurement_options;
SELECT COUNT(*) FROM budget_data;
```

**Example Output:**
```
optimization_runs:      5
finalized_decisions:   45
cashflow_events:      150
projects:              10  ← Should stay
procurement_options:   75  ← Should stay
budget_data:           12  ← Should stay
```

### **After Running Wipe:**

Run same queries:

**Expected Result:**
```
optimization_runs:      0  ← DELETED ✅
finalized_decisions:    0  ← DELETED ✅
cashflow_events:        0  ← DELETED ✅
projects:              10  ← KEPT ✅
procurement_options:   75  ← KEPT ✅
budget_data:           12  ← KEPT ✅
```

---

## 🎨 **Dashboard After Wipe**

### **What You'll See:**

**Dashboard Page:**
```
Total Budget: $500,000 ✅ (Kept)
Total Inflow:  $0      ✅ (Events deleted)
Total Outflow: $0      ✅ (Events deleted)
Net Position:  $500,000 ✅ (Correct)
```

**Finalized Decisions Page:**
```
No finalized decisions found ✅ (All deleted)
```

**Optimization Page:**
```
No previous runs ✅ (History deleted)
```

**Projects Page:**
```
All your projects still there ✅ (Kept)
All project items still there ✅ (Kept)
All delivery options still there ✅ (Kept)
```

**Procurement Page:**
```
All procurement options still there ✅ (Kept)
All supplier info still there ✅ (Kept)
```

---

## ⚠️ **Important Notes**

### **1. This is NOT Reversible!**

```
Once you wipe:
- ❌ Deleted data CANNOT be recovered
- ❌ No "undo" button
- ✅ But you can re-run optimizations
- ✅ Base data is safe
```

**Recommendation:** Create backup first!
```powershell
.\backup_database.bat
```

### **2. Order Matters (Foreign Keys)**

```
The script deletes in correct order:
1. cashflow_events (references decisions)
2. finalized_decisions (references optimization_runs)
3. optimization_results (references optimization_runs)
4. optimization_runs (parent table)

This prevents foreign key constraint errors ✅
```

### **3. Bunch Management Data**

```
Finalized decisions include:
- bunch_id
- bunch_name

These are also deleted ✅
You'll need to create new bunches after re-optimization
```

---

## 🔄 **Workflow After Wipe**

```
1. Run wipe script
   .\wipe_calculated_data.bat
   
2. Verify data (optional)
   Check dashboard - should show $0 inflow/outflow
   
3. Run new optimization
   Navigate to: Advanced Optimization
   Select strategy
   Run optimization
   
4. Save results
   Review proposals
   Save as decisions
   
5. Finalize
   Lock decisions
   Cashflow events created
   
6. Dashboard updated
   Shows new financial data
```

---

## 📚 **Files Created**

```
✅ backend/wipe_calculated_data.py
   - Python script to wipe data
   - Runs inside Docker container
   - Safe deletion with logging

✅ wipe_calculated_data.bat
   - Windows batch script
   - Double confirmation required
   - Easy to run

✅ 📋_WIPE_CALCULATED_DATA_GUIDE.md (This file)
   - Complete documentation
   - Usage guide
   - Safety information
```

---

## 💡 **Safety Features**

### **1. Double Confirmation**
```
Requires two separate confirmations:
1. Type exact phrase: "WIPE RESULTS"
2. Type exact phrase: "YES"

Prevents accidental deletion ✅
```

### **2. Clear Logging**
```
Shows exactly what's being deleted:
- Table name
- Number of rows
- Success/failure

Full transparency ✅
```

### **3. Transaction Safety**
```
Uses database transaction:
- If any error occurs → Rollback all changes
- All-or-nothing operation

Data integrity guaranteed ✅
```

### **4. Keep Base Data**
```
Only deletes from specific tables:
- optimization_runs
- optimization_results
- finalized_decisions
- cashflow_events

Never touches:
- users
- projects
- project_items
- delivery_options
- procurement_options
- budget_data

Your setup is safe ✅
```

---

## 🚀 **Quick Commands**

### **Wipe Calculated Data:**
```powershell
.\wipe_calculated_data.bat
```

### **Backup Before Wipe (Recommended):**
```powershell
.\backup_database.bat
.\wipe_calculated_data.bat
```

### **Check What Will Be Deleted:**
```powershell
docker-compose exec postgres psql -U postgres -d procurement_dss -c "
SELECT 
  'optimization_runs' as table_name, COUNT(*) as count FROM optimization_runs
UNION ALL
SELECT 'optimization_results', COUNT(*) FROM optimization_results
UNION ALL
SELECT 'finalized_decisions', COUNT(*) FROM finalized_decisions
UNION ALL
SELECT 'cashflow_events', COUNT(*) FROM cashflow_events;
"
```

### **Verify After Wipe:**
```powershell
# Should all show 0
docker-compose exec postgres psql -U postgres -d procurement_dss -c "
SELECT COUNT(*) as cashflow_events_count FROM cashflow_events;
"
```

---

## ✅ **Summary**

**Purpose:** Clean slate for new optimizations while keeping base data

**Deletes:**
- ✅ Optimization runs (history)
- ✅ Optimization results (calculations)
- ✅ Finalized decisions (all statuses)
- ✅ Cashflow events (all types)

**Keeps:**
- ✅ Users, Projects, Items, Delivery Options
- ✅ Procurement Options
- ✅ Budget Data

**Safety:**
- ✅ Double confirmation required
- ✅ Transaction-safe (all-or-nothing)
- ✅ Can backup first
- ✅ Clear logging

**Use When:**
- ✅ Starting new optimization phase
- ✅ Testing different strategies
- ✅ Fixing mistakes
- ✅ New budget period

---

## 🎊 **READY TO USE!**

**Command:**
```powershell
.\wipe_calculated_data.bat
```

**Remember:** 
1. **Backup first** (optional but recommended): `.\backup_database.bat`
2. **Double confirm** when prompted
3. **Verify results** on dashboard

**Your base data is safe! Only calculated results will be wiped! 🎉**

