"""
Exchange Rates API endpoints

Provides endpoints for managing historical exchange rates used in currency conversions.
"""

from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.database import get_db
from app.auth import get_current_user, require_admin
from app.models import ExchangeRate, User
from app.schemas import (
    ExchangeRate as ExchangeRateSchema,
    ExchangeRateCreate,
    ExchangeRateUpdate,
    ExchangeRateHistory
)
from pydantic import BaseModel, Field

router = APIRouter(prefix="/exchange-rates", tags=["exchange-rates"])


class ExchangeRateResponse(BaseModel):
    """Response model for exchange rate"""
    id: int
    date: date
    from_currency: str
    to_currency: str
    rate: Decimal
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None
    
    model_config = {"from_attributes": True}


class ExchangeRateCreateRequest(BaseModel):
    """Request model for creating exchange rate"""
    date: date = Field(..., description="Date for which this rate is valid")
    from_currency: str = Field(..., min_length=3, max_length=3, description="Source currency code")
    to_currency: str = Field(..., min_length=3, max_length=3, description="Target currency code")
    rate: Decimal = Field(..., gt=0, description="Exchange rate")
    is_active: bool = Field(default=True, description="Whether this rate is active")


class ExchangeRateUpdateRequest(BaseModel):
    """Request model for updating exchange rate"""
    rate: Optional[Decimal] = Field(None, gt=0, description="Exchange rate")
    is_active: Optional[bool] = Field(None, description="Whether this rate is active")


class ExchangeRateHistoryRequest(BaseModel):
    """Request model for getting rate history"""
    from_currency: str = Field(..., min_length=3, max_length=3, description="Source currency code")
    to_currency: str = Field(..., min_length=3, max_length=3, description="Target currency code")
    start_date: Optional[date] = Field(None, description="Start date for history")
    end_date: Optional[date] = Field(None, description="End date for history")


@router.get("/", response_model=List[ExchangeRateResponse])
async def list_exchange_rates(
    from_currency: Optional[str] = Query(None, description="Filter by source currency"),
    to_currency: Optional[str] = Query(None, description="Filter by target currency"),
    date_from: Optional[date] = Query(None, description="Filter by date from"),
    date_to: Optional[date] = Query(None, description="Filter by date to"),
    active_only: bool = Query(True, description="Show only active rates"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of exchange rates with optional filtering"""
    
    stmt = select(ExchangeRate)
    
    # Apply filters
    if from_currency:
        stmt = stmt.where(ExchangeRate.from_currency == from_currency)
    
    if to_currency:
        stmt = stmt.where(ExchangeRate.to_currency == to_currency)
    
    if date_from:
        stmt = stmt.where(ExchangeRate.date >= date_from)
    
    if date_to:
        stmt = stmt.where(ExchangeRate.date <= date_to)
    
    if active_only:
        stmt = stmt.where(ExchangeRate.is_active == True)
    
    # Order by date (most recent first)
    stmt = stmt.order_by(desc(ExchangeRate.date))
    
    # Apply pagination
    stmt = stmt.offset(offset).limit(limit)
    
    result = await db.execute(stmt)
    rates = result.scalars().all()
    
    return [
        ExchangeRateResponse(
            id=rate.id,
            date=rate.date,
            from_currency=rate.from_currency,
            to_currency=rate.to_currency,
            rate=rate.rate,
            is_active=rate.is_active,
            created_at=rate.created_at.isoformat(),
            updated_at=rate.updated_at.isoformat() if rate.updated_at else None
        )
        for rate in rates
    ]


@router.post("/", response_model=ExchangeRateResponse)
async def create_exchange_rate(
    rate_data: ExchangeRateCreateRequest,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
):
    """Create a new exchange rate (admin only)"""
    
    # Validate currencies are different
    if rate_data.from_currency == rate_data.to_currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source and target currencies must be different"
        )
    
    # Check if rate already exists for this date and currency pair
    existing_stmt = select(ExchangeRate).where(
        and_(
            ExchangeRate.date == rate_data.date,
            ExchangeRate.from_currency == rate_data.from_currency,
            ExchangeRate.to_currency == rate_data.to_currency
        )
    )
    existing_result = await db.execute(existing_stmt)
    existing_rate = existing_result.scalar_one_or_none()
    
    if existing_rate:
        # Update existing rate instead of creating duplicate
        existing_rate.rate = rate_data.rate
        existing_rate.is_active = rate_data.is_active
        await db.commit()
        await db.refresh(existing_rate)
        
        return ExchangeRateResponse(
            id=existing_rate.id,
            date=existing_rate.date,
            from_currency=existing_rate.from_currency,
            to_currency=existing_rate.to_currency,
            rate=existing_rate.rate,
            is_active=existing_rate.is_active,
            created_at=existing_rate.created_at.isoformat(),
            updated_at=existing_rate.updated_at.isoformat() if existing_rate.updated_at else None
        )
    
    # Create new rate
    new_rate = ExchangeRate(
        date=rate_data.date,
        from_currency=rate_data.from_currency,
        to_currency=rate_data.to_currency,
        rate=rate_data.rate,
        is_active=rate_data.is_active,
        created_by_id=current_user.id
    )
    
    db.add(new_rate)
    await db.commit()
    await db.refresh(new_rate)
    
    return ExchangeRateResponse(
        id=new_rate.id,
        date=new_rate.date,
        from_currency=new_rate.from_currency,
        to_currency=new_rate.to_currency,
        rate=new_rate.rate,
        is_active=new_rate.is_active,
        created_at=new_rate.created_at.isoformat(),
        updated_at=new_rate.updated_at.isoformat() if new_rate.updated_at else None
    )


@router.get("/{rate_id}", response_model=ExchangeRateResponse)
async def get_exchange_rate(
    rate_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific exchange rate by ID"""
    
    stmt = select(ExchangeRate).where(ExchangeRate.id == rate_id)
    result = await db.execute(stmt)
    rate = result.scalar_one_or_none()
    
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange rate not found"
        )
    
    return ExchangeRateResponse(
        id=rate.id,
        date=rate.date,
        from_currency=rate.from_currency,
        to_currency=rate.to_currency,
        rate=rate.rate,
        is_active=rate.is_active,
        created_at=rate.created_at.isoformat(),
        updated_at=rate.updated_at.isoformat() if rate.updated_at else None
    )


@router.put("/{rate_id}", response_model=ExchangeRateResponse)
async def update_exchange_rate(
    rate_id: int,
    rate_data: ExchangeRateUpdateRequest,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
):
    """Update an exchange rate (admin only)"""
    
    stmt = select(ExchangeRate).where(ExchangeRate.id == rate_id)
    result = await db.execute(stmt)
    rate = result.scalar_one_or_none()
    
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange rate not found"
        )
    
    # Update fields
    if rate_data.rate is not None:
        rate.rate = rate_data.rate
    
    if rate_data.is_active is not None:
        rate.is_active = rate_data.is_active
    
    await db.commit()
    await db.refresh(rate)
    
    return ExchangeRateResponse(
        id=rate.id,
        date=rate.date,
        from_currency=rate.from_currency,
        to_currency=rate.to_currency,
        rate=rate.rate,
        is_active=rate.is_active,
        created_at=rate.created_at.isoformat(),
        updated_at=rate.updated_at.isoformat() if rate.updated_at else None
    )


@router.delete("/{rate_id}")
async def delete_exchange_rate(
    rate_id: int,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
):
    """Delete an exchange rate (admin only)"""
    
    stmt = select(ExchangeRate).where(ExchangeRate.id == rate_id)
    result = await db.execute(stmt)
    rate = result.scalar_one_or_none()
    
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange rate not found"
        )
    
    await db.delete(rate)
    await db.commit()
    
    return {"message": "Exchange rate deleted successfully"}


@router.post("/history", response_model=List[ExchangeRateHistory])
async def get_rate_history(
    request: ExchangeRateHistoryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get historical exchange rates between two currencies"""
    
    stmt = select(ExchangeRate).where(
        and_(
            ExchangeRate.from_currency == request.from_currency,
            ExchangeRate.to_currency == request.to_currency,
            ExchangeRate.is_active == True
        )
    )
    
    if request.start_date:
        stmt = stmt.where(ExchangeRate.date >= request.start_date)
    
    if request.end_date:
        stmt = stmt.where(ExchangeRate.date <= request.end_date)
    
    stmt = stmt.order_by(ExchangeRate.date)
    
    result = await db.execute(stmt)
    rates = result.scalars().all()
    
    return [
        ExchangeRateHistory(
            date=rate.date,
            rate=rate.rate
        )
        for rate in rates
    ]


@router.get("/currencies/available")
async def get_available_currencies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of all currencies that have exchange rates"""
    
    stmt = select(ExchangeRate.from_currency, ExchangeRate.to_currency).where(
        ExchangeRate.is_active == True
    ).distinct()
    
    result = await db.execute(stmt)
    currencies = set()
    
    for row in result:
        currencies.add(row.from_currency)
        currencies.add(row.to_currency)
    
    # Always include base currency
    currencies.add('IRR')
    
    return {"currencies": sorted(list(currencies))}
