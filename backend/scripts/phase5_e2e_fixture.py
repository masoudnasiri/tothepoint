"""
Create deterministic fixture data for Phase 5 lock-coverage E2E checks.

Prints JSON with decision IDs:
- fail_decision_id: should fail LOCK due to incomplete coverage
- pass_target_decision_id: should pass LOCK (combined with existing locked package)
"""

import asyncio
import json
import time
from datetime import date, datetime
from decimal import Decimal

from app.database import AsyncSessionLocal
import app.models_invoice_payment  # noqa: F401 - ensure relationship registry is populated
from app.models import (
    FinalizedDecision,
    ItemMaster,
    ItemSubItem,
    PackageSubItem,
    ProcurementOption,
    ProcurementPackage,
    Project,
    ProjectItem,
    ProjectItemSubItem,
)


async def _create_decision(db, project, item, package, supplier_name, status):
    option = ProcurementOption(
        package_id=package.id,
        project_item_id=item.id,
        item_code=item.item_code,
        supplier_name=supplier_name,
        cost_amount=Decimal("1000"),
        cost_currency="IRR",
        base_cost=Decimal("1000"),
        payment_terms={"type": "cash"},
        is_active=True,
        is_finalized=True,
    )
    db.add(option)
    await db.flush()

    decision = FinalizedDecision(
        project_id=project.id,
        project_item_id=item.id,
        package_id=package.id,
        item_code=item.item_code,
        procurement_option_id=option.id,
        purchase_date=date.today(),
        delivery_date=date.today(),
        quantity=1,
        final_cost_amount=Decimal("1000"),
        final_cost_currency="IRR",
        final_cost=Decimal("1000"),
        decision_maker_id=1,
        decision_date=datetime.utcnow(),
        status=status,
    )
    db.add(decision)
    await db.flush()
    return decision


async def main():
    suffix = str(int(time.time()))
    async with AsyncSessionLocal() as db:
        # FAIL scenario: incomplete coverage (2/5)
        p_fail = Project(
            project_code=f"PH5FAIL-{suffix}",
            name="Phase5 Fail Scenario",
            priority_weight=5,
            is_active=True,
        )
        db.add(p_fail)
        await db.flush()

        pi_fail = ProjectItem(
            project_id=p_fail.id,
            item_code=f"PH5-FAIL-ITEM-{suffix}",
            item_name="Phase5 Fail Item",
            quantity=1,
            delivery_options=[],
            status="PENDING",
            is_finalized=True,
        )
        db.add(pi_fail)
        await db.flush()

        im_fail = ItemMaster(
            item_code=f"PH5-FAIL-MASTER-{suffix}",
            company="TestCo",
            item_name="Fail Master",
            model="M1",
            is_active=True,
        )
        db.add(im_fail)
        await db.flush()

        isi_fail = ItemSubItem(
            item_master_id=im_fail.id,
            name="CPU",
            part_number=f"PN-FAIL-{suffix}",
        )
        db.add(isi_fail)
        await db.flush()

        pis_fail = ProjectItemSubItem(
            project_item_id=pi_fail.id,
            item_subitem_id=isi_fail.id,
            quantity=5,
        )
        db.add(pis_fail)
        await db.flush()

        pkg_fail = ProcurementPackage(
            project_item_id=pi_fail.id,
            package_name=f"FailPkg-{suffix}",
            package_type="PARTIAL",
            is_active=True,
            main_item_quantity=1,
        )
        db.add(pkg_fail)
        await db.flush()

        db.add(
            PackageSubItem(
                package_id=pkg_fail.id,
                project_item_subitem_id=pis_fail.id,
                quantity_covered=2,
                is_fully_covered=False,
                coverage_percentage=Decimal("40.0"),
            )
        )
        await db.flush()

        dec_fail = await _create_decision(db, p_fail, pi_fail, pkg_fail, "Supplier Fail", "PROPOSED")

        # PASS scenario: locked package A (2/5) + target package B (3/5) => complete
        p_pass = Project(
            project_code=f"PH5PASS-{suffix}",
            name="Phase5 Pass Scenario",
            priority_weight=5,
            is_active=True,
        )
        db.add(p_pass)
        await db.flush()

        pi_pass = ProjectItem(
            project_id=p_pass.id,
            item_code=f"PH5-PASS-ITEM-{suffix}",
            item_name="Phase5 Pass Item",
            quantity=1,
            delivery_options=[],
            status="PENDING",
            is_finalized=True,
        )
        db.add(pi_pass)
        await db.flush()

        im_pass = ItemMaster(
            item_code=f"PH5-PASS-MASTER-{suffix}",
            company="TestCo",
            item_name="Pass Master",
            model="M1",
            is_active=True,
        )
        db.add(im_pass)
        await db.flush()

        isi_pass = ItemSubItem(
            item_master_id=im_pass.id,
            name="RAM",
            part_number=f"PN-PASS-{suffix}",
        )
        db.add(isi_pass)
        await db.flush()

        pis_pass = ProjectItemSubItem(
            project_item_id=pi_pass.id,
            item_subitem_id=isi_pass.id,
            quantity=5,
        )
        db.add(pis_pass)
        await db.flush()

        pkg_a = ProcurementPackage(
            project_item_id=pi_pass.id,
            package_name=f"PassPkgA-{suffix}",
            package_type="PARTIAL",
            is_active=True,
            main_item_quantity=1,
        )
        pkg_b = ProcurementPackage(
            project_item_id=pi_pass.id,
            package_name=f"PassPkgB-{suffix}",
            package_type="PARTIAL",
            is_active=True,
            main_item_quantity=1,
        )
        db.add(pkg_a)
        db.add(pkg_b)
        await db.flush()

        db.add(
            PackageSubItem(
                package_id=pkg_a.id,
                project_item_subitem_id=pis_pass.id,
                quantity_covered=2,
                is_fully_covered=False,
                coverage_percentage=Decimal("40.0"),
            )
        )
        db.add(
            PackageSubItem(
                package_id=pkg_b.id,
                project_item_subitem_id=pis_pass.id,
                quantity_covered=3,
                is_fully_covered=False,
                coverage_percentage=Decimal("60.0"),
            )
        )
        await db.flush()

        dec_locked = await _create_decision(db, p_pass, pi_pass, pkg_a, "Supplier A", "LOCKED")
        dec_target = await _create_decision(db, p_pass, pi_pass, pkg_b, "Supplier B", "PROPOSED")

        await db.commit()

        print(
            json.dumps(
                {
                    "suffix": suffix,
                    "fail_decision_id": dec_fail.id,
                    "pass_locked_decision_id": dec_locked.id,
                    "pass_target_decision_id": dec_target.id,
                    "fail_project_item_id": pi_fail.id,
                    "pass_project_item_id": pi_pass.id,
                }
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
