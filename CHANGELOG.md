# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1] - 2026-01-23

### Fixed
- **n8n Community Node Compliance**: Cleaned up node structure and fixed compliance issues
  - Removed nested `ChartCrypto` node from `n8n-nodes-binance-kline` package
  - Removed unused packages: `n8n-nodes-chart-crypto`, `n8n-nodes-crypto`
  - Fixed Binance API credentials to use `X-MBX-APIKEY` header instead of `Authorization: Bearer`
  - Added `typeOptions: { password: true }` to `apiSecret` field for proper secret handling
  - Added `documentationUrl` property to credentials for user guidance
  - Added icons directory with credential icons
  - Added `main` field to `package.json` pointing to compiled JS entry point
  - Updated `docker-compose.yml` volume mount path to mount entire package (not just dist/)
  - All linting checks pass with `eslint.config.mjs`

### Added
- **n8n Node Development Documentation**: Added comprehensive development guidelines
  - Added "n8n Custom Node Development" section to `AGENTS.md` with build/lint/test commands
  - Added Node Compliance Checklist for community node verification
  - Added credentials configuration examples for Binance API
  - Updated `docs/n8n-custom-node-kimi.md` with practical implementation guide
  - Documented common compliance issues and fixes

### Changed
- **Node Package Structure**: Simplified to single focused node package
  - `nodes/@stix/n8n-nodes-binance-kline/` is now the only active node package
  - Improved separation of concerns for easier maintenance

## [0.5.0] - 2026-01-22

### Added
- **Binance Price Data Validation**: Implemented comprehensive validation for Binance API price data
  - Added `validate_close_time()` to ensure close_time matches expected interval timeframe
  - Added `validate_prices()` to ensure high >= open/close and low <= open/close
  - Added `validate_volume()` to ensure volume > 0
  - Added optional query parameters: `skip_volume_validation`, `skip_time_validation`, `skip_price_validation`
  - Added comprehensive test suite (25 tests for validation utils)
  - Created new module `api/src/utils/price_validation.py`

### Added
- **N8N Version Configuration**: Made n8n version configurable via `N8N_VERSION` environment variable
  - Updated `docker-compose.yml` to use `${N8N_VERSION:-2.4.4-amd64}` for n8n image
  - Updated `docker-compose.yml` to use `${N8N_VERSION:-2.4.4}-local` for task-runners image
  - Added `ARG N8N_VERSION` in `dockers/Dockerfile` for build-time configuration

### Added
- **API Version Configuration**: Made API image version configurable via `API_VERSION` environment variable
  - Updated `docker-compose.yml` to use `${API_VERSION:-0.4.1}` for api image
  - Added `ARG API_VERSION` in `dockers/Dockerfile.python` for build-time configuration
  - Added image metadata labels for version tracking

### Fixed
- **Settings Configuration**: Fixed `env_prefix` configuration in Pydantic Settings class
  - Moved `env_prefix` from class attribute to `ConfigDict` in `api/src/models/settings.py`

### Testing
- Updated test mock data with correct timestamps for close_time validation
- All 71 tests passing in Docker container

## [0.4.1] - 2026-01-22

### Added
- **Environment Configuration**: Added `env_prefix = "API_"` to Settings class for consistent environment variable naming

### Changed
- **Logging System**: Implemented structured JSON logging for production environments
  - Added JSONFormatter for log aggregation systems
  - Integrated logging system in main.py
  - Configurable log level via `API_LOG_LEVEL` environment variable
  - Error-only request logging (4xx/5xx responses)
  - Reduced noise from third-party libraries (httpx, httpcore, urllib3)

### Changed
- **Docker Configuration**: Updated docker-compose for production deployment
  - Production settings: restart policy, read-only volumes, resource limits
  - Non-root user (appuser, uid 1000) for security

### Fixed
- **JSON Formatter**: Properly capture extra fields in JSONFormatter
- **Dockerfile**: Simplified API Dockerfile to use pip instead of uv venv

### Technical
- Added comprehensive FastAPI Docker Best Practices documentation
- Reorganized API documentation to docs directory
- Removed unused files (.python-version, requirements.txt)

## [0.3.1] - 2026-01-20

### Fixed
- **Docker Environment Variables**: Fixed API container to read from single .env file at project root
  - Updated `api/src/main.py` to load dotenv from `/app/.env` instead of relative path
  - Updated `api/src/models/settings.py` to use absolute path for env_file
  - Removed duplicate `api/.env` file - now uses single source at project root
  - Added `extra="allow"` to Pydantic Settings to handle shared environment variables across services
- **Binance API Connectivity**: Fixed network connectivity issues by adding proper DNS entries
  - Added DNS host mapping for `api.binance.com:108.156.104.23` to API service
  - Fixed duplicate DNS entries between task-runners and API services
  - Ensured consistent Binance API connectivity across all containers
- **Container Configuration**: Resolved Docker compose configuration conflicts
  - Removed redundant DNS entries to prevent Docker limitation conflicts
  - Updated API image version from 0.3.0 to 0.3.1

### Changed
- Updated docker-compose.yml API image tag to 0.3.1
- Improved Settings documentation with clear comments for shared .env configuration
- Enhanced container networking with single authoritative DNS entry per hostname

## [0.3.0] - 2026-01-20

### Added
- **Technical Indicators Analysis**: Implemented comprehensive RSI and MACD calculations for cryptocurrency trading analysis
  - Added RSI (Relative Strength Index) calculation with configurable periods (default: 14)
  - Implemented MACD (Moving Average Convergence Divergence) with line, signal, and histogram components
  - Created intelligent recommendation engine (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL)
  - Added comprehensive API endpoints:
    - `GET /api/indicators/analysis` - Full RSI + MACD analysis
    - `GET /api/indicators/{indicator}` - Single indicator (RSI or MACD)
  - Implemented robust data validation (minimum 30 candles requirement)
  - Created production-ready error handling and parameter validation
  - Added comprehensive test suite with 22 test scenarios covering all edge cases
  - Implemented demo script showcasing all features and validation
- **Extensible Architecture**: Designed for future indicators (Bollinger Bands, Stochastic, ATR, etc.)

### Technical
- Added numpy>=1.24.0 and pandas>=2.0.0 dependencies for efficient calculations
- Implemented optimized mathematical algorithms using vectorized operations
- Created modular indicator factory pattern for easy extension
- Added comprehensive mathematical validation against trading standards
- Implemented proper async/await patterns for API integration

### Changed
- Updated API version to 0.3.0 in pyproject.toml
- Updated docker-compose.yml API image tag to 0.3.0
- Enhanced main FastAPI application with new indicators router
- Updated API description to include technical indicators functionality

### Quality Assurance
- Achieved 22/22 tests passing for technical indicators functionality
- Maintained 24/24 tests passing for existing API functionality (no regressions)
- Implemented mathematical accuracy validation against known trading formulas
- Added extensive edge case testing and boundary condition validation

## [Unreleased]

### Added
- **Pydantic Type Checking**: Implemented comprehensive runtime type validation for API requests and responses
  - Added Pydantic models: PriceRequest, PriceResponse, PriceDataPoint, ErrorResponse, HealthResponse, RootResponse
  - Implemented custom validation rules for trading symbols, date formats (YYYYMMDD), and numeric ranges
  - Added IntervalEnum for safe Binance kline interval handling
  - Enhanced error handling with HTTP 422 status codes for validation failures
  - Created comprehensive test suite covering 24 validation scenarios
  - Updated API to use Pydantic v2 best practices with field validators and ConfigDict
  - Added demo script showcasing validation features and benefits
- Docker container can read `.env` file from project root
- API container accessible from host terminal on port 8000

### Fixed
- Fixed FastAPI startup error by setting correct working directory (`/app/src`) in Dockerfile
- Added `python-dotenv` package for environment variable loading

### Changed
- Updated `docker-compose.yml` to mount `.env` file to api container
- Updated `dockers/Dockerfile.python` with proper WORKDIR and dotenv support

### Added
- New Binance API endpoint `/api/binance/price` for fetching cryptocurrency prices
- Support for multiple time intervals (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
- Date range filtering with YYYYMMDD format
- Comprehensive unit tests with 98% coverage

### Changed
- Restructured API codebase into modular architecture (src/routes/, src/utils/)
- Updated environment variable loading with python-dotenv
- Enhanced error handling for API failures and validation
- Updated documentation with proper port specifications (8000)

### Fixed
- Resolved missing 'interval' parameter in Binance API calls
- Fixed uvicorn startup command for proper development server
- Updated gitignore to exclude coverage and test artifacts

### Technical
- Implemented FastAPI router pattern for better API organization
- Added dependency injection for API key management
- Created isolated utility functions for date processing
- Established professional testing framework with mock HTTP requests

## Changed
- Move `api` folder from `dockers/api` to project root for better project organization
- Update `docker-compose.yml` to use new API folder location at project root

## [2.4.4] - 2026-01-18

### Changed
- Upgrade n8n from `2.4.2-amd64` to `2.4.4-amd64`
- Update base Docker image to `n8nio/n8n:2.4.4-amd64`

## [2.4.2] - 2026-01-15

### Changed
- Upgrade n8n from `2.3.2-amd64` to `2.4.2-amd64`
- Update task runners from `2.3.2` to `2.4.2` with new base image `n8nio/runners:2.4.2-amd64`

## [2.3.2] - 2026-01-12

### Changed
- Upgrade n8n from `2.3.1-amd64` to `2.3.2-amd64`
- Update task runners from `2.3.1` to `2.3.2` with new base image `n8nio/runners:2.3.2-amd64`

### Fixed
- Resolve SSL certificate error in PostgreSQL Docker build
- Create custom PostgreSQL 16 image to replace problematic pgvector compilation
- Update docker-compose.yml to use custom PostgreSQL image with proper environment variables

### Technical
- Replace complex pgvector build process with simplified PostgreSQL 16 configuration
- Ensure all Docker services build successfully without SSL connectivity issues
- Maintain compatibility with existing n8n workflow configurations