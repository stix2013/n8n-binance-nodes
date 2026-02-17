"""Unified Binance API client for Spot, USD-M Futures, and Coin-M Futures."""

import os
import hmac
import hashlib
import time
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
import httpx
from .exceptions import (
    BinanceAPIError,
    BinanceAuthError,
    BinanceRateLimitError,
    BinanceValidationError,
    BinanceOrderError,
    BinanceServerError,
)


class BinanceClient:
    """Unified client for Binance Spot and Futures APIs."""

    # Base URLs
    SPOT_BASE_URL = "https://api.binance.com"
    USD_M_FUTURES_BASE_URL = "https://fapi.binance.com"
    COIN_M_FUTURES_BASE_URL = "https://dapi.binance.com"

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 10  # seconds

    def __init__(self, api_key: str = None, api_secret: str = None):
        """Initialize client with API credentials."""
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")

        if not self.api_key or not self.api_secret:
            raise BinanceAuthError("API key and secret are required")

        # Create async HTTP client
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature."""
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _get_base_url(self, market_type: str) -> str:
        """Get base URL based on market type."""
        market_type = market_type.lower()
        if market_type == "spot":
            return self.SPOT_BASE_URL
        elif market_type in ["usd_m", "usdm", "usd-m"]:
            return self.USD_M_FUTURES_BASE_URL
        elif market_type in ["coin_m", "coinm", "coin-m"]:
            return self.COIN_M_FUTURES_BASE_URL
        else:
            raise BinanceValidationError(f"Invalid market type: {market_type}")

    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Get request headers."""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        if include_auth and self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key
        return headers

    def _handle_error(self, response: httpx.Response, context: str = ""):
        """Handle API error responses."""
        try:
            error_data = response.json()
            error_msg = error_data.get("msg", "Unknown error")
            error_code = error_data.get("code", 0)
        except:
            error_msg = response.text or "Unknown error"
            error_code = 0

        full_message = f"{context}: {error_msg}" if context else error_msg

        if response.status_code == 401:
            raise BinanceAuthError(full_message, error_data)
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise BinanceRateLimitError(full_message, retry_after)
        elif response.status_code == 400:
            # Check if it's an order-related error
            if any(
                keyword in error_msg.lower()
                for keyword in ["order", "balance", "margin", "position"]
            ):
                raise BinanceOrderError(full_message, error_data)
            raise BinanceValidationError(full_message, error_data)
        elif response.status_code >= 500:
            raise BinanceServerError(full_message, error_data)
        else:
            raise BinanceAPIError(full_message, response.status_code, error_data)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        market_type: str = "spot",
        params: Dict[str, Any] = None,
        signed: bool = True,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        base_url = self._get_base_url(market_type)
        url = f"{base_url}{endpoint}"

        # Prepare parameters
        params = params or {}

        # Add timestamp for signed requests
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            query_string = urlencode(params)
            params["signature"] = self._generate_signature(query_string)

        headers = self._get_headers(include_auth=signed)

        try:
            if method.upper() == "GET":
                response = await self.client.get(url, params=params, headers=headers)
            elif method.upper() == "POST":
                response = await self.client.post(url, data=params, headers=headers)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, params=params, headers=headers)
            else:
                raise BinanceValidationError(f"Unsupported HTTP method: {method}")

            # Check for errors
            if response.status_code >= 400:
                self._handle_error(response, f"{method} {endpoint}")

            return response.json()

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            # Network errors - retry
            if retry_count < self.MAX_RETRIES:
                print(
                    f"Request failed (attempt {retry_count + 1}/{self.MAX_RETRIES}), retrying in {self.RETRY_DELAY}s..."
                )
                await self._sleep(self.RETRY_DELAY)
                return await self._make_request(
                    method, endpoint, market_type, params, signed, retry_count + 1
                )
            raise BinanceAPIError(
                f"Request failed after {self.MAX_RETRIES} retries: {str(e)}"
            )

        except BinanceServerError:
            # Server errors - retry
            if retry_count < self.MAX_RETRIES:
                print(
                    f"Server error (attempt {retry_count + 1}/{self.MAX_RETRIES}), retrying in {self.RETRY_DELAY}s..."
                )
                await self._sleep(self.RETRY_DELAY)
                return await self._make_request(
                    method, endpoint, market_type, params, signed, retry_count + 1
                )
            raise

        except BinanceRateLimitError:
            # Rate limit - retry with backoff
            if retry_count < self.MAX_RETRIES:
                delay = self.RETRY_DELAY * (retry_count + 1)
                print(
                    f"Rate limited (attempt {retry_count + 1}/{self.MAX_RETRIES}), retrying in {delay}s..."
                )
                await self._sleep(delay)
                return await self._make_request(
                    method, endpoint, market_type, params, signed, retry_count + 1
                )
            raise

    async def _sleep(self, seconds: float):
        """Async sleep helper."""
        import asyncio

        await asyncio.sleep(seconds)

    # ==================== SPOT API METHODS ====================

    async def get_spot_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: int = None,
        end_time: int = None,
    ) -> List[List]:
        """Get spot candlestick data."""
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit,
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        return await self._make_request(
            "GET", "/api/v3/klines", market_type="spot", params=params, signed=False
        )

    async def place_spot_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """Place spot order."""
        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": quantity,
        }

        if order_type.upper() != "MARKET":
            params["timeInForce"] = time_in_force

        if price is not None:
            params["price"] = price

        return await self._make_request(
            "POST", "/api/v3/order", market_type="spot", params=params, signed=True
        )

    # ==================== USD-M FUTURES API METHODS ====================

    async def get_usdm_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: int = None,
        end_time: int = None,
    ) -> List[List]:
        """Get USD-M futures candlestick data."""
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit,
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        return await self._make_request(
            "GET", "/fapi/v1/klines", market_type="usd_m", params=params, signed=False
        )

    async def get_usdm_mark_price_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: int = None,
        end_time: int = None,
    ) -> List[List]:
        """Get USD-M futures mark price klines."""
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit,
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        return await self._make_request(
            "GET",
            "/fapi/v1/markPriceKlines",
            market_type="usd_m",
            params=params,
            signed=False,
        )

    async def get_usdm_mark_price(self, symbol: str = None) -> Dict[str, Any]:
        """Get USD-M futures mark price."""
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()

        return await self._make_request(
            "GET",
            "/fapi/v1/premiumIndex",
            market_type="usd_m",
            params=params,
            signed=False,
        )

    async def get_usdm_open_interest(self, symbol: str) -> Dict[str, Any]:
        """Get USD-M futures open interest."""
        params = {"symbol": symbol.upper()}

        return await self._make_request(
            "GET",
            "/fapi/v1/openInterest",
            market_type="usd_m",
            params=params,
            signed=False,
        )

    async def get_usdm_open_interest_hist(
        self,
        symbol: str,
        period: str = "1h",
        limit: int = 500,
        start_time: int = None,
        end_time: int = None,
    ) -> List[Dict[str, Any]]:
        """Get USD-M futures open interest history."""
        params = {
            "symbol": symbol.upper(),
            "period": period,
            "limit": limit,
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        return await self._make_request(
            "GET",
            "/futures/data/openInterestHist",
            market_type="usd_m",
            params=params,
            signed=False,
        )

    async def place_usdm_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None,
        stop_price: float = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
        close_position: bool = False,
        working_type: str = "CONTRACT_PRICE",
        price_protect: bool = False,
    ) -> Dict[str, Any]:
        """Place USD-M futures order."""
        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": quantity,
        }

        if order_type.upper() not in ["MARKET", "STOP_MARKET", "TAKE_PROFIT_MARKET"]:
            params["timeInForce"] = time_in_force

        if price is not None:
            params["price"] = price

        if stop_price is not None:
            params["stopPrice"] = stop_price

        if reduce_only:
            params["reduceOnly"] = "true"

        if close_position:
            params["closePosition"] = "true"

        params["workingType"] = working_type

        if price_protect:
            params["priceProtect"] = "true"

        return await self._make_request(
            "POST", "/fapi/v1/order", market_type="usd_m", params=params, signed=True
        )

    # ==================== COIN-M FUTURES API METHODS ====================

    async def get_coinm_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: int = None,
        end_time: int = None,
    ) -> List[List]:
        """Get Coin-M futures candlestick data."""
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit,
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        return await self._make_request(
            "GET", "/dapi/v1/klines", market_type="coin_m", params=params, signed=False
        )

    async def get_coinm_mark_price(self, symbol: str = None) -> Dict[str, Any]:
        """Get Coin-M futures mark price."""
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()

        return await self._make_request(
            "GET",
            "/dapi/v1/premiumIndex",
            market_type="coin_m",
            params=params,
            signed=False,
        )

    async def get_coinm_open_interest(self, symbol: str) -> Dict[str, Any]:
        """Get Coin-M futures open interest."""
        params = {"symbol": symbol.upper()}

        return await self._make_request(
            "GET",
            "/dapi/v1/openInterest",
            market_type="coin_m",
            params=params,
            signed=False,
        )

    async def place_coinm_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None,
        stop_price: float = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        """Place Coin-M futures order."""
        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": quantity,
        }

        if order_type.upper() not in ["MARKET", "STOP_MARKET", "TAKE_PROFIT_MARKET"]:
            params["timeInForce"] = time_in_force

        if price is not None:
            params["price"] = price

        if stop_price is not None:
            params["stopPrice"] = stop_price

        if reduce_only:
            params["reduceOnly"] = "true"

        return await self._make_request(
            "POST", "/dapi/v1/order", market_type="coin_m", params=params, signed=True
        )

    # ==================== UNIFIED METHODS ====================

    async def get_klines(
        self,
        symbol: str,
        market_type: str,
        interval: str,
        limit: int = 500,
        start_time: int = None,
        end_time: int = None,
    ) -> List[List]:
        """Get klines for any market type (unified method)."""
        market_type = market_type.lower()

        if market_type == "spot":
            return await self.get_spot_klines(
                symbol, interval, limit, start_time, end_time
            )
        elif market_type in ["usd_m", "usdm", "usd-m"]:
            return await self.get_usdm_klines(
                symbol, interval, limit, start_time, end_time
            )
        elif market_type in ["coin_m", "coinm", "coin-m"]:
            return await self.get_coinm_klines(
                symbol, interval, limit, start_time, end_time
            )
        else:
            raise BinanceValidationError(f"Invalid market type: {market_type}")

    async def place_order(
        self,
        symbol: str,
        market_type: str,
        side: str,
        order_type: str,
        quantity: float,
        **kwargs,
    ) -> Dict[str, Any]:
        """Place order for any market type (unified method)."""
        market_type = market_type.lower()

        if market_type == "spot":
            return await self.place_spot_order(
                symbol,
                side,
                order_type,
                quantity,
                price=kwargs.get("price"),
                time_in_force=kwargs.get("time_in_force", "GTC"),
            )
        elif market_type in ["usd_m", "usdm", "usd-m"]:
            return await self.place_usdm_order(
                symbol,
                side,
                order_type,
                quantity,
                price=kwargs.get("price"),
                stop_price=kwargs.get("stop_price"),
                time_in_force=kwargs.get("time_in_force", "GTC"),
                reduce_only=kwargs.get("reduce_only", False),
                close_position=kwargs.get("close_position", False),
                working_type=kwargs.get("working_type", "CONTRACT_PRICE"),
                price_protect=kwargs.get("price_protect", False),
            )
        elif market_type in ["coin_m", "coinm", "coin-m"]:
            return await self.place_coinm_order(
                symbol,
                side,
                order_type,
                quantity,
                price=kwargs.get("price"),
                stop_price=kwargs.get("stop_price"),
                time_in_force=kwargs.get("time_in_force", "GTC"),
                reduce_only=kwargs.get("reduce_only", False),
            )
        else:
            raise BinanceValidationError(f"Invalid market type: {market_type}")
