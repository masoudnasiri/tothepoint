"""
Phase 8 release-candidate demo dataset generator.

Usage:
  python scripts/create_demo_dataset.py --mode create
  python scripts/create_demo_dataset.py --mode cleanup

The script is non-destructive to non-demo data:
- all demo records are tagged with DEMO_RC8_ prefix
- cleanup only removes DEMO_RC8_ tagged rows
"""

import argparse
import asyncio
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List

from fastapi import HTTPException
from sqlalchemy import delete, select

from app.database import AsyncSessionLocal
import app.models_invoice_payment  # noqa: F401  ensure model registry is populated
from app.models import (
    AuditLog,
    CashflowEvent,
    DeliveryOption,
    FinalizedDecision,
    ItemMaster,
    ItemSubItem,
    PackageSubItem,
    ProcurementOption,
    ProcurementPackage,
    Project,
    ProjectItem,
    ProjectItemSubItem,
    Supplier,
    SupplierPayment,
    User,
)
from app.models_invoice_payment import Invoice, InvoiceStatus, Payment, PaymentMethod, PaymentStatus
from app.services.package_service import validate_package_coverage_for_lock


PREFIX = "DEMO_RC8_"


def _coverage_percentage(covered: int, required: int) -> Decimal:
    if required <= 0:
        return Decimal("0")
    return (Decimal(covered) * Decimal("100")) / Decimal(required)


async def _get_or_create_demo_user_id(db) -> int:
    result = await db.execute(
        select(User).where(User.username == f"{PREFIX}system")
    )
    user = result.scalar_one_or_none()
    if user:
        return user.id

    user = User(
        username=f"{PREFIX}system",
        password_hash="demo_hash_not_for_login",
        role="admin",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user.id


async def cleanup_demo_dataset() -> Dict[str, int]:
    deleted = {
        "audit_logs": 0,
        "cashflow_events": 0,
        "supplier_payments": 0,
        "payments": 0,
        "invoices": 0,
        "finalized_decisions": 0,
        "procurement_options": 0,
        "delivery_options": 0,
        "package_subitems": 0,
        "procurement_packages": 0,
        "project_item_subitems": 0,
        "project_items": 0,
        "item_subitems": 0,
        "items_master": 0,
        "suppliers": 0,
        "projects": 0,
        "users": 0,
    }

    async with AsyncSessionLocal() as db:
        project_ids = (
            await db.execute(
                select(Project.id).where(Project.project_code.like(f"{PREFIX}%"))
            )
        ).scalars().all()

        project_item_ids = (
            await db.execute(
                select(ProjectItem.id).where(
                    (ProjectItem.project_id.in_(project_ids)) |
                    (ProjectItem.item_code.like(f"{PREFIX}%"))
                )
            )
        ).scalars().all()

        package_ids = (
            await db.execute(
                select(ProcurementPackage.id).where(
                    (ProcurementPackage.project_item_id.in_(project_item_ids)) |
                    (ProcurementPackage.package_name.like(f"{PREFIX}%"))
                )
            )
        ).scalars().all()

        decision_ids = (
            await db.execute(
                select(FinalizedDecision.id).where(
                    (FinalizedDecision.project_id.in_(project_ids)) |
                    (FinalizedDecision.item_code.like(f"{PREFIX}%"))
                )
            )
        ).scalars().all()

        supplier_ids = (
            await db.execute(
                select(Supplier.id).where(
                    Supplier.supplier_id.like(f"{PREFIX}%")
                )
            )
        ).scalars().all()

        item_master_ids = (
            await db.execute(
                select(ItemMaster.id).where(ItemMaster.item_code.like(f"{PREFIX}%"))
            )
        ).scalars().all()

        item_subitem_ids = (
            await db.execute(
                select(ItemSubItem.id).where(
                    (ItemSubItem.item_master_id.in_(item_master_ids)) |
                    (ItemSubItem.part_number.like(f"{PREFIX}%"))
                )
            )
        ).scalars().all()

        # delete child/linked tables first
        for key, stmt in [
            (
                "audit_logs",
                delete(AuditLog).where(
                    (AuditLog.action.like(f"{PREFIX}%")) |
                    (AuditLog.entity_type == "demo_dataset")
                ),
            ),
            (
                "cashflow_events",
                delete(CashflowEvent).where(
                    (CashflowEvent.related_decision_id.in_(decision_ids)) |
                    (CashflowEvent.description.like(f"%{PREFIX}%"))
                ),
            ),
            (
                "supplier_payments",
                delete(SupplierPayment).where(
                    (SupplierPayment.decision_id.in_(decision_ids)) |
                    (SupplierPayment.item_code.like(f"{PREFIX}%")) |
                    (SupplierPayment.supplier_id.in_(supplier_ids))
                ),
            ),
            (
                "payments",
                delete(Payment).where(
                    (Payment.decision_id.in_(decision_ids)) |
                    (Payment.package_id.in_(package_ids))
                ),
            ),
            (
                "invoices",
                delete(Invoice).where(
                    (Invoice.decision_id.in_(decision_ids)) |
                    (Invoice.package_id.in_(package_ids)) |
                    (Invoice.invoice_number.like(f"{PREFIX}%"))
                ),
            ),
            (
                "finalized_decisions",
                delete(FinalizedDecision).where(FinalizedDecision.id.in_(decision_ids)),
            ),
            (
                "procurement_options",
                delete(ProcurementOption).where(
                    (ProcurementOption.project_item_id.in_(project_item_ids)) |
                    (ProcurementOption.package_id.in_(package_ids)) |
                    (ProcurementOption.item_code.like(f"{PREFIX}%"))
                ),
            ),
            (
                "delivery_options",
                delete(DeliveryOption).where(
                    (DeliveryOption.project_item_id.in_(project_item_ids)) |
                    (DeliveryOption.package_id.in_(package_ids))
                ),
            ),
            (
                "package_subitems",
                delete(PackageSubItem).where(PackageSubItem.package_id.in_(package_ids)),
            ),
            (
                "procurement_packages",
                delete(ProcurementPackage).where(ProcurementPackage.id.in_(package_ids)),
            ),
            (
                "project_item_subitems",
                delete(ProjectItemSubItem).where(ProjectItemSubItem.project_item_id.in_(project_item_ids)),
            ),
            (
                "project_items",
                delete(ProjectItem).where(ProjectItem.id.in_(project_item_ids)),
            ),
            (
                "item_subitems",
                delete(ItemSubItem).where(ItemSubItem.id.in_(item_subitem_ids)),
            ),
            (
                "items_master",
                delete(ItemMaster).where(ItemMaster.id.in_(item_master_ids)),
            ),
            (
                "suppliers",
                delete(Supplier).where(Supplier.id.in_(supplier_ids)),
            ),
            (
                "projects",
                delete(Project).where(Project.id.in_(project_ids)),
            ),
            (
                "users",
                delete(User).where(User.username == f"{PREFIX}system"),
            ),
        ]:
            result = await db.execute(stmt)
            deleted[key] = int(result.rowcount or 0)

        await db.commit()

    return deleted


async def create_demo_dataset() -> Dict[str, object]:
    # Deterministic recreation
    cleanup_summary = await cleanup_demo_dataset()

    async with AsyncSessionLocal() as db:
        user_id = await _get_or_create_demo_user_id(db)

        # Projects
        dc_project = Project(
            project_code=f"{PREFIX}PRJ_DC",
            name=f"{PREFIX}Data Center Infrastructure",
            priority_weight=9,
            is_active=True,
        )
        sec_project = Project(
            project_code=f"{PREFIX}PRJ_SEC",
            name=f"{PREFIX}Monitoring and Security Upgrade",
            priority_weight=7,
            is_active=True,
        )
        db.add(dc_project)
        db.add(sec_project)
        await db.flush()

        # Master items
        server_master = ItemMaster(
            item_code=f"{PREFIX}MASTER_SERVER",
            company="InoTech",
            item_name="Server",
            model="Rivar-RC8",
            category="Infrastructure",
            unit="set",
            description="Demo RC8 decomposed server item",
            is_active=True,
            created_by_id=user_id,
        )
        simple_master = ItemMaster(
            item_code=f"{PREFIX}MASTER_NVR",
            company="SecureWatch",
            item_name="Network Video Recorder",
            model="NVR-64CH",
            category="Security",
            unit="unit",
            description="Demo RC8 simple item (no decomposition)",
            is_active=True,
            created_by_id=user_id,
        )
        db.add(server_master)
        db.add(simple_master)
        await db.flush()

        # Server sub-items
        components = [
            "Case",
            "CPU",
            "Heatsink",
            "RAM",
            "Storage",
            "Power Supply",
            "Rail Kit",
            "Network Card",
        ]
        subitems: List[ItemSubItem] = []
        for comp in components:
            sub = ItemSubItem(
                item_master_id=server_master.id,
                name=comp,
                description=f"{PREFIX}{comp} component",
                part_number=f"{PREFIX}PN_{comp.replace(' ', '_').upper()}",
            )
            db.add(sub)
            subitems.append(sub)
        await db.flush()

        # Project items
        server_item = ProjectItem(
            project_id=dc_project.id,
            master_item_id=server_master.id,
            item_code=f"{PREFIX}ITEM_SERVER",
            item_name="Server",
            quantity=4,
            delivery_options=[],
            status="PENDING",
            description=f"{PREFIX}Server for core rack expansion",
            is_finalized=True,
        )
        simple_item = ProjectItem(
            project_id=sec_project.id,
            master_item_id=simple_master.id,
            item_code=f"{PREFIX}ITEM_NVR",
            item_name="Network Video Recorder",
            quantity=2,
            delivery_options=[],
            status="PENDING",
            description=f"{PREFIX}Simple security item without decomposition",
            is_finalized=True,
        )
        db.add(server_item)
        db.add(simple_item)
        await db.flush()

        required_by_component: Dict[str, ProjectItemSubItem] = {}
        for sub in subitems:
            req = ProjectItemSubItem(
                project_item_id=server_item.id,
                item_subitem_id=sub.id,
                quantity=4,
            )
            db.add(req)
            required_by_component[sub.name] = req
        await db.flush()

        # Suppliers
        supplier_full = Supplier(
            supplier_id=f"{PREFIX}SUP_FULL",
            company_name=f"{PREFIX}FullStack Systems",
            payment_terms="cash",
            status="ACTIVE",
            risk_level="LOW",
            compliance_status="APPROVED",
        )
        supplier_partial_a = Supplier(
            supplier_id=f"{PREFIX}SUP_PART_A",
            company_name=f"{PREFIX}Core Components Ltd",
            payment_terms="installments_30_70",
            status="ACTIVE",
            risk_level="MEDIUM",
            compliance_status="APPROVED",
        )
        supplier_partial_b = Supplier(
            supplier_id=f"{PREFIX}SUP_PART_B",
            company_name=f"{PREFIX}Peripheral Integrators",
            payment_terms="net_45",
            status="ACTIVE",
            risk_level="MEDIUM",
            compliance_status="APPROVED",
        )
        db.add_all([supplier_full, supplier_partial_a, supplier_partial_b])
        await db.flush()

        # Packages for server item
        pkg_incomplete = ProcurementPackage(
            project_item_id=server_item.id,
            package_name=f"{PREFIX}PKG_SERVER_INCOMPLETE",
            package_type="PARTIAL",
            supplier_id=supplier_partial_a.id,
            main_item_quantity=2,
            is_active=True,
            created_by_id=user_id,
        )
        pkg_partial_a = ProcurementPackage(
            project_item_id=server_item.id,
            package_name=f"{PREFIX}PKG_SERVER_PART_A",
            package_type="PARTIAL",
            supplier_id=supplier_partial_a.id,
            main_item_quantity=2,
            is_active=True,
            created_by_id=user_id,
        )
        pkg_partial_b = ProcurementPackage(
            project_item_id=server_item.id,
            package_name=f"{PREFIX}PKG_SERVER_PART_B",
            package_type="PARTIAL",
            supplier_id=supplier_partial_b.id,
            main_item_quantity=2,
            is_active=True,
            created_by_id=user_id,
        )
        pkg_full = ProcurementPackage(
            project_item_id=server_item.id,
            package_name=f"{PREFIX}PKG_SERVER_FULL",
            package_type="FULL",
            supplier_id=supplier_full.id,
            main_item_quantity=4,
            is_active=True,
            created_by_id=user_id,
        )
        pkg_simple = ProcurementPackage(
            project_item_id=simple_item.id,
            package_name=f"{PREFIX}PKG_SIMPLE_FULL",
            package_type="FULL",
            supplier_id=supplier_full.id,
            main_item_quantity=2,
            is_active=True,
            created_by_id=user_id,
        )
        db.add_all([pkg_incomplete, pkg_partial_a, pkg_partial_b, pkg_full, pkg_simple])
        await db.flush()

        # Coverage mapping
        first_three = components[:3]
        first_half = components[:4]
        second_half = components[4:]

        for comp in first_three:
            req = required_by_component[comp]
            db.add(
                PackageSubItem(
                    package_id=pkg_incomplete.id,
                    project_item_subitem_id=req.id,
                    quantity_covered=2,
                    is_fully_covered=False,
                    coverage_percentage=_coverage_percentage(2, 4),
                )
            )

        for comp in first_half:
            req = required_by_component[comp]
            db.add(
                PackageSubItem(
                    package_id=pkg_partial_a.id,
                    project_item_subitem_id=req.id,
                    quantity_covered=4,
                    is_fully_covered=True,
                    coverage_percentage=Decimal("100"),
                )
            )

        for comp in second_half:
            req = required_by_component[comp]
            db.add(
                PackageSubItem(
                    package_id=pkg_partial_b.id,
                    project_item_subitem_id=req.id,
                    quantity_covered=4,
                    is_fully_covered=True,
                    coverage_percentage=Decimal("100"),
                )
            )

        for comp in components:
            req = required_by_component[comp]
            db.add(
                PackageSubItem(
                    package_id=pkg_full.id,
                    project_item_subitem_id=req.id,
                    quantity_covered=4,
                    is_fully_covered=True,
                    coverage_percentage=Decimal("100"),
                )
            )
        await db.flush()

        # Procurement options with varied payment terms
        opt_incomplete = ProcurementOption(
            package_id=pkg_incomplete.id,
            project_item_id=server_item.id,
            item_code=server_item.item_code,
            supplier_name=supplier_partial_a.company_name,
            supplier_id=supplier_partial_a.id,
            cost_amount=Decimal("18500"),
            cost_currency="USD",
            base_cost=Decimal("18500"),
            payment_terms={"type": "installments", "schedule": [{"percent": 30, "due_offset": 0}, {"percent": 70, "due_offset": 45}]},
            is_active=True,
            is_finalized=True,
        )
        opt_full = ProcurementOption(
            package_id=pkg_full.id,
            project_item_id=server_item.id,
            item_code=server_item.item_code,
            supplier_name=supplier_full.company_name,
            supplier_id=supplier_full.id,
            cost_amount=Decimal("36000"),
            cost_currency="USD",
            base_cost=Decimal("36000"),
            payment_terms={"type": "cash", "discount_percent": 3},
            is_active=True,
            is_finalized=True,
        )
        opt_simple = ProcurementOption(
            package_id=pkg_simple.id,
            project_item_id=simple_item.id,
            item_code=simple_item.item_code,
            supplier_name=supplier_full.company_name,
            supplier_id=supplier_full.id,
            cost_amount=Decimal("8400"),
            cost_currency="USD",
            base_cost=Decimal("8400"),
            payment_terms={"type": "net45"},
            is_active=True,
            is_finalized=True,
        )
        db.add_all([opt_incomplete, opt_full, opt_simple])
        await db.flush()

        today = date.today()

        # Decisions
        decision_fail = FinalizedDecision(
            project_id=dc_project.id,
            project_item_id=server_item.id,
            package_id=pkg_incomplete.id,
            item_code=server_item.item_code,
            procurement_option_id=opt_incomplete.id,
            purchase_date=today,
            delivery_date=today + timedelta(days=21),
            quantity=4,
            final_cost_amount=Decimal("18500"),
            final_cost_currency="USD",
            final_cost=Decimal("18500"),
            decision_maker_id=user_id,
            decision_date=datetime.utcnow(),
            status="PROPOSED",
            notes=f"{PREFIX}Expected to fail lock because coverage is incomplete",
        )
        decision_pass = FinalizedDecision(
            project_id=dc_project.id,
            project_item_id=server_item.id,
            package_id=pkg_full.id,
            item_code=server_item.item_code,
            procurement_option_id=opt_full.id,
            purchase_date=today,
            delivery_date=today + timedelta(days=20),
            quantity=4,
            final_cost_amount=Decimal("36000"),
            final_cost_currency="USD",
            final_cost=Decimal("36000"),
            decision_maker_id=user_id,
            decision_date=datetime.utcnow(),
            status="PROPOSED",
            notes=f"{PREFIX}Expected to pass lock because coverage is complete",
        )
        decision_finance = FinalizedDecision(
            project_id=sec_project.id,
            project_item_id=simple_item.id,
            package_id=pkg_simple.id,
            item_code=simple_item.item_code,
            procurement_option_id=opt_simple.id,
            purchase_date=today - timedelta(days=20),
            delivery_date=today - timedelta(days=10),
            quantity=2,
            final_cost_amount=Decimal("8400"),
            final_cost_currency="USD",
            final_cost=Decimal("8400"),
            decision_maker_id=user_id,
            decision_date=datetime.utcnow() - timedelta(days=25),
            status="LOCKED",
            delivery_status="DELIVERY_COMPLETE",
            actual_delivery_date=today - timedelta(days=9),
            is_correct_item_confirmed=True,
            procurement_confirmed_at=datetime.utcnow() - timedelta(days=9),
            procurement_confirmed_by_id=user_id,
            is_accepted_by_pm=True,
            pm_accepted_at=datetime.utcnow() - timedelta(days=8),
            pm_accepted_by_id=user_id,
            customer_delivery_date=today - timedelta(days=8),
            actual_invoice_issue_date=today - timedelta(days=7),
            actual_invoice_amount=Decimal("10200"),
            actual_invoice_amount_currency="USD",
            actual_invoice_received_date=today - timedelta(days=6),
            actual_payment_date=today - timedelta(days=4),
            actual_payment_amount=Decimal("10200"),
            actual_payment_amount_currency="USD",
            notes=f"{PREFIX}Execution/finance demo record",
        )
        db.add_all([decision_fail, decision_pass, decision_finance])
        await db.flush()

        # Invoice/Payment rows for execution visibility
        invoice = Invoice(
            decision_id=decision_finance.id,
            package_id=decision_finance.package_id,
            invoice_number=f"{PREFIX}INV_001",
            invoice_date=datetime.combine(today - timedelta(days=7), datetime.min.time()),
            invoice_amount=Decimal("10200"),
            currency="USD",
            due_date=datetime.combine(today + timedelta(days=10), datetime.min.time()),
            status=InvoiceStatus.SENT,
            payment_terms="net_30",
            notes=f"{PREFIX}Demo customer invoice",
        )
        db.add(invoice)
        await db.flush()

        payment_in = Payment(
            invoice_id=invoice.id,
            decision_id=decision_finance.id,
            package_id=decision_finance.package_id,
            payment_date=datetime.combine(today - timedelta(days=4), datetime.min.time()),
            payment_amount=Decimal("10200"),
            currency="USD",
            payment_method=PaymentMethod.BANK_TRANSFER,
            reference_number=f"{PREFIX}PAYIN_001",
            status=PaymentStatus.COMPLETED,
            notes=f"{PREFIX}Demo customer payment in",
        )
        db.add(payment_in)
        await db.flush()

        supplier_payment = SupplierPayment(
            decision_id=decision_finance.id,
            package_id=decision_finance.package_id,
            supplier_id=supplier_full.id,
            supplier_name=supplier_full.company_name,
            item_code=simple_item.item_code,
            project_id=sec_project.id,
            payment_date=today - timedelta(days=5),
            payment_amount=Decimal("8400"),
            currency="USD",
            payment_method="bank_transfer",
            reference_number=f"{PREFIX}PAYOUT_001",
            status="completed",
            notes=f"{PREFIX}Demo supplier payment out",
            created_by_id=user_id,
        )
        db.add(supplier_payment)

        # Cashflow visibility rows
        db.add(
            CashflowEvent(
                related_decision_id=decision_finance.id,
                event_type="INFLOW",
                forecast_type="ACTUAL",
                event_date=today - timedelta(days=4),
                amount_value=Decimal("10200"),
                amount_currency="USD",
                amount=Decimal("10200"),
                description=f"{PREFIX}Customer payment inflow",
            )
        )
        db.add(
            CashflowEvent(
                related_decision_id=decision_finance.id,
                event_type="OUTFLOW",
                forecast_type="ACTUAL",
                event_date=today - timedelta(days=5),
                amount_value=Decimal("8400"),
                amount_currency="USD",
                amount=Decimal("8400"),
                description=f"{PREFIX}Supplier payment outflow",
            )
        )

        # Basic audit traceability rows
        db.add(
            AuditLog(
                user_id=user_id,
                action=f"{PREFIX}DATASET_CREATED",
                entity_type="demo_dataset",
                entity_id=decision_finance.id,
                details={
                    "projects": [dc_project.project_code, sec_project.project_code],
                    "decisions": {
                        "fail": decision_fail.id,
                        "pass": decision_pass.id,
                        "finance": decision_finance.id,
                    },
                },
            )
        )
        await db.commit()

        # Validate lock behavior expectations
        fail_lock_error = ""
        pass_lock_ok = True
        try:
            await validate_package_coverage_for_lock(db, [decision_fail.id])
        except HTTPException as exc:  # expected
            fail_lock_error = str(exc.detail)
        except Exception as exc:
            fail_lock_error = str(exc)

        try:
            await validate_package_coverage_for_lock(db, [decision_pass.id])
        except Exception:
            pass_lock_ok = False

        summary = {
            "prefix": PREFIX,
            "projects": [dc_project.project_code, sec_project.project_code],
            "master_items": [server_master.item_code, simple_master.item_code],
            "suppliers": [
                supplier_full.supplier_id,
                supplier_partial_a.supplier_id,
                supplier_partial_b.supplier_id,
            ],
            "decisions": {
                "incomplete_lock_should_fail": decision_fail.id,
                "complete_lock_should_pass": decision_pass.id,
                "execution_finance_locked": decision_finance.id,
            },
            "finance_records": {
                "invoice_id": invoice.id,
                "payment_in_id": payment_in.id,
                "supplier_payment_id": supplier_payment.id,
            },
            "validation": {
                "fail_lock_error_contains_incomplete": "incomplete" in fail_lock_error.lower(),
                "pass_lock_ok": pass_lock_ok,
            },
            "cleanup_hint": "python scripts/create_demo_dataset.py --mode cleanup",
            "cleanup_removed_before_create": cleanup_summary,
        }
        return summary


async def main(mode: str) -> None:
    if mode in {"create", "recreate"}:
        result = await create_demo_dataset()
    elif mode == "cleanup":
        result = {"cleanup_removed": await cleanup_demo_dataset()}
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create/Cleanup DEMO_RC8 release candidate dataset.")
    parser.add_argument(
        "--mode",
        choices=["create", "recreate", "cleanup"],
        default="create",
        help="create/recreate demo dataset or cleanup tagged demo rows",
    )
    args = parser.parse_args()
    asyncio.run(main(args.mode))
