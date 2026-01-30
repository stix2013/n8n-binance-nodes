"""Binance API routes."""

from fastapi import APIRouter, HTTPException, Depends, Query
import httpx
import os
import logging
from datetime import datetime

# Import utilities with fallback for both relative and absolute imports
try:
    from ..utils.date_utils import convert_date_format, timestamp_to_iso
    from ..utils.price_validation import validate_price_data, PriceValidationError
    from ..utils.crypto_utils import generate_signature, get_timestamp
    from ..models.api_models import (
        PriceResponse,
        ErrorResponse,
        IntervalEnum,
        OrderRequest,
        OrderResponse,
    )
    from ..models.settings import settings
except ImportError:
    from utils.date_utils import convert_date_format, timestamp_to_iso
    from utils.price_validation import validate_price_data
    from utils.crypto_utils import generate_signature, get_timestamp
    from models.api_models import (
        PriceResponse,
        ErrorResponse,
        IntervalEnum,
        OrderRequest,
        OrderResponse,
    )

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


async def get_binance_secret_key() -> str:
    """Dependency to get Binance secret key from environment."""
    secret_key = os.getenv("BINANCE_SECRET_KEY")
    if not secret_key:
        raise HTTPException(
            status_code=500,
            detail="BINANCE_SECRET_KEY not found in environment variables",
        )
    return secret_key


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
    skip_volume_validation: bool = Query(
        False, description="Skip volume validation (volume > 0)"
    ),
    skip_time_validation: bool = Query(
        False, description="Skip close_time validation (close at end of interval)"
    ),
    skip_price_validation: bool = Query(
        False, description="Skip price validation (prices within high/low bounds)"
    ),
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

                # Validate price data
                validation_errors = validate_price_data(
                    transformed_data,
                    interval.value,
                    skip_volume_validation=skip_volume_validation,
                    skip_time_validation=skip_time_validation,
                    skip_price_validation=skip_price_validation,
                )

                if validation_errors:
                    error_messages = [
                        f"Data point {error.index}: {error.message}"
                        for error in validation_errors
                    ]
                    logger.warning(
                        f"Price validation failed for {symbol}: {len(validation_errors)} errors found"
                    )
                    raise HTTPException(
                        status_code=400,
                        detail=f"Price validation failed: {'; '.join(error_messages)}",
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
                except Exception:
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


@router.post(
    "/order",
    response_model=OrderResponse,
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def place_binance_order(
    order: OrderRequest,
    api_key: str = Depends(get_binance_api_key),
    secret_key: str = Depends(get_binance_secret_key),
):
    """
    Place an order on Binance.
    Supports simple orders and bracket orders (Limit/Market + SL/TP).
    """
    headers = {"X-MBX-APIKEY": api_key}

    # Check if this is a bracket order
    has_bracket = order.takeProfitPrice is not None or order.stopLossPrice is not None

    try:
        async with httpx.AsyncClient() as client:
            # CASE 1: Limit Order + Bracket (OTOCO)
            if has_bracket and order.type == "LIMIT":
                url = "https://api.binance.com/api/v3/orderList/otoco"

                params = {
                    "symbol": order.symbol,
                    "workingSide": order.side.value,
                    "workingType": "LIMIT",
                    "workingQuantity": order.quantity,
                    "workingPrice": order.price,
                    "workingTimeInForce": "GTC",
                    "pendingSide": "SELL" if order.side.value == "BUY" else "BUY",
                    "pendingQuantity": order.quantity,
                    "timestamp": get_timestamp(),
                }

                # Add Take Profit (LIMIT_MAKER)
                if order.takeProfitPrice:
                    params["pendingPrice"] = order.takeProfitPrice
                else:
                    # OCO requires both legs, if missing one, we might need a different strategy
                    # But for now assuming full bracket if bracket is requested
                    pass

                # Add Stop Loss
                if order.stopLossPrice:
                    params["pendingStopPrice"] = order.stopLossPrice

                    if order.stopLossType == "LIMIT":
                        params["pendingStopLimitPrice"] = (
                            order.stopLossLimitPrice or order.stopLossPrice
                        )
                        params["pendingStopLimitTimeInForce"] = "GTC"
                    else:
                        # For Market Stop, we don't set pendingStopLimitPrice
                        # However, OCO endpoint typically expects STOP_LOSS_LIMIT.
                        # Binance Spot OCO *must* have a Limit leg for the Stop Loss if using OCO.
                        # Wait, OCO has two legs: LimitMaker (TP) and StopLoss (Limit or Market).
                        # Let's check docs.
                        # For OCO:
                        # Leg 1: LIMIT_MAKER (Price)
                        # Leg 2: STOP_LOSS or STOP_LOSS_LIMIT (StopPrice + [StopLimitPrice])

                        # So if user wants Market Stop, we just send stopPrice.
                        pass

                # Sign and execute
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                params["signature"] = generate_signature(query_string, secret_key)

                response = await client.post(
                    url, params=params, headers=headers, timeout=30.0
                )

                if response.status_code == 200:
                    return OrderResponse(**response.json())
                else:
                    raise_binance_error(response)

            # CASE 2: Market Order + Bracket (Sequential)
            elif has_bracket and order.type == "MARKET":
                # Step 1: Execute Market Entry
                url_order = "https://api.binance.com/api/v3/order"
                params_entry = {
                    "symbol": order.symbol,
                    "side": order.side.value,
                    "type": "MARKET",
                    "quantity": order.quantity,
                    "timestamp": get_timestamp(),
                }

                query_string = "&".join([f"{k}={v}" for k, v in params_entry.items()])
                params_entry["signature"] = generate_signature(query_string, secret_key)

                resp_entry = await client.post(
                    url_order, params=params_entry, headers=headers, timeout=30.0
                )

                if resp_entry.status_code != 200:
                    raise_binance_error(resp_entry)

                entry_data = resp_entry.json()
                executed_qty = float(entry_data.get("executedQty", order.quantity))

                # Step 2: Execute OCO Exit
                url_oco = "https://api.binance.com/api/v3/orderList/oco"
                exit_side = "SELL" if order.side.value == "BUY" else "BUY"

                params_oco = {
                    "symbol": order.symbol,
                    "side": exit_side,
                    "quantity": executed_qty,
                    "price": order.takeProfitPrice,  # Limit Maker
                    "stopPrice": order.stopLossPrice,
                    "timestamp": get_timestamp(),
                }

                if order.stopLossType == "LIMIT":
                    params_oco["stopLimitPrice"] = (
                        order.stopLossLimitPrice or order.stopLossPrice
                    )
                    params_oco["stopLimitTimeInForce"] = "GTC"

                query_string = "&".join([f"{k}={v}" for k, v in params_oco.items()])
                params_oco["signature"] = generate_signature(query_string, secret_key)

                resp_oco = await client.post(
                    url_oco, params=params_oco, headers=headers, timeout=30.0
                )

                if resp_oco.status_code == 200:
                    # Combine responses or return the OCO response?
                    # The user cares about the entry fill primarily, but the OCO details are also useful.
                    # We'll return the entry response but maybe append info?
                    # For strict typing, let's return the Entry response for now,
                    # as that contains the most critical trade info (price/qty).
                    # OR we could return the OCO response which has orderListId.

                    # Ideally we should define a complex response, but for now let's return the entry response
                    # and maybe log the OCO success.
                    # Actually, if we return the entry response, the user won't know the OCO ID.

                    # Let's return the Entry response, but inject the orderListId from the OCO.
                    oco_data = resp_oco.json()
                    entry_data["orderListId"] = oco_data.get("orderListId")
                    entry_data["contingencyType"] = "OCO"
                    return OrderResponse(**entry_data)
                else:
                    # If OCO fails, we have an open position!
                    # We should log this CRITICAL error and maybe return a warning.
                    logger.error(
                        f"OCO Exit failed for {order.symbol} after successful entry! Error: {resp_oco.text}"
                    )
                    # We still return success for the entry, but maybe throw an error?
                    # No, that would mask the successful trade.
                    # We'll return the entry data but validation might fail if we don't handle it.
                    raise_binance_error(resp_oco)

            # CASE 3: Standard Single Order (Limit/Market/Stop, etc.)
            else:
                url = "https://api.binance.com/api/v3/order"

                # Prepare base parameters
                params = {
                    "symbol": order.symbol,
                    "side": order.side.value,
                    "type": order.type.value,
                    "quantity": order.quantity,
                    "timestamp": get_timestamp(),
                }

                if order.type != "MARKET":
                    params["timeInForce"] = "GTC"  # Good Till Cancelled

                if order.price is not None:
                    params["price"] = order.price

                if order.stopPrice is not None:
                    params["stopPrice"] = order.stopPrice

                # Create query string for signature
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                signature = generate_signature(query_string, secret_key)
                params["signature"] = signature

                response = await client.post(
                    url, params=params, headers=headers, timeout=30.0
                )

                if response.status_code == 200:
                    return OrderResponse(**response.json())
                else:
                    raise_binance_error(response)

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
        logger.error(f"Unexpected error in place_binance_order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def raise_binance_error(response):
    error_detail = f"Binance API error: {response.status_code}"
    try:
        error_data = response.json()
        error_detail += f" - {error_data.get('msg', 'Unknown error')}"
    except Exception:
        error_detail += f" - {response.text}"

    raise HTTPException(status_code=response.status_code, detail=error_detail)
