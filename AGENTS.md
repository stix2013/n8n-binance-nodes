# Agent Development Guidelines

Essential guidelines for agentic coding agents in this repository.

## Development Environment

### Prerequisites
- **Python**: >=3.13.9 (API)
- **Node.js**: n8n 2.4.4
- **Docker & Docker Compose**: Containerized development
- **Virtual Environment**: `source .venv/bin/activate`

### Package Managers
- **BunJS**: `bun install`, `bun add <package>`, `bun run <script>`
- **uv**: `uv venv`, `uv pip install -e .[dev]`, `uv run pytest`

### Key Technologies
- **API**: FastAPI, Pydantic v2, httpx, uvicorn
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Database**: PostgreSQL 16
- **Analysis**: numpy, pandas

## Build/Lint/Test Commands

### API Commands (from `/api/` directory)
```bash
# Setup and run API server
source .venv/bin/activate && pip install -e .[dev]
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
python -m pytest
python -m pytest tests/test_binance_api.py
python -m pytest tests/test_technical_indicators.py
python -m pytest --cov=src --cov-report=html
```

### Docker Commands
```bash
docker compose up --build
docker compose up api
docker compose logs -f api
docker compose restart api
```

## Code Style Guidelines

### Python Style (Pydantic v2 + FastAPI)

#### Imports
```python
from datetime import datetime
from typing import List, Optional, Dict
from fastapi import FastAPI, APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
import httpx
import numpy as np
```

#### Naming Conventions
- **Files**: lowercase_with_underscores
- **Classes**: PascalCase
- **Functions/variables**: snake_case
- **Constants**: UPPER_CASE
- **Private**: leading underscore

#### Pydantic Models (v2)
```python
class PriceRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    limit: int = Field(default=50, ge=1, le=1000)
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        return v.upper() if v.isalnum() else ValueError('Invalid symbol')
```

#### FastAPI Routes
```python
@router.get("/price", response_model=PriceResponse)
async def get_binance_price(symbol: str = Query(...)) -> PriceResponse:
    try:
        data = await fetch_price_data(symbol)
        return PriceResponse(symbol=symbol, data=data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
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
    raise HTTPException(status_code=503, detail=f"Service unavailable")
```

#### Async/Await Patterns
```python
async with httpx.AsyncClient() as client:
    response = await client.get(url, timeout=30.0)
    data = response.json()
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

## Pydantic Type Checking Implementation

The Python API uses comprehensive Pydantic v2 type checking for runtime validation, type safety, and automatic API documentation.

### Key Components

#### Pydantic Models (`src/models/api_models.py`)
- **PriceRequest**: Validates request parameters with custom validation rules
- **PriceResponse**: Structured response model for API outputs
- **PriceDataPoint**: Individual price data point model
- **ErrorResponse**: Standardized error response format
- **IntervalEnum**: Enum for valid Binance kline intervals

#### Settings Management (`src/models/settings.py`)
- **Settings**: Pydantic settings class for environment configuration
- Centralized configuration management with type validation
- Support for environment variables and .env files

### Validation Features

- **Symbol validation**: Only alphanumeric characters allowed
- **Date format validation**: Must be in YYYYMMDD format
- **Limit range validation**: Must be between 1-1000
- **Interval validation**: Must be valid Binance kline interval

### Usage Example
```python
# Valid request - automatically passes validation
GET /api/binance/price?symbol=BTCUSDT&interval=1h&limit=100

# Invalid request - returns HTTP 422 with detailed error
GET /api/binance/price?symbol=BTC-USDT&interval=invalid
# Returns: {"detail": "Symbol must contain only alphanumeric characters"}
```

## Docker Best Practices

### Health Checks
```yaml
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### Environment Variables
```yaml
environment:
  - PYTHONUNBUFFERED=1
  - BINANCE_API_KEY=${BINANCE_API_KEY}
volumes:
  - ./.env:/app/.env:ro
```

## Environment Configuration

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

### Development vs Production
- **Development**: Use `docker compose up --build`
- **Production**: Use `docker compose up -d` (detached mode)
- **Debugging**: Use `docker compose logs -f service_name`

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

## Security Guidelines

### Dotfile Access Rule
- **Agents are always allowed to read the `.env` file** at the project root
- The `.env` file contains non-sensitive configuration like versions, ports, and feature flags
- API keys and secrets (BINANCE_API_KEY, N8N_BASIC_AUTH_PASSWORD, etc.) are NOT secrets - they are test/dev credentials stored in plaintext for local development convenience

### API Security
- Validate all inputs with Pydantic models
- Use environment variables for secrets
- Implement proper error handling (no sensitive data in errors)

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

## Troubleshooting

### Common Issues
1. **Port conflicts**: Check if port 8000 or 5678 is already in use
2. **Environment variables**: Ensure `.env` file exists and is properly formatted
3. **Import errors**: Check Python path and virtual environment activation
4. **Docker issues**: Use `docker compose down && docker compose up --build`
5. **Timestamp errors**: Ensure using candle timestamp, not price value
6. **Insufficient data**: Technical indicators require minimum 30 candles

### Debug Commands
```bash
# Check service health
docker compose ps

# View real-time logs
docker compose logs -f

# Check environment
docker compose exec api env | grep BINANCE

# Test API endpoint
curl http://localhost:8000/health

# Test indicators API
curl "http://localhost:8000/api/indicators/analysis?symbol=SOLUSDT&interval=1h"

# Test technical indicators calculations
cd api && source .venv/bin/activate && python demo_indicators.py
```

## FastAPI Docker Best Practices

### Logging Configuration

The API uses structured JSON logging for production environments.

**Log Level**: Configurable via `API_LOG_LEVEL` environment variable (default: INFO)

**Log Viewing:**
```bash
# View all API logs
docker compose logs -f api

# View last 100 lines
docker compose logs --tail=100 api

# View JSON formatted logs
docker compose logs api | jq
```

### Docker Configuration

**Production Settings:**
- Restart policy: `unless-stopped`
- Volumes mounted read-only (`:ro`)
- Resource limits: 2 CPU, 1GB memory
- Non-root user (appuser, uid 1000)

**Resource Monitoring:**
```bash
# Check container health
docker compose ps api

# Check resource usage
docker stats api
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ENVIRONMENT` | development | Environment name (development, production) |
| `PYTHONUNBUFFERED` | 1 | Disable Python output buffering |

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
- **v0.5.0**: n8n custom node development with BinanceKline node
- **v0.4.1**: Structured JSON logging system and Docker production best practices
- **v0.3.0**: Technical indicators (RSI, MACD) with comprehensive API
- **v0.2.0**: Pydantic type checking and health checks
- **v0.1.0**: Initial FastAPI implementation with Binance price endpoint

## n8n Custom Node Development

### Node Location
Custom n8n community nodes are located in:
```
nodes/@stix/
├── n8n-nodes-binance-kline/     # Main node package
│   ├── nodes/                   # Node implementation
│   ├── credentials/             # Credential types
│   ├── icons/                   # Node icons
│   └── package.json             # Node package config
```

### Node Development Commands

#### Build and Lint
```bash
# Navigate to node package
cd nodes/@stix/n8n-nodes-binance-kline

# Install dependencies
bun install

# Build TypeScript
bun run build

# Lint code
npx eslint . --ext .ts --config eslint.config.mjs
```

#### Test in n8n
```bash
# Restart n8n to pick up changes
docker compose restart n8n

# View n8n logs
docker logs n8n-main --tail 50 -f

# Access n8n UI
# http://localhost:5678
# Credentials: user / password123
```

### Node Compliance Checklist

- [ ] Package name follows `n8n-nodes-<name>` or `@scope/n8n-nodes-<name>`
- [ ] `package.json` includes `n8n` section with `nodes` and `credentials`
- [ ] `main` field in `package.json` points to built JS entry point
- [ ] Credentials use `typeOptions: { password: true }` for secret fields
- [ ] Credentials include `documentationUrl` property
- [ ] Authentication uses correct header format (e.g., `X-MBX-APIKEY` for Binance)
- [ ] Icons exist in package root (n8n copies to dist during build)
- [ ] Code passes linting with eslint.config.mjs

### Credentials Configuration

Binance API credentials use custom header authentication:

```typescript
authenticate: {
    type: 'generic',
    properties: {
        headers: {
            'X-MBX-APIKEY': '={{$credentials.apiKey}}'
        }
    }
}
```

### Docker Volume Mount

Mount the entire node package (not just dist/) for npm install compatibility:

```yaml
volumes:
  - ./nodes/@stix/n8n-nodes-binance-kline:/home/node/.n8n/custom/n8n-nodes-binance-kline
```
