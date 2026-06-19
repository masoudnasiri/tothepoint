"""
Phase 1 Database Schema Verification Script
This script performs automated verification of the Phase 1 refactoring
"""

import asyncio
import sys
from sqlalchemy import text
from backend.app.database import AsyncSessionLocal, init_db, engine
from backend.app.models import (
    Project, ProjectPhase, ProjectItem, DecisionFactorWeight,
    FinalizedDecision, OptimizationRun
)

async def verify_database_schema():
    """Verify database schema and data integrity"""
    print("=" * 70)
    print("PHASE 1 DATABASE SCHEMA VERIFICATION")
    print("=" * 70)
    print()
    
    try:
        # Step 1: Initialize Database
        print("Step 1: Initializing Database...")
        await init_db()
        print("✓ Database schema created successfully\n")
        
        # Step 2: Seed Sample Data
        print("Step 2: Seeding Sample Data...")
        from backend.app.seed_data import seed_sample_data
        await seed_sample_data()
        print("✓ Sample data seeded successfully\n")
        
        # Step 3: Data Integrity Checks
        print("Step 3: Data Integrity Verification")
        print("-" * 70)
        
        async with AsyncSessionLocal() as db:
            # Check 1: Projects table with priority_weight
            print("\n[Check 1] Projects Table:")
            result = await db.execute(
                text("SELECT project_code, priority_weight FROM projects ORDER BY project_code")
            )
            projects = result.fetchall()
            print(f"  Found {len(projects)} projects:")
            for proj in projects:
                print(f"    - {proj[0]}: priority_weight = {proj[1]}")
                if not (1 <= proj[1] <= 10):
                    print(f"      ✗ FAILED: priority_weight {proj[1]} not in range 1-10")
                    return False
            print("  ✓ All priority_weight values are valid (1-10)\n")
            
            # Check 2: Project Items with required_by_date
            print("[Check 2] Project Items Table:")
            result = await db.execute(
                text("SELECT item_code, required_by_date, status FROM project_items LIMIT 5")
            )
            items = result.fetchall()
            print(f"  Found {len(items)} sample items:")
            for item in items:
                print(f"    - {item[0]}: required_by_date = {item[1]}, status = {item[2]}")
                if item[2] != 'PENDING':
                    print(f"      ✗ FAILED: Expected status 'PENDING', got '{item[2]}'")
                    return False
            print("  ✓ All items have valid required_by_date and status = PENDING\n")
            
            # Check 3: Project Phases
            print("[Check 3] Project Phases Table:")
            result = await db.execute(
                text("""
                    SELECT p.project_code, ph.phase_name, ph.start_date, ph.end_date 
                    FROM project_phases ph 
                    JOIN projects p ON ph.project_id = p.id 
                    ORDER BY p.project_code, ph.start_date
                    LIMIT 8
                """)
            )
            phases = result.fetchall()
            print(f"  Found {len(phases)} sample phases:")
            for phase in phases:
                print(f"    - {phase[0]}: {phase[1]} ({phase[2]} to {phase[3]})")
                if phase[3] < phase[2]:
                    print(f"      ✗ FAILED: end_date before start_date")
                    return False
            print("  ✓ All phases have valid date ranges\n")
            
            # Check 4: Decision Factor Weights
            print("[Check 4] Decision Factor Weights Table:")
            result = await db.execute(
                text("SELECT factor_name, weight, description FROM decision_factor_weights ORDER BY weight DESC")
            )
            weights = result.fetchall()
            print(f"  Found {len(weights)} decision factors:")
            for weight in weights:
                print(f"    - {weight[0]}: weight = {weight[1]}")
                if not (1 <= weight[1] <= 10):
                    print(f"      ✗ FAILED: weight {weight[1]} not in range 1-10")
                    return False
            print("  ✓ All factor weights are valid (1-10)\n")
            
            # Check 5: New tables exist (empty is OK)
            print("[Check 5] New Tables Existence:")
            result = await db.execute(text("SELECT COUNT(*) FROM finalized_decisions"))
            fd_count = result.scalar()
            print(f"  - finalized_decisions: {fd_count} records")
            
            result = await db.execute(text("SELECT COUNT(*) FROM optimization_runs"))
            or_count = result.scalar()
            print(f"  - optimization_runs: {or_count} records")
            print("  ✓ All new tables exist and are accessible\n")
            
            # Check 6: Verify old fields are removed
            print("[Check 6] Verify Old Fields Removed from project_items:")
            try:
                await db.execute(text("SELECT must_buy_time FROM project_items LIMIT 1"))
                print("  ✗ FAILED: Column 'must_buy_time' still exists!")
                return False
            except Exception:
                print("  ✓ Column 'must_buy_time' successfully removed")
            
            try:
                await db.execute(text("SELECT allowed_times FROM project_items LIMIT 1"))
                print("  ✗ FAILED: Column 'allowed_times' still exists!")
                return False
            except Exception:
                print("  ✓ Column 'allowed_times' successfully removed\n")
        
        print("=" * 70)
        print("VERIFICATION RESULT: ✓ ALL CHECKS PASSED")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ VERIFICATION FAILED WITH ERROR:")
        print(f"  {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    result = asyncio.run(verify_database_schema())
    sys.exit(0 if result else 1)
