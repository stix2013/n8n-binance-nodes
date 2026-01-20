import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
import asyncio
import os
from datetime import datetime
import sys
import httpx

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from main import app
from routes.binance import get_http_client, get_api_key
from routes.indicators import (
    get_http_client as get_indicators_http_client,
    get_api_key as get_indicators_api_key,
)

client = TestClient(app)


_mock_client = None


def set_mock_client(mock_client):
    """Set the mock client for testing."""
    global _mock_client
    _mock_client = mock_client


async def override_http_client():
    """Override HTTP client for testing."""
    return _mock_client


def override_api_key():
    """Override API key for testing."""
    return "test_api_key_12345"


app.dependency_overrides[get_http_client] = override_http_client
app.dependency_overrides[get_api_key] = override_api_key
app.dependency_overrides[get_indicators_http_client] = override_http_client
app.dependency_overrides[get_indicators_api_key] = override_api_key


class TestBinanceAPI:
    """Test suite for Binance API endpoint"""

    def setup_method(self):
        """Setup method to run before each test"""
        self.mock_api_key = "test_api_key_12345"

    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Hello from" in data["message"]
        assert "n8n Binance API" in data["message"]

    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_binance_price_success(self):
        """Test successful Binance price fetch with all parameters"""
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

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_client.get.return_value = mock_response
        set_mock_client(mock_client)

        response = client.get(
            "/v1/binance/price?symbol=BTCUSDT&interval=1h&limit=1&startdate=20240101&enddate=20240102"
        )

        assert response.status_code == 200
        data = response.json()

        assert "symbol" in data
        assert "data" in data
        assert "count" in data
        assert data["symbol"] == "BTCUSDT"
        assert len(data["data"]) == 1

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

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_client.get.return_value = mock_response
        set_mock_client(mock_client)

        response = client.get("/v1/binance/price?symbol=ETHUSDT")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "ETHUSDT"
        assert data["count"] == 1

    def test_binance_price_missing_api_key(self):
        """Test Binance price fetch when API key is missing"""
        app.dependency_overrides[get_api_key] = lambda: None
        try:
            response = client.get("/v1/binance/price?symbol=BTCUSDT")
            assert response.status_code == 500
            assert "BINANCE_API_KEY" in response.json()["detail"]
        finally:
            app.dependency_overrides[get_api_key] = override_api_key

    def test_binance_price_api_error(self):
        """Test Binance price fetch when API returns error"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"msg": "Invalid symbol"}
        mock_response.text.return_value = '{"msg": "Invalid symbol"}'
        mock_client.get.return_value = mock_response
        set_mock_client(mock_client)

        response = client.get("/v1/binance/price?symbol=INVALID")

        assert response.status_code == 400
        assert "Invalid symbol" in response.json()["detail"]

    def test_binance_price_timeout_error(self):
        """Test Binance price fetch when request times out"""
        from httpx import TimeoutException

        mock_client = AsyncMock()
        mock_client.get.side_effect = TimeoutException("Request timeout")
        set_mock_client(mock_client)

        response = client.get("/v1/binance/price?symbol=BTCUSDT")

        assert response.status_code == 408
        assert "Request timeout" in response.json()["detail"]

    def test_binance_price_connection_error(self):
        """Test Binance price fetch when connection fails"""
        from httpx import RequestError

        mock_client = AsyncMock()
        mock_client.get.side_effect = RequestError("Connection failed")
        set_mock_client(mock_client)

        response = client.get("/v1/binance/price?symbol=BTCUSDT")

        assert response.status_code == 503
        assert "Failed to connect to Binance API" in response.json()["detail"]

    def test_binance_price_invalid_date_format(self):
        """Test Binance price fetch with invalid date format"""
        response = client.get("/v1/binance/price?symbol=BTCUSDT&startdate=2024-01-01")
        assert response.status_code == 422

    def test_binance_price_invalid_limit_range(self):
        """Test Binance price fetch with invalid limit range"""
        response = client.get("/v1/binance/price?symbol=BTCUSDT&limit=2000")
        assert response.status_code == 422

        response = client.get("/v1/binance/price?symbol=BTCUSDT&limit=0")
        assert response.status_code == 422

    def test_binance_price_missing_symbol(self):
        """Test Binance price fetch without required symbol parameter"""
        response = client.get("/v1/binance/price")
        assert response.status_code == 422

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

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_client.get.return_value = mock_response
        set_mock_client(mock_client)

        response = client.get("/v1/binance/price?symbol=btcusdt")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTCUSDT"

    def test_binance_price_invalid_interval(self):
        """Test Binance price fetch with invalid interval"""
        response = client.get("/v1/binance/price?symbol=BTCUSDT&interval=invalid")
        assert response.status_code == 422

    def test_binance_price_symbol_with_special_chars(self):
        """Test Binance price fetch with invalid symbol containing special characters"""
        response = client.get("/v1/binance/price?symbol=BTC-USDT")
        assert response.status_code == 422

    def test_binance_price_invalid_date_value(self):
        """Test Binance price fetch with invalid date value"""
        response = client.get("/v1/binance/price?symbol=BTCUSDT&startdate=20241301")
        assert response.status_code == 422


class TestPydanticModels:
    """Test suite for Pydantic models"""

    def test_price_request_valid(self):
        """Test PriceRequest model with valid data"""
        from models.api_models import PriceRequest, IntervalEnum

        request = PriceRequest(
            symbol="BTCUSDT", interval=IntervalEnum.ONE_HOUR, limit=100
        )

        assert request.symbol == "BTCUSDT"
        assert request.interval == IntervalEnum.ONE_HOUR
        assert request.limit == 100

    def test_price_request_symbol_validation(self):
        """Test PriceRequest symbol validation"""
        from models.api_models import PriceRequest

        request = PriceRequest(symbol="BTCUSDT")
        assert request.symbol == "BTCUSDT"

        request = PriceRequest(symbol="btcusdt")
        assert request.symbol == "BTCUSDT"

        try:
            PriceRequest(symbol="BTC-USDT")
            assert False, "Should have raised ValidationError"
        except Exception:
            pass

    def test_price_request_date_validation(self):
        """Test PriceRequest date format validation"""
        from models.api_models import PriceRequest

        request = PriceRequest(symbol="BTCUSDT", startdate="20240101")
        assert request.startdate == "20240101"

        try:
            PriceRequest(symbol="BTCUSDT", startdate="2024-01-01")
            assert False, "Should have raised ValidationError"
        except Exception:
            pass

        try:
            PriceRequest(symbol="BTCUSDT", startdate="20241301")
            assert False, "Should have raised ValidationError"
        except Exception:
            pass

    def test_price_request_limit_validation(self):
        """Test PriceRequest limit validation"""
        from models.api_models import PriceRequest

        request = PriceRequest(symbol="BTCUSDT", limit=1)
        assert request.limit == 1

        request = PriceRequest(symbol="BTCUSDT", limit=1000)
        assert request.limit == 1000

        try:
            PriceRequest(symbol="BTCUSDT", limit=0)
            assert False, "Should have raised ValidationError"
        except Exception:
            pass

        try:
            PriceRequest(symbol="BTCUSDT", limit=1001)
            assert False, "Should have raised ValidationError"
        except Exception:
            pass

    def test_price_data_point_model(self):
        """Test PriceDataPoint model"""
        from models.api_models import PriceDataPoint
        from datetime import datetime

        data_point = PriceDataPoint(
            open_time=datetime(2024, 1, 1),
            open_price=50000.0,
            high_price=51000.0,
            low_price=49000.0,
            close_price=50500.0,
            volume=1000.0,
            close_time=datetime(2024, 1, 1, 1),
            quote_asset_volume=50000000.0,
            number_of_trades=100,
            taker_buy_base_asset_volume=500.0,
            taker_buy_quote_asset_volume=25000000.0,
            ignore="ignore_value",
        )

        assert data_point.open_price == 50000.0
        assert data_point.volume == 1000.0
        assert data_point.number_of_trades == 100

    def test_interval_enum(self):
        """Test IntervalEnum values"""
        from models.api_models import IntervalEnum

        assert IntervalEnum.ONE_MINUTE.value == "1m"
        assert IntervalEnum.ONE_HOUR.value == "1h"
        assert IntervalEnum.ONE_DAY.value == "1d"
        assert IntervalEnum.ONE_MONTH.value == "1M"

    def test_price_response_model(self):
        """Test PriceResponse model"""
        from models.api_models import PriceResponse, PriceDataPoint
        from datetime import datetime

        data_point = PriceDataPoint(
            open_time=datetime(2024, 1, 1),
            open_price=50000.0,
            high_price=51000.0,
            low_price=49000.0,
            close_price=50500.0,
            volume=1000.0,
            close_time=datetime(2024, 1, 1, 1),
            quote_asset_volume=50000000.0,
            number_of_trades=100,
            taker_buy_base_asset_volume=500.0,
            taker_buy_quote_asset_volume=25000000.0,
            ignore="ignore_value",
        )

        response = PriceResponse(symbol="BTCUSDT", data=[data_point], count=1)

        assert response.symbol == "BTCUSDT"
        assert len(response.data) == 1
        assert response.count == 1


class TestDateConversion:
    """Test suite for date conversion functionality"""

    def test_convert_date_format_valid(self):
        """Test successful date format conversion"""
        from utils.date_utils import convert_date_format

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
