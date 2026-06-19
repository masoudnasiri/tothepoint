"""
Audit logs endpoints (admin-only)
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func  # type: ignore

from app.database import get_db
from app.auth import get_current_user, require_admin
from app.models import User, AuditLog

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("/")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=200),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
):
    """List audit logs with basic filters (admin-only)."""
    filters = []
    if user_id is not None:
        filters.append(AuditLog.user_id == user_id)
    if action:
        filters.append(AuditLog.action == action)
    if entity_type:
        filters.append(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        filters.append(AuditLog.entity_id == entity_id)

    where_clause = and_(*filters) if filters else None

    # Count total
    count_query = select(func.count(AuditLog.id))
    if where_clause is not None:
        count_query = count_query.where(where_clause)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Data query with pagination
    # Join user for username; keep outer join to handle deleted users
    data_query = (
        select(AuditLog, User.username)
        .select_from(AuditLog)
        .outerjoin(User, User.id == AuditLog.user_id)
        .order_by(AuditLog.created_at.desc())
    )
    if where_clause is not None:
        data_query = data_query.where(where_clause)
    data_query = data_query.offset((page - 1) * size).limit(size)

    result = await db.execute(data_query)
    rows = result.all()

    # Serialize simply
    items = []
    for (log_row, username) in rows:
        payload = {
            "id": log_row.id,
            "user_id": log_row.user_id,
            "username": username,
            "action": log_row.action,
            "entity_type": log_row.entity_type,
            "entity_id": log_row.entity_id,
            "details": log_row.details,
            "ip_address": log_row.ip_address,
            "user_agent": log_row.user_agent,
            "created_at": log_row.created_at.isoformat() if log_row.created_at else None,
        }
        items.append(jsonable_encoder(payload))

    pages = (total + size - 1) // size if size else 1
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


