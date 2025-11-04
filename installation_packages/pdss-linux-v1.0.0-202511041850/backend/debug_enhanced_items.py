import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.optimization_engine_enhanced import EnhancedProcurementOptimizer
from app.schemas import OptimizationRunRequest

async def debug_enhanced_optimization():
    async for db in get_db():
        try:
            print('🔍 Debugging why only 1 item is optimized...')
            
            optimizer = EnhancedProcurementOptimizer(db, solver_type='CP_SAT')
            await optimizer._load_data()
            
            print(f'\n📊 DATA LOADED:')
            print(f'Projects: {len(optimizer.projects)}')
            print(f'Project items: {len(optimizer.project_items)}')
            print(f'Procurement options: {len(optimizer.procurement_options)}')
            
            print(f'\n📦 PROJECT ITEMS:')
            for item in optimizer.project_items:
                print(f'  Item {item.id}: {item.item_code} (Project {item.project_id})')
                print(f'    Quantity: {item.quantity}')
                print(f'    Delivery options: {item.delivery_options}')
                
                # Check procurement options for this item
                item_options = [opt for opt in optimizer.procurement_options.values() 
                              if opt.item_code == item.item_code]
                print(f'    Procurement options: {len(item_options)}')
                for opt in item_options:
                    print(f'      Option {opt.id}: {opt.supplier_name}, cost: {opt.cost_amount}, lead_time: {opt.lomc_lead_time}')
            
            print(f'\n🛒 ALL PROCUREMENT OPTIONS:')
            for opt_id, opt in optimizer.procurement_options.items():
                print(f'  Option {opt_id}: {opt.item_code} - {opt.supplier_name} - {opt.cost_amount} - lead_time: {opt.lomc_lead_time}')
            
            # Test model building
            print(f'\n🏗️ TESTING MODEL BUILDING:')
            request = OptimizationRunRequest(
                max_time_slots=10,
                time_limit_seconds=60,
                budget_limit=100000000000000,
                solver_type='CP_SAT'
            )
            
            # Test CP-SAT model building
            from ortools.sat.python import cp_model
            model = cp_model.CpModel()
            variables = {}
            
            items_processed = 0
            variables_created = 0
            
            for item in optimizer.project_items:
                print(f'\n🔍 Processing item {item.item_code}:')
                
                delivery_options = item.delivery_options if item.delivery_options else []
                print(f'  Delivery options: {delivery_options}')
                
                if not delivery_options:
                    print(f'  ❌ No delivery options - SKIPPING')
                    continue
                
                # Parse delivery dates
                from datetime import date, datetime
                today = date.today()
                valid_times = []
                for delivery_date_str in delivery_options:
                    try:
                        if isinstance(delivery_date_str, dict):
                            delivery_date_str = delivery_date_str.get('delivery_date', '')
                        
                        if delivery_date_str:
                            delivery_date = datetime.fromisoformat(delivery_date_str.replace('Z', '+00:00')).date()
                            days_from_today = (delivery_date - today).days
                            print(f'    Delivery date: {delivery_date}, days from today: {days_from_today}')
                            if days_from_today > 0:
                                valid_times.append(days_from_today)
                    except (ValueError, TypeError) as e:
                        print(f'    Invalid date format: {delivery_date_str}, error: {e}')
                        continue
                
                print(f'  Valid times: {valid_times}')
                
                if not valid_times:
                    print(f'  ❌ No valid future delivery dates - SKIPPING')
                    continue
                
                item_options = [opt for opt in optimizer.procurement_options.values() 
                              if opt.item_code == item.item_code]
                print(f'  Procurement options: {len(item_options)}')
                
                if not item_options:
                    print(f'  ❌ No finalized procurement options - SKIPPING')
                    continue
                
                print(f'  ✅ Processing item {item.item_code}: {len(item_options)} options, {len(valid_times)} time slots')
                items_processed += 1
                
                for option in item_options:
                    print(f'    Option {option.id}: {option.supplier_name}')
                    for delivery_time in valid_times:
                        purchase_time = delivery_time - option.lomc_lead_time
                        print(f'      Delivery time: {delivery_time}, lead_time: {option.lomc_lead_time}, purchase_time: {purchase_time}')
                        if purchase_time < 1:
                            print(f'      ❌ Purchase time < 1, skipping')
                            continue
                        
                        var_name = f"buy_{item.project_id}_{item.item_code}_{option.id}_{delivery_time}"
                        variables[var_name] = model.NewBoolVar(var_name)
                        variables_created += 1
                        print(f'      ✅ Created variable: {var_name}')
            
            print(f'\n📈 MODEL BUILDING SUMMARY:')
            print(f'Items processed: {items_processed}/{len(optimizer.project_items)}')
            print(f'Variables created: {variables_created}')
            print(f'Variable names: {list(variables.keys())}')
            
            break
        except Exception as e:
            print(f'❌ ERROR: {e}')
            import traceback
            traceback.print_exc()
            break

asyncio.run(debug_enhanced_optimization())
