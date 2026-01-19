# n8n Binance API

API for fetching cryptocurrency prices from Binance.

## Directory Structure

```
api/
├── src/
│   ├── main.py              # FastAPI application setup
│   ├── routes/
│   │   ├── __init__.py
│   │   └── binance.py       # Binance API routes
│   └── utils/
│       ├── __init__.py
│       └── date_utils.py    # Date utility functions
├── tests/
│   ├── __init__.py
│   ├── README.md           # Test documentation
│   └── test_binance_api.py # Unit tests
├── pyproject.toml          # Project dependencies
└── uv.lock               # Dependency lock file
```

## Features

- **Binance Price Endpoint**: `/api/binance/price`
- **Environment Variables**: Uses `BINANCE_API_KEY` from `.env`
- **Date Format**: Supports `YYYYMMDD` format for date parameters
- **Error Handling**: Comprehensive error handling for API failures
- **Input Validation**: Parameter validation with FastAPI
- **Async Operations**: Uses `httpx.AsyncClient` for efficient API calls

## Endpoints

### Root
- `GET /` - Returns hello message
- `GET /health` - Health check endpoint

### Binance API
- `GET /api/binance/price` - Get historical price data from Binance

### Parameters for `/api/binance/price`
- `symbol` (required): Trading pair symbol (e.g., BTCUSDT, ETHUSDT)
- `interval` (optional): Kline interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M) - default: 1h
- `limit` (optional): Number of records (1-1000, default: 50)
- `startdate` (optional): Start date in YYYYMMDD format
- `enddate` (optional): End date in YYYYMMDD format

## Example Usage

```bash
# Get BTCUSDT prices (default 1h interval)
curl "http://localhost:8000/api/binance/price?symbol=BTCUSDT"

# Get ETHUSDT prices with 15m interval and date range
curl "http://localhost:8000/api/binance/price?symbol=ETHUSDT&interval=15m&startdate=20240101&enddate=20240102"

# Get specific number of records with custom interval
curl "http://localhost:8000/api/binance/price?symbol=BTCUSDT&interval=4h&limit=10"
```

## Running the API

```bash
# Install dependencies
uv sync

# Run development server
uv run python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

Create a `.env` file in the project root:

```bash
BINANCE_API_KEY=your_binance_api_key_here
```

## Development

The project is organized in a modular structure:

- **src/main.py**: FastAPI application configuration
- **src/routes/**: API route handlers
- **src/utils/**: Utility functions
- **tests/**: Unit tests with comprehensive coverage

## Testing

See [tests/README.md](tests/README.md) for detailed testing information.
