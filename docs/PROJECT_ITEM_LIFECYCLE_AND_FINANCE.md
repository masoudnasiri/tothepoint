# Project Item Lifecycle and Finance Features

**Last Updated:** October 21, 2025  
**Version:** 1.1.0

## Table of Contents
- [Overview](#overview)
- [Project Item Lifecycle](#project-item-lifecycle)
- [Finance Page Features](#finance-page-features)
- [Exchange Rate Management](#exchange-rate-management)
- [Complete Workflow](#complete-workflow)

---

## Overview

This document describes the complete lifecycle of project items from creation to procurement finalization, including the Finance page features and currency exchange rate management.

---

## Project Item Lifecycle

### 1. **Item States**

Project items go through the following states:

#### **A. Draft State (Not Finalized)**
- **Who Can Create:** Project Managers (PM)
- **Editable:** Yes (until procurement options are added)
- **Deletable:** Yes (until procurement options are added)
- **Visible in Procurement:** No

#### **B. Finalized State**
- **Who Can Finalize:** PMO or Admin users
- **Visible in Procurement:** Yes
- **Editable:** No (procurement options may exist)
- **Deletable:** No (procurement options may exist)

#### **C. Locked State (Procurement Finalized)**
- **Triggered When:** Procurement creates a finalized decision
- **Unfinalize:** Disabled (locked with 🔒 icon)
- **Reason:** Procurement team has made a binding decision

---

### 2. **Action Buttons & Their Rules**

#### **Edit Button (✏️)**
- **Enabled When:** `procurement_options_count == 0`
- **Disabled When:** Item has any procurement options
- **Tooltip When Disabled:** "Cannot edit: X procurement option(s) exist"
- **Reason:** Once procurement team adds options, the item specifications are locked

#### **Delete Button (🗑️)**
- **Enabled When:** `procurement_options_count == 0`
- **Disabled When:** Item has any procurement options
- **Tooltip When Disabled:** "Cannot delete: X procurement option(s) exist"
- **Reason:** Cannot delete items that are in the procurement process

#### **Finalize Button (✅) - PMO/Admin Only**
- **Visible When:** `is_finalized == false`
- **Action:** Marks item as finalized and makes it visible in Procurement page
- **Confirmation:** "Are you sure you want to finalize this item? It will be visible in procurement."

#### **Unfinalize Button (🚫) - PMO/Admin Only**
- **Visible When:** `is_finalized == true`
- **Enabled When:** `has_finalized_decision == false`
- **Disabled When:** `has_finalized_decision == true` (shows 🔒 icon)
- **Tooltip When Disabled:** "Cannot unfinalize: Procurement has finalized decision"
- **Confirmation:** "Are you sure you want to unfinalize this item? It will be removed from procurement view."

---

### 3. **Workflow Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│                    PROJECT ITEM LIFECYCLE                    │
└─────────────────────────────────────────────────────────────┘

 1. PM Creates Item
    ↓
 [DRAFT - Not Finalized]
    │
    ├─ Edit: ✅ Enabled
    ├─ Delete: ✅ Enabled
    └─ Finalize Button: ✅ Visible (PMO/Admin)
    ↓
 2. PMO/Admin Clicks FINALIZE
    ↓
 [FINALIZED]
    │
    ├─ Visible in Procurement: ✅ Yes
    ├─ Unfinalize Button: ✅ Enabled (PMO/Admin)
    └─ Edit/Delete: ✅ Enabled (if no procurement options)
    ↓
 3. Procurement Team Adds Options
    ↓
 [FINALIZED + Has Procurement Options]
    │
    ├─ Edit: ❌ Disabled
    ├─ Delete: ❌ Disabled
    └─ Unfinalize Button: ✅ Still Enabled (PMO/Admin)
    ↓
 4. Procurement Creates Finalized Decision
    ↓
 [LOCKED - Procurement Finalized]
    │
    ├─ Edit: ❌ Disabled
    ├─ Delete: ❌ Disabled
    └─ Unfinalize Button: ❌ Disabled (🔒 Locked)
```

---

## Finance Page Features

The Finance page has **three main tabs**:

### **Tab 1: Budget Management**

#### **Features:**
- Create monthly budget allocations
- Support for multi-currency budgets (USD, IRR, EUR)
- Track budget by date
- Edit and delete budget entries

#### **Budget Data Fields:**
- **Budget Date:** Month for which budget is allocated
- **Available Budget:** Total budget in base currency
- **Multi-Currency Budget:** JSON object with currency-specific allocations
  ```json
  {
    "USD": 300000.00,
    "IRR": 12000000000.00,
    "EUR": 250000.00
  }
  ```

#### **Current Seeded Data:**
- **19 months** of budget data (6 months history + 12 months future)
- Random budget amounts between:
  - USD: $300,000 - $400,000
  - IRR: 12-17 billion Rials
  - EUR: €250,000 - €330,000

---

### **Tab 2: Finalized Decisions**

This tab displays all procurement decisions that have been finalized by the Finance/Optimization team.

#### **Data Source:**
- Table: `finalized_decisions`
- **Current Count:** 145 decisions

#### **Decision Breakdown:**
```
Status Distribution:
├─ ORDERED:     60 decisions (41%)
├─ IN_TRANSIT:  54 decisions (37%)
└─ DELIVERED:   31 decisions (21%)

Delivery Status:
├─ AWAITING_DELIVERY: 58 (40%)
├─ IN_TRANSIT:        44 (30%)
└─ DELIVERED:         43 (30%)

Currency Distribution:
├─ USD: 98 decisions (68%)
└─ EUR: 47 decisions (32%)
```

#### **Features:**
- View all finalized procurement decisions
- Track invoice data (38 items have actual invoice data - 26%)
- Track payment data (26 items have payment data - 18%)
- Filter by project, status, or date
- Export to Excel

---

### **Tab 3: Currency & Exchange Rates**

This tab is imported from the **Currency Management Page** and provides comprehensive currency and exchange rate management.

---

## Exchange Rate Management

### **1. Currency Setup**

#### **Active Currencies:**
- **USD** - United States Dollar
- **IRR** - Iranian Rial
- **EUR** - Euro

#### **Currency Fields:**
- `code`: 3-letter currency code (e.g., USD, IRR, EUR)
- `name`: Full currency name
- `symbol`: Currency symbol (e.g., $, ﷼, €)
- `is_base_currency`: Whether this is the base currency (usually IRR)
- `is_active`: Whether currency is currently in use
- `decimal_places`: Number of decimal places (2 for USD/EUR, 0 for IRR)

---

### **2. Exchange Rates**

#### **Current Exchange Rates (as of Oct 20, 2025):**

| From | To  | Rate           | Description                    |
|------|-----|----------------|--------------------------------|
| USD  | IRR | 42,000.00      | 1 USD = 42,000 Rials          |
| IRR  | USD | 0.000024       | 1 Rial = 0.000024 USD         |
| USD  | EUR | 0.92           | 1 USD = 0.92 Euro             |
| EUR  | USD | 1.09           | 1 Euro = 1.09 USD             |
| EUR  | IRR | 45,650.00      | 1 Euro = 45,650 Rials         |
| IRR  | EUR | 0.000022       | 1 Rial = 0.000022 Euro        |

#### **Exchange Rate Fields:**
- `date`: The date the rate is effective
- `from_currency`: Source currency code
- `to_currency`: Target currency code
- `rate`: Conversion rate
- `is_active`: Whether the rate is currently active

---

### **3. How Exchange Rates Work**

#### **In Procurement:**
When creating a procurement option:
1. Supplier quotes price in their currency (USD, EUR, or IRR)
2. System automatically converts to base currency (IRR) using latest exchange rate
3. `base_cost` is stored in IRR for comparison
4. Original currency and amount are preserved:
   - `base_cost_currency` (e.g., "USD")
   - `base_cost_amount` (original amount)

#### **In Finance/Decisions:**
When finalizing a decision:
1. `final_cost_currency` stores the currency used
2. `final_cost_amount` stores the amount in that currency
3. System can convert to any currency for reporting

#### **Adding/Updating Exchange Rates:**
1. **Navigate to:** Finance → Currency & Exchange Rates tab
2. **Add New Rate:**
   - Click "Add Exchange Rate"
   - Select from/to currencies
   - Enter rate
   - Set effective date
3. **Update Rate:**
   - Edit existing rate
   - System maintains history

---

## Complete Workflow

### **Scenario: Adding a New Project Item Through to Procurement Finalization**

#### **Step 1: PM Creates Item**
```
User: pm1 (Project Manager)
Page: Projects → Select Project → Project Items
Action: Click "Add Item"
Fields:
  - Item Code: AUTO-SRV-001
  - Item Name: Dell PowerEdge R750 Server
  - Quantity: 5
  - Delivery Options: [2025-11-15, 2025-11-30]
  - Description: Production database server
Status: DRAFT (is_finalized = false)
```

**Available Actions:**
- ✅ Edit
- ✅ Delete
- ✅ View
- ✅ Manage Delivery Options

---

#### **Step 2: PMO Finalizes Item**
```
User: pmo1 (PMO User) or admin
Page: Projects → Select Project → Project Items
Action: Click ✅ Finalize button
Confirmation: "Are you sure you want to finalize this item? It will be visible in procurement."
Result:
  - is_finalized = true
  - finalized_by = pmo1's user ID
  - finalized_at = current timestamp
  - Item now appears in Procurement page
```

**Available Actions:**
- ❌ Edit (if procurement options exist)
- ❌ Delete (if procurement options exist)
- ✅ View
- ✅ Manage Delivery Options
- ✅ Unfinalize (PMO/Admin) - if no finalized decision

---

#### **Step 3: Procurement Adds Options**
```
User: proc1 (Procurement User)
Page: Procurement
Action: Search for item "AUTO-SRV-001"
Action: Click "Add Option"
Result:
  - procurement_options_count = 1 (then 2, 3, etc.)
  - Edit/Delete buttons become disabled on Project Items page
```

**Procurement Options Example:**
| Supplier | Price (USD) | Lead Time | Status |
|----------|-------------|-----------|--------|
| Dell Direct | $8,500 | 30 days | Proposed |
| CDW | $8,750 | 20 days | Proposed |
| Insight | $8,400 | 35 days | Proposed |

---

#### **Step 4: Finance Runs Optimization**
```
User: finance1 (Finance User)
Page: Optimization
Action: Click "Run Optimization"
Config:
  - Max Time Slots: 24
  - Time Limit: 300 seconds
Result:
  - System selects best option (e.g., Insight - $8,400)
  - Creates optimization run record
```

---

#### **Step 5: Finance Finalizes Decision**
```
User: finance1
Page: Optimization → Review Results
Action: Click "Finalize All Decisions"
Result:
  - Creates record in finalized_decisions table
  - Sets project_item.has_finalized_decision = true
  - Unfinalize button becomes locked (🔒) on Project Items page
```

**Finalized Decision Data:**
```sql
INSERT INTO finalized_decisions (
  project_id: 1,
  project_item_id: 123,
  item_code: 'AUTO-SRV-001',
  procurement_option_id: 456,
  purchase_date: '2025-10-25',
  delivery_date: '2025-11-30',
  quantity: 5,
  final_cost: 42000.00,
  final_cost_currency: 'USD',
  status: 'ORDERED',
  delivery_status: 'AWAITING_DELIVERY'
)
```

---

#### **Step 6: Item is Now Locked**
```
Page: Projects → Select Project → Project Items
Status: LOCKED (has_finalized_decision = true)
```

**Available Actions:**
- ❌ Edit (disabled - has procurement options)
- ❌ Delete (disabled - has procurement options)
- ✅ View
- ✅ Manage Delivery Options
- 🔒 Unfinalize (locked - procurement has finalized)

**Visual Indicators:**
- Chip: "FINALIZED" (green, with ✅ icon)
- Unfinalize button shows 🔒 icon
- Tooltip: "Cannot unfinalize: Procurement has finalized decision"

---

## API Endpoints

### **Project Items**

```http
GET    /items/project/{project_id}
POST   /items/
PUT    /items/{item_id}
DELETE /items/{item_id}
PUT    /items/{item_id}/finalize
PUT    /items/{item_id}/unfinalize
GET    /items/finalized
```

### **Finalized Decisions**

```http
GET    /decisions/
POST   /decisions/
PUT    /decisions/{decision_id}
DELETE /decisions/{decision_id}
GET    /decisions/finalized
```

### **Budget Data**

```http
GET    /finance/budget/
POST   /finance/budget/
PUT    /finance/budget/{budget_date}
DELETE /finance/budget/{budget_date}
```

### **Exchange Rates**

```http
GET    /currencies/
POST   /currencies/
PUT    /currencies/{currency_id}
GET    /currencies/exchange-rates/
POST   /currencies/exchange-rates/
PUT    /currencies/exchange-rates/{rate_id}
GET    /currencies/convert
```

---

## Database Summary

### **Current Data Volumes:**

```
┌──────────────────────────┬─────────┐
│ Component                │ Count   │
├──────────────────────────┼─────────┤
│ Currencies               │ 3       │
│ Exchange Rates           │ 6       │
│ Users                    │ 6       │
│ Items Master             │ 145     │
│ Projects                 │ 12      │
│ Project Items (Total)    │ 1,160   │
│ Project Items (Finalized)│ 1,160   │
│ Procurement Options      │ 1,009   │
│ Finalized Decisions      │ 145     │
│ Budget Data              │ 19      │
└──────────────────────────┴─────────┘

Average Procurement Options per Item: 6.96
Multi-Currency Support: USD, IRR, EUR
```

---

## User Permissions

### **Project Items:**

| Action      | PM  | PMO | Admin | Procurement | Finance |
|-------------|-----|-----|-------|-------------|---------|
| Create      | ✅  | ❌  | ✅    | ❌          | ❌      |
| View        | ✅* | ✅  | ✅    | ✅          | ✅      |
| Edit        | ✅**| ❌  | ❌    | ❌          | ❌      |
| Delete      | ✅**| ❌  | ❌    | ❌          | ❌      |
| Finalize    | ❌  | ✅  | ✅    | ❌          | ❌      |
| Unfinalize  | ❌  | ✅***| ✅***| ❌          | ❌      |

\* PM can only view items from their assigned projects  
\** Only if `procurement_options_count == 0`  
\*** Only if `has_finalized_decision == false`

---

## Troubleshooting

### **"Cannot unfinalize" Error**

**Problem:** Unfinalize button is disabled (🔒)

**Reason:** Procurement team has created a finalized decision for this item

**Solution:**
1. Contact procurement team
2. Ask them to revert their decision first
3. Delete the entry from `finalized_decisions` table
4. Then you can unfinalize the item

---

### **"Cannot edit/delete" Error**

**Problem:** Edit/Delete buttons are disabled

**Reason:** Item has procurement options

**Solution:**
1. Go to Procurement page
2. Find the item by item code
3. Delete all procurement options
4. Then you can edit/delete the item

---

### **Finance Page Shows No Data**

**Problem:** Finance page is empty

**Reason:** No finalized decisions exist

**Solution:**
1. Finalize project items (PMO/Admin)
2. Procurement team creates options
3. Finance runs optimization
4. Finance finalizes decisions

---

## Best Practices

1. **Always finalize items** before procurement starts working on them
2. **Don't unfinalize items** with procurement options unless absolutely necessary
3. **Use exchange rates** consistently - update them regularly
4. **Track budget monthly** to ensure adequate funds
5. **Review finalized decisions** regularly for invoice and payment tracking

---

## Technical Notes

### **Backend Checks:**
- `/items/{item_id}/unfinalize` checks for `finalized_decisions` before allowing unfinalize
- `/items/{item_id}` (PUT/DELETE) checks for `procurement_options` before allowing changes
- `/items/project/{project_id}` (GET) returns enriched data with:
  - `procurement_options_count`
  - `has_finalized_decision`

### **Frontend Logic:**
- Edit button: `disabled={item.procurement_options_count > 0}`
- Delete button: `disabled={item.procurement_options_count > 0}`
- Unfinalize button: `disabled={item.has_finalized_decision}`
- Icon toggles: ✅ Finalize / 🚫 Unfinalize / 🔒 Locked

---

## Version History

| Version | Date       | Changes                                    |
|---------|------------|--------------------------------------------|
| 1.0.0   | Oct 20     | Initial document                           |
| 1.1.0   | Oct 21     | Added unfinalize feature, updated workflow |

---

**For More Information:**
- See [PLATFORM_OVERVIEW.md](./PLATFORM_OVERVIEW.md) for complete system documentation
- See [USER_GUIDE.md](./USER_GUIDE.md) for end-user instructions
- See [ADMIN_GUIDE.md](./ADMIN_GUIDE.md) for administrative procedures

