#!/usr/bin/env python3
"""
Minimal CP-SAT Test
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
from app.optimization_engine_enhanced import EnhancedProcurementOptimizer, OptimizationRunRequest, OptimizationStrategy
from app.schemas import OptimizationRunRequest

async def test_minimal_cpsat():
    """Test CP-SAT with minimal setup"""
    print("🧪 MINIMAL CP-SAT TEST")
    print("=" * 30)
    
    async for db in get_db():
        try:
            # Initialize optimizer
            optimizer = EnhancedProcurementOptimizer(db)
            
            print("🔄 Loading data...")
            await optimizer._load_data()
            print(f"✅ Loaded {len(optimizer.project_items)} items, {len(optimizer.procurement_options)} options")
            
            print("🔄 Building dependency graph...")
            optimizer._build_dependency_graph()
            print("✅ Dependency graph built")
            
            print("🔄 Testing CP-SAT model creation...")
            from ortools.sat.python import cp_model
            
            model = cp_model.CpModel()
            variables = {}
            
            # Create just a few variables for testing
            test_items = optimizer.project_items[:3]  # Only first 3 items
            test_options = list(optimizer.procurement_options.values())[:5]  # Only first 5 options
            
            print(f"Testing with {len(test_items)} items and {len(test_options)} options")
            
            for item in test_items:
                for option in test_options:
                    if option.item_code == item.item_code:
                        var_name = f"test_{item.project_id}_{item.item_code}_{option.id}"
                        variables[var_name] = model.NewBoolVar(var_name)
                        print(f"  Created variable: {var_name}")
                        break  # Only one option per item for testing
            
            print(f"✅ Created {len(variables)} variables")
            
            # Test basic constraint
            if variables:
                var_list = list(variables.values())
                model.Add(sum(var_list) <= 2)  # Simple constraint
                print("✅ Added basic constraint")
            
            # Test solver
            print("🔄 Testing solver...")
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = 5
            
            status = solver.Solve(model)
            print(f"✅ Solver completed with status: {status}")
            
            break
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            break

if __name__ == "__main__":
    asyncio.run(test_minimal_cpsat())
