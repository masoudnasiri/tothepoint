"""
Create deterministic fixture data for Sprint 3A-4A runtime verification.

Fixture tag:
  RIVAR_DEMO_ACCEPTED_BASELINE

Usage:
  python scripts/create_sprint4a_demo_fixture.py --mode recreate
  python scripts/create_sprint4a_demo_fixture.py --mode create
  python scripts/create_sprint4a_demo_fixture.py --mode cleanup
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date
from decimal import Decimal
from typing import Dict, List

from sqlalchemy import delete, select

from app.auth import get_password_hash
from app.database import AsyncSessionLocal
import app.models_invoice_payment  # noqa: F401  ensure relationship registry is populated
from app.models import (
    Currency,
    DeliveryOption,
    ItemMaster,
    ItemSubItem,
    PackageSubItem,
    PaymentMethod,
    ProcurementCostComponent,
    ProcurementOption,
    ProcurementPackage,
    Project,
    ProjectItem,
    ProjectItemStatus,
    ProjectItemSubItem,
    Supplier,
    User,
)
from app.services.procurement_financials_service import (
    apply_procurement_option_persistence_contract,
    get_procurement_option_readiness,
    synchronize_procurement_option_legacy_pricing_fields,
)


PREFIX = "RIVAR_DEMO_ACCEPTED_BASELINE"
PROJECT_CODE = f"{PREFIX}_PRJ"
PROJECT_NAME = f"{PREFIX} Project"
ITEM_CODE = f"{PREFIX}_ITEM"
SUPPLIER_CODE = f"{PREFIX}_SUPPLIER"
PAYMENT_METHOD_CODE = f"{PREFIX}_NET5"
PROC_USER = f"{PREFIX.lower()}_proc"
FIN_USER = f"{PREFIX.lower()}_fin"


async def _cleanup_fixture(db) -> Dict[str, int]:
    deleted: Dict[str, int] = {}

    supplier_ids = (
        await db.execute(
            select(Supplier.id).where(Supplier.supplier_id.like(f"{PREFIX}%"))
        )
    ).scalars().all()
    payment_method_ids = (
        await db.execute(
            select(PaymentMethod.id).where(PaymentMethod.code.like(f"{PREFIX}%"))
        )
    ).scalars().all()
    project_ids = (
        await db.execute(
            select(Project.id).where(Project.project_code.like(f"{PREFIX}%"))
        )
    ).scalars().all()
    project_item_ids = (
        await db.execute(
            select(ProjectItem.id).where(
                ProjectItem.project_id.in_(project_ids) if project_ids else False
            )
        )
    ).scalars().all()
    package_ids = (
        await db.execute(
            select(ProcurementPackage.id).where(
                ProcurementPackage.project_item_id.in_(project_item_ids)
                if project_item_ids
                else False
            )
        )
    ).scalars().all()
    option_ids = (
        await db.execute(
            select(ProcurementOption.id).where(
                (
                    ProcurementOption.item_code.like(f"{PREFIX}%")
                    | (
                        ProcurementOption.project_item_id.in_(project_item_ids)
                        if project_item_ids
                        else False
                    )
                    | (
                        ProcurementOption.package_id.in_(package_ids)
                        if package_ids
                        else False
                    )
                    | (
                        ProcurementOption.supplier_id.in_(supplier_ids)
                        if supplier_ids
                        else False
                    )
                    | (
                        ProcurementOption.payment_method_id.in_(payment_method_ids)
                        if payment_method_ids
                        else False
                    )
                )
            )
        )
    ).scalars().all()

    delete_plan = [
        (
            "package_subitems",
            delete(PackageSubItem).where(
                PackageSubItem.package_id.in_(package_ids) if package_ids else False
            ),
        ),
        (
            "procurement_options",
            delete(ProcurementOption).where(
                ProcurementOption.id.in_(option_ids) if option_ids else False
            ),
        ),
        (
            "delivery_options",
            delete(DeliveryOption).where(
                (
                    DeliveryOption.project_item_id.in_(project_item_ids)
                    if project_item_ids
                    else False
                )
                | (DeliveryOption.package_id.in_(package_ids) if package_ids else False)
            ),
        ),
        (
            "procurement_packages",
            delete(ProcurementPackage).where(
                ProcurementPackage.id.in_(package_ids) if package_ids else False
            ),
        ),
        (
            "project_item_subitems",
            delete(ProjectItemSubItem).where(
                ProjectItemSubItem.project_item_id.in_(project_item_ids)
                if project_item_ids
                else False
            ),
        ),
        (
            "project_items",
            delete(ProjectItem).where(
                ProjectItem.id.in_(project_item_ids) if project_item_ids else False
            ),
        ),
        (
            "projects",
            delete(Project).where(Project.id.in_(project_ids) if project_ids else False),
        ),
        (
            "item_subitems",
            delete(ItemSubItem).where(ItemSubItem.part_number.like(f"{PREFIX}%")),
        ),
        (
            "items_master",
            delete(ItemMaster).where(ItemMaster.item_code.like(f"{PREFIX}%")),
        ),
        (
            "suppliers",
            delete(Supplier).where(Supplier.supplier_id.like(f"{PREFIX}%")),
        ),
        (
            "payment_methods",
            delete(PaymentMethod).where(PaymentMethod.code.like(f"{PREFIX}%")),
        ),
        (
            "users",
            delete(User).where(User.username.in_([PROC_USER, FIN_USER])),
        ),
    ]

    for key, stmt in delete_plan:
        result = await db.execute(stmt)
        deleted[key] = int(result.rowcount or 0)

    await db.commit()
    return deleted


async def _get_or_create_user(db, username: str, role: str) -> User:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user:
        user.role = role
        user.is_active = True
        return user
    user = User(
        username=username,
        password_hash=get_password_hash("fixture-only-password"),
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def _ensure_currency_irr(db) -> Currency:
    result = await db.execute(select(Currency).where(Currency.code == "IRR"))
    currency = result.scalar_one_or_none()
    if currency:
        return currency
    currency = Currency(
        code="IRR",
        name="Iranian Rial",
        symbol="IRR",
        is_base_currency=True,
        is_active=True,
        decimal_places=0,
    )
    db.add(currency)
    await db.flush()
    return currency


async def create_fixture() -> Dict[str, object]:
    async with AsyncSessionLocal() as db:
        finance_user = await _get_or_create_user(db, FIN_USER, "finance")
        procurement_user = await _get_or_create_user(db, PROC_USER, "procurement")
        currency = await _ensure_currency_irr(db)

        supplier = Supplier(
            supplier_id=SUPPLIER_CODE,
            company_name=f"{PREFIX} Supplier",
            status="ACTIVE",
            compliance_status="APPROVED",
            risk_level="LOW",
        )
        db.add(supplier)

        item_master = ItemMaster(
            item_code=f"{PREFIX}_MASTER",
            company="Rivar",
            item_name=f"{PREFIX} Master Item",
            model="S4A",
            category="Fixture",
            unit="unit",
            description="Deterministic Sprint 4A fixture master item",
            is_active=True,
            created_by_id=procurement_user.id,
        )
        db.add(item_master)
        await db.flush()

        item_subitem = ItemSubItem(
            item_master_id=item_master.id,
            name="Core Component",
            description="Fixture component",
            part_number=f"{PREFIX}_COMPONENT",
        )
        db.add(item_subitem)
        await db.flush()

        project = Project(
            project_code=PROJECT_CODE,
            name=PROJECT_NAME,
            priority_weight=9,
            is_active=True,
        )
        db.add(project)
        await db.flush()

        project_item = ProjectItem(
            project_id=project.id,
            master_item_id=item_master.id,
            item_code=ITEM_CODE,
            item_name=f"{PREFIX} Item",
            quantity=2,
            delivery_options=[date(2026, 7, 20).isoformat()],
            status=ProjectItemStatus.DECIDED,
            is_finalized=True,
            description="Deterministic Sprint 4A fixture project item",
        )
        db.add(project_item)
        await db.flush()

        project_item_subitem = ProjectItemSubItem(
            project_item_id=project_item.id,
            item_subitem_id=item_subitem.id,
            quantity=2,
        )
        db.add(project_item_subitem)
        await db.flush()

        ready_package = ProcurementPackage(
            project_item_id=project_item.id,
            package_name=f"{PREFIX}_PKG_READY",
            package_type="FULL",
            supplier_id=supplier.id,
            is_active=True,
            main_item_quantity=2,
            created_by_id=procurement_user.id,
        )
        not_ready_package = ProcurementPackage(
            project_item_id=project_item.id,
            package_name=f"{PREFIX}_PKG_NOT_READY",
            package_type="PARTIAL",
            supplier_id=supplier.id,
            is_active=True,
            main_item_quantity=1,
            created_by_id=procurement_user.id,
        )
        db.add_all([ready_package, not_ready_package])
        await db.flush()

        db.add(
            PackageSubItem(
                package_id=ready_package.id,
                project_item_subitem_id=project_item_subitem.id,
                quantity_covered=2,
                is_fully_covered=True,
                coverage_percentage=Decimal("100"),
            )
        )
        db.add(
            PackageSubItem(
                package_id=not_ready_package.id,
                project_item_subitem_id=project_item_subitem.id,
                quantity_covered=1,
                is_fully_covered=False,
                coverage_percentage=Decimal("50"),
            )
        )
        await db.flush()

        delivery_option = DeliveryOption(
            package_id=ready_package.id,
            project_item_id=project_item.id,
            delivery_date=date(2026, 7, 20),
            invoice_timing_type="RELATIVE",
            invoice_days_after_delivery=0,
            invoice_amount_per_unit=Decimal("120"),
            is_active=True,
            notes=f"{PREFIX} delivery option",
        )
        db.add(delivery_option)
        await db.flush()
        await db.commit()

        payment_method = PaymentMethod(
            code=PAYMENT_METHOD_CODE,
            name_en=f"{PREFIX} Net 5",
            name_fa=f"{PREFIX} Net 5",
            settlement_delay_days=5,
            is_active=True,
        )
        db.add(payment_method)
        await db.flush()

        ready_option = ProcurementOption(
            package_id=ready_package.id,
            project_item_id=project_item.id,
            item_code=project_item.item_code,
            supplier_name=supplier.company_name,
            supplier_id=supplier.id,
            cost_amount=Decimal("100"),
            cost_currency="IRR",
            shipping_cost=Decimal("20"),
            base_cost=Decimal("100"),
            currency_id=currency.id,
            payment_terms={"type": "cash", "discount_percent": 0},
            payment_method_id=payment_method.id,
            planned_supplier_payment_date=date(2026, 7, 1),
            project_requested_delivery_date=date(2026, 7, 20),
            supplier_actual_delivery_date=date(2026, 7, 20),
            delivery_option_id=delivery_option.id,
            is_active=True,
            is_finalized=True,
        )
        db.add(ready_option)
        await db.flush()

        db.add(
            ProcurementCostComponent(
                procurement_option_id=ready_option.id,
                component_type="BASE_PRICE",
                amount_value=Decimal("100"),
                amount_currency="IRR",
                payment_metadata={
                    "inherit_option_payment_schedule": True,
                    "payee_type": "SUPPLIER",
                },
                is_active=True,
            )
        )
        db.add(
            ProcurementCostComponent(
                procurement_option_id=ready_option.id,
                component_type="SHIPPING",
                amount_value=Decimal("20"),
                amount_currency="IRR",
                payment_metadata={
                    "inherit_option_payment_schedule": False,
                    "payee_type": "LOGISTICS_PROVIDER",
                    "payee_label": f"{PREFIX} Logistics",
                    "payment_method_id": payment_method.id,
                    "payment_type": "INSTALLMENTS",
                    "planned_payment_date": date(2026, 7, 2).isoformat(),
                    "payment_schedule": [
                        {"due_offset_days": 0, "percent": 50},
                        {"due_offset_days": 10, "percent": 50},
                    ],
                },
                is_active=True,
            )
        )
        await db.flush()
        await synchronize_procurement_option_legacy_pricing_fields(
            option_id=ready_option.id,
            db=db,
            require_base_price=False,
        )
        await apply_procurement_option_persistence_contract(option_id=ready_option.id, db=db)

        not_ready_option = ProcurementOption(
            package_id=not_ready_package.id,
            project_item_id=project_item.id,
            item_code=project_item.item_code,
            supplier_name=supplier.company_name,
            supplier_id=supplier.id,
            cost_amount=Decimal("95"),
            cost_currency="IRR",
            shipping_cost=Decimal("5"),
            base_cost=Decimal("95"),
            currency_id=currency.id,
            payment_terms={"type": "cash", "discount_percent": 0},
            is_active=True,
            is_finalized=True,
        )
        db.add(not_ready_option)
        await db.commit()

        ready_readiness = await get_procurement_option_readiness(
            option_id=ready_option.id, db=db
        )
        not_ready_readiness = await get_procurement_option_readiness(
            option_id=not_ready_option.id, db=db
        )

        candidate_id = (
            f"candidate:{project.id}:{project_item.id}:{ready_package.id}:{ready_option.id}"
        )
        return {
            "fixture_tag": PREFIX,
            "project_id": project.id,
            "project_item_id": project_item.id,
            "package_id": ready_package.id,
            "option_id_ready": ready_option.id,
            "option_id_not_ready": not_ready_option.id,
            "candidate_id": candidate_id,
            "readiness_ready": bool(
                ready_readiness.get("is_ready_for_candidate_builder")
            ),
            "readiness_not_ready": bool(
                not_ready_readiness.get("is_ready_for_candidate_builder")
            ),
        }


async def main(mode: str) -> Dict[str, object]:
    if mode == "cleanup":
        async with AsyncSessionLocal() as db:
            return {"mode": mode, "cleanup": await _cleanup_fixture(db)}

    if mode == "create":
        return {"mode": mode, "result": await create_fixture()}

    if mode == "recreate":
        async with AsyncSessionLocal() as db:
            cleanup = await _cleanup_fixture(db)
        created = await create_fixture()
        return {"mode": mode, "cleanup": cleanup, "result": created}

    raise ValueError(f"Unsupported mode: {mode}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create deterministic Sprint 4A demo fixture"
    )
    parser.add_argument(
        "--mode", choices=["create", "recreate", "cleanup"], default="recreate"
    )
    args = parser.parse_args()
    output = asyncio.run(main(args.mode))
    print(json.dumps(output, indent=2, default=str))
