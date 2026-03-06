# Plan: Enable API to Send Celery Tasks

## Objective
Enable the `api` service in `n8n-binance-nodes` to send tasks to the `worker` service in `trader/crypto-analysis` using Celery. This will allow the API to trigger long-running tasks like model training and backtesting asynchronously.

## Problem
- The `api` service and `worker` service are in different Docker networks (`n8n_network` vs `shared_network`).
- The `api` service cannot resolve the Redis broker used by the worker.
- The `api` service lacks the code to trigger Celery tasks.

## Proposed Solution
1.  **Network Integration**: Connect the `api` service to the `shared_network` so it can communicate with the Redis broker.
2.  **Configuration**: Update `CELERY_BROKER_URL` to point to the correct Redis host (`redis_broker`).
3.  **Implementation**: Add a `CeleryClient` service and a new `/api/tasks` router to the API to expose Celery task triggers.

## Key Files & Context
- `n8n-binance-nodes/docker-compose.yml`: Needs network update.
- `n8n-binance-nodes/api/src/main.py`: Register new router.
- `n8n-binance-nodes/api/src/services/celery_client.py`: New file.
- `n8n-binance-nodes/api/src/routes/tasks.py`: New file.
- `trader/crypto-analysis/CELERY_CLI.md`: Reference for task names.

## Implementation Steps

### 1. Infrastructure Update [DONE]
- **Modify `n8n-binance-nodes/docker-compose.yml`**:
    - Define `shared_network` as an external network.
    - Add `shared_network` to the `api` service's networks.
    - **Verification**: `docker network inspect shared_network` should show the `api` container after restart.

### 2. Service Implementation [DONE]
- **Create `api/src/services/celery_client.py`**:
    - Initialize `Celery` app with `broker_url` from environment.
    - Define a `send_task` helper method.
- **Create `api/src/routes/tasks.py`**:
    - Define Pydantic models for task arguments (e.g., `TrainModelRequest`).
    - Implement endpoints:
        - `POST /api/tasks/fetch-market-data` -> `fetch_market_data`
        - `POST /api/tasks/train-model` -> `train_model`
        - `POST /api/tasks/run-prediction` -> `run_prediction`
        - `POST /api/tasks/run-backtest` -> `run_backtest`
        - `POST /api/tasks/train-and-backtest` -> `train_and_backtest`
    - Return `task_id` and `status_url` (optional).
    - Add `GET /api/tasks/{task_id}` to check task status.

### 3. Integration [DONE]
- **Update `api/src/main.py`**:
    - Import and include `tasks.router`.
- **Update `env-example`**:
    - Ensure `CELERY_BROKER_URL` is documented as `redis://redis_broker:6379/0` (using container name for cross-project reliability).

## Verification Plan
1.  **Network Check**:
    - Restart containers: `docker compose up -d`.
    - Exec into `api` container: `docker compose exec api sh`.
    - Ping redis: `ping redis_broker`.
2.  **Task Trigger Test**:
    - Trigger a task via API: `curl -X POST http://localhost:8000/api/tasks/fetch-market-data ...`
    - Check response: Should return a task ID.
    - Monitor worker logs: `docker logs -f crypto-worker-worker-1` (or similar) to see if task is received.
    - Check task status: `curl http://localhost:8000/api/tasks/{task_id}`.

## Git Worktree
- I will use a git worktree `feat/enable-celery-tasks` for this implementation to ensure isolation.
