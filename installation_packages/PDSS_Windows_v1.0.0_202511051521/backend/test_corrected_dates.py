import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.optimization_engine_enhanced import EnhancedProcurementOptimizer
from app.schemas import OptimizationRunRequest

async def test_corrected_dates():
    async for db in get_db():
        try:
            print('🔍 Testing CORRECTED DATE CALCULATION...')
            print('📅 Expected: Delivery dates should match project delivery options')
            print('📅 Expected: Purchase dates should be delivery_date - lead_time')
            
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
            
            print(f'\n📅 DATE CORRECTION RESULTS:')
            print(f'📊 Status: {result.status}')
            print(f'📦 Items optimized: {result.items_optimized}')
            
            if result.proposals:
                proposal = result.proposals[0]
                print(f'\n📅 DETAILED DATES:')
                
                for i, decision in enumerate(proposal.decisions, 1):
                    print(f'  {i}. {decision.item_code} (Project {decision.project_id})')
                    print(f'     Supplier: {decision.supplier_name}')
                    print(f'     Purchase Date: {decision.purchase_date}')
                    print(f'     Delivery Date: {decision.delivery_date}')
                    print(f'     Lead Time: {decision.delivery_date - decision.purchase_date} days')
                    print()
            
            # Check if dates are reasonable (not in 2028-2031)
            if result.proposals:
                proposal = result.proposals[0]
                all_reasonable = True
                
                for decision in proposal.decisions:
                    if decision.delivery_date.year > 2026:
                        print(f'❌ UNREASONABLE DATE: {decision.item_code} delivery on {decision.delivery_date}')
                        all_reasonable = False
                    if decision.purchase_date.year > 2026:
                        print(f'❌ UNREASONABLE DATE: {decision.item_code} purchase on {decision.purchase_date}')
                        all_reasonable = False
                
                if all_reasonable:
                    print(f'✅ SUCCESS: All dates are reasonable (2025-2026)')
                else:
                    print(f'⚠️  Some dates are still unreasonable')
                    
            break
        except Exception as e:
            print(f'\n❌ ERROR: {e}')
            import traceback
            traceback.print_exc()
            break

asyncio.run(test_corrected_dates())
