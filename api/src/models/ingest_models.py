from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class N8NKline(BaseModel):
    """Kline object from n8n Binance node."""

    openTime: int
    open: str
    high: str
    low: str
    close: str
    volume: str
    closeTime: int
    quoteVolume: str
    trades: int
    takerBuyBaseVolume: str
    takerBuyQuoteVolume: str


class N8NNodeOutput(BaseModel):
    """Output structure from n8n Binance Kline node."""

    symbol: str
    interval: str
    limit: int
    currentPrice: Optional[str] = None
    klineCount: int
    klines: List[N8NKline]
    fetchedAt: str


class AnalysisParameters(BaseModel):
    """Configuration for technical analysis."""

    rsi_period: int = Field(default=14, ge=2, description="RSI period")
    macd_fast: int = Field(default=12, ge=2, description="MACD fast period")
    macd_slow: int = Field(default=26, ge=2, description="MACD slow period")
    macd_signal: int = Field(default=9, ge=2, description="MACD signal period")
    sma_enabled: bool = Field(default=True, description="Calculate SMA indicators")


class IngestRequest(BaseModel):
    """Request body for ingestion endpoint."""

    data: N8NNodeOutput
    parameters: Optional[AnalysisParameters] = Field(default_factory=AnalysisParameters)


class RSIResult(BaseModel):
    value: float
    signal: str


class MACDResult(BaseModel):
    macd_line: float
    signal_line: float
    histogram: float
    signal_type: str
    crossover: str


class SMAResult(BaseModel):
    """SMA calculation result."""

    sma_10: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    signal: str


class IngestResponse(BaseModel):
    """Response containing analysis results."""

    symbol: str
    interval: str
    current_price: float
    analysis_timestamp: datetime
    rsi: RSIResult
    macd: MACDResult
    sma: SMAResult
    recommendation: str
