import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.optimization_engine import ProcurementOptimizer
from app.schemas import OptimizationRunRequest

async def test_fixed_optimization():
    async for db in get_db():
        try:
            print('🚀 Testing fixed optimization engine...')
            
            # Create optimizer and load data
            optimizer = ProcurementOptimizer(db)
            await optimizer._load_data()
            
            print(f'📊 Loaded {len(optimizer.project_items)} project items')
            print(f'📦 Loaded {len(optimizer.procurement_options)} procurement options')
            print(f'🏢 Company-wide quantities: {optimizer.company_wide_quantities}')
            
            # Test model building
            print('\n🏗️ Building optimization model...')
            await optimizer._build_model(max_time_slots=10)
            
            print(f'📈 Created {len(optimizer.variables)} variables')
            
            # Check which items got variables
            processed_items = set()
            for var_name in optimizer.variables.keys():
                parts = var_name.split('_')
                project_item_id = int(parts[2])
                item = next((i for i in optimizer.project_items if i.id == project_item_id), None)
                if item:
                    processed_items.add(f"{item.item_code}({project_item_id})")
            
            print(f'✅ Items with variables: {list(processed_items)}')
            
            # Run optimization
            print('\n🎯 Running optimization...')
            request = OptimizationRunRequest(
                max_time_slots=10,
                time_limit_seconds=60,
                budget_limit=100000000000000,
                solver_type='CP_SAT'
            )
            result = await optimizer.run_optimization(request)
            
            print(f'\n🎉 OPTIMIZATION RESULTS:')
            print(f'📊 Status: {result.status}')
            print(f'📦 Items optimized: {result.items_optimized}')
            print(f'💰 Total cost: {result.total_cost:,.2f} IRR')
            
            if result.items_optimized >= 2:
                print(f'✅ SUCCESS: Multiple items optimized with company-wide bundling!')
            else:
                print(f'⚠️  Only {result.items_optimized} item optimized')
                
            break
        except Exception as e:
            print(f'\n❌ ERROR: {e}')
            import traceback
            traceback.print_exc()
            break

asyncio.run(test_fixed_optimization())
