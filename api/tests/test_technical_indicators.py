"""Tests for technical indicators functionality."""

import pytest
import numpy as np
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Add the parent directory to the path so we can import main
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from main import app

client = TestClient(app)


class TestTechnicalIndicators:
    """Test suite for technical indicator calculations"""

    def test_calculate_rsi_valid_data(self):
        """Test RSI calculation with valid data."""
        from utils.indicators import TechnicalIndicators

        # Sample price data with known RSI value
        prices = [
            10.0,
            10.5,
            10.3,
            10.8,
            11.0,
            10.9,
            11.2,
            11.5,
            11.3,
            11.7,
            11.8,
            12.0,
            11.9,
            12.2,
            12.5,
        ]  # 15 prices

        rsi = TechnicalIndicators.calculate_rsi(prices, period=14)

        assert isinstance(rsi, float)
        assert 0 <= rsi <= 100

    def test_calculate_rsi_insufficient_data(self):
        """Test RSI calculation with insufficient data."""
        from utils.indicators import TechnicalIndicators

        prices = [10.0, 10.5]  # Only 2 prices, need 15 for period 14

        with pytest.raises(ValueError, match="Insufficient data"):
            TechnicalIndicators.calculate_rsi(prices, period=14)

    def test_calculate_rsi_edge_cases(self):
        """Test RSI calculation edge cases."""
        from utils.indicators import TechnicalIndicators

        # Test with period = 2 (minimum)
        prices = [10.0, 10.5, 10.3, 10.8, 11.0]
        rsi = TechnicalIndicators.calculate_rsi(prices, period=2)
        assert 0 <= rsi <= 100

        # Test with all rising prices
        rising_prices = [
            10.0,
            10.1,
            10.2,
            10.3,
            10.4,
            10.5,
            10.6,
            10.7,
            10.8,
            10.9,
            11.0,
            11.1,
            11.2,
            11.3,
            11.4,
            11.5,
            11.6,
            11.7,
            11.8,
            11.9,
            12.0,
            12.1,
            12.2,
            12.3,
            12.4,
            12.5,
            12.6,
            12.7,
            12.8,
            12.9,
        ]
        rsi = TechnicalIndicators.calculate_rsi(rising_prices, period=14)
        assert rsi > 50  # Should be high for rising trend

    def test_calculate_ema_valid_data(self):
        """Test EMA calculation with valid data."""
        from utils.indicators import TechnicalIndicators

        prices = [10.0, 10.5, 10.3, 10.8, 11.0, 10.9, 11.2, 11.5, 11.3, 11.7]

        ema = TechnicalIndicators.calculate_ema(prices, period=3)

        assert len(ema) == len(prices)
        assert isinstance(ema[0], (int, float))
        assert ema[0] == pytest.approx(
            10.2667, rel=1e-2
        )  # First 3 prices average (10.0 + 10.5 + 10.3) / 3 = 10.267

    def test_calculate_macd_valid_data(self):
        """Test MACD calculation with valid data."""
        from utils.indicators import TechnicalIndicators

        # Generate more data for MACD calculation
        prices = [
            10.0,
            10.5,
            10.3,
            10.8,
            11.0,
            10.9,
            11.2,
            11.5,
            11.3,
            11.7,
            11.8,
            12.0,
            11.9,
            12.2,
            12.5,
            12.3,
            12.8,
            13.0,
            12.9,
            13.2,
            13.5,
            13.3,
            13.8,
            14.0,
            13.9,
            14.2,
            14.5,
            14.3,
            14.8,
            15.0,
        ]  # 30 prices

        macd_result = TechnicalIndicators.calculate_macd(prices)

        assert "macd_line" in macd_result
        assert "signal_line" in macd_result
        assert "histogram" in macd_result
        assert isinstance(macd_result["macd_line"], float)
        assert isinstance(macd_result["signal_line"], float)
        assert isinstance(macd_result["histogram"], float)

    def test_calculate_macd_insufficient_data(self):
        """Test MACD calculation with insufficient data."""
        from utils.indicators import TechnicalIndicators

        prices = [
            10.0,
            10.5,
            10.3,
            10.8,
            11.0,
        ]  # Only 5 prices, need at least 35 for slow=26 + signal=9

        with pytest.raises(ValueError, match="Insufficient data"):
            TechnicalIndicators.calculate_macd(prices)

    def test_calculate_macd_invalid_periods(self):
        """Test MACD calculation with invalid periods."""
        from utils.indicators import TechnicalIndicators

        prices = [
            10.0,
            10.5,
            10.3,
            10.8,
            11.0,
            10.9,
            11.2,
            11.5,
            11.3,
            11.7,
            11.8,
            12.0,
            11.9,
            12.2,
            12.5,
            12.3,
            12.8,
            13.0,
            12.9,
            13.2,
            13.5,
            13.3,
            13.8,
            14.0,
            13.9,
            14.2,
            14.5,
            14.3,
            14.8,
            15.0,
        ]  # 30 prices

        # Test slow <= fast
        with pytest.raises(ValueError, match="Slow period.*must be greater"):
            TechnicalIndicators.calculate_macd(prices, fast_period=26, slow_period=12)

    def test_generate_rsi_signal(self):
        """Test RSI signal generation."""
        from utils.indicators import TechnicalIndicators

        # Test oversold signal
        signal = TechnicalIndicators.generate_rsi_signal(25)
        assert signal == "OVERSOLD"

        # Test overbought signal
        signal = TechnicalIndicators.generate_rsi_signal(75)
        assert signal == "OVERBOUGHT"

        # Test neutral signal
        signal = TechnicalIndicators.generate_rsi_signal(50)
        assert signal == "NEUTRAL"

    def test_generate_macd_signal(self):
        """Test MACD signal generation."""
        from utils.indicators import TechnicalIndicators

        # Test bullish signal
        macd_data = {"macd_line": 1.0, "signal_line": 0.5, "histogram": 0.5}
        signal_type, crossover = TechnicalIndicators.generate_macd_signal(macd_data)
        assert signal_type == "BULLISH"
        assert crossover == "ABOVE"

        # Test bearish signal
        macd_data = {"macd_line": 0.5, "signal_line": 1.0, "histogram": -0.5}
        signal_type, crossover = TechnicalIndicators.generate_macd_signal(macd_data)
        assert signal_type == "BEARISH"
        assert crossover == "BELOW"

    def test_generate_overall_recommendation(self):
        """Test overall recommendation logic."""
        from utils.indicators import TechnicalIndicators

        # Test strong buy
        recommendation = TechnicalIndicators.generate_overall_recommendation(
            "OVERSOLD", "BULLISH", "ABOVE"
        )
        assert recommendation == "STRONG_BUY"

        # Test strong sell
        recommendation = TechnicalIndicators.generate_overall_recommendation(
            "OVERBOUGHT", "BEARISH", "BELOW"
        )
        assert recommendation == "STRONG_SELL"

        # Test hold
        recommendation = TechnicalIndicators.generate_overall_recommendation(
            "NEUTRAL", "NEUTRAL", "EQUAL"
        )
        assert recommendation == "HOLD"

    def test_validate_price_data(self):
        """Test price data validation."""
        from utils.indicators import TechnicalIndicators

        # Test valid data
        prices = [10.0, 10.5, 10.3, 10.8, 11.0] * 6  # 30 prices
        TechnicalIndicators.validate_price_data(
            prices, min_candles=30
        )  # Should not raise

        # Test insufficient data
        with pytest.raises(ValueError, match="Insufficient price data"):
            TechnicalIndicators.validate_price_data(prices[:5], min_candles=30)

        # Test empty data
        with pytest.raises(ValueError, match="Price data cannot be empty"):
            TechnicalIndicators.validate_price_data([])

        # Test negative prices
        with pytest.raises(ValueError, match="All prices must be positive"):
            TechnicalIndicators.validate_price_data([10.0, -5.0, 10.5], min_candles=30)

        # Test identical prices
        with pytest.raises(ValueError, match="Price data must contain variation"):
            TechnicalIndicators.validate_price_data([10.0] * 30, min_candles=30)


class TestTechnicalIndicatorsAPI:
    """Test suite for technical indicators API endpoints"""

    def setup_method(self):
        """Setup method to run before each test"""
        self.mock_api_key = "test_api_key_12345"

    def test_technical_analysis_endpoint_success(self):
        """Test successful technical analysis API call."""
        # Mock response data from Binance API with varying closing prices
        mock_response_data = []
        base_price = 45000.0
        for i in range(50):
            close_price = base_price + (i * 100)  # Varying closing prices
            mock_response_data.append(
                [
                    1704067200000 + (i * 60000),  # Open time
                    f"{close_price + 100:.2f}".encode(),  # Open price (string)
                    f"{close_price + 200:.2f}".encode(),  # High price (string)
                    f"{close_price - 100:.2f}".encode(),  # Low price (string)
                    f"{close_price:.2f}".encode(),  # Close price (string) - varying
                    "1000.00000000",  # Volume
                    1704067260000 + (i * 60000),  # Close time
                    "45500000.00000000",  # Quote asset volume
                    1000,  # Number of trades
                    "500.00000000",  # Taker buy base asset volume
                    "22750000.00000000",  # Taker buy quote asset volume
                    "ignore",  # Ignore
                ]
            )

        with patch.dict(
            os.environ, {"BINANCE_API_KEY": self.mock_api_key}, clear=False
        ):
            with patch("routes.indicators.httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_response_data
                mock_client.get.return_value = mock_response
                mock_client_class.return_value.__aenter__.return_value = mock_client

                response = client.get(
                    "/api/indicators/analysis?symbol=BTCUSDT&interval=1h&limit=50"
                )

                assert response.status_code == 200
                data = response.json()

                # Verify response structure
                assert "symbol" in data
                assert "current_price" in data
                assert "rsi" in data
                assert "macd" in data
                assert "overall_recommendation" in data

                # Verify RSI structure
                assert "value" in data["rsi"]
                assert "signal" in data["rsi"]
                assert data["rsi"]["value"] >= 0
                assert data["rsi"]["value"] <= 100
                assert data["rsi"]["signal"] in ["OVERSOLD", "NEUTRAL", "OVERBOUGHT"]

                # Verify MACD structure
                assert "macd_line" in data["macd"]
                assert "signal_line" in data["macd"]
                assert "histogram" in data["macd"]

    def test_technical_analysis_invalid_symbol(self):
        """Test technical analysis with invalid symbol."""
        with patch.dict(
            os.environ, {"BINANCE_API_KEY": self.mock_api_key}, clear=False
        ):
            response = client.get(
                "/api/indicators/analysis?symbol=BTC-USDT&interval=1h"
            )

            assert response.status_code == 422
            assert (
                "Symbol must contain only alphanumeric characters"
                in response.json()["detail"]
            )

    def test_technical_analysis_insufficient_data(self):
        """Test technical analysis with insufficient data."""
        # Mock response with only 5 data points (need 30) with varying prices
        mock_response_data = []
        base_price = 45000.0
        for i in range(5):
            close_price = base_price + (i * 100)
            mock_response_data.append(
                [
                    1704067200000 + (i * 60000),
                    f"{close_price + 100:.2f}".encode(),
                    f"{close_price + 200:.2f}".encode(),
                    f"{close_price - 100:.2f}".encode(),
                    f"{close_price:.2f}".encode(),
                    "1000.00000000",
                    1704067260000 + (i * 60000),
                    "45500000.00000000",
                    1000,
                    "500.00000000",
                    "22750000.00000000",
                    "ignore",
                ]
            )

        with patch.dict(
            os.environ, {"BINANCE_API_KEY": self.mock_api_key}, clear=False
        ):
            with patch("routes.indicators.httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_response_data
                mock_client.get.return_value = mock_response
                mock_client_class.return_value.__aenter__.return_value = mock_client

                response = client.get(
                    "/api/indicators/analysis?symbol=BTCUSDT&interval=1h&limit=5"
                )

                assert (
                    response.status_code == 422
                )  # FastAPI validation error (limit parameter)
                assert "greater than or equal to 30" in str(response.json()["detail"])

    def test_single_indicator_rsi_endpoint(self):
        """Test single RSI indicator endpoint."""
        mock_response_data = []
        base_price = 45000.0
        for i in range(50):
            close_price = base_price + (i * 100)
            mock_response_data.append(
                [
                    1704067200000 + (i * 60000),
                    f"{close_price + 100:.2f}".encode(),
                    f"{close_price + 200:.2f}".encode(),
                    f"{close_price - 100:.2f}".encode(),
                    f"{close_price:.2f}".encode(),
                    "1000.00000000",
                    1704067260000 + (i * 60000),
                    "45500000.00000000",
                    1000,
                    "500.00000000",
                    "22750000.00000000",
                    "ignore",
                ]
            )

        with patch.dict(
            os.environ, {"BINANCE_API_KEY": self.mock_api_key}, clear=False
        ):
            with patch("routes.indicators.httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_response_data
                mock_client.get.return_value = mock_response
                mock_client_class.return_value.__aenter__.return_value = mock_client

                response = client.get("/api/indicators/rsi?symbol=BTCUSDT&interval=1h")

                assert response.status_code == 200
                data = response.json()

                # Verify response structure
                assert "symbol" in data
                assert "indicator" in data
                assert "value" in data
                assert "signal" in data
                assert data["indicator"] == "rsi"

    def test_single_indicator_macd_endpoint(self):
        """Test single MACD indicator endpoint."""
        mock_response_data = []
        base_price = 45000.0
        for i in range(50):
            close_price = base_price + (i * 100)
            mock_response_data.append(
                [
                    1704067200000 + (i * 60000),
                    f"{close_price + 100:.2f}".encode(),
                    f"{close_price + 200:.2f}".encode(),
                    f"{close_price - 100:.2f}".encode(),
                    f"{close_price:.2f}".encode(),
                    "1000.00000000",
                    1704067260000 + (i * 60000),
                    "45500000.00000000",
                    1000,
                    "500.00000000",
                    "22750000.00000000",
                    "ignore",
                ]
            )

        with patch.dict(
            os.environ, {"BINANCE_API_KEY": self.mock_api_key}, clear=False
        ):
            with patch("routes.indicators.httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_response_data
                mock_client.get.return_value = mock_response
                mock_client_class.return_value.__aenter__.return_value = mock_client

                response = client.get("/api/indicators/macd?symbol=BTCUSDT&interval=1h")

                assert response.status_code == 200
                data = response.json()

                # Verify response structure
                assert "symbol" in data
                assert "indicator" in data
                assert "value" in data
                assert "signal" in data
                assert data["indicator"] == "macd"

    def test_single_indicator_invalid_name(self):
        """Test single indicator with invalid indicator name."""
        with patch.dict(
            os.environ, {"BINANCE_API_KEY": self.mock_api_key}, clear=False
        ):
            response = client.get("/api/indicators/invalid?symbol=BTCUSDT&interval=1h")

            assert response.status_code == 400  # Route-level validation error
            assert "Supported indicators: 'rsi', 'macd'" in response.json()["detail"]

    def test_technical_analysis_missing_api_key(self):
        """Test technical analysis without API key."""
        with patch.dict(os.environ, {}, clear=True):
            response = client.get("/api/indicators/analysis?symbol=BTCUSDT&interval=1h")

            assert response.status_code == 500
            assert "BINANCE_API_KEY not found" in response.json()["detail"]

    def test_technical_analysis_macd_period_validation(self):
        """Test MACD period validation in analysis endpoint."""
        with patch.dict(
            os.environ, {"BINANCE_API_KEY": self.mock_api_key}, clear=False
        ):
            response = client.get(
                "/api/indicators/analysis?symbol=BTCUSDT&interval=1h&macd_slow=10&macd_fast=15"
            )

            assert response.status_code == 422
            assert (
                "MACD slow period must be greater than fast period"
                in response.json()["detail"]
            )


class TestTechnicalIndicatorsIntegration:
    """Integration tests for technical indicators"""

    def test_mathematical_accuracy_rsi(self):
        """Test RSI calculation mathematical accuracy."""
        from utils.indicators import TechnicalIndicators

        # Create a simple price series with known pattern
        # All rising prices should give RSI > 50
        rising_prices = [100.0 + i for i in range(50)]  # Linear increase
        rsi = TechnicalIndicators.calculate_rsi(rising_prices, period=14)
        assert rsi > 50, f"Expected RSI > 50 for rising prices, got {rsi}"

        # All falling prices should give RSI < 50
        falling_prices = [150.0 - i for i in range(50)]  # Linear decrease
        rsi = TechnicalIndicators.calculate_rsi(falling_prices, period=14)
        assert rsi < 50, f"Expected RSI < 50 for falling prices, got {rsi}"

    def test_mathematical_accuracy_macd(self):
        """Test MACD calculation mathematical consistency."""
        from utils.indicators import TechnicalIndicators

        # Use a simple trending price series
        trending_prices = [100.0 + i * 0.1 for i in range(50)]  # Steady uptrend

        macd_result = TechnicalIndicators.calculate_macd(trending_prices)

        # In an uptrend, MACD should generally be positive
        assert macd_result["macd_line"] > 0, (
            f"MACD line should be positive in uptrend, got {macd_result['macd_line']}"
        )

        # Verify histogram calculation
        expected_histogram = macd_result["macd_line"] - macd_result["signal_line"]
        assert abs(macd_result["histogram"] - expected_histogram) < 1e-10, (
            "Histogram calculation error"
        )

    def test_parameter_bounds(self):
        """Test parameter boundary conditions."""
        from utils.indicators import TechnicalIndicators

        prices = [100.0 + i for i in range(50)]

        # Test minimum period
        rsi = TechnicalIndicators.calculate_rsi(prices, period=2)
        assert 0 <= rsi <= 100

        # Test maximum reasonable period
        rsi = TechnicalIndicators.calculate_rsi(prices, period=25)
        assert 0 <= rsi <= 100

        # Test MACD with different periods
        macd_result = TechnicalIndicators.calculate_macd(
            prices, fast_period=5, slow_period=15, signal_period=7
        )
        assert "macd_line" in macd_result
        assert "signal_line" in macd_result
        assert "histogram" in macd_result


if __name__ == "__main__":
    pytest.main([__file__])
