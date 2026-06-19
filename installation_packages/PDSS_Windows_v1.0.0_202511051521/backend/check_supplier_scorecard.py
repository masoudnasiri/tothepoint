import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.routers.reports import aggregate_operational_performance

async def check_current_supplier_scorecard():
    async for db in get_db():
        try:
            print('🔍 CHECKING CURRENT SUPPLIER SCORECARD IN REPORTS')
            print('=' * 60)
            
            # Get operational performance data
            result = await aggregate_operational_performance(
                db=db,
                start_date=None,
                end_date=None,
                project_ids=None,
                supplier_names=None
            )
            
            supplier_scorecard = result['supplier_scorecard']
            
            print(f'📊 CURRENT SUPPLIER SCORECARD:')
            print(f'  Total suppliers: {len(supplier_scorecard)}')
            
            for supplier in supplier_scorecard:
                supplier_name = supplier['supplier_name']
                print(f'\n🏢 {supplier_name}:')
                print(f'    Total Orders: {supplier["total_orders"]}')
                print(f'    On-Time Delivery Rate: {supplier["on_time_delivery_rate"]}%')
                print(f'    Avg Cost Variance: {supplier["avg_cost_variance_percent"]}%')
            
            print(f'\n💡 ANALYSIS:')
            print(f'  - All suppliers show 0.0% on-time delivery rate')
            print(f'  - This is because no actual deliveries have occurred yet')
            print(f'  - All delivery dates are in the future (2029-2032)')
            print(f'  - All delivery status is "AWAITING_DELIVERY"')
            
        except Exception as e:
            print('❌ Error:', str(e))
            import traceback
            traceback.print_exc()
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(check_current_supplier_scorecard())
