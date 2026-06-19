#!/usr/bin/env python3
"""
Test Original Optimization Engine
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
from app.optimization_engine import ProcurementOptimizer
from app.schemas import OptimizationRunRequest

async def test_original_optimization():
    """Test the original optimization engine"""
    print("🧪 TESTING ORIGINAL OPTIMIZATION ENGINE")
    print("=" * 50)
    
    async for db in get_db():
        try:
            # Create optimization request
            request = OptimizationRunRequest(
                max_time_slots=6,  # Reduced time slots
                time_limit_seconds=15,  # Shorter time limit
                budget_limit=1000000,  # 1M budget
                solver_type="CP_SAT"
            )
            
            # Initialize original optimizer
            optimizer = ProcurementOptimizer(db)
            
            print("🔄 Running original optimization...")
            result = await optimizer.run_optimization(request)
            
            print(f"✅ Optimization completed!")
            print(f"   Status: {result.status}")
            print(f"   Execution time: {result.execution_time_seconds:.2f}s")
            print(f"   Items optimized: {result.items_optimized}")
            print(f"   Total cost: {result.total_cost}")
            print(f"   Message: {result.message}")
            
            if result.status in ["OPTIMAL", "FEASIBLE"]:
                print("\n🎉 ORIGINAL OPTIMIZATION ENGINE IS WORKING!")
            else:
                print(f"\n❌ Original optimization failed: {result.status}")
            
            break
            
        except Exception as e:
            print(f"❌ Optimization failed: {str(e)}")
            import traceback
            traceback.print_exc()
            break

if __name__ == "__main__":
    asyncio.run(test_original_optimization())
