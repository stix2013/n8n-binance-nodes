from fastapi import APIRouter, HTTPException

try:
    from ..models.ingest_models import (
        IngestRequest,
        IngestResponse,
        RSIResult,
        MACDResult,
        SMAResult,
        EMAResult,
    )
    from ..utils.indicators import TechnicalIndicators
except ImportError:
    from models.ingest_models import (
        IngestRequest,
        IngestResponse,
        RSIResult,
        MACDResult,
        SMAResult,
        EMAResult,
    )
    from utils.indicators import TechnicalIndicators
from datetime import datetime
import logging

router = APIRouter(prefix="/api/ingest", tags=["ingest"])
logger = logging.getLogger(__name__)

# SMA window configuration based on interval
INTERVAL_SMA_WINDOWS = {
    "15m": [10, 20, 50],
    "1h": [20, 50, 200],
    "4h": [20, 50, 200],
}

# EMA window configuration based on interval (matches indicators route)
INTERVAL_EMA_WINDOWS = {
    "1m": [9, 21],
    "5m": [5, 8],
    "15m": [12, 26],
    "1h": [20, 50],
    "4h": [50, 200],
    "1d": [50, 200],
}


def get_sma_windows(interval: str) -> list[int]:
    """
    Get appropriate SMA windows based on the candle interval.

    Args:
        interval: Candle interval (e.g., "15m", "1h", "4h")

    Returns:
        List of SMA windows to calculate
    """
    return INTERVAL_SMA_WINDOWS.get(
        interval, [20, 50]
    )  # Default to [20, 50] if interval not found


def get_ema_windows(interval: str) -> list[int]:
    """
    Get appropriate EMA windows based on the candle interval.

    Args:
        interval: Candle interval (e.g., "1m", "15m", "1h", "4h")

    Returns:
        List of EMA windows to calculate
    """
    return INTERVAL_EMA_WINDOWS.get(
        interval, [20, 50]
    )  # Default to [20, 50] if interval not found


@router.post(
    "/analyze", response_model=IngestResponse, response_model_exclude_none=True
)
async def analyze_n8n_data(request: IngestRequest):
    """
    Analyze kline data received from n8n Binance node.
    Performs RSI and MACD analysis based on provided parameters.
    """
    try:
        # Extract data
        klines = request.data.klines
        if not klines:
            raise HTTPException(status_code=400, detail="No kline data provided")

        # Convert close prices to float (n8n sends strings)
        # Sort by closeTime just in case, though n8n usually sends sorted
        sorted_klines = sorted(klines, key=lambda k: k.closeTime)
        prices = [float(k.close) for k in sorted_klines]

        # Get parameters
        params = request.parameters

        # Calculate RSI
        rsi_value = TechnicalIndicators.calculate_rsi(prices, period=params.rsi_period)
        rsi_signal = TechnicalIndicators.generate_rsi_signal(rsi_value)

        # Calculate MACD
        macd_data = TechnicalIndicators.calculate_macd(
            prices,
            fast_period=params.macd_fast,
            slow_period=params.macd_slow,
            signal_period=params.macd_signal,
        )
        macd_signal_type, macd_crossover = TechnicalIndicators.generate_macd_signal(
            macd_data
        )

        # Get current price
        current_price = prices[-1]

        # Calculate SMA based on interval, filtering out windows larger than available data
        sma_values = {}
        sma_signal = "NEUTRAL"
        if params.sma_enabled:
            sma_windows = get_sma_windows(request.data.interval)
            valid_sma_windows = [w for w in sma_windows if w <= len(prices)]
            if valid_sma_windows:
                sma_values = TechnicalIndicators.calculate_sma(
                    prices, valid_sma_windows
                )
                sma_signal = TechnicalIndicators.generate_sma_signal(
                    current_price, sma_values
                )

        # Calculate EMA based on interval, filtering out windows larger than available data
        ema_values = {}
        ema_signal = "NEUTRAL"
        if params.ema_enabled:
            ema_windows = get_ema_windows(request.data.interval)
            valid_ema_windows = [w for w in ema_windows if w <= len(prices)]
            if valid_ema_windows:
                ema_values = TechnicalIndicators.calculate_emas(
                    prices, valid_ema_windows
                )
                ema_signal = TechnicalIndicators.generate_ema_signal(
                    current_price, ema_values
                )

        # Generate Recommendation (considering RSI, MACD, SMA, and EMA)
        recommendation = TechnicalIndicators.generate_overall_recommendation(
            rsi_signal, macd_signal_type, macd_crossover
        )
        last_close_time_ms = sorted_klines[-1].closeTime
        analysis_timestamp = datetime.fromtimestamp(last_close_time_ms / 1000.0)

        sma_result = None
        if params.sma_enabled:
            sma_result = SMAResult(
                sma_10=sma_values.get(10),
                sma_20=sma_values.get(20),
                sma_50=sma_values.get(50),
                sma_200=sma_values.get(200),
                signal=sma_signal,
            )

        ema_result = None
        if params.ema_enabled:
            ema_result = EMAResult(
                ema_5=ema_values.get(5),
                ema_8=ema_values.get(8),
                ema_9=ema_values.get(9),
                ema_12=ema_values.get(12),
                ema_20=ema_values.get(20),
                ema_21=ema_values.get(21),
                ema_26=ema_values.get(26),
                ema_50=ema_values.get(50),
                ema_200=ema_values.get(200),
                signal=ema_signal,
            )

        return IngestResponse(
            symbol=request.data.symbol,
            interval=request.data.interval,
            current_price=current_price,
            analysis_timestamp=analysis_timestamp,
            rsi=RSIResult(value=rsi_value, signal=rsi_signal),
            macd=MACDResult(
                macd_line=macd_data["macd_line"],
                signal_line=macd_data["signal_line"],
                histogram=macd_data["histogram"],
                signal_type=macd_signal_type,
                crossover=macd_crossover,
            ),
            sma=sma_result,
            ema=ema_result,
            recommendation=recommendation,
        )

    except ValueError as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Unexpected error in ingest analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal analysis error")
