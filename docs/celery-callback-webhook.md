# Celery Task Callback Webhook Integration

## Overview

This document describes the webhook endpoint for receiving Celery task completion callbacks from the `crypto-analysis` worker.

## Webhook Endpoint

**URL:** `POST /webhook/celery-callback`

**Full URL (after n8n activation):**
```
http://localhost:5678/webhook/celery-callback
```

## Request Payload Schema

```json
{
  "task_id": "string (required)",
  "task_name": "string (required)",
  "status": "string (required)",
  "symbol": "string (optional)",
  "interval": "string (optional)",
  "result": "object (optional)",
  "error": "string (optional)"
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | string | Yes | Celery task ID (UUID) |
| `task_name` | string | Yes | Name of the task: `train_model`, `run_prediction`, `run_backtest`, `fetch_market_data` |
| `status` | string | Yes | Task status: `SUCCESS`, `FAILURE`, `PENDING`, `STARTED`, `RETRY` |
| `symbol` | string | No | Trading symbol (e.g., `BTCUSDT`) |
| `interval` | string | No | Time interval (e.g., `15m`, `1h`, `4h`) |
| `result` | object | No | Task-specific result data |
| `error` | string | No | Error message if status is `FAILURE` |

## Task-Specific Result Schemas

### train_model

```json
{
  "task_id": "abc-123",
  "task_name": "train_model",
  "status": "SUCCESS",
  "symbol": "ETHUSDT",
  "interval": "15m",
  "result": {
    "model_path": "/app/models/model_ethusdt_15m.joblib",
    "metrics": {
      "train_loss": 0.0234,
      "val_loss": 0.0312,
      "accuracy": 0.8723
    },
    "training_time_seconds": 145.2,
    "epochs": 50,
    "bars_used": 5000
  },
  "error": null
}
```

### run_prediction

```json
{
  "task_id": "def-456",
  "task_name": "run_prediction",
  "status": "SUCCESS",
  "symbol": "ETHUSDT",
  "interval": "15m",
  "result": {
    "signal": "LONG",
    "confidence": 0.78,
    "entry_price": 3245.67,
    "stop_loss": 3200.00,
    "take_profit": 3320.00,
    "rsi": 42.5,
    "macd_histogram": 0.0234,
    "ema_signal": "bullish"
  },
  "error": null
}
```

### run_backtest

```json
{
  "task_id": "ghi-789",
  "task_name": "run_backtest",
  "status": "SUCCESS",
  "symbol": "BTCUSDT",
  "interval": "1h",
  "result": {
    "total_trades": 156,
    "winning_trades": 98,
    "losing_trades": 58,
    "win_rate": 0.628,
    "total_pnl": 2345.67,
    "total_pnl_percent": 23.45,
    "max_drawdown": -456.78,
    "sharpe_ratio": 1.45,
    "avg_trade_pnl": 15.04,
    "best_trade": 234.56,
    "worst_trade": -89.12
  },
  "error": null
}
```

### fetch_market_data

```json
{
  "task_id": "jkl-012",
  "task_name": "fetch_market_data",
  "status": "SUCCESS",
  "symbol": "BTCUSDT",
  "interval": "1h",
  "result": {
    "bars": 1000,
    "data_path": "/app/data/btcusdt_1h_1000.csv",
    "start_time": "2025-01-01T00:00:00Z",
    "end_time": "2025-03-07T00:00:00Z",
    "klines_count": 1000
  },
  "error": null
}
```

### Failure Example

```json
{
  "task_id": "mno-345",
  "task_name": "train_model",
  "status": "FAILURE",
  "symbol": "ETHUSDT",
  "interval": "15m",
  "result": null,
  "error": "Insufficient data: required minimum 500 bars, got 234"
}
```

## Integration with crypto-analysis

Add the callback to your Celery tasks in `crypto-analysis`:

```python
import os
import requests
from celery import Task

class CallbackTask(Task):
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Send callback to n8n after task completes."""
        webhook_url = os.getenv('N8N_WEBHOOK_URL')
        if not webhook_url:
            return
        
        # Extract symbol and interval from args
        symbol = args[0] if args else None
        interval = kwargs.get('interval')
        
        # Build payload
        payload = {
            'task_id': task_id,
            'task_name': self.name,
            'status': status.upper(),
            'symbol': symbol,
            'interval': interval,
            'result': retval if status == 'SUCCESS' else None,
            'error': str(einfo) if status == 'FAILURE' else None
        }
        
        try:
            requests.post(webhook_url, json=payload, timeout=10)
        except requests.RequestException as e:
            print(f"Failed to send callback: {e}")

# Apply to your tasks
@app.task(base=CallbackTask, bind=True)
def train_model(self, symbol, interval='15m', bars=5000, **kwargs):
    # ... existing training logic ...
    return {
        'model_path': output_path,
        'metrics': {'train_loss': 0.02, 'val_loss': 0.03},
        'training_time_seconds': 120.5,
        'epochs': kwargs.get('epochs', 50),
        'bars_used': bars
    }
```

## Environment Variables

Set in `crypto-analysis` environment:

```bash
# n8n webhook URL
N8N_WEBHOOK_URL=http://n8n:5678/webhook/celery-callback
```

## Testing

```bash
# Test webhook manually
curl -X POST http://localhost:5678/webhook/celery-callback \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test-123",
    "task_name": "train_model",
    "status": "SUCCESS",
    "symbol": "BTCUSDT",
    "interval": "15m",
    "result": {"model_path": "/app/models/test.joblib", "metrics": {}},
    "error": null
  }'
```

Expected response:
```json
{
  "received": true,
  "task_id": "test-123",
  "status": "SUCCESS"
}
```
