# ⚡ Wipe Calculated Data - Quick Start

## ✅ **YOUR REQUEST - READY!**

**You Want:**
> "wipe the calculated data contain optimization results, final decision and cash flow and just let the project data, procurement and finance data be there"

**Status:** ✅ **SCRIPT READY TO RUN!**

---

## 🚀 **RUN IT NOW**

```powershell
.\wipe_calculated_data.bat
```

**What it does:**
1. Asks for confirmation (twice for safety)
2. Deletes all optimization results
3. Deletes all finalized decisions
4. Deletes all cashflow events
5. **KEEPS** all your projects, procurement options, and budgets

---

## 📊 **What Gets Deleted vs Kept**

| Data Type | Action |
|-----------|--------|
| **Optimization Runs** | ❌ DELETED |
| **Optimization Results** | ❌ DELETED |
| **Finalized Decisions** | ❌ DELETED |
| **Cashflow Events** | ❌ DELETED |
| **Users** | ✅ KEPT |
| **Projects** | ✅ KEPT |
| **Project Items** | ✅ KEPT |
| **Delivery Options** | ✅ KEPT |
| **Procurement Options** | ✅ KEPT |
| **Budget Data** | ✅ KEPT |

---

## 🧪 **Quick Test (Optional)**

**Before running wipe, check counts:**

```powershell
docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT COUNT(*) FROM finalized_decisions;"
docker-compose exec postgres psql -U postgres -d procurement_dss -c "SELECT COUNT(*) FROM cashflow_events;"
```

**After running wipe, check again:**
- Should show 0 for decisions and cashflow ✅
- Projects and procurement options unchanged ✅

---

## ⚠️ **Safety**

**Double Confirmation Required:**
1. Type `WIPE RESULTS` exactly
2. Type `YES` exactly

**Backup First (Recommended):**
```powershell
.\backup_database.bat
.\wipe_calculated_data.bat
```

---

## 🎯 **When to Use**

✅ **Use when:**
- Starting new optimization phase
- Want to test different strategies
- Need to redo decisions
- New budget period

❌ **Don't use when:**
- You want to keep current decisions
- Need historical optimization data
- Still analyzing results

---

## 📚 **Documentation**

**Quick:** `⚡_WIPE_RESULTS_NOW.md` (This file)  
**Complete:** `📋_WIPE_CALCULATED_DATA_GUIDE.md`

---

## ✅ **Summary**

**Command:** `.\wipe_calculated_data.bat`  
**Safety:** Double confirmation required  
**Deletes:** Optimization results, decisions, cashflow  
**Keeps:** Projects, procurement, budgets  
**Time:** ~10 seconds  
**Reversible:** ❌ No (backup first!)  

---

**Ready when you are! Run the script and start fresh! 🚀**

