import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.optimization_engine import ProcurementOptimizer
from app.schemas import OptimizationRunRequest

async def test_opt():
    async for db in get_db():
        try:
            request = OptimizationRunRequest(
                max_time_slots=10,
                time_limit_seconds=60,
                budget_limit=100000000000000,
                solver_type='CP_SAT'
            )
            optimizer = ProcurementOptimizer(db)
            result = await optimizer.run_optimization(request)
            print(f'Status: {result.status}')
            print(f'Items: {result.items_optimized}')
            print(f'Cost: {result.total_cost}')
            break
        except Exception as e:
            print(f'ERROR: {e}')
            import traceback
            traceback.print_exc()
            break

asyncio.run(test_opt())

