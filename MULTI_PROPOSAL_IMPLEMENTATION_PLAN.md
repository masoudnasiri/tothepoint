# Multi-Proposal Optimization & Cash Flow Enhancement - Implementation Plan

## **STATUS:** Ready to Implement

This document outlines the complete implementation of three major enhancements:
1. Multi-proposal optimization (3 strategic alternatives)
2. Decision finalization UI with invoice date input
3. Enhanced cash flow dashboard with data table and Excel export

---

## **PHASE 1: Multi-Proposal Optimization**

### Backend Changes

#### 1.1 Schemas Updated ✅
**File:** `backend/app/schemas.py`

**New Schemas Added:**
```python
class OptimizationDecision(BaseModel):
    project_id: int
    project_code: str
    item_code: str
    item_name: str
    procurement_option_id: int
    supplier_name: str
    purchase_date: date
    delivery_date: date
    quantity: int
    unit_cost: Decimal
    final_cost: Decimal
    payment_terms: str

class OptimizationProposal(BaseModel):
    proposal_name: str
    strategy_type: str  # BALANCED, LOWEST_COST, SMOOTH_CASHFLOW
    total_cost: Decimal
    weighted_cost: Decimal
    status: str
    items_count: int
    decisions: List[OptimizationDecision]
    summary_notes: Optional[str] = None

class OptimizationRunResponse(BaseModel):
    run_id: uuid.UUID
    run_timestamp: datetime
    status: str
    execution_time_seconds: float
    proposals: List[OptimizationProposal]  # NEW: Multiple proposals
    message: Optional[str] = None
```

#### 1.2 Optimization Engine Refactor (TODO)
**File:** `backend/app/optimization_engine.py`

**Changes Needed:**

1. **Add Strategy Constants:**
```python
STRATEGY_BALANCED = "BALANCED"
STRATEGY_LOWEST_COST = "LOWEST_COST"  
STRATEGY_SMOOTH_CASHFLOW = "SMOOTH_CASHFLOW"
PENALTY_PER_DAY_EARLY = 100  # Penalty for early cash outflow
```

2. **Refactor `run_optimization` to Generate 3 Proposals:**
```python
async def run_optimization(self, request):
    self.start_time = datetime.now()
    await self._load_data()
    
    proposals = []
    
    # Proposal 1: Balanced (Priority-Weighted)
    proposal1 = await self._solve_model(STRATEGY_BALANCED, request)
    if proposal1:
        proposals.append(proposal1)
    
    # Proposal 2: Lowest Cost (No Priority Weighting)
    proposal2 = await self._solve_model(STRATEGY_LOWEST_COST, request)
    if proposal2:
        proposals.append(proposal2)
    
    # Proposal 3: Cash Flow Smoothing (Defer Payments)
    proposal3 = await self._solve_model(STRATEGY_SMOOTH_CASHFLOW, request)
    if proposal3:
        proposals.append(proposal3)
    
    execution_time = (datetime.now() - self.start_time).total_seconds()
    
    return OptimizationRunResponse(
        run_id=uuid.UUID(self.run_id),
        run_timestamp=self.start_time,
        status="SUCCESS" if proposals else "FAILED",
        execution_time_seconds=execution_time,
        proposals=proposals,
        message=f"Generated {len(proposals)} strategic proposals"
    )
```

3. **Create `_solve_model` Helper:**
```python
async def _solve_model(self, strategy_type: str, request) -> Optional[OptimizationProposal]:
    """Solve with a specific objective strategy"""
    # Rebuild model for each strategy
    self._build_model(request.max_time_slots)
    self._set_objective(strategy_type)  # Modified to accept strategy
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = request.time_limit_seconds
    status = solver.Solve(self.model)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        return self._parse_solution_to_proposal(solver, strategy_type)
    
    return None
```

4. **Modify `_set_objective` to Support Strategies:**
```python
def _set_objective(self, strategy_type: str):
    """Build objective function based on strategy"""
    objective_vars = []
    objective_coeffs = []
    
    for item in self.project_items:
        project = self.projects[item.project_id]
        
        for option_id, option in self.procurement_options.items():
            if option.item_code != item.item_code:
                continue
            
            for time_slot in range(1, self.max_time_slots + 1):
                key = (item.id, option_id, time_slot)
                if key not in self.variables:
                    continue
                
                var = self.variables[key]
                total_cost = option.base_cost * item.quantity
                
                if strategy_type == STRATEGY_BALANCED:
                    # Priority-weighted cost
                    weight_factor = (11 - project.priority_weight)
                    coefficient = int(total_cost * 100 * weight_factor)
                
                elif strategy_type == STRATEGY_LOWEST_COST:
                    # Pure cost minimization
                    coefficient = int(total_cost * 100)
                
                elif strategy_type == STRATEGY_SMOOTH_CASHFLOW:
                    # Cost + penalty for early payments
                    weight_factor = (11 - project.priority_weight)
                    cost_term = int(total_cost * 100 * weight_factor)
                    
                    # Penalty for earlier time slots (encourage deferring)
                    early_penalty = int(PENALTY_PER_DAY_EARLY * 100 * (self.max_time_slots - time_slot))
                    coefficient = cost_term + early_penalty
                
                objective_vars.append(var)
                objective_coeffs.append(coefficient)
    
    # Minimize total
    self.model.Minimize(
        sum(var * coeff for var, coeff in zip(objective_vars, objective_coeffs))
    )
```

5. **Create `_parse_solution_to_proposal` Method:**
```python
def _parse_solution_to_proposal(self, solver, strategy_type: str) -> OptimizationProposal:
    """Parse solver solution into a proposal"""
    decisions = []
    total_cost = Decimal(0)
    weighted_cost = Decimal(0)
    
    for item in self.project_items:
        project = self.projects[item.project_id]
        
        for option_id, option in self.procurement_options.items():
            for time_slot in range(1, self.max_time_slots + 1):
                key = (item.id, option_id, time_slot)
                if key not in self.variables:
                    continue
                
                if solver.Value(self.variables[key]) == 1:
                    # This decision was selected
                    cost = option.base_cost * item.quantity
                    total_cost += cost
                    weighted_cost += cost * Decimal(11 - project.priority_weight)
                    
                    # Map time slot to actual date
                    purchase_date = self._map_slot_to_date(time_slot)
                    delivery_date = purchase_date + timedelta(days=option.lomc_lead_time)
                    
                    decisions.append(OptimizationDecision(
                        project_id=project.id,
                        project_code=project.project_code,
                        item_code=item.item_code,
                        item_name=item.item_name,
                        procurement_option_id=option.id,
                        supplier_name=option.supplier_name,
                        purchase_date=purchase_date,
                        delivery_date=delivery_date,
                        quantity=item.quantity,
                        unit_cost=option.base_cost,
                        final_cost=cost,
                        payment_terms=option.payment_terms
                    ))
    
    # Map strategy to user-friendly names
    names = {
        STRATEGY_BALANCED: "Balanced Strategy (Priority-Weighted)",
        STRATEGY_LOWEST_COST: "Lowest Cost (Budget-Focused)",
        STRATEGY_SMOOTH_CASHFLOW: "Cash Flow Optimized (Deferred Payments)"
    }
    
    notes = {
        STRATEGY_BALANCED: "Balances cost and project priorities",
        STRATEGY_LOWEST_COST: "Minimizes total procurement cost",
        STRATEGY_SMOOTH_CASHFLOW: "Defers payments to smooth cash flow"
    }
    
    return OptimizationProposal(
        proposal_name=names[strategy_type],
        strategy_type=strategy_type,
        total_cost=total_cost,
        weighted_cost=weighted_cost,
        status="Optimal",
        items_count=len(decisions),
        decisions=decisions,
        summary_notes=notes[strategy_type]
    )
```

### Frontend Changes

#### 1.3 Update OptimizationPage (TODO)
**File:** `frontend/src/pages/OptimizationPage.tsx`

**Major UI Changes:**

1. **Add Tabs for Proposals:**
```typescript
const [selectedProposal, setSelectedProposal] = useState<number>(0);
const [selectedTab, setSelectedTab] = useState<number>(0);

// After optimization completes
{results && results.proposals && results.proposals.length > 0 && (
  <>
    <Typography variant="h5" sx={{ mt: 4, mb: 2 }}>
      Strategic Proposals
    </Typography>
    
    <Tabs value={selectedTab} onChange={(e, v) => setSelectedTab(v)}>
      {results.proposals.map((proposal, idx) => (
        <Tab 
          key={idx}
          label={proposal.proposal_name}
          icon={<Chip label={`$${proposal.total_cost.toLocaleString()}`} size="small" />}
        />
      ))}
    </Tabs>
    
    {results.proposals.map((proposal, idx) => (
      <TabPanel value={selectedTab} index={idx} key={idx}>
        <ProposalView 
          proposal={proposal}
          onSelect={() => setSelectedProposal(idx)}
        />
      </TabPanel>
    ))}
  </>
)}
```

2. **Proposal Summary Cards:**
```typescript
<Grid container spacing={2} sx={{ mb: 3 }}>
  <Grid item xs={12} md={4}>
    <Card>
      <CardContent>
        <Typography color="textSecondary">Total Cost</Typography>
        <Typography variant="h4">${proposal.total_cost.toLocaleString()}</Typography>
      </CardContent>
    </Card>
  </Grid>
  <Grid item xs={12} md={4}>
    <Card>
      <CardContent>
        <Typography color="textSecondary">Weighted Cost</Typography>
        <Typography variant="h4">${proposal.weighted_cost.toLocaleString()}</Typography>
      </CardContent>
    </Card>
  </Grid>
  <Grid item xs={12} md={4}>
    <Card>
      <CardContent>
        <Typography color="textSecondary">Items</Typography>
        <Typography variant="h4">{proposal.items_count}</Typography>
      </CardContent>
    </Card>
  </Grid>
</Grid>
```

---

## **PHASE 2: Decision Finalization UI**

### Frontend Changes

#### 2.1 Editable Data Grid with Invoice Date (TODO)
**File:** `frontend/src/pages/OptimizationPage.tsx`

**Requirements:**
1. Use Material-UI DataGridPro or custom editable table
2. Add "Invoice Issue Date" column with DatePicker
3. Collect data and send to POST /decisions

```typescript
const [editableDecisions, setEditableDecisions] = useState<any[]>([]);

// When proposal is selected
const handleSelectProposal = (proposalIndex: number) => {
  const proposal = results.proposals[proposalIndex];
  // Add invoice_issue_date field to each decision (default: delivery_date + 30 days)
  const decisionsWithInvoiceDate = proposal.decisions.map(d => ({
    ...d,
    invoice_issue_date: addDays(new Date(d.delivery_date), 30).toISOString().split('T')[0]
  }));
  setEditableDecisions(decisionsWithInvoiceDate);
  setSelectedProposal(proposalIndex);
};

// Data Grid with editable invoice_issue_date
<DataGrid
  rows={editableDecisions}
  columns={[
    { field: 'item_code', headerName: 'Item', width: 120 },
    { field: 'supplier_name', headerName: 'Supplier', width: 150 },
    { field: 'purchase_date', headerName: 'Purchase Date', width: 130,
      valueFormatter: (params) => new Date(params.value).toLocaleDateString()
    },
    { field: 'delivery_date', headerName: 'Delivery Date', width: 130,
      valueFormatter: (params) => new Date(params.value).toLocaleDateString()
    },
    { field: 'invoice_issue_date', headerName: 'Invoice Date', width: 150,
      editable: true,
      renderEditCell: (params) => (
        <DatePicker
          value={new Date(params.value)}
          onChange={(newValue) => {
            const updated = [...editableDecisions];
            const idx = updated.findIndex(d => d.id === params.id);
            updated[idx].invoice_issue_date = newValue.toISOString().split('T')[0];
            setEditableDecisions(updated);
          }}
        />
      )
    },
    { field: 'final_cost', headerName: 'Cost', width: 120,
      valueFormatter: (params) => `$${params.value.toLocaleString()}`
    }
  ]}
  processRowUpdate={(newRow) => {
    const updated = [...editableDecisions];
    const idx = updated.findIndex(d => d.id === newRow.id);
    updated[idx] = newRow;
    setEditableDecisions(updated);
    return newRow;
  }}
/>

<Button 
  variant="contained" 
  onClick={handleSavePlan}
  disabled={!selectedProposal || editableDecisions.length === 0}
>
  Save Final Plan
</Button>
```

### Backend Verification

#### 2.2 Ensure POST /decisions Handles Invoice Date ✅
**File:** `backend/app/routers/decisions.py`

**Already Implemented:**
- `FinalizedDecisionCreate` schema includes `invoice_issue_date: date`
- Cash flow generation uses `invoice_issue_date` for inflow events
- **Status:** Ready

---

## **PHASE 3: Enhanced Cash Flow Dashboard**

### Backend Changes

#### 3.1 Create Excel Export Endpoint (TODO)
**File:** `backend/app/routers/dashboard.py`

**New Endpoint:**
```python
from fastapi.responses import StreamingResponse
import pandas as pd
from io import BytesIO

@router.get("/cashflow/export")
async def export_cashflow_to_excel(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export cash flow events to Excel"""
    try:
        # Query cashflow events
        query = select(CashflowEvent)
        if start_date:
            query = query.where(CashflowEvent.event_date >= date.fromisoformat(start_date))
        if end_date:
            query = query.where(CashflowEvent.event_date <= date.fromisoformat(end_date))
        
        result = await db.execute(query.order_by(CashflowEvent.event_date))
        events = result.scalars().all()
        
        # Convert to DataFrame
        data = []
        for event in events:
            data.append({
                'Event Date': event.event_date.isoformat(),
                'Event Type': event.event_type.upper(),
                'Amount': float(event.amount),
                'Description': event.description or '',
                'Related Decision ID': event.related_decision_id or '',
                'Created At': event.created_at.isoformat()
            })
        
        df = pd.DataFrame(data)
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Cash Flow Events')
            
            # Add summary sheet
            summary_df = pd.DataFrame({
                'Metric': ['Total Inflow', 'Total Outflow', 'Net Position'],
                'Amount': [
                    df[df['Event Type'] == 'INFLOW']['Amount'].sum(),
                    df[df['Event Type'] == 'OUTFLOW']['Amount'].sum(),
                    df[df['Event Type'] == 'INFLOW']['Amount'].sum() - df[df['Event Type'] == 'OUTFLOW']['Amount'].sum()
                ]
            })
            summary_df.to_excel(writer, index=False, sheet_name='Summary')
        
        output.seek(0)
        
        headers = {
            'Content-Disposition': 'attachment; filename="cashflow_export.xlsx"'
        }
        
        return StreamingResponse(
            output, 
            headers=headers, 
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting cash flow: {str(e)}"
        )
```

### Frontend Changes

#### 3.2 Add Data Table and Export Button (TODO)
**File:** `frontend/src/pages/DashboardPage.tsx`

**New Features:**

1. **Add Export Button:**
```typescript
import { Download as DownloadIcon } from '@mui/icons-material';

const handleExportToExcel = async () => {
  try {
    const response = await dashboardAPI.exportCashflow();
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'cashflow_export.xlsx';
    link.click();
  } catch (err) {
    setError('Failed to export cash flow data');
  }
};

<Button
  variant="outlined"
  startIcon={<DownloadIcon />}
  onClick={handleExportToExcel}
  sx={{ mb: 2 }}
>
  Export to Excel
</Button>
```

2. **Add Data Table Below Charts:**
```typescript
<Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
  Cash Flow Events Detail
</Typography>

<DataGrid
  rows={cashflowData?.time_series || []}
  columns={[
    { field: 'month', headerName: 'Month', width: 120 },
    { field: 'budget', headerName: 'Budget', width: 130,
      valueFormatter: (params) => `$${params.value.toLocaleString()}`
    },
    { field: 'inflow', headerName: 'Revenue Inflow', width: 150,
      valueFormatter: (params) => `$${params.value.toLocaleString()}`,
      cellClassName: 'positive-amount'
    },
    { field: 'outflow', headerName: 'Payment Outflow', width: 150,
      valueFormatter: (params) => `$${params.value.toLocaleString()}`,
      cellClassName: 'negative-amount'
    },
    { field: 'net_flow', headerName: 'Net Flow', width: 130,
      valueFormatter: (params) => `$${params.value.toLocaleString()}`,
      cellClassName: (params) => params.value >= 0 ? 'positive-amount' : 'negative-amount'
    },
    { field: 'cumulative_balance', headerName: 'Cumulative Balance', width: 180,
      valueFormatter: (params) => `$${params.value.toLocaleString()}`,
      cellClassName: (params) => params.value >= 0 ? 'positive-amount' : 'negative-amount'
    }
  ]}
  autoHeight
  pageSize={12}
  rowsPerPageOptions={[12, 24, 36]}
/>
```

3. **Add API Method:**
```typescript
// In frontend/src/services/api.ts
export const dashboardAPI = {
  getCashflow: (startDate?, endDate?) => api.get(...),
  getSummary: () => api.get('/dashboard/summary'),
  exportCashflow: (startDate?, endDate?) => 
    api.get('/dashboard/cashflow/export', {
      params: { start_date: startDate, end_date: endDate },
      responseType: 'blob'
    })
};
```

---

## **Implementation Priority**

### HIGH Priority (Week 1)
1. ✅ Update schemas for multi-proposal
2. 🔄 Refactor optimization_engine.py for 3 proposals
3. 🔄 Update OptimizationPage to display proposals in tabs

### MEDIUM Priority (Week 2)
4. 🔄 Add editable data grid with invoice date picker
5. 🔄 Implement "Save Final Plan" workflow
6. 🔄 Add dashboard Excel export endpoint

### LOW Priority (Week 3)
7. 🔄 Add dashboard data table
8. 🔄 UI polish and testing
9. 🔄 Performance optimization

---

## **Testing Checklist**

### Multi-Proposal Testing
- [ ] Run optimization and verify 3 proposals are returned
- [ ] Verify each proposal has different costs
- [ ] Verify "Lowest Cost" is actually the cheapest
- [ ] Verify "Cash Flow Optimized" defers payments
- [ ] Switch between proposal tabs smoothly

### Decision Finalization Testing
- [ ] Select a proposal and edit invoice dates
- [ ] Save final plan successfully
- [ ] Verify cash flow events are created with correct invoice dates
- [ ] Edit and re-save a plan

### Dashboard Testing
- [ ] View cash flow charts with saved decisions
- [ ] Export to Excel successfully
- [ ] Open Excel file and verify data accuracy
- [ ] View data table with sorting/filtering

---

## **Dependencies Check**

### Backend
- ✅ pandas (already in requirements.txt)
- ✅ openpyxl (already in requirements.txt)
- ✅ ortools (already in requirements.txt)

### Frontend
- ✅ @mui/x-date-pickers (already installed)
- ✅ @mui/x-data-grid (may need to install)
- ✅ recharts (already installed)

---

**This implementation will transform the DSS into a comprehensive strategic planning tool!** 🚀

*Created: October 8, 2025*  
*Status: Ready for Implementation*

