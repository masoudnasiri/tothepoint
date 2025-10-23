# 🔄 Procurement Workflow Guide

## Overview

This document explains the complete procurement workflow in PDSS, from project creation to final payment tracking.

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PDSS PROCUREMENT WORKFLOW                         │
└─────────────────────────────────────────────────────────────────────┘

PHASE 1: PROJECT SETUP
├── Create Project (PM/PMO)
├── Define Budget & Timeline
└── Add Project Team

PHASE 2: ITEM MANAGEMENT
├── Add Items from Master Catalog (PM/PMO)
│   ├── Select Company & Item
│   ├── Define Quantity
│   ├── Add Delivery Options (Multiple Dates)
│   └── Add Project-Specific Description
├── OR Create Custom Items
└── Review & Organize Items

PHASE 3: ITEM FINALIZATION ⭐ (KEY GATE)
├── PMO/Admin Reviews Items
├── Verifies Completeness
├── Clicks "Finalize Item" Button
└── ✅ Item Now Visible to Procurement Team

PHASE 4: PROCUREMENT OPTIONS
├── Procurement Team Views Finalized Items
├── For Each Item:
│   ├── Create Multiple Supplier Options
│   ├── Define Pricing & Currency
│   ├── Set Lead Times
│   ├── Configure Payment Terms
│   └── Add Bundle Discounts
└── Finalize Procurement Options

PHASE 5: DECISION OPTIMIZATION
├── Finance Runs Optimization Analysis
├── Review Pareto Front
├── Analyze Cost vs Lead Time Trade-offs
├── Perform What-If Scenarios
└── Select Optimal Options

PHASE 6: DECISION FINALIZATION
├── Lock Selected Options
├── Generate Procurement Plan
├── Assign to Procurement Team
└── Create Purchase Orders

PHASE 7: EXECUTION & TRACKING
├── Track Order Status
├── Monitor Delivery Dates
├── Update Invoice Information
├── Track Payments
└── Monitor Cash Flow

PHASE 8: COMPLETION
├── Confirm Delivery
├── Process Payments
├── Update Actual Dates
├── Generate Performance Reports
└── Archive Project Data
```

---

## Detailed Workflow Steps

### Phase 1: Project Setup

**Who:** Project Manager (PM) or PMO

**Steps:**
1. Navigate to **Projects** module
2. Click **Add Project**
3. Fill in project information:
   - **Name:** Clear, descriptive name
   - **Budget:** Total allocated budget
   - **Start Date:** Project kickoff
   - **End Date:** Expected completion
   - **Description:** Project objectives and scope
4. Click **Create**

**Best Practices:**
- Use consistent naming conventions
- Set realistic budgets and timelines
- Include relevant stakeholders in description
- Review budget allocation regularly

---

### Phase 2: Item Management

**Who:** Project Manager (PM) or PMO

#### Method 1: Add from Master Catalog (Recommended)

1. Open project and click **View Items**
2. Click **Add from Master** button
3. Browse or search items by:
   - Company name
   - Item name
   - Category
   - Specifications
4. Select desired item
5. Configure:
   - **Quantity:** Number needed
   - **Delivery Options:** Add multiple possible dates
     - Click date picker
     - Select date
     - Click **Add Date**
     - Repeat for alternative dates
   - **External Purchase:** Check if procured externally
   - **Description:** Project-specific context or requirements
6. Click **Add to Project**

#### Method 2: Create Custom Item

1. Open project and click **View Items**
2. Click **Add Item** button
3. Enter manually:
   - **Item Code:** Unique identifier
   - **Item Name:** Descriptive name
   - **Quantity:** Number needed
   - **Delivery Options:** Required dates
   - **External Purchase:** If applicable
   - **Description:** Full specifications
4. Click **Create**

**Best Practices:**
- Prefer master catalog items (standardized)
- Add multiple delivery date options for flexibility
- Include detailed project-specific descriptions
- Verify quantities carefully
- Consider lead times when setting dates
- Group related items logically

**Common Pitfalls:**
- ❌ Not adding delivery options
- ❌ Creating custom items for catalog items
- ❌ Insufficient description detail
- ❌ Unrealistic delivery dates

---

### Phase 3: Item Finalization (KEY GATE)

**Who:** PMO or Admin ONLY

**Purpose:** Quality gate ensuring items are ready for procurement

#### Finalization Criteria

Before finalizing, verify:
- ✅ Item details are complete and accurate
- ✅ Quantities are confirmed
- ✅ Delivery options are realistic
- ✅ Budget approval obtained
- ✅ Specifications are clear
- ✅ No pending changes

#### Finalization Process

1. Navigate to project items
2. Review each item thoroughly
3. For ready items, click **Finalize** button (✅ icon)
4. Confirm the action in dialog
5. Item status changes to **FINALIZED**
6. Item becomes visible in **Procurement** module

**Important Notes:**
- ⚠️ Only finalized items appear in Procurement
- ⚠️ Finalization creates an audit trail (who/when)
- ⚠️ Items can be un-finalized if needed
- ⚠️ PM cannot finalize - requires PMO/Admin approval

**Best Practices:**
- Review items in batches
- Coordinate with project team before finalizing
- Document any special requirements
- Communicate finalization to procurement team

---

### Phase 4: Procurement Options

**Who:** Procurement Team

#### Viewing Finalized Items

1. Navigate to **Procurement** module
2. See ONLY finalized items (filtered automatically)
3. Items grouped by item code
4. Summary statistics displayed:
   - Total finalized items
   - Number of procurement options
   - Suppliers count
   - Cost totals

#### Creating Procurement Options

For each finalized item:

1. **Click on item code** to expand
2. Click **Add Option** button
3. Fill in supplier information:

**Basic Information:**
- **Supplier Name:** Company name (required)
- **Base Cost:** Unit price before discounts (required)
- **Currency:** Select from configured currencies (required)

**Delivery Information:**
- **Lead Time:** Days from order to delivery
- **Delivery Date:** Choose from item's delivery options
- **Shipping Cost:** Additional freight charges

**Discounts:**
- **Bundle Threshold:** Minimum quantity for discount
- **Bundle Discount %:** Percentage off when threshold met

**Payment Terms:**

*Option A: Cash Payment*
```json
{
  "type": "cash",
  "discount_percent": 2.0  // Early payment discount
}
```

*Option B: Installments*
```json
{
  "type": "installments",
  "schedule": [
    {"due_offset": 0, "percent": 30},    // 30% upfront
    {"due_offset": 30, "percent": 30},   // 30% after 30 days
    {"due_offset": 60, "percent": 40}    // 40% after 60 days
  ]
}
```

4. Click **Create**

#### Creating Multiple Options

**Best Practice:** Create 3-5 options per item for comparison:
- Include various suppliers
- Mix of cost vs lead time trade-offs
- Different payment term options
- Local vs international suppliers

**Example for MRI Scanner:**

| Supplier | Cost | Lead Time | Payment | Notes |
|----------|------|-----------|---------|-------|
| Siemens Direct | $500K | 90 days | Cash, 2% discount | Premium, fast |
| Medical Distributor | $480K | 120 days | Installments | Good balance |
| Import Specialist | $450K | 150 days | Cash | Cheapest, slower |

---

### Phase 5: Decision Optimization

**Who:** Finance Team or Admin

#### Running Optimization

1. Navigate to **Advanced Optimization** module
2. **Select Items** to optimize (can select multiple)
3. **Configure Weights:**
   - Cost Weight: How important is price? (0.0-1.0)
   - Lead Time Weight: How important is speed?
   - Quality Weight: How important is reliability?
   - Payment Terms Weight: How important are favorable terms?
   - **Total must equal 1.0**

4. Click **Run Optimization**

#### Analyzing Results

**Pareto Front:**
- Shows trade-offs between criteria
- Optimal solutions highlighted
- Interactive charts
- Hover for details

**Recommendations:**
- System suggests best options
- Rationale provided
- Alternative options shown
- Risk assessment included

**What-If Analysis:**
- Adjust weights dynamically
- See impact on recommendations
- Compare scenarios
- Export results

#### Decision Criteria

Consider:
- **Budget constraints:** Must stay within budget
- **Timeline requirements:** Can't miss critical dates
- **Risk tolerance:** Reliability vs cost savings
- **Payment capability:** Cash flow considerations
- **Strategic relationships:** Preferred suppliers

---

### Phase 6: Decision Finalization

**Who:** Finance Team or Admin

1. Review optimization results
2. Select optimal option for each item
3. Click **Finalize Decision** button
4. Add decision rationale/notes
5. Confirm finalization

**Result:**
- Decision is locked
- Procurement plan generated
- Purchase order templates created
- Team notifications sent

---

### Phase 7: Execution & Tracking

**Who:** Multiple Roles

#### Procurement Team:
- Create purchase orders
- Send to suppliers
- Track order status
- Coordinate deliveries
- Update system status

#### Finance Team:
1. Navigate to **Finance** module
2. For each item:
   - Track **Invoice Submission Date**
   - Record **Payment Date**
   - Update **Expected Cash In Date**
   - Confirm **Actual Cash In Date**
3. Monitor cash flow forecasts
4. Reconcile accounts

#### Status Updates:
Items progress through:
```
DECIDED → PROCURED → FULFILLED → PAID → CASH_RECEIVED
```

Update status as milestones are reached.

---

### Phase 8: Completion

**Who:** Project Manager, Finance, Admin

#### Project Closeout:

1. **Verify Completion:**
   - All items delivered
   - All payments made
   - All invoices received
   - Cash flow reconciled

2. **Generate Reports:**
   - Project summary
   - Cost analysis (budget vs actual)
   - Timeline analysis (planned vs actual)
   - Supplier performance
   - Lessons learned

3. **Archive:**
   - Export project data
   - Save reports
   - Document lessons learned
   - Archive supporting documents

4. **Review:**
   - Team debrief
   - Process improvements
   - Update master catalog
   - Update supplier ratings

---

## Workflow Rules & Gates

### Required Actions by Role

| Action | Admin | PMO | PM | Procurement | Finance |
|--------|:-----:|:---:|:--:|:-----------:|:-------:|
| Create Project | ✅ | ✅ | ✅ | ❌ | ❌ |
| Add Items | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Finalize Items** | ✅ | ✅ | ❌ | ❌ | ❌ |
| Create Options | ✅ | ❌ | ❌ | ✅ | ❌ |
| Run Optimization | ✅ | ❌ | ❌ | ❌ | ✅ |
| Finalize Decisions | ✅ | ❌ | ❌ | ❌ | ✅ |
| Track Payments | ✅ | ❌ | ❌ | ❌ | ✅ |

### Critical Gates

**Gate 1: Item Finalization**
- **Required:** PMO/Admin approval
- **Criteria:** Complete item information
- **Impact:** Items become visible to Procurement
- **Cannot bypass:** Hard requirement

**Gate 2: Option Finalization**
- **Required:** Procurement team completion
- **Criteria:** All supplier details entered
- **Impact:** Options ready for optimization
- **Can be skipped:** No, but can be edited later

**Gate 3: Decision Finalization**
- **Required:** Finance approval
- **Criteria:** Optimization analysis complete
- **Impact:** Locks decisions, generates POs
- **Cannot bypass:** Hard requirement

---

## Integration Points

### With External Systems

**ERP Integration (Future):**
- Push finalized decisions to ERP
- Sync purchase orders
- Pull payment status
- Sync inventory data

**Supplier Portals (Future):**
- Share order status
- Receive delivery updates
- Track invoices
- Manage documents

**Financial Systems:**
- Export payment schedules
- Import bank transactions
- Reconcile accounts
- Generate financial reports

---

## Performance Metrics

### Track These KPIs:

**Time Metrics:**
- Days from project start to first item finalization
- Days from finalization to procurement options
- Days from options to decision
- Days from decision to delivery

**Cost Metrics:**
- Budget vs actual cost
- Savings from optimization
- Cost per item type
- Supplier cost comparison

**Quality Metrics:**
- On-time delivery rate
- Supplier defect rate
- Process compliance rate
- Decision reversal rate

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Items not visible in Procurement | Not finalized | PMO must finalize items first |
| Can't create procurement options | No finalized items | Wait for PMO finalization |
| Optimization fails | Missing data | Ensure all options have complete data |
| Can't finalize decision | Incomplete options | Complete all required fields |
| Payment tracking issues | Dates not updated | Finance must update dates promptly |

---

## Best Practices Summary

### Do's ✅
- Follow the workflow sequence
- Complete all required fields
- Add multiple delivery options
- Create multiple supplier options
- Run optimization before deciding
- Update statuses promptly
- Document decisions
- Generate regular reports

### Don'ts ❌
- Skip item finalization step
- Create options for non-finalized items
- Rush decision finalization
- Ignore optimization results
- Forget to update payment dates
- Delete items with history
- Bypass approval gates
- Share sensitive data inappropriately

---

*For more information, see:*
- [User Guide](../USER_GUIDE.md)
- [Admin Guide](../ADMIN_GUIDE.md)
- [Platform Overview](../PLATFORM_OVERVIEW.md)

---

*Last Updated: October 20, 2025*

