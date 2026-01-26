# Changelog

## 0.2.0 (2026-01-26)

### Features
- Added watchlist support - store favorite crypto symbols in credentials and fetch data for all at once
- Added Symbol Source option: choose between single symbol or watchlist mode
- Added interval selection (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
- Added limit parameter (1-1000 candles)
- Implemented real Binance API integration via local API service
- Multi-symbol output for watchlist mode

### Bug Fixes
- Fixed network connectivity issues by routing through local API service
- Improved error handling for empty watchlist

### Changes
- Node renamed from "BinanceKline" to "Binance Kline" for better display
- Route requests through api:8000 service for Binance connectivity

## 0.1.0 (2025-01-15)

### Initial Release
- Initial scaffold for Binance Kline node
- Basic credentials structure with API key and secret