from fastapi import APIRouter, HTTPException

try:
    from ..models.ingest_models import (
        IngestRequest,
        IngestResponse,
        RSIResult,
        MACDResult,
    )
    from ..utils.indicators import TechnicalIndicators
except ImportError:
    from models.ingest_models import (
        IngestRequest,
        IngestResponse,
        RSIResult,
        MACDResult,
    )
    from utils.indicators import TechnicalIndicators
from datetime import datetime
import logging

router = APIRouter(prefix="/api/ingest", tags=["ingest"])
logger = logging.getLogger(__name__)


@router.post("/analyze", response_model=IngestResponse)
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

        # Generate Recommendation
        recommendation = TechnicalIndicators.generate_overall_recommendation(
            rsi_signal, macd_signal_type, macd_crossover
        )

        # Prepare Response
        current_price = prices[-1]
        last_close_time_ms = sorted_klines[-1].closeTime
        analysis_timestamp = datetime.fromtimestamp(last_close_time_ms / 1000.0)

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
