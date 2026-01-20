# Agent Development Guidelines

This file provides essential guidelines for agentic coding agents working in this repository.

## Development Environment

### Prerequisites
- **Python**: >=3.13.9 (required for API)
- **Node.js**: For n8n development (n8n 2.4.4)
- **Docker & Docker Compose**: For containerized development
- **Virtual Environment**: Use `source .venv/bin/activate` for API work
- **Package Managers**:
  - **BunJS**: Node.js package manager (preferred over npm/yarn)
  - **uv**: Python package manager (preferred over pip/poetry)

### Package Manager Commands

#### BunJS (Node.js package manager)
```bash
# Install dependencies
bun install

# Add a package
bun add <package_name>

# Add dev dependency
bun add -D <package_name>

# Remove a package
bun remove <package_name>

# Run scripts
bun run <script_name>

# Update packages
bun update

# Check for outdated packages
bun outdated
```

#### uv (Python package manager)
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
uv pip install -e .[dev]

# Add a dependency
uv pip add <package_name>

# Remove a dependency
uv pip remove <package_name>

# Sync dependencies from pyproject.toml
uv pip sync

# Update all packages
uv pip upgrade

# Show installed packages
uv pip list

# Run Python scripts
uv run python script.py

# Run tests
uv run pytest

# Install specific Python version
uv python install 3.13.9
```

### Key Technologies
- **API**: FastAPI, Pydantic v2, uvicorn, httpx
- **Testing**: pytest, pytest-asyncio, pytest-httpx, pytest-cov
- **Database**: PostgreSQL 16
- **Containers**: Docker Compose with health checks
- **Technical Analysis**: numpy, pandas for indicator calculations

## Build/Lint/Test Commands

### API Commands (from `/api/` directory)
```bash
# Setup
source .venv/bin/activate
pip install -e .[dev]  # Install dependencies

# Run API server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
python -m pytest                                    # All tests
python -m pytest tests/test_binance_api.py         # Binance API tests
python -m pytest tests/test_technical_indicators.py  # Technical indicators tests
python -m pytest tests/test_binance_api.py::TestBinanceAPI::test_binance_price_success
python -m pytest tests/test_technical_indicators.py::TestTechnicalIndicators::test_calculate_rsi_valid_data
python -m pytest -v                                 # Verbose output
python -m pytest --cov=src --cov-report=html        # Coverage report

# Run demo scripts
python demo_pydantic.py         # Pydantic validation demo
python demo_indicators.py       # Technical indicators demo
python sol_macd_tool.py         # SOL analysis tool

# Linting (if available)
python -m ruff check src/
python -m ruff format src/
```

### Modern Docker Management Commands

#### Development Workflow
```bash
# Build and start all services
docker-compose up --build --force-recreate

# Start specific services with dependencies
docker-compose up --build api redis postgres

# Development mode with hot reload
docker-compose up --build --watch api

# View real-time logs with follow
docker-compose logs -f --tail=100 api

# Interactive container access
docker-compose exec api /bin/bash
docker-compose exec postgres psql -U postgres -d binance_db

# Database operations
docker-compose exec postgres pg_dump -U postgres binance_db > backup.sql
docker-compose exec postgres psql -U postgres -d binance_db < backup.sql
```

#### Production Deployment
```bash
# Production deployment with health checks
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale services
docker-compose up --scale api=3 --scale task-runners=2 -d

# Rolling updates
docker-compose pull && docker-compose up -d

# Backup and restore
docker-compose exec postgres pg_dump -U postgres binance_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

#### Monitoring and Debugging
```bash
# Resource usage monitoring
docker stats

# Service health status
docker-compose ps

# Inspect specific service
docker-compose inspect api

# Logs with structured output
docker-compose logs --timestamps api

# Network inspection
docker network ls
docker network inspect n8n-binance-nodes_app-network

# Volume management
docker volume ls
docker volume inspect n8n-binance-nodes_redis_data

# Security scanning
docker scout cves n8n-binance-api:latest
```

#### Performance Optimization
```bash
# Multi-stage build optimization
docker build --target builder -t n8n-binance-api:builder .
docker build --target runtime -t n8n-binance-api:latest .

# Image optimization
docker build --compress --no-cache -t n8n-binance-api:latest .

# Resource limits
docker run --cpus=1.0 --memory=512m --memory-swap=1g n8n-binance-api:latest
```

#### CI/CD Integration
```bash
# GitHub Actions / GitLab CI
docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

# Docker Swarm deployment
docker stack deploy -c docker-compose.yml n8n-binance-stack

# Kubernetes deployment
kubectl apply -f k8s/
```

#### Task Runner Container Management
```bash
# From /dockers/task-runner-python/
docker build -t task-runner:latest .
docker run -it --rm task-runner:latest

# With environment variables
docker run -it --rm \
  -e BINANCE_API_KEY=${BINANCE_API_KEY} \
  -e REDIS_URL=${REDIS_URL} \
  task-runner:latest

# Task runner orchestration
docker-compose run --rm task-runner python -m src.main
```

### Task Runner Commands (from `/dockers/task-runner-python/`)
```bash
# Install dependencies
pip install -e .

# Run task runner
python -m src.main

# Test imports
python -m src.import_validation
```

## Code Style Guidelines

### Python Style (Pydantic v2 + FastAPI)

#### Imports
```python
# Standard library
from datetime import datetime
from typing import List, Optional, Tuple
from enum import Enum

# Third-party
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
import httpx
import numpy as np

# Local imports (relative)
from ..utils.date_utils import convert_date_format, timestamp_to_iso
from ..models.api_models import PriceRequest
from ..utils.indicators import TechnicalIndicators
```

#### Naming Conventions
- **Files**: lowercase with underscores (`date_utils.py`, `indicators.py`)
- **Classes**: PascalCase (`PriceRequest`, `BinanceAPI`, `TechnicalIndicators`)
- **Functions/variables**: snake_case (`get_binance_price`, `calculate_rsi`)
- **Constants**: UPPER_CASE (`BINANCE_API_URL`)
- **Private**: leading underscore (`_internal_function`, `_private_var`)

#### Modern Type Hints (Python 3.13+)
```python
from typing import Dict, List, Optional, Tuple, Union, Any, Literal, TypedDict
from datetime import datetime
from dataclasses import dataclass

# Literal types for strict values
PriceInterval = Literal["1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
RSISignal = Literal["OVERSOLD", "NEUTRAL", "OVERBOUGHT"]
RecommendationType = Literal["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]

# TypedDict for structured data
class PriceData(TypedDict):
    """Type-safe price data structure."""
    symbol: str
    price: float
    timestamp: datetime
    interval: PriceInterval
    volume: float

@dataclass
class IndicatorConfig:
    """Configuration for technical indicators."""
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

# Modern function signatures
def get_binance_price(symbol: str, interval: PriceInterval) -> Dict[str, Union[str, Any]]:
    """Get price with modern type hints."""
    return {"symbol": symbol, "interval": interval}

def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calculate RSI with proper type hints."""
    return float

# Return type improvements
async def fetch_price_data(symbol: str) -> PriceData:
    """Fetch price data with structured return type."""
    ...

def analyze_market_data(symbol: str, prices: List[float]) -> Dict[str, Union[float, RSISignal, RecommendationType]]:
    """Analyze market data with multiple return types."""
    ...
```

#### Enhanced Pydantic v2 Models (Modern Patterns)
```python
from pydantic import BaseModel, Field, field_validator, field_serializer
from pydantic import ConfigDict
from datetime import datetime
from decimal import Decimal

class PriceRequest(BaseModel):
    """Price request with enhanced validation."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_to_upper=True,
        extra='forbid',
        validate_assignment=True,
        arbitrary_types_allowed=True
    )
    
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol")
    limit: int = Field(default=50, ge=1, le=1000, description="Data limit")
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError('Symbol must be alphanumeric')
        return v.upper()
    
    @field_serializer('symbol')
    def serialize_symbol(self, value: str) -> str:
        return value.upper()

class TechnicalIndicators(BaseModel):
    """Technical indicators response model with enhanced validation."""
    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }
    )
    
    rsi_value: float = Field(..., ge=0, le=100, description="RSI value (0-100)")
    macd_line: float = Field(..., description="MACD line value")
    signal_line: float = Field(..., description="Signal line value")
    histogram: float = Field(..., description="MACD histogram value")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Advanced model with relationships
class MarketAnalysis(BaseModel):
    """Complete market analysis with nested models."""
    symbol: str
    current_price: Decimal = Field(..., ge=0)
    indicators: TechnicalIndicators
    recommendations: List[RecommendationType]
    confidence_score: float = Field(..., ge=0, le=1)
    
    @field_validator('recommendations')
    @classmethod
    def validate_recommendations(cls, v):
        if not v:
            raise ValueError('At least one recommendation required')
        return v

# Model for API responses with status codes
class APIResponse(BaseModel):
    """Standard API response model."""
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

#### Modern FastAPI Patterns (Enhanced)
```python
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from typing import Annotated, Optional
from enum import Enum

# Enhanced dependency injection
async def get_current_user(authorization: str = Depends(get_bearer_token)):
    """Enhanced dependency for user authentication."""
    try:
        user = await verify_token(authorization)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")

# Annotated types for better documentation
SymbolQuery = Annotated[str, Query(..., min_length=1, max_length=20, description="Trading symbol")]
LimitParam = Annotated[int, Query(50, ge=1, le=1000, description="Data limit")]

@router.get("/price", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def get_binance_price(
    symbol: SymbolQuery,
    current_user: Annotated[dict, Depends(get_current_user)] = None
) -> APIResponse:
    """Get price data with enhanced error handling."""
    try:
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
            
        data = await fetch_price_data(symbol)
        if not data:
            raise HTTPException(status_code=404, detail="Price data not found")
            
        return APIResponse(
            success=True,
            data=data,
            message="Price data retrieved successfully"
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Request timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analysis", response_model=APIResponse)
async def get_technical_analysis(
    symbol: SymbolQuery,
    interval: Annotated[str, Query(..., description="Candle interval")],
    rsi_period: Annotated[int, Query(14, ge=2, le=100)] = 14,
    current_user: Optional[dict] = Depends(get_current_user)
) -> APIResponse:
    """Get RSI and MACD analysis with comprehensive validation."""
    try:
        # Enhanced validation
        if interval not in ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]:
            raise HTTPException(status_code=400, detail="Invalid interval format")
            
        analysis_data = await perform_technical_analysis(symbol, interval, rsi_period)
        
        return APIResponse(
            success=True,
            data=MarketAnalysis(**analysis_data),
            message="Technical analysis completed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis failed")

# Error handling middleware
@router.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """Global error handling middleware."""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": "Internal server error"}
        )
```

#### Error Handling
```python
try:
    result = await fetch_data()
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except httpx.TimeoutException:
    raise HTTPException(status_code=408, detail="Request timeout")
except httpx.RequestError as e:
    raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
```

#### Enhanced Async/Await Patterns
```python
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# Enhanced HTTP client with connection pooling
async def get_binance_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Enhanced async HTTP client with proper cleanup."""
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    timeout = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)
    
    async with httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        headers={"User-Agent": "n8n-binance-api/1.0"}
    ) as client:
        yield client

# Dependency injection with async context
async def get_api_key() -> str:
    """Enhanced API key dependency with caching."""
    api_key = os.getenv("BINANCE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    return api_key

# Concurrent data fetching
async def fetch_multiple_symbols(symbols: List[str]) -> Dict[str, Any]:
    """Fetch data for multiple symbols concurrently."""
    async with get_binance_client() as client:
        tasks = [fetch_symbol_data(client, symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            symbol: result for symbol, result in zip(symbols, results)
            if not isinstance(result, Exception)
        }

# Background task management
async def run_periodic_analysis():
    """Background task for periodic market analysis."""
    while True:
        try:
            await analyze_all_symbols()
            await asyncio.sleep(300)  # 5 minutes
        except Exception as e:
            logger.error(f"Background analysis error: {str(e)}")
            await asyncio.sleep(60)  # Wait 1 minute before retry

@asynccontextmanager
async def lifespan_context(app: FastAPI):
    """Application lifespan management."""
    # Startup
    task = asyncio.create_task(run_periodic_analysis())
    logger.info("Application startup completed")
    
    try:
        yield
    finally:
        # Shutdown
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        logger.info("Application shutdown completed")
```

## File Organization

### API Structure (`/api/src/`)
```
src/
├── main.py              # FastAPI app entry point
├── models/             # Pydantic models
│   ├── __init__.py
│   ├── api_models.py    # Request/response models (PriceRequest, PriceResponse, etc.)
│   ├── indicators.py    # Technical indicators models (RSI, MACD analysis)
│   └── settings.py     # Configuration models
├── routes/             # API route handlers
│   ├── __init__.py
│   ├── binance.py      # Binance API routes (/api/binance/price)
│   └── indicators.py   # Technical indicators routes (/api/indicators/*)
└── utils/              # Utility functions
    ├── __init__.py
    ├── date_utils.py   # Date conversion utilities
    └── indicators.py   # Technical indicators calculations
```

### Technical Indicators Files
```
api/src/utils/indicators.py      # Core calculation engine (RSI, MACD, EMA)
api/src/models/indicators.py     # Pydantic models for indicators API
api/src/routes/indicators.py     # API endpoints for analysis
api/tests/test_technical_indicators.py  # 22 comprehensive tests
api/demo_indicators.py           # Interactive demo script
api/sol_macd_tool.py             # SOL analysis command-line tool
```

### Testing Structure
```
tests/
├── test_binance_api.py          # Binance API endpoint tests (24 tests)
├── test_technical_indicators.py # Technical indicators tests (22 tests)
└── conftest.py                 # Pytest configuration
```

## Technical Indicators Implementation

### Core Indicators
```python
from utils.indicators import TechnicalIndicators

# RSI Calculation
rsi_value = TechnicalIndicators.calculate_rsi(prices, period=14)
rsi_signal = TechnicalIndicators.generate_rsi_signal(rsi_value)
# Returns: "OVERSOLD" (RSI < 30), "NEUTRAL" (30-70), "OVERBOUGHT" (RSI > 70)

# MACD Calculation
macd_data = TechnicalIndicators.calculate_macd(prices, fast=12, slow=26, signal=9)
# Returns: {'macd_line': float, 'signal_line': float, 'histogram': float}

# Combined Analysis
recommendation = TechnicalIndicators.generate_overall_recommendation(
    rsi_signal, macd_signal_type, macd_crossover
)
# Returns: "STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"
```

### API Endpoints
```bash
# Full Analysis (RSI + MACD)
GET /api/indicators/analysis?symbol=BTCUSDT&interval=1h&limit=100

# Single Indicator
GET /api/indicators/rsi?symbol=BTCUSDT&interval=1h&period=14
GET /api/indicators/macd?symbol=BTCUSDT&interval=1h&fast=12&slow=26&signal=9

# Parameters
- symbol: Trading pair (e.g., BTCUSDT, SOLUSDT)
- interval: Timeframe (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
- limit: Number of candles (30-1000, default: 100)
- period: Indicator period (2-100, default: 14 for RSI, 12/26/9 for MACD)
```

### Response Format
```json
{
  "symbol": "SOLUSDT",
  "current_price": 133.86,
  "rsi": {"value": 38.21, "signal": "NEUTRAL"},
  "macd": {"macd_line": -0.92, "signal_line": -1.19, "histogram": 0.27},
  "macd_interpretation": {"signal_type": "BULLISH", "crossover": "ABOVE"},
  "overall_recommendation": "BUY",
  "analysis_timestamp": "2024-01-20T15:00:00",
  "candles_analyzed": 100
}
```

## Modern Docker Best Practices

### Multi-Stage Build Optimization
```dockerfile
# Multi-stage Python API build
FROM python:3.13-slim as builder
WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY api/requirements.txt api/pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .[dev]

# Production stage
FROM python:3.13-slim as runtime
WORKDIR /app

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser api/src/ ./src/
COPY --chown=appuser:appuser api/ ./

# Set security context
USER appuser

# Health check with detailed output
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Security-Focused Docker Compose
```yaml
services:
  api:
    build:
      context: .
      dockerfile: api/Dockerfile
      target: runtime
    security_opt:
      - no-new-privileges:true
    user: "1000:1000"
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
    cap_drop:
      - ALL
    cap_add:
      - SETUID
      - SETGID
    mem_limit: 512m
    mem_reservation: 256m
    cpus: 0.5
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Enhanced Health Checks
```yaml
    healthcheck:
      test: |
        ["CMD", "curl", "-f", "http://localhost:8000/health"]
        ["CMD", "curl", "-f", "http://localhost:8000/api/indicators/analysis?symbol=BTCUSDT&interval=1h"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### Modern Environment Variables Management
```yaml
    environment:
      - PYTHONUNBUFFERED=1
      - PYTHONPATH=/app/src
      - BINANCE_API_KEY_FILE=/run/secrets/binance_api_key
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/binance_db
    secrets:
      - binance_api_key
      - postgres_password
    volumes:
      - ./logs:/app/logs:rw
      - ./cache:/tmp/cache:rw

secrets:
  binance_api_key:
    file: ./secrets/binance_api_key.txt
  postgres_password:
    file: ./secrets/postgres_password.txt
```

### Resource Management and Scaling
```yaml
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M
    scale: 3
    restart_policy:
      condition: on-failure
      delay: 5s
      max_attempts: 3
      window: 120s
```

### Service Dependencies and Networking
```yaml
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
      - monitoring
    links:
      - postgres:db
```

### Service Discovery and Load Balancing
```yaml
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    networks:
      - app-network
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}

volumes:
  redis_data:
    driver: local

networks:
  app-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
  monitoring:
    external: true
```

## Environment Configuration and Secrets Management

### Development vs Production
- **Development**: Use `docker-compose up --build`
- **Production**: Use `docker-compose up -d` (detached mode)
- **Debugging**: Use `docker-compose logs -f service_name`

### Required Environment Variables
```bash
# API Configuration
BINANCE_API_KEY=your_api_key_here
N8N_HOST_PORT=5678
POSTGRES_PASSWORD=your_db_password

# n8n Configuration  
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=password
```

### Modern Environment Management
```yaml
# docker-compose.yml
version: '3.8'

x-common-variables: &common-vars
  PYTHONUNBUFFERED: 1
  LOG_LEVEL: INFO
  ENVIRONMENT: development
  REDIS_DB: 0
  API_RATE_LIMIT: 1000
  HEALTH_CHECK_INTERVAL: 30

services:
  api:
    <<: *common-vars
    environment:
      <<: *common-vars
      DATABASE_URL: postgresql://postgres:password@postgres:5432/binance_dev
      BINANCE_TESTNET: true
      CACHE_TTL: 300
      REQUEST_TIMEOUT: 30
    env_file:
      - .env.development
      - .secrets.env
```

### Production Configuration
```yaml
# docker-compose.prod.yml
version: '3.8'

x-common-variables: &common-vars
  PYTHONUNBUFFERED: 1
  PYTHONPATH: /app/src
  ENVIRONMENT: production
  LOG_LEVEL: WARNING
  REDIS_DB: 1
  API_RATE_LIMIT: 5000
  CACHE_TTL: 600
  REQUEST_TIMEOUT: 60

services:
  api:
    <<: *common-vars
    environment:
      <<: *common-vars
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/binance_prod
      BINANCE_TESTNET: false
      REDIS_URL: redis://redis:6379/1
    secrets:
      - binance_api_key
      - postgres_password
      - jwt_secret
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

### Docker Secrets Management
```bash
# Create secrets
echo "your_api_key_here" | docker secret create binance_api_key -
echo "your_db_password_here" | docker secret create postgres_password -
echo "your_jwt_secret_here" | docker secret create jwt_secret -

# Use secrets in Docker Swarm
docker service create --secret binance_api_key n8n-binance-api:latest
```

### Configuration Management with Consul/etcd
```yaml
# config.yml
api:
  version: 1.0
  services:
    binance_api:
      base_url: ${BINANCE_API_BASE_URL}
      timeout: ${REQUEST_TIMEOUT}
      retries: 3
    redis:
      host: redis
      port: 6379
      db: ${REDIS_DB}
    postgres:
      host: postgres
      port: 5432
      database: ${POSTGRES_DB}
      ssl_mode: ${POSTGRES_SSL_MODE}
```

### Development vs Production
- **Development**: Use `docker-compose up --build`
- **Production**: Use `docker-compose up -d` (detached mode)
- **Debugging**: Use `docker-compose logs -f service_name`

## Testing Guidelines

### Test Structure
```python
class TestTechnicalIndicators:
    """Test suite for technical indicators."""
    
    def test_calculate_rsi_valid_data(self):
        """Test RSI calculation with valid data."""
        prices = [10.0, 10.5, 10.3, 10.8, 11.0] * 10
        rsi = TechnicalIndicators.calculate_rsi(prices, period=14)
        assert 0 <= rsi <= 100
    
    def test_calculate_macd_valid_data(self):
        """Test MACD calculation with valid data."""
        prices = [100.0 + i for i in range(50)]
        macd_result = TechnicalIndicators.calculate_macd(prices)
        assert 'macd_line' in macd_result
        assert 'signal_line' in macd_result
        assert 'histogram' in macd_result

class TestIndicatorsAPI:
    """Test suite for indicators API endpoints."""
    
    def test_analysis_endpoint(self):
        """Test technical analysis endpoint."""
        # Mock Binance API response
        # Test request/response validation
        # Verify response structure
```

### Test Commands
- **All tests**: `python -m pytest`
- **Technical indicators**: `python -m pytest tests/test_technical_indicators.py`
- **Binance API**: `python -m pytest tests/test_binance_api.py`
- **Single test**: `python -m pytest tests/test_technical_indicators.py::TestClass::test_method`
- **Coverage**: `python -m pytest --cov=src --cov-report=term-missing`
- **Async tests**: Use `pytest-asyncio` plugin

## Security Guidelines

### API Security
- Validate all inputs with Pydantic models
- Use environment variables for secrets
- Implement proper error handling (no sensitive data in errors)
- Use HTTPS in production (configured in docker-compose)

### Dependencies
- Pin versions in `pyproject.toml`
- Use `python-dotenv` for local development
- Regular security updates via `pip audit`

## Common Patterns

### Environment-Based Configuration
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    binance_api_key: Optional[str] = None
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### Fallback Imports
```python
try:
    from ..models.api_models import PriceRequest
    from ..utils.indicators import TechnicalIndicators
except ImportError:
    from models.api_models import PriceRequest
    from utils.indicators import TechnicalIndicators
```

### Date Utilities
```python
def convert_date_format(date_str: str) -> str:
    """Convert YYYYMMDD to timestamp."""
    if len(date_str) != 8 or not date_str.isdigit():
        raise ValueError("Date format must be YYYYMMDD")
    timestamp = int(datetime.strptime(date_str, '%Y%m%d').timestamp() * 1000)
    return str(timestamp)
```

### Technical Indicators Pattern
```python
class TechnicalIndicators:
    """Core technical indicator calculations."""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate RSI value (0-100)."""
        
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """Calculate MACD components."""
        
    @staticmethod
    def generate_rsi_signal(rsi_value: float) -> str:
        """Generate RSI signal (OVERSOLD/NEUTRAL/OVERBOUGHT)."""
        
    @staticmethod
    def generate_macd_signal(macd_data: Dict[str, float]) -> Tuple[str, str]:
        """Generate MACD signal (BULLISH/BEARISH/NEUTRAL)."""
        
    @staticmethod
    def generate_overall_recommendation(rsi_signal: str, macd_signal: str, macd_crossover: str) -> str:
        """Generate overall trading recommendation."""
```

## Troubleshooting and Debugging

### Common Issues
1. **Port conflicts**: Check if port 8000 or 5678 is already in use
2. **Environment variables**: Ensure `.env` file exists and is properly formatted
3. **Import errors**: Check Python path and virtual environment activation
4. **Docker issues**: Use `docker-compose down && docker-compose up --build`
5. **Timestamp errors**: Ensure using candle timestamp, not price value
6. **Insufficient data**: Technical indicators require minimum 30 candles

### Debug Commands
```bash
# Check service health
docker-compose ps

# View real-time logs
docker-compose logs -f

# Check environment
docker-compose exec api env | grep BINANCE

# Test API endpoint
curl http://localhost:8000/health

# Test indicators API
curl "http://localhost:8000/api/indicators/analysis?symbol=SOLUSDT&interval=1h"

# Test technical indicators calculations
cd api && source .venv/bin/activate && python demo_indicators.py
```

### Container Debugging
```bash
# Check container status and logs
docker-compose ps
docker-compose logs --tail=50 --follow api

# Resource usage analysis
docker stats --no-stream

# Network connectivity testing
docker-compose exec api ping postgres
docker-compose exec api curl -v redis:6379

# Database connectivity
docker-compose exec postgres psql -U postgres -c "SELECT version();"
docker-compose exec postgres pg_lsclusters

# Redis debugging
docker-compose exec redis redis-cli ping
docker-compose exec redis redis-cli info
```

### Performance Debugging
```bash
# API response times
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/health"

# Memory and CPU profiling
docker exec $(docker-compose ps -q api) python -m cProfile -o profile.prof src/main.py
docker cp $(docker-compose ps -q api):/app/profile.prof ./profile.prof

# Database query analysis
docker-compose exec postgres psql -U postgres -c "SELECT * FROM pg_stat_activity;"
```

### Network Debugging
```bash
# DNS resolution testing
docker-compose exec api nslookup postgres
docker-compose exec api dig postgres

# Port accessibility
docker-compose exec api netstat -tulpn | grep :8000
docker-compose exec postgres netstat -tulpn | grep :5432

# SSL/TLS testing
openssl s_client -connect api:8000 -servername api
```

### Security Debugging
```bash
# Check file permissions
docker-compose exec api ls -la /app/
docker-compose exec api id

# Verify secrets mounting
docker-compose exec api ls -la /run/secrets/
docker-compose exec api cat /run/secrets/binance_api_key

# Container security scanning
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image n8n-binance-api:latest
```

### Log Analysis
```bash
# Structured log parsing
docker-compose logs --tail=100 api | jq .

# Error rate monitoring
docker-compose logs --since=1h api | grep -i error | wc -l

# Performance log analysis
docker-compose logs --since=1h api | grep -E "(duration|latency|time)" | head -20
```

## Performance Considerations

- Use async/await for I/O operations
- Implement proper connection pooling for HTTP clients
- Cache frequently accessed data when appropriate
- Use appropriate timeout values for external API calls
- Monitor memory usage in containerized environment
- Optimize numpy calculations for large datasets
- Consider Redis caching for frequently requested indicators

## Development Workflow

1. **Feature development**: Create feature branch, implement changes, add tests
2. **Testing**: Run full test suite before committing (pytest)
3. **Documentation**: Update CHANGELOG.md and AGENTS.md
4. **Review**: Ensure code follows style guidelines and patterns
5. **Deployment**: Use Docker Compose for consistent deployments
6. **Version bump**: Update version in pyproject.toml and docker-compose.yml

## Version History
- **v0.3.0**: Technical indicators (RSI, MACD) with comprehensive API
- **v0.2.0**: Pydantic type checking and health checks
- **v0.1.0**: Initial FastAPI implementation with Binance price endpoint

## Related Documentation
- **API Improvements**: See [`api/TODO.md`](api/TODO.md) for detailed API improvement tracking, completed tasks, and future enhancements