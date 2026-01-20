# Agent Development Guidelines

This file provides essential guidelines for agentic coding agents working in this repository.

## Development Environment

### Prerequisites
- **Python**: >=3.13.9 (required for API)
- **Node.js**: For n8n development (n8n 2.4.4)
- **Docker & Docker Compose**: For containerized development
- **Virtual Environment**: Use `source .venv/bin/activate` for API work

### Key Technologies
- **API**: FastAPI, Pydantic v2, uvicorn, httpx
- **Testing**: pytest, pytest-asyncio, pytest-httpx, pytest-cov
- **Database**: PostgreSQL 16
- **Containers**: Docker Compose with health checks

## Build/Lint/Test Commands

### API Commands (from `/api/` directory)
```bash
# Setup
source .venv/bin/activate
pip install -e .[dev]  # Install dependencies

# Run API server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
python -m pytest                    # All tests
python -m pytest tests/test_binance_api.py::TestBinanceAPI::test_binance_price_success
python -m pytest -v                  # Verbose output
python -m pytest --cov=src --cov-report=html  # Coverage report

# Linting (if available)
python -m ruff check src/
python -m ruff format src/

# Pydantic validation demo
python demo_pydantic.py
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
from typing import List, Optional
from enum import Enum

# Third-party
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

# Local imports (relative)
from ..utils.date_utils import convert_date_format
from ..models.api_models import PriceRequest
```

#### Naming Conventions
- **Files**: lowercase with underscores (`date_utils.py`)
- **Classes**: PascalCase (`PriceRequest`, `BinanceAPI`)
- **Functions/variables**: snake_case (`get_binance_price`, `convert_date_format`)
- **Constants**: UPPER_CASE (`BINANCE_API_URL`)
- **Private**: leading underscore (`_internal_function`, `_private_var`)

#### Type Hints (Required)
```python
def get_binance_price(symbol: str, interval: str = "1h") -> Dict[str, Any]:
    """Get price with proper type hints."""
    return {"symbol": symbol, "interval": interval}
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
        # Business logic
        data = await fetch_price_data(symbol)
        return PriceResponse(symbol=symbol, data=data)
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

#### Error Handling
```python
# Good: Specific exceptions
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
# Good: Async HTTP operations
async with httpx.AsyncClient() as client:
    response = await client.get(url, timeout=30.0)
    data = response.json()

# Good: Async dependencies
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
│   ├── api_models.py    # Request/response models
│   └── settings.py     # Configuration models
├── routes/             # API route handlers
│   ├── __init__.py
│   └── binance.py      # Binance API routes
└── utils/              # Utility functions
    ├── __init__.py
    └── date_utils.py   # Date conversion utilities
```

### Testing Structure
```
tests/
├── test_binance_api.py    # API endpoint tests
└── conftest.py           # Pytest configuration
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
class TestBinanceAPI:
    """Test suite for Binance API."""
    
    @patch.dict(os.environ, {"BINANCE_API_KEY": "test_key"}, clear=False)
    def test_binance_price_success(self):
        """Test successful price fetch."""
        # Mock external dependencies
        # Test input validation
        # Verify response structure
        pass
        
    def test_pydantic_validation(self):
        """Test Pydantic model validation."""
        # Test valid inputs
        # Test invalid inputs
        # Verify error messages
```

### Test Commands
- **Single test**: `python -m pytest tests/test_binance_api.py::TestClass::test_method`
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
# Pydantic settings
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
except ImportError:
    from models.api_models import PriceRequest
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

## Troubleshooting

### Common Issues
1. **Port conflicts**: Check if port 8000 or 5678 is already in use
2. **Environment variables**: Ensure `.env` file exists and is properly formatted
3. **Import errors**: Check Python path and virtual environment activation
4. **Docker issues**: Use `docker-compose down && docker-compose up --build`

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
```

## Performance Considerations

- Use async/await for I/O operations
- Implement proper connection pooling for HTTP clients
- Cache frequently accessed data when appropriate
- Use appropriate timeout values for external API calls
- Monitor memory usage in containerized environment

## Development Workflow

1. **Feature development**: Create feature branch, implement changes, add tests
2. **Testing**: Run full test suite before committing
3. **Documentation**: Update CHANGELOG.md and relevant docs
4. **Review**: Ensure code follows style guidelines and patterns
5. **Deployment**: Use Docker Compose for consistent deployments