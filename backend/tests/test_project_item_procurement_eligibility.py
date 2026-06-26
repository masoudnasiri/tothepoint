"""
Sprint 3A-0: procurement eligibility gate tests for project-item finalization.
"""

from datetime import date
from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.auth import get_current_user
from app.database import get_db
from app.models import DeliveryOption, OptimizationSubmission, ProcurementPackage, ProjectItem, User
from app.routers import items as items_router_module
from app.routers.items import finalize_all_project_items, finalize_project_item_by_id
from app.schemas import ProjectItemFinalize
from app.services.procurement_eligibility_service import (
    validate_project_item_procurement_eligibility,
)


async def _create_pmo_user(db_session, username: str) -> User:
    user = User(username=username, password_hash="hash", role="pmo", is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _create_delivery_option(
    db_session,
    *,
    project_item_id: int,
    amount: Decimal,
    delivery_date: date = date(2026, 1, 10),
):
    option = DeliveryOption(
        project_item_id=project_item_id,
        delivery_date=delivery_date,
        invoice_amount_per_unit=amount,
        invoice_timing_type="RELATIVE",
        invoice_days_after_delivery=30,
        is_active=True,
    )
    db_session.add(option)
    await db_session.commit()
    await db_session.refresh(option)
    return option


def _extract_blocker_codes(exc: HTTPException) -> list[str]:
    detail = exc.detail if isinstance(exc.detail, dict) else {}
    eligibility = detail.get("eligibility", {})
    return [row.get("code") for row in eligibility.get("blockers", [])]


async def _request_items_api(
    db_session,
    current_user: User,
    method: str,
    path: str,
    *,
    json: dict | None = None,
):
    app = FastAPI()
    app.include_router(items_router_module.router)

    async def _override_get_db():
        yield db_session

    async def _override_get_current_user():
        return current_user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, path, json=json)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_sprint3a_no_delivery_option_cannot_be_finalized(db_session, test_project_item):
    pmo_user = await _create_pmo_user(db_session, "s3a_pmo_no_delivery")
    test_project_item.delivery_options = []
    await db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await finalize_project_item_by_id(
            item_id=test_project_item.id,
            finalize_data=ProjectItemFinalize(is_finalized=True),
            current_user=pmo_user,
            db=db_session,
        )

    assert exc.value.status_code == 422
    assert "NO_DELIVERY_OPTION" in _extract_blocker_codes(exc.value)


@pytest.mark.asyncio
async def test_sprint3a_invalid_delivery_schedule_reports_missing_date(db_session, test_project_item):
    test_project_item.delivery_options = ["not-a-date"]
    await db_session.commit()

    eligibility = await validate_project_item_procurement_eligibility(
        db_session, test_project_item.id
    )
    blocker_codes = [row["code"] for row in eligibility["blockers"]]
    assert "MISSING_DELIVERY_DATE" in blocker_codes


@pytest.mark.asyncio
async def test_sprint3a_schedule_without_price_is_blocked(db_session, test_project_item):
    pmo_user = await _create_pmo_user(db_session, "s3a_pmo_missing_price")
    test_project_item.delivery_options = ["2026-02-01"]
    await db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await finalize_project_item_by_id(
            item_id=test_project_item.id,
            finalize_data=ProjectItemFinalize(is_finalized=True),
            current_user=pmo_user,
            db=db_session,
        )

    blocker_codes = _extract_blocker_codes(exc.value)
    assert "MISSING_DELIVERY_PRICE" in blocker_codes


@pytest.mark.asyncio
async def test_sprint3a_non_positive_delivery_price_is_blocked(db_session, test_project_item):
    pmo_user = await _create_pmo_user(db_session, "s3a_pmo_bad_price")
    test_project_item.delivery_options = ["2026-02-01"]
    await _create_delivery_option(
        db_session,
        project_item_id=test_project_item.id,
        amount=Decimal("0"),
    )

    with pytest.raises(HTTPException) as exc:
        await finalize_project_item_by_id(
            item_id=test_project_item.id,
            finalize_data=ProjectItemFinalize(is_finalized=True),
            current_user=pmo_user,
            db=db_session,
        )

    blocker_codes = _extract_blocker_codes(exc.value)
    assert "INVALID_DELIVERY_PRICE" in blocker_codes


@pytest.mark.asyncio
async def test_sprint3a_valid_item_can_be_finalized(db_session, test_project_item):
    pmo_user = await _create_pmo_user(db_session, "s3a_pmo_valid")
    test_project_item.delivery_options = ["2026-02-01"]
    await _create_delivery_option(
        db_session,
        project_item_id=test_project_item.id,
        amount=Decimal("1500.00"),
    )

    result = await finalize_project_item_by_id(
        item_id=test_project_item.id,
        finalize_data=ProjectItemFinalize(is_finalized=True),
        current_user=pmo_user,
        db=db_session,
    )
    assert result.is_finalized is True


@pytest.mark.asyncio
async def test_sprint3a_invalid_finalize_does_not_mutate_item_or_create_records(
    db_session, test_project_item
):
    pmo_user = await _create_pmo_user(db_session, "s3a_pmo_guard")
    test_project_item.delivery_options = []
    await db_session.commit()

    before_pkg_count = (
        await db_session.execute(select(ProcurementPackage))
    ).scalars().all()
    before_submission_count = (
        await db_session.execute(select(OptimizationSubmission))
    ).scalars().all()

    with pytest.raises(HTTPException):
        await finalize_project_item_by_id(
            item_id=test_project_item.id,
            finalize_data=ProjectItemFinalize(is_finalized=True),
            current_user=pmo_user,
            db=db_session,
        )

    await db_session.refresh(test_project_item)
    assert test_project_item.is_finalized is False
    assert test_project_item.finalized_at is None

    after_pkg_count = (
        await db_session.execute(select(ProcurementPackage))
    ).scalars().all()
    after_submission_count = (
        await db_session.execute(select(OptimizationSubmission))
    ).scalars().all()

    assert len(after_pkg_count) == len(before_pkg_count)
    assert len(after_submission_count) == len(before_submission_count)


@pytest.mark.asyncio
async def test_sprint3a_bulk_finalize_reports_invalid_items_without_partial_updates(
    db_session, test_project_item
):
    pmo_user = await _create_pmo_user(db_session, "s3a_pmo_bulk")

    # Invalid item
    test_project_item.delivery_options = []

    # Valid item in same project
    valid_item = ProjectItem(
        project_id=test_project_item.project_id,
        item_code="S3A-VALID-001",
        item_name="Sprint 3A Valid Item",
        quantity=2,
        delivery_options=["2026-02-10"],
        status="PENDING",
        is_finalized=False,
    )
    db_session.add(valid_item)
    await db_session.commit()
    await db_session.refresh(valid_item)
    await _create_delivery_option(
        db_session,
        project_item_id=valid_item.id,
        amount=Decimal("2000.00"),
        delivery_date=date(2026, 2, 10),
    )

    with pytest.raises(HTTPException) as exc:
        await finalize_all_project_items(
            project_id=test_project_item.project_id,
            current_user=pmo_user,
            db=db_session,
        )

    assert exc.value.status_code == 422
    detail = exc.value.detail if isinstance(exc.value.detail, dict) else {}
    assert detail.get("code") == "BULK_PROCUREMENT_ELIGIBILITY_FAILED"
    assert detail.get("invalid_count") == 1
    assert isinstance(detail.get("invalid_items"), list)
    assert detail["invalid_items"][0]["project_item_id"] == test_project_item.id

    await db_session.refresh(test_project_item)
    await db_session.refresh(valid_item)
    assert test_project_item.is_finalized is False
    assert valid_item.is_finalized is False


@pytest.mark.asyncio
async def test_sprint3a_invalid_delivery_price_finalize_http_422_json_response(
    db_session, test_project_item
):
    pmo_user = await _create_pmo_user(db_session, "s3a_pmo_http_bad_price")
    test_project_item.delivery_options = ["2026-02-01"]
    await _create_delivery_option(
        db_session,
        project_item_id=test_project_item.id,
        amount=Decimal("0"),
    )

    response = await _request_items_api(
        db_session,
        pmo_user,
        "PUT",
        f"/items/{test_project_item.id}/finalize",
        json={"is_finalized": True},
    )

    assert response.status_code == 422
    payload = response.json()
    detail = payload.get("detail", {})
    assert detail.get("code") == "PROCUREMENT_ELIGIBILITY_FAILED"
    eligibility = detail.get("eligibility", {})
    blocker_codes = [row.get("code") for row in eligibility.get("blockers", [])]
    assert "INVALID_DELIVERY_PRICE" in blocker_codes
    assert isinstance(eligibility.get("messages"), list)
    assert isinstance(eligibility.get("inspected_delivery_options"), list)
    assert isinstance(
        eligibility["inspected_delivery_options"][0].get("delivery_date"), str
    )


@pytest.mark.asyncio
async def test_sprint3a_missing_quantity_finalize_http_422_json_response(
    db_session, test_project_item
):
    pmo_user = await _create_pmo_user(db_session, "s3a_pmo_http_missing_qty")
    test_project_item.delivery_options = ["2026-02-01"]
    test_project_item.quantity = 0
    await db_session.commit()
    await _create_delivery_option(
        db_session,
        project_item_id=test_project_item.id,
        amount=Decimal("1500.00"),
    )

    response = await _request_items_api(
        db_session,
        pmo_user,
        "PUT",
        f"/items/{test_project_item.id}/finalize",
        json={"is_finalized": True},
    )

    assert response.status_code == 422
    payload = response.json()
    detail = payload.get("detail", {})
    assert detail.get("code") == "PROCUREMENT_ELIGIBILITY_FAILED"
    eligibility = detail.get("eligibility", {})
    blocker_codes = [row.get("code") for row in eligibility.get("blockers", [])]
    assert "MISSING_QUANTITY" in blocker_codes
    assert isinstance(eligibility.get("messages"), list)
    assert isinstance(eligibility.get("inspected_delivery_options"), list)
    assert response.headers.get("content-type", "").startswith("application/json")


@pytest.mark.asyncio
async def test_sprint3a_bulk_finalize_http_422_structured_diagnostics(
    db_session, test_project_item
):
    pmo_user = await _create_pmo_user(db_session, "s3a_pmo_http_bulk")
    test_project_item.delivery_options = []
    await db_session.commit()

    valid_item = ProjectItem(
        project_id=test_project_item.project_id,
        item_code="S3A-VALID-HTTP-001",
        item_name="Sprint 3A Valid HTTP Item",
        quantity=2,
        delivery_options=["2026-02-10"],
        status="PENDING",
        is_finalized=False,
    )
    db_session.add(valid_item)
    await db_session.commit()
    await db_session.refresh(valid_item)
    await _create_delivery_option(
        db_session,
        project_item_id=valid_item.id,
        amount=Decimal("2000.00"),
        delivery_date=date(2026, 2, 10),
    )

    response = await _request_items_api(
        db_session,
        pmo_user,
        "PUT",
        f"/items/project/{test_project_item.project_id}/finalize-all",
        json={},
    )

    assert response.status_code == 422
    payload = response.json()
    detail = payload.get("detail", {})
    assert detail.get("code") == "BULK_PROCUREMENT_ELIGIBILITY_FAILED"
    assert isinstance(detail.get("invalid_items"), list)
    assert detail.get("invalid_items")
    assert detail["invalid_items"][0].get("project_item_id") == test_project_item.id
    assert response.headers.get("content-type", "").startswith("application/json")


@pytest.mark.asyncio
async def test_sprint3a_eligibility_endpoint_returns_json_response(
    db_session, test_project_item
):
    pmo_user = await _create_pmo_user(db_session, "s3a_pmo_http_eligibility")
    test_project_item.delivery_options = ["2026-02-01"]
    await _create_delivery_option(
        db_session,
        project_item_id=test_project_item.id,
        amount=Decimal("0"),
    )

    response = await _request_items_api(
        db_session,
        pmo_user,
        "GET",
        f"/items/{test_project_item.id}/procurement-eligibility",
    )

    assert response.status_code == 200
    payload = response.json()
    blocker_codes = [row.get("code") for row in payload.get("blockers", [])]
    assert "INVALID_DELIVERY_PRICE" in blocker_codes
    assert isinstance(payload.get("inspected_delivery_options"), list)
    assert response.headers.get("content-type", "").startswith("application/json")
