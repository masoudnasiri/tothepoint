# 🧪 Platform Workflow Testing Guide

**Status:** ✅ Clean data seeded and ready for testing  
**Date:** October 21, 2025

---

## 📊 Current Data State

### **What We Have:**
- ✅ **10 Projects** with realistic budgets and assignments
- ✅ **34 Master Items** in `items_master` (Dell, HP, Cisco, etc.)
- ✅ **66 Project Items** across all projects
- ✅ **0 Finalized Items** (ready to test finalization)
- ✅ **0 Procurement Options** (ready to add via UI)
- ✅ **0 Delivery Data** (clean state)

### **Projects Overview:**

| ID | Project Code | Name | Items | PM Assigned |
|----|--------------|------|-------|-------------|
| 1 | DC-MOD-2025 | Data Center Modernization | 10 | pm1 |
| 2 | OFF-IT-2025 | Office IT Refresh | 10 | pm1 |
| 3 | NET-INF-2025 | Network Infrastructure Upgrade | 10 | pm1 |
| 4 | SRV-VIRT-2025 | Server Virtualization Project | 8 | pm1 |
| 5 | STR-EXP-2025 | Storage Expansion Initiative | 6 | pm1 |
| 6 | SEC-SYS-2025 | Security Systems Upgrade | 6 | pm2 |
| 7 | BKP-DR-2025 | Backup and Disaster Recovery | 5 | pm2 |
| 8 | WLAN-EXP-2025 | Wireless Network Expansion | 4 | pm2 |
| 9 | VID-CONF-2025 | Video Conferencing Upgrade | 4 | pm2 |
| 10 | PRT-INF-2025 | Printing Infrastructure Renewal | 3 | pm2 |

---

## 🔐 User Credentials

| Username | Password | Role | Access |
|----------|----------|------|--------|
| `admin` | `admin123` | Admin | Full access to all features |
| `pmo_user` | `pmo123` | PMO | Can finalize project items |
| `pm1` | `pm123` | PM | Projects 1-5 |
| `pm2` | `pm123` | PM | Projects 6-10 |
| `procurement1` | `proc123` | Procurement | View finalized items, add options |
| `finance1` | `finance123` | Finance | View finalized decisions |

---

## 🧪 Complete Workflow Testing

### **Test 1: Project Manager - View Items**

**Login:** `pm1` / `pm123`

**Steps:**
1. Go to **Projects** page
2. Click on **"DC-MOD-2025"** (Data Center Modernization)
3. View the 10 project items

**Expected Results:**
- ✅ See 10 items (DELL-SRV-001, CISCO-SW-001, etc.)
- ✅ All items show `is_finalized = false`
- ✅ No "Finalize" button (PM cannot finalize)
- ✅ Can edit and delete items (no procurement options yet)

---

### **Test 2: PMO/Admin - Finalize Items**

**Login:** `admin` / `admin123` or `pmo_user` / `pmo123`

**Steps:**
1. Go to **Projects** → Select **"DC-MOD-2025"**
2. Find item **"DELL-SRV-001"** (PowerEdge R750 Server)
3. Click the **"Finalize"** button (green checkmark icon)
4. Confirm finalization

**API Call:**
```
PUT /items/{item_id}/finalize
Body: { "is_finalized": true }
```

**Expected Results:**
- ✅ Item shows "FINALIZED" chip/badge
- ✅ Item now appears in Procurement page
- ✅ Cannot unfinalize (no procurement decision yet)
- ✅ Success message displayed

**Test Additional Items:**
- Finalize 2-3 more items from different projects
- This gives procurement multiple items to work with

---

### **Test 3: Procurement - View Finalized Items**

**Login:** `procurement1` / `proc123`

**Steps:**
1. Go to **Procurement** page
2. View finalized items

**Expected Results:**
- ✅ See only the items you finalized (e.g., DELL-SRV-001)
- ✅ Items show with project information
- ✅ Can click to expand and view details
- ✅ **No loading issues** (this was the bug we fixed!)
- ✅ **No duplicate key warnings** (React keys fixed!)

---

### **Test 4: Procurement - Add Options**

**Still logged in as:** `procurement1`

**Steps:**
1. In Procurement page, find **"DELL-SRV-001"**
2. Click **"Add Option"** button
3. Fill in procurement option form:
   - **Supplier Name:** Dell Direct
   - **Base Cost:** 5000
   - **Currency:** USD
   - **Shipping Cost:** 200
   - **Lead Time:** 30 days
   - **Payment Terms:** Cash / 30 days
4. Click **"Save"**

**API Call:**
```
POST /procurement/options
Body: {
  "item_code": "DELL-SRV-001",
  "supplier_name": "Dell Direct",
  "base_cost": 5000,
  "currency_id": 1,
  "shipping_cost": 200,
  "lomc_lead_time": 30,
  "payment_terms": { "type": "cash", "days": 30 }
}
```

**Expected Results:**
- ✅ Option appears in the item's options list
- ✅ Shows supplier, cost, lead time
- ✅ Can add multiple options for comparison

**Add More Options:**
- Add 2-3 options per item with different:
  - Suppliers (Dell Direct, Vendor A, Vendor B)
  - Costs (5000, 4800, 5200)
  - Currencies (USD, EUR)
  - Lead times (30, 45, 60 days)

---

### **Test 5: Procurement - Finalize Decision**

**Still logged in as:** `procurement1`

**Steps:**
1. View options for **"DELL-SRV-001"**
2. Select the best option (e.g., Dell Direct - $5000)
3. Click **"Finalize"** button on that option
4. Confirm finalization

**API Call:**
```
PUT /procurement/option/{option_id}
Body: { "is_finalized": true }
```

**Expected Results:**
- ✅ Option marked as "Locked" or "Finalized"
- ✅ Other options for same item become read-only
- ✅ Cannot add more options for this item
- ✅ Decision visible in Finance page

---

### **Test 6: Finance - View Decisions**

**Login:** `finance1` / `finance123`

**Steps:**
1. Go to **Finance** page
2. View finalized decisions

**Expected Results:**
- ✅ See finalized decision for DELL-SRV-001
- ✅ Shows:
  - Project: DC-MOD-2025
  - Item: DELL-SRV-001 (PowerEdge R750)
  - Supplier: Dell Direct
  - Cost: $5,000 + $200 shipping = $5,200
  - Quantity: 5 units
  - Total: $26,000
- ✅ Can view budget vs. actual costs
- ✅ Can see payment terms and dates

---

### **Test 7: Workflow Restrictions**

#### **Test 7a: Cannot Unfinalize After Procurement Decision**

**Login as:** `admin`

**Steps:**
1. Go to Projects → DC-MOD-2025
2. Try to click "Unfinalize" on DELL-SRV-001

**Expected Results:**
- ❌ Unfinalize button is **disabled**
- ℹ️ Tooltip: "Cannot unfinalize: Procurement has finalized decision"

---

#### **Test 7b: Cannot Edit/Delete After Procurement Decision**

**Login as:** `pm1`

**Steps:**
1. Go to Projects → DC-MOD-2025
2. Try to click "Edit" or "Delete" on DELL-SRV-001

**Expected Results:**
- ❌ Edit and Delete buttons are **disabled**
- ℹ️ Tooltip: "Cannot edit/delete: Procurement has finalized decision"

---

#### **Test 7c: Can Edit/Delete Before Procurement Decision**

**Login as:** `pm1`

**Steps:**
1. Find an item that is **NOT finalized** (e.g., CISCO-SW-001)
2. Click "Edit" button
3. Change quantity from 4 to 6
4. Save

**Expected Results:**
- ✅ Edit works successfully
- ✅ Quantity updated to 6
- ✅ Can also delete this item (no procurement options exist)

---

## 📋 Testing Checklist

Use this checklist to verify all functionality:

### **Project Management**
- [ ] PM can view assigned projects
- [ ] PM can add items from master items
- [ ] PM can edit unfinalized items
- [ ] PM can delete items without procurement options
- [ ] PM **cannot** finalize items (no button visible)

### **PMO/Admin Functions**
- [ ] Can finalize project items
- [ ] Finalize button appears and works
- [ ] Can unfinalize items (only if no procurement decision)
- [ ] Cannot unfinalize after procurement decision

### **Procurement Functions**
- [ ] See only finalized items
- [ ] **No loading issues** when clicking items
- [ ] **No React duplicate key warnings**
- [ ] Can add procurement options
- [ ] Can add multiple options per item
- [ ] Can finalize procurement decision
- [ ] After finalizing, item becomes locked

### **Finance Functions**
- [ ] View finalized decisions
- [ ] See accurate costs and totals
- [ ] View budget information
- [ ] Track payment status

### **Workflow Integrity**
- [ ] Cannot unfinalize item with procurement decision
- [ ] Cannot edit item with procurement decision
- [ ] Cannot delete item with procurement decision
- [ ] Can edit/delete items without procurement options

---

## 🐛 Known Issues Fixed

1. ✅ **Procurement Loading Issue** - Fixed by correcting accordion key parsing
2. ✅ **Duplicate React Keys** - Fixed by using `itemCode-projectItemId` format
3. ✅ **Internal Server Error on Edit** - Fixed by importing `FinalizedDecision` model
4. ✅ **Wrong items in Procurement** - Fixed by using `listFinalized()` endpoint

---

## 🎯 Success Criteria

The platform is working correctly if:

1. ✅ **Complete workflow from PM → PMO → Procurement → Finance works**
2. ✅ **No console errors or React warnings**
3. ✅ **Proper access control** (PMs can't finalize, Procurement can't edit projects)
4. ✅ **Data integrity** (can't edit after procurement decision)
5. ✅ **UI responsive** (no infinite loading, no crashes)

---

## 📞 Next Steps

After testing, you can:

1. **Add more master items** to `items_master` table
2. **Create more projects** and assign to PMs
3. **Test multi-currency** procurement options (USD, EUR, IRR)
4. **Test exchange rates** in Finance page
5. **Test budget tracking** and overspend warnings

---

**Happy Testing!** 🎉

If you find any issues, they are now isolated and can be debugged using the actual API endpoints and UI workflow.
