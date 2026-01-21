"""Pydantic models for API requests and responses with v2 best practices."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
)


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


class PriceDataPoint(BaseModel):
    """Model for a single price data point."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

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

    @field_serializer("open_time", "close_time")
    @classmethod
    def serialize_datetime(cls, v: datetime) -> str:
        return v.isoformat()


class PriceRequest(BaseModel):
    """Model for price request parameters."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_to_upper=True,
        validate_assignment=True,
    )

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

    @field_validator("symbol", mode="before")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate and normalize symbol."""
        if not v.isalnum():
            raise ValueError("Symbol must contain only alphanumeric characters")
        return v.upper()

    @field_validator("startdate", "enddate", mode="before")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate date format is YYYYMMDD."""
        if v is not None:
            if len(v) != 8 or not v.isdigit():
                raise ValueError("Date must be in YYYYMMDD format")
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


class ErrorResponse(BaseModel):
    """Model for error responses."""

    success: bool = Field(default=False, description="Request success status")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )

    @field_serializer("timestamp")
    @classmethod
    def serialize_datetime(cls, v: datetime) -> str:
        return v.isoformat()


class HealthResponse(BaseModel):
    """Model for health check response."""

    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Check timestamp"
    )

    @field_serializer("timestamp")
    @classmethod
    def serialize_datetime(cls, v: datetime) -> str:
        return v.isoformat()


class RootResponse(BaseModel):
    """Model for root endpoint response."""

    message: str = Field(..., description="Welcome message")
    version: str = Field(default="1.0.0", description="API version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )

    @field_serializer("timestamp")
    @classmethod
    def serialize_datetime(cls, v: datetime) -> str:
        return v.isoformat()
