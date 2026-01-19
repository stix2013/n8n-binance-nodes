import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
import asyncio
import os
from datetime import datetime
import sys
import os

# Add the parent directory to the path so we can import main
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from main import app

client = TestClient(app)


class TestBinanceAPI:
    """Test suite for Binance API endpoint"""

    def setup_method(self):
        """Setup method to run before each test"""
        # Mock environment variable
        self.mock_api_key = "test_api_key_12345"

    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello from FastAPI!"}

    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    @patch.dict(os.environ, {"BINANCE_API_KEY": "test_key"}, clear=False)
    def test_binance_price_success(self):
        """Test successful Binance price fetch with all parameters"""
        # Mock response data from Binance API
        mock_response_data = [
            [
                1704067200000,  # Open time
                "46800.00000000",  # Open price
                "46900.00000000",  # High price
                "46700.00000000",  # Low price
                "46850.00000000",  # Close price
                "125.43210000",  # Volume
                1704067260000,  # Close time
                "5876543.21000000",  # Quote asset volume
                1543,  # Number of trades
                "62.12340000",  # Taker buy base asset volume
                "2908765.43000000",  # Taker buy quote asset volume
                "ignore",  # Ignore
            ]
        ]

        with patch("routes.binance.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            response = client.get(
                "/api/binance/price?symbol=BTCUSDT&interval=1h&limit=1&startdate=20240101&enddate=20240102"
            )

            assert response.status_code == 200
            data = response.json()

            # Verify structure
            assert "symbol" in data
            assert "data" in data
            assert "count" in data

            # Verify symbol
            assert data["symbol"] == "BTCUSDT"

            # Verify data structure
            assert len(data["data"]) == 1
            price_data = data["data"][0]

            # Verify all expected fields
            expected_fields = [
                "open_time",
                "open_price",
                "high_price",
                "low_price",
                "close_price",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_asset_volume",
                "taker_buy_quote_asset_volume",
                "ignore",
            ]

            for field in expected_fields:
                assert field in price_data

            # Verify data types and values
            assert price_data["open_price"] == 46800.0
            assert price_data["high_price"] == 46900.0
            assert price_data["low_price"] == 46700.0
            assert price_data["close_price"] == 46850.0
            assert price_data["volume"] == 125.4321
            assert price_data["number_of_trades"] == 1543

    @patch.dict(os.environ, {"BINANCE_API_KEY": "test_key"}, clear=False)
    def test_binance_price_minimal_params(self):
        """Test Binance price fetch with minimal parameters (symbol only)"""
        mock_response_data = [
            [
                1704067200000,
                "46800.00000000",
                "46900.00000000",
                "46700.00000000",
                "46850.00000000",
                "125.43210000",
                1704067260000,
                "5876543.21000000",
                1543,
                "62.12340000",
                "2908765.43000000",
                "ignore",
            ]
        ]

        with patch("routes.binance.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            response = client.get("/api/binance/price?symbol=ETHUSDT")

            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "ETHUSDT"
            assert data["count"] == 1

    def test_binance_price_missing_api_key(self):
        """Test Binance price fetch when API key is missing"""
        # Ensure no API key in environment
        with patch.dict(os.environ, {}, clear=True):
            response = client.get("/api/binance/price?symbol=BTCUSDT")

            assert response.status_code == 500
            assert "BINANCE_API_KEY not found" in response.json()["detail"]

    @patch.dict(os.environ, {"BINANCE_API_KEY": "test_key"}, clear=False)
    def test_binance_price_api_error(self):
        """Test Binance price fetch when API returns error"""
        with patch("routes.binance.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"msg": "Invalid symbol"}
            mock_response.text.return_value = '{"msg": "Invalid symbol"}'
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            response = client.get("/api/binance/price?symbol=INVALID")

            assert response.status_code == 400
            assert "Invalid symbol" in response.json()["detail"]

    @patch.dict(os.environ, {"BINANCE_API_KEY": "test_key"}, clear=False)
    def test_binance_price_timeout_error(self):
        """Test Binance price fetch when request times out"""
        with patch("routes.binance.httpx.AsyncClient") as mock_client_class:
            from httpx import TimeoutException

            mock_client = AsyncMock()
            mock_client.get.side_effect = TimeoutException("Request timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            response = client.get("/api/binance/price?symbol=BTCUSDT")

            assert response.status_code == 408
            assert "Request timeout" in response.json()["detail"]

    @patch.dict(os.environ, {"BINANCE_API_KEY": "test_key"}, clear=False)
    def test_binance_price_connection_error(self):
        """Test Binance price fetch when connection fails"""
        with patch("routes.binance.httpx.AsyncClient") as mock_client_class:
            from httpx import RequestError

            mock_client = AsyncMock()
            mock_client.get.side_effect = RequestError("Connection failed")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            response = client.get("/api/binance/price?symbol=BTCUSDT")

            assert response.status_code == 503
            assert "Failed to connect to Binance API" in response.json()["detail"]

    def test_binance_price_invalid_date_format(self):
        """Test Binance price fetch with invalid date format"""
        with patch.dict(os.environ, {"BINANCE_API_KEY": "test_key"}, clear=False):
            response = client.get(
                "/api/binance/price?symbol=BTCUSDT&startdate=2024-01-01"
            )

            assert response.status_code == 400
            assert "Date format must be YYYYMMDD" in response.json()["detail"]

    def test_binance_price_invalid_limit_range(self):
        """Test Binance price fetch with invalid limit range"""
        with patch.dict(os.environ, {"BINANCE_API_KEY": "test_key"}, clear=False):
            # Test limit too high
            response = client.get("/api/binance/price?symbol=BTCUSDT&limit=2000")
            assert response.status_code == 422  # FastAPI validation error

            # Test limit too low
            response = client.get("/api/binance/price?symbol=BTCUSDT&limit=0")
            assert response.status_code == 422  # FastAPI validation error

    def test_binance_price_missing_symbol(self):
        """Test Binance price fetch without required symbol parameter"""
        with patch.dict(os.environ, {"BINANCE_API_KEY": "test_key"}, clear=False):
            response = client.get("/api/binance/price")

            assert response.status_code == 422  # FastAPI validation error
            # Should have a validation error for the missing required parameter

    @patch.dict(os.environ, {"BINANCE_API_KEY": "test_key"}, clear=False)
    def test_binance_price_symbol_case_insensitive(self):
        """Test that symbol parameter is case insensitive"""
        mock_response_data = [
            [
                1704067200000,
                "46800.00000000",
                "46900.00000000",
                "46700.00000000",
                "46850.00000000",
                "125.43210000",
                1704067260000,
                "5876543.21000000",
                1543,
                "62.12340000",
                "2908765.43000000",
                "ignore",
            ]
        ]

        with patch("routes.binance.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Test lowercase symbol
            response = client.get("/api/binance/price?symbol=btcusdt")

            assert response.status_code == 200
            data = response.json()

            # Verify that the symbol was converted to uppercase
            assert data["symbol"] == "BTCUSDT"

            # Verify that the API was called with uppercase symbol
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["symbol"] == "BTCUSDT"


class TestDateConversion:
    """Test suite for date conversion functionality"""

    def test_convert_date_format_valid(self):
        """Test successful date format conversion"""
        from utils.date_utils import convert_date_format

        # Test standard date conversion
        result = convert_date_format("20240101")
        expected_timestamp = int(datetime(2024, 1, 1).timestamp() * 1000)
        assert result == str(expected_timestamp)

    def test_convert_date_format_invalid(self):
        """Test invalid date format conversion"""
        from utils.date_utils import convert_date_format

        with pytest.raises(ValueError) as exc_info:
            convert_date_format("2024-01-01")

        assert "Date format must be YYYYMMDD" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            convert_date_format("202401")

        assert "Date format must be YYYYMMDD" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            convert_date_format("invalid")

        assert "Date format must be YYYYMMDD" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])
