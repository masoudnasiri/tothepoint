import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.optimization_engine_enhanced import EnhancedProcurementOptimizer
from app.schemas import OptimizationRunRequest

async def test_multiple_items_optimization():
    async for db in get_db():
        try:
            print('🚀 Testing optimization with different parameters...')
            
            # Test with different budget limits
            test_cases = [
                {"budget_limit": 100000000000000, "name": "Very High Budget"},
                {"budget_limit": 5000000000000, "name": "High Budget"},
                {"budget_limit": 1000000000000, "name": "Medium Budget"},
                {"budget_limit": 100000000000, "name": "Low Budget"},
            ]
            
            for test_case in test_cases:
                print(f'\n📊 Testing with {test_case["name"]}: {test_case["budget_limit"]:,} IRR')
                
                request = OptimizationRunRequest(
                    max_time_slots=10,
                    time_limit_seconds=60,
                    budget_limit=test_case["budget_limit"],
                    solver_type='CP_SAT'
                )
                
                optimizer = EnhancedProcurementOptimizer(db, solver_type='CP_SAT')
                result = await optimizer.run_optimization(
                    request, 
                    generate_multiple_proposals=False,
                    strategies=None
                )
                
                print(f'  Status: {result.status}')
                print(f'  Items optimized: {result.items_optimized}')
                print(f'  Total cost: {result.total_cost:,.2f} IRR')
                
                if result.proposals:
                    proposal = result.proposals[0]
                    print(f'  Decisions: {len(proposal.decisions)}')
                    for decision in proposal.decisions:
                        print(f'    - {decision.item_code} (Project {decision.project_id}): {decision.supplier_name}, Cost: {decision.final_cost:,.2f}')
            
            break
        except Exception as e:
            print(f'❌ ERROR: {e}')
            import traceback
            traceback.print_exc()
            break

asyncio.run(test_multiple_items_optimization())
