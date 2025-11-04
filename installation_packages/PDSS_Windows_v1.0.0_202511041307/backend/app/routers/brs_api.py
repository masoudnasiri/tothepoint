"""
BrsApi Currency Conversion Endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from decimal import Decimal
import logging

# Lazy import to avoid memory issues during startup
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/brs-api", tags=["BrsApi Currency"])

def _get_brs_client():
    """Lazy import of brs_api_client to avoid memory issues during module import"""
    from app.services.brs_api_client import brs_api_client, CurrencyRate
    return brs_api_client, CurrencyRate

@router.get("/currencies", response_model=List[dict])
async def get_brs_currencies():
    """Get all available currencies from BrsApi"""
    try:
        brs_api_client, CurrencyRate = _get_brs_client()
        rates = await brs_api_client.get_currency_rates()
        return [
            {
                "symbol": rate.symbol,
                "name": rate.name_en,
                "price": rate.price,
                "change_percent": rate.change_percent,
                "timestamp": rate.timestamp.isoformat()
            }
            for rate in rates
        ]
    except Exception as e:
        logger.error(f"Failed to fetch currencies from BrsApi: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch currencies: {str(e)}")

@router.get("/currencies/{symbol}", response_model=dict)
async def get_brs_currency_rate(symbol: str):
    """Get rate for a specific currency from BrsApi"""
    try:
        brs_api_client, CurrencyRate = _get_brs_client()
        rate = await brs_api_client.get_currency_rate(symbol)
        if not rate:
            raise HTTPException(status_code=404, detail=f"Currency {symbol} not found")
        
        return {
            "symbol": rate.symbol,
            "name": rate.name_en,
            "price": rate.price,
            "change_percent": rate.change_percent,
            "timestamp": rate.timestamp.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch currency rate for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch currency rate: {str(e)}")

@router.post("/convert", response_model=dict)
async def convert_with_brs_api(
    amount: float = Query(..., gt=0, description="Amount to convert"),
    from_currency: str = Query(..., description="Source currency symbol (e.g., USD)"),
    to_currency: str = Query(..., description="Target currency symbol (e.g., EUR)"),
    force_refresh: bool = Query(False, description="Force refresh of currency rates")
):
    """Convert amount between currencies using BrsApi rates"""
    try:
        brs_api_client, CurrencyRate = _get_brs_client()
        if force_refresh:
            await brs_api_client.get_currency_rates(force_refresh=True)
        
        result = await brs_api_client.convert_currency(amount, from_currency, to_currency)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Currency conversion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

@router.get("/supported-currencies", response_model=List[str])
async def get_supported_currencies():
    """Get list of supported currency symbols from BrsApi"""
    try:
        brs_api_client, CurrencyRate = _get_brs_client()
        currencies = await brs_api_client.get_supported_currencies()
        return currencies
    except Exception as e:
        logger.error(f"Failed to fetch supported currencies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch supported currencies: {str(e)}")

@router.get("/health", response_model=dict)
async def brs_api_health_check():
    """Health check for BrsApi connectivity"""
    try:
        brs_api_client, CurrencyRate = _get_brs_client()
        rates = await brs_api_client.get_currency_rates()
        return {
            "status": "healthy",
            "currencies_count": len(rates),
            "last_update": brs_api_client._cache_timestamp.isoformat() if brs_api_client._cache_timestamp else None,
            "source": "BrsApi"
        }
    except Exception as e:
        logger.error(f"BrsApi health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "source": "BrsApi"
        }
