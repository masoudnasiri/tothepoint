"""
Currency conversion and utility functions
"""

from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import Currency, ExchangeRate


class CurrencyService:
    """Service for currency conversion and management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_base_currency(self) -> Optional[Currency]:
        """Get the base currency (IRR)"""
        result = await self.db.execute(
            select(Currency).where(Currency.is_base_currency == True)
        )
        return result.scalar_one_or_none()
    
    async def get_currency_by_id(self, currency_id: int) -> Optional[Currency]:
        """Get currency by ID"""
        result = await self.db.execute(
            select(Currency).where(Currency.id == currency_id)
        )
        return result.scalar_one_or_none()
    
    async def get_currency_by_code(self, code: str) -> Optional[Currency]:
        """Get currency by code"""
        result = await self.db.execute(
            select(Currency).where(Currency.code == code.upper())
        )
        return result.scalar_one_or_none()
    
    async def get_latest_exchange_rate(self, currency_id: int, rate_date: Optional[date] = None) -> Optional[ExchangeRate]:
        """Get the latest exchange rate for a currency"""
        if rate_date is None:
            rate_date = date.today()
        
        query = select(ExchangeRate).where(
            and_(
                ExchangeRate.currency_id == currency_id,
                ExchangeRate.is_active == True,
                ExchangeRate.rate_date <= rate_date
            )
        ).order_by(ExchangeRate.rate_date.desc()).limit(1)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def convert_to_base_currency(self, amount: Decimal, from_currency_id: int, rate_date: Optional[date] = None) -> Optional[Decimal]:
        """Convert amount to base currency (IRR)"""
        if rate_date is None:
            rate_date = date.today()
        
        # Get exchange rate
        rate = await self.get_latest_exchange_rate(from_currency_id, rate_date)
        if not rate:
            return None
        
        return amount * rate.rate_to_base
    
    async def convert_from_base_currency(self, amount: Decimal, to_currency_id: int, rate_date: Optional[date] = None) -> Optional[Decimal]:
        """Convert amount from base currency (IRR) to target currency"""
        if rate_date is None:
            rate_date = date.today()
        
        # Get exchange rate
        rate = await self.get_latest_exchange_rate(to_currency_id, rate_date)
        if not rate:
            return None
        
        return amount / rate.rate_to_base
    
    async def convert_currency(self, amount: Decimal, from_currency_id: int, to_currency_id: int, rate_date: Optional[date] = None) -> Optional[Decimal]:
        """Convert amount between any two currencies"""
        if from_currency_id == to_currency_id:
            return amount
        
        # Convert to base currency first
        base_amount = await self.convert_to_base_currency(amount, from_currency_id, rate_date)
        if base_amount is None:
            return None
        
        # Convert from base currency to target currency
        return await self.convert_from_base_currency(base_amount, to_currency_id, rate_date)
    
    async def format_currency_amount(self, amount: Decimal, currency_id: int) -> str:
        """Format amount according to currency settings"""
        currency = await self.get_currency_by_id(currency_id)
        if not currency:
            return str(amount)
        
        # Format with appropriate decimal places
        decimal_places = currency.decimal_places
        formatted_amount = f"{amount:.{decimal_places}f}"
        
        # Add currency symbol
        return f"{currency.symbol}{formatted_amount}"
    
    async def get_currency_display_info(self, currency_id: int) -> Optional[Dict[str, Any]]:
        """Get currency display information"""
        currency = await self.get_currency_by_id(currency_id)
        if not currency:
            return None
        
        latest_rate = await self.get_latest_exchange_rate(currency_id)
        
        return {
            "id": currency.id,
            "code": currency.code,
            "name": currency.name,
            "symbol": currency.symbol,
            "decimal_places": currency.decimal_places,
            "is_base_currency": currency.is_base_currency,
            "latest_rate": latest_rate.rate_to_base if latest_rate else None,
            "rate_date": latest_rate.rate_date if latest_rate else None
        }
    
    async def get_all_active_currencies(self) -> list[Currency]:
        """Get all active currencies"""
        result = await self.db.execute(
            select(Currency).where(Currency.is_active == True).order_by(Currency.code)
        )
        return result.scalars().all()
    
    async def validate_currency_conversion(self, from_currency_id: int, to_currency_id: int, rate_date: Optional[date] = None) -> bool:
        """Validate that conversion is possible between currencies"""
        if from_currency_id == to_currency_id:
            return True
        
        # Check if both currencies have exchange rates
        from_rate = await self.get_latest_exchange_rate(from_currency_id, rate_date)
        to_rate = await self.get_latest_exchange_rate(to_currency_id, rate_date)
        
        return from_rate is not None and to_rate is not None


# Global currency service instance
_currency_service: Optional[CurrencyService] = None

def get_currency_service(db: AsyncSession) -> CurrencyService:
    """Get currency service instance"""
    return CurrencyService(db)
