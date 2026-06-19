import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.optimization_engine_enhanced import EnhancedProcurementOptimizer
from app.schemas import OptimizationRunRequest

async def test_demand_fulfillment_optimization():
    async for db in get_db():
        try:
            print('🚀 Testing DEMAND FULFILLMENT optimization...')
            print('📋 Expected: ALL 3 items should be optimized (demand fulfillment)')
            
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
            
            print(f'\n🎉 DEMAND FULFILLMENT RESULTS:')
            print(f'📊 Status: {result.status}')
            print(f'📦 Items optimized: {result.items_optimized}')
            print(f'💰 Total cost: {result.total_cost:,.2f} IRR')
            print(f'⏱️  Execution time: {result.execution_time_seconds:.2f} seconds')
            print(f'📋 Proposals: {len(result.proposals)}')
            
            if result.proposals:
                proposal = result.proposals[0]
                print(f'\n📋 DETAILED DECISIONS:')
                print(f'Strategy: {proposal.strategy_type}')
                print(f'Total decisions: {len(proposal.decisions)}')
                
                for i, decision in enumerate(proposal.decisions, 1):
                    print(f'  {i}. {decision.item_code} (Project {decision.project_id})')
                    print(f'     Supplier: {decision.supplier_name}')
                    print(f'     Quantity: {decision.quantity}')
                    print(f'     Unit Cost: {decision.unit_cost:,.2f} IRR')
                    print(f'     Total Cost: {decision.final_cost:,.2f} IRR')
                    print(f'     Purchase Date: {decision.purchase_date}')
                    print(f'     Delivery Date: {decision.delivery_date}')
                    print()
            
            if result.items_optimized == 3:
                print(f'✅ SUCCESS: All 3 items optimized with demand fulfillment!')
            elif result.items_optimized > 1:
                print(f'✅ PARTIAL SUCCESS: {result.items_optimized} items optimized (better than before)')
            else:
                print(f'⚠️  Still only {result.items_optimized} item optimized')
                
            break
        except Exception as e:
            print(f'\n❌ ERROR: {e}')
            import traceback
            traceback.print_exc()
            break

asyncio.run(test_demand_fulfillment_optimization())
