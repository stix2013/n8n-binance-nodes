# API Tests

This directory contains unit tests for the API.

## Test Structure

### `test_binance_api.py`
Comprehensive test suite for the Binance API endpoint `/api/binance/price`

#### Test Classes:

**`TestBinanceAPI`**
- `test_root_endpoint()` - Tests basic FastAPI root endpoint
- `test_health_endpoint()` - Tests health check endpoint
- `test_binance_price_success()` - Tests successful price fetch with all parameters
- `test_binance_price_minimal_params()` - Tests fetch with minimal parameters (symbol only)
- `test_binance_price_missing_api_key()` - Tests error when BINANCE_API_KEY is missing
- `test_binance_price_api_error()` - Tests error handling for API errors
- `test_binance_price_timeout_error()` - Tests timeout error handling
- `test_binance_price_connection_error()` - Tests connection error handling
- `test_binance_price_invalid_date_format()` - Tests invalid date format validation
- `test_binance_price_invalid_limit_range()` - Tests limit parameter validation
- `test_binance_price_missing_symbol()` - Tests missing required symbol parameter
- `test_binance_price_symbol_case_insensitive()` - Tests case-insensitive symbol handling

**`TestDateConversion`**
- `test_convert_date_format_valid()` - Tests successful date format conversion
- `test_convert_date_format_invalid()` - Tests invalid date format error handling

## Running Tests

```bash
# Install test dependencies
uv sync --extra dev

# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_binance_api.py -v

# Run tests with coverage
uv run pytest tests/ --cov=. --cov-report=html
uv run pytest tests/ --cov=. --cov-report=term-missing

# View coverage report
open htmlcov/index.html  # On macOS
xdg-open htmlcov/index.html  # On Linux
```

## Test Coverage

Current coverage: **97%** (218 statements, 6 missed)

✅ **Success Cases**
- Full parameter set (symbol, limit, startdate, enddate)
- Minimal parameters (symbol only)
- Case-insensitive symbol handling

✅ **Error Cases**
- Missing API key
- Invalid date format
- Invalid limit range
- Missing required parameters
- API errors (400, etc.)
- Timeout errors (408)
- Connection errors (503)

✅ **Data Transformation**
- Response structure validation
- Data type conversion
- Timestamp conversion

## Mocking Strategy

- Uses `unittest.mock.patch` to mock HTTP requests
- Mocks environment variables with `patch.dict`
- Tests run in isolation without external dependencies
- All Binance API interactions are simulated
