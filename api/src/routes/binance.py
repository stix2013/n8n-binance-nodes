"""Binance API routes."""

from fastapi import APIRouter, HTTPException, Depends, Query
import httpx
import os
import logging
from datetime import datetime

# Import utilities with fallback for both relative and absolute imports
try:
    from ..utils.date_utils import convert_date_format, timestamp_to_iso
    from ..models.api_models import PriceResponse, ErrorResponse, IntervalEnum
    from ..models.settings import settings
except ImportError:
    from utils.date_utils import convert_date_format, timestamp_to_iso
    from models.api_models import PriceResponse, ErrorResponse, IntervalEnum
    from models.settings import settings

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


@router.get(
    "/price",
    response_model=PriceResponse,
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def get_binance_price(
    symbol: str = Query(
        ...,
        min_length=1,
        max_length=20,
        description="Trading pair symbol (e.g., BTCUSDT)",
    ),
    interval: IntervalEnum = Query(
        default=IntervalEnum.ONE_HOUR, description="Kline interval"
    ),
    limit: int = Query(
        default=50, ge=1, le=1000, description="Number of records to return"
    ),
    startdate: str = Query(None, description="Start date in YYYYMMDD format"),
    enddate: str = Query(None, description="End date in YYYYMMDD format"),
    api_key: str = Depends(get_binance_api_key),
):
    """
    Get historical price data from Binance API
    """

    # Validate input parameters
    if not symbol.isalnum():
        raise HTTPException(
            status_code=422, detail="Symbol must contain only alphanumeric characters"
        )

    # Convert symbol to uppercase
    symbol = symbol.upper()

    # Validate date format if provided
    for date_field, date_value in [("startdate", startdate), ("enddate", enddate)]:
        if date_value:
            if len(date_value) != 8 or not date_value.isdigit():
                raise HTTPException(
                    status_code=422, detail=f"{date_field} must be in YYYYMMDD format"
                )
            try:
                datetime.strptime(date_value, "%Y%m%d")
            except ValueError:
                raise HTTPException(status_code=422, detail=f"Invalid {date_field}")

    # Build Binance API URL
    url = "https://api.binance.com/api/v3/klines"

    # Prepare query parameters
    params = {"symbol": symbol, "interval": interval.value, "limit": limit}

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

                return PriceResponse(
                    symbol=symbol,
                    data=transformed_data,
                    count=len(transformed_data),
                )
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
