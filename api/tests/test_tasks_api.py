import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def client():
    return TestClient(app)

@patch("src.services.celery_client.celery_client.app.send_task")
def test_fetch_market_data_endpoint(mock_send_task, client):
    """Test the fetch-market-data endpoint triggers a Celery task."""
    # Mock the return value of send_task
    mock_result = MagicMock()
    mock_result.id = "test-task-id"
    mock_send_task.return_value = mock_result
    
    response = client.post(
        "/api/tasks/fetch-market-data",
        json={"symbol": "BTCUSDT", "interval": "1h", "bars": 100}
    )
    
    assert response.status_code == 200
    assert response.json() == {
        "task_id": "test-task-id",
        "status_url": "/api/tasks/test-task-id"
    }
    
    # Verify send_task was called with correct arguments
    mock_send_task.assert_called_once_with(
        "fetch_market_data",
        args=["BTCUSDT", "1h", 100],
        kwargs={}
    )

@patch("src.services.celery_client.celery_client.app.send_task")
def test_train_model_endpoint(mock_send_task, client):
    """Test the train-model endpoint triggers a Celery task."""
    mock_result = MagicMock()
    mock_result.id = "train-task-id"
    mock_send_task.return_value = mock_result
    
    response = client.post(
        "/api/tasks/train-model",
        json={
            "symbol": "ETHUSDT",
            "interval": "15m",
            "bars": 5000,
            "warmup_bars": 1000,
            "sequence_length": 60
        }
    )
    
    assert response.status_code == 200
    assert response.json()["task_id"] == "train-task-id"
    
    mock_send_task.assert_called_once_with(
        "train_model",
        args=["ETHUSDT"],
        kwargs={
            "interval": "15m",
            "bars": 5000,
            "warmup_bars": 1000,
            "sequence_length": 60
        }
    )

@patch("src.services.celery_client.celery_client.app.AsyncResult")
def test_get_task_status_endpoint(mock_async_result, client):
    """Test the get task status endpoint."""
    mock_result = MagicMock()
    mock_result.status = "SUCCESS"
    mock_result.ready.return_value = True
    mock_result.successful.return_value = True
    mock_result.result = {"accuracy": 0.85}
    mock_async_result.return_value = mock_result
    
    response = client.get("/api/tasks/some-task-id")
    
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "some-task-id"
    assert data["status"] == "SUCCESS"
    assert data["ready"] is True
    assert data["successful"] is True
    assert data["result"] == {"accuracy": 0.85}


@patch("src.routes.tasks.task_service.save_task_result")
def test_celery_callback_webhook(mock_save_result, client):
    """Test the celery callback webhook endpoint."""
    mock_save_result.return_value = True
    
    payload = {
        "task_id": "test-webhook-id",
        "task_name": "train_model",
        "status": "SUCCESS",
        "symbol": "BTCUSDT",
        "interval": "15m",
        "result": {"accuracy": 0.92},
        "error": None
    }
    
    response = client.post("/api/tasks/webhook/celery-callback", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {
        "received": True,
        "task_id": "test-webhook-id",
        "status": "SUCCESS"
    }
    
    mock_save_result.assert_called_once_with(
        task_id="test-webhook-id",
        task_name="train_model",
        status="SUCCESS",
        symbol="BTCUSDT",
        interval="15m",
        result={"accuracy": 0.92},
        error=None
    )
