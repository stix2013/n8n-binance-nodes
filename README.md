# n8n Binance Nodes

A Docker-based n8n workflow automation environment with custom community nodes for cryptocurrency trading on Binance. This project includes specialized nodes and infrastructure for automated crypto trading analysis and execution.

## Features

- **Custom n8n Community Nodes:**
  - **BinanceKline:** Fetch cryptocurrency market data from Binance API with customizable symbol parameters
  - **ChartCrypto:** Generate crypto trading charts with technical indicators

- **Infrastructure:**
  - n8n 2.4.2 with external task runners
  - PostgreSQL 16 database
  - FastAPI service for custom endpoints
  - Python 3.13 task runner environment

- **Trading Tools:**
  - Technical analysis workflows (MACD, RSI, Volume)
  - Multi-timeframe analysis (5m, 15m, 1h, 4h)
  - News sentiment analysis integration
  - Automated signal generation (long, short, hold)

## Project Structure

```
n8n-binance-nodes/
├── nodes/
│   └── @stix/
│       ├── n8n-nodes-binance-kline/    # Binance API integration node
│       └── n8n-nodes-chart-crypto/     # Crypto charting node
├── dockers/
│   ├── api/                            # FastAPI service
│   ├── task-runner-python/             # Python task runner
│   └── Dockerfile                      # Custom Docker images
├── config/
│   └── n8n-task-runners.json           # Task runner configuration
├── docs/
│   ├── day-trader-expert.md            # Trading strategy documentation
│   └── chart-img/                      # Chart examples
├── docker-compose.yml                  # Main orchestration
└── .env                               # Environment configuration
```

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Binance API credentials (for the BinanceKline node)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/stix2013/n8n-nodes-binance-kline.git
cd n8n-binance-nodes
```

2. Configure environment variables:
```bash
cp env-example .env
# Edit .env with your settings
```

3. Start the services:
```bash
docker-compose up -d
```

4. Access n8n at `http://localhost:5678`
   - Default credentials: `user` / `password123` (change in `.env`)

### Services

| Service | Port | Description |
|---------|------|-------------|
| n8n | 5678 | Main workflow automation platform |
| FastAPI | 8000 | API service for custom endpoints |
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

- `N8N_HOST`: n8n host address
- `N8N_PORT`: n8n port (default: 5678)
- `N8N_BASIC_AUTH_USER`: Admin username
- `N8N_BASIC_AUTH_PASSWORD`: Admin password
- `N8N_RUNNERS_AUTH_TOKEN`: Task runner authentication
- `POSTGRES_DB`: PostgreSQL database name
- `POSTGRES_PASSWORD`: PostgreSQL password
- `TZ`: Timezone (default: Asia/Jakarta)

## Development

### Task Runners

The project uses external task runners with Python 3.13 for:

- Data processing with pandas, numpy
- Technical analysis
- News sentiment analysis with VADER
- Machine learning with torch

Allowed modules: `numpy,pandas,feedparser,requests,bs4,textblob,vaderSentiment,torch,datetime,urllib,quote`

### API Service

FastAPI service available at `http://localhost:8000`

- `GET /` - Root endpoint
- `GET /health` - Health check

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version information.

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
