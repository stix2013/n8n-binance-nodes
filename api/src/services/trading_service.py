"""Trading service for order management and database persistence."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

# Import with fallback for both relative and absolute imports
try:
    from ..models.trading_models import (
        SpotOrder,
        FuturesOrder,
        SpotOrderRequest,
        FuturesOrderRequest,
        OrderResponse,
        MarketTypeEnum,
        OrderStatusEnum,
    )
    from ..utils.binance_client import BinanceClient
    from ..utils.exceptions import BinanceAPIError, DatabaseError
    from .database import db
except ImportError:
    from models.trading_models import (
        SpotOrder,
        FuturesOrder,
        SpotOrderRequest,
        FuturesOrderRequest,
        OrderResponse,
        MarketTypeEnum,
        OrderStatusEnum,
    )
    from utils.binance_client import BinanceClient
    from utils.exceptions import BinanceAPIError, DatabaseError
    from services.database import db

logger = logging.getLogger(__name__)


class TradingService:
    """Service for handling trading operations with database persistence."""

    def __init__(self):
        self.client: Optional[BinanceClient] = None

    async def _get_client(self) -> BinanceClient:
        """Get or create Binance client."""
        if not self.client:
            self.client = BinanceClient()
        return self.client

    async def _get_order_status_from_binance(
        self, order_id: int, symbol: str, market_type: str
    ) -> Dict[str, Any]:
        """Query current order status from Binance."""
        try:
            client = await self._get_client()

            if market_type == "spot":
                endpoint = "/api/v3/order"
            elif market_type in ["usd_m", "usdm", "usd-m"]:
                endpoint = "/fapi/v1/order"
            elif market_type in ["coin_m", "coinm", "coin-m"]:
                endpoint = "/dapi/v1/order"
            else:
                logger.warning(f"Unknown market type for status query: {market_type}")
                return {}

            params = {"symbol": symbol.upper(), "orderId": order_id}

            return await client._make_request(
                "GET", endpoint, market_type=market_type, params=params, signed=True
            )
        except Exception as e:
            logger.error(f"Failed to get order status from Binance: {e}")
            return {}

    async def place_spot_order(self, order_request: SpotOrderRequest) -> OrderResponse:
        """Place spot order on Binance and persist to database with current status."""
        try:
            client = await self._get_client()

            # Step 1: Place order on Binance
            logger.info(
                f"Placing spot order: {order_request.side.value} {order_request.quantity} {order_request.symbol}"
            )

            binance_response = await client.place_spot_order(
                symbol=order_request.symbol,
                side=order_request.side.value,
                order_type=order_request.order_type.value,
                quantity=order_request.quantity,
                price=order_request.price,
                time_in_force=order_request.time_in_force,
            )

            order_id = binance_response.get("orderId")

            # Step 2: Query current status from Binance
            logger.debug(f"Querying current status for order {order_id}")
            status_response = await self._get_order_status_from_binance(
                order_id=order_id, symbol=order_request.symbol, market_type="spot"
            )

            # Use status response if available, otherwise use initial response
            current_data = status_response if status_response else binance_response

            # Step 3: Prepare order data for database
            order_data = {
                "order_id": order_id,
                "client_order_id": current_data.get("clientOrderId"),
                "symbol": order_request.symbol.upper(),
                "side": order_request.side.value,
                "order_type": order_request.order_type.value,
                "status": current_data.get("status", "NEW"),
                "price": float(current_data.get("price", 0)) or order_request.price,
                "quantity": float(current_data.get("origQty", order_request.quantity)),
                "executed_qty": float(current_data.get("executedQty", 0)),
                "time_in_force": current_data.get(
                    "timeInForce", order_request.time_in_force
                ),
                "binance_response": current_data,
            }

            # Step 4: Persist to database
            try:
                await self._persist_spot_order(order_data)
                logger.info(f"Spot order {order_id} persisted successfully")
            except Exception as db_error:
                # Log error but don't fail - order is already live on Binance
                logger.error(
                    f"CRITICAL: Binance order {order_id} placed successfully but DB insertion failed: {db_error}"
                )
                logger.error(f"Order details: {order_data}")

            # Step 5: Return response
            return OrderResponse(
                success=True,
                order_id=order_id,
                client_order_id=order_data["client_order_id"],
                symbol=order_data["symbol"],
                side=order_data["side"],
                order_type=order_data["order_type"],
                status=order_data["status"],
                price=order_data["price"],
                quantity=order_data["quantity"],
                executed_qty=order_data["executed_qty"],
                binance_response=current_data,
            )

        except BinanceAPIError as e:
            logger.error(f"Binance API error placing spot order: {e}")
            return OrderResponse(
                success=False,
                symbol=order_request.symbol,
                side=order_request.side.value,
                order_type=order_request.order_type.value,
                status="FAILED",
                quantity=order_request.quantity,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error placing spot order: {e}")
            return OrderResponse(
                success=False,
                symbol=order_request.symbol,
                side=order_request.side.value,
                order_type=order_request.order_type.value,
                status="FAILED",
                quantity=order_request.quantity,
                error=f"Internal error: {str(e)}",
            )

    async def _persist_spot_order(self, order_data: Dict[str, Any]) -> None:
        """Persist spot order to database."""
        query = """
            INSERT INTO spot_orders (
                order_id, client_order_id, symbol, side, order_type, status,
                price, quantity, executed_qty, time_in_force, binance_response
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (order_id) DO UPDATE SET
                status = EXCLUDED.status,
                executed_qty = EXCLUDED.executed_qty,
                updated_at = NOW(),
                binance_response = EXCLUDED.binance_response
        """

        await db.pool.execute(
            query,
            order_data["order_id"],
            order_data["client_order_id"],
            order_data["symbol"],
            order_data["side"],
            order_data["order_type"],
            order_data["status"],
            order_data["price"],
            order_data["quantity"],
            order_data["executed_qty"],
            order_data["time_in_force"],
            order_data["binance_response"],
        )

    async def place_futures_order(
        self, order_request: FuturesOrderRequest
    ) -> OrderResponse:
        """Place futures order on Binance and persist to database with current status."""
        try:
            client = await self._get_client()
            market_type = order_request.market_type.value

            # Step 1: Place order on Binance
            logger.info(
                f"Placing {market_type} futures order: "
                f"{order_request.side.value} {order_request.quantity} {order_request.symbol}"
            )

            binance_response = await client.place_order(
                symbol=order_request.symbol,
                market_type=market_type,
                side=order_request.side.value,
                order_type=order_request.order_type.value,
                quantity=order_request.quantity,
                price=order_request.price,
                stop_price=order_request.stop_price,
                time_in_force=order_request.time_in_force,
                reduce_only=order_request.reduce_only,
                close_position=order_request.close_position,
                working_type=order_request.working_type,
                price_protect=order_request.price_protect,
            )

            order_id = binance_response.get("orderId")

            # Step 2: Query current status from Binance
            logger.debug(f"Querying current status for futures order {order_id}")
            status_response = await self._get_order_status_from_binance(
                order_id=order_id, symbol=order_request.symbol, market_type=market_type
            )

            # Use status response if available, otherwise use initial response
            current_data = status_response if status_response else binance_response

            # Step 3: Prepare order data for database
            order_data = {
                "order_id": order_id,
                "client_order_id": current_data.get("clientOrderId"),
                "symbol": order_request.symbol.upper(),
                "market_type": market_type,
                "side": order_request.side.value,
                "order_type": order_request.order_type.value,
                "status": current_data.get("status", "NEW"),
                "price": float(current_data.get("price", 0)) or order_request.price,
                "quantity": float(current_data.get("origQty", order_request.quantity)),
                "executed_qty": float(current_data.get("executedQty", 0)),
                "time_in_force": current_data.get(
                    "timeInForce", order_request.time_in_force
                ),
                "reduce_only": order_request.reduce_only,
                "close_position": order_request.close_position,
                "stop_price": order_request.stop_price,
                "working_type": order_request.working_type,
                "price_protect": order_request.price_protect,
                "binance_response": current_data,
            }

            # Step 4: Persist to database
            try:
                await self._persist_futures_order(order_data)
                logger.info(f"Futures order {order_id} persisted successfully")
            except Exception as db_error:
                # Log error but don't fail - order is already live on Binance
                logger.error(
                    f"CRITICAL: Futures order {order_id} placed successfully but DB insertion failed: {db_error}"
                )
                logger.error(f"Order details: {order_data}")

            # Step 5: Return response
            return OrderResponse(
                success=True,
                order_id=order_id,
                client_order_id=order_data["client_order_id"],
                symbol=order_data["symbol"],
                side=order_data["side"],
                order_type=order_data["order_type"],
                status=order_data["status"],
                price=order_data["price"],
                quantity=order_data["quantity"],
                executed_qty=order_data["executed_qty"],
                binance_response=current_data,
            )

        except BinanceAPIError as e:
            logger.error(f"Binance API error placing futures order: {e}")
            return OrderResponse(
                success=False,
                symbol=order_request.symbol,
                side=order_request.side.value,
                order_type=order_request.order_type.value,
                status="FAILED",
                quantity=order_request.quantity,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error placing futures order: {e}")
            return OrderResponse(
                success=False,
                symbol=order_request.symbol,
                side=order_request.side.value,
                order_type=order_request.order_type.value,
                status="FAILED",
                quantity=order_request.quantity,
                error=f"Internal error: {str(e)}",
            )

    async def _persist_futures_order(self, order_data: Dict[str, Any]) -> None:
        """Persist futures order to database."""
        query = """
            INSERT INTO futures_orders (
                order_id, client_order_id, symbol, market_type, side, order_type, status,
                price, quantity, executed_qty, time_in_force, reduce_only, close_position,
                stop_price, working_type, price_protect, binance_response
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
            ON CONFLICT (order_id) DO UPDATE SET
                status = EXCLUDED.status,
                executed_qty = EXCLUDED.executed_qty,
                updated_at = NOW(),
                binance_response = EXCLUDED.binance_response
        """

        await db.pool.execute(
            query,
            order_data["order_id"],
            order_data["client_order_id"],
            order_data["symbol"],
            order_data["market_type"],
            order_data["side"],
            order_data["order_type"],
            order_data["status"],
            order_data["price"],
            order_data["quantity"],
            order_data["executed_qty"],
            order_data["time_in_force"],
            order_data["reduce_only"],
            order_data["close_position"],
            order_data["stop_price"],
            order_data["working_type"],
            order_data["price_protect"],
            order_data["binance_response"],
        )

    async def get_recent_spot_orders(
        self, symbol: Optional[str] = None, limit: int = 3
    ) -> List[SpotOrder]:
        """Get recent spot orders (max 3 per symbol by default)."""
        try:
            if symbol:
                query = """
                    SELECT * FROM spot_orders 
                    WHERE symbol = $1 
                    ORDER BY created_at DESC 
                    LIMIT $2
                """
                rows = await db.pool.fetch(query, symbol.upper(), limit)
            else:
                # Get max 3 per symbol for all symbols
                query = """
                    SELECT DISTINCT ON (symbol) * FROM spot_orders
                    ORDER BY symbol, created_at DESC
                """
                rows = await db.pool.fetch(query)

            orders = []
            for row in rows:
                orders.append(
                    SpotOrder(
                        id=row["id"],
                        order_id=row["order_id"],
                        client_order_id=row["client_order_id"],
                        symbol=row["symbol"],
                        side=row["side"],
                        order_type=row["order_type"],
                        status=row["status"],
                        price=float(row["price"]) if row["price"] else None,
                        quantity=float(row["quantity"]),
                        executed_qty=float(row["executed_qty"]),
                        time_in_force=row["time_in_force"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        binance_response=row["binance_response"],
                    )
                )

            return orders

        except Exception as e:
            logger.error(f"Error fetching spot orders: {e}")
            raise DatabaseError(f"Failed to fetch spot orders: {e}", operation="SELECT")

    async def get_recent_futures_orders(
        self,
        symbol: Optional[str] = None,
        market_type: Optional[str] = None,
        limit: int = 3,
    ) -> List[FuturesOrder]:
        """Get recent futures orders (max 3 per symbol by default)."""
        try:
            conditions = []
            params = []
            param_idx = 1

            if symbol:
                conditions.append(f"symbol = ${param_idx}")
                params.append(symbol.upper())
                param_idx += 1

            if market_type:
                conditions.append(f"market_type = ${param_idx}")
                params.append(market_type.lower())
                param_idx += 1

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            query = f"""
                SELECT * FROM futures_orders 
                {where_clause}
                ORDER BY created_at DESC 
                LIMIT ${param_idx}
            """
            params.append(limit)

            rows = await db.pool.fetch(query, *params)

            orders = []
            for row in rows:
                orders.append(
                    FuturesOrder(
                        id=row["id"],
                        order_id=row["order_id"],
                        client_order_id=row["client_order_id"],
                        symbol=row["symbol"],
                        market_type=row["market_type"],
                        side=row["side"],
                        order_type=row["order_type"],
                        status=row["status"],
                        price=float(row["price"]) if row["price"] else None,
                        quantity=float(row["quantity"]),
                        executed_qty=float(row["executed_qty"]),
                        time_in_force=row["time_in_force"],
                        reduce_only=row["reduce_only"],
                        close_position=row["close_position"],
                        stop_price=float(row["stop_price"])
                        if row["stop_price"]
                        else None,
                        working_type=row["working_type"],
                        price_protect=row["price_protect"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        binance_response=row["binance_response"],
                    )
                )

            return orders

        except Exception as e:
            logger.error(f"Error fetching futures orders: {e}")
            raise DatabaseError(
                f"Failed to fetch futures orders: {e}", operation="SELECT"
            )

    async def close(self):
        """Close Binance client connection."""
        if self.client:
            await self.client.close()


# Global service instance
trading_service = TradingService()
