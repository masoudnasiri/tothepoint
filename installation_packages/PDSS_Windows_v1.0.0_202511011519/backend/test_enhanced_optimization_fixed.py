#!/usr/bin/env python3
"""
Test Enhanced Optimization Engine After Fix
"""

import asyncio
import sys
import os
from datetime import datetime, date
from decimal import Decimal
import json

# Add the app directory to the path
sys.path.append('/app')

from app.database import get_db
from app.optimization_engine_enhanced import EnhancedProcurementOptimizer, SolverType, OptimizationStrategy
from app.schemas import OptimizationRunRequest

async def test_enhanced_optimization():
    """Test the enhanced optimization engine after fixing recursion issue"""
    print("🧪 TESTING ENHANCED OPTIMIZATION ENGINE (FIXED)")
    print("=" * 60)
    
    async for db in get_db():
        try:
            # Create optimization request
            request = OptimizationRunRequest(
                max_time_slots=6,  # Reduced time slots
                time_limit_seconds=15,  # Shorter time limit
                budget_limit=1000000,  # 1M budget
                solver_type="CP_SAT"
            )
            
            # Initialize enhanced optimizer
            optimizer = EnhancedProcurementOptimizer(db, solver_type=SolverType.CP_SAT)
            
            print("🔄 Running enhanced optimization...")
            result = await optimizer.run_optimization(
                request,
                generate_multiple_proposals=False,
                strategies=[OptimizationStrategy.PRIORITY_WEIGHTED]
            )
            
            print(f"✅ Optimization completed!")
            print(f"   Status: {result.status}")
            print(f"   Execution time: {result.execution_time_seconds:.2f}s")
            print(f"   Proposals: {len(result.proposals)}")
            print(f"   Message: {result.message}")
            
            if result.proposals:
                print(f"\n🎉 ENHANCED OPTIMIZATION ENGINE IS WORKING!")
                for i, proposal in enumerate(result.proposals[:2]):  # Show first 2 proposals
                    print(f"\n   --- Proposal {i+1} ---")
                    print(f"     Strategy: {proposal.strategy_type}")
                    print(f"     Total Cost: {proposal.total_cost}")
                    print(f"     Items Count: {proposal.items_count}")
                    print(f"     Status: {proposal.status}")
            else:
                print(f"\n❌ No proposals generated")
            
            break
            
        except Exception as e:
            print(f"❌ Optimization failed: {str(e)}")
            import traceback
            traceback.print_exc()
            break

if __name__ == "__main__":
    asyncio.run(test_enhanced_optimization())
