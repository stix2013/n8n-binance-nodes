# n8n Binance Nodes

A Docker-based n8n workflow automation environment with custom community nodes for cryptocurrency trading on Binance. This project includes specialized nodes and infrastructure for automated crypto trading analysis and execution.

## Features

- **Custom n8n Community Nodes:**
  - **BinanceKline:** Fetch cryptocurrency market data from Binance API with customizable symbol parameters
  - **ChartCrypto:** Generate crypto trading charts with technical indicators

- **Infrastructure:**
  - n8n with external task runners (version configurable via `N8N_VERSION`)
  - PostgreSQL 16 database
  - FastAPI service for custom endpoints (Python 3.13, version configurable via `API_VERSION`)
  - Python 3.13 task runner environment

- **Trading Tools:**
  - Technical analysis workflows (MACD, RSI, Volume)
  - Multi-timeframe analysis (5m, 15m, 1h, 4h)
  - News sentiment analysis integration
  - Automated signal generation (long, short, hold)

- **Data Validation:**
  - Binance price data validation (close_time, price consistency, volume > 0)
  - Optional validation skip parameters for flexibility

## Project Structure

```
n8n-binance-nodes/
├── .env                            # Environment configuration (API keys, versions, ports)
├── .env-example                    # Environment template example
├── docker-compose.yml              # Main Docker orchestration
├── README.md                       # This file
├── CHANGELOG.md                    # Version history and changes
├── AGENTS.md                       # Agent development guidelines
├── opencode.json                   # OpenCode configuration
├── policy.yaml                     # Policy definitions
│
├── nodes/                          # n8n custom community nodes
│   └── @stix/
│       └── n8n-nodes-binance-kline/   # Binance Kline node (crypto market data)
│
├── api/                            # FastAPI Python service
│   ├── src/
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── config/                 # Configuration modules
│   │   │   └── logging_config.py   # JSON logging configuration
│   │   ├── middleware/             # HTTP middleware
│   │   │   └── logging_middleware.py
│   │   ├── models/                 # Pydantic models
│   │   │   ├── api_models.py       # Request/response models
│   │   │   ├── indicators.py       # Technical indicators models
│   │   │   └── settings.py         # Environment settings
│   │   ├── routes/                 # API route handlers
│   │   │   ├── binance.py          # Binance API endpoints
│   │   │   └── indicators.py       # Technical indicators endpoints
│   │   └── utils/                  # Utility functions
│   │       ├── date_utils.py       # Date/time conversion
│   │       ├── indicators.py       # RSI, MACD calculations
│   │       └── price_validation.py # Binance data validation
│   ├── tests/                      # Unit tests
│   ├── pyproject.toml              # Python dependencies
│   └── demo_indicators.py          # Technical indicators demo
│
├── dockers/                        # Docker build files
│   ├── Dockerfile                  # Task runner image (n8nio/runners)
│   ├── Dockerfile.python           # FastAPI Python 3.13 image
│   ├── Dockerfile.postgres         # PostgreSQL customization
│   └── n8n-task-runners.json       # Task runner config
│
├── config/                         # Configuration files
│   └── n8n-task-runners.json       # n8n task runner settings
│
├── docs/                           # Documentation
│   ├── day-trader-expert.md        # Trading strategy guide
│   ├── chart-img/                  # Chart examples
│   └── workflows/                  # Example n8n workflows
│       └── n8n-workflow-ingres.json # Data ingestion and analysis workflow
│
├── scripts/                        # Environment management scripts
│   ├── start-env.ts                # Start services and Zrok tunnel
│   ├── stop-env.ts                 # Stop services and Zrok tunnel
│   ├── build-images.ts             # Automated Docker image builder
│   ├── build-image-choice.ts       # Interactive visual image selector
│   └── utils/                      # Script utilities
│       └── docker-build.ts         # Shared Docker build logic
│
└── .vscode/                        # VS Code settings
```

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Binance API credentials (for the BinanceKline node)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/stix2013/n8n-binance-nodes.git
cd n8n-binance-nodes
```

2. Configure environment variables:
```bash
cp env-example .env
# Edit .env with your settings
```

3. Start the services:
```bash
bun start
```

4. Access n8n at `http://localhost:5678`
   - Default credentials: `user` / `password123` (change in `.env`)

### Services

| Service | Port | Description |
|---------|------|-------------|
| n8n | 5678 | Main workflow automation platform |
| FastAPI | 8000 | API service for Binance price data and custom endpoints |
| PostgreSQL | 5432 | Database backend |

## Custom Nodes

### BinanceKline Node

Fetches cryptocurrency trading data from Binance.

**Configuration:**
- Symbol: Crypto pair (e.g., `BTCUSDT`)
- Requires Binance API credentials

### ChartCrypto Node

Generates trading charts with technical indicators for analysis.

**Configuration:**
- Symbol: Crypto pair identifier

## Trading Workflows

The project includes pre-configured trading analysis patterns:

- **Regime Engine (4h):** Market trend analysis
- **Bias Engine (1h):** Directional bias determination
- **Setup Engine (15m):** Entry setup identification
- **Execution Engine (5m):** Order execution logic

See `docs/day-trader-expert.md` for detailed trading strategies and signal logic.

## Example Workflows

The project includes example workflows to demonstrate node usage and API integration:

- **Data Ingestion Analysis (`docs/workflows/n8n-workflow-ingres.json`):** 
  Demonstrates how to fetch market data using the `BinanceKline` custom node, transform the data for the API, and call the `/api/ingest/analyze` endpoint for technical analysis.

## Building Custom Nodes

For each node package:

```bash
cd nodes/@stix/n8n-nodes-{node-name}
npm install
npm run build
npm run lint
```

## Environment Variables

Key variables in `.env`:

### n8n Configuration
- `N8N_HOST`: n8n host address
- `N8N_PORT`: n8n port (default: 5678)
- `N8N_BASIC_AUTH_USER`: Admin username
- `N8N_BASIC_AUTH_PASSWORD`: Admin password
- `N8N_RUNNERS_AUTH_TOKEN`: Task runner authentication

### API Configuration
- `API_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR; default: INFO)
- `ENVIRONMENT`: Environment name (development, production)
- `API_HOST`: API bind address (default: 0.0.0.0)
- `API_PORT`: API port (default: 8000)

### Database
- `POSTGRES_DB`: PostgreSQL database name
- `POSTGRES_PASSWORD`: PostgreSQL password

### Other
- `TZ`: Timezone (default: Asia/Jakarta)
- `ZROK_RESERVED_NAME`: Zrok reserved name for public access
- `ZROK_PUBLIC_URL`: Public URL for Zrok tunnel

## Development

### Task Runners

The project uses external task runners with Python 3.13 for:

- Data processing with pandas, numpy
- Technical analysis
- News sentiment analysis with VADER
- Machine learning with torch

Allowed modules: `numpy,pandas,feedparser,requests,bs4,textblob,vaderSentiment,torch,datetime,urllib,quote`

### Environment Management

The project includes convenience scripts for managing the development environment.

**Start Environment:**
```bash
bun start
```
This command starts all Docker containers and launches the Zrok tunnel.

**Stop Environment:**
```bash
bun stop
```
This command stops all Docker containers and terminates the Zrok tunnel.

**Build Docker Images:**
```bash
# Automated build for all images
bun run build:images

# Interactive build with visual selection menu
bun run build:image
```
These scripts build the custom n8n-runners, FastAPI API, and Postgres images using versions from `.env`.

**Configuration:**
- `ZROK_RESERVED_NAME`: The reserved Zrok share name (e.g., `stix2025n8n`)
- `ZROK_PUBLIC_URL`: The public URL for the tunnel (e.g., `https://stixgoauth2025.share.zrok.io`)

### API Service

FastAPI service available at `http://localhost:8000`

**Endpoints:**
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/binance/price` - Fetch cryptocurrency prices from Binance (with validation)
- `GET /api/indicators/analysis` - Full RSI + MACD technical analysis
- `GET /api/indicators/rsi` - RSI indicator only
- `GET /api/indicators/macd` - MACD indicator only
- `POST /api/ingest/analyze` - Receives n8n BinanceKline data and performs technical analysis.

**Configuration:**
- Python 3.13 with pip
- Reads environment variables from `.env` file
- Supports multiple time intervals (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
- Date range filtering with YYYYMMDD format

### API Logging

The API outputs structured JSON logs for production environments.

**View API Logs:**
```bash
# View all API logs
docker compose logs -f api

# View last 100 lines
docker compose logs --tail=100 api

# View logs with JSON formatting
docker compose logs api | jq
```

**Log Levels:** Configurable via `API_LOG_LEVEL` in `.env` (DEBUG, INFO, WARNING, ERROR)

**Key Log Events:**
- Startup/shutdown events with environment info
- Error requests (4xx, 5xx) with full request details
- Process time included for all logged requests

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version information.

- **v1.0.0** (2026-01-27) - Startup scripts, Zrok integration, n8n 2.6.0
- **v0.5.1** (2026-01-23) - Node compliance fixes, n8n documentation
- **v0.5.0** (2026-01-22) - Binance price validation, version configuration
- **v0.4.1** (2026-01-22) - Structured JSON logging, Docker best practices
- **v2.4.4** (2026-01-18) - Upgrade to n8n 2.4.4-amd64
- **v2.4.2** (2026-01-15) - Upgrade to n8n 2.4.2-amd64
- **v2.3.2** (2026-01-12) - PostgreSQL SSL fix, base image updates

## License

MIT License - see individual node packages for details.

## Author

Stevan H. Moeladi - [stevan.moeladi@gmail.com](mailto:stevan.moeladi@gmail.com)

## Resources

- [n8n Documentation](https://docs.n8n.io/)
- [n8n Community Nodes](https://docs.n8n.io/integrations/#community-nodes)
- [Binance API Documentation](https://binance-docs.github.io/apidocs/)
- [TradingView Documentation](https://www.tradingview.com/)
