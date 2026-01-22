# FastAPI Docker Production Readiness - TODO

## Overview
Transform the FastAPI container into a production-ready service with enhanced logging, stability, and monitoring.

## Target Configuration
- **Log Level**: INFO (configurable via `API_LOG_LEVEL` environment variable)
- **Log Persistence**: Stdout only (captured by Docker daemon)
- **Workers**: Auto-configured (CPU × 2 + 1)
- **Request Logging**: Errors only (4xx and 5xx responses)
- **Python Version**: 3.13 (no changes)

---

## Task List

### Phase 1: Docker & Server Configuration

#### 1.1 Update Dockerfile (`dockers/Dockerfile.python`)
- [ ] Add system dependencies (curl for health checks)
- [ ] Create non-root user (appuser, uid 1000) for security
- [ ] Set proper permissions for /app directory
- [ ] Switch to non-root user

### Phase 2: Logging System

#### 2.1 Create Logging Configuration Module
- [ ] Create directory `api/src/config/`
- [ ] Create `api/src/config/__init__.py`
- [ ] Create `api/src/config/logging_config.py`
- [ ] Implement `JSONFormatter` class for structured logs
- [ ] Create `setup_logging()` function with configuration:
  - Root logger with configurable level
  - Console handler (stdout) for INFO and above
  - JSON formatter for structured output
  - Uvicorn access logger (ERROR level only)
  - Reduce noise from third-party loggers (httpx, httpcore, urllib3)

#### 2.2 Create Request Logging Middleware
- [ ] Create directory `api/src/middleware/`
- [ ] Create `api/src/middleware/__init__.py`
- [ ] Create `api/src/middleware/logging_middleware.py`
- [ ] Implement `ErrorLoggingMiddleware` class:
  - Log only 4xx and 5xx responses
  - Log exceptions with full stack traces
  - Include request details (method, path, query params, user agent)
  - Include response details (status code, process time)
  - Use JSON format for all logs

### Phase 3: Application Updates

#### 3.1 Update Main Application (`api/src/main.py`)
- [ ] Import new modules:
  - `setup_logging` from `config.logging_config`
  - `ErrorLoggingMiddleware` from `middleware.logging_middleware`
- [ ] Call `setup_logging(settings.log_level)` early in startup
- [ ] Implement `lifespan()` context manager:
  - Log startup event with environment
  - Log shutdown event
- [ ] Add `lifespan=lifespan` to FastAPI initialization
- [ ] Register middleware: `app.add_middleware(ErrorLoggingMiddleware)`

### Phase 4: Docker Compose Updates

#### 4.1 Update `docker-compose.yml` (API Section)
- [ ] Update image version to `api-python3.13:0.4.0`
- [ ] Change restart policy to `unless-stopped`
- [ ] Add environment variables:
  - `API_LOG_LEVEL=${API_LOG_LEVEL:-INFO}`
- [ ] Update volumes:
  - Change source mount to read-only (`:ro`)
- [ ] Add `deploy` section with resource limits:
  - `limits: cpus: '2', memory: 1G`
  - `reservations: cpus: '0.5', memory: 512M`

#### 4.2 Update Environment Variables (`.env`)
- [ ] Add new environment variables:
  ```
  API_LOG_LEVEL=INFO
  ENVIRONMENT=development
  ```

### Phase 5: Documentation

#### 5.1 Update AGENTS.md
- [ ] Add section "FastAPI Docker Best Practices"
- [ ] Document logging configuration
- [ ] Add troubleshooting commands
- [ ] Add log viewing examples

#### 5.2 Update README.md (if exists)
- [ ] Update deployment instructions
- [ ] Add environment variable documentation
- [ ] Add log monitoring commands

---

## Implementation Order

1. **Phase 1** - Docker & Server Configuration
2. **Phase 2** - Logging System
3. **Phase 3** - Application Updates
4. **Phase 4** - Docker Compose Updates
5. **Phase 5** - Documentation

---

## Testing Checklist

### Docker Build & Run
- [ ] Build image: `docker compose build api`
- [ ] Start container: `dockerr compose up -d api`
- [ ] Check container status: `docker compose ps api`
- [ ] Verify health check: `docker inspect --format='{{.State.Health.Status}}' api`

### API Functionality
- [ ] Test root endpoint: `curl http://localhost:8000/`
- [ ] Test health check: `curl http://localhost:8000/health`
- [ ] Test Binance price endpoint: `curl "http://localhost:8000/api/binance/price?symbol=BTCUSDT&interval=1h&limit=50"`
- [ ] Test technical indicators endpoint: `curl "http://localhost:8000/api/indicators/analysis?symbol=BTCUSDT&interval=1h"`

### Logging Verification
- [ ] Verify logs are JSON formatted
- [ ] Verify successful requests are NOT logged (per requirements)
- [ ] Verify error requests ARE logged (test with invalid params)
- [ ] Verify startup/shutdown logs are present
- [ ] Check log level can be changed via `API_LOG_LEVEL`
- [ ] View logs: `docker-compose logs -f api`

### Error Handling
- [ ] Test with invalid symbol (should log error)
- [ ] Test with invalid interval (should log error)
- [ ] Test with missing API key (should log error)
- [ ] Verify log includes stack traces for exceptions
- [ ] Verify log includes request details (method, path, timing)

### Resource Limits
- [ ] Verify memory limit is enforced
- [ ] Verify CPU limit is respected
- [ ] Monitor resource usage: `docker stats api`

---

## Log Examples

### Startup Log
```json
{
  "timestamp": "2025-01-21T10:00:00.000Z",
  "level": "INFO",
  "logger": "__main__",
  "message": "API starting up",
  "module": "main",
  "function": "lifespan",
  "line": 28,
  "extra": {
    "event": "startup",
    "message": "API starting up",
    "environment": "production"
  }
}
```

### Error Request Log
```json
{
  "timestamp": "2025-01-21T10:30:45.123Z",
  "level": "ERROR",
  "logger": "api.request",
  "message": "Request failed",
  "module": "logging_middleware",
  "function": "_log_error",
  "line": 42,
  "extra": {
    "type": "request_error",
    "method": "GET",
    "path": "/api/binance/price",
    "query_params": "symbol=BTCUSDT&interval=invalid",
    "status_code": 422,
    "client_host": "172.18.0.1",
    "process_time_ms": 12.45,
    "user_agent": "curl/7.81.0"
  }
}
```

---

## Troubleshooting Commands

```bash
# View all API logs
docker compose logs -f api

# View logs since a specific time
docker compose logs -f api --since="2025-01-21T10:00:00"

# View last 100 lines
docker compose logs --tail=100 api

# Check container health
docker compose ps api
docker inspect --format='{{.State.Health.Status}}' api

# Check worker count
docker compose exec api ps aux | grep gunicorn

# Check resource usage
docker stats api

# Restart API service
docker compose restart api

# Rebuild and start
docker compose up --build -d api

# View detailed container info
docker inspect api

# Enter container for debugging
docker compose exec api sh
```

---

## Migration Notes

### Breaking Changes
- Container will run as non-root user (may affect file permissions)
- Logging format changes to JSON (log parsers may need updates)
- Request logging changed to errors-only (success requests no longer logged)

### Rollback Plan
If issues occur, revert to previous configuration:
1. Restore original `Dockerfile.python`
2. Remove new logging config files
3. Revert changes to `main.py` and `docker-compose.yml`
4. Rebuild: `docker compose up --build api`

---

## Optional Future Enhancements

- [ ] API key authentication middleware
- [ ] Request validation middleware
- [ ] Log aggregation (ELK stack, Loki)
- [ ] Health check with dependency status
- [ ] Graceful shutdown with request draining
