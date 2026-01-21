"""Shared Binance API utilities for fetching and transforming data."""

import logging
from typing import Optional

import httpx
from fastapi import HTTPException, status

try:
    from ..models.settings import settings
except ImportError:
    from models.settings import settings

logger = logging.getLogger(__name__)

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
        headers={"User-Agent": f"n8n-binance-api/{settings.api_version}"},
    )


async def fetch_binance_data(
    client: httpx.AsyncClient,
    symbol: str,
    interval: str,
    limit: int,
    start_timestamp: Optional[int] = None,
    end_timestamp: Optional[int] = None,
) -> list:
    """Fetch kline data from Binance API."""
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit,
    }

    if start_timestamp:
        params["startTime"] = start_timestamp
    if end_timestamp:
        params["endTime"] = end_timestamp

    headers = {"X-MBX-APIKEY": settings.binance_api_key or ""}

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
    """Transform Binance kline data to standardized format."""
    transformed = []
    for kline in klines:
        transformed.append(
            {
                "open_time": kline[0],
                "open_price": float(kline[1]),
                "high_price": float(kline[2]),
                "low_price": float(kline[3]),
                "close_price": float(kline[4]),
                "volume": float(kline[5]),
                "close_time": kline[6],
                "quote_asset_volume": float(kline[7]),
                "number_of_trades": int(kline[8]),
                "taker_buy_base_asset_volume": float(kline[9]),
                "taker_buy_quote_asset_volume": float(kline[10]),
                "ignore": kline[11],
            }
        )
    return transformed


def extract_closing_prices(klines: list) -> list[float]:
    """Extract closing prices from kline data for technical analysis."""
    return [float(kline[4]) for kline in klines]
