"""
Currency and Exchange Rate management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from datetime import date, datetime
from decimal import Decimal
import logging

from app.database import get_db
from app.auth import get_current_user, require_finance
from app.models import Currency, ExchangeRate, User

logger = logging.getLogger(__name__)
from app.schemas import (
    Currency as CurrencySchema, CurrencyCreate, CurrencyUpdate,
    ExchangeRate as ExchangeRateSchema, ExchangeRateCreate, ExchangeRateUpdate,
    CurrencyWithRates
)

router = APIRouter(prefix="/currencies", tags=["currencies"])


@router.get("/", response_model=List[CurrencyWithRates])
async def list_currencies(
    include_inactive: bool = Query(False, description="Include inactive currencies"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of all currencies with latest exchange rates"""
    query = select(Currency)
    
    if not include_inactive:
        query = query.where(Currency.is_active == True)
    
    query = query.order_by(Currency.is_base_currency.desc(), Currency.code.asc())
    
    result = await db.execute(query)
    currencies = result.scalars().all()
    
    # Get latest exchange rates for each currency
    currency_list = []
    for currency in currencies:
        # Base currency always has rate 1.0
        if currency.is_base_currency:
            currency_data = CurrencyWithRates(
                id=currency.id,
                code=currency.code,
                name=currency.name,
                symbol=currency.symbol,
                is_base_currency=currency.is_base_currency,
                is_active=currency.is_active,
                decimal_places=currency.decimal_places,
                created_at=currency.created_at,
                updated_at=currency.updated_at,
                created_by_id=currency.created_by_id,
                latest_rate=None,
                rate_to_base=1.0
            )
        else:
            # Get latest exchange rate for non-base currencies (convert to IRR)
            # Note: Exchange rates table may not exist yet
            try:
                rate_query = select(ExchangeRate).where(
                    and_(
                        ExchangeRate.from_currency == currency.code,
                        ExchangeRate.to_currency == 'IRR',  # Convert to base currency
                        ExchangeRate.is_active == True,
                        ExchangeRate.date <= date.today()
                    )
                ).order_by(ExchangeRate.date.desc()).limit(1)
                
                rate_result = await db.execute(rate_query)
                latest_rate = rate_result.scalar_one_or_none()
                
                currency_data = CurrencyWithRates(
                    id=currency.id,
                    code=currency.code,
                    name=currency.name,
                    symbol=currency.symbol,
                    is_base_currency=currency.is_base_currency,
                    is_active=currency.is_active,
                    decimal_places=currency.decimal_places,
                    created_at=currency.created_at,
                    updated_at=currency.updated_at,
                    created_by_id=currency.created_by_id,
                    latest_rate=latest_rate,
                    rate_to_base=latest_rate.rate if latest_rate else None
                )
            except Exception as e:
                # If exchange rates table doesn't exist, return currency without rate
                logger.warning(f"Could not fetch exchange rate for {currency.code}: {e}")
                currency_data = CurrencyWithRates(
                    id=currency.id,
                    code=currency.code,
                    name=currency.name,
                    symbol=currency.symbol,
                    is_base_currency=currency.is_base_currency,
                    is_active=currency.is_active,
                    decimal_places=currency.decimal_places,
                    created_at=currency.created_at,
                    updated_at=currency.updated_at,
                    created_by_id=currency.created_by_id,
                    latest_rate=None,
                    rate_to_base=None
                )
        currency_list.append(currency_data)
    
    return currency_list


@router.post("/", response_model=CurrencySchema)
async def create_currency(
    currency: CurrencyCreate,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Create a new currency (Finance/Admin only)"""
    
    # Check if currency code already exists
    existing = await db.execute(
        select(Currency).where(Currency.code == currency.code.upper())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Currency with code '{currency.code}' already exists"
        )
    
    # If setting as base currency, unset any existing base currency
    if currency.is_base_currency:
        await db.execute(
            select(Currency).where(Currency.is_base_currency == True)
        )
        existing_base = await db.execute(
            select(Currency).where(Currency.is_base_currency == True)
        )
        if existing_base.scalar_one_or_none():
            # Update existing base currency
            existing_base_currency = existing_base.scalar_one()
            existing_base_currency.is_base_currency = False
            await db.commit()
    
    # Create new currency
    db_currency = Currency(
        code=currency.code.upper(),
        name=currency.name,
        symbol=currency.symbol,
        is_base_currency=currency.is_base_currency,
        is_active=currency.is_active,
        decimal_places=currency.decimal_places,
        created_by_id=current_user.id
    )
    
    db.add(db_currency)
    await db.commit()
    await db.refresh(db_currency)
    
    return db_currency


@router.get("/{currency_id}", response_model=CurrencyWithRates)
async def get_currency(
    currency_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get currency details with latest exchange rate"""
    result = await db.execute(
        select(Currency).where(Currency.id == currency_id)
    )
    currency = result.scalar_one_or_none()
    
    if not currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Currency not found"
        )
    
    # Get latest exchange rate
    rate_query = select(ExchangeRate).where(
        and_(
            ExchangeRate.currency_id == currency.id,
            ExchangeRate.is_active == True,
            ExchangeRate.rate_date <= date.today()
        )
    ).order_by(ExchangeRate.rate_date.desc()).limit(1)
    
    rate_result = await db.execute(rate_query)
    latest_rate = rate_result.scalar_one_or_none()
    
    return CurrencyWithRates(
        id=currency.id,
        code=currency.code,
        name=currency.name,
        symbol=currency.symbol,
        is_base_currency=currency.is_base_currency,
        is_active=currency.is_active,
        decimal_places=currency.decimal_places,
        created_at=currency.created_at,
        updated_at=currency.updated_at,
        created_by_id=currency.created_by_id,
        latest_rate=latest_rate,
        rate_to_base=latest_rate.rate_to_base if latest_rate else None
    )


@router.put("/{currency_id}", response_model=CurrencySchema)
async def update_currency(
    currency_id: int,
    currency_update: CurrencyUpdate,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Update currency (Finance/Admin only)"""
    result = await db.execute(
        select(Currency).where(Currency.id == currency_id)
    )
    currency = result.scalar_one_or_none()
    
    if not currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Currency not found"
        )
    
    # If setting as base currency, unset any existing base currency
    if currency_update.is_base_currency:
        existing_base = await db.execute(
            select(Currency).where(
                and_(
                    Currency.is_base_currency == True,
                    Currency.id != currency_id
                )
            )
        )
        if existing_base.scalar_one_or_none():
            # Update existing base currency
            existing_base_currency = existing_base.scalar_one()
            existing_base_currency.is_base_currency = False
            await db.commit()
    
    # Update currency
    update_data = currency_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(currency, field, value)
    
    await db.commit()
    await db.refresh(currency)
    
    return currency


@router.delete("/{currency_id}")
async def delete_currency(
    currency_id: int,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Delete currency (Finance/Admin only)"""
    result = await db.execute(
        select(Currency).where(Currency.id == currency_id)
    )
    currency = result.scalar_one_or_none()
    
    if not currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Currency not found"
        )
    
    if currency.is_base_currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete base currency"
        )
    
    # Check if currency is used in procurement options or decisions
    # This would require additional queries to check for dependencies
    
    await db.delete(currency)
    await db.commit()
    
    return {"message": "Currency deleted successfully"}


# NEW: Simple Exchange Rate Management for new structure
@router.post("/rates/add")
async def add_exchange_rate(
    date_str: str = Query(..., description="Date in YYYY-MM-DD format"),
    from_currency: str = Query(..., description="Source currency code"),
    to_currency: str = Query(..., description="Target currency code"),  
    rate: Decimal = Query(..., gt=0, description="Exchange rate"),
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Add or update an exchange rate for a specific date (Finance/Admin only)"""
    
    # Parse date
    try:
        rate_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Check if rate already exists
    existing_query = select(ExchangeRate).where(
        and_(
            ExchangeRate.date == rate_date,
            ExchangeRate.from_currency == from_currency,
            ExchangeRate.to_currency == to_currency
        )
    )
    result = await db.execute(existing_query)
    existing_rate = result.scalar_one_or_none()
    
    if existing_rate:
        # Update existing rate
        existing_rate.rate = rate
        existing_rate.is_active = True
        existing_rate.updated_at = datetime.now()
        await db.commit()
        return {"message": "Exchange rate updated successfully", "id": existing_rate.id}
    else:
        # Create new rate
        new_rate = ExchangeRate(
            date=rate_date,
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
            is_active=True,
            created_by_id=current_user.id
        )
        db.add(new_rate)
        await db.commit()
        await db.refresh(new_rate)
        return {"message": "Exchange rate added successfully", "id": new_rate.id}


@router.get("/rates/list")
async def list_exchange_rates(
    from_currency: Optional[str] = Query(None, description="Filter by source currency"),
    to_currency: Optional[str] = Query(None, description="Filter by target currency"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all exchange rates with optional filtering"""
    
    query = select(ExchangeRate).where(ExchangeRate.is_active == True)
    
    if from_currency:
        query = query.where(ExchangeRate.from_currency == from_currency)
    if to_currency:
        query = query.where(ExchangeRate.to_currency == to_currency)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.where(ExchangeRate.date >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.where(ExchangeRate.date <= end)
        except ValueError:
            pass
    
    query = query.order_by(ExchangeRate.date.desc(), ExchangeRate.from_currency)
    
    result = await db.execute(query)
    rates = result.scalars().all()
    
    return [
        {
            "id": rate.id,
            "date": rate.date.isoformat(),
            "from_currency": rate.from_currency,
            "to_currency": rate.to_currency,
            "rate": float(rate.rate),
            "is_active": rate.is_active
        }
        for rate in rates
    ]


@router.put("/rates/{rate_id}")
async def update_exchange_rate(
    rate_id: int,
    rate: Decimal = Query(..., gt=0, description="New exchange rate"),
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Update an exchange rate (Finance/Admin only)"""
    
    query = select(ExchangeRate).where(ExchangeRate.id == rate_id)
    result = await db.execute(query)
    exchange_rate = result.scalar_one_or_none()
    
    if not exchange_rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange rate not found"
        )
    
    exchange_rate.rate = rate
    exchange_rate.updated_at = datetime.now()
    await db.commit()
    
    return {"message": "Exchange rate updated successfully"}


@router.delete("/rates/{rate_id}")
async def delete_exchange_rate(
    rate_id: int,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Delete an exchange rate (Finance/Admin only)"""
    
    query = select(ExchangeRate).where(ExchangeRate.id == rate_id)
    result = await db.execute(query)
    exchange_rate = result.scalar_one_or_none()
    
    if not exchange_rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange rate not found"
        )
    
    await db.delete(exchange_rate)
    await db.commit()
    
    return {"message": "Exchange rate deleted successfully"}


# Exchange Rate Management
@router.get("/{currency_id}/exchange-rates", response_model=List[ExchangeRateSchema])
async def get_exchange_rates(
    currency_id: int,
    start_date: Optional[date] = Query(None, description="Start date for rate history"),
    end_date: Optional[date] = Query(None, description="End date for rate history"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get exchange rates for a currency"""
    query = select(ExchangeRate).options(selectinload(ExchangeRate.currency)).where(ExchangeRate.currency_id == currency_id)
    
    if start_date:
        query = query.where(ExchangeRate.rate_date >= start_date)
    if end_date:
        query = query.where(ExchangeRate.rate_date <= end_date)
    
    query = query.order_by(ExchangeRate.rate_date.desc())
    
    result = await db.execute(query)
    rates = result.scalars().all()
    
    return rates


@router.post("/{currency_id}/exchange-rates", response_model=ExchangeRateSchema)
async def create_exchange_rate(
    currency_id: int,
    rate: ExchangeRateCreate,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Create exchange rate for a currency (Finance/Admin only)"""
    
    # Verify currency exists
    currency_result = await db.execute(
        select(Currency).where(Currency.id == currency_id)
    )
    currency = currency_result.scalar_one_or_none()
    
    if not currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Currency not found"
        )
    
    # Check if rate already exists for this date
    existing_rate_result = await db.execute(
        select(ExchangeRate).where(
            and_(
                ExchangeRate.currency_id == currency_id,
                ExchangeRate.rate_date == rate.rate_date
            )
        )
    )
    existing_rate = existing_rate_result.scalar_one_or_none()
    
    if existing_rate:
        # Update existing rate instead of creating a duplicate
        existing_rate.rate_to_base = rate.rate_to_base
        existing_rate.is_active = rate.is_active
        existing_rate.created_by_id = current_user.id  # Track who updated it
        await db.commit()
        await db.refresh(existing_rate)
        return existing_rate
    
    # Create new exchange rate
    db_rate = ExchangeRate(
        currency_id=currency_id,
        rate_date=rate.rate_date,
        rate_to_base=rate.rate_to_base,
        is_active=rate.is_active,
        created_by_id=current_user.id
    )
    
    db.add(db_rate)
    await db.commit()
    await db.refresh(db_rate)
    
    return db_rate


@router.put("/exchange-rates/{rate_id}", response_model=ExchangeRateSchema)
async def update_exchange_rate(
    rate_id: int,
    rate_update: ExchangeRateUpdate,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Update exchange rate (Finance/Admin only)"""
    result = await db.execute(
        select(ExchangeRate).where(ExchangeRate.id == rate_id)
    )
    rate = result.scalar_one_or_none()
    
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange rate not found"
        )
    
    # Update rate
    update_data = rate_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rate, field, value)
    
    await db.commit()
    await db.refresh(rate)
    
    return rate


@router.delete("/exchange-rates/{rate_id}")
async def delete_exchange_rate_legacy(
    rate_id: int,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Delete exchange rate (Finance/Admin only)"""
    result = await db.execute(
        select(ExchangeRate).where(ExchangeRate.id == rate_id)
    )
    rate = result.scalar_one_or_none()
    
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange rate not found"
        )
    
    await db.delete(rate)
    await db.commit()
    
    return {"message": "Exchange rate deleted successfully"}


@router.get("/base-currency", response_model=CurrencySchema)
async def get_base_currency(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the base currency"""
    result = await db.execute(
        select(Currency).where(Currency.is_base_currency == True)
    )
    base_currency = result.scalar_one_or_none()
    
    if not base_currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No base currency configured"
        )
    
    return base_currency


@router.post("/convert", response_model=dict)
async def convert_currency(
    amount: Decimal = Query(..., gt=0, description="Amount to convert"),
    from_currency_id: int = Query(..., description="Source currency ID"),
    to_currency_id: int = Query(..., description="Target currency ID"),
    conversion_date: Optional[date] = Query(None, description="Date for conversion (defaults to today)"),
    db: AsyncSession = Depends(get_db)
):
    """Convert amount between currencies"""
    if conversion_date is None:
        conversion_date = date.today()
    
    # Get the currencies to check if they are base currencies
    from_currency_result = await db.execute(
        select(Currency).where(Currency.id == from_currency_id)
    )
    to_currency_result = await db.execute(
        select(Currency).where(Currency.id == to_currency_id)
    )
    
    from_currency = from_currency_result.scalar_one_or_none()
    to_currency = to_currency_result.scalar_one_or_none()
    
    if not from_currency or not to_currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both currencies not found"
        )
    
    # Get exchange rates (base currency always has rate 1.0)
    from_rate_to_base = Decimal("1.0")
    to_rate_to_base = Decimal("1.0")
    
    if not from_currency.is_base_currency:
        from_rate_query = select(ExchangeRate).where(
            and_(
                ExchangeRate.from_currency == from_currency.code,
                ExchangeRate.to_currency == 'IRR',  # Assuming IRR is base currency
                ExchangeRate.is_active == True,
                ExchangeRate.date <= conversion_date
            )
        ).order_by(ExchangeRate.date.desc()).limit(1)
        
        from_rate_result = await db.execute(from_rate_query)
        from_rate = from_rate_result.scalar_one_or_none()
        
        if not from_rate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No exchange rate found for {from_currency.code} on or before {conversion_date}"
            )
        from_rate_to_base = from_rate.rate
    
    if not to_currency.is_base_currency:
        to_rate_query = select(ExchangeRate).where(
            and_(
                ExchangeRate.from_currency == to_currency.code,
                ExchangeRate.to_currency == 'IRR',  # Assuming IRR is base currency
                ExchangeRate.is_active == True,
                ExchangeRate.date <= conversion_date
            )
        ).order_by(ExchangeRate.date.desc()).limit(1)
        
        to_rate_result = await db.execute(to_rate_query)
        to_rate = to_rate_result.scalar_one_or_none()
        
        if not to_rate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No exchange rate found for {to_currency.code} on or before {conversion_date}"
            )
        to_rate_to_base = to_rate.rate
    
    # Convert to base currency first, then to target currency
    base_amount = amount * from_rate_to_base
    converted_amount = base_amount / to_rate_to_base
    
    return {
        "original_amount": amount,
        "converted_amount": converted_amount,
        "from_currency_id": from_currency_id,
        "to_currency_id": to_currency_id,
        "conversion_date": conversion_date,
        "from_rate": from_rate_to_base,
        "to_rate": to_rate_to_base
    }
