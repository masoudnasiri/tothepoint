# 🔒 Procurement Page - Hide Finalized Items

## ✅ **ISSUE RESOLVED**

**Date**: October 21, 2025  
**Status**: ✅ **FIXED**

---

## 🚨 **PROBLEM**

Items that were finalized in the "Finalized Decisions" page (with LOCKED or PROPOSED status) still appeared in the Procurement page.

**Expected Behavior**: Once an item has a finalized decision (saved from optimization), it should disappear from the Procurement page.

**Actual Behavior**: Items remained visible in Procurement even after finalization.

---

## 🔍 **ROOT CAUSE**

The `/items/finalized` endpoint was only checking if items are finalized by PMO (`is_finalized = true`), but NOT checking if they have finalized decisions.

**Code Before:**
```python
# Get finalized items
result = await db.execute(
    select(ProjectItemModel)
    .where(ProjectItemModel.is_finalized == True)  # ✅ Only finalized items
    # ❌ But doesn't exclude items with finalized decisions!
)
```

**Similarly**, the `/procurement/items-with-details` endpoint was excluding items with decisions, but NOT checking if items were finalized by PMO.

---

## 🔧 **SOLUTION**

### **File 1: `backend/app/routers/items.py`**

Added filtering to exclude items with LOCKED or PROPOSED finalized decisions.

**Updated `/items/finalized` endpoint (Lines 164-196):**

```python
# Get finalized items that DON'T have LOCKED or PROPOSED decisions
result = await db.execute(
    select(ProjectItemModel)
    .where(
        and_(
            ProjectItemModel.is_finalized == True,  # ✅ Finalized by PMO
            # ✅ Exclude items with LOCKED or PROPOSED decisions
            ~exists(
                select(FinalizedDecision.id)
                .where(
                    FinalizedDecision.project_item_id == ProjectItemModel.id,
                    FinalizedDecision.status.in_(['LOCKED', 'PROPOSED'])
                )
            )
        )
    )
)
```

### **File 2: `backend/app/routers/procurement.py`**

Added check for `is_finalized = true` to the existing query.

**Updated `/procurement/items-with-details` endpoint (Line 86):**

```sql
WHERE fd.id IS NULL  -- Only items without LOCKED or PROPOSED decisions
  AND pi.is_finalized = true  -- ✅ Only finalized project items
```

---

## 🔄 **COMPLETE WORKFLOW**

### **Item Visibility in Procurement Page:**

```
┌──────────────────────────────────────────────────────────────┐
│ PROCUREMENT PAGE VISIBILITY RULES                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Project Item Created        → NOT visible (not finalized)   │
│         ↓                                                    │
│  PMO Finalizes Item          → ✅ VISIBLE in Procurement     │
│         ↓                                                    │
│  Procurement adds options    → ✅ Still VISIBLE              │
│         ↓                                                    │
│  Optimization runs           → ✅ Still VISIBLE              │
│         ↓                                                    │
│  Finance saves proposal      → ❌ HIDDEN (PROPOSED status)   │
│  (Creates PROPOSED decision)                                 │
│         ↓                                                    │
│  Finance finalizes decision  → ❌ HIDDEN (LOCKED status)     │
│  (Changes to LOCKED status)                                  │
│         ↓                                                    │
│  Finance reverts decision    → ✅ VISIBLE again (REVERTED)   │
│  (Changes to REVERTED status)                                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### **Decision Status Impact:**

| Item Status | Decision Status | Visible in Procurement? |
|-------------|-----------------|-------------------------|
| Not Finalized | - | ❌ NO |
| Finalized | No decision | ✅ YES |
| Finalized | PROPOSED | ❌ NO (already optimized) |
| Finalized | LOCKED | ❌ NO (already finalized) |
| Finalized | REVERTED | ✅ YES (available for re-optimization) |

---

## ✅ **EXPECTED BEHAVIOR**

### **Scenario 1: New Finalized Item**
```
1. PMO finalizes item
   → Item appears in Procurement ✅
2. Procurement adds options
   → Item still visible ✅
3. Finance runs optimization and saves proposal
   → Item DISAPPEARS from Procurement ✅ (status = PROPOSED)
4. Finance finalizes the decision
   → Item stays hidden ✅ (status = LOCKED)
```

### **Scenario 2: Reverted Item**
```
1. Item has LOCKED decision
   → Not visible in Procurement ❌
2. Finance reverts the decision
   → Item REAPPEARS in Procurement ✅ (status = REVERTED)
3. Procurement can add new options
   → Item still visible ✅
```

---

## 🎯 **BUSINESS LOGIC**

### **Why Items Are Hidden After Finalization:**

1. **Prevent Duplicate Work**: Item already has procurement decision
2. **Workflow Clarity**: Clear separation between "to be decided" and "decided"
3. **Data Integrity**: Prevents conflicting procurement options
4. **Process Control**: Forces use of Finalized Decisions page for changes
5. **Audit Trail**: All changes tracked through decision status changes

### **When to Use Each Page:**

| Page | Purpose | Shows |
|------|---------|-------|
| **Procurement** | Add options for undecided items | Items needing procurement |
| **Finalized Decisions** | Manage decided items | Items with PROPOSED/LOCKED/REVERTED decisions |

---

## 📋 **FILES MODIFIED**

1. `backend/app/routers/items.py`
   - **Line 164**: Updated docstring
   - **Lines 165-166**: Added imports for `and_`, `exists`, `FinalizedDecision`
   - **Lines 177-196**: Added filtering to exclude items with LOCKED/PROPOSED decisions

2. `backend/app/routers/procurement.py`
   - **Line 86**: Added `AND pi.is_finalized = true` to SQL query

---

## 🧪 **VERIFICATION STEPS**

### **Test 1: Before Optimization**
1. Log in as Procurement
2. Navigate to Procurement page
3. Expected: See all finalized items (5 items)

### **Test 2: After Saving Proposal**
1. Log in as Finance
2. Run optimization
3. Save a proposal (creates PROPOSED decisions)
4. Log in as Procurement
5. Navigate to Procurement page
6. Expected: Items with PROPOSED decisions are HIDDEN ✅

### **Test 3: After Finalizing Decisions**
1. Log in as Finance
2. Navigate to Finalized Decisions
3. Finalize some decisions (PROPOSED → LOCKED)
4. Log in as Procurement
5. Navigate to Procurement page
6. Expected: Items with LOCKED decisions remain HIDDEN ✅

### **Test 4: After Reverting Decisions**
1. Log in as Finance
2. Navigate to Finalized Decisions
3. Revert a decision (LOCKED → REVERTED)
4. Log in as Procurement
5. Navigate to Procurement page
6. Expected: Reverted item REAPPEARS ✅

---

## ✅ **TESTING RESULTS**

| Scenario | Before Fix | After Fix | Status |
|----------|------------|-----------|--------|
| Item finalized by PMO | ✅ Visible | ✅ Visible | No change |
| Item with PROPOSED decision | ✅ Visible (BUG) | ❌ Hidden | **FIXED** |
| Item with LOCKED decision | ✅ Visible (BUG) | ❌ Hidden | **FIXED** |
| Item with REVERTED decision | ? | ✅ Visible | **CORRECT** |

---

## 🔒 **DATA INTEGRITY**

This fix ensures:
- ✅ **No Duplicate Options**: Can't add options to already-decided items
- ✅ **Clear Workflow**: Procurement sees only items needing decisions
- ✅ **Proper Separation**: Decided items managed in Finalized Decisions page
- ✅ **Reversibility**: Reverted items can receive new options

---

## 📊 **SUMMARY**

### **Procurement Page Now Shows:**
- ✅ Items finalized by PMO (is_finalized = true)
- ✅ Items WITHOUT finalized decisions
- ✅ Items with REVERTED decisions (can be re-optimized)

### **Procurement Page Does NOT Show:**
- ❌ Items not finalized by PMO
- ❌ Items with PROPOSED decisions (saved from optimization)
- ❌ Items with LOCKED decisions (finalized by finance)

---

**Status**: ✅ **COMPLETE**  
**Impact**: Procurement page now correctly hides items that have been finalized  
**Service**: Backend restarted to apply changes
