"""Test API ingestion from n8n node."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import sys
import os

# Add the parent directory to the path so we can import main
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Sample kline data matching n8n BinanceKline node output
SAMPLE_KLINE_DATA = {
    "symbol": "BTCUSDT",
    "interval": "15m",
    "limit": 100,
    "currentPrice": "42000.50",
    "klineCount": 100,
    "fetchedAt": "2023-10-27T10:00:00.000Z",
    "klines": [
        {
            "openTime": 1698393600000 + (i * 900000),
            "open": str(40000 + i * 10),
            "high": str(40100 + i * 10),
            "low": str(39900 + i * 10),
            "close": str(40000 + i * 15),
            "volume": "100.5",
            "closeTime": 1698394499999 + (i * 900000),
            "quoteVolume": "4020000",
            "trades": 1500,
            "takerBuyBaseVolume": "50.25",
            "takerBuyQuoteVolume": "2010000",
        }
        for i in range(100)
    ],
}


class TestIngestAPI:
    """Test suite for n8n ingestion endpoint"""

    def test_ingest_analyze_success(self):
        """Test successful analysis of n8n kline data."""
        # Create sample data with sufficient variation for RSI calculation
        sample_data = {
            "symbol": "BTCUSDT",
            "interval": "15m",
            "limit": 100,
            "currentPrice": "42000.50",
            "klineCount": 100,
            "fetchedAt": "2023-10-27T10:00:00.000Z",
            "klines": [
                {
                    "openTime": 1698393600000 + (i * 900000),
                    "open": str(40000 + i * 15),
                    "high": str(40100 + i * 15),
                    "low": str(39900 + i * 15),
                    "close": str(40000 + (i % 2) * 50 + i * 15),  # Add some variation
                    "volume": "100.5",
                    "closeTime": 1698394499999 + (i * 900000),
                    "quoteVolume": "4020000",
                    "trades": 1500,
                    "takerBuyBaseVolume": "50.25",
                    "takerBuyQuoteVolume": "2010000",
                }
                for i in range(100)
            ],
        }

        response = client.post("/api/ingest/analyze", json={"data": sample_data})

        assert response.status_code == 200
        result = response.json()

        assert result["symbol"] == "BTCUSDT"
        assert result["interval"] == "15m"
        assert "rsi" in result
        assert "macd" in result
        assert "sma" in result
        assert "ema" in result
        assert "recommendation" in result
        assert "current_price" in result
        assert "analysis_timestamp" in result

        # Check EMA structure
        assert "ema_12" in result["ema"]
        assert "ema_26" in result["ema"]
        assert "signal" in result["ema"]
        assert result["ema"]["signal"] in ["BULLISH", "BEARISH", "NEUTRAL"]

        # Check RSI structure
        assert "value" in result["rsi"]
        assert "signal" in result["rsi"]
        assert result["rsi"]["value"] >= 0 and result["rsi"]["value"] <= 100
        assert result["rsi"]["signal"] in ["OVERSOLD", "NEUTRAL", "OVERBOUGHT"]

        # Check MACD structure
        assert "macd_line" in result["macd"]
        assert "signal_line" in result["macd"]
        assert "histogram" in result["macd"]
        assert "signal_type" in result["macd"]
        assert "crossover" in result["macd"]
        assert result["macd"]["signal_type"] in ["BULLISH", "BEARISH", "NEUTRAL"]
        assert result["macd"]["crossover"] in ["ABOVE", "BELOW", "EQUAL"]

    def test_ingest_analyze_with_custom_parameters(self):
        """Test analysis with custom RSI/MACD parameters."""
        # Create sample data with sufficient candles
        sample_data = {
            "symbol": "BTCUSDT",
            "interval": "15m",
            "limit": 100,
            "currentPrice": "42000.50",
            "klineCount": 100,
            "fetchedAt": "2023-10-27T10:00:00.000Z",
            "klines": [
                {
                    "openTime": 1698393600000 + (i * 900000),
                    "open": str(40000 + i * 15),
                    "high": str(40100 + i * 15),
                    "low": str(39900 + i * 15),
                    "close": str(40000 + (i % 2) * 50 + i * 15),
                    "volume": "100.5",
                    "closeTime": 1698394499999 + (i * 900000),
                    "quoteVolume": "4020000",
                    "trades": 1500,
                    "takerBuyBaseVolume": "50.25",
                    "takerBuyQuoteVolume": "2010000",
                }
                for i in range(100)
            ],
        }

        response = client.post(
            "/api/ingest/analyze",
            json={
                "data": sample_data,
                "parameters": {
                    "rsi_period": 10,
                    "macd_fast": 8,
                    "macd_slow": 21,
                    "macd_signal": 5,
                },
            },
        )

        assert response.status_code == 200
        result = response.json()

        assert result["symbol"] == "BTCUSDT"
        assert result["interval"] == "15m"
        assert "rsi" in result
        assert "macd" in result

    def test_ingest_analyze_empty_klines(self):
        """Test error handling for empty kline data."""
        empty_data = {
            **{
                k: v
                for k, v in SAMPLE_KLINE_DATA.items()
                if k != "klines" and k != "klineCount"
            },
            "klines": [],
            "klineCount": 0,
        }

        response = client.post("/api/ingest/analyze", json={"data": empty_data})

        assert response.status_code == 400
        assert "No kline data" in response.json()["detail"]

    def test_ingest_analyze_invalid_parameters(self):
        """Test validation of analysis parameters."""
        sample_data = {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "limit": 100,
            "currentPrice": "42000.50",
            "klineCount": 100,
            "fetchedAt": "2023-10-27T10:00:00.000Z",
            "klines": [
                {
                    "openTime": 1698393600000 + (i * 3600000),
                    "open": str(40000 + i * 15),
                    "high": str(40100 + i * 15),
                    "low": str(39900 + i * 15),
                    "close": str(40000 + (i % 2) * 50 + i * 15),
                    "volume": "100.5",
                    "closeTime": 1698400799999 + (i * 3600000),
                    "quoteVolume": "4020000",
                    "trades": 1500,
                    "takerBuyBaseVolume": "50.25",
                    "takerBuyQuoteVolume": "2010000",
                }
                for i in range(100)
            ],
        }

        response = client.post(
            "/api/ingest/analyze",
            json={
                "data": sample_data,
                "parameters": {
                    "rsi_period": 1  # Should be >= 2
                },
            },
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_ingest_analyze_insufficient_candles(self):
        """Test error when insufficient candles for calculation."""
        # Create sample with fewer than 30 candles
        small_data = {
            **{
                k: v
                for k, v in SAMPLE_KLINE_DATA.items()
                if k != "klines" and k != "klineCount"
            },
            "klines": [
                {
                    "openTime": 1698393600000 + (i * 3600000),
                    "open": "40000",
                    "high": "40100",
                    "low": "39900",
                    "close": f"{40000 + i * 10}",
                    "volume": "100.5",
                    "closeTime": 1698400799999 + (i * 3600000),
                    "quoteVolume": "4020000",
                    "trades": 1500,
                    "takerBuyBaseVolume": "50.25",
                    "takerBuyQuoteVolume": "2010000",
                }
                for i in range(10)
            ],
            "klineCount": 10,
        }

        response = client.post("/api/ingest/analyze", json={"data": small_data})

        # Should return 400 due to insufficient candles for RSI calculation
        assert response.status_code == 400


class TestIngestModels:
    """Test suite for ingest Pydantic models"""

    def test_n8n_kline_model(self):
        """Test N8NKline Pydantic model."""
        from models.ingest_models import N8NKline

        kline = N8NKline(
            openTime=1698393600000,
            open="40000",
            high="40100",
            low="39900",
            close="40050",
            volume="100.5",
            closeTime=1698400799999,
            quoteVolume="4020000",
            trades=1500,
            takerBuyBaseVolume="50.25",
            takerBuyQuoteVolume="2010000",
        )

        assert kline.close == "40050"
        assert kline.openTime == 1698393600000
        assert kline.trades == 1500

    def test_n8n_node_output_model(self):
        """Test N8NNodeOutput Pydantic model."""
        from models.ingest_models import N8NNodeOutput, N8NKline

        kline = N8NKline(
            openTime=1698393600000,
            open="40000",
            high="40100",
            low="39900",
            close="40050",
            volume="100.5",
            closeTime=1698400799999,
            quoteVolume="4020000",
            trades=1500,
            takerBuyBaseVolume="50.25",
            takerBuyQuoteVolume="2010000",
        )

        output = N8NNodeOutput(
            symbol="BTCUSDT",
            interval="1h",
            limit=100,
            klineCount=1,
            klines=[kline],
            fetchedAt="2023-10-27T10:00:00.000Z",
        )

        assert output.symbol == "BTCUSDT"
        assert output.interval == "1h"
        assert len(output.klines) == 1

    def test_analysis_parameters_model(self):
        """Test AnalysisParameters Pydantic model."""
        from models.ingest_models import AnalysisParameters

        params = AnalysisParameters()

        assert params.rsi_period == 14  # Default
        assert params.macd_fast == 12  # Default
        assert params.macd_slow == 26  # Default
        assert params.macd_signal == 9  # Default

        # Test custom values
        custom = AnalysisParameters(
            rsi_period=10, macd_fast=8, macd_slow=21, macd_signal=5
        )

        assert custom.rsi_period == 10


if __name__ == "__main__":
    pytest.main([__file__])
