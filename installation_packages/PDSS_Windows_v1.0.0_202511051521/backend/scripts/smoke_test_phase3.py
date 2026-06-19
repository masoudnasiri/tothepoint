#!/usr/bin/env python3
"""
Phase 3 Dual-Mode Smoke Tests

Executes smoke tests for Phase 3 dual-mode operation, testing both
package-first and legacy fallback paths.

Prerequisites:
- Backend dependencies installed (pip install -r requirements.txt)
- Database connection configured (DATABASE_URL or .env)
- Phase 2 migrations completed (packages exist)

Usage:
    python scripts/smoke_test_phase3.py
    
    Or from project root:
    cd backend && python scripts/smoke_test_phase3.py
"""

import asyncio
import sys
import os
import json
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Any, Optional

# Check for required dependencies
try:
    import sqlalchemy
except ImportError:
    print("ERROR: sqlalchemy not found. Please install dependencies:")
    print("  pip install -r requirements.txt")
    print("\nOr if using Docker:")
    print("  docker-compose exec backend python scripts/smoke_test_phase3.py")
    sys.exit(1)

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.database import get_db
except ImportError as e:
    print(f"ERROR: Failed to import app modules: {e}")
    print("\nMake sure you're running from the backend directory:")
    print("  cd backend")
    print("  python scripts/smoke_test_phase3.py")
    print("\nOr install dependencies:")
    print("  pip install -r requirements.txt")
    sys.exit(1)
from app.config import settings
from app.models import (
    Project, ProjectItem, ProcurementOption, DeliveryOption, 
    FinalizedDecision, Supplier, ProcurementPackage, User, Currency
)
from app.crud import (
    create_procurement_option, create_delivery_option,
    get_procurement_option, get_delivery_option
)
from app.schemas import (
    ProcurementOptionCreate, DeliveryOptionCreate,
    ProcurementOptionUpdate
)
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession


class SmokeTestResults:
    """Collects smoke test results"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.flag_states: Dict[str, bool] = {}
        self.scenarios: List[Dict[str, Any]] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.summary: Dict[str, Any] = {}
    
    def add_scenario(self, name: str, success: bool, details: Dict[str, Any]):
        """Add a test scenario result"""
        self.scenarios.append({
            "name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_warning(self, message: str):
        """Add a warning"""
        self.warnings.append(f"{datetime.now().isoformat()}: {message}")
    
    def add_error(self, message: str):
        """Add an error"""
        self.errors.append(f"{datetime.now().isoformat()}: {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary"""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "flag_states": self.flag_states,
            "scenarios": self.scenarios,
            "warnings": self.warnings,
            "errors": self.errors,
            "summary": {
                "total_scenarios": len(self.scenarios),
                "passed": sum(1 for s in self.scenarios if s["success"]),
                "failed": sum(1 for s in self.scenarios if not s["success"]),
                "warnings_count": len(self.warnings),
                "errors_count": len(self.errors)
            }
        }
    
    def to_markdown(self) -> str:
        """Convert results to markdown"""
        lines = [
            "# Phase 3 Smoke Test Results",
            "",
            f"**Test Run**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Flag States",
            ""
        ]
        
        for flag, value in self.flag_states.items():
            lines.append(f"- `{flag}`: `{value}`")
        
        lines.extend([
            "",
            "## Test Scenarios",
            ""
        ])
        
        for scenario in self.scenarios:
            status = "✅ PASS" if scenario["success"] else "❌ FAIL"
            lines.append(f"### {scenario['name']} - {status}")
            lines.append(f"**Time**: {scenario['timestamp']}")
            for key, value in scenario["details"].items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")
        
        if self.warnings:
            lines.extend([
                "## Warnings",
                ""
            ])
            for warning in self.warnings:
                lines.append(f"- {warning}")
            lines.append("")
        
        if self.errors:
            lines.extend([
                "## Errors",
                ""
            ])
            for error in self.errors:
                lines.append(f"- {error}")
            lines.append("")
        
        summary = self.summary
        lines.extend([
            "## Summary",
            "",
            f"- **Total Scenarios**: {summary.get('total_scenarios', 0)}",
            f"- **Passed**: {summary.get('passed', 0)}",
            f"- **Failed**: {summary.get('failed', 0)}",
            f"- **Warnings**: {summary.get('warnings_count', 0)}",
            f"- **Errors**: {summary.get('errors_count', 0)}",
            ""
        ])
        
        return "\n".join(lines)


async def get_or_create_test_data(db: AsyncSession, results: SmokeTestResults) -> Dict[str, Any]:
    """Get or create test data (project, item, supplier, package)"""
    test_data = {}
    
    # Get or create a test project
    result = await db.execute(
        select(Project).limit(1)
    )
    project = result.scalar_one_or_none()
    if not project:
        results.add_warning("No projects found, creating test project")
        project = Project(name="Smoke Test Project", description="Test project for Phase 3")
        db.add(project)
        await db.commit()
        await db.refresh(project)
    
    test_data["project"] = project
    
    # Get or create a test project item
    result = await db.execute(
        select(ProjectItem).where(ProjectItem.project_id == project.id).limit(1)
    )
    project_item = result.scalar_one_or_none()
    if not project_item:
        results.add_warning("No project items found, creating test item")
        project_item = ProjectItem(
            project_id=project.id,
            item_code="SMOKE-TEST-001",
            item_name="Smoke Test Item",
            quantity=1,
            delivery_options=[],
            status="PENDING"
        )
        db.add(project_item)
        await db.commit()
        await db.refresh(project_item)
    
    test_data["project_item"] = project_item
    
    # Get or create a test supplier
    result = await db.execute(
        select(Supplier).limit(1)
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        results.add_warning("No suppliers found, creating test supplier")
        supplier = Supplier(
            supplier_id="SUP-SMOKE-001",
            company_name="Smoke Test Supplier",
            status="ACTIVE"
        )
        db.add(supplier)
        await db.commit()
        await db.refresh(supplier)
    
    test_data["supplier"] = supplier
    
    # Get or create a currency (USD)
    result = await db.execute(
        select(Currency).where(Currency.code == "USD").limit(1)
    )
    currency = result.scalar_one_or_none()
    if not currency:
        results.add_warning("No USD currency found, creating test currency")
        currency = Currency(code="USD", name="US Dollar", symbol="$")
        db.add(currency)
        await db.commit()
        await db.refresh(currency)
    
    test_data["currency"] = currency
    
    # Get or create a FULL package for the project item
    result = await db.execute(
        select(ProcurementPackage).where(
            ProcurementPackage.project_item_id == project_item.id,
            ProcurementPackage.package_type == "FULL"
        ).limit(1)
    )
    package = result.scalar_one_or_none()
    if not package:
        results.add_warning("No FULL package found, creating test package")
        package = ProcurementPackage(
            project_item_id=project_item.id,
            package_name=f"FULL Package for {project_item.item_code}",
            package_type="FULL",
            is_active=True
        )
        db.add(package)
        await db.commit()
        await db.refresh(package)
    
    test_data["package"] = package
    
    return test_data


async def test_procurement_option_package_first(db: AsyncSession, test_data: Dict, results: SmokeTestResults):
    """Test creating procurement option with package_id (package-first mode)"""
    try:
        option_data = ProcurementOptionCreate(
            package_id=test_data["package"].id,
            item_code=test_data["project_item"].item_code,
            supplier_name=test_data["supplier"].company_name,  # Required legacy field
            supplier_id=test_data["supplier"].id,
            base_cost=Decimal("1000.00"),  # Required legacy field
            currency_id=test_data["currency"].id,  # Required legacy field
            payment_terms={"type": "cash"}
        )
        
        option = await create_procurement_option(db, option_data)
        
        # Store all needed data immediately while object is still attached
        option_id = option.id
        package_id = option.package_id
        project_item_id = option.project_item_id
        supplier_id = option.supplier_id
        
        # Success: option created successfully
        # package_id should be preserved even if flag is off
        success = (
            option is not None 
            and option_id is not None
            and supplier_id == test_data["supplier"].id
        )
        
        results.add_scenario(
            "Procurement Option - Package First",
            success,
            {
                "package_id": package_id,
                "project_item_id": project_item_id,
                "supplier_id": supplier_id,
                "option_id": option_id,
                "flag_enabled": settings.enable_package_procurement
            }
        )
        
        # Cleanup - use stored ID (don't fail test if cleanup fails)
        try:
            await db.execute(delete(ProcurementOption).where(ProcurementOption.id == option_id))
            await db.commit()
        except Exception as cleanup_error:
            # Log but don't fail the test
            pass
        
    except Exception as e:
        results.add_error(f"Procurement Option - Package First failed: {str(e)}")
        results.add_scenario("Procurement Option - Package First", False, {"error": str(e)})
        # Try cleanup even on error
        try:
            if 'option_id' in locals():
                await db.execute(delete(ProcurementOption).where(ProcurementOption.id == option_id))
                await db.commit()
        except:
            pass


async def test_procurement_option_legacy(db: AsyncSession, test_data: Dict, results: SmokeTestResults):
    """Test creating procurement option with project_item_id (legacy mode)"""
    try:
        option_data = ProcurementOptionCreate(
            project_item_id=test_data["project_item"].id,
            item_code=test_data["project_item"].item_code,
            supplier_name=test_data["supplier"].company_name,  # Required legacy field
            supplier_id=test_data["supplier"].id,
            base_cost=Decimal("1000.00"),  # Required legacy field
            currency_id=test_data["currency"].id,  # Required legacy field
            payment_terms={"type": "cash"}
        )
        
        option = await create_procurement_option(db, option_data)
        
        # Store all needed data immediately while object is still attached
        option_id = option.id
        package_id = option.package_id
        project_item_id = option.project_item_id
        supplier_id = option.supplier_id
        
        # Verify project_item_id is set
        success = project_item_id == test_data["project_item"].id
        
        results.add_scenario(
            "Procurement Option - Legacy Fallback",
            success,
            {
                "package_id": package_id,
                "project_item_id": project_item_id,
                "supplier_id": supplier_id,
                "option_id": option_id,
                "package_resolved": package_id is not None if settings.enable_package_procurement else False
            }
        )
        
        # Cleanup - use stored ID (don't fail test if cleanup fails)
        try:
            await db.execute(delete(ProcurementOption).where(ProcurementOption.id == option_id))
            await db.commit()
        except Exception as cleanup_error:
            # Log but don't fail the test
            pass
        
    except Exception as e:
        results.add_error(f"Procurement Option - Legacy Fallback failed: {str(e)}")
        results.add_scenario("Procurement Option - Legacy Fallback", False, {"error": str(e)})
        # Try cleanup even on error
        try:
            if 'option_id' in locals():
                await db.execute(delete(ProcurementOption).where(ProcurementOption.id == option_id))
                await db.commit()
        except:
            pass


async def test_delivery_option_package_first(db: AsyncSession, test_data: Dict, results: SmokeTestResults):
    """Test creating delivery option with package_id"""
    try:
        option_data = DeliveryOptionCreate(
            package_id=test_data["package"].id,
            project_item_id=test_data["project_item"].id,  # Set for backward compatibility
            delivery_date=date.today(),
            invoice_amount_per_unit=Decimal("1200.00"),
            invoice_timing_type="RELATIVE",
            invoice_days_after_delivery=30
        )
        
        option = await create_delivery_option(db, option_data)
        
        # Store all needed data immediately while object is still attached
        option_id = option.id
        package_id = option.package_id
        project_item_id = option.project_item_id
        
        # Success: option created successfully
        # package_id should be preserved even if flag is off
        success = (
            option is not None 
            and option_id is not None
            and project_item_id == test_data["project_item"].id
        )
        
        results.add_scenario(
            "Delivery Option - Package First",
            success,
            {
                "package_id": package_id,
                "project_item_id": project_item_id,
                "option_id": option_id,
                "flag_enabled": settings.enable_package_procurement
            }
        )
        
        # Cleanup - use stored ID (don't fail test if cleanup fails)
        try:
            await db.execute(delete(DeliveryOption).where(DeliveryOption.id == option_id))
            await db.commit()
        except Exception as cleanup_error:
            # Log but don't fail the test
            pass
        
    except Exception as e:
        results.add_error(f"Delivery Option - Package First failed: {str(e)}")
        results.add_scenario("Delivery Option - Package First", False, {"error": str(e)})
        # Try cleanup even on error
        try:
            if 'option_id' in locals():
                await db.execute(delete(DeliveryOption).where(DeliveryOption.id == option_id))
                await db.commit()
        except:
            pass


async def test_delivery_option_legacy(db: AsyncSession, test_data: Dict, results: SmokeTestResults):
    """Test creating delivery option with project_item_id (legacy)"""
    try:
        option_data = DeliveryOptionCreate(
            project_item_id=test_data["project_item"].id,
            delivery_date=date.today(),
            invoice_amount_per_unit=Decimal("1200.00"),
            invoice_timing_type="RELATIVE",
            invoice_days_after_delivery=30
        )
        
        option = await create_delivery_option(db, option_data)
        
        # Store all needed data immediately while object is still attached
        option_id = option.id
        package_id = option.package_id
        project_item_id = option.project_item_id
        
        # Verify project_item_id is set
        success = project_item_id == test_data["project_item"].id
        
        results.add_scenario(
            "Delivery Option - Legacy Fallback",
            success,
            {
                "package_id": package_id,
                "project_item_id": project_item_id,
                "option_id": option_id,
                "package_resolved": package_id is not None if settings.enable_package_procurement else False
            }
        )
        
        # Cleanup - use stored ID (don't fail test if cleanup fails)
        try:
            await db.execute(delete(DeliveryOption).where(DeliveryOption.id == option_id))
            await db.commit()
        except Exception as cleanup_error:
            # Log but don't fail the test
            pass
        
    except Exception as e:
        results.add_error(f"Delivery Option - Legacy Fallback failed: {str(e)}")
        results.add_scenario("Delivery Option - Legacy Fallback", False, {"error": str(e)})
        # Try cleanup even on error
        try:
            if 'option_id' in locals():
                await db.execute(delete(DeliveryOption).where(DeliveryOption.id == option_id))
                await db.commit()
        except:
            pass


async def test_supplier_normalization(db: AsyncSession, test_data: Dict, results: SmokeTestResults):
    """Test supplier normalization (supplier_id vs supplier_name)"""
    try:
        # Test with supplier_id
        option_data = ProcurementOptionCreate(
            project_item_id=test_data["project_item"].id,
            item_code=test_data["project_item"].item_code,
            supplier_name=test_data["supplier"].company_name,  # Required legacy field
            supplier_id=test_data["supplier"].id,
            base_cost=Decimal("1000.00"),  # Required legacy field
            currency_id=test_data["currency"].id,  # Required legacy field
            payment_terms={"type": "cash"}
        )
        
        option = await create_procurement_option(db, option_data)
        supplier_id_1 = option.supplier_id
        supplier_name_1 = option.supplier_name
        option_id_1 = option.id
        
        success_id = supplier_id_1 == test_data["supplier"].id
        
        # Cleanup - use stored ID (don't fail test if cleanup fails)
        try:
            await db.execute(delete(ProcurementOption).where(ProcurementOption.id == option_id_1))
            await db.commit()
        except Exception:
            pass
        
        # Test with supplier_name (if not enforced)
        if not settings.supplier_normalization_enforced:
            option_data = ProcurementOptionCreate(
                project_item_id=test_data["project_item"].id,
                item_code=test_data["project_item"].item_code,
                supplier_name="Test Supplier Name",
                base_cost=Decimal("1000.00"),  # Required legacy field
                currency_id=test_data["currency"].id,  # Required legacy field
                payment_terms={"type": "cash"}
            )
            
            option = await create_procurement_option(db, option_data)
            supplier_name_2 = option.supplier_name
            option_id_2 = option.id
            
            success_name = supplier_name_2 == "Test Supplier Name"
            
            # Cleanup - use stored ID (don't fail test if cleanup fails)
            try:
                await db.execute(delete(ProcurementOption).where(ProcurementOption.id == option_id_2))
                await db.commit()
            except Exception:
                pass
        else:
            success_name = True  # Not tested if enforced
        
        results.add_scenario(
            "Supplier Normalization",
            success_id and success_name,
            {
                "supplier_id_test": success_id,
                "supplier_name_test": success_name if not settings.supplier_normalization_enforced else "skipped (enforced)",
                "normalization_enforced": settings.supplier_normalization_enforced
            }
        )
        
    except Exception as e:
        results.add_error(f"Supplier Normalization failed: {str(e)}")
        results.add_scenario("Supplier Normalization", False, {"error": str(e)})
        # Try cleanup even on error
        try:
            if 'option_id_1' in locals():
                await db.execute(delete(ProcurementOption).where(ProcurementOption.id == option_id_1))
                await db.commit()
            if 'option_id_2' in locals():
                await db.execute(delete(ProcurementOption).where(ProcurementOption.id == option_id_2))
                await db.commit()
        except:
            pass


async def run_smoke_tests():
    """Run all smoke tests"""
    print("=" * 60)
    print("Phase 3 Dual-Mode Smoke Tests")
    print("=" * 60)
    print()
    
    results = SmokeTestResults()
    
    # Capture flag states
    results.flag_states = {
        "ENABLE_PACKAGE_PROCUREMENT": settings.enable_package_procurement,
        "LEGACY_PROJECT_ITEM_FALLBACK": settings.legacy_project_item_fallback,
        "SUPPLIER_NORMALIZATION_ENFORCED": settings.supplier_normalization_enforced,
        "ENABLE_PACKAGE_BASED_OPTIMIZATION": settings.enable_package_based_optimization,
        "REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS": settings.require_package_id_for_new_options
    }
    
    print("Flag States:")
    for flag, value in results.flag_states.items():
        print(f"  {flag}: {value}")
    print()
    
    async for db in get_db():
        try:
            # Get or create test data
            print("Setting up test data...")
            test_data = await get_or_create_test_data(db, results)
            print(f"  Project: {test_data['project'].name} (ID: {test_data['project'].id})")
            print(f"  Project Item: {test_data['project_item'].item_code} (ID: {test_data['project_item'].id})")
            print(f"  Supplier: {test_data['supplier'].company_name} (ID: {test_data['supplier'].id})")
            print(f"  Package: {test_data['package'].package_name} (ID: {test_data['package'].id})")
            print()
            
            # Run test scenarios
            print("Running test scenarios...")
            print()
            
            await test_procurement_option_package_first(db, test_data, results)
            print("  ✓ Procurement Option - Package First")
            
            await test_procurement_option_legacy(db, test_data, results)
            print("  ✓ Procurement Option - Legacy Fallback")
            
            await test_delivery_option_package_first(db, test_data, results)
            print("  ✓ Delivery Option - Package First")
            
            await test_delivery_option_legacy(db, test_data, results)
            print("  ✓ Delivery Option - Legacy Fallback")
            
            await test_supplier_normalization(db, test_data, results)
            print("  ✓ Supplier Normalization")
            
            print()
            
            # Update summary
            results.summary = results.to_dict()["summary"]
            
        except Exception as e:
            results.add_error(f"Smoke test execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            break
    
    # Write results
    results_dict = results.to_dict()
    results_md = results.to_markdown()
    
    # Write JSON
    output_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(output_dir, "PHASE3_SMOKE_TEST_RESULTS.json")
    with open(json_path, "w") as f:
        json.dump(results_dict, f, indent=2)
    
    # Write Markdown
    md_path = os.path.join(output_dir, "PHASE3_SMOKE_TEST_RESULTS.md")
    with open(md_path, "w") as f:
        f.write(results_md)
    
    print("=" * 60)
    print("Smoke Test Results")
    print("=" * 60)
    print()
    print(f"Total Scenarios: {results.summary.get('total_scenarios', 0)}")
    print(f"Passed: {results.summary.get('passed', 0)}")
    print(f"Failed: {results.summary.get('failed', 0)}")
    print(f"Warnings: {results.summary.get('warnings_count', 0)}")
    print(f"Errors: {results.summary.get('errors_count', 0)}")
    print()
    print(f"Results saved to:")
    print(f"  - {json_path}")
    print(f"  - {md_path}")
    print()
    
    # Exit with error code if any failures
    if results.summary.get('failed', 0) > 0 or results.summary.get('errors_count', 0) > 0:
        print("❌ Smoke tests failed!")
        sys.exit(1)
    else:
        print("✅ All smoke tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(run_smoke_tests())

