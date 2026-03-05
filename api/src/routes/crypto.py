"""Crypto prediction API routes."""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crypto", tags=["crypto"])


class PredictRequest(BaseModel):
    """Request model for prediction."""

    symbol: str = Field(..., description="Trading pair symbol (e.g., BNBUSDT, ETHUSDT)")
    interval: str = Field(
        default="1m", description="Kline interval (e.g., 1m, 15m, 1h)"
    )
    bars: int = Field(default=200, description="Number of recent bars to fetch", ge=210)


class PredictResponse(BaseModel):
    """Response model for prediction."""

    symbol: str
    signal: str


@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    """
    Generate trading signals using a trained model.

    Loads the trained model for the specified symbol and interval,
    fetches recent market data from Binance, and generates a prediction.
    """
    import joblib

    try:
        from crypto_analysis.data import create_client
    except ImportError as e:
        logger.error(f"Failed to import crypto-analysis module: {e}")
        raise HTTPException(
            status_code=500, detail="Crypto analysis module not available"
        )

    symbol = request.symbol.upper()
    interval = request.interval.replace("m", "min")
    model_filename = f"model_{symbol.lower()}_{interval}.joblib"
    model_path = Path("/app/models") / model_filename

    if not model_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Model not found: {model_filename}. Train a model first using /api/training/train",
        )

    try:
        logger.info(f"Loading model from {model_path}")
        generator = joblib.load(model_path)
        logger.info(f"Model loaded: {generator.name}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

    feature_lookback = 200
    fetch_bars = max(request.bars, feature_lookback + generator.sequence_length + 10)

    try:
        client = create_client()
        data = client.fetch_historical(symbol, request.interval, fetch_bars)
        logger.info(f"Fetched {len(data)} candles for {symbol}")
    except Exception as e:
        logger.error(f"Failed to fetch market data: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch market data: {str(e)}"
        )

    try:
        signals = generator.generate(data)
    except Exception as e:
        logger.error(f"Failed to generate signals: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate signals: {str(e)}"
        )

    if signals:
        signal_type = signals[0].signal_type.name
        if signal_type == "ENTRY_LONG":
            signal = "LONG"
        elif signal_type == "ENTRY_SHORT":
            signal = "SHORT"
        else:
            signal = "WAIT"
    else:
        signal = "WAIT"

    logger.info(f"Prediction for {symbol}: {signal}")

    return PredictResponse(symbol=symbol, signal=signal)
