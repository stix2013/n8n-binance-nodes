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

    @patch.dict(
        os.environ,
        {"BINANCE_API_KEY": "test_key", "BINANCE_SECRET_KEY": "test_secret"},
        clear=False,
    )
    def test_place_bracket_limit_order_success(self):
        """Test successful Limit + Bracket (OTOCO) order placement"""
        # Mock OTOCO response from Binance
        mock_otoco_response = {
            "orderListId": 12345,
            "contingencyType": "OTO",
            "listStatusType": "EXEC_STARTED",
            "listOrderStatus": "EXECUTING",
            "listClientOrderId": "test_list_1",
            "transactionTime": 1704067200000,
            "symbol": "BTCUSDT",
            "orders": [
                {"symbol": "BTCUSDT", "orderId": 1, "clientOrderId": "entry"},
                {"symbol": "BTCUSDT", "orderId": 2, "clientOrderId": "tp"},
                {"symbol": "BTCUSDT", "orderId": 3, "clientOrderId": "sl"},
            ],
        }

        # We need to mock OrderResponse structure compatibility
        # Since our code returns OrderResponse(**response.json()),
        # but OTOCO returns a list structure, we modified OrderResponse to handle optional fields.
        # But wait, OrderResponse has mandatory fields like 'symbol', 'status', 'side', 'type'.
        # OTOCO response does NOT have status/side/type at top level usually.
        # Let's check my implementation in binance.py...
        # "return OrderResponse(**response.json())"

        # If the Binance OTOCO response doesn't match OrderResponse, pydantic will error.
        # OTOCO response: { "orderListId": ..., "orders": [...] }
        # OrderResponse needs: symbol, orderId, clientOrderId...
        #
        # I need to fix binance.py logic for OTOCO return first!
        # The OTOCO response is different from a single Order response.
        pass

    @patch.dict(
        os.environ,
        {"BINANCE_API_KEY": "test_key", "BINANCE_SECRET_KEY": "test_secret"},
        clear=False,
    )
    def test_place_bracket_limit_order_success(self):
        """Test successful Limit + Bracket (OTOCO) order placement"""
        # Mock OTOCO response from Binance
        mock_otoco_response = {
            "orderListId": 12345,
            "contingencyType": "OTO",
            "listStatusType": "EXEC_STARTED",
            "listOrderStatus": "EXECUTING",
            "listClientOrderId": "test_list_1",
            "transactionTime": 1704067200000,
            "symbol": "BTCUSDT",
            "orders": [
                {"symbol": "BTCUSDT", "orderId": 1, "clientOrderId": "entry"},
                {"symbol": "BTCUSDT", "orderId": 2, "clientOrderId": "tp"},
                {"symbol": "BTCUSDT", "orderId": 3, "clientOrderId": "sl"},
            ],
        }

        with patch("routes.binance.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_otoco_response
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            order_data = {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "LIMIT",
                "quantity": 0.01,
                "price": 40000.0,
                "takeProfitPrice": 45000.0,
                "stopLossPrice": 35000.0,
                "stopLossType": "MARKET",
            }

            response = client.post("/api/binance/order", json=order_data)

            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "BTCUSDT"
            assert data["orderListId"] == 12345
            assert data["contingencyType"] == "OTO"
            assert len(data["orders"]) == 3

            # Verify parameters
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            params = call_args[1]["params"]
            assert params["workingType"] == "LIMIT"
            assert params["pendingSide"] == "SELL"
            assert float(params["workingPrice"]) == 40000.0
            assert float(params["pendingPrice"]) == 45000.0
            assert float(params["pendingStopPrice"]) == 35000.0

    @patch.dict(
        os.environ,
        {"BINANCE_API_KEY": "test_key", "BINANCE_SECRET_KEY": "test_secret"},
        clear=False,
    )
    def test_place_bracket_market_order_success(self):
        """Test successful Market + Bracket (Sequential) order placement"""
        # Mock responses
        mock_entry_response = {
            "symbol": "BTCUSDT",
            "orderId": 100,
            "clientOrderId": "entry",
            "transactTime": 1704067200000,
            "price": "0.00000000",
            "origQty": "0.01000000",
            "executedQty": "0.01000000",
            "status": "FILLED",
            "type": "MARKET",
            "side": "BUY",
        }

        mock_oco_response = {
            "orderListId": 999,
            "contingencyType": "OCO",
            "listStatusType": "EXEC_STARTED",
            "listOrderStatus": "EXECUTING",
            "listClientOrderId": "oco_list",
            "transactionTime": 1704067200000,
            "symbol": "BTCUSDT",
            "orders": [],
        }

        with patch("routes.binance.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()

            # Setup sequential side effects for post calls
            # 1. Market Entry
            resp1 = MagicMock()
            resp1.status_code = 200
            resp1.json.return_value = mock_entry_response

            # 2. OCO Exit
            resp2 = MagicMock()
            resp2.status_code = 200
            resp2.json.return_value = mock_oco_response

            mock_client.post.side_effect = [resp1, resp2]
            mock_client_class.return_value.__aenter__.return_value = mock_client

            order_data = {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "MARKET",
                "quantity": 0.01,
                "takeProfitPrice": 45000.0,
                "stopLossPrice": 35000.0,
                "stopLossType": "LIMIT",
                "stopLossLimitPrice": 34900.0,
            }

            response = client.post("/api/binance/order", json=order_data)

            assert response.status_code == 200
            data = response.json()
            assert data["orderId"] == 100
            assert data["status"] == "FILLED"
            # We injected orderListId from OCO
            assert data["orderListId"] == 999
            assert data["contingencyType"] == "OCO"

            assert mock_client.post.call_count == 2

            # Verify OCO params
            oco_call_args = mock_client.post.call_args_list[1]
            params = oco_call_args[1]["params"]
            assert params["side"] == "SELL"  # Opposite of entry
            assert float(params["quantity"]) == 0.01
            assert float(params["price"]) == 45000.0
            assert float(params["stopPrice"]) == 35000.0
            assert float(params["stopLimitPrice"]) == 34900.0
