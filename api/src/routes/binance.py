"""Binance API routes with best practices."""

import logging
from datetime import datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

try:
    from ..utils.date_utils import convert_date_format, timestamp_to_iso
    from ..utils.binance import (
        get_api_key as shared_get_api_key,
        get_http_client as shared_get_http_client,
        fetch_binance_data as shared_fetch_binance_data,
        transform_kline_data as shared_transform_kline_data,
    )
    from ..models.api_models import (
        PriceResponse,
        ErrorResponse,
        IntervalEnum,
    )
    from ..models.settings import settings
except ImportError:
    from utils.date_utils import convert_date_format, timestamp_to_iso
    from utils.binance import (
        get_api_key as shared_get_api_key,
        get_http_client as shared_get_http_client,
        fetch_binance_data as shared_fetch_binance_data,
        transform_kline_data as shared_transform_kline_data,
    )
    from models.api_models import (
        PriceResponse,
        ErrorResponse,
        IntervalEnum,
    )
    from models.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/binance", tags=["Price Data"])

get_api_key = shared_get_api_key
get_http_client = shared_get_http_client


async def fetch_binance_price_data(
    client: httpx.AsyncClient,
    symbol: str,
    interval: IntervalEnum,
    limit: int,
    start_timestamp: int | None = None,
    end_timestamp: int | None = None,
) -> list:
    """Fetch kline data from Binance API for price endpoint."""
    return await shared_fetch_binance_data(
        client, symbol, interval.value, limit, start_timestamp, end_timestamp
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
        klines = await fetch_binance_price_data(
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
