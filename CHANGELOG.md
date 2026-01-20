# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.2] - 2026-01-20

### Fixed
- **API Code Quality**: Resolved comprehensive linting issues across the codebase
  - Fixed 13 unused imports across multiple files (src/models/indicators.py, src/routes/binance.py, src/routes/indicators.py, src/utils/indicators.py)
  - Replaced 2 bare `except` clauses with specific exception types (ValueError, httpx.HTTPStatusError) for safer error handling
  - Removed unused imports: typing.List, typing.Dict, pandas, datetime.datetime, models.settings.settings
  - Auto-fixed all fixable issues using `ruff check --fix` command
  - Formatted all source code with `ruff format` for consistent style

### Quality Assurance
- Verified all 46 tests still pass after linting fixes
- Maintained 100% test coverage with no regressions introduced
- Ensured all imports are properly utilized and exception handling is explicit

### Technical
- Updated API version from 0.3.1 to 0.3.2 in pyproject.toml
- Updated docker-compose.yml API image tag to 0.3.2
- Enhanced code readability and maintainability through consistent formatting and proper error handling

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