# TODO: Celery-Based Online Model Training

## Executive Summary

Implement a background task system using Celery to train machine learning models with online Binance market data, leveraging the existing `crypto-analysis` module from `/home/stevan/projects/AI/trader/crypto-analysis`.

---

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   FastAPI   │────▶│   Redis      │────▶│  Celery Worker  │
│   (API)     │◀────│   (Broker)   │◀────│  (Training)     │
└─────────────┘     └──────────────┘     └─────────────────┘
      │                                         │
      │                                         ▼
      │                              ┌─────────────────┐
      │                              │ crypto-analysis │
      │                              │   Module        │
      │                              └─────────────────┘
      ▼                                         │
┌─────────────┐                                 ▼
│  PostgreSQL │                        ┌─────────────────┐
│  (Database) │                        │  Model Storage  │
└─────────────┘                        │  (/app/models)  │
                                       └─────────────────┘
```

---

## Implementation Steps

### 1. Workspace Setup ✓
- [x] Create git worktree at `.worktrees/feat/online-training`
- [ ] Branch: `feat/online-training`
- [ ] Module linking via Docker volumes and PYTHONPATH

### 2. Infrastructure (Docker Compose)
- [ ] Add `redis:7-alpine` service as Celery broker
- [ ] Add `celery-worker` service
  - Image: Re-use `api` image (Python 3.14)
  - Command: `celery -A src.config.celery_app worker --loglevel=info`
  - Networks: `n8n_network`
  - Volumes:
    - `./api:/app` (code sharing)
    - `/home/stevan/projects/AI/trader/crypto-analysis:/libs/crypto-analysis` (module access)
    - `./models:/app/models` (persistence for .joblib files)
  - Environment: `PYTHONPATH=/app/src:/libs/crypto-analysis/src`
- [ ] Update `.env` with Celery configurations:
  - `CELERY_BROKER_URL=redis://redis:6379/0`
  - `CELERY_RESULT_BACKEND=redis://redis:6379/0`

### 3. Backend Dependencies (api/pyproject.toml)
- [ ] Add Celery dependencies:
  - `celery[redis]>=5.3.0`
  - `redis>=5.0.0`
  - `joblib>=1.3.0`
  - `scikit-learn>=1.3.0`
  - `torch>=2.0.0` (for LSTM support in crypto-analysis)

### 4. Celery Implementation (api/src)
- [ ] Create `api/src/config/celery_app.py`
  - Initialize Celery instance with Redis broker/backend
  - Configure task autodiscovery
- [ ] Create `api/src/tasks/__init__.py`
- [ ] Create `api/src/tasks/training.py`
  - Task: `train_online_model(symbol, interval, bars, warmup_bars, sequence_length)`
  - Use `crypto_analysis.online.generator.OnlineSignalGenerator`
  - Fetch data via `BinanceClient` or `crypto_analysis.data.binance`
  - Save model to `/app/models/model_{symbol}_{interval}.joblib`
  - Return training metrics (accuracy, signal count, etc.)

### 5. API Endpoints (api/src/routes)
- [ ] Create `api/src/routes/training.py`
  - `POST /api/training/train` - Trigger background training
    - Payload: `{ symbol, interval, bars, warmup_bars }`
    - Returns: `{ task_id, status: "PENDING" }`
  - `GET /api/training/status/{task_id}` - Check training progress
    - Returns: `{ task_id, status, result?, error? }`
  - `GET /api/training/models` - List available trained models
    - Returns: `[{ symbol, interval, path, created_at, metrics }]`
- [ ] Register router in `api/src/main.py`

### 6. Integration with crypto-analysis Module
- [ ] Ensure worker has access to Binance credentials from `.env`
- [ ] Test `OnlineSignalGenerator` with live Binance data
- [ ] Handle model persistence and loading
- [ ] Create prediction task for inference (optional)

### 7. Testing & Verification
- [ ] Test infrastructure: Redis and Celery Worker start successfully
- [ ] Test task dispatch: Trigger training for `ETHUSDT` (15m, 1000 bars)
- [ ] Test execution: Monitor worker logs for crypto-analysis module loading
- [ ] Test persistence: Verify `.joblib` files created in shared volume
- [ ] Test API endpoints: All training endpoints respond correctly

### 8. Documentation & Cleanup
- [ ] Update `README.md` with Celery worker usage
- [ ] Add environment variable documentation to `.env` example
- [ ] Create example workflow for n8n to trigger training
- [ ] Document model storage structure and cleanup procedures

---

## Technical Decisions

### Result Backend
- **Decision**: Use Redis for both broker and result backend (simplicity)
- **Alternative**: PostgreSQL (more persistent, but adds complexity)

### Hardware Configuration
- **Default**: CPU-only training (sufficient for online learning models)
- **Optional**: GPU pass-through for LSTM training (requires CUDA setup)

### Model Storage
- **Location**: Shared Docker volume `./models:/app/models`
- **Format**: `.joblib` files (compatible with crypto-analysis module)
- **Naming**: `model_{symbol}_{interval}.joblib`

---

## Docker Compose Changes (Planned)

```yaml
# redis
redis:
  image: redis:7-alpine
  container_name: redis
  restart: unless-stopped
  networks:
    - n8n_network
  ports:
    - "6379:6379"
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5

# celery-worker
celery-worker:
  image: api-python:${API_VERSION:-1.5.0}
  build:
    context: .
    dockerfile: dockers/Dockerfile.python
  container_name: celery-worker
  restart: unless-stopped
  networks:
    - n8n_network
  command: celery -A src.config.celery_app worker --loglevel=info
  volumes:
    - ./api:/app
    - /home/stevan/projects/AI/trader/crypto-analysis:/libs/crypto-analysis
    - ./models:/app/models
    - ./.env:/app/.env:ro
  environment:
    - PYTHONPATH=/app/src:/libs/crypto-analysis/src
    - CELERY_BROKER_URL=redis://redis:6379/0
    - CELERY_RESULT_BACKEND=redis://redis:6379/0
  depends_on:
    redis:
      condition: service_healthy
    postgres:
      condition: service_healthy
```

---

## API Endpoint Specifications

### POST /api/training/train
```json
// Request
{
  "symbol": "ETHUSDT",
  "interval": "15m",
  "bars": 5000,
  "warmup_bars": 1000,
  "sequence_length": 60
}

// Response
{
  "task_id": "abc123",
  "status": "PENDING",
  "message": "Training task queued"
}
```

### GET /api/training/status/{task_id}
```json
// Response (Success)
{
  "task_id": "abc123",
  "status": "SUCCESS",
  "result": {
    "symbol": "ETHUSDT",
    "interval": "15m",
    "model_path": "/app/models/model_ethusdt_15m.joblib",
    "signals_generated": 42,
    "training_accuracy": 0.67,
    "duration_seconds": 15.3
  }
}
```

### GET /api/training/models
```json
// Response
[
  {
    "symbol": "ETHUSDT",
    "interval": "15m",
    "path": "/app/models/model_ethusdt_15m.joblib",
    "created_at": "2026-03-03T10:00:00Z",
    "metrics": {
      "signals_generated": 42,
      "training_accuracy": 0.67
    }
  }
]
```

---

## Open Questions

1. **Dependency Management**: Should `crypto-analysis` dependencies (torch, etc.) be added to `api/pyproject.toml` or should the worker use a dedicated Dockerfile?

2. **GPU Support**: Does the current Docker setup support GPU pass-through for LSTM training, or should we default to CPU-only?

3. **Training Schedule**: Should we implement periodic re-training using Celery Beat, or keep it manual via API?

4. **Model Versioning**: Should we version trained models (e.g., `model_ethusdt_15m_v1.joblib`) or overwrite on each training?

---

## References

- `crypto-analysis` module: `/home/stevan/projects/AI/trader/crypto-analysis`
- Training script reference: `crypto-analysis/scripts/train_online.py`
- OnlineSignalGenerator: `crypto-analysis/src/crypto_analysis/online/generator.py`
- Celery Documentation: https://docs.celeryq.dev/
- Existing FastAPI structure: `/api/src/`

---

## Progress Log

| Date | Step | Status | Notes |
|------|------|--------|-------|
| 2026-03-03 | Plan created | ✅ Complete | Plan saved to docs/TODO-celery-online-training.md |
| 2026-03-03 | Git worktree | 🔄 In Progress | Creating worktree at .worktrees/feat/online-training |
| 2026-03-03 | Docker services | ⏳ Pending | Redis + Celery Worker setup |
| 2026-03-03 | Celery config | ⏳ Pending | celery_app.py initialization |
| 2026-03-03 | Training task | ⏳ Pending | Integrate crypto-analysis module |
| 2026-03-03 | API endpoints | ⏳ Pending | Training routes implementation |

---

**Created**: 2026-03-03  
**Author**: AI Assistant  
**Branch**: `feat/online-training`
