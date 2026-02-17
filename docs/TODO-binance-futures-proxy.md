# TODO: Binance Futures Proxy with Database Persistence

## Overview

Extend the FastAPI proxy to support both **Spot** and **Futures** (USD-M and Coin-M) markets with PostgreSQL persistence for orders and cached candlestick data.

## Requirements

- ✅ **USD-M Futures** (fapi.binance.com) - prices & orders
- ✅ **Coin-M Futures** (dapi.binance.com) - prices & orders
- ✅ **Spot market** - orders persisted to database
- ✅ **Max 3 recent orders** per symbol (auto-pruning)
- ✅ **Candlestick sync** every 1 minute
- ✅ **Single orders only** (no batch initially)
- ✅ **Same API key** for all markets
- ✅ **Configurable symbol list** via `.env`
- ✅ **Intervals**: 1m, 15m, 1h, 4h, 1d

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────────┐
│   n8n Nodes     │────▶│  FastAPI     │────▶│  Binance APIs       │
│  (Spot/Futures) │     │   Proxy      │     │  Spot/USD-M/Coin-M  │
└─────────────────┘     └──────┬───────┘     └─────────────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  PostgreSQL  │
                        │  - Orders    │
                        │  - Candles   │
                        └──────────────┘
```

## Configuration

Add to root `.env`:

```bash
# Trading Configuration
TRADING_SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT
TRADING_INTERVALS=1m,15m,1h,4h,1d
CANDLESTICK_SYNC_INTERVAL=60

# Market Types to Sync
TRADING_MARKET_TYPES=spot,usd_m

# Binance API (same key for all markets)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_secret_here
```

## Phase 1: Database Schema

### File: `api/migrations/002_trading_tables.sql`

```sql
-- Spot orders table
CREATE TABLE IF NOT EXISTS spot_orders (
    id SERIAL PRIMARY KEY,
    order_id BIGINT UNIQUE,
    client_order_id VARCHAR(255),
    symbol VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    order_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    price DECIMAL(36, 18),
    quantity DECIMAL(36, 18) NOT NULL,
    executed_qty DECIMAL(36, 18) DEFAULT 0,
    time_in_force VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    binance_response JSONB
);

-- Futures orders table
CREATE TABLE IF NOT EXISTS futures_orders (
    id SERIAL PRIMARY KEY,
    order_id BIGINT UNIQUE,
    client_order_id VARCHAR(255),
    symbol VARCHAR(50) NOT NULL,
    market_type VARCHAR(10) NOT NULL CHECK (market_type IN ('usd_m', 'coin_m')),
    side VARCHAR(10) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    order_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    price DECIMAL(36, 18),
    quantity DECIMAL(36, 18) NOT NULL,
    executed_qty DECIMAL(36, 18) DEFAULT 0,
    time_in_force VARCHAR(10),
    reduce_only BOOLEAN DEFAULT FALSE,
    close_position BOOLEAN DEFAULT FALSE,
    stop_price DECIMAL(36, 18),
    working_type VARCHAR(10),
    price_protect BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    binance_response JSONB
);

-- Auto-prune function (keeps max 3 orders per symbol)
CREATE OR REPLACE FUNCTION prune_old_orders()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE_NAME = 'spot_orders' THEN
        DELETE FROM spot_orders
        WHERE id NOT IN (
            SELECT id FROM spot_orders
            WHERE symbol = NEW.symbol
            ORDER BY created_at DESC
            LIMIT 3
        )
        AND symbol = NEW.symbol;
    ELSIF TG_TABLE_NAME = 'futures_orders' THEN
        DELETE FROM futures_orders
        WHERE id NOT IN (
            SELECT id FROM futures_orders
            WHERE symbol = NEW.symbol AND market_type = NEW.market_type
            ORDER BY created_at DESC
            LIMIT 3
        )
        AND symbol = NEW.symbol AND market_type = NEW.market_type;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for auto-pruning
CREATE TRIGGER prune_spot_orders_trigger
    AFTER INSERT ON spot_orders
    FOR EACH ROW EXECUTE FUNCTION prune_old_orders();

CREATE TRIGGER prune_futures_orders_trigger
    AFTER INSERT ON futures_orders
    FOR EACH ROW EXECUTE FUNCTION prune_old_orders();

-- Candlestick cache table
CREATE TABLE IF NOT EXISTS candlestick_cache (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    market_type VARCHAR(10) NOT NULL CHECK (market_type IN ('spot', 'usd_m', 'coin_m')),
    interval VARCHAR(10) NOT NULL,
    open_time TIMESTAMP WITH TIME ZONE NOT NULL,
    open_price DECIMAL(36, 18) NOT NULL,
    high_price DECIMAL(36, 18) NOT NULL,
    low_price DECIMAL(36, 18) NOT NULL,
    close_price DECIMAL(36, 18) NOT NULL,
    volume DECIMAL(36, 18) NOT NULL,
    close_time TIMESTAMP WITH TIME ZONE NOT NULL,
    quote_volume DECIMAL(36, 18) NOT NULL,
    trades INTEGER NOT NULL,
    taker_buy_base_volume DECIMAL(36, 18) NOT NULL,
    taker_buy_quote_volume DECIMAL(36, 18) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(symbol, market_type, interval, open_time)
);

CREATE INDEX IF NOT EXISTS idx_candlestick_lookup 
    ON candlestick_cache(symbol, market_type, interval, open_time);
```

## Phase 2: New Files

### 1. Models: `api/src/models/trading_models.py`

Create Pydantic models for:
- `SpotOrder`, `FuturesOrder`
- `CandlestickData`
- `MarketTypeEnum`, `OrderSideEnum`, `OrderStatusEnum`
- Request/response models for all endpoints

### 2. Trading Service: `api/src/services/trading_service.py`

```python
class TradingService:
    async def place_spot_order(self, order_data: dict) -> dict:
        """Place spot order on Binance and persist to DB."""
        pass
    
    async def place_futures_order(self, order_data: dict, market_type: str) -> dict:
        """Place USD-M or Coin-M futures order and persist to DB."""
        pass
    
    async def get_recent_orders(self, symbol: str, market_type: str = None) -> list:
        """Get max 3 recent orders per symbol."""
        pass
```

### 3. Candlestick Sync: `api/src/services/candlestick_sync.py`

```python
class CandlestickSyncService:
    async def start_sync_loop(self):
        """Start background sync every 60 seconds."""
        pass
    
    async def sync_symbol_interval(self, symbol: str, market_type: str, interval: str):
        """Fetch from Binance and upsert to DB."""
        pass
    
    async def get_cached_candles(self, symbol: str, market_type: str, 
                                  interval: str, limit: int) -> list:
        """Query cached candlesticks."""
        pass
```

### 4. Binance Client: `api/src/utils/binance_client.py`

Unified client for all Binance APIs:
- Spot: `https://api.binance.com`
- USD-M Futures: `https://fapi.binance.com`
- Coin-M Futures: `https://dapi.binance.com`
- HMAC signature generation
- Error handling

### 5. Trading Routes: `api/src/routes/trading.py`

**Spot Endpoints:**
- `POST /api/binance/spot/order` - Place order
- `GET /api/binance/spot/orders` - Get recent orders

**Futures Endpoints:**
- `POST /api/binance/futures/order` - Place futures order
- `GET /api/binance/futures/orders` - Get recent orders
- `GET /api/binance/futures/klines` - Cached klines (all markets)
- `GET /api/binance/futures/markPrice` - Current mark price
- `GET /api/binance/futures/openInterest` - Current open interest
- `GET /api/binance/futures/openInterestHist` - Historical OI

**Admin Endpoints:**
- `POST /api/admin/sync/now` - Trigger immediate sync
- `GET /api/admin/sync/status` - Sync status

## Phase 3: Modified Files

### 1. Settings: `api/src/models/settings.py`

Add to Settings class:
```python
trading_symbols: list = Field(default_factory=lambda: ["BTCUSDT"])
trading_intervals: list = Field(default_factory=lambda: ["1m", "15m", "1h", "4h", "1d"])
candlestick_sync_interval: int = 60
trading_market_types: list = Field(default_factory=lambda: ["spot", "usd_m"])
```

### 2. Database Service: `api/src/services/database.py`

- Add migration runner for `002_trading_tables.sql`

### 3. Main App: `api/src/main.py`

- Add trading router
- Start candlestick sync on startup
- Graceful shutdown

### 4. Binance Routes: `api/src/routes/binance.py`

- Update existing `POST /api/binance/order` to use trading service
- Maintain backward compatibility

## Phase 4: API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/binance/spot/order` | POST | Place spot order + persist |
| `/api/binance/spot/orders` | GET | Get recent orders (max 3/symbol) |
| `/api/binance/futures/order` | POST | Place USD-M/Coin-M order |
| `/api/binance/futures/orders` | GET | Get recent futures orders |
| `/api/binance/futures/klines` | GET | Get cached klines |
| `/api/binance/futures/markPrice` | GET | Current mark price |
| `/api/binance/futures/openInterest` | GET | Current open interest |
| `/api/binance/futures/openInterestHist` | GET | Historical OI |
| `/api/admin/sync/now` | POST | Trigger manual sync |
| `/api/admin/sync/status` | GET | Sync status |

## Phase 5: Testing Strategy

### Unit Tests
- [ ] Order pruning logic
- [ ] Candlestick data transformation
- [ ] HMAC signature generation

### Integration Tests
- [ ] Full order flow (place → persist → query)
- [ ] Candlestick sync (fetch → cache → retrieve)
- [ ] Database trigger testing

### Manual Tests
- [ ] Docker compose up
- [ ] Place test orders
- [ ] Verify max 3 orders limit
- [ ] Verify 1-minute candlestick sync

## Implementation Timeline

| Day | Task |
|-----|------|
| 1 | Database schema + migrations |
| 2 | Trading models + Binance client |
| 3 | Trading service (orders) |
| 4 | Candlestick sync service |
| 5 | Trading routes (spot) |
| 6 | Trading routes (futures) |
| 7 | Update existing binance.py |
| 8 | Integration + testing |

**Total: ~8 days of work**

## Open Questions

1. **Order Status Updates**: Should the proxy poll Binance to update order status (FILLED, CANCELLED, etc.), or only store initial placement?

2. **Error Handling**: If DB insertion fails after Binance order succeeds:
   - A) Return success to user (log error only)
   - B) Return error but order is already placed
   - C) Try to cancel the Binance order

3. **Candlestick Retention**: How long to keep cached candlesticks? (suggested: 30 days)

## Notes

- All markets use the same API key
- No position tracking (orders only)
- Background sync runs every 60 seconds
- Auto-pruning keeps only 3 most recent orders per symbol
- Spot orders are now persisted (backward compatible)
