import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.optimization_engine import ProcurementOptimizer
from datetime import date

async def debug_third_item():
    async for db in get_db():
        try:
            print('🔍 Debugging why third item is not getting variables...')
            
            optimizer = ProcurementOptimizer(db)
            await optimizer._load_data()
            
            # Find the third item
            third_item = next((item for item in optimizer.project_items if item.id == 3), None)
            if not third_item:
                print('❌ Third item not found in project_items')
                return
                
            print(f'📦 Third item: {third_item.item_code} (ID: {third_item.id})')
            
            # Check delivery options
            delivery_options = third_item.delivery_options_rel if third_item.delivery_options_rel else []
            print(f'📅 Delivery options: {len(delivery_options)}')
            
            if delivery_options:
                today = date.today()
                valid_times = []
                for delivery_option in delivery_options:
                    if hasattr(delivery_option, 'delivery_date'):
                        delivery_date = delivery_option.delivery_date
                        days_from_today = (delivery_date - today).days
                        print(f'  Delivery date: {delivery_date}, days from today: {days_from_today}')
                        if days_from_today >= 1:
                            valid_times.append(days_from_today)
                
                print(f'✅ Valid delivery times: {valid_times}')
            
            # Check procurement options
            item_options = optimizer.procurement_options_by_item.get(third_item.id, [])
            print(f'🛒 Procurement options: {len(item_options)}')
            
            if item_options:
                for option in item_options:
                    print(f'  Option {option.id}: {option.supplier_name}, lead_time: {option.lomc_lead_time}')
                    
                    # Check if variables would be created
                    if valid_times:
                        for delivery_time in valid_times:
                            purchase_time = delivery_time - option.lomc_lead_time
                            print(f'    Delivery time: {delivery_time}, Purchase time: {purchase_time}')
                            if purchase_time < 1:
                                print(f'    ❌ Purchase time < 1, skipping')
                            else:
                                print(f'    ✅ Would create variable')
            
            break
        except Exception as e:
            print(f'❌ ERROR: {e}')
            import traceback
            traceback.print_exc()
            break

asyncio.run(debug_third_item())
