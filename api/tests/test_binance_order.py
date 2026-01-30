import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
import os
import sys

# Add the parent directory to the path so we can import main
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from main import app

client = TestClient(app)


class TestBinanceOrder:
    """Test suite for Binance Order endpoint"""

    @patch.dict(
        os.environ,
        {"BINANCE_API_KEY": "test_key", "BINANCE_SECRET_KEY": "test_secret"},
        clear=False,
    )
    def test_place_market_order_success(self):
        """Test successful market order placement"""
        mock_order_response = {
            "symbol": "BTCUSDT",
            "orderId": 12345678,
            "clientOrderId": "test_order_1",
            "transactTime": 1704067200000,
            "price": "0.00000000",
            "origQty": "0.01000000",
            "executedQty": "0.01000000",
            "status": "FILLED",
            "type": "MARKET",
            "side": "BUY",
        }

        with patch("routes.binance.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_order_response
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            order_data = {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "MARKET",
                "quantity": 0.01,
            }

            response = client.post("/api/binance/order", json=order_data)

            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "BTCUSDT"
            assert data["orderId"] == 12345678
            assert data["status"] == "FILLED"
            assert data["side"] == "BUY"

    @patch.dict(
        os.environ,
        {"BINANCE_API_KEY": "test_key", "BINANCE_SECRET_KEY": "test_secret"},
        clear=False,
    )
    def test_place_limit_order_success(self):
        """Test successful limit order placement"""
        mock_order_response = {
            "symbol": "BTCUSDT",
            "orderId": 87654321,
            "clientOrderId": "test_limit_1",
            "transactTime": 1704067200000,
            "price": "45000.00000000",
            "origQty": "0.01000000",
            "executedQty": "0.00000000",
            "status": "NEW",
            "type": "LIMIT",
            "side": "SELL",
        }

        with patch("routes.binance.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_order_response
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            order_data = {
                "symbol": "BTCUSDT",
                "side": "SELL",
                "type": "LIMIT",
                "quantity": 0.01,
                "price": 45000.0,
            }

            response = client.post("/api/binance/order", json=order_data)

            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "BTCUSDT"
            assert data["type"] == "LIMIT"
            assert data["price"] == 45000.0
            assert data["status"] == "NEW"

    @patch.dict(
        os.environ,
        {"BINANCE_API_KEY": "test_key", "BINANCE_SECRET_KEY": "test_secret"},
        clear=False,
    )
    def test_place_order_api_error(self):
        """Test order placement when Binance returns an error"""
        with patch("routes.binance.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"msg": "Insufficient balance"}
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            order_data = {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "MARKET",
                "quantity": 100.0,
            }

            response = client.post("/api/binance/order", json=order_data)

            assert response.status_code == 400
            assert "Insufficient balance" in response.json()["detail"]

    def test_place_order_missing_keys(self):
        """Test order placement when API keys are missing"""
        with patch.dict(os.environ, {}, clear=True):
            order_data = {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "MARKET",
                "quantity": 0.01,
            }
            response = client.post("/api/binance/order", json=order_data)
            # Should fail with 500 because get_binance_api_key dependency fails
            assert response.status_code == 500
            assert "BINANCE_API_KEY not found" in response.json()["detail"]
