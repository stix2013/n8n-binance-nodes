"""Technical indicators calculations for trading analysis."""

from typing import List, Dict, Tuple
import numpy as np
import pandas as pd
from datetime import datetime


class TechnicalIndicators:
    """Core technical indicator calculations."""

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """
        Calculate RSI (Relative Strength Index).

        Args:
            prices: List of closing prices
            period: RSI calculation period (default 14)

        Returns:
            RSI value between 0 and 100

        Raises:
            ValueError: If insufficient data or invalid inputs
        """
        if len(prices) < period + 1:
            raise ValueError(
                f"Insufficient data for RSI calculation. Need at least {period + 1} prices, got {len(prices)}"
            )

        if period < 2:
            raise ValueError(f"RSI period must be at least 2, got {period}")

        # Convert to numpy array for efficiency
        prices_array = np.array(prices)

        # Calculate price changes
        deltas = np.diff(prices_array)

        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        # Calculate initial averages using simple moving average
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        # Use exponential smoothing for subsequent periods
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        # Calculate RS and RSI
        if avg_loss == 0:
            return 100.0  # No losses means RSI = 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[float]:
        """
        Calculate Exponential Moving Average.

        Args:
            prices: List of closing prices
            period: EMA period

        Returns:
            List of EMA values

        Raises:
            ValueError: If insufficient data or invalid inputs
        """
        if len(prices) < period:
            raise ValueError(
                f"Insufficient data for EMA calculation. Need at least {period} prices, got {len(prices)}"
            )

        if period < 1:
            raise ValueError(f"EMA period must be at least 1, got {period}")

        prices_array = np.array(prices)

        # Calculate multiplier
        multiplier = 2 / (period + 1)

        # Initialize EMA array
        ema_values = [0.0] * len(prices)

        # Start with SMA for first value
        sma_first_period = np.mean(prices_array[:period])
        ema_values[period - 1] = sma_first_period

        # Calculate EMA for remaining values
        for i in range(period, len(prices)):
            ema_values[i] = (prices_array[i] * multiplier) + (
                ema_values[i - 1] * (1 - multiplier)
            )

        # Fill the values before period with the first valid EMA
        for i in range(period):
            ema_values[i] = sma_first_period

        return ema_values

    @staticmethod
    def calculate_macd(
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> Dict[str, float]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            prices: List of closing prices
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line EMA period (default 9)

        Returns:
            Dictionary with 'macd_line', 'signal_line', 'histogram'

        Raises:
            ValueError: If insufficient data or invalid inputs
        """
        # Validate inputs
        if slow_period <= fast_period:
            raise ValueError(
                f"Slow period ({slow_period}) must be greater than fast period ({fast_period})"
            )

        min_required = slow_period  # Only need slow period for MACD line, signal is applied to MACD line
        if len(prices) < min_required:
            raise ValueError(
                f"Insufficient data for MACD calculation. Need at least {min_required} prices, got {len(prices)}"
            )

        # Calculate EMAs
        fast_ema = TechnicalIndicators.calculate_ema(prices, fast_period)
        slow_ema = TechnicalIndicators.calculate_ema(prices, slow_period)

        # Calculate MACD line
        macd_line = []
        for i in range(len(fast_ema)):
            if i < len(slow_ema):
                macd_line.append(fast_ema[i] - slow_ema[i])
            else:
                # Use last slow_ema value for calculation
                macd_line.append(fast_ema[i] - slow_ema[-1])

        # Calculate signal line (EMA of MACD line)
        signal_line = TechnicalIndicators.calculate_ema(macd_line, signal_period)

        # Calculate histogram (MACD - Signal)
        histogram = []
        for i in range(len(macd_line)):
            if i < len(signal_line):
                histogram.append(macd_line[i] - signal_line[i])
            else:
                # Use last signal_line value for calculation
                histogram.append(macd_line[i] - signal_line[-1])

        return {
            "macd_line": round(macd_line[-1], 6),
            "signal_line": round(signal_line[-1], 6),
            "histogram": round(histogram[-1], 6),
        }

    @staticmethod
    def generate_rsi_signal(rsi_value: float) -> str:
        """
        Generate RSI signal based on value.

        Args:
            rsi_value: RSI value (0-100)

        Returns:
            Signal string: "OVERSOLD", "NEUTRAL", or "OVERBOUGHT"
        """
        if rsi_value < 30:
            return "OVERSOLD"
        elif rsi_value > 70:
            return "OVERBOUGHT"
        else:
            return "NEUTRAL"

    @staticmethod
    def generate_macd_signal(macd_data: Dict[str, float]) -> Tuple[str, str]:
        """
        Generate MACD signal based on MACD components.

        Args:
            macd_data: Dictionary with macd_line, signal_line, histogram

        Returns:
            Tuple of (signal_type, crossover)
        """
        macd_line = macd_data["macd_line"]
        signal_line = macd_data["signal_line"]
        histogram = macd_data["histogram"]

        # Determine signal type based on MACD vs Signal line
        if macd_line > signal_line:
            signal_type = "BULLISH"
        elif macd_line < signal_line:
            signal_type = "BEARISH"
        else:
            signal_type = "NEUTRAL"

        # Determine crossover
        if histogram > 0:
            crossover = "ABOVE"
        elif histogram < 0:
            crossover = "BELOW"
        else:
            crossover = "EQUAL"

        return signal_type, crossover

    @staticmethod
    def generate_overall_recommendation(
        rsi_signal: str, macd_signal: str, macd_crossover: str
    ) -> str:
        """
        Generate overall trading recommendation based on RSI and MACD signals.

        Args:
            rsi_signal: RSI signal ("OVERSOLD", "NEUTRAL", "OVERBOUGHT")
            macd_signal: MACD signal ("BULLISH", "NEUTRAL", "BEARISH")
            macd_crossover: MACD crossover ("ABOVE", "BELOW", "EQUAL")

        Returns:
            Overall recommendation: "STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"
        """
        # Strong signals
        if rsi_signal == "OVERSOLD" and macd_signal == "BULLISH":
            return "STRONG_BUY"
        elif rsi_signal == "OVERBOUGHT" and macd_signal == "BEARISH":
            return "STRONG_SELL"

        # Moderate signals
        elif rsi_signal == "OVERSOLD" or (
            macd_signal == "BULLISH" and macd_crossover == "ABOVE"
        ):
            return "BUY"
        elif rsi_signal == "OVERBOUGHT" or (
            macd_signal == "BEARISH" and macd_crossover == "BELOW"
        ):
            return "SELL"

        # Neutral/hold signals
        else:
            return "HOLD"

    @staticmethod
    def validate_price_data(prices: List[float], min_candles: int = 30) -> None:
        """
        Validate price data for technical analysis.

        Args:
            prices: List of closing prices
            min_candles: Minimum number of candles required

        Raises:
            ValueError: If data validation fails
        """
        if not prices:
            raise ValueError("Price data cannot be empty")

        if not all(isinstance(price, (int, float)) for price in prices):
            raise ValueError("All prices must be numeric values")

        if any(price <= 0 for price in prices):
            raise ValueError("All prices must be positive")

        if len(prices) < min_candles:
            raise ValueError(
                f"Insufficient price data. Need at least {min_candles} candles, got {len(prices)}"
            )

        # Check for reasonable price variation
        if len(set(prices)) < 2:
            raise ValueError(
                "Price data must contain variation (all prices are identical)"
            )
