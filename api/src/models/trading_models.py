"""Trading models for spot and futures orders, candlestick data."""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum


class MarketTypeEnum(str, Enum):
    """Market types for trading."""

    SPOT = "spot"
    USD_M = "usd_m"
    COIN_M = "coin_m"


class OrderSideEnum(str, Enum):
    """Order side (buy or sell)."""

    BUY = "BUY"
    SELL = "SELL"


class OrderStatusEnum(str, Enum):
    """Order status."""

    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    PENDING_CANCEL = "PENDING_CANCEL"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class OrderTypeEnum(str, Enum):
    """Order types."""

    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
    LIMIT_MAKER = "LIMIT_MAKER"
    STOP = "STOP"
    STOP_MARKET = "STOP_MARKET"
    TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"
    TRAILING_STOP_MARKET = "TRAILING_STOP_MARKET"


class IntervalEnum(str, Enum):
    """Valid candlestick intervals."""

    ONE_MINUTE = "1m"
    FIFTEEN_MINUTES = "15m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"


class SpotOrder(BaseModel):
    """Spot order model."""

    id: Optional[int] = None
    order_id: Optional[int] = None
    client_order_id: Optional[str] = None
    symbol: str
    side: OrderSideEnum
    order_type: OrderTypeEnum
    status: OrderStatusEnum
    price: Optional[float] = None
    quantity: float
    executed_qty: float = 0
    time_in_force: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    binance_response: Optional[dict] = None


class FuturesOrder(BaseModel):
    """Futures order model."""

    id: Optional[int] = None
    order_id: Optional[int] = None
    client_order_id: Optional[str] = None
    symbol: str
    market_type: MarketTypeEnum
    side: OrderSideEnum
    order_type: OrderTypeEnum
    status: OrderStatusEnum
    price: Optional[float] = None
    quantity: float
    executed_qty: float = 0
    time_in_force: Optional[str] = None
    reduce_only: bool = False
    close_position: bool = False
    stop_price: Optional[float] = None
    working_type: Optional[str] = None
    price_protect: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    binance_response: Optional[dict] = None


class CandlestickData(BaseModel):
    """Candlestick/OHLCV data model."""

    symbol: str
    market_type: MarketTypeEnum
    interval: str
    open_time: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    close_time: datetime
    quote_volume: float
    trades: int
    taker_buy_base_volume: float
    taker_buy_quote_volume: float
    updated_at: Optional[datetime] = None


class SpotOrderRequest(BaseModel):
    """Request model for placing spot order."""

    symbol: str = Field(..., description="Trading pair symbol (e.g., BTCUSDT)")
    side: OrderSideEnum = Field(..., description="Order side")
    order_type: OrderTypeEnum = Field(
        default=OrderTypeEnum.MARKET, description="Order type"
    )
    quantity: float = Field(..., gt=0, description="Quantity to buy/sell")
    price: Optional[float] = Field(None, gt=0, description="Price for LIMIT orders")
    time_in_force: Optional[str] = Field("GTC", description="Time in force")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate and uppercase symbol."""
        if not v or not v.isalnum():
            raise ValueError("Symbol must contain only alphanumeric characters")
        return v.upper()


class FuturesOrderRequest(BaseModel):
    """Request model for placing futures order."""

    symbol: str = Field(..., description="Trading pair symbol (e.g., BTCUSDT)")
    market_type: MarketTypeEnum = Field(
        ..., description="Market type (usd_m or coin_m)"
    )
    side: OrderSideEnum = Field(..., description="Order side")
    order_type: OrderTypeEnum = Field(
        default=OrderTypeEnum.MARKET, description="Order type"
    )
    quantity: float = Field(..., gt=0, description="Quantity to buy/sell")
    price: Optional[float] = Field(None, gt=0, description="Price for LIMIT orders")
    time_in_force: Optional[str] = Field("GTC", description="Time in force")
    reduce_only: bool = Field(False, description="Reduce only flag")
    close_position: bool = Field(False, description="Close position flag")
    stop_price: Optional[float] = Field(
        None, gt=0, description="Stop price for stop orders"
    )
    working_type: Optional[str] = Field("CONTRACT_PRICE", description="Working type")
    price_protect: bool = Field(False, description="Price protection")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate and uppercase symbol."""
        if not v or not v.isalnum():
            raise ValueError("Symbol must contain only alphanumeric characters")
        return v.upper()


class OrderResponse(BaseModel):
    """Response model for order placement."""

    success: bool
    order_id: Optional[int] = None
    client_order_id: Optional[str] = None
    symbol: str
    side: str
    order_type: str
    status: str
    price: Optional[float] = None
    quantity: float
    executed_qty: float = 0
    message: str = "Order placed successfully"
    error: Optional[str] = None
    binance_response: Optional[dict] = None


class CandlestickRequest(BaseModel):
    """Request model for fetching candlesticks."""

    symbol: str = Field(..., description="Trading pair symbol")
    market_type: MarketTypeEnum = Field(..., description="Market type")
    interval: IntervalEnum = Field(
        default=IntervalEnum.ONE_HOUR, description="Candlestick interval"
    )
    limit: int = Field(default=100, ge=1, le=1000, description="Number of candles")
    start_time: Optional[datetime] = Field(None, description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate and uppercase symbol."""
        if not v or not v.isalnum():
            raise ValueError("Symbol must contain only alphanumeric characters")
        return v.upper()


class CandlestickResponse(BaseModel):
    """Response model for candlestick data."""

    success: bool
    symbol: str
    market_type: str
    interval: str
    data: List[CandlestickData]
    count: int
    message: str = "Success"
    error: Optional[str] = None


class MarkPriceResponse(BaseModel):
    """Response model for mark price."""

    success: bool
    symbol: str
    market_type: str
    mark_price: float
    index_price: Optional[float] = None
    estimated_settle_price: Optional[float] = None
    last_funding_rate: Optional[float] = None
    next_funding_time: Optional[datetime] = None
    time: Optional[datetime] = None
    message: str = "Success"
    error: Optional[str] = None


class OpenInterestResponse(BaseModel):
    """Response model for open interest."""

    success: bool
    symbol: str
    market_type: str
    open_interest: float
    open_interest_value: Optional[float] = None
    time: Optional[datetime] = None
    message: str = "Success"
    error: Optional[str] = None


class SyncStatusResponse(BaseModel):
    """Response model for sync status."""

    success: bool
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    symbols: List[str]
    intervals: List[str]
    market_types: List[str]
    is_running: bool
    message: str = "Success"
