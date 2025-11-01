"""
Decision factor weights management endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import get_current_user, require_admin
from app.crud import (
    create_decision_factor_weight, get_decision_factor_weight, get_decision_factor_weights,
    update_decision_factor_weight, delete_decision_factor_weight
)
from app.models import User
from app.schemas import DecisionFactorWeight, DecisionFactorWeightCreate, DecisionFactorWeightUpdate

router = APIRouter(prefix="/weights", tags=["decision-factor-weights"])


@router.get("/", response_model=List[DecisionFactorWeight])
async def list_decision_factor_weights(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all decision factor weights"""
    weights = await get_decision_factor_weights(db, skip=skip, limit=limit)
    return weights


@router.post("/", response_model=DecisionFactorWeight)
async def create_new_decision_factor_weight(
    weight: DecisionFactorWeightCreate,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
):
    """Create a new decision factor weight (admin only)"""
    return await create_decision_factor_weight(db, weight)


@router.get("/{weight_id}", response_model=DecisionFactorWeight)
async def get_weight_by_id(
    weight_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get decision factor weight by ID"""
    weight = await get_decision_factor_weight(db, weight_id)
    if not weight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision factor weight not found"
        )
    return weight


@router.put("/{weight_id}", response_model=DecisionFactorWeight)
async def update_weight_by_id(
    weight_id: int,
    weight_update: DecisionFactorWeightUpdate,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
):
    """Update decision factor weight (admin only)"""
    weight = await update_decision_factor_weight(db, weight_id, weight_update)
    if not weight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision factor weight not found"
        )
    return weight


@router.delete("/{weight_id}")
async def delete_weight_by_id(
    weight_id: int,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
):
    """Delete decision factor weight (admin only)"""
    success = await delete_decision_factor_weight(db, weight_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision factor weight not found"
        )
    return {"message": "Decision factor weight deleted successfully"}
