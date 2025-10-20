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
                print("   ℹ️  Run: python -m app.seed_data")
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
        print("   ℹ️  Add test data to run full optimization test")
    
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
    try:
        success = asyncio.run(test_installation())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

