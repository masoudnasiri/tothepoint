import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.optimization_engine_enhanced import EnhancedProcurementOptimizer
from app.schemas import OptimizationRunRequest

async def test_corrected_purchase_delivery_dates():
    async for db in get_db():
        try:
            print('🔍 Testing CORRECTED PURCHASE & DELIVERY DATES...')
            print('📅 Expected: Purchase dates should be when to place orders')
            print('📅 Expected: Delivery dates should be when suppliers deliver')
            print('📅 Expected: Dates should come from procurement options, not calculated')
            
            request = OptimizationRunRequest(
                max_time_slots=10,
                time_limit_seconds=60,
                budget_limit=100000000000000,
                solver_type='CP_SAT'
            )
            
            optimizer = EnhancedProcurementOptimizer(db, solver_type='CP_SAT')
            result = await optimizer.run_optimization(
                request, 
                generate_multiple_proposals=False,
                strategies=None
            )
            
            print(f'\n📅 CORRECTED DATE RESULTS:')
            print(f'📊 Status: {result.status}')
            print(f'📦 Items optimized: {result.items_optimized}')
            
            if result.proposals:
                proposal = result.proposals[0]
                print(f'\n📅 DETAILED PURCHASE & DELIVERY DATES:')
                
                for i, decision in enumerate(proposal.decisions, 1):
                    print(f'  {i}. {decision.item_code} (Project {decision.project_id})')
                    print(f'     Supplier: {decision.supplier_name}')
                    print(f'     📅 Purchase Date: {decision.purchase_date} (when to place order)')
                    print(f'     📦 Delivery Date: {decision.delivery_date} (when supplier delivers)')
                    print(f'     ⏱️  Lead Time: {decision.delivery_date - decision.purchase_date} days')
                    print()
            
            # Check if dates are realistic and properly separated
            if result.proposals:
                proposal = result.proposals[0]
                all_realistic = True
                
                for decision in proposal.decisions:
                    # Check if purchase date is before delivery date
                    if decision.purchase_date >= decision.delivery_date:
                        print(f'❌ LOGIC ERROR: {decision.item_code} purchase ({decision.purchase_date}) >= delivery ({decision.delivery_date})')
                        all_realistic = False
                    
                    # Check if dates are in reasonable timeframe (2025-2026)
                    if decision.delivery_date.year > 2026:
                        print(f'❌ UNREASONABLE DATE: {decision.item_code} delivery on {decision.delivery_date}')
                        all_realistic = False
                    if decision.purchase_date.year > 2026:
                        print(f'❌ UNREASONABLE DATE: {decision.item_code} purchase on {decision.purchase_date}')
                        all_realistic = False
                
                if all_realistic:
                    print(f'✅ SUCCESS: All dates are realistic and properly ordered!')
                else:
                    print(f'⚠️  Some dates still have issues')
                    
            break
        except Exception as e:
            print(f'\n❌ ERROR: {e}')
            import traceback
            traceback.print_exc()
            break

asyncio.run(test_corrected_purchase_delivery_dates())
