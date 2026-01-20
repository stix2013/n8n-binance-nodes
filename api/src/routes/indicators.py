"""Technical indicators API routes."""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Tuple
import httpx
import os
import logging

# Import utilities with fallback for both relative and absolute imports
try:
    from ..utils.date_utils import timestamp_to_iso
    from ..utils.indicators import TechnicalIndicators
    from ..models.indicators import (
        TechnicalAnalysisResponse,
        RSIResult,
        MACDResult,
        MACDSignal,
        SingleIndicatorResponse,
        IndicatorType,
        ErrorResponse as IndicatorsErrorResponse,
    )
except ImportError:
    from utils.date_utils import timestamp_to_iso
    from utils.indicators import TechnicalIndicators
    from models.indicators import (
        TechnicalAnalysisResponse,
        RSIResult,
        MACDResult,
        MACDSignal,
        SingleIndicatorResponse,
        IndicatorType,
        ErrorResponse as IndicatorsErrorResponse,
    )

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/indicators", tags=["technical-indicators"])


async def get_binance_api_key() -> str:
    """Dependency to get Binance API key from environment."""
    api_key = os.getenv("BINANCE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, detail="BINANCE_API_KEY not found in environment variables"
        )
    return api_key


async def get_price_data(
    symbol: str, interval: str, limit: int, api_key: str
) -> Tuple[List[float], int]:
    """
    Fetch price data from Binance API and extract closing prices.

    Args:
        symbol: Trading pair symbol
        interval: Candle interval
        limit: Number of candles to fetch
        api_key: Binance API key

    Returns:
        Tuple of (closing_prices, last_timestamp)

    Raises:
        HTTPException: If unable to fetch data from Binance
    """
    # Build Binance API URL
    url = "https://api.binance.com/api/v3/klines"

    # Prepare query parameters
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}

    # Prepare headers
    headers = {"X-MBX-APIKEY": api_key}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, params=params, headers=headers, timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()

                # Extract closing prices and timestamps
                closing_prices = []
                last_timestamp = None
                for kline in data:
                    closing_prices.append(float(kline[4]))  # Close price is at index 4
                    if last_timestamp is None:
                        last_timestamp = int(kline[0])  # Open time is at index 0

                return closing_prices, last_timestamp
            else:
                error_detail = f"Binance API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_detail += f" - {error_data.get('msg', 'Unknown error')}"
                except (ValueError, httpx.HTTPStatusError):
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
    except Exception as e:
        logger.error(f"Unexpected error fetching price data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/analysis",
    response_model=TechnicalAnalysisResponse,
    responses={
        400: {"model": IndicatorsErrorResponse},
        422: {"model": IndicatorsErrorResponse},
        500: {"model": IndicatorsErrorResponse},
        503: {"model": IndicatorsErrorResponse},
    },
)
async def get_technical_analysis(
    symbol: str = Query(
        ...,
        min_length=1,
        max_length=20,
        description="Trading pair symbol (e.g., BTCUSDT)",
    ),
    interval: str = Query(
        ...,
        description="Candle interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)",
    ),
    rsi_period: int = Query(14, ge=2, le=100, description="RSI calculation period"),
    macd_fast: int = Query(12, ge=2, le=50, description="MACD fast EMA period"),
    macd_slow: int = Query(26, ge=2, le=100, description="MACD slow EMA period"),
    macd_signal: int = Query(9, ge=2, le=50, description="MACD signal line period"),
    limit: int = Query(100, ge=30, le=1000, description="Number of candles to analyze"),
    api_key: str = Depends(get_binance_api_key),
) -> TechnicalAnalysisResponse:
    """
    Get comprehensive RSI and MACD analysis for a trading pair.

    - **symbol**: Trading pair symbol (required) - e.g., BTCUSDT, ETHUSDT
    - **interval**: Candle interval (required)
    - **rsi_period**: RSI calculation period (default: 14, range: 2-100)
    - **macd_fast**: MACD fast EMA period (default: 12, range: 2-50)
    - **macd_slow**: MACD slow EMA period (default: 26, range: 31-100)
    - **macd_signal**: MACD signal line period (default: 9, range: 2-50)
    - **limit**: Number of candles to analyze (default: 100, range: 30-1000)
    """

    # Validate symbol format
    if not symbol.isalnum():
        raise HTTPException(
            status_code=422, detail="Symbol must contain only alphanumeric characters"
        )

    # Ensure macd_slow > macd_fast
    if macd_slow <= macd_fast:
        raise HTTPException(
            status_code=422, detail="MACD slow period must be greater than fast period"
        )

    try:
        # Fetch price data from Binance
        closing_prices, last_timestamp = await get_price_data(
            symbol, interval, limit, api_key
        )

        # Validate price data
        TechnicalIndicators.validate_price_data(closing_prices, min_candles=30)

        # Calculate RSI
        rsi_value = TechnicalIndicators.calculate_rsi(closing_prices, rsi_period)
        rsi_signal = TechnicalIndicators.generate_rsi_signal(rsi_value)

        # Calculate MACD
        macd_data = TechnicalIndicators.calculate_macd(
            closing_prices, macd_fast, macd_slow, macd_signal
        )
        macd_signal_type, macd_crossover = TechnicalIndicators.generate_macd_signal(
            macd_data
        )

        # Generate overall recommendation
        overall_recommendation = TechnicalIndicators.generate_overall_recommendation(
            rsi_signal, macd_signal_type, macd_crossover
        )

        # Create response
        current_price = closing_prices[-1]

        return TechnicalAnalysisResponse(
            symbol=symbol.upper(),
            current_price=current_price,
            rsi=RSIResult(value=rsi_value, signal=rsi_signal),
            macd=MACDResult(
                macd_line=macd_data["macd_line"],
                signal_line=macd_data["signal_line"],
                histogram=macd_data["histogram"],
            ),
            macd_interpretation=MACDSignal(
                signal_type=macd_signal_type, crossover=macd_crossover
            ),
            overall_recommendation=overall_recommendation,
            analysis_timestamp=timestamp_to_iso(last_timestamp)
            if last_timestamp
            else None,
            candles_analyzed=len(closing_prices),
        )
        macd_signal_type, macd_crossover = TechnicalIndicators.generate_macd_signal(
            macd_data
        )

        # Generate overall recommendation
        overall_recommendation = TechnicalIndicators.generate_overall_recommendation(
            rsi_signal, macd_signal_type, macd_crossover
        )

        # Create response
        current_price = closing_prices[-1]

        return TechnicalAnalysisResponse(
            symbol=symbol.upper(),
            current_price=current_price,
            rsi=RSIResult(value=rsi_value, signal=rsi_signal),
            macd=MACDResult(
                macd_line=macd_data["macd_line"],
                signal_line=macd_data["signal_line"],
                histogram=macd_data["histogram"],
            ),
            macd_interpretation=MACDSignal(
                signal_type=macd_signal_type, crossover=macd_crossover
            ),
            overall_recommendation=overall_recommendation,
            analysis_timestamp=timestamp_to_iso(last_timestamp)
            if last_timestamp
            else None,
            candles_analyzed=len(closing_prices),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTPException instances without logging them as errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error in technical analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/{indicator_name}",
    responses={
        400: {"model": IndicatorsErrorResponse},
        422: {"model": IndicatorsErrorResponse},
        500: {"model": IndicatorsErrorResponse},
        503: {"model": IndicatorsErrorResponse},
    },
)
async def get_single_indicator(
    indicator_name: str,
    symbol: str = Query(
        ..., min_length=1, max_length=20, description="Trading pair symbol"
    ),
    interval: str = Query(..., description="Candle interval"),
    period: int = Query(None, ge=2, le=100, description="Calculation period"),
    limit: int = Query(100, ge=30, le=1000, description="Number of candles to analyze"),
    api_key: str = Depends(get_binance_api_key),
) -> SingleIndicatorResponse:
    """
    Get a single technical indicator calculation.

    - **indicator_name**: Indicator to calculate ("rsi" or "macd")
    - **symbol**: Trading pair symbol (required)
    - **interval**: Candle interval (required)
    - **period**: Calculation period (optional, defaults to standard values)
    - **limit**: Number of candles to analyze
    """

    # Validate indicator name
    indicator_name = indicator_name.lower()
    if indicator_name not in ["rsi", "macd"]:
        raise HTTPException(
            status_code=400, detail="Supported indicators: 'rsi', 'macd'"
        )

    # Set default periods
    if indicator_name == "rsi":
        period = period or 14
    elif indicator_name == "macd":
        period = period or 12  # For MACD fast period

    try:
        # Fetch price data from Binance
        closing_prices, last_timestamp = await get_price_data(
            symbol, interval, limit, api_key
        )

        # Validate price data
        TechnicalIndicators.validate_price_data(closing_prices, min_candles=30)

        # Calculate indicator
        if indicator_name == "rsi":
            value = TechnicalIndicators.calculate_rsi(closing_prices, period)
            signal = TechnicalIndicators.generate_rsi_signal(value)
        else:  # macd
            # For MACD, we'll return the MACD line as the primary value
            macd_data = TechnicalIndicators.calculate_macd(closing_prices, period)
            value = macd_data["macd_line"]
            signal_type, _ = TechnicalIndicators.generate_macd_signal(macd_data)
            signal = signal_type

        return SingleIndicatorResponse(
            symbol=symbol.upper(),
            indicator=IndicatorType(indicator_name),  # Return enum value
            value=value,
            signal=signal,
            timestamp=timestamp_to_iso(last_timestamp) if last_timestamp else None,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTPException instances without logging them as errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error calculating {indicator_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
