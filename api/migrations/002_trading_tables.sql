-- Migration 002: Trading tables for spot/futures orders and candlestick cache
-- Created: 2026-02-17
-- Description: Add tables for order persistence and candlestick caching with auto-pruning

-- ============================================
-- SPOT ORDERS TABLE
-- ============================================
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

-- Index for faster symbol lookups
CREATE INDEX IF NOT EXISTS idx_spot_orders_symbol ON spot_orders(symbol);
CREATE INDEX IF NOT EXISTS idx_spot_orders_status ON spot_orders(status);
CREATE INDEX IF NOT EXISTS idx_spot_orders_created_at ON spot_orders(created_at DESC);

-- ============================================
-- FUTURES ORDERS TABLE
-- ============================================
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

-- Indexes for futures orders
CREATE INDEX IF NOT EXISTS idx_futures_orders_symbol ON futures_orders(symbol);
CREATE INDEX IF NOT EXISTS idx_futures_orders_market_type ON futures_orders(market_type);
CREATE INDEX IF NOT EXISTS idx_futures_orders_status ON futures_orders(status);
CREATE INDEX IF NOT EXISTS idx_futures_orders_created_at ON futures_orders(created_at DESC);

-- ============================================
-- AUTO-PRUNE FUNCTION (Keeps max 3 orders per symbol)
-- ============================================
CREATE OR REPLACE FUNCTION prune_old_orders()
RETURNS TRIGGER AS $$
BEGIN
    -- For spot orders: keep max 3 per symbol
    IF TG_TABLE_NAME = 'spot_orders' THEN
        DELETE FROM spot_orders
        WHERE id NOT IN (
            SELECT id FROM spot_orders
            WHERE symbol = NEW.symbol
            ORDER BY created_at DESC
            LIMIT 3
        )
        AND symbol = NEW.symbol;
    
    -- For futures orders: keep max 3 per symbol + market_type combination
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

-- Trigger for spot orders auto-pruning
DROP TRIGGER IF EXISTS prune_spot_orders_trigger ON spot_orders;
CREATE TRIGGER prune_spot_orders_trigger
    AFTER INSERT ON spot_orders
    FOR EACH ROW EXECUTE FUNCTION prune_old_orders();

-- Trigger for futures orders auto-pruning
DROP TRIGGER IF EXISTS prune_futures_orders_trigger ON futures_orders;
CREATE TRIGGER prune_futures_orders_trigger
    AFTER INSERT ON futures_orders
    FOR EACH ROW EXECUTE FUNCTION prune_old_orders();

-- ============================================
-- CANDLESTICK CACHE TABLE
-- ============================================
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

-- Indexes for candlestick cache
CREATE INDEX IF NOT EXISTS idx_candlestick_lookup 
    ON candlestick_cache(symbol, market_type, interval, open_time);
CREATE INDEX IF NOT EXISTS idx_candlestick_updated 
    ON candlestick_cache(updated_at);

-- ============================================
-- CANDLESTICK PRUNE FUNCTION (30 days retention)
-- ============================================
CREATE OR REPLACE FUNCTION prune_old_candlesticks()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM candlestick_cache
    WHERE open_time < NOW() - INTERVAL '30 days';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to prune old candlesticks on each insert
DROP TRIGGER IF EXISTS prune_candlesticks_trigger ON candlestick_cache;
CREATE TRIGGER prune_candlesticks_trigger
    AFTER INSERT ON candlestick_cache
    FOR EACH ROW EXECUTE FUNCTION prune_old_candlesticks();

-- ============================================
-- MIGRATION METADATA
-- ============================================
-- Track migration version
CREATE TABLE IF NOT EXISTS migration_versions (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT
);

-- Record this migration
INSERT INTO migration_versions (version, description)
VALUES ('002_trading_tables', 'Add spot/futures orders and candlestick cache tables with auto-pruning')
ON CONFLICT (version) DO UPDATE SET applied_at = NOW();
