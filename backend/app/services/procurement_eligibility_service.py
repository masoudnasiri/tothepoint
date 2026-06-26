"""
Project-item procurement eligibility validation.

This service centralizes backend enforcement for "send to procurement"
(project-item finalization visibility in procurement scope).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    DeliveryOption,
    PackageSubItem,
    ProcurementPackage,
    Project,
    ProjectItem,
    ProjectItemSubItem,
)


BLOCKER_MESSAGES: Dict[str, str] = {
    "PROJECT_ITEM_NOT_FOUND": "Project item not found.",
    "PROJECT_ITEM_CANCELLED": "Project item is not active for procurement.",
    "MISSING_QUANTITY": "Required quantity must be greater than zero.",
    "NO_DELIVERY_OPTION": "No delivery option or delivery schedule is defined.",
    "MISSING_DELIVERY_DATE": "Delivery date is missing for delivery options/schedule.",
    "MISSING_DELIVERY_PRICE": "Delivery/sales price is missing.",
    "INVALID_DELIVERY_PRICE": "Delivery/sales price must be greater than zero.",
    "MISSING_DELIVERY_CURRENCY": "Delivery/sales currency is missing.",
}

WARNING_MESSAGES: Dict[str, str] = {
    "SUBITEM_COVERAGE_INCOMPLETE": (
        "Sub-item requirements are not fully covered by active package data."
    ),
    "INVALID_DELIVERY_SCHEDULE_DATE": (
        "Some delivery schedule values are invalid and could not be parsed."
    ),
}


def _build_issue(code: str, *, metadata: Optional[Dict[str, Any]] = None, warning: bool = False) -> Dict[str, Any]:
    dictionary = WARNING_MESSAGES if warning else BLOCKER_MESSAGES
    return {
        "code": code,
        "message": dictionary.get(code, code),
        "metadata": metadata or {},
    }


def _safe_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _parse_schedule_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    candidate = text[:10]
    try:
        return date.fromisoformat(candidate)
    except ValueError:
        return None


async def _resolve_project_item(
    db: AsyncSession, project_item_id: int, project_item: Optional[ProjectItem]
) -> Optional[ProjectItem]:
    if project_item is not None:
        return project_item
    result = await db.execute(
        select(ProjectItem).where(ProjectItem.id == project_item_id)
    )
    return result.scalar_one_or_none()


async def validate_project_item_procurement_eligibility(
    db: AsyncSession,
    project_item_id: int,
    *,
    project_item: Optional[ProjectItem] = None,
) -> Dict[str, Any]:
    """
    Validate whether a project item can be sent to procurement.

    Returns a diagnostics object:
    - is_eligible
    - blockers
    - warnings
    - messages
    - delivery_option_count
    - valid_delivery_option_count
    - inspected_delivery_options
    """
    blockers: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    inspected_delivery_options: List[Dict[str, Any]] = []
    valid_delivery_option_count = 0

    item = await _resolve_project_item(db, project_item_id, project_item)
    if item is None:
        blockers.append(_build_issue("PROJECT_ITEM_NOT_FOUND"))
        return {
            "project_item_id": project_item_id,
            "is_eligible": False,
            "blockers": blockers,
            "warnings": warnings,
            "messages": [issue["message"] for issue in blockers],
            "delivery_option_count": 0,
            "valid_delivery_option_count": 0,
            "has_delivery_schedule_dates": False,
            "inspected_delivery_options": [],
        }

    # "Active/not cancelled" maps to active project in current model.
    project_result = await db.execute(
        select(Project.is_active).where(Project.id == item.project_id)
    )
    project_is_active = project_result.scalar_one_or_none()
    if project_is_active is False:
        blockers.append(_build_issue("PROJECT_ITEM_CANCELLED"))

    quantity_value = int(item.quantity or 0)
    if quantity_value <= 0:
        blockers.append(_build_issue("MISSING_QUANTITY", metadata={"quantity": quantity_value}))

    raw_schedule = item.delivery_options if isinstance(item.delivery_options, list) else []
    parsed_schedule_dates: List[date] = []
    invalid_schedule_count = 0
    for value in raw_schedule:
        parsed = _parse_schedule_date(value)
        if parsed:
            parsed_schedule_dates.append(parsed)
        else:
            invalid_schedule_count += 1

    if invalid_schedule_count > 0:
        warnings.append(
            _build_issue(
                "INVALID_DELIVERY_SCHEDULE_DATE",
                metadata={"invalid_count": invalid_schedule_count},
                warning=True,
            )
        )

    has_schedule_dates = len(parsed_schedule_dates) > 0

    delivery_result = await db.execute(
        select(DeliveryOption)
        .where(
            DeliveryOption.project_item_id == item.id,
            DeliveryOption.is_active == True,  # noqa: E712
        )
        .order_by(DeliveryOption.id)
    )
    delivery_options = delivery_result.scalars().all()
    delivery_option_count = len(delivery_options)

    has_any_option_date = False
    has_any_price = False
    has_any_positive_price = False
    has_any_currency = False

    for option in delivery_options:
        price_amount = _safe_decimal(option.invoice_amount_per_unit)
        has_delivery_date = option.delivery_date is not None
        has_delivery_price = price_amount is not None
        is_positive_delivery_price = bool(
            price_amount is not None and price_amount > Decimal("0")
        )

        # DeliveryOption has no explicit sales currency in current model.
        # We expose IRR as implicit/base currency marker for diagnostics.
        delivery_currency = "IRR"
        has_delivery_currency = True

        has_any_option_date = has_any_option_date or has_delivery_date
        has_any_price = has_any_price or has_delivery_price
        has_any_positive_price = has_any_positive_price or is_positive_delivery_price
        has_any_currency = has_any_currency or has_delivery_currency

        is_valid = has_delivery_date and is_positive_delivery_price and has_delivery_currency
        if is_valid:
            valid_delivery_option_count += 1

        inspected_delivery_options.append(
            {
                "delivery_option_id": int(option.id),
                "source": "delivery_option",
                "delivery_date": option.delivery_date,
                "has_delivery_date": has_delivery_date,
                "delivery_price_amount": price_amount,
                "has_delivery_price": has_delivery_price,
                "is_positive_delivery_price": is_positive_delivery_price,
                "delivery_price_currency": delivery_currency,
                "has_delivery_currency": has_delivery_currency,
                "is_valid": is_valid,
            }
        )

    if delivery_option_count == 0 and not has_schedule_dates:
        blockers.append(_build_issue("NO_DELIVERY_OPTION"))

    if invalid_schedule_count > 0 and not has_schedule_dates and delivery_option_count == 0:
        blockers.append(
            _build_issue(
                "MISSING_DELIVERY_DATE",
                metadata={"invalid_schedule_count": invalid_schedule_count},
            )
        )

    if not has_schedule_dates and delivery_option_count > 0 and not has_any_option_date:
        blockers.append(_build_issue("MISSING_DELIVERY_DATE"))

    if has_schedule_dates and delivery_option_count == 0:
        blockers.append(_build_issue("MISSING_DELIVERY_PRICE"))
    elif delivery_option_count > 0:
        if not has_any_price:
            blockers.append(_build_issue("MISSING_DELIVERY_PRICE"))
        elif not has_any_positive_price:
            blockers.append(_build_issue("INVALID_DELIVERY_PRICE"))

        if not has_any_currency:
            blockers.append(_build_issue("MISSING_DELIVERY_CURRENCY"))

    # Sub-item diagnostics: warning-only in current business model.
    subitem_result = await db.execute(
        select(ProjectItemSubItem).where(ProjectItemSubItem.project_item_id == item.id)
    )
    required_subitems = [
        row for row in subitem_result.scalars().all() if int(row.quantity or 0) > 0
    ]
    if required_subitems:
        required_map = {int(row.id): int(row.quantity or 0) for row in required_subitems}
        coverage_result = await db.execute(
            select(
                PackageSubItem.project_item_subitem_id,
                func.coalesce(func.sum(PackageSubItem.quantity_covered), 0),
            )
            .join(ProcurementPackage, ProcurementPackage.id == PackageSubItem.package_id)
            .where(
                ProcurementPackage.project_item_id == item.id,
                ProcurementPackage.is_active == True,  # noqa: E712
                PackageSubItem.project_item_subitem_id.in_(list(required_map.keys())),
            )
            .group_by(PackageSubItem.project_item_subitem_id)
        )
        covered_map = {
            int(row[0]): int(row[1] or 0) for row in coverage_result.all()
        }
        uncovered_ids = [
            subitem_id
            for subitem_id, required in required_map.items()
            if int(covered_map.get(subitem_id, 0)) < required
        ]
        if uncovered_ids:
            warnings.append(
                _build_issue(
                    "SUBITEM_COVERAGE_INCOMPLETE",
                    metadata={
                        "required_subitem_count": len(required_map),
                        "uncovered_subitem_count": len(uncovered_ids),
                        "uncovered_subitem_ids": uncovered_ids,
                    },
                    warning=True,
                )
            )

    # De-duplicate blockers by code while preserving first occurrence.
    dedup_blockers: List[Dict[str, Any]] = []
    seen_blockers = set()
    for issue in blockers:
        code = issue["code"]
        if code in seen_blockers:
            continue
        seen_blockers.add(code)
        dedup_blockers.append(issue)

    messages = [issue["message"] for issue in dedup_blockers] + [
        issue["message"] for issue in warnings
    ]

    return {
        "project_item_id": int(item.id),
        "is_eligible": len(dedup_blockers) == 0,
        "blockers": dedup_blockers,
        "warnings": warnings,
        "messages": messages,
        "delivery_option_count": delivery_option_count,
        "valid_delivery_option_count": valid_delivery_option_count,
        "has_delivery_schedule_dates": has_schedule_dates,
        "inspected_delivery_options": inspected_delivery_options,
    }
