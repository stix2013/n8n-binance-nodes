"""Trading routes for spot and futures operations."""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
import logging

# Import utilities with fallback for both relative and absolute imports
try:
    from ..models.trading_models import (
        SpotOrderRequest,
        FuturesOrderRequest,
        OrderResponse,
        SpotOrder,
        FuturesOrder,
        CandlestickResponse,
        MarkPriceResponse,
        OpenInterestResponse,
        SyncStatusResponse,
        IntervalEnum,
        MarketTypeEnum,
    )
    from ..services.trading_service import trading_service
    from ..services.candlestick_sync import candlestick_sync
    from ..utils.exceptions import BinanceAPIError, DatabaseError
except ImportError:
    from models.trading_models import (
        SpotOrderRequest,
        FuturesOrderRequest,
        OrderResponse,
        SpotOrder,
        FuturesOrder,
        CandlestickResponse,
        MarkPriceResponse,
        OpenInterestResponse,
        SyncStatusResponse,
        IntervalEnum,
        MarketTypeEnum,
    )
    from services.trading_service import trading_service
    from services.candlestick_sync import candlestick_sync
    from utils.exceptions import BinanceAPIError, DatabaseError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/binance", tags=["trading"])


# ==================== SPOT TRADING ENDPOINTS ====================


@router.post(
    "/spot/order",
    response_model=OrderResponse,
    summary="Place spot order",
    description="Place a spot order on Binance and persist to database with current status",
)
async def place_spot_order(order_request: SpotOrderRequest):
    """
    Place a spot order on Binance.

    The order will be placed on Binance, current status will be queried,
    and the order will be persisted to the database (max 3 per symbol).
    """
    try:
        response = await trading_service.place_spot_order(order_request)

        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)

        return response

    except BinanceAPIError as e:
        logger.error(f"Binance API error in place_spot_order: {e}")
        raise HTTPException(status_code=e.status_code or 400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in place_spot_order: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/spot/orders",
    response_model=List[SpotOrder],
    summary="Get recent spot orders",
    description="Get recent spot orders from database (max 3 per symbol)",
)
async def get_recent_spot_orders(
    symbol: Optional[str] = Query(None, description="Filter by symbol (e.g., BTCUSDT)"),
    limit: int = Query(3, ge=1, le=10, description="Maximum orders per symbol"),
):
    """
    Get recent spot orders from the database.

    Returns the most recent orders (max 3 per symbol by default).
    Orders are auto-pruned to keep only the 3 most recent per symbol.
    """
    try:
        orders = await trading_service.get_recent_spot_orders(
            symbol=symbol, limit=limit
        )
        return orders

    except DatabaseError as e:
        logger.error(f"Database error in get_recent_spot_orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_recent_spot_orders: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ==================== FUTURES TRADING ENDPOINTS ====================


@router.post(
    "/futures/order",
    response_model=OrderResponse,
    summary="Place futures order",
    description="Place a USD-M or Coin-M futures order on Binance and persist to database with current status",
)
async def place_futures_order(order_request: FuturesOrderRequest):
    """
    Place a futures order on Binance (USD-M or Coin-M).

    The order will be placed on Binance, current status will be queried,
    and the order will be persisted to the database (max 3 per symbol per market type).
    """
    try:
        response = await trading_service.place_futures_order(order_request)

        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)

        return response

    except BinanceAPIError as e:
        logger.error(f"Binance API error in place_futures_order: {e}")
        raise HTTPException(status_code=e.status_code or 400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in place_futures_order: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/futures/orders",
    response_model=List[FuturesOrder],
    summary="Get recent futures orders",
    description="Get recent futures orders from database (max 3 per symbol)",
)
async def get_recent_futures_orders(
    symbol: Optional[str] = Query(None, description="Filter by symbol (e.g., BTCUSDT)"),
    market_type: Optional[str] = Query(
        None, description="Filter by market type (usd_m or coin_m)"
    ),
    limit: int = Query(3, ge=1, le=10, description="Maximum orders per symbol"),
):
    """
    Get recent futures orders from the database.

    Returns the most recent orders (max 3 per symbol by default).
    Orders are auto-pruned to keep only the 3 most recent per symbol per market type.
    """
    try:
        orders = await trading_service.get_recent_futures_orders(
            symbol=symbol, market_type=market_type, limit=limit
        )
        return orders

    except DatabaseError as e:
        logger.error(f"Database error in get_recent_futures_orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_recent_futures_orders: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/futures/klines",
    response_model=CandlestickResponse,
    summary="Get futures klines",
    description="Get cached futures candlestick data from database",
)
async def get_futures_klines(
    symbol: str = Query(..., description="Trading pair symbol (e.g., BTCUSDT)"),
    market_type: str = Query(..., description="Market type (usd_m or coin_m)"),
    interval: IntervalEnum = Query(
        default=IntervalEnum.ONE_HOUR, description="Kline interval"
    ),
    limit: int = Query(default=100, ge=1, le=1000, description="Number of candles"),
):
    """
    Get cached futures kline data.

    Returns candlestick data from the database cache.
    If data is not cached, it will be fetched from Binance.
    """
    try:
        candles = await candlestick_sync.get_cached_candles(
            symbol=symbol, market_type=market_type, interval=interval.value, limit=limit
        )

        return CandlestickResponse(
            success=True,
            symbol=symbol.upper(),
            market_type=market_type.lower(),
            interval=interval.value,
            data=candles,
            count=len(candles),
        )

    except Exception as e:
        logger.error(f"Error fetching futures klines: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch klines: {str(e)}")


@router.get(
    "/futures/markPrice",
    response_model=MarkPriceResponse,
    summary="Get mark price",
    description="Get current mark price for a futures symbol",
)
async def get_mark_price(
    symbol: str = Query(..., description="Trading pair symbol (e.g., BTCUSDT)"),
    market_type: str = Query(..., description="Market type (usd_m or coin_m)"),
):
    """
    Get current mark price for a futures symbol.

    Mark price is used for liquidation and margin calculations.
    """
    try:
        from ..utils.binance_client import BinanceClient

        client = BinanceClient()

        if market_type.lower() in ["usd_m", "usdm", "usd-m"]:
            data = await client.get_usdm_mark_price(symbol)
        elif market_type.lower() in ["coin_m", "coinm", "coin-m"]:
            data = await client.get_coinm_mark_price(symbol)
        else:
            raise HTTPException(
                status_code=400, detail=f"Invalid market type: {market_type}"
            )

        await client.close()

        return MarkPriceResponse(
            success=True,
            symbol=symbol.upper(),
            market_type=market_type.lower(),
            mark_price=float(data.get("markPrice", 0)),
            index_price=float(data.get("indexPrice"))
            if data.get("indexPrice")
            else None,
            estimated_settle_price=float(data.get("estimatedSettlePrice"))
            if data.get("estimatedSettlePrice")
            else None,
            last_funding_rate=float(data.get("lastFundingRate"))
            if data.get("lastFundingRate")
            else None,
            next_funding_time=datetime.fromtimestamp(
                data.get("nextFundingTime", 0) / 1000
            )
            if data.get("nextFundingTime")
            else None,
            time=datetime.fromtimestamp(data.get("time", 0) / 1000)
            if data.get("time")
            else None,
        )

    except BinanceAPIError as e:
        logger.error(f"Binance API error in get_mark_price: {e}")
        raise HTTPException(status_code=e.status_code or 400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_mark_price: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/futures/openInterest",
    response_model=OpenInterestResponse,
    summary="Get open interest",
    description="Get current open interest for a futures symbol",
)
async def get_open_interest(
    symbol: str = Query(..., description="Trading pair symbol (e.g., BTCUSDT)"),
    market_type: str = Query(..., description="Market type (usd_m or coin_m)"),
):
    """
    Get current open interest for a futures symbol.

    Open interest represents the total number of outstanding derivative contracts.
    """
    try:
        try:
            from ..utils.binance_client import BinanceClient
        except ImportError:
            from utils.binance_client import BinanceClient

        client = BinanceClient()

        if market_type.lower() in ["usd_m", "usdm", "usd-m"]:
            data = await client.get_usdm_open_interest(symbol)
        elif market_type.lower() in ["coin_m", "coinm", "coin-m"]:
            data = await client.get_coinm_open_interest(symbol)
        else:
            await client.close()
            raise HTTPException(
                status_code=400, detail=f"Invalid market type: {market_type}"
            )

        await client.close()

        return OpenInterestResponse(
            success=True,
            symbol=symbol.upper(),
            market_type=market_type.lower(),
            open_interest=float(data.get("openInterest", 0)),
            time=datetime.fromtimestamp(data.get("time", 0) / 1000)
            if data.get("time")
            else None,
        )

    except BinanceAPIError as e:
        logger.error(f"Binance API error in get_open_interest: {e}")
        raise HTTPException(status_code=e.status_code or 400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_open_interest: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/futures/openInterestHist",
    summary="Get open interest history",
    description="Get historical open interest data for a futures symbol",
)
async def get_open_interest_history(
    symbol: str = Query(..., description="Trading pair symbol (e.g., BTCUSDT)"),
    market_type: str = Query(..., description="Market type (usd_m only for now)"),
    period: str = Query(
        default="1h", description="Time period (5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d)"
    ),
    limit: int = Query(default=100, ge=1, le=500, description="Number of records"),
):
    """
    Get historical open interest data.

    Only USD-M futures supports historical open interest data via API.
    """
    try:
        try:
            from ..utils.binance_client import BinanceClient
        except ImportError:
            from utils.binance_client import BinanceClient

        client = BinanceClient()

        if market_type.lower() not in ["usd_m", "usdm", "usd-m"]:
            await client.close()
            raise HTTPException(
                status_code=400, detail="Historical OI only available for USD-M futures"
            )

        data = await client.get_usdm_open_interest_hist(
            symbol=symbol, period=period, limit=limit
        )

        await client.close()

        # Transform data
        history = []
        for item in data:
            history.append(
                {
                    "symbol": item.get("symbol"),
                    "sum_open_interest": float(item.get("sumOpenInterest", 0)),
                    "sum_open_interest_value": float(
                        item.get("sumOpenInterestValue", 0)
                    ),
                    "timestamp": datetime.fromtimestamp(
                        item.get("timestamp", 0) / 1000
                    ).isoformat()
                    if item.get("timestamp")
                    else None,
                }
            )

        return {
            "success": True,
            "symbol": symbol.upper(),
            "market_type": market_type.lower(),
            "period": period,
            "data": history,
            "count": len(history),
        }

    except BinanceAPIError as e:
        logger.error(f"Binance API error in get_open_interest_history: {e}")
        raise HTTPException(status_code=e.status_code or 400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_open_interest_history: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ==================== ADMIN/SYNC ENDPOINTS ====================


@router.post(
    "/admin/sync/now",
    summary="Trigger immediate candlestick sync",
    description="Manually trigger candlestick sync for all configured symbols",
)
async def trigger_sync_now():
    """
    Trigger an immediate candlestick synchronization.

    This will fetch the latest candlestick data for all configured
    symbols, intervals, and market types.
    """
    try:
        # Run sync in background to not block the response
        asyncio.create_task(candlestick_sync.trigger_sync_now())

        return {
            "success": True,
            "message": "Sync triggered successfully",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger sync: {str(e)}")


@router.get(
    "/admin/sync/status",
    response_model=SyncStatusResponse,
    summary="Get sync status",
    description="Get current candlestick sync service status",
)
async def get_sync_status():
    """
    Get the current status of the candlestick sync service.

    Returns information about last sync, next sync, configured symbols,
    intervals, and market types.
    """
    try:
        status = candlestick_sync.get_status()
        return SyncStatusResponse(
            success=True,
            is_running=status["is_running"],
            last_sync=datetime.fromisoformat(status["last_sync"])
            if status["last_sync"]
            else None,
            next_sync=datetime.fromisoformat(status["next_sync"])
            if status["next_sync"]
            else None,
            symbols=status["symbols"],
            intervals=status["intervals"],
            market_types=status["market_types"],
            message="Sync service status retrieved successfully",
        )

    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get sync status: {str(e)}"
        )


# Import asyncio for background tasks
import asyncio
