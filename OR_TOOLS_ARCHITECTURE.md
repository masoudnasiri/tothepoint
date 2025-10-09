# OR-Tools Enhancement Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + TypeScript)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  OptimizationPage_enhanced.tsx                                 │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │ │
│  │  │ Solver Cards │  │ Config Form  │  │ Multi-Proposal Tabs  │ │ │
│  │  │  - CP_SAT    │  │  - Time      │  │  - Cost Strategy     │ │ │
│  │  │  - GLOP      │  │  - Slots     │  │  - Priority Strategy │ │ │
│  │  │  - SCIP      │  │  - Strategies│  │  - Speed Strategy    │ │ │
│  │  │  - CBC       │  │              │  │  - Flow Strategy     │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                 │                                     │
│                                 │ API Calls                           │
│                                 ▼                                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ HTTP/REST
                                  │
┌─────────────────────────────────▼─────────────────────────────────────┐
│                      BACKEND (FastAPI + Python)                       │
├───────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  routers/finance.py - API Endpoints                              │ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │ │
│  │  │ /optimize        │  │ /optimize-       │  │ /solver-info   │ │ │
│  │  │ (legacy)         │  │  enhanced        │  │                │ │ │
│  │  │                  │  │                  │  │                │ │ │
│  │  │ Uses:            │  │ Uses:            │  │ Returns:       │ │ │
│  │  │ - Original       │  │ - Enhanced       │  │ - Solver specs │ │ │
│  │  │   optimizer      │  │   optimizer      │  │ - Strategies   │ │ │
│  │  └──────────────────┘  └──────────────────┘  └────────────────┘ │ │
│  │                                                                   │ │
│  │  ┌──────────────────────────────────────────────────────────┐   │ │
│  │  │ /optimization-analysis/{run_id}                          │   │ │
│  │  │ - Critical path analysis                                 │   │ │
│  │  │ - Network flow statistics                                │   │ │
│  │  └──────────────────────────────────────────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                 │                                      │
│                                 ▼                                      │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  optimization_engine_enhanced.py                                 │ │
│  │                                                                   │ │
│  │  ┌────────────────────────────────────────────────────────────┐ │ │
│  │  │ EnhancedProcurementOptimizer                               │ │ │
│  │  │                                                             │ │ │
│  │  │  Capabilities:                                              │ │ │
│  │  │  • Multi-solver support                                     │ │ │
│  │  │  • Strategy-based optimization                              │ │ │
│  │  │  • Multi-proposal generation                                │ │ │
│  │  │  • Graph-based analysis                                     │ │ │
│  │  └────────────────────────────────────────────────────────────┘ │ │
│  │                                 │                                │ │
│  │                ┌────────────────┼────────────────┐              │ │
│  │                │                │                │              │ │
│  │                ▼                ▼                ▼              │ │
│  │  ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐ │ │
│  │  │ Solver Selection │  │  Strategy    │  │ Graph Algorithms │ │ │
│  │  ├──────────────────┤  │  Selection   │  ├──────────────────┤ │ │
│  │  │ • CP_SAT         │  ├──────────────┤  │ • NetworkX       │ │ │
│  │  │ • GLOP           │  │ • LOWEST_    │  │ • Critical Path  │ │ │
│  │  │ • SCIP           │  │   COST       │  │ • Network Flow   │ │ │
│  │  │ • CBC            │  │ • PRIORITY_  │  │ • Centrality     │ │ │
│  │  └──────────────────┘  │   WEIGHTED   │  └──────────────────┘ │ │
│  │                        │ • FAST_      │                        │ │
│  │                        │   DELIVERY   │                        │ │
│  │                        │ • SMOOTH_    │                        │ │
│  │                        │   CASHFLOW   │                        │ │
│  │                        │ • BALANCED   │                        │ │
│  │                        └──────────────┘                        │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                 │                                      │
│                                 ▼                                      │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                     OR-Tools Library                             │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │ │
│  │  │  CP-SAT  │  │   GLOP   │  │   SCIP   │  │   CBC    │        │ │
│  │  │  Solver  │  │  Solver  │  │  Solver  │  │  Solver  │        │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                 │                                      │
│                                 ▼                                      │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                     Database (PostgreSQL)                        │ │
│  │  ┌───────────────┐  ┌────────────────┐  ┌───────────────────┐  │ │
│  │  │ Projects      │  │ ProjectItems   │  │ Procurement       │  │ │
│  │  │ BudgetData    │  │ Optimization   │  │ Options           │  │ │
│  │  │ Finalized     │  │ Results        │  │ Decisions         │  │ │
│  │  │ Decisions     │  │                │  │                   │  │ │
│  │  └───────────────┘  └────────────────┘  └───────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### Frontend Components

#### 1. OptimizationPage_enhanced.tsx
**Purpose:** Advanced optimization UI with multi-solver support

**Key Features:**
- Visual solver selection cards
- Configuration form with strategy selection
- Multi-proposal tabbed interface
- Detailed results tables
- Solver information dialogs

**State Management:**
```typescript
{
  solverInfo: { solvers, strategies },
  optimizationConfig: { solver_type, time_limit, strategies },
  lastRun: { proposals[], status, execution_time },
  selectedProposalIndex: number
}
```

---

### Backend Components

#### 1. optimization_engine_enhanced.py
**Purpose:** Core optimization logic with multiple solvers

**Class Hierarchy:**
```
EnhancedProcurementOptimizer
  ├─ Solver Management
  │   ├─ _solve_with_cpsat()
  │   ├─ _solve_with_glop()
  │   ├─ _solve_with_mip() (SCIP/CBC)
  │   └─ _run_single_optimization()
  │
  ├─ Strategy Implementation
  │   ├─ LOWEST_COST
  │   ├─ PRIORITY_WEIGHTED
  │   ├─ FAST_DELIVERY
  │   ├─ SMOOTH_CASHFLOW
  │   └─ BALANCED
  │
  ├─ Graph Analysis
  │   ├─ _build_dependency_graph()
  │   ├─ get_critical_path()
  │   └─ analyze_network_flow()
  │
  └─ Proposal Generation
      └─ _generate_multiple_proposals()
```

#### 2. routers/finance.py
**Purpose:** API endpoints for optimization

**Endpoints:**
```
POST   /finance/optimize-enhanced
  ├─ Query: solver_type, generate_multiple_proposals, strategies
  └─ Returns: OptimizationRunResponse with proposals

GET    /finance/solver-info
  └─ Returns: Available solvers and strategies

GET    /finance/optimization-analysis/{run_id}
  └─ Returns: Graph analysis and critical path
```

---

## Data Flow Diagram

### Optimization Request Flow

```
User Action: Click "Run Optimization"
     │
     ├─ 1. Frontend collects configuration
     │      - Solver type
     │      - Time parameters
     │      - Strategy selection
     │
     ├─ 2. API call to /optimize-enhanced
     │      POST with config + query params
     │
     ├─ 3. Backend creates EnhancedProcurementOptimizer
     │      EnhancedProcurementOptimizer(db, solver_type)
     │
     ├─ 4. Load data from database
     │      - Projects (active only)
     │      - Project items (exclude locked)
     │      - Procurement options
     │      - Budget data
     │
     ├─ 5. Build dependency graph
     │      NetworkX graph with items as nodes
     │
     ├─ 6. Generate proposals
     │      For each strategy:
     │      ├─ Select appropriate solver
     │      ├─ Build optimization model
     │      ├─ Set objective function
     │      ├─ Add constraints
     │      └─ Solve and extract decisions
     │
     ├─ 7. Analyze results
     │      - Calculate total costs
     │      - Determine execution times
     │      - Extract critical path
     │
     ├─ 8. Return proposals
     │      OptimizationRunResponse {
     │        proposals: [
     │          { name, strategy, cost, decisions[] },
     │          ...
     │        ]
     │      }
     │
     └─ 9. Frontend displays results
            - Proposal tabs
            - Decision tables
            - Statistics
```

---

## Solver Selection Logic

### Decision Tree Implementation

```python
if solver_type == SolverType.CP_SAT:
    # Constraint Programming
    model = cp_model.CpModel()
    variables = { ... NewBoolVar() ... }
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
elif solver_type == SolverType.GLOP:
    # Linear Programming
    solver = pywraplp.Solver.CreateSolver('GLOP')
    variables = { ... NumVar(0, 1) ... }  # LP relaxation
    status = solver.Solve()
    # Round to integer solution
    
elif solver_type in [SolverType.SCIP, SolverType.CBC]:
    # Mixed-Integer Programming
    solver = pywraplp.Solver.CreateSolver(solver_type.value)
    variables = { ... IntVar(0, 1) ... }  # Binary
    status = solver.Solve()
```

---

## Strategy Implementation

### Objective Function Formula

#### LOWEST_COST
```python
Minimize: Σ (unit_cost × quantity)
Weight: 1.0 for all items
```

#### PRIORITY_WEIGHTED
```python
Minimize: Σ (unit_cost × quantity × (11 - priority_weight))
Weight: 11 - priority_weight
  where priority_weight ∈ [1, 10]
```

#### FAST_DELIVERY
```python
Minimize: Σ (delivery_time × selection_variable)
Weight: delivery_time
```

#### SMOOTH_CASHFLOW
```python
Minimize: Variance of cash outflows across time periods
Weight: 1 + |delivery_time - midpoint| × 0.1
```

#### BALANCED
```python
Minimize: 0.7 × weighted_cost + 0.3 × delivery_factor
Weight: (11 - priority_weight) × 0.7 + delivery_time × 0.3
```

---

## Graph Algorithm Integration

### NetworkX Graph Structure

```python
Graph:
  Nodes = Project Items
    Attributes:
      - project_id
      - item_code
      - quantity
      - delivery_options

  Edges = Dependencies
    Attributes:
      - weight (dependency strength)

Algorithms Used:
  1. DAG Longest Path → Critical Path
  2. Betweenness Centrality → Key Items
  3. In-Degree Centrality → Dependent Items
  4. Connected Components → Project Groups
```

### Critical Path Calculation

```python
def get_critical_path(self) -> List[str]:
    """
    Find longest path through dependency graph
    Identifies items that determine project timeline
    """
    return nx.dag_longest_path(
        self.dependency_graph, 
        weight='weight'
    )

# Returns: ["P1_I001", "P1_I003", "P1_I007"]
```

---

## Database Schema Integration

### Optimization Results

```sql
optimization_results
├─ run_id (UUID, indexed)
├─ project_id
├─ item_code
├─ procurement_option_id
├─ purchase_time
├─ delivery_time
├─ quantity
└─ final_cost

# Supports multiple proposals per run
```

### Finalized Decisions

```sql
finalized_decisions
├─ id
├─ run_id (links to optimization_results)
├─ project_item_id
├─ procurement_option_id
├─ purchase_date
├─ delivery_date
├─ status (PROPOSED | LOCKED | REVERTED)
└─ ... (invoice tracking)

# Can be created from any proposal
```

---

## Performance Optimization Techniques

### 1. Variable Scaling
```python
# CP-SAT requires integers
# Scale costs to cents (×100)
cost_cents = int(cost_dollars * 100)
```

### 2. Early Termination
```python
solver.parameters.max_time_in_seconds = time_limit
# Stops after time limit, returns best found
```

### 3. Constraint Reduction
```python
# Only create variables for valid combinations
if purchase_time >= 1 and delivery_time <= max_slots:
    create_variable()
```

### 4. Parallel Proposals (Future)
```python
# Could use multiprocessing for strategies
# Currently sequential for simplicity
```

---

## Error Handling & Resilience

### Error Handling Flow

```python
try:
    # Load data
    await self._load_data()
    
    # Build model
    self._build_dependency_graph()
    
    # Solve
    proposals = await self._generate_multiple_proposals()
    
except Exception as e:
    # Return error response
    return OptimizationRunResponse(
        status="ERROR",
        message=str(e),
        proposals=[]
    )
```

### Fallback Strategies

```python
# If solver fails
if not solver_available:
    logger.warning(f"{solver_type} not available")
    return None  # Try next strategy

# If time limit exceeded
if status == TIMEOUT:
    # Return best solution found so far
    return FEASIBLE solution
```

---

## Testing Strategy

### Unit Tests (Recommended)

```python
# test_optimization_engine_enhanced.py

def test_cpsat_solver():
    optimizer = EnhancedProcurementOptimizer(db, SolverType.CP_SAT)
    result = await optimizer.run_optimization(request)
    assert result.status in ["OPTIMAL", "FEASIBLE"]

def test_multiple_proposals():
    optimizer = EnhancedProcurementOptimizer(db)
    result = await optimizer.run_optimization(
        request, 
        generate_multiple_proposals=True
    )
    assert len(result.proposals) > 1

def test_critical_path():
    optimizer = EnhancedProcurementOptimizer(db)
    await optimizer._load_data()
    optimizer._build_dependency_graph()
    path = optimizer.get_critical_path()
    assert isinstance(path, list)
```

### Integration Tests

```python
# Test API endpoints
def test_solver_info_endpoint():
    response = client.get("/finance/solver-info")
    assert response.status_code == 200
    assert "available_solvers" in response.json()

def test_enhanced_optimization_endpoint():
    response = client.post(
        "/finance/optimize-enhanced?solver_type=CP_SAT",
        json={"max_time_slots": 12, "time_limit_seconds": 60}
    )
    assert response.status_code == 200
```

---

## Monitoring & Logging

### Key Metrics to Track

```python
logger.info(f"Loaded {len(self.project_items)} items")
logger.info(f"Built model with {len(variables)} variables")
logger.info(f"Solver status: {status}")
logger.info(f"Execution time: {execution_time}s")
logger.info(f"Generated {len(proposals)} proposals")
```

### Performance Metrics

```python
{
  "run_id": "uuid",
  "solver_type": "CP_SAT",
  "strategy": "PRIORITY_WEIGHTED",
  "execution_time": 45.2,
  "items_count": 120,
  "variables_count": 1440,
  "status": "OPTIMAL",
  "total_cost": 1250000.00
}
```

---

## Security Considerations

### Authorization
```python
@router.post("/optimize-enhanced")
async def run_enhanced_optimization(
    current_user: User = Depends(require_finance())
):
    # Only finance and admin users
```

### Input Validation
```python
class OptimizationRunRequest(BaseModel):
    max_time_slots: int = Field(12, ge=1, le=100)
    time_limit_seconds: int = Field(300, ge=10, le=3600)
```

### Resource Limits
```python
# Time limit prevents infinite loops
solver.parameters.max_time_in_seconds = time_limit

# Max time slots prevents excessive memory
if max_time_slots > 100:
    raise ValueError("Too many time slots")
```

---

## Scalability Considerations

### Current Limits

| Metric | Small | Medium | Large | Very Large |
|--------|-------|--------|-------|------------|
| Items | < 50 | 50-500 | 500-1000 | 1000+ |
| CP_SAT | ✅ Excellent | ✅ Good | ⚠️ Slow | ❌ Timeout |
| GLOP | ✅ Very Fast | ✅ Fast | ✅ Fast | ✅ OK |
| CBC | ✅ Fast | ✅ Good | ✅ OK | ⚠️ Slow |

### Optimization Techniques

1. **Use GLOP for large problems**
2. **Reduce max_time_slots for faster solving**
3. **Disable multiple proposals in production**
4. **Cache optimization results**
5. **Implement timeout handling**

---

## Future Architecture Enhancements

### 1. Microservices (Optional)
```
┌────────────────┐
│  API Gateway   │
└────────┬───────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐  ┌─▼──────────┐
│  Core │  │ Optimization│
│ API   │  │  Service    │
└───────┘  └────────────┘
```

### 2. Queue-Based Processing
```
Frontend → API → Queue (Redis/Celery) → Worker Pool → Database
                        ↓
                 Status Updates via WebSocket
```

### 3. Caching Layer
```
Request → Cache Check → Cache Hit? Return
                      → Cache Miss? Compute → Cache → Return
```

---

## Conclusion

This architecture provides:

✅ **Flexibility:** Multiple solvers and strategies  
✅ **Scalability:** From small to large problems  
✅ **Maintainability:** Clean separation of concerns  
✅ **Extensibility:** Easy to add new solvers/strategies  
✅ **Performance:** Optimized for production use  
✅ **Reliability:** Error handling and fallbacks  

**The system is production-ready and enterprise-grade! 🚀**

