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

### Docker Commands
```bash
# Start all services
docker-compose up --build

# Start specific services
docker-compose up api
docker-compose up task-runners

# View health status
docker-compose ps

# Logs
docker-compose logs api
docker-compose logs -f task-runners

# Restart services
docker-compose restart api
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

#### Type Hints (Required)
```python
from typing import Dict, List, Optional, Tuple

def get_binance_price(symbol: str, interval: str = "1h") -> Dict[str, Any]:
    """Get price with proper type hints."""
    return {"symbol": symbol, "interval": interval}

def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calculate RSI with proper type hints."""
    return float
```

#### Pydantic Models (v2)
```python
from pydantic import BaseModel, Field, field_validator

class PriceRequest(BaseModel):
    """Price request with validation."""
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol")
    limit: int = Field(default=50, ge=1, le=1000, description="Data limit")
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        if not v.isalnum():
            raise ValueError('Symbol must be alphanumeric')
        return v.upper()

class TechnicalIndicators(BaseModel):
    """Technical indicators response model."""
    rsi_value: float = Field(..., ge=0, le=100)
    macd_line: float
    signal_line: float
    histogram: float
```

#### FastAPI Routes
```python
@router.get("/price", response_model=PriceResponse)
async def get_binance_price(
    symbol: str = Query(..., description="Trading symbol"),
    api_key: str = Depends(get_api_key)
) -> PriceResponse:
    """Get price data."""
    try:
        data = await fetch_price_data(symbol)
        return PriceResponse(symbol=symbol, data=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analysis", response_model=TechnicalAnalysisResponse)
async def get_technical_analysis(
    symbol: str = Query(..., description="Trading pair symbol"),
    interval: str = Query(..., description="Candle interval"),
    rsi_period: int = Query(14, ge=2, le=100),
) -> TechnicalAnalysisResponse:
    """Get RSI and MACD analysis."""
    # Implementation
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

#### Async/Await Patterns
```python
async with httpx.AsyncClient() as client:
    response = await client.get(url, timeout=30.0)
    data = response.json()

async def get_binance_api_key() -> str:
    api_key = os.getenv("BINANCE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    return api_key
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

## Troubleshooting

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