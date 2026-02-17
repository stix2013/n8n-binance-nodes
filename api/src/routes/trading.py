"""Trading routes for spot and futures operations."""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
import logging

from ..models.trading_models import (
    SpotOrderRequest,
    OrderResponse,
    SpotOrder,
    SyncStatusResponse,
)
from ..services.trading_service import trading_service
from ..services.candlestick_sync import candlestick_sync
from ..utils.exceptions import BinanceAPIError, DatabaseError

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
