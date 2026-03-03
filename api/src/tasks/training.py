"""Celery tasks for model training."""

import logging
from datetime import datetime
from pathlib import Path
from celery.exceptions import SoftTimeLimitExceeded, TimeLimitExceeded

from src.config.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=0)
def train_online_model(
    self,
    symbol: str = "ETHUSDT",
    interval: str = "15m",
    bars: int = 5000,
    warmup_bars: int = 1000,
    sequence_length: int = 60,
) -> dict:
    """
    Train an online learning model using the crypto-analysis module.

    Args:
        symbol: Trading pair symbol (e.g., ETHUSDT, BTCUSDT)
        interval: Kline interval (e.g., 15m, 1h, 4h)
        bars: Number of historical bars to fetch
        warmup_bars: Number of bars for initial training
        sequence_length: Sequence length for LSTM models

    Returns:
        dict: Training results including model path, metrics, and signal count

    Raises:
        Exception: If training fails
    """
    try:
        logger.info(f"Starting training task for {symbol} {interval}")
        logger.info(
            f"Parameters: bars={bars}, warmup_bars={warmup_bars}, sequence_length={sequence_length}"
        )

        # Import crypto-analysis modules
        try:
            from crypto_analysis.data import create_client
            from crypto_analysis.online.generator import OnlineSignalGenerator
            import joblib
        except ImportError as e:
            logger.error(f"Failed to import crypto-analysis module: {e}")
            raise

        # Step 1: Create Binance client and fetch data
        logger.info(f"[1/4] Fetching {bars} bars of historical data for {symbol}...")
        client = create_client()

        try:
            data = client.fetch_historical(symbol, interval, bars)
            logger.info(f"Fetched {len(data)} candles")
            logger.info(f"Date range: {data.index[0]} to {data.index[-1]}")
        except Exception as fetch_error:
            logger.error(f"Failed to fetch historical data: {fetch_error}")
            raise

        # Step 2: Initialize and train on warmup data
        logger.info(f"[2/4] Initial training on first {warmup_bars} bars...")

        if len(data) < warmup_bars:
            logger.warning(
                f"Not enough data for warmup. Requested {warmup_bars}, got {len(data)}. Adjusting..."
            )
            warmup_bars = int(len(data) * 0.5)

        warmup_data = data.iloc[:warmup_bars]

        generator = OnlineSignalGenerator(
            name=f"Online_{symbol}_{interval}",
            sequence_length=sequence_length,
            update_frequency=10,
        )

        try:
            if len(warmup_data) < generator.lookback_period:
                logger.warning(
                    f"Warmup data ({len(warmup_data)}) is less than generator lookback ({generator.lookback_period})"
                )

            generator.fit(warmup_data)
            logger.info("Initial training completed successfully")
        except Exception as fit_error:
            logger.error(f"Initial training failed: {fit_error}")
            # Try to continue without initial fit if we have enough data later,
            # but usually fit is required for scaler
            raise Exception(
                f"Failed to fit model with {len(warmup_data)} samples: {str(fit_error)}"
            )

        # Step 3: Run online learning simulation
        logger.info("[3/4] Running online learning simulation...")
        signals = []
        online_data = data.iloc[warmup_bars:]

        for i, idx in enumerate(online_data.index):
            lookback = data.loc[:idx]
            if len(lookback) < generator.lookback_period:
                continue

            try:
                signal_list = generator.generate(lookback)
                if signal_list:
                    for sig in signal_list:
                        signals.append(
                            {
                                "timestamp": sig.timestamp.isoformat()
                                if hasattr(sig.timestamp, "isoformat")
                                else str(sig.timestamp),
                                "symbol": symbol,
                                "signal_type": sig.signal_type.name,
                                "confidence": sig.confidence,
                                "prediction": sig.metadata.get(
                                    "ensemble_prediction", 0
                                ),
                                "regime": sig.metadata.get("regime", "unknown"),
                            }
                        )
            except Exception as gen_error:
                logger.warning(f"Error generating signal at index {i}: {gen_error}")
                continue

            # Progress update
            if (i + 1) % sequence_length == 0:
                progress = int((i + 1) / len(online_data) * 100)
                logger.info(
                    f"  Processed {i + 1}/{len(online_data)} bars ({progress}%)"
                )
                try:
                    self.update_state(
                        state="PROGRESS",
                        meta={"progress": progress, "current_bar": i + 1},
                    )
                except Exception:
                    pass

        # Step 4: Save results
        logger.info("[4/4] Saving results...")

        # Create models directory if it doesn't exist
        models_dir = Path("/app/models")
        models_dir.mkdir(exist_ok=True)

        # Save model
        model_filename = f"model_{symbol.lower()}_{interval.replace('m', 'min')}.joblib"
        model_path = models_dir / model_filename

        joblib.dump(generator, model_path)
        logger.info(f"Model saved to: {model_path}")

        # Calculate metrics
        signal_count = len(signals)
        signal_breakdown = {}
        if signals:
            from collections import Counter

            signal_types = [s["signal_type"] for s in signals]
            signal_breakdown = dict(Counter(signal_types))

        result = {
            "symbol": symbol,
            "interval": interval,
            "model_path": str(model_path),
            "model_filename": model_filename,
            "bars_processed": len(data),
            "warmup_bars": warmup_bars,
            "online_bars": len(online_data),
            "signals_generated": signal_count,
            "signal_breakdown": signal_breakdown,
            "sequence_length": sequence_length,
            "trained_at": datetime.now().isoformat(),
            "status": "success",
        }

        logger.info(f"Training complete! Generated {signal_count} signals")
        logger.info(f"Signal breakdown: {signal_breakdown}")

        return result

    except (SoftTimeLimitExceeded, TimeLimitExceeded):
        logger.error(f"Training task for {symbol} {interval} exceeded time limit")
        raise
    except Exception as e:
        logger.error(
            f"Training task failed for {symbol} {interval}: {e}", exc_info=True
        )
        raise
