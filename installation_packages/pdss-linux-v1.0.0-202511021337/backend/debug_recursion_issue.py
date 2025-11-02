#!/usr/bin/env python3
"""
Debug Recursion Issue in Enhanced Optimization
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

async def debug_recursion():
    """Debug the recursion issue step by step"""
    print("🔍 DEBUGGING RECURSION ISSUE")
    print("=" * 40)
    
    async for db in get_db():
        try:
            # Initialize optimizer
            optimizer = EnhancedProcurementOptimizer(db, solver_type=SolverType.CP_SAT)
            
            print("🔄 Loading data...")
            await optimizer._load_data()
            
            print(f"✅ Data loaded successfully:")
            print(f"   Projects: {len(optimizer.projects)}")
            print(f"   Project items: {len(optimizer.project_items)}")
            print(f"   Procurement options: {len(optimizer.procurement_options)}")
            print(f"   Budget data: {len(optimizer.budget_data)}")
            
            # Test building dependency graph
            print("\n🔄 Building dependency graph...")
            try:
                optimizer._build_dependency_graph()
                print("✅ Dependency graph built successfully")
            except Exception as e:
                print(f"❌ Dependency graph failed: {e}")
                import traceback
                traceback.print_exc()
                return
            
            # Test CP-SAT model building
            print("\n🔄 Building CP-SAT model...")
            try:
                request = OptimizationRunRequest(
                    max_time_slots=6,
                    time_limit_seconds=15,
                    budget_limit=1000000,
                    solver_type="CP_SAT"
                )
                
                # Test just the model building part
                model = await optimizer._solve_with_cpsat(request, OptimizationStrategy.PRIORITY_WEIGHTED)
                if model:
                    print("✅ CP-SAT model built successfully")
                else:
                    print("❌ CP-SAT model returned None")
                    
            except Exception as e:
                print(f"❌ CP-SAT model building failed: {e}")
                import traceback
                traceback.print_exc()
                return
            
            print("\n🎉 All steps completed successfully!")
            break
            
        except Exception as e:
            print(f"❌ Debug failed: {str(e)}")
            import traceback
            traceback.print_exc()
            break

if __name__ == "__main__":
    asyncio.run(debug_recursion())
