import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.optimization_engine import ProcurementOptimizer
from app.schemas import OptimizationRunRequest

async def debug_model_building():
    async for db in get_db():
        try:
            print('🔍 Debugging model building phase...')
            
            # Create optimizer and load data
            optimizer = ProcurementOptimizer(db)
            await optimizer._load_data()
            
            print(f'📊 Loaded {len(optimizer.project_items)} project items')
            print(f'📦 Loaded {len(optimizer.procurement_options)} procurement options')
            
            # Test model building
            print('\n🏗️ Building optimization model...')
            await optimizer._build_model(max_time_slots=10)
            
            print(f'📈 Created {len(optimizer.variables)} variables')
            
            # Check which items actually got variables
            processed_items = set()
            for var_name in optimizer.variables.keys():
                parts = var_name.split('_')
                project_item_id = int(parts[2])
                item = next((i for i in optimizer.project_items if i.id == project_item_id), None)
                if item:
                    processed_items.add(f"{item.item_code}({project_item_id})")
            
            print(f'✅ Items with variables: {list(processed_items)}')
            
            break
        except Exception as e:
            print(f'❌ ERROR: {e}')
            import traceback
            traceback.print_exc()
            break

asyncio.run(debug_model_building())
