import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.optimization_engine_enhanced import EnhancedProcurementOptimizer
from app.schemas import OptimizationRunRequest

async def debug_feasibility():
    async for db in get_db():
        try:
            print('🔍 Debugging feasibility issues...')
            
            optimizer = EnhancedProcurementOptimizer(db, solver_type='CP_SAT')
            await optimizer._load_data()
            
            print(f'\n📊 DATA ANALYSIS:')
            print(f'Projects: {len(optimizer.projects)}')
            print(f'Project items: {len(optimizer.project_items)}')
            print(f'Procurement options: {len(optimizer.procurement_options)}')
            
            print(f'\n🔍 FEASIBILITY CHECK:')
            feasible_items = 0
            
            for item in optimizer.project_items:
                print(f'\n📦 Item: {item.item_code} (Project {item.project_id})')
                
                # Check delivery options
                delivery_options = item.delivery_options if item.delivery_options else []
                print(f'  Delivery options: {delivery_options}')
                
                if not delivery_options:
                    print(f'  ❌ No delivery options - NOT FEASIBLE')
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
                            if days_from_today > 0:
                                valid_times.append(days_from_today)
                    except (ValueError, TypeError) as e:
                        print(f'    Invalid date format: {delivery_date_str}, error: {e}')
                        continue
                
                print(f'  Valid delivery times: {valid_times}')
                
                if not valid_times:
                    print(f'  ❌ No valid future delivery dates - NOT FEASIBLE')
                    continue
                
                # Check procurement options
                item_options = [opt for opt in optimizer.procurement_options.values() 
                              if opt.item_code == item.item_code]
                print(f'  Procurement options: {len(item_options)}')
                
                if not item_options:
                    print(f'  ❌ No finalized procurement options - NOT FEASIBLE')
                    continue
                
                # Check if any option can meet delivery constraints
                feasible_options = 0
                for option in item_options:
                    print(f'    Option {option.id}: {option.supplier_name}')
                    print(f'      Cost: {option.cost_amount}, Lead time: {option.lomc_lead_time}')
                    
                    option_feasible = False
                    for delivery_time in valid_times:
                        purchase_time = delivery_time - option.lomc_lead_time
                        print(f'      Delivery time: {delivery_time}, Purchase time: {purchase_time}')
                        if purchase_time >= 1:
                            option_feasible = True
                            print(f'      ✅ Feasible')
                        else:
                            print(f'      ❌ Purchase time < 1')
                    
                    if option_feasible:
                        feasible_options += 1
                
                if feasible_options > 0:
                    print(f'  ✅ Item is FEASIBLE ({feasible_options} options)')
                    feasible_items += 1
                else:
                    print(f'  ❌ Item is NOT FEASIBLE (no valid options)')
            
            print(f'\n📈 FEASIBILITY SUMMARY:')
            print(f'Total items: {len(optimizer.project_items)}')
            print(f'Feasible items: {feasible_items}')
            print(f'Infeasible items: {len(optimizer.project_items) - feasible_items}')
            
            if feasible_items == 0:
                print(f'\n❌ NO ITEMS ARE FEASIBLE - This is why optimization fails!')
                print(f'💡 SOLUTION: Need to fix delivery dates or lead times')
            elif feasible_items < len(optimizer.project_items):
                print(f'\n⚠️  Only {feasible_items} out of {len(optimizer.project_items)} items are feasible')
                print(f'💡 SOLUTION: Need to fix infeasible items or use partial optimization')
            else:
                print(f'\n✅ ALL ITEMS ARE FEASIBLE - Optimization should work!')
            
            break
        except Exception as e:
            print(f'❌ ERROR: {e}')
            import traceback
            traceback.print_exc()
            break

asyncio.run(debug_feasibility())
