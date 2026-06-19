"""
Phase 5 increment tests for package-aware optimization and decision boundary rules.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from app.config import settings
from app.models import (
    BudgetData,
    ProcurementOption,
    ProcurementPackage,
    FinalizedDecision,
)
from app.optimization_engine import ProcurementOptimizer
from app.routers.decisions import _decision_boundary_conditions


class TestPhase5DecisionBoundary:
    def test_decision_boundary_prefers_package_when_enabled(self):
        prev = settings.enable_package_based_optimization
        settings.enable_package_based_optimization = True
        try:
            conditions = _decision_boundary_conditions(
                package_id=99,
                project_item_id=10,
                item_code="ITEM-001",
            )
            assert len(conditions) == 1
            assert conditions[0].left.key == "package_id"
        finally:
            settings.enable_package_based_optimization = prev

    def test_decision_boundary_falls_back_to_legacy_when_disabled(self):
        prev = settings.enable_package_based_optimization
        settings.enable_package_based_optimization = False
        try:
            conditions = _decision_boundary_conditions(
                package_id=99,
                project_item_id=10,
                item_code="ITEM-001",
            )
            keys = {condition.left.key for condition in conditions}
            assert keys == {"project_item_id", "item_code"}
        finally:
            settings.enable_package_based_optimization = prev


@pytest.mark.asyncio
async def test_optimizer_filters_only_decided_packages_in_package_mode(
    db_session,
    test_user,
    test_project_item,
):
    """
    In package boundary mode, a decided package should block only its own options,
    not all options under the same project item.
    """
    prev_package_mode = settings.enable_package_based_optimization
    prev_package_procurement = settings.enable_package_procurement
    settings.enable_package_based_optimization = True
    settings.enable_package_procurement = True

    try:
        package_a = ProcurementPackage(
            project_item_id=test_project_item.id,
            package_name="PKG-A",
            package_type="PARTIAL",
            is_active=True,
        )
        package_b = ProcurementPackage(
            project_item_id=test_project_item.id,
            package_name="PKG-B",
            package_type="PARTIAL",
            is_active=True,
        )
        db_session.add(package_a)
        db_session.add(package_b)
        await db_session.commit()
        await db_session.refresh(package_a)
        await db_session.refresh(package_b)

        option_a = ProcurementOption(
            package_id=package_a.id,
            project_item_id=test_project_item.id,
            item_code=test_project_item.item_code,
            supplier_name="Supplier A",
            cost_amount=Decimal("1000"),
            cost_currency="IRR",
            base_cost=Decimal("1000"),
            payment_terms={"type": "cash"},
            is_active=True,
            is_finalized=True,
        )
        option_b = ProcurementOption(
            package_id=package_b.id,
            project_item_id=test_project_item.id,
            item_code=test_project_item.item_code,
            supplier_name="Supplier B",
            cost_amount=Decimal("1100"),
            cost_currency="IRR",
            base_cost=Decimal("1100"),
            payment_terms={"type": "cash"},
            is_active=True,
            is_finalized=True,
        )
        db_session.add(option_a)
        db_session.add(option_b)
        await db_session.commit()
        await db_session.refresh(option_a)
        await db_session.refresh(option_b)

        decided = FinalizedDecision(
            project_id=test_project_item.project_id,
            project_item_id=test_project_item.id,
            package_id=package_a.id,
            item_code=test_project_item.item_code,
            procurement_option_id=option_a.id,
            purchase_date=date.today(),
            delivery_date=date.today(),
            quantity=1,
            final_cost_amount=Decimal("1000"),
            final_cost_currency="IRR",
            final_cost=Decimal("1000"),
            status="LOCKED",
            decision_maker_id=test_user.id,
            decision_date=datetime.utcnow(),
        )
        db_session.add(decided)
        await db_session.commit()

        # Optimizer requires at least one budget row.
        db_session.add(
            BudgetData(
                budget_date=date.today(),
                available_budget=Decimal("100000000"),
                multi_currency_budget={"IRR": 100000000},
            )
        )
        await db_session.commit()

        optimizer = ProcurementOptimizer(db_session)
        await optimizer._load_data()

        assert option_a.id not in optimizer.procurement_options
        assert option_b.id in optimizer.procurement_options
    finally:
        settings.enable_package_based_optimization = prev_package_mode
        settings.enable_package_procurement = prev_package_procurement
