# Installation Testing Guide

## Step-by-Step Testing Procedure

### 1️⃣ Test Backend Dependencies

Open PowerShell in your project root and run:

```powershell
# Navigate to backend
cd backend

# Activate virtual environment (if using venv)
.\venv\Scripts\activate

# Test NetworkX installation
python -c "import networkx; print('✅ NetworkX version:', networkx.__version__)"

# Test OR-Tools installation
python -c "import ortools; print('✅ OR-Tools version:', ortools.__version__)"

# Test all solver imports
python -c "from ortools.sat.python import cp_model; from ortools.linear_solver import pywraplp; print('✅ All solvers available')"

# Test enhanced optimizer import
python -c "from app.optimization_engine_enhanced import EnhancedProcurementOptimizer, SolverType, OptimizationStrategy; print('✅ Enhanced optimizer imported successfully')"
```

**Expected Output:**
```
✅ NetworkX version: 3.2.1
✅ OR-Tools version: 9.8.3296
✅ All solvers available
✅ Enhanced optimizer imported successfully
```

---

### 2️⃣ Test Backend Server

```powershell
# Start the backend server (from backend directory)
uvicorn app.main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

Keep this terminal open and open a new PowerShell window for the next tests.

---

### 3️⃣ Test API Endpoints

In a new PowerShell window:

```powershell
# Test 1: Get solver information
curl http://localhost:8000/finance/solver-info

# Expected: JSON with available_solvers and available_strategies
```

**Expected Response:**
```json
{
  "available_solvers": [
    {
      "type": "CP_SAT",
      "name": "Constraint Programming SAT",
      ...
    }
  ],
  "available_strategies": [
    {
      "type": "LOWEST_COST",
      ...
    }
  ]
}
```

---

### 4️⃣ Test Frontend

```powershell
# Open new PowerShell window
cd frontend

# Start frontend (if not already running)
npm start
```

**Browser Tests:**

1. **Navigate to**: `http://localhost:3000/login`
2. **Login** with admin or finance user
3. **Check sidebar** - Should see "Advanced Optimization" menu item
4. **Navigate to**: `http://localhost:3000/optimization-enhanced`
5. **Verify page loads** - Should see solver selection cards

---

### 5️⃣ End-to-End Test (Full Optimization Run)

**Prerequisites:**
- Backend running
- Frontend running
- Logged in as admin or finance user
- Have some test data (projects, items, procurement options, budget)

**Test Steps:**

1. **Navigate to Advanced Optimization**
   - URL: `http://localhost:3000/optimization-enhanced`
   - Should see 4 solver cards (CP_SAT, GLOP, SCIP, CBC)

2. **Configure Optimization**
   - Select **CP_SAT** (should be selected by default)
   - Click "Run Optimization" button

3. **In Dialog:**
   - Solver Type: **CP_SAT**
   - Max Time Slots: **12**
   - Time Limit: **60** seconds (for quick test)
   - Enable "Generate Multiple Proposals": **Yes**
   - Strategies: Leave empty (will generate all)

4. **Click "Run Optimization"**

5. **Wait for Results** (may take 1-2 minutes)

6. **Verify Results:**
   - ✅ Status shows "OPTIMAL" or "FEASIBLE"
   - ✅ Multiple proposal tabs appear
   - ✅ Can switch between proposals
   - ✅ Each proposal shows decisions table
   - ✅ Costs are calculated correctly
   - ✅ Execution time is displayed

---

## 🧪 Automated Test Script

Save this as `test_enhanced_optimization.py` in the backend directory:

```python
"""
Automated test script for enhanced optimization
Run: python test_enhanced_optimization.py
"""

import asyncio
import sys
from sqlalchemy import select
from app.database import async_session_maker
from app.optimization_engine_enhanced import (
    EnhancedProcurementOptimizer, 
    SolverType, 
    OptimizationStrategy
)
from app.schemas import OptimizationRunRequest
from app.models import Project, ProjectItem, ProcurementOption, BudgetData

async def test_installation():
    print("🧪 Testing Enhanced Optimization Installation\n")
    print("=" * 60)
    
    # Test 1: Import check
    print("\n1️⃣ Testing imports...")
    try:
        from ortools.sat.python import cp_model
        from ortools.linear_solver import pywraplp
        import networkx as nx
        print("   ✅ All imports successful")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 2: Solver availability
    print("\n2️⃣ Testing solver availability...")
    solvers_available = {
        'CP_SAT': False,
        'GLOP': False,
        'CBC': False,
        'SCIP': False
    }
    
    # Test CP-SAT
    try:
        model = cp_model.CpModel()
        solver = cp_model.CpSolver()
        solvers_available['CP_SAT'] = True
        print("   ✅ CP-SAT available")
    except:
        print("   ❌ CP-SAT not available")
    
    # Test GLOP
    try:
        solver = pywraplp.Solver.CreateSolver('GLOP')
        if solver:
            solvers_available['GLOP'] = True
            print("   ✅ GLOP available")
        else:
            print("   ⚠️  GLOP not available")
    except:
        print("   ❌ GLOP not available")
    
    # Test CBC
    try:
        solver = pywraplp.Solver.CreateSolver('CBC')
        if solver:
            solvers_available['CBC'] = True
            print("   ✅ CBC available")
        else:
            print("   ⚠️  CBC not available")
    except:
        print("   ❌ CBC not available")
    
    # Test SCIP
    try:
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if solver:
            solvers_available['SCIP'] = True
            print("   ✅ SCIP available")
        else:
            print("   ⚠️  SCIP not available (optional)")
    except:
        print("   ⚠️  SCIP not available (optional)")
    
    # Test 3: Database connectivity
    print("\n3️⃣ Testing database connectivity...")
    try:
        async with async_session_maker() as db:
            # Check for data
            projects = await db.execute(select(Project).where(Project.is_active == True))
            project_list = list(projects.scalars().all())
            
            items = await db.execute(select(ProjectItem))
            items_list = list(items.scalars().all())
            
            options = await db.execute(select(ProcurementOption).where(ProcurementOption.is_active == True))
            options_list = list(options.scalars().all())
            
            budgets = await db.execute(select(BudgetData))
            budgets_list = list(budgets.scalars().all())
            
            print(f"   ✅ Database connected")
            print(f"      - Projects: {len(project_list)}")
            print(f"      - Items: {len(items_list)}")
            print(f"      - Procurement Options: {len(options_list)}")
            print(f"      - Budget Periods: {len(budgets_list)}")
            
            if len(project_list) == 0:
                print("   ⚠️  No projects found - add test data first")
                return False
                
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False
    
    # Test 4: Create optimizer instance
    print("\n4️⃣ Testing optimizer instantiation...")
    try:
        async with async_session_maker() as db:
            optimizer = EnhancedProcurementOptimizer(db, solver_type=SolverType.CP_SAT)
            print("   ✅ Optimizer created successfully")
            
            # Load data
            await optimizer._load_data()
            print(f"   ✅ Data loaded: {len(optimizer.project_items)} items")
            
            # Build graph
            optimizer._build_dependency_graph()
            if optimizer.dependency_graph:
                print(f"   ✅ Dependency graph built: {len(optimizer.dependency_graph.nodes)} nodes")
            
    except Exception as e:
        print(f"   ❌ Optimizer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Quick optimization test (if data available)
    if len(items_list) > 0 and len(options_list) > 0 and len(budgets_list) > 0:
        print("\n5️⃣ Running quick optimization test...")
        try:
            async with async_session_maker() as db:
                optimizer = EnhancedProcurementOptimizer(db, solver_type=SolverType.CP_SAT)
                
                request = OptimizationRunRequest(
                    max_time_slots=12,
                    time_limit_seconds=30  # Quick test
                )
                
                print("   ⏳ Running optimization (30s limit)...")
                result = await optimizer.run_optimization(
                    request,
                    generate_multiple_proposals=False,
                    strategies=[OptimizationStrategy.LOWEST_COST]
                )
                
                print(f"   ✅ Optimization completed")
                print(f"      - Status: {result.status}")
                print(f"      - Execution time: {result.execution_time_seconds:.2f}s")
                print(f"      - Total cost: ${result.total_cost:,.2f}")
                print(f"      - Items optimized: {result.items_optimized}")
                print(f"      - Proposals generated: {len(result.proposals)}")
                
        except Exception as e:
            print(f"   ⚠️  Optimization test skipped: {e}")
    else:
        print("\n5️⃣ Skipping optimization test (insufficient data)")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_solvers = sum(solvers_available.values())
    print(f"\n✅ Solvers available: {total_solvers}/4")
    for solver, available in solvers_available.items():
        status = "✅" if available else ("⚠️ " if solver == "SCIP" else "❌")
        print(f"   {status} {solver}")
    
    if solvers_available['CP_SAT'] and solvers_available['GLOP']:
        print("\n🎉 Installation successful! Core solvers ready.")
        print("\n📝 Recommended next steps:")
        print("   1. Start backend: uvicorn app.main:app --reload")
        print("   2. Start frontend: npm start (in frontend directory)")
        print("   3. Navigate to: http://localhost:3000/optimization-enhanced")
        print("   4. Run your first optimization!")
        return True
    else:
        print("\n⚠️  Some required solvers are missing.")
        print("   Please ensure OR-Tools is installed: pip install ortools")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_installation())
    sys.exit(0 if success else 1)
```

**Run the test:**
```powershell
cd backend
python test_enhanced_optimization.py
```

---

## 🎯 Quick Verification Checklist

After running all tests, verify:

- [ ] NetworkX imported successfully
- [ ] OR-Tools imported successfully
- [ ] CP-SAT solver available
- [ ] GLOP solver available
- [ ] CBC solver available
- [ ] Backend server starts without errors
- [ ] Frontend loads optimization page
- [ ] Solver selection cards visible
- [ ] Can click "Run Optimization"
- [ ] Optimization completes successfully
- [ ] Results display correctly

---

## ⚠️ Troubleshooting Common Issues

### Issue: "ModuleNotFoundError: No module named 'networkx'"

**Solution:**
```powershell
cd backend
pip install networkx==3.2.1
```

### Issue: "Solver GLOP not available"

**Solution:**
```powershell
pip install --upgrade ortools
```

### Issue: "No optimization runs found"

**Solution:** Add test data first:
- At least 1 active project
- At least 1 project item with delivery options
- At least 1 procurement option for that item
- At least 1 budget period

### Issue: Optimization returns "INFEASIBLE"

**Solutions:**
1. Check budget amounts (increase if too tight)
2. Verify delivery options exist for all items
3. Ensure procurement options match item codes
4. Check that locked decisions don't conflict

### Issue: Frontend shows "Advanced Optimization" but page is blank

**Solution:**
```powershell
# Clear cache and rebuild
cd frontend
rm -rf node_modules/.cache
npm start
```

---

## 🚀 Next Steps After Successful Installation

1. **Read Quick Reference**
   ```powershell
   type OR_TOOLS_QUICK_REFERENCE.md
   ```

2. **Try Different Solvers**
   - Run with CP_SAT
   - Run with GLOP
   - Compare execution times

3. **Test Multiple Proposals**
   - Enable "Generate Multiple Proposals"
   - Compare different strategies

4. **Explore Graph Analysis**
   ```powershell
   curl http://localhost:8000/finance/optimization-analysis/YOUR_RUN_ID
   ```

---

## 📞 Getting Help

If tests fail:
1. Check error messages carefully
2. Verify all dependencies installed
3. Ensure database has test data
4. Check backend logs for details
5. Review `OR_TOOLS_ENHANCEMENT_GUIDE.md`

**Installation is complete when all core tests pass! 🎉**

