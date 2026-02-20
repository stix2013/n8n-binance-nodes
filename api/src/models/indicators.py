"""Pydantic models for technical indicators API."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime
from enum import Enum


class TechnicalAnalysisRequest(BaseModel):
    """Request for RSI/MACD analysis."""

    symbol: str = Field(
        ..., min_length=1, max_length=20, description="Trading pair symbol"
    )
    interval: str = Field(
        ...,
        description="Candle interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)",
    )
    rsi_period: int = Field(
        default=14, ge=2, le=100, description="RSI calculation period"
    )
    macd_fast: int = Field(default=12, ge=2, le=50, description="MACD fast EMA period")
    macd_slow: int = Field(
        default=26, ge=31, le=100, description="MACD slow EMA period"
    )
    macd_signal: int = Field(
        default=9, ge=2, le=50, description="MACD signal line period"
    )
    limit: int = Field(
        default=100, ge=30, le=1000, description="Number of candles to analyze"
    )


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
    crossover: Optional[Literal["ABOVE", "BELOW"]] = Field(
        None, description="Signal line crossover"
    )


class SMAResult(BaseModel):
    """SMA calculation result."""

    sma_10: Optional[float] = Field(None, description="10-period SMA value")
    sma_20: Optional[float] = Field(None, description="20-period SMA value")
    sma_50: Optional[float] = Field(None, description="50-period SMA value")
    sma_200: Optional[float] = Field(None, description="200-period SMA value")
    signal: Literal["BULLISH", "BEARISH", "NEUTRAL"] = Field(
        description="SMA trend signal"
    )


class EMAResult(BaseModel):
    """EMA calculation result."""

    ema_5: Optional[float] = Field(None, description="5-period EMA (Scalping)")
    ema_8: Optional[float] = Field(None, description="8-period EMA (Scalping)")
    ema_9: Optional[float] = Field(None, description="9-period EMA (1m)")
    ema_12: Optional[float] = Field(None, description="12-period EMA (15m)")
    ema_20: Optional[float] = Field(None, description="20-period EMA (1h)")
    ema_21: Optional[float] = Field(None, description="21-period EMA (1m)")
    ema_26: Optional[float] = Field(None, description="26-period EMA (15m)")
    ema_50: Optional[float] = Field(None, description="50-period EMA (1h/4h)")
    ema_200: Optional[float] = Field(None, description="200-period EMA (4h)")
    signal: Literal["BULLISH", "BEARISH", "NEUTRAL"] = Field(
        description="EMA trend signal"
    )


class TechnicalAnalysisResponse(BaseModel):
    """Response with RSI, MACD, SMA, and EMA analysis."""

    symbol: str = Field(description="Trading pair symbol")
    interval: str = Field(description="Candle interval used for analysis")
    current_price: float = Field(ge=0, description="Current closing price")
    rsi: RSIResult = Field(description="RSI analysis result")
    macd: MACDResult = Field(description="MACD calculation result")
    macd_interpretation: MACDSignal = Field(description="MACD signal interpretation")
    sma: SMAResult = Field(description="SMA analysis result")
    ema: EMAResult = Field(description="EMA analysis result")
    overall_recommendation: Literal[
        "STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"
    ] = Field(description="Overall trading recommendation")
    analysis_timestamp: datetime = Field(description="Analysis timestamp")
    candles_analyzed: int = Field(
        ge=30, description="Number of candles used in analysis"
    )


class IndicatorType(str, Enum):
    """Supported indicator types."""

    RSI = "rsi"
    MACD = "macd"
    SMA = "sma"
    EMA = "ema"


class SingleIndicatorRequest(BaseModel):
    """Request for single indicator calculation."""

    symbol: str = Field(
        ..., min_length=1, max_length=20, description="Trading pair symbol"
    )
    interval: str = Field(..., description="Candle interval")
    indicator: IndicatorType = Field(..., description="Indicator to calculate")
    period: Optional[int] = Field(None, ge=2, le=100, description="Calculation period")


class SingleIndicatorResponse(BaseModel):
    """Response for single indicator calculation."""

    symbol: str = Field(description="Trading pair symbol")
    interval: str = Field(description="Candle interval used for calculation")
    indicator: IndicatorType = Field(description="Indicator type calculated")
    value: float = Field(description="Indicator value")
    signal: str = Field(description="Indicator signal")
    timestamp: datetime = Field(description="Calculation timestamp")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
