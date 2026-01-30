"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum


class IntervalEnum(str, Enum):
    """Valid Binance kline intervals."""

    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    TWO_HOURS = "2h"
    FOUR_HOURS = "4h"
    SIX_HOURS = "6h"
    EIGHT_HOURS = "8h"
    TWELVE_HOURS = "12h"
    ONE_DAY = "1d"
    THREE_DAYS = "3d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"


class OrderSideEnum(str, Enum):
    """Binance order sides."""

    BUY = "BUY"
    SELL = "SELL"


class OrderTypeEnum(str, Enum):
    """Binance order types."""

    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
    LIMIT_MAKER = "LIMIT_MAKER"


class PriceDataPoint(BaseModel):
    """Model for a single price data point."""

    open_time: datetime = Field(..., description="Opening time in ISO format")
    open_price: float = Field(..., ge=0, description="Opening price")
    high_price: float = Field(..., ge=0, description="Highest price")
    low_price: float = Field(..., ge=0, description="Lowest price")
    close_price: float = Field(..., ge=0, description="Closing price")
    volume: float = Field(..., ge=0, description="Trading volume")
    close_time: datetime = Field(..., description="Closing time in ISO format")
    quote_asset_volume: float = Field(..., ge=0, description="Quote asset volume")
    number_of_trades: int = Field(..., ge=0, description="Number of trades")
    taker_buy_base_asset_volume: float = Field(
        ..., ge=0, description="Taker buy base asset volume"
    )
    taker_buy_quote_asset_volume: float = Field(
        ..., ge=0, description="Taker buy quote asset volume"
    )
    ignore: str = Field(..., description="Ignore field")


class PriceRequest(BaseModel):
    """Model for price request parameters."""

    symbol: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Trading pair symbol (e.g., BTCUSDT)",
    )
    interval: IntervalEnum = Field(
        default=IntervalEnum.ONE_HOUR, description="Kline interval"
    )
    limit: int = Field(
        default=50, ge=1, le=1000, description="Number of records to return"
    )
    startdate: Optional[str] = Field(None, description="Start date in YYYYMMDD format")
    enddate: Optional[str] = Field(None, description="End date in YYYYMMDD format")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v):
        """Validate that symbol contains only alphanumeric characters."""
        if not v.isalnum():
            raise ValueError("Symbol must contain only alphanumeric characters")
        return v.upper()

    @field_validator("startdate", "enddate")
    @classmethod
    def validate_date_format(cls, v):
        """Validate date format is YYYYMMDD."""
        if v is not None:
            if len(v) != 8 or not v.isdigit():
                raise ValueError("Date must be in YYYYMMDD format")
            # Additional validation for valid date
            try:
                datetime.strptime(v, "%Y%m%d")
            except ValueError:
                raise ValueError("Invalid date")
        return v


class PriceResponse(BaseModel):
    """Model for price response."""

    symbol: str = Field(..., description="Trading pair symbol")
    data: List[PriceDataPoint] = Field(..., description="List of price data points")
    count: int = Field(..., ge=0, description="Number of data points returned")


class OrderRequest(BaseModel):
    """Model for order placement request."""

    symbol: str = Field(..., description="Trading pair symbol (e.g., BTCUSDT)")
    side: OrderSideEnum = Field(..., description="Order side (BUY or SELL)")
    type: OrderTypeEnum = Field(default=OrderTypeEnum.MARKET, description="Order type")
    quantity: float = Field(..., ge=0, description="Quantity to buy/sell")
    price: Optional[float] = Field(None, ge=0, description="Price for LIMIT orders")
    stopPrice: Optional[float] = Field(
        None, ge=0, description="Stop price for STOP orders"
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v):
        """Validate that symbol contains only alphanumeric characters."""
        if not v.isalnum():
            raise ValueError("Symbol must contain only alphanumeric characters")
        return v.upper()


class OrderResponse(BaseModel):
    """Model for order placement response."""

    symbol: str
    orderId: int
    clientOrderId: str
    transactTime: int
    price: float
    origQty: float
    executedQty: float
    status: str
    type: str
    side: str


class ErrorResponse(BaseModel):
    """Model for error responses."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Model for health check response."""

    status: str = Field(..., description="Health status")


class RootResponse(BaseModel):
    """Model for root endpoint response."""

    message: str = Field(..., description="Welcome message")
