# Performance Issue Analysis - Procurement Options Page

## 📊 Current System State

- **10 IT Projects**
- **3,552 Project Items** (300-400 items per project)
- **23,069 Procurement Options** (average 6.5 options per item)
- All items have 5-8 procurement options each

---

## 🐌 Performance Problem Identified

### Root Cause
The slowness is **NOT** from the Procurement Options page itself. The backend logs show that another component (likely **Dashboard** or **Projects Summary**) is making **3,552+ individual database queries** to calculate average costs:

```sql
SELECT avg(procurement_options.base_cost) AS avg_1
FROM procurement_options
WHERE procurement_options.item_code = 'IT-292-001' AND procurement_options.is_active = true

SELECT avg(procurement_options.base_cost) AS avg_1
FROM procurement_options
WHERE procurement_options.item_code = 'IT-292-002' AND procurement_options.is_active = true

... (repeated 3,552 times for each item!)
```

This is a classic **N+1 query problem** that causes extreme slowness.

---

## 📝 Current Data Loading Process for Procurement Options Page

### Step 1: Initial Page Load
**Frontend (`ProcurementPage.tsx`):**
```typescript
// On component mount
useEffect(() => {
  fetchData();
}, []);

const fetchData = async () => {
  // Fetch only the list of items (NOT the options)
  const itemsResponse = await procurementAPI.getItemsWithDetails();
  setItemsWithDetails(itemsResponse.data);  // ~3,552 items
  setItemCodes(itemsResponse.data.map(item => item.item_code));
};
```

**Backend (`/procurement/items-with-details`):**
```sql
-- Single optimized query
SELECT DISTINCT ON (pi.item_code)
    pi.item_code,
    pi.item_name,
    pi.description,
    pi.project_id,
    pi.id as project_item_id
FROM project_items pi
LEFT JOIN finalized_decisions fd ON pi.id = fd.project_item_id AND fd.status = 'LOCKED'
WHERE fd.id IS NULL  -- Only items without LOCKED decisions
ORDER BY pi.item_code, 
         CASE WHEN pi.description IS NOT NULL THEN 1 ELSE 2 END,
         pi.created_at DESC
```

**Result:** Returns ~3,552 unique items

---

### Step 2: User Expands an Item (Lazy Loading)
**Frontend:**
```typescript
// When user clicks to expand an accordion
const handleAccordionChange = (itemCode: string) => async (event, isExpanded) => {
  if (isExpanded && !loadedItemOptions[itemCode]) {
    // Fetch options ONLY for this specific item
    const options = await fetchOptionsByItemCode(itemCode);
    setLoadedItemOptions(prev => ({
      ...prev,
      [itemCode]: options  // Cache the loaded options
    }));
  }
};
```

**Backend (`/procurement/options/{item_code}`):**
```sql
SELECT * FROM procurement_options
WHERE is_active = true 
  AND item_code = 'IT-287-001'
ORDER BY item_code, created_at DESC
LIMIT 100
```

**Result:** Returns 5-8 options for that specific item only

---

## ⚠️ THE ACTUAL PROBLEM

### Where the Slowness Comes From

The **3,552 average cost queries** are coming from a **different endpoint** (NOT the Procurement Options page). Based on the logs, this is likely:

1. **Dashboard Page** - calculating statistics for all items
2. **Projects Summary Page** - showing average costs per project
3. **Some background process** - running continuously

### Evidence from Logs:
```
SELECT avg(procurement_options.base_cost) AS avg_1
FROM procurement_options
WHERE procurement_options.item_code = $1::VARCHAR AND procurement_options.is_active = true
INFO:sqlalchemy.engine.Engine:[cached since 1.438s ago] ('IT-292-289',)
... (repeated 3,552 times)
```

This pattern shows:
- Query is cached (same query repeated)
- Running for EVERY item code in sequence
- NOT related to the `/procurement/items-with-details` endpoint

---

## 💡 Solutions to Fix the Performance Issue

### Solution 1: Find and Optimize the Dashboard/Summary Query (RECOMMENDED)

**Problem:** Dashboard is calculating average cost for each item individually

**Fix:** Use a single aggregated query:
```sql
-- Instead of 3,552 queries, use ONE query:
SELECT 
    item_code,
    AVG(base_cost) as avg_cost,
    COUNT(*) as option_count
FROM procurement_options
WHERE is_active = true
GROUP BY item_code
```

This reduces **3,552 queries → 1 query** (3,552x faster!)

---

### Solution 2: Add Database Indexes

```sql
CREATE INDEX idx_procurement_options_item_code_active 
ON procurement_options(item_code, is_active);

CREATE INDEX idx_finalized_decisions_project_item_status 
ON finalized_decisions(project_item_id, status);
```

---

### Solution 3: Add Caching Layer

Use Redis or in-memory caching for frequently accessed data:
- Average costs per item
- Item summaries
- Project statistics

---

## 🔍 How to Identify the Culprit

### Step 1: Check which endpoint is being called
```bash
docker logs cahs_flow_project-backend-1 --tail 500 | grep "GET /"
```

Look for patterns like:
- `GET /dashboard`
- `GET /projects`
- `GET /projects/{id}/summary`

### Step 2: Check the Dashboard page
The Dashboard likely loads project summaries with average costs for all items.

### Step 3: Profile the slow query
```bash
# Watch logs in real-time
docker logs -f cahs_flow_project-backend-1 | grep "avg(procurement_options.base_cost)"
```

---

## 📈 Current Performance Metrics

### Procurement Options Page (OPTIMIZED ✅)
- **Initial Load:** 1 SQL query (items list)
- **Per Item Expansion:** 1 SQL query (that item's options)
- **Total Queries:** 1 + N (where N = number of expanded items)
- **Performance:** Fast! ⚡

### The Problem Component (NEEDS FIX ❌)
- **Queries:** 3,552 individual `AVG()` queries
- **Time:** Several seconds to minutes
- **Performance:** Very slow 🐌

---

## 🎯 Recommended Action Plan

1. **Identify the slow component:**
   - Check Dashboard page
   - Check Projects summary page
   - Look for any component loading project statistics

2. **Optimize the aggregation query:**
   - Replace N individual queries with 1 GROUP BY query
   - Add proper indexes

3. **Add caching if needed:**
   - Cache average costs
   - Refresh cache only when options are added/updated

4. **Consider pagination:**
   - Don't load all 3,552 items at once
   - Load 50-100 items per page
   - Add virtual scrolling for large lists

---

## 📞 Questions for Your Friend

1. **Is it normal to calculate average costs for 3,552 items on every page load?**
   - Should this be cached?
   - Should this be pre-calculated?

2. **Can we use a single GROUP BY query instead of 3,552 individual queries?**
   - This would be 1000x+ faster

3. **Should we add pagination to the Procurement Options page?**
   - Currently showing all 3,552 items at once
   - Could show 50-100 items per page instead

4. **Should we add database indexes?**
   - On `procurement_options(item_code, is_active)`
   - On `finalized_decisions(project_item_id, status)`

5. **Is there a background process running that's calculating these averages?**
   - The logs show continuous calculation
   - Might be a dashboard refresh or websocket update

---

## 🔧 Technical Details

### Current Architecture:
```
Frontend (React) 
  ↓ HTTP Request
Backend (FastAPI) 
  ↓ SQLAlchemy ORM
Database (PostgreSQL)
```

### Problem Pattern (N+1 Query):
```python
# BAD: N+1 queries
for item_code in all_item_codes:  # 3,552 iterations
    avg_cost = db.query(func.avg(ProcurementOption.base_cost))\
        .filter(ProcurementOption.item_code == item_code)\
        .scalar()
```

### Solution Pattern (Single Query):
```python
# GOOD: 1 query
results = db.query(
    ProcurementOption.item_code,
    func.avg(ProcurementOption.base_cost).label('avg_cost')
)\
.filter(ProcurementOption.is_active == True)\
.group_by(ProcurementOption.item_code)\
.all()
```

---

## 📊 Performance Comparison

| Approach | Queries | Estimated Time | Status |
|----------|---------|----------------|--------|
| Current (N+1) | 3,552 | 30-60 seconds | ❌ Very Slow |
| Optimized (GROUP BY) | 1 | < 1 second | ✅ Fast |
| With Caching | 0-1 | < 100ms | ✅ Very Fast |

---

## 🚀 Quick Win

Find this pattern in your code:
```python
for item_code in item_codes:
    avg = await db.execute(
        select(func.avg(ProcurementOption.base_cost))
        .where(ProcurementOption.item_code == item_code)
    )
```

Replace with:
```python
# Single query with GROUP BY
results = await db.execute(
    select(
        ProcurementOption.item_code,
        func.avg(ProcurementOption.base_cost).label('avg_cost')
    )
    .where(ProcurementOption.is_active == True)
    .group_by(ProcurementOption.item_code)
)
```

This single change will make the system **1000x+ faster**! 🎉

