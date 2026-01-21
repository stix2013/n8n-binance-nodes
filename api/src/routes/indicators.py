"""Technical indicators API routes with best practices."""

import logging
from typing import Annotated, Tuple

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

try:
    from ..utils.date_utils import timestamp_to_iso
    from ..utils.indicators import TechnicalIndicators
    from ..utils.binance import (
        get_api_key as shared_get_api_key,
        get_http_client as shared_get_http_client,
        fetch_binance_data as shared_fetch_binance_data,
        extract_closing_prices,
    )
    from ..models.indicators import (
        TechnicalAnalysisResponse,
        RSIResult,
        MACDResult,
        MACDSignal,
        SingleIndicatorResponse,
        IndicatorType,
        ErrorResponse as IndicatorsErrorResponse,
    )
    from ..models.settings import settings
except ImportError:
    from utils.date_utils import timestamp_to_iso
    from utils.indicators import TechnicalIndicators
    from utils.binance import (
        get_api_key as shared_get_api_key,
        get_http_client as shared_get_http_client,
        fetch_binance_data as shared_fetch_binance_data,
        extract_closing_prices,
    )
    from models.indicators import (
        TechnicalAnalysisResponse,
        RSIResult,
        MACDResult,
        MACDSignal,
        SingleIndicatorResponse,
        IndicatorType,
        ErrorResponse as IndicatorsErrorResponse,
    )
    from models.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/indicators", tags=["Technical Indicators"])

get_api_key = shared_get_api_key
get_http_client = shared_get_http_client


async def fetch_closing_prices(
    client: httpx.AsyncClient,
    symbol: str,
    interval: str,
    limit: int,
) -> Tuple[list[float], int | None]:
    """Fetch closing prices from Binance API."""
    klines = await shared_fetch_binance_data(client, symbol, interval, limit)

    closing_prices = extract_closing_prices(klines)
    last_timestamp = int(klines[-1][0]) if klines else None

    return closing_prices, last_timestamp


SymbolQuery = Annotated[
    str,
    Query(
        ...,
        min_length=1,
        max_length=20,
        description="Trading pair symbol (e.g., BTCUSDT)",
    ),
]

IntervalQuery = Annotated[
    str,
    Query(
        ...,
        description="Candle interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)",
    ),
]

LimitQuery = Annotated[
    int,
    Query(ge=30, le=1000, description="Number of candles to analyze"),
]

PeriodQuery = Annotated[
    int,
    Query(ge=2, le=100, description="Calculation period"),
]

MACDFastQuery = Annotated[
    int,
    Query(ge=2, le=50, description="MACD fast EMA period"),
]

MACDSlowQuery = Annotated[
    int,
    Query(ge=26, le=100, description="MACD slow EMA period"),
]

MACDSignalQuery = Annotated[
    int,
    Query(ge=2, le=50, description="MACD signal line period"),
]


@router.get(
    "/analysis",
    response_model=TechnicalAnalysisResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": IndicatorsErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": IndicatorsErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": IndicatorsErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": IndicatorsErrorResponse},
    },
    summary="Technical Analysis",
    description="Get comprehensive RSI and MACD analysis for a trading pair",
)
async def get_technical_analysis(
    symbol: SymbolQuery,
    interval: IntervalQuery,
    api_key: Annotated[str, Depends(get_api_key)],
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
    limit: LimitQuery = 100,
    rsi_period: PeriodQuery = 14,
    macd_fast: MACDFastQuery = 12,
    macd_slow: MACDSlowQuery = 26,
    macd_signal: MACDSignalQuery = 9,
) -> TechnicalAnalysisResponse:
    """
    Get comprehensive RSI and MACD analysis for a trading pair.

    - **symbol**: Trading pair symbol (required) - e.g., BTCUSDT, ETHUSDT
    - **interval**: Candle interval (required)
    - **limit**: Number of candles to analyze (default: 100, range: 30-1000)
    - **rsi_period**: RSI calculation period (default: 14, range: 2-100)
    - **macd_fast**: MACD fast EMA period (default: 12, range: 2-50)
    - **macd_slow**: MACD slow EMA period (default: 26, range: 31-100)
    - **macd_signal**: MACD signal line period (default: 9, range: 2-50)
    """
    if not symbol.isalnum():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Symbol must contain only alphanumeric characters",
        )

    if macd_slow <= macd_fast:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="MACD slow period must be greater than fast period",
        )

    try:
        closing_prices, last_timestamp = await fetch_closing_prices(
            client, symbol, interval, limit
        )

        TechnicalIndicators.validate_price_data(
            closing_prices, min_candles=settings.min_candles_for_analysis
        )

        rsi_value = TechnicalIndicators.calculate_rsi(closing_prices, rsi_period)
        rsi_signal = TechnicalIndicators.generate_rsi_signal(rsi_value)

        macd_data = TechnicalIndicators.calculate_macd(
            closing_prices, macd_fast, macd_slow, macd_signal
        )
        macd_signal_type, macd_crossover = TechnicalIndicators.generate_macd_signal(
            macd_data
        )

        overall_recommendation = TechnicalIndicators.generate_overall_recommendation(
            rsi_signal, macd_signal_type, macd_crossover
        )

        current_price = closing_prices[-1]
        analysis_ts = timestamp_to_iso(last_timestamp) if last_timestamp else None

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
            analysis_timestamp=analysis_ts,
            candles_analyzed=len(closing_prices),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in get_technical_analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/{indicator_name}",
    response_model=SingleIndicatorResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": IndicatorsErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": IndicatorsErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": IndicatorsErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": IndicatorsErrorResponse},
    },
    summary="Single Indicator",
    description="Get a single technical indicator calculation",
)
async def get_single_indicator(
    indicator_name: str,
    symbol: SymbolQuery,
    interval: IntervalQuery,
    api_key: Annotated[str, Depends(get_api_key)],
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
    period: PeriodQuery = None,
    limit: LimitQuery = 100,
) -> SingleIndicatorResponse:
    """
    Get a single technical indicator calculation.

    - **indicator_name**: Indicator to calculate ("rsi" or "macd")
    - **symbol**: Trading pair symbol (required)
    - **interval**: Candle interval (required)
    - **period**: Calculation period (optional, defaults to standard values)
    - **limit**: Number of candles to analyze
    """
    indicator_name = indicator_name.lower()

    if indicator_name not in ["rsi", "macd"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supported indicators: 'rsi', 'macd'",
        )

    if indicator_name == "rsi":
        period = period or settings.default_rsi_period
    elif indicator_name == "macd":
        period = period or settings.default_macd_fast

    try:
        closing_prices, last_timestamp = await fetch_closing_prices(
            client, symbol, interval, limit
        )

        TechnicalIndicators.validate_price_data(
            closing_prices, min_candles=settings.min_candles_for_analysis
        )

        if indicator_name == "rsi":
            value = TechnicalIndicators.calculate_rsi(closing_prices, period)
            signal = TechnicalIndicators.generate_rsi_signal(value)
        else:
            macd_data = TechnicalIndicators.calculate_macd(closing_prices, period)
            value = macd_data["macd_line"]
            signal_type, _ = TechnicalIndicators.generate_macd_signal(macd_data)
            signal = signal_type

        return SingleIndicatorResponse(
            symbol=symbol.upper(),
            indicator=IndicatorType(indicator_name),
            value=value,
            signal=signal,
            timestamp=timestamp_to_iso(last_timestamp) if last_timestamp else None,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error calculating {indicator_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
