from datetime import date
from decimal import Decimal

import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    BudgetData,
    ExchangeRate,
    ItemMaster,
    ItemSubItem,
    PackageSubItem,
    ProcurementOption,
    ProcurementPackage,
    Project,
    ProjectItem,
    ProjectItemSubItem,
)
from app.services.optimization_budget_service import (
    analyze_proposal_decisions_financial,
    build_optimization_budget_analysis,
    get_currency_symbol,
    select_decisions_within_budget,
)


async def _create_project_with_item(
    db: AsyncSession,
    *,
    project_code: str,
    item_code: str,
    quantity: int = 1,
) -> tuple[Project, ProjectItem]:
    project = Project(project_code=project_code, name=project_code, is_active=True)
    db.add(project)
    await db.flush()
    item = ProjectItem(
        project_id=project.id,
        item_code=item_code,
        item_name=item_code,
        quantity=quantity,
        delivery_options=[],
        status="PENDING",
        is_finalized=True,
    )
    db.add(item)
    await db.flush()
    return project, item


async def _add_option(
    db: AsyncSession,
    *,
    item: ProjectItem,
    option_id_seed: int,
    cost: Decimal,
    currency: str = "IRR",
) -> ProcurementOption:
    option = ProcurementOption(
        item_code=item.item_code,
        project_item_id=item.id,
        supplier_name=f"SUP-{option_id_seed}",
        cost_amount=cost,
        cost_currency=currency,
        shipping_cost=Decimal("0"),
        lomc_lead_time=0,
        payment_terms={"type": "cash"},
        is_active=True,
        is_finalized=True,
        purchase_date=date(2026, 6, 1),
        expected_delivery_date=date(2026, 6, 15),
    )
    db.add(option)
    await db.flush()
    return option


async def _add_budget(db: AsyncSession, amount: Decimal) -> None:
    budget = BudgetData(
        budget_date=date(2026, 6, 1),
        available_budget=amount,
        multi_currency_budget={"IRR": float(amount)},
    )
    db.add(budget)
    await db.flush()


@pytest.mark.asyncio
async def test_phase12e0_test_a_multiple_candidates_not_summed(db_session: AsyncSession):
    _, item = await _create_project_with_item(
        db_session, project_code="P12E0-A", item_code="ITEM-A", quantity=1
    )
    await _add_option(db_session, item=item, option_id_seed=1, cost=Decimal("100000000"))
    await _add_option(db_session, item=item, option_id_seed=2, cost=Decimal("120000000"))
    await _add_option(db_session, item=item, option_id_seed=3, cost=Decimal("140000000"))
    await _add_budget(db_session, Decimal("1000000000"))
    await db_session.commit()

    minimum = await build_optimization_budget_analysis(db_session, scenario="minimum_feasible")
    average = await build_optimization_budget_analysis(db_session, scenario="average_candidate")
    conservative = await build_optimization_budget_analysis(db_session, scenario="conservative")

    assert minimum.budget_required_irr == Decimal("100000000")
    assert average.budget_required_irr == Decimal("120000000")
    assert conservative.budget_required_irr == Decimal("140000000")
    assert minimum.budget_required_irr != Decimal("360000000")
    assert average.budget_required_irr != Decimal("360000000")
    assert conservative.budget_required_irr != Decimal("360000000")


@pytest.mark.asyncio
async def test_phase12e0_test_b_package_combinations_not_summed(db_session: AsyncSession):
    _, item = await _create_project_with_item(
        db_session, project_code="P12E0-B", item_code="ITEM-B", quantity=2
    )
    master = ItemMaster(
        item_code="MASTER-B",
        company="TEST",
        item_name="MASTER-B",
        unit="pcs",
        is_active=True,
    )
    db_session.add(master)
    await db_session.flush()

    sub1 = ItemSubItem(item_master_id=master.id, name="S1")
    sub2 = ItemSubItem(item_master_id=master.id, name="S2")
    db_session.add_all([sub1, sub2])
    await db_session.flush()

    rel1 = ProjectItemSubItem(project_item_id=item.id, item_subitem_id=sub1.id, quantity=1)
    rel2 = ProjectItemSubItem(project_item_id=item.id, item_subitem_id=sub2.id, quantity=1)
    db_session.add_all([rel1, rel2])
    await db_session.flush()

    pkg_a = ProcurementPackage(
        project_item_id=item.id,
        package_name="A",
        package_type="PARTIAL",
        is_active=True,
        main_item_quantity=1,
    )
    pkg_b = ProcurementPackage(
        project_item_id=item.id,
        package_name="B",
        package_type="PARTIAL",
        is_active=True,
        main_item_quantity=1,
    )
    pkg_c = ProcurementPackage(
        project_item_id=item.id,
        package_name="C",
        package_type="PARTIAL",
        is_active=True,
        main_item_quantity=1,
    )
    pkg_d = ProcurementPackage(
        project_item_id=item.id,
        package_name="D",
        package_type="PARTIAL",
        is_active=True,
        main_item_quantity=1,
    )
    db_session.add_all([pkg_a, pkg_b, pkg_c, pkg_d])
    await db_session.flush()

    db_session.add_all(
        [
            PackageSubItem(package_id=pkg_a.id, project_item_subitem_id=rel1.id, quantity_covered=1),
            PackageSubItem(package_id=pkg_b.id, project_item_subitem_id=rel2.id, quantity_covered=1),
            PackageSubItem(package_id=pkg_c.id, project_item_subitem_id=rel1.id, quantity_covered=1),
            PackageSubItem(package_id=pkg_d.id, project_item_subitem_id=rel2.id, quantity_covered=1),
        ]
    )
    await db_session.flush()

    for pkg, cost in [
        (pkg_a, Decimal("100000000")),
        (pkg_b, Decimal("100000000")),
        (pkg_c, Decimal("120000000")),
        (pkg_d, Decimal("130000000")),
    ]:
        db_session.add(
            ProcurementOption(
                item_code=item.item_code,
                project_item_id=item.id,
                package_id=pkg.id,
                supplier_name=f"SUP-{pkg.package_name}",
                cost_amount=cost,
                cost_currency="IRR",
                shipping_cost=Decimal("0"),
                lomc_lead_time=0,
                payment_terms={"type": "cash"},
                is_active=True,
                is_finalized=True,
                purchase_date=date(2026, 6, 1),
                expected_delivery_date=date(2026, 6, 15),
            )
        )
    await _add_budget(db_session, Decimal("1000000000"))
    await db_session.commit()

    minimum = await build_optimization_budget_analysis(db_session, scenario="minimum_feasible")
    conservative = await build_optimization_budget_analysis(db_session, scenario="conservative")

    assert minimum.budget_required_irr == Decimal("200000000")
    assert conservative.budget_required_irr == Decimal("250000000")
    assert minimum.budget_required_irr != Decimal("450000000")
    assert conservative.budget_required_irr != Decimal("450000000")


@pytest.mark.asyncio
async def test_phase12e0_test_c_multiple_items_count_once(db_session: AsyncSession):
    _, item1 = await _create_project_with_item(
        db_session, project_code="P12E0-C", item_code="ITEM-C1", quantity=1
    )
    _, item2 = await _create_project_with_item(
        db_session, project_code="P12E0-C2", item_code="ITEM-C2", quantity=1
    )
    await _add_option(db_session, item=item1, option_id_seed=1, cost=Decimal("100"))
    await _add_option(db_session, item=item1, option_id_seed=2, cost=Decimal("120"))
    await _add_option(db_session, item=item1, option_id_seed=3, cost=Decimal("140"))
    await _add_option(db_session, item=item2, option_id_seed=4, cost=Decimal("50"))
    await _add_option(db_session, item=item2, option_id_seed=5, cost=Decimal("70"))
    await _add_budget(db_session, Decimal("1000"))
    await db_session.commit()

    result = await build_optimization_budget_analysis(db_session, scenario="minimum_feasible")
    assert result.items_analyzed == 2
    assert result.budget_required_irr == Decimal("150")


@pytest.mark.asyncio
async def test_phase12e0_test_d_missing_candidate_warning(db_session: AsyncSession):
    _, item = await _create_project_with_item(
        db_session, project_code="P12E0-D", item_code="ITEM-D", quantity=1
    )
    await _add_option(
        db_session,
        item=item,
        option_id_seed=1,
        cost=Decimal("100"),
        currency="USD",
    )
    await _add_budget(db_session, Decimal("1000"))
    await db_session.commit()

    result = await build_optimization_budget_analysis(db_session, scenario="minimum_feasible")
    assert result.items_with_no_valid_candidate == 1
    assert result.budget_required_irr == Decimal("0")
    assert any("Missing exchange rate" in warning or "no eligible candidate" in warning for warning in result.warnings)


@pytest.mark.asyncio
async def test_phase12e0_test_e_currency_conversion(db_session: AsyncSession):
    _, item = await _create_project_with_item(
        db_session, project_code="P12E0-E", item_code="ITEM-E", quantity=1
    )
    await _add_option(
        db_session,
        item=item,
        option_id_seed=1,
        cost=Decimal("100"),
        currency="USD",
    )
    db_session.add(
        ExchangeRate(
            date=date(2026, 6, 1),
            from_currency="USD",
            to_currency="IRR",
            rate=Decimal("500000"),
            is_active=True,
        )
    )
    await _add_budget(db_session, Decimal("1000000000"))
    await db_session.commit()

    result = await build_optimization_budget_analysis(db_session, scenario="minimum_feasible")
    assert result.budget_required_irr == Decimal("50000000")
    assert result.budget_required_by_currency["USD"] == Decimal("100")


@pytest.mark.asyncio
async def test_phase12e0_test_f_missing_exchange_rate_warning(db_session: AsyncSession):
    _, item = await _create_project_with_item(
        db_session, project_code="P12E0-F", item_code="ITEM-F", quantity=1
    )
    await _add_option(
        db_session,
        item=item,
        option_id_seed=1,
        cost=Decimal("10"),
        currency="EUR",
    )
    await _add_budget(db_session, Decimal("1000000000"))
    await db_session.commit()

    result = await build_optimization_budget_analysis(db_session, scenario="minimum_feasible")
    assert result.items_with_no_valid_candidate == 1
    assert any("Missing exchange rate" in warning for warning in result.warnings)


@pytest.mark.asyncio
async def test_phase12e0_test_g_shortage_non_blocking(db_session: AsyncSession):
    _, item = await _create_project_with_item(
        db_session, project_code="P12E0-G", item_code="ITEM-G", quantity=1
    )
    await _add_option(db_session, item=item, option_id_seed=1, cost=Decimal("1000"))
    await _add_budget(db_session, Decimal("100"))
    await db_session.commit()

    result = await build_optimization_budget_analysis(db_session, scenario="minimum_feasible")
    assert result.budget_status in {"WARNING", "CRITICAL"}
    assert result.is_blocking is False
    assert result.can_continue_with_warning is True
    assert "optimize_within_available_budget" in result.allowed_actions
    assert "optimize_all_with_shortage_analysis" in result.allowed_actions
    assert "cancel_and_update_budget" in result.allowed_actions


@pytest.mark.asyncio
async def test_phase12e0_test_h_constrained_mode_selection(db_session: AsyncSession):
    _, item1 = await _create_project_with_item(
        db_session, project_code="P12E0-H", item_code="ITEM-H1", quantity=1
    )
    _, item2 = await _create_project_with_item(
        db_session, project_code="P12E0-H2", item_code="ITEM-H2", quantity=1
    )
    option1 = await _add_option(db_session, item=item1, option_id_seed=1, cost=Decimal("70"))
    option2 = await _add_option(db_session, item=item2, option_id_seed=2, cost=Decimal("60"))
    await _add_budget(db_session, Decimal("100"))
    await db_session.commit()

    decisions = [
        {
            "project_id": item1.project_id,
            "project_item_id": item1.id,
            "item_code": item1.item_code,
            "procurement_option_id": option1.id,
            "purchase_date": "2026-06-01",
            "quantity": 1,
        },
        {
            "project_id": item2.project_id,
            "project_item_id": item2.id,
            "item_code": item2.item_code,
            "procurement_option_id": option2.id,
            "purchase_date": "2026-06-01",
            "quantity": 1,
        },
    ]
    kept, deferred = await select_decisions_within_budget(
        db_session, decisions=decisions, available_budget_irr=Decimal("100")
    )
    analysis = await analyze_proposal_decisions_financial(
        db_session, decisions=kept, budget_mode="constrained"
    )

    assert len(kept) == 1
    assert len(deferred) == 1
    assert deferred[0]["defer_reason"] == "insufficient_budget"
    assert analysis.budget_required_irr <= analysis.budget_available_irr


@pytest.mark.asyncio
async def test_phase12e0_test_i_allow_shortage_mode_financial_analysis(db_session: AsyncSession):
    _, item1 = await _create_project_with_item(
        db_session, project_code="P12E0-I", item_code="ITEM-I1", quantity=1
    )
    _, item2 = await _create_project_with_item(
        db_session, project_code="P12E0-I2", item_code="ITEM-I2", quantity=1
    )
    option1 = await _add_option(db_session, item=item1, option_id_seed=1, cost=Decimal("70"))
    option2 = await _add_option(db_session, item=item2, option_id_seed=2, cost=Decimal("60"))
    await _add_budget(db_session, Decimal("100"))
    await db_session.commit()

    decisions = [
        {
            "project_id": item1.project_id,
            "project_item_id": item1.id,
            "item_code": item1.item_code,
            "procurement_option_id": option1.id,
            "purchase_date": "2026-06-01",
            "quantity": 1,
        },
        {
            "project_id": item2.project_id,
            "project_item_id": item2.id,
            "item_code": item2.item_code,
            "procurement_option_id": option2.id,
            "purchase_date": "2026-06-01",
            "quantity": 1,
        },
    ]
    analysis = await analyze_proposal_decisions_financial(
        db_session, decisions=decisions, budget_mode="allow_shortage"
    )
    assert analysis.candidate_count == 2
    assert analysis.budget_required_irr == Decimal("130")
    assert analysis.budget_status in {"WARNING", "CRITICAL"}
    assert analysis.can_continue_with_warning is True
    assert len(analysis.periods) >= 1


def test_phase12e0_test_j_currency_symbol_mapping():
    assert get_currency_symbol("IRR") == "ریال"
    assert get_currency_symbol("USD") == "$"
    assert get_currency_symbol("EUR") == "€"
    assert get_currency_symbol("AED") == "د.إ"
    assert get_currency_symbol("CNY") == "¥"
    assert get_currency_symbol("TRY") == "₺"

