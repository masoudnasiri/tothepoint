import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.optimization_engine import ProcurementOptimizer
from app.schemas import OptimizationRunRequest

async def debug_optimization():
    async for db in get_db():
        try:
            print('🔍 Debugging optimization engine...')
            
            # Create optimizer and load data
            optimizer = ProcurementOptimizer(db)
            await optimizer._load_data()
            
            print(f'📊 Loaded {len(optimizer.project_items)} project items')
            print(f'📦 Loaded {len(optimizer.procurement_options)} procurement options')
            print(f'🏢 Company-wide quantities: {optimizer.company_wide_quantities}')
            
            # Check each project item
            for item in optimizer.project_items:
                options = optimizer.procurement_options_by_item.get(item.id, [])
                print(f'  Item {item.item_code} (ID: {item.id}): {len(options)} options')
                
            break
        except Exception as e:
            print(f'❌ ERROR: {e}')
            import traceback
            traceback.print_exc()
            break

asyncio.run(debug_optimization())
