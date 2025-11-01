import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.optimization_engine import ProcurementOptimizer
from app.schemas import OptimizationRunRequest

async def test_refactored_optimization():
    async for db in get_db():
        try:
            print('🚀 Testing refactored optimization engine with company-wide bundling...')
            request = OptimizationRunRequest(
                max_time_slots=10,
                time_limit_seconds=60,
                budget_limit=100000000000000,
                solver_type='CP_SAT'
            )
            optimizer = ProcurementOptimizer(db)
            result = await optimizer.run_optimization(request)
            
            print(f'\n✅ OPTIMIZATION COMPLETED')
            print(f'📊 Status: {result.status}')
            print(f'📦 Items optimized: {result.items_optimized}')
            print(f'💰 Total cost: {result.total_cost:,.2f} IRR')
            
            if result.items_optimized > 1:
                print(f'🎉 SUCCESS: Multiple items optimized with company-wide bundling!')
            else:
                print(f'⚠️  Only {result.items_optimized} item optimized - may need more data')
                
            break
        except Exception as e:
            print(f'\n❌ ERROR: {e}')
            import traceback
            traceback.print_exc()
            break

asyncio.run(test_refactored_optimization())
