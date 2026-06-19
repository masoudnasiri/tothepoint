# Decision Lifecycle Management - Implementation Status

## **OVERVIEW**

This document tracks the implementation of the advanced Decision Lifecycle Management system with interactive workbench.

---

## **COMPLETED ✅**

### Phase 1: Backend Models & Schemas

#### 1.1 Enhanced FinalizedDecision Model ✅
**File:** `backend/app/models.py`

**New Fields Added:**
```python
# Lifecycle Management
status = Column(String(20), default='PROPOSED', index=True)
# Values: 'PROPOSED', 'LOCKED', 'REVERTED'

# Flexible Invoicing
invoice_timing_type = Column(String(20), default='ABSOLUTE')
# Values: 'ABSOLUTE', 'RELATIVE'
invoice_issue_date = Column(Date, nullable=True)  # For ABSOLUTE
invoice_days_after_delivery = Column(Integer, nullable=True)  # For RELATIVE

# Finalization Tracking
finalized_at = Column(DateTime, nullable=True)
finalized_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
```

**Benefits:**
- Track decision lifecycle from proposal to locked to reverted
- Flexible invoice timing (absolute date or relative days)
- Audit trail for who locked decisions and when

#### 1.2 Updated Schemas ✅
**File:** `backend/app/schemas.py`

**New Schemas:**
```python
class FinalizedDecisionBase:
    # ... existing fields
    status: str = 'PROPOSED'  # PROPOSED, LOCKED, REVERTED
    invoice_timing_type: str = 'ABSOLUTE'  # ABSOLUTE, RELATIVE
    invoice_issue_date: Optional[date]
    invoice_days_after_delivery: Optional[int]

class FinalizeDecisionsRequest:
    decision_ids: List[int]
    finalize_all: bool = False

class DecisionStatusUpdate:
    status: str  # PROPOSED, LOCKED, REVERTED
    notes: Optional[str]
```

---

## **IN PROGRESS 🔄**

### Phase 2: Optimization Engine Enhancement

#### 2.1 Exclude Locked Items from Re-Optimization (TODO)
**File:** `backend/app/optimization_engine.py`

**Required Changes:**

```python
async def _load_data(self):
    """Load optimization data, excluding locked items"""
    
    # Step 1: Get all locked decisions
    locked_query = await self.db.execute(
        select(FinalizedDecision.project_id, FinalizedDecision.item_code)
        .where(FinalizedDecision.status == 'LOCKED')
    )
    locked_items = {(d.project_id, d.item_code) for d in locked_query.all()}
    
    # Step 2: Load items, then filter out locked ones
    items_result = await self.db.execute(
        select(ProjectItem)
        .join(Project)
        .where(Project.is_active == True)
    )
    all_items = items_result.scalars().all()
    
    # Filter in Python to exclude locked items
    self.project_items = [
        item for item in all_items
        if (item.project_id, item.item_code) not in locked_items
    ]
    
    logger.info(f"Excluded {len(all_items) - len(self.project_items)} locked items from optimization")
```

**Impact:**
- LOCKED decisions are preserved across optimization runs
- Only PROPOSED/REVERTED items are re-optimized
- Allows incremental decision-making

---

### Phase 3: Backend API Endpoints

#### 3.1 Modify POST /decisions ✅ (Partially)
**File:** `backend/app/routers/decisions.py`

**Status:** Existing endpoint needs minor updates to handle new fields

**Changes Needed:**
```python
@router.post("/", response_model=dict)
async def save_optimization_results(
    decisions: List[FinalizedDecisionCreate],
    current_user: User = Depends(require_pm()),
    db: AsyncSession = Depends(get_db)
):
    """Save decisions with new lifecycle fields"""
    # Decision creation already handles new fields via Pydantic schema
    # No code changes needed - schemas handle it automatically
```

#### 3.2 Create POST /decisions/finalize (TODO)
**File:** `backend/app/routers/decisions.py`

**Purpose:** Lock decisions and generate cash flow events

**Implementation:**
```python
from datetime import timedelta

@router.post("/finalize", response_model=dict)
async def finalize_decisions(
    request: FinalizeDecisionsRequest,
    current_user: User = Depends(require_pm()),
    db: AsyncSession = Depends(get_db)
):
    """Finalize (lock) decisions and create cash flow events"""
    
    # Get decisions to finalize
    query = select(FinalizedDecision).where(FinalizedDecision.id.in_(request.decision_ids))
    result = await db.execute(query)
    decisions = result.scalars().all()
    
    finalized_count = 0
    cashflow_events_created = 0
    
    for decision in decisions:
        if decision.status != 'PROPOSED':
            continue  # Skip already locked/reverted
        
        # Calculate invoice date
        if decision.invoice_timing_type == 'ABSOLUTE':
            invoice_date = decision.invoice_issue_date
        else:  # RELATIVE
            invoice_date = decision.delivery_date + timedelta(days=decision.invoice_days_after_delivery)
        
        # Update decision status
        decision.status = 'LOCKED'
        decision.finalized_at = datetime.utcnow()
        decision.finalized_by_id = current_user.id
        
        # Generate cash flow events
        # Get procurement option for payment terms
        proc_option = await db.execute(
            select(ProcurementOption).where(ProcurementOption.id == decision.procurement_option_id)
        )
        option = proc_option.scalar_one()
        
        # OUTFLOW events (based on payment terms)
        if option.payment_terms.lower() == 'cash':
            outflow = CashflowEvent(
                related_decision_id=decision.id,
                event_type='outflow',
                event_date=decision.purchase_date,
                amount=decision.final_cost,
                description=f"Payment: {decision.item_code} - {option.supplier_name}"
            )
            db.add(outflow)
            cashflow_events_created += 1
        
        elif 'installment' in option.payment_terms.lower():
            num_installments = 3  # Default or parse from payment_terms
            installment_amount = decision.final_cost / Decimal(num_installments)
            
            for i in range(num_installments):
                installment_date = decision.purchase_date + timedelta(days=30 * i)
                outflow = CashflowEvent(
                    related_decision_id=decision.id,
                    event_type='outflow',
                    event_date=installment_date,
                    amount=installment_amount,
                    description=f"Installment {i+1}/{num_installments}: {decision.item_code}"
                )
                db.add(outflow)
                cashflow_events_created += 1
        
        # INFLOW event (revenue)
        if invoice_date:
            inflow = CashflowEvent(
                related_decision_id=decision.id,
                event_type='inflow',
                event_date=invoice_date,
                amount=decision.final_cost,
                description=f"Revenue: {decision.item_code}"
            )
            db.add(inflow)
            cashflow_events_created += 1
        
        finalized_count += 1
    
    await db.commit()
    
    return {
        "message": "Decisions finalized successfully",
        "finalized_count": finalized_count,
        "cashflow_events_created": cashflow_events_created,
        "finalized_by": current_user.username
    }
```

#### 3.3 Create PUT /decisions/{decision_id}/status (TODO)
**File:** `backend/app/routers/decisions.py`

**Purpose:** Change decision status (e.g., revert locked decisions)

**Implementation:**
```python
@router.put("/{decision_id}/status", response_model=FinalizedDecision)
async def update_decision_status(
    decision_id: int,
    status_update: DecisionStatusUpdate,
    current_user: User = Depends(require_pm()),
    db: AsyncSession = Depends(get_db)
):
    """Update decision status (e.g., LOCKED -> REVERTED)"""
    
    # Get decision
    result = await db.execute(
        select(FinalizedDecision).where(FinalizedDecision.id == decision_id)
    )
    decision = result.scalar_one_or_none()
    
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    old_status = decision.status
    new_status = status_update.status
    
    # If reverting from LOCKED, delete associated cash flow events
    if old_status == 'LOCKED' and new_status == 'REVERTED':
        # Delete cash flow events
        await db.execute(
            delete(CashflowEvent).where(CashflowEvent.related_decision_id == decision_id)
        )
        
        # Clear finalization data
        decision.finalized_at = None
        decision.finalized_by_id = None
    
    # Update status
    decision.status = new_status
    if status_update.notes:
        decision.notes = status_update.notes
    
    await db.commit()
    await db.refresh(decision)
    
    return decision
```

---

### Phase 4: Frontend - Decision Workbench

#### 4.1 Enhanced OptimizationPage (TODO)
**File:** `frontend/src/pages/OptimizationPage.tsx`

**Major UI Changes Required:**

**Two-Panel Layout:**
```typescript
const [stagingArea, setStagingArea] = useState<OptimizationDecision[]>([]);
const [selectedProposal, setSelectedProposal] = useState<number | null>(null);

<Grid container spacing={2}>
  {/* LEFT PANEL: Staging Area */}
  <Grid item xs={12} md={6}>
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6">Immediate Purchases (Staging Area)</Typography>
      <Typography variant="caption" color="textSecondary">
        Items ready to be locked and finalized
      </Typography>
      
      <DataGrid
        rows={stagingArea}
        columns={[
          { field: 'item_code', headerName: 'Item', width: 100 },
          { field: 'supplier_name', headerName: 'Supplier', width: 150 },
          { field: 'final_cost', headerName: 'Cost', width: 100 },
          { 
            field: 'invoice_timing_type', 
            headerName: 'Invoice Timing', 
            width: 150,
            renderCell: (params) => (
              <Select
                value={params.row.invoice_timing_type}
                onChange={(e) => handleInvoiceTypeChange(params.row.id, e.target.value)}
              >
                <MenuItem value="ABSOLUTE">Absolute Date</MenuItem>
                <MenuItem value="RELATIVE">Days After Delivery</MenuItem>
              </Select>
            )
          },
          {
            field: 'invoice_config',
            headerName: 'Invoice Date/Days',
            width: 200,
            renderCell: (params) => {
              if (params.row.invoice_timing_type === 'ABSOLUTE') {
                return (
                  <DatePicker
                    value={params.row.invoice_issue_date}
                    onChange={(date) => handleInvoiceDateChange(params.row.id, date)}
                  />
                );
              } else {
                return (
                  <TextField
                    type="number"
                    value={params.row.invoice_days_after_delivery}
                    onChange={(e) => handleInvoiceDaysChange(params.row.id, e.target.value)}
                    label="Days"
                  />
                );
              }
            }
          },
          {
            field: 'actions',
            headerName: 'Actions',
            width: 100,
            renderCell: (params) => (
              <IconButton onClick={() => removeFromStaging(params.row.id)}>
                <RemoveIcon /> Remove
              </IconButton>
            )
          }
        ]}
      />
      
      <Button
        variant="contained"
        color="primary"
        disabled={stagingArea.length === 0}
        onClick={handleFinalizeStagedPurchases}
        sx={{ mt: 2 }}
      >
        Lock & Finalize Staged Purchases ({stagingArea.length} items)
      </Button>
    </Paper>
  </Grid>
  
  {/* RIGHT PANEL: Optimization Proposals */}
  <Grid item xs={12} md={6}>
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6">Optimization Proposals</Typography>
      
      {results && results.proposals && (
        <Tabs value={selectedProposal || 0} onChange={(e, v) => setSelectedProposal(v)}>
          {results.proposals.map((proposal, idx) => (
            <Tab key={idx} label={proposal.proposal_name} />
          ))}
        </Tabs>
      )}
      
      {results && results.proposals && results.proposals[selectedProposal] && (
        <DataGrid
          rows={results.proposals[selectedProposal].decisions}
          columns={[
            { field: 'item_code', headerName: 'Item', width: 100 },
            { field: 'supplier_name', headerName: 'Supplier', width: 150 },
            { field: 'final_cost', headerName: 'Cost', width: 100 },
            {
              field: 'actions',
              headerName: 'Actions',
              width: 150,
              renderCell: (params) => (
                <Button
                  size="small"
                  onClick={() => moveToStaging(params.row)}
                  disabled={stagingArea.some(item => item.id === params.row.id)}
                >
                  Move to Staging →
                </Button>
              )
            }
          ]}
        />
      )}
    </Paper>
  </Grid>
</Grid>
```

**Handler Functions:**
```typescript
const moveToStaging = (decision: OptimizationDecision) => {
  // Add to staging with default invoice config
  const enhanced = {
    ...decision,
    invoice_timing_type: 'RELATIVE',
    invoice_days_after_delivery: 30,
    invoice_issue_date: null
  };
  setStagingArea([...stagingArea, enhanced]);
};

const removeFromStaging = (id: number) => {
  setStagingArea(stagingArea.filter(item => item.id !== id));
};

const handleFinalizeStagedPurchases = async () => {
  try {
    // First, save decisions as PROPOSED
    const decisionsToSave = stagingArea.map(item => ({
      ...item,
      status: 'PROPOSED'
    }));
    
    const saveResponse = await decisionsAPI.save(decisionsToSave);
    
    // Then, finalize them (LOCK and create cash flows)
    const decision_ids = saveResponse.data.decision_ids;  // Assuming API returns IDs
    await decisionsAPI.finalize({ decision_ids });
    
    // Success!
    setSuccess('Successfully finalized ' + stagingArea.length + ' decisions!');
    setStagingArea([]);
    
  } catch (err) {
    setError('Failed to finalize decisions');
  }
};
```

#### 4.2 New FinalizedDecisionsPage (TODO)
**File:** `frontend/src/pages/FinalizedDecisionsPage.tsx`

**Purpose:** View and manage all finalized decisions

**Implementation:**
```typescript
import React, { useState, useEffect } from 'react';
import { DataGrid } from '@mui/x-data-grid';
import { Button, Chip, Box, Typography } from '@mui/material';
import { decisionsAPI } from '../services/api';

export const FinalizedDecisionsPage: React.FC = () => {
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchDecisions();
  }, []);
  
  const fetchDecisions = async () => {
    const response = await decisionsAPI.list();
    setDecisions(response.data);
    setLoading(false);
  };
  
  const handleRevert = async (decisionId: number) => {
    if (!window.confirm('Revert this decision? Cash flow events will be deleted.')) {
      return;
    }
    
    try {
      await decisionsAPI.updateStatus(decisionId, { status: 'REVERTED' });
      fetchDecisions();  // Refresh
    } catch (err) {
      alert('Failed to revert decision');
    }
  };
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Finalized Decisions
      </Typography>
      
      <DataGrid
        rows={decisions}
        loading={loading}
        columns={[
          { field: 'item_code', headerName: 'Item', width: 120 },
          { field: 'project_code', headerName: 'Project', width: 120 },
          { field: 'supplier_name', headerName: 'Supplier', width: 150 },
          { field: 'final_cost', headerName: 'Cost', width: 120,
            valueFormatter: (params) => `$${params.value.toLocaleString()}`
          },
          { field: 'delivery_date', headerName: 'Delivery', width: 120,
            valueFormatter: (params) => new Date(params.value).toLocaleDateString()
          },
          { field: 'status', headerName: 'Status', width: 120,
            renderCell: (params) => (
              <Chip 
                label={params.value}
                color={
                  params.value === 'LOCKED' ? 'success' :
                  params.value === 'PROPOSED' ? 'warning' :
                  'error'
                }
                size="small"
              />
            )
          },
          { field: 'finalized_at', headerName: 'Finalized', width: 150,
            valueFormatter: (params) => params.value ? new Date(params.value).toLocaleDateString() : '-'
          },
          { field: 'actions', headerName: 'Actions', width: 150,
            renderCell: (params) => (
              params.row.status === 'LOCKED' && (
                <Button 
                  size="small" 
                  color="error"
                  onClick={() => handleRevert(params.row.id)}
                >
                  Revert
                </Button>
              )
            )
          }
        ]}
        autoHeight
        pageSize={25}
      />
    </Box>
  );
};
```

**Add Route:**
```typescript
// In App.tsx
import { FinalizedDecisionsPage } from './pages/FinalizedDecisionsPage';

<Route path="/decisions" element={<FinalizedDecisionsPage />} />
```

**Add Navigation:**
```typescript
// In Layout.tsx
{ text: 'Decisions', icon: <CheckCircle />, path: '/decisions', roles: ['admin', 'pm', 'finance'] }
```

---

## **API Services Update (TODO)**

**File:** `frontend/src/services/api.ts`

```typescript
export const decisionsAPI = {
  list: (params?) => api.get('/decisions', { params }),
  save: (decisions: FinalizedDecisionCreate[]) => api.post('/decisions', decisions),
  finalize: (request: { decision_ids: number[] }) => api.post('/decisions/finalize', request),
  updateStatus: (id: number, update: { status: string, notes?: string }) => 
    api.put(`/decisions/${id}/status`, update),
  get: (id: number) => api.get(`/decisions/${id}`),
  delete: (id: number) => api.delete(`/decisions/${id}`)
};
```

---

## **DEPLOYMENT REQUIREMENTS**

### Database Migration
Since we added new columns to `finalized_decisions`, you need to recreate the database:

```bash
# Stop containers
docker-compose down -v

# Start with fresh database
docker-compose up -d
```

### New Dependencies
All required libraries are already installed:
- ✅ @mui/x-data-grid (may need to install)
- ✅ @mui/x-date-pickers (already installed)

---

## **TESTING CHECKLIST**

### Backend Testing
- [ ] Create PROPOSED decisions
- [ ] Finalize decisions (PROPOSED → LOCKED)
- [ ] Verify cash flow events are created
- [ ] Revert decision (LOCKED → REVERTED)
- [ ] Verify cash flow events are deleted
- [ ] Run optimization with locked items (should exclude them)

### Frontend Testing
- [ ] Run optimization and see proposals
- [ ] Move items to staging area
- [ ] Configure invoice timing (both ABSOLUTE and RELATIVE)
- [ ] Finalize staged purchases
- [ ] View finalized decisions page
- [ ] Revert a locked decision
- [ ] Verify dashboard reflects changes

---

## **NEXT STEPS**

1. ✅ **Models & Schemas Updated** - Ready for database recreation
2. 🔄 **Implement optimization engine filter** - Exclude locked items
3. 🔄 **Implement backend endpoints** - Finalize and status update
4. 🔄 **Build decision workbench UI** - Two-panel interface
5. 🔄 **Build finalized decisions page** - Management interface
6. 🔄 **Test end-to-end workflow** - Complete lifecycle

---

**This system will provide unprecedented control over the procurement decision process!** 🎯

*Status: Models & Schemas Complete, Implementation In Progress*  
*Created: October 8, 2025*

