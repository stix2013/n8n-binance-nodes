"""Binance API routes."""

from fastapi import APIRouter, HTTPException, Query, Depends
import httpx
import os
from typing import Optional
from datetime import datetime
import logging

# Import utilities with fallback for both relative and absolute imports
try:
    from ..utils.date_utils import convert_date_format, timestamp_to_iso
except ImportError:
    from utils.date_utils import convert_date_format, timestamp_to_iso

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/binance", tags=["binance"])


async def get_binance_api_key() -> str:
    """Dependency to get Binance API key from environment."""
    api_key = os.getenv("BINANCE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, detail="BINANCE_API_KEY not found in environment variables"
        )
    return api_key


@router.get("/price")
async def get_binance_price(
    symbol: str = Query(..., description="Trading pair symbol (e.g., BTCUSDT)"),
    interval: str = Query(
        "1h",
        description="Kline interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)",
    ),
    limit: int = Query(50, ge=1, le=1000, description="Number of records to return"),
    startdate: Optional[str] = Query(None, description="Start date in YYYYMMDD format"),
    enddate: Optional[str] = Query(None, description="End date in YYYYMMDD format"),
    api_key: str = Depends(get_binance_api_key),
):
    """
    Get historical price data from Binance API

    - **symbol**: Trading pair symbol (required) - e.g., BTCUSDT, ETHUSDT
    - **interval**: Kline interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
    - **limit**: Number of records to return (1-1000, default: 50)
    - **startdate**: Start date in YYYYMMDD format (optional)
    - **enddate**: End date in YYYYMMDD format (optional)
    """

    # Build Binance API URL
    url = "https://api.binance.com/api/v3/klines"

    # Prepare query parameters
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}

    # Add date range if provided
    try:
        if startdate:
            start_timestamp = convert_date_format(startdate)
            params["startTime"] = start_timestamp

        if enddate:
            end_timestamp = convert_date_format(enddate)
            params["endTime"] = end_timestamp
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Prepare headers
    headers = {"X-MBX-APIKEY": api_key}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, params=params, headers=headers, timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()

                # Transform the response to a more user-friendly format
                transformed_data = []
                for kline in data:
                    transformed_data.append(
                        {
                            "open_time": timestamp_to_iso(kline[0]),
                            "open_price": float(kline[1]),
                            "high_price": float(kline[2]),
                            "low_price": float(kline[3]),
                            "close_price": float(kline[4]),
                            "volume": float(kline[5]),
                            "close_time": timestamp_to_iso(kline[6]),
                            "quote_asset_volume": float(kline[7]),
                            "number_of_trades": int(kline[8]),
                            "taker_buy_base_asset_volume": float(kline[9]),
                            "taker_buy_quote_asset_volume": float(kline[10]),
                            "ignore": kline[11],
                        }
                    )

                return {
                    "symbol": symbol.upper(),
                    "data": transformed_data,
                    "count": len(transformed_data),
                }
            else:
                error_detail = f"Binance API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_detail += f" - {error_data.get('msg', 'Unknown error')}"
                except:
                    error_detail += f" - {response.text}"

                raise HTTPException(
                    status_code=response.status_code, detail=error_detail
                )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=408,
            detail="Request timeout - Binance API took too long to respond",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503, detail=f"Failed to connect to Binance API: {str(e)}"
        )
    except HTTPException:
        # Re-raise HTTPException instances without logging them as errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
