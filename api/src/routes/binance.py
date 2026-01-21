"""Binance API routes with best practices."""

import logging
from datetime import datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

try:
    from ..utils.date_utils import convert_date_format, timestamp_to_iso
    from ..models.api_models import (
        PriceResponse,
        ErrorResponse,
        IntervalEnum,
    )
    from ..models.settings import settings
except ImportError:
    from utils.date_utils import convert_date_format, timestamp_to_iso
    from models.api_models import PriceResponse, ErrorResponse, IntervalEnum
    from models.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/binance", tags=["Price Data"])

BINANCE_API_URL = f"{settings.binance_base_url}/api/v3/klines"


async def get_api_key() -> str:
    """Dependency to get Binance API key from environment."""
    api_key = settings.binance_api_key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="BINANCE_API_KEY not configured",
        )
    return api_key


async def get_http_client() -> httpx.AsyncClient:
    """Dependency to get HTTP client with proper configuration."""
    limits = httpx.Limits(
        max_keepalive_connections=settings.http_client_max_keepalive_connections,
        max_connections=settings.http_client_max_connections,
    )
    timeout = httpx.Timeout(settings.request_timeout)

    return httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        headers={"User-Agent": "n8n-binance-api/v1"},
    )
    timeout = httpx.Timeout(settings.request_timeout)

    return httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        headers={
            "User-Agent": f"n8n-binance-api/{settings.__fields__['api_host'].default}"
        },
    )


async def fetch_binance_data(
    client: httpx.AsyncClient,
    symbol: str,
    interval: IntervalEnum,
    limit: int,
    start_timestamp: int | None = None,
    end_timestamp: int | None = None,
) -> list:
    """Fetch kline data from Binance API."""
    params = {
        "symbol": symbol.upper(),
        "interval": interval.value,
        "limit": limit,
    }

    if start_timestamp:
        params["startTime"] = start_timestamp
    if end_timestamp:
        params["endTime"] = end_timestamp

    headers = {"X-MBX-APIKEY": settings.binance_api_key}

    try:
        response = await client.get(BINANCE_API_URL, params=params, headers=headers)

        if response.status_code == status.HTTP_200_OK:
            return response.json()

        error_detail = f"Binance API error: {response.status_code}"
        try:
            error_data = response.json()
            error_detail += f" - {error_data.get('msg', 'Unknown error')}"
        except Exception:
            error_detail += f" - {response.text}"

        raise HTTPException(
            status_code=response.status_code,
            detail=error_detail,
        )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Request timeout - Binance API took too long to respond",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Binance API: {str(e)}",
        )


def transform_kline_data(klines: list) -> list[dict]:
    """Transform Binance kline data to PriceDataPoint format."""
    transformed = []
    for kline in klines:
        transformed.append(
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
    return transformed


SymbolQuery = Annotated[
    str,
    Query(
        ...,
        min_length=1,
        max_length=20,
        description="Trading pair symbol (e.g., BTCUSDT)",
    ),
]

IntervalQuery = Annotated[
    IntervalEnum,
    Query(description="Kline interval"),
]

LimitQuery = Annotated[
    int,
    Query(ge=1, le=1000, description="Number of records to return"),
]

DateQuery = Annotated[
    str,
    Query(description="Date in YYYYMMDD format"),
]


@router.get(
    "/price",
    response_model=PriceResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
    summary="Get Price Data",
    description="Fetch historical kline/candlestick data from Binance API",
)
async def get_binance_price(
    symbol: SymbolQuery,
    interval: IntervalQuery,
    api_key: Annotated[str, Depends(get_api_key)],
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
    startdate: DateQuery = None,
    enddate: DateQuery = None,
    limit: LimitQuery = 50,
) -> PriceResponse:
    """
    Get historical price data from Binance API.

    - **symbol**: Trading pair symbol (required) - e.g., BTCUSDT, ETHUSDT
    - **interval**: Kline interval (default: 1h)
    - **limit**: Number of records (default: 50, max: 1000)
    - **startdate**: Start date filter (optional, YYYYMMDD format)
    - **enddate**: End date filter (optional, YYYYMMDD format)
    """
    start_timestamp: int | None = None
    end_timestamp: int | None = None

    if startdate:
        try:
            start_timestamp = int(convert_date_format(startdate))
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    if enddate:
        try:
            end_timestamp = int(convert_date_format(enddate))
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    try:
        klines = await fetch_binance_data(
            client, symbol, interval, limit, start_timestamp, end_timestamp
        )

        transformed_data = transform_kline_data(klines)

        return PriceResponse(
            symbol=symbol.upper(),
            data=transformed_data,
            count=len(transformed_data),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in get_binance_price: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
