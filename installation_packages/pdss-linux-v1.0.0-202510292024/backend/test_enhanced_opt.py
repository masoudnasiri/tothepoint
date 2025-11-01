import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.optimization_engine_enhanced import EnhancedProcurementOptimizer
from app.schemas import OptimizationRunRequest

async def test_enhanced_optimization():
    async for db in get_db():
        try:
            print('🚀 Testing enhanced optimization engine...')
            
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
            
            print(f'\n🎉 ENHANCED OPTIMIZATION RESULTS:')
            print(f'📊 Status: {result.status}')
            print(f'📦 Items optimized: {result.items_optimized}')
            print(f'💰 Total cost: {result.total_cost:,.2f} IRR')
            print(f'⏱️  Execution time: {result.execution_time_seconds:.2f} seconds')
            print(f'📋 Proposals: {len(result.proposals)}')
            
            if result.proposals:
                for i, proposal in enumerate(result.proposals):
                    print(f'  Proposal {i+1}: {proposal.proposal_name}')
                    print(f'    Strategy: {proposal.strategy_type}')
                    print(f'    Items: {proposal.items_count}')
                    print(f'    Cost: ${proposal.total_cost:,.2f}')
                    print(f'    Decisions: {len(proposal.decisions)}')
                    
            if result.items_optimized > 0:
                print(f'✅ SUCCESS: Enhanced optimization working!')
            else:
                print(f'⚠️  No items optimized - may need data fixes')
                
            break
        except Exception as e:
            print(f'\n❌ ERROR: {e}')
            import traceback
            traceback.print_exc()
            break

asyncio.run(test_enhanced_optimization())
