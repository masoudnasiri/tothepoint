# PM User Permissions & Access Control

## 🔒 Updated Permission Model

PM (Project Manager) users now have **restricted access** to protect sensitive financial data.

---

## ✅ What PM Users CAN Do

### **1. Dashboard Access - Revenue Inflow ONLY**

PM users can:
- ✅ View **Revenue Inflow** data (money coming in from clients)
- ✅ See revenue timing and forecasts
- ✅ Track expected revenue by month
- ✅ View revenue inflow charts
- ✅ Export revenue data to Excel

PM users **CANNOT** see:
- ❌ Budget allocations
- ❌ Payment outflows (supplier payments)
- ❌ Net cash position
- ❌ Cumulative balance
- ❌ Variance analysis

**Why?**
- Protects sensitive budget information
- Prevents unauthorized access to payment data
- PM only needs revenue visibility for project tracking
- Financial decisions remain with Finance team

---

### **2. Optimization Page - View Only**

PM users can:
- ✅ View **Advanced Optimization** page
- ✅ See optimization results and proposals
- ✅ Review recommended decisions
- ✅ View previous optimization runs
- ✅ Access solver information

PM users **CANNOT**:
- ❌ **Run new optimizations** (Finance/Admin only)
- ❌ **Save proposals as decisions** (Finance/Admin only)
- ❌ **Finalize & lock decisions** (Finance/Admin only)
- ❌ Edit decisions
- ❌ Add items to proposals
- ❌ Remove items from proposals
- ❌ Delete optimization results

**Why?**
- Optimization is a financial decision-making process
- Only Finance/Admin should commit to procurement decisions
- PM can view and provide input, but not execute
- Maintains proper approval workflow

---

### **3. Projects & Items - Full Access**

PM users can:
- ✅ View assigned projects
- ✅ Create/edit/delete project items
- ✅ Manage delivery options
- ✅ Update project phases
- ✅ View project status

---

### **4. Finalized Decisions - View Only**

PM users can:
- ✅ View finalized decisions
- ✅ See decision details
- ✅ Track decision status

PM users **CANNOT**:
- ❌ Create finalized decisions
- ❌ **Finalize/lock decisions** (Finance/Admin only)
- ❌ Revert decisions
- ❌ Enter invoice data

---

## 🎯 Role Comparison Matrix

| Feature | PM | Finance | Admin |
|---------|-----|---------|-------|
| **Dashboard** |
| View Revenue Inflow | ✅ | ✅ | ✅ |
| View Budgets | ❌ | ✅ | ✅ |
| View Outflows | ❌ | ✅ | ✅ |
| View Net Position | ❌ | ✅ | ✅ |
| Export Data | ✅ (Inflows only) | ✅ (All) | ✅ (All) |
| **Optimization** |
| Run Optimization | ❌ | ✅ | ✅ |
| View Results | ✅ | ✅ | ✅ |
| Save Proposals | ❌ | ✅ | ✅ |
| Edit Decisions | ❌ | ✅ | ✅ |
| Finalize & Lock | ❌ | ✅ | ✅ |
| Delete Results | ❌ | ✅ | ✅ |
| **Decisions** |
| View Decisions | ✅ | ✅ | ✅ |
| Create Decisions | ❌ | ✅ | ✅ |
| Finalize Decisions | ❌ | ✅ | ✅ |
| Revert Decisions | ❌ | ✅ | ✅ |
| Enter Invoice Data | ❌ | ✅ | ✅ |
| **Projects** |
| View Projects | ✅ (Assigned) | ✅ (All) | ✅ (All) |
| Create Projects | ❌ | ❌ | ✅ |
| Edit Items | ✅ | ✅ | ✅ |
| Manage Phases | ✅ | ✅ | ✅ |
| **Procurement** |
| View Options | ✅ | ✅ | ✅ |
| Create Options | ❌ | ❌ | ✅ (or procurement role) |
| Edit Options | ❌ | ❌ | ✅ (or procurement role) |

---

## 🔧 Implementation Details

### Backend Changes

#### **1. Dashboard Endpoints (`/backend/app/routers/dashboard.py`)**

```python
@router.get("/cashflow")
async def get_cashflow_analysis(...):
    # PM users can only see INFLOW (revenue) events
    if current_user.role == "pm":
        query = query.where(CashflowEvent.event_type == "INFLOW")
    
    # PM users don't see budget data
    if current_user.role in ["finance", "admin"]:
        # Load budgets for finance/admin only
        ...

@router.get("/summary")
async def get_dashboard_summary(...):
    # PM users only see inflow summary
    if current_user.role == "pm":
        return {
            "total_inflow": float(total_inflow),
            "total_outflow": 0,  # Hidden
            "total_budget": 0,   # Hidden
            ...
        }
```

#### **2. Decisions Endpoints (`/backend/app/routers/decisions.py`)**

```python
# CHANGED: PM removed from access
@router.post("/save-proposal")
async def save_proposal_as_decisions(
    current_user: User = Depends(require_finance()),  # Was: require_pm()
    ...
):

# CHANGED: PM removed from access
@router.post("/batch")
async def save_batch_decisions(
    current_user: User = Depends(require_finance()),  # Was: require_pm()
    ...
):

# Already restricted (no change needed)
@router.post("/finalize")
async def finalize_decisions(
    current_user: User = Depends(require_finance()),
    ...
):
```

### Frontend Changes

#### **1. Dashboard (`/frontend/src/pages/DashboardPage.tsx`)**

```typescript
// Detect PM user
const isPM = user?.role === 'pm';

// Show different title
<Typography variant="h4">
  {isPM ? 'Revenue Dashboard' : 'Cash Flow Analysis Dashboard'}
</Typography>

// Show only appropriate cards
{isPM ? (
  // Only Revenue Inflow card
  <StatCard title="Total Revenue Inflow" ... />
) : (
  // All 4 cards (Inflow, Outflow, Net, Balance)
  ...
)}

// Hide columns in table for PM
<TableCell>{!isPM && 'Budget'}</TableCell>
<TableCell>Revenue Inflow</TableCell>
<TableCell>{!isPM && 'Payment Outflow'}</TableCell>
```

#### **2. Advanced Optimization (`/frontend/src/pages/OptimizationPage_enhanced.tsx`)**

```typescript
// Hide save/finalize buttons from PM
{(user?.role === 'finance' || user?.role === 'admin') && (
  <Button>Save Proposal as Decisions</Button>
  <Button>Finalize & Lock Decisions</Button>
)}

// Show read-only message to PM
{user?.role === 'pm' && (
  <Alert>
    PM Access: You can view optimization results but cannot save or finalize decisions.
  </Alert>
)}
```

---

## 📊 Visual Comparison

### **What PM Users See:**

```
Dashboard:
┌────────────────────────────────────────────┐
│  Revenue Dashboard                          │
│                                            │
│  ┌───────────────────┐                    │
│  │ Total Revenue     │                    │
│  │ Inflow: $125,000  │                    │
│  └───────────────────┘                    │
│                                            │
│  Chart: Revenue Inflow by Month           │
│  [Only green bars showing revenue]         │
│                                            │
│  Table:                                    │
│  Month | Revenue Inflow                    │
│  11/25 | $25,000                           │
│  12/25 | $30,000                           │
│  ...                                       │
└────────────────────────────────────────────┘

Advanced Optimization:
┌────────────────────────────────────────────┐
│  Advanced Optimization                      │
│  (Read-Only for PM)                        │
│                                            │
│  Proposals (can view only):                │
│  [💰 Lowest] [🎯 Priority] [⚡ Fast]      │
│                                            │
│  ⚠️  PM Access: You can view results       │
│     but cannot save or finalize decisions  │
│                                            │
│  (No Save or Finalize buttons)             │
└────────────────────────────────────────────┘
```

### **What Finance/Admin Users See:**

```
Dashboard:
┌────────────────────────────────────────────┐
│  Cash Flow Analysis Dashboard              │
│                                            │
│  ┌──────┬──────┬──────┬──────┐            │
│  │Inflow│Outfl│Net  │Final │            │
│  │$125K │$100K│$25K │$150K │            │
│  └──────┴──────┴──────┴──────┘            │
│                                            │
│  Chart: Complete Cash Flow                │
│  [Green (in) + Red (out) + Blue (balance)]│
│                                            │
│  Table:                                    │
│  Month│Budget│Inflow│Outflow│Net│Balance │
│  11/25│$50K  │$25K  │$20K   │$5K│$50K   │
│  ...                                       │
└────────────────────────────────────────────┘

Advanced Optimization:
┌────────────────────────────────────────────┐
│  Advanced Optimization                      │
│  (Full Access)                             │
│                                            │
│  [Run Optimization] [Delete Results]       │
│                                            │
│  Proposals:                                │
│  [Can view, edit, add, remove]             │
│                                            │
│  [Save Proposal as Decisions] ✅           │
│  [Finalize & Lock Decisions] ✅            │
└────────────────────────────────────────────┘
```

---

## 🎯 Use Case Examples

### **Use Case 1: PM Checks Revenue**

```
PM logs in
  ↓
Opens Dashboard
  ↓
Sees: "Revenue Dashboard"
  ↓
Views:
- Total Revenue Inflow: $125,000
- Revenue by month chart
- Revenue inflow table
  ↓
Cannot see:
- Budget amounts
- Payment outflows
- Net positions
```

### **Use Case 2: PM Views Optimization Results**

```
PM logs in
  ↓
Opens "Advanced Optimization"
  ↓
Sees optimization results from Finance team
  ↓
Can review proposals
Can switch between tabs
  ↓
Cannot save or finalize
Sees message: "Contact Finance or Admin users"
  ↓
Reports findings to Finance team
```

### **Use Case 3: Finance User Full Workflow**

```
Finance logs in
  ↓
Opens "Advanced Optimization"
  ↓
Runs optimization (CP_SAT, multiple proposals)
  ↓
Reviews all 5 proposals
  ↓
Edits decisions as needed
  ↓
Saves proposal
  ↓
Finalizes & locks decisions
  ↓
PM can now see revenue impact in dashboard
```

---

## 📝 Permission Changes Summary

### **REMOVED PM Access:**

❌ **Dashboard:**
- Budget data
- Payment outflows
- Net position calculations
- Full financial metrics

❌ **Optimization:**
- Save proposals
- Finalize decisions
- Edit decisions
- Add/remove items

❌ **Decisions:**
- Create finalized decisions
- Lock/unlock decisions
- Revert decisions
- Enter invoice data

### **MAINTAINED PM Access:**

✅ **Dashboard:**
- Revenue inflow data
- Revenue charts
- Revenue tables

✅ **Optimization:**
- View results (read-only)
- See proposals
- Access solver information

✅ **Projects:**
- Manage assigned projects
- Create/edit items
- Manage phases

✅ **Decisions:**
- View finalized decisions
- See decision status

---

## 🛡️ Security Rationale

### **Why These Restrictions?**

**1. Financial Data Protection:**
```
Budget data = Company's financial capacity
Payment data = Supplier pricing & contracts
Net position = Company's financial health

→ Should be restricted to Finance/Admin only
→ PM doesn't need this for project management
```

**2. Decision Authority:**
```
Procurement decisions = Financial commitments
Finalizing decisions = Legal/contractual commitments
Locking decisions = Budget allocation

→ Should require Finance approval
→ PM can recommend, Finance decides
```

**3. Separation of Duties:**
```
PM: Project execution & delivery
Finance: Budget & financial decisions
Admin: System & user management

→ Clear role boundaries
→ Prevents conflicts of interest
→ Maintains audit trail
```

---

## 🎯 Workflow with New Permissions

### **Collaborative Workflow:**

```
Step 1: PM Manages Projects
├─ Creates project items
├─ Sets delivery options
└─ Updates project phases

Step 2: Finance Runs Optimization
├─ Analyzes all projects
├─ Generates proposals
├─ Reviews cost implications
└─ Selects best strategy

Step 3: PM Reviews Results
├─ Opens Advanced Optimization (read-only)
├─ Sees recommended decisions
├─ Reviews delivery timelines
└─ Provides feedback to Finance

Step 4: Finance Finalizes
├─ Incorporates PM feedback
├─ Edits decisions if needed
├─ Saves proposal
└─ Finalizes & locks decisions

Step 5: PM Tracks Revenue
├─ Views Revenue Dashboard
├─ Sees expected inflows
├─ Tracks delivery-to-invoice timing
└─ Monitors revenue realization
```

---

## 📊 API Endpoint Permissions

### **Restricted Endpoints (Finance/Admin ONLY):**

```http
POST   /finance/optimize                # Run optimization
POST   /finance/optimize-enhanced       # Run enhanced optimization
POST   /finance/budget                  # Create budget
PUT    /finance/budget/{date}           # Update budget
DELETE /finance/budget/{date}           # Delete budget
DELETE /finance/optimization-results/{id}  # Delete results

POST   /decisions/save-proposal         # Save proposal
POST   /decisions/batch                 # Save batch
POST   /decisions/finalize              # Finalize decisions
PUT    /decisions/{id}/status          # Update status
POST   /decisions/{id}/actual-invoice  # Enter invoice
```

### **Read-Only for PM:**

```http
GET    /dashboard/cashflow              # Revenue inflow only
GET    /dashboard/summary               # Inflow summary only
GET    /finance/optimization-runs       # View previous runs
GET    /finance/solver-info             # View solver info
GET    /decisions/                      # View decisions
GET    /finance/optimization-results    # View results
```

### **Full Access for PM:**

```http
GET    /projects/                       # View assigned projects
POST   /items/                          # Create project items
PUT    /items/{id}                      # Update items
DELETE /items/{id}                      # Delete items
POST   /phases/project/{id}             # Create phases
PUT    /phases/{id}                     # Update phases
```

---

## 🧪 Testing Permission Changes

### **Test as PM User:**

```powershell
# 1. Login as PM
# Username: pm_user (or create one)
# Password: [password]

# 2. Test Dashboard
- Navigate to Dashboard
- ✅ Should see "Revenue Dashboard"
- ✅ Should see only Revenue Inflow card
- ✅ Chart shows only green bars (inflow)
- ✅ Table shows only Month & Revenue columns
- ❌ Should NOT see Budget, Outflow, Net columns

# 3. Test Advanced Optimization
- Navigate to Advanced Optimization
- ✅ Can view the page
- ✅ Can see optimization results (if Finance ran one)
- ✅ Can switch between proposal tabs
- ❌ Should NOT see "Run Optimization" button
- ❌ Should NOT see "Save Proposal" button
- ❌ Should NOT see "Finalize & Lock" button
- ✅ Should see info message: "PM Access: You can view..."

# 4. Test Finalized Decisions
- Navigate to Finalized Decisions
- ✅ Can view decisions
- ❌ Should NOT see "Finalize" button
- ❌ Should NOT be able to enter invoice data
```

### **Test as Finance User:**

```powershell
# 1. Login as Finance
- Navigate to Dashboard
- ✅ Should see "Cash Flow Analysis Dashboard"
- ✅ Should see all 4 cards
- ✅ Chart shows all data
- ✅ Table shows all columns

# 2. Advanced Optimization
- ✅ Can run optimization
- ✅ Can save proposals
- ✅ Can finalize & lock
- ✅ Full access to all features

# 3. Finalized Decisions
- ✅ Can create decisions
- ✅ Can finalize/lock
- ✅ Can enter invoice data
- ✅ Full access
```

---

## 📋 Migration Guide

### **If You Have Existing PM Users:**

**Option 1: Keep PM Users (Recommended)**
```
- Existing PM users automatically get new restrictions
- They keep project management capabilities
- Revenue visibility maintained
- Financial data now protected
```

**Option 2: Upgrade Some PMs to Finance**
```sql
-- If some PMs need full financial access:
UPDATE users 
SET role = 'finance' 
WHERE username IN ('pm_user1', 'pm_user2');
```

**Option 3: Create New Roles (Future Enhancement)**
```
Consider creating:
- pm_senior: PM + some financial view
- pm_restricted: PM + no financial data
- finance_analyst: View only
```

---

## 🔍 Verification Queries

### **Check User Roles:**

```sql
SELECT username, role FROM users;
```

### **Check What PM Can See:**

```sql
-- Revenue inflows only
SELECT 
    event_date,
    amount,
    description
FROM cashflow_events
WHERE event_type = 'INFLOW'
  AND is_cancelled = false
ORDER BY event_date;
```

### **Check What PM Cannot See:**

```sql
-- Budget data (restricted)
SELECT * FROM budget_data;

-- Payment outflows (restricted)
SELECT * FROM cashflow_events WHERE event_type = 'OUTFLOW';
```

---

## ✅ Permission Change Checklist

After updating:

**Backend:**
- [x] Dashboard `/cashflow` filters INFLOW for PM
- [x] Dashboard `/summary` returns limited data for PM
- [x] `/save-proposal` requires finance role
- [x] `/batch` requires finance role
- [x] `/finalize` already requires finance role

**Frontend:**
- [x] Dashboard shows limited cards for PM
- [x] Dashboard hides sensitive columns for PM
- [x] Dashboard shows PM access notice
- [x] Advanced Optimization hides buttons for PM
- [x] Advanced Optimization shows read-only message for PM

**Documentation:**
- [x] Permission model documented
- [x] Role comparison matrix created
- [x] Testing procedures provided

---

## 🎉 Summary

**PM Users Now Have:**
- ✅ **Appropriate Access:** Revenue visibility for project tracking
- ✅ **Read-Only Optimization:** Can see Finance's decisions
- ✅ **Project Management:** Full control over assigned projects
- ❌ **No Financial Control:** Cannot commit budget or make procurement decisions

**Finance/Admin Users:**
- ✅ **Full Access:** All features unchanged
- ✅ **Financial Control:** Complete decision-making authority
- ✅ **Audit Trail:** All decisions tracked with user ID

**System Benefits:**
- ✅ **Separation of Duties:** Clear role boundaries
- ✅ **Data Protection:** Sensitive financial data secured
- ✅ **Compliance:** Proper approval workflow
- ✅ **Audit Trail:** Who did what, when

**Your procurement system now has enterprise-grade access control! 🔒**

