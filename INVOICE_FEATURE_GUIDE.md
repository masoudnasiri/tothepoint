# 📋 Invoice Feature - Complete User Guide

## **✅ INVOICE FEATURE IS NOW LIVE!**

**Status:** Compiled successfully and deployed  
**Location:** Finalized Decisions page  
**Access:** http://localhost:3000/decisions  

---

## 🎯 **WHERE TO FIND THE INVOICE FEATURE**

### **Main Location: "Finalized Decisions" Page**

**How to Access:**
1. Login to http://localhost:3000
2. Look at the left navigation menu
3. Click **"Finalized Decisions"** (has a checkmark icon ✓)
4. You'll see all procurement decisions with their invoice configuration

---

## 📊 **WHAT YOU'LL SEE**

### **Invoice Timing Display (All Decisions)**

In the **"Finalized Decisions"** table, there's a column called **"Invoice Timing"** that shows:

**For ABSOLUTE timing:**
```
Date: 05/01/2025
```

**For RELATIVE timing:**
```
+30 days after delivery
```

### **Edit Invoice Button (PROPOSED Decisions)**

For decisions with status **"PROPOSED"** (yellow chip), you'll see:
- 📝 **Blue icon button** (Assignment/Document icon)
- **Tooltip:** "Configure Invoice Timing"
- **Click it** to open the invoice configuration dialog

---

## 🔧 **HOW TO CONFIGURE INVOICE TIMING**

### **Step-by-Step Guide:**

#### **Step 1: Create or Load Decisions**

First, you need decisions in PROPOSED status:
```
1. Go to Optimization page
2. Run optimization
3. Click "Save Plan"
4. Decisions saved with status='PROPOSED'
```

#### **Step 2: Navigate to Finalized Decisions**

```
1. Click "Finalized Decisions" in left menu
2. See all PROPOSED decisions (yellow chips)
3. Look at the "Actions" column
```

#### **Step 3: Open Invoice Configuration**

```
1. Find a PROPOSED decision
2. Click the blue 📝 icon in Actions column
3. Invoice Configuration dialog opens
```

#### **Step 4: Configure Invoice Timing**

**You have 2 options:**

##### **Option A: ABSOLUTE (Specific Date)**

```
1. Select "Absolute Date (Specific Date)" from dropdown
2. A date picker appears
3. Click on the date picker
4. Select the exact date when invoice will be issued
5. Example: May 15, 2025
```

**Use Case:** 
- Milestone-based payments
- Fixed contract dates
- Pre-agreed billing dates

##### **Option B: RELATIVE (Days After Delivery)**

```
1. Select "Relative (Days After Delivery)" from dropdown
2. A number input appears
3. Enter number of days after delivery
4. Example: 30 (for "Net 30" terms)
```

**Use Case:**
- Standard payment terms (Net 30, Net 60)
- Flexible scheduling
- Client-driven timing

#### **Step 5: Preview & Save**

```
1. See "Calculation Preview" at bottom of dialog
2. Shows exactly when invoice will be issued
3. Click "Save Invoice Configuration"
4. Done! Invoice timing configured
```

---

## 💡 **EXAMPLES**

### **Example 1: Net 30 Terms**

**Scenario:** Standard business terms, invoice 30 days after delivery

**Configuration:**
```
Delivery Date: April 20, 2025
Invoice Timing Type: RELATIVE
Days After Delivery: 30

Result: Invoice issued May 20, 2025
```

### **Example 2: Milestone Payment**

**Scenario:** Fixed date payment per contract

**Configuration:**
```
Delivery Date: April 20, 2025
Invoice Timing Type: ABSOLUTE
Invoice Issue Date: June 1, 2025

Result: Invoice issued June 1, 2025 (regardless of delivery)
```

### **Example 3: Net 60 Terms**

**Scenario:** Extended payment terms

**Configuration:**
```
Delivery Date: March 15, 2025
Invoice Timing Type: RELATIVE
Days After Delivery: 60

Result: Invoice issued May 14, 2025
```

---

## 🔄 **COMPLETE WORKFLOW WITH INVOICE**

### **Full Procurement Cycle:**

```
Step 1: Create Project & Items
├─ Projects page
├─ Add "Construction Project"
└─ Add items with delivery dates

Step 2: Add Suppliers & Budgets
├─ Procurement page → Add suppliers
└─ Finance page → Add budgets

Step 3: Run Optimization
├─ Optimization page
├─ Click "Run Optimization"
└─ Click "Save Plan"
Result: Decisions created with status=PROPOSED

Step 4: Configure Invoice Timing ⭐ NEW
├─ Go to "Finalized Decisions" page
├─ See PROPOSED decisions (yellow chips)
├─ Click blue 📝 icon for each decision
├─ Choose: ABSOLUTE or RELATIVE
├─ Set: Date or Days
└─ Save configuration

Step 5: Finalize Decisions
├─ (Future: Finalize button on page)
├─ (Current: Use API or set status=LOCKED)
└─ Cash flows auto-generated using invoice config

Step 6: View Cash Flow
├─ Go to Dashboard
├─ See inflow events on calculated invoice dates
└─ Outflow events based on payment terms

Step 7: (Optional) Revert
├─ Go to Finalized Decisions
├─ Find LOCKED decision (green chip)
├─ Click red ↶ icon
├─ Confirm reversion
└─ Cash flows marked as cancelled (not deleted!)
```

---

## 📱 **UI ELEMENTS GUIDE**

### **Finalized Decisions Page:**

**Top Section:**
- Page title: "Finalized Decisions"
- Refresh button (right side)
- Summary cards showing counts by status

**Table Columns:**
```
| ID | Item Code | Purchase | Delivery | Cost | Invoice Timing | Status | Finalized | Actions |
```

**Status Colors:**
- 🟡 **PROPOSED** (Yellow) - Editable, has 📝 icon
- 🟢 **LOCKED** (Green) - Finalized, has ↶ icon  
- 🔴 **REVERTED** (Red) - Cancelled

**Action Icons:**
- 📝 **Blue icon** (PROPOSED) - Configure invoice timing
- ↶ **Red icon** (LOCKED) - Revert decision
- ℹ️ **Gray icon** (If notes exist) - View notes

### **Invoice Configuration Dialog:**

**Header:** "Configure Invoice Timing"

**Content:**
1. **Info alert** - Explains purpose
2. **Decision summary** - Item, delivery date, cost
3. **Timing type dropdown** - ABSOLUTE or RELATIVE
4. **Configuration input** - Date picker OR number input
5. **Preview alert** - Shows calculated invoice date

**Buttons:**
- **Cancel** - Close without saving
- **Save Invoice Configuration** - Save and close

---

## 🎯 **HOW IT WORKS BEHIND THE SCENES**

### **When You Configure Invoice:**

```python
# Updates the FinalizedDecision record:
decision.invoice_timing_type = 'RELATIVE'  # or 'ABSOLUTE'
decision.invoice_days_after_delivery = 30   # or null
decision.invoice_issue_date = null          # or specific date
```

### **When You Finalize (Lock):**

```python
# System calculates invoice date:
if invoice_timing_type == 'ABSOLUTE':
    invoice_date = invoice_issue_date
else:  # RELATIVE
    invoice_date = delivery_date + timedelta(days=invoice_days_after_delivery)

# Creates cash flow inflow event:
CashflowEvent(
    event_type='inflow',
    event_date=invoice_date,
    amount=final_cost,
    description=f"Revenue: {item_code}",
    is_cancelled=False
)
```

### **When You Revert:**

```python
# System marks events as cancelled (NOT deleted!):
UPDATE cashflow_events 
SET is_cancelled = TRUE,
    cancelled_at = NOW(),
    cancelled_by_id = current_user_id,
    cancellation_reason = 'Decision reverted'
WHERE related_decision_id = decision_id

# Audit trail preserved!
```

---

## 🔍 **TESTING THE FEATURE**

### **Quick Test (2 minutes):**

```
1. Login as admin
2. Go to "Finalized Decisions" page
3. Click "Finalized Decisions" in left menu
4. If no decisions exist:
   a. Go to Optimization → Run → Save
   b. Come back to Finalized Decisions
5. Look for PROPOSED decisions (yellow chips)
6. Click the blue 📝 icon
7. Dialog opens!
8. Try ABSOLUTE: Pick a date
9. Try RELATIVE: Enter 45 days
10. See preview at bottom
11. Click "Save Invoice Configuration"
12. Success message appears!
13. Invoice timing now displayed in table
```

---

## 📊 **WHAT THE INVOICE FEATURE ENABLES**

### **Flexible Payment Terms:**
- ✅ Net 30, Net 60, Net 90
- ✅ Fixed milestone dates
- ✅ Client-specific terms
- ✅ Contract-based timing

### **Accurate Cash Flow:**
- ✅ Inflow events on correct dates
- ✅ Revenue timing matches reality
- ✅ Better financial projections
- ✅ Improved planning

### **Business Intelligence:**
- ✅ Compare payment terms impact
- ✅ Optimize cash conversion cycle
- ✅ Plan working capital needs
- ✅ Negotiate better terms

---

## ✅ **VERIFICATION CHECKLIST**

Test each feature:

- [ ] Navigate to Finalized Decisions page
- [ ] See "Invoice Timing" column in table
- [ ] Find a PROPOSED decision
- [ ] Click blue 📝 icon
- [ ] Dialog opens
- [ ] Switch between ABSOLUTE and RELATIVE
- [ ] Configure invoice timing
- [ ] See preview calculation
- [ ] Save configuration
- [ ] Success message appears
- [ ] Table updates with new timing

---

## 🎊 **SUMMARY**

**Invoice Feature Location:**
```
📍 Main Page: Finalized Decisions
📍 URL: http://localhost:3000/decisions
📍 Navigation: Left menu, "Finalized Decisions"
📍 Icon: Blue 📝 (for PROPOSED decisions)
```

**What It Does:**
- Configure when invoices are issued
- Choose ABSOLUTE date or RELATIVE days
- Preview calculated dates
- Save configuration
- Auto-generate cash flows on finalization

**Status:**
- ✅ Backend API: Complete
- ✅ Database Schema: Complete
- ✅ Frontend UI: Complete & Compiled
- ✅ Feature: **LIVE AND READY TO USE**

---

**Access your system now at: http://localhost:3000**  
**Login as admin and explore the "Finalized Decisions" page!** 🚀

*Invoice Feature Guide*  
*Version: 3.1*  
*Date: October 8, 2025*  
*Status: Live & Operational*
