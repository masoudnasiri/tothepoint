"""
Currency Conversion Service

This service handles all currency conversions using time-variant exchange rates.
It implements rigorous financial accounting principles:
- All conversions use exchange rates valid for the transaction date
- Base currency (IRR) is used for all aggregate calculations
- No mixing of currencies without explicit conversion
"""

from typing import Optional
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.models import ExchangeRate
import logging

logger = logging.getLogger(__name__)

# Base currency for the system
BASE_CURRENCY = 'IRR'


class CurrencyConversionService:
    """Service for handling currency conversions with time-variant exchange rates"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def convert_to_base(
        self, 
        amount: Decimal, 
        currency: str, 
        transaction_date: date
    ) -> Decimal:
        """
        Convert any currency amount to base currency (IRR) using exchange rate
        valid for the transaction date.
        
        Args:
            amount: The amount to convert
            currency: Source currency code (e.g., 'USD', 'EUR')
            transaction_date: Date of the transaction (for rate lookup)
            
        Returns:
            Amount converted to base currency (IRR)
            
        Raises:
            ValueError: If currency is invalid or rate not found
        """
        if not amount or amount <= 0:
            return Decimal('0')
        
        # If already in base currency, return as-is
        if currency == BASE_CURRENCY:
            return amount
        
        # Find the exchange rate for the transaction date
        # Use the closest available rate on or before the transaction date
        rate = await self._get_exchange_rate(currency, BASE_CURRENCY, transaction_date)
        
        if not rate:
            raise ValueError(
                f"No exchange rate found for {currency} to {BASE_CURRENCY} "
                f"on or before {transaction_date}"
            )
        
        # Convert to base currency
        converted_amount = amount * rate
        logger.info(
            f"Converted {amount} {currency} to {converted_amount} {BASE_CURRENCY} "
            f"using rate {rate} for date {transaction_date}"
        )
        
        return converted_amount
    
    async def convert_currency(
        self, 
        amount: Decimal, 
        from_currency: str, 
        to_currency: str, 
        transaction_date: date
    ) -> Decimal:
        """
        Convert amount from one currency to another using exchange rates
        valid for the transaction date.
        
        Args:
            amount: The amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            transaction_date: Date of the transaction
            
        Returns:
            Amount converted to target currency
        """
        if not amount or amount <= 0:
            return Decimal('0')
        
        # If same currency, return as-is
        if from_currency == to_currency:
            return amount
        
        # Convert via base currency for consistency
        base_amount = await self.convert_to_base(amount, from_currency, transaction_date)
        
        # If target is base currency, we're done
        if to_currency == BASE_CURRENCY:
            return base_amount
        
        # Convert from base to target currency
        rate = await self._get_exchange_rate(BASE_CURRENCY, to_currency, transaction_date)
        
        if not rate:
            raise ValueError(
                f"No exchange rate found for {BASE_CURRENCY} to {to_currency} "
                f"on or before {transaction_date}"
            )
        
        # Convert from base to target (inverse rate)
        converted_amount = base_amount / rate
        
        logger.info(
            f"Converted {amount} {from_currency} to {converted_amount} {to_currency} "
            f"via {BASE_CURRENCY} for date {transaction_date}"
        )
        
        return converted_amount
    
    async def _get_exchange_rate(
        self, 
        from_currency: str, 
        to_currency: str, 
        transaction_date: date
    ) -> Optional[Decimal]:
        """
        Get exchange rate between two currencies for a specific date.
        Returns the closest available rate on or before the transaction date.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            transaction_date: Date for which rate is needed
            
        Returns:
            Exchange rate as Decimal, or None if not found
        """
        # Query for the most recent rate on or before the transaction date
        stmt = (
            select(ExchangeRate.rate)
            .where(
                and_(
                    ExchangeRate.from_currency == from_currency,
                    ExchangeRate.to_currency == to_currency,
                    ExchangeRate.date <= transaction_date,
                    ExchangeRate.is_active == True
                )
            )
            .order_by(desc(ExchangeRate.date))
            .limit(1)
        )
        
        result = await self.db.execute(stmt)
        rate = result.scalar_one_or_none()
        
        if rate:
            logger.debug(
                f"Found exchange rate {rate} for {from_currency} to {to_currency} "
                f"on or before {transaction_date}"
            )
        
        return rate
    
    async def get_available_currencies(self) -> list[str]:
        """
        Get list of all currencies that have exchange rates.
        
        Returns:
            List of currency codes
        """
        stmt = (
            select(ExchangeRate.from_currency, ExchangeRate.to_currency)
            .where(ExchangeRate.is_active == True)
            .distinct()
        )
        
        result = await self.db.execute(stmt)
        currencies = set()
        
        for row in result:
            currencies.add(row.from_currency)
            currencies.add(row.to_currency)
        
        # Always include base currency
        currencies.add(BASE_CURRENCY)
        
        return sorted(list(currencies))
    
    async def get_rate_history(
        self, 
        from_currency: str, 
        to_currency: str, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[dict]:
        """
        Get historical exchange rates between two currencies.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of rate records with date and rate
        """
        stmt = (
            select(ExchangeRate.date, ExchangeRate.rate)
            .where(
                and_(
                    ExchangeRate.from_currency == from_currency,
                    ExchangeRate.to_currency == to_currency,
                    ExchangeRate.is_active == True
                )
            )
        )
        
        if start_date:
            stmt = stmt.where(ExchangeRate.date >= start_date)
        
        if end_date:
            stmt = stmt.where(ExchangeRate.date <= end_date)
        
        stmt = stmt.order_by(ExchangeRate.date)
        
        result = await self.db.execute(stmt)
        
        return [
            {"date": row.date, "rate": row.rate}
            for row in result
        ]


# Convenience functions for direct usage
async def convert_to_base_currency(
    db: AsyncSession, 
    amount: Decimal, 
    currency: str, 
    transaction_date: date
) -> Decimal:
    """
    Convenience function to convert amount to base currency.
    
    Args:
        db: Database session
        amount: Amount to convert
        currency: Source currency
        transaction_date: Transaction date
        
    Returns:
        Amount in base currency (IRR)
    """
    service = CurrencyConversionService(db)
    return await service.convert_to_base(amount, currency, transaction_date)


async def convert_currency_amount(
    db: AsyncSession, 
    amount: Decimal, 
    from_currency: str, 
    to_currency: str, 
    transaction_date: date
) -> Decimal:
    """
    Convenience function to convert between any two currencies.
    
    Args:
        db: Database session
        amount: Amount to convert
        from_currency: Source currency
        to_currency: Target currency
        transaction_date: Transaction date
        
    Returns:
        Amount in target currency
    """
    service = CurrencyConversionService(db)
    return await service.convert_currency(amount, from_currency, to_currency, transaction_date)
