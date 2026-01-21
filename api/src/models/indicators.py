"""Pydantic models for technical indicators API with v2 best practices."""

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class IndicatorType(str, Enum):
    """Supported indicator types."""

    RSI = "rsi"
    MACD = "macd"


class RSIResult(BaseModel):
    """RSI calculation result."""

    value: float = Field(ge=0, le=100, description="RSI value (0-100)")
    signal: Literal["OVERSOLD", "NEUTRAL", "OVERBOUGHT"] = Field(
        description="RSI signal"
    )


class MACDResult(BaseModel):
    """MACD calculation result."""

    macd_line: float = Field(description="MACD line value")
    signal_line: float = Field(description="MACD signal line value")
    histogram: float = Field(description="MACD histogram (MACD - Signal)")


class MACDSignal(BaseModel):
    """MACD signal interpretation."""

    signal_type: Literal["BULLISH", "BEARISH", "NEUTRAL"] = Field(
        description="MACD signal type"
    )
    crossover: Optional[Literal["ABOVE", "BELOW", "EQUAL"]] = Field(
        default=None, description="Signal line crossover"
    )


class TechnicalAnalysisResponse(BaseModel):
    """Response with RSI and MACD analysis."""

    symbol: str = Field(description="Trading pair symbol")
    current_price: float = Field(ge=0, description="Current closing price")
    rsi: RSIResult = Field(description="RSI analysis result")
    macd: MACDResult = Field(description="MACD calculation result")
    macd_interpretation: MACDSignal = Field(description="MACD signal interpretation")
    overall_recommendation: Literal[
        "STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"
    ] = Field(description="Overall trading recommendation")
    analysis_timestamp: datetime = Field(description="Analysis timestamp")
    candles_analyzed: int = Field(
        ge=30, description="Number of candles used in analysis"
    )

    @field_serializer("analysis_timestamp")
    @classmethod
    def serialize_datetime(cls, v: datetime) -> str:
        return v.isoformat()


class SingleIndicatorRequest(BaseModel):
    """Request for single indicator calculation."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_to_lower=True,
        validate_assignment=True,
    )

    symbol: str = Field(
        ..., min_length=1, max_length=20, description="Trading pair symbol"
    )
    interval: str = Field(..., description="Candle interval")
    indicator: IndicatorType = Field(..., description="Indicator to calculate")
    period: Optional[int] = Field(None, ge=2, le=100, description="Calculation period")


class SingleIndicatorResponse(BaseModel):
    """Response for single indicator calculation."""

    symbol: str = Field(description="Trading pair symbol")
    indicator: IndicatorType = Field(description="Indicator type calculated")
    value: float = Field(description="Indicator value")
    signal: str = Field(description="Indicator signal")
    timestamp: datetime = Field(description="Calculation timestamp")

    @field_serializer("timestamp")
    @classmethod
    def serialize_datetime(cls, v: datetime) -> str:
        return v.isoformat()


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = Field(default=False, description="Request success status")
    error: str = Field(description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )

    @field_serializer("timestamp")
    @classmethod
    def serialize_datetime(cls, v: datetime) -> str:
        return v.isoformat()
