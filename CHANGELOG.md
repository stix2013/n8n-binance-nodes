# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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