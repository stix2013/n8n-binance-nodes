# Binance URL Option - Node Build Issue

**Date**: 2026-02-17  
**Issue**: `rawKlines.map is not a function` error in BinanceKline node

## Problem

The BinanceKline node was throwing `rawKlines.map is not a function` when fetching data via the proxy API.

## Root Cause

The container had old build files (timestamp Feb 17 05:43) while the local build was newer (Feb 17 14:37). The old build didn't have the correct field mapping fixes for the proxy response format.

## Solution

### 1. Identify the correct container path

The custom node is mounted at `/home/node/custom-extensions/@stix/n8n-nodes-binance-kline/` inside the n8n container (not at `/home/node/.n8n/custom/`).

### 2. Copy updated node file to container

```bash
docker cp /path/to/local/n8n-nodes-binance-kline/dist/nodes/BinanceKline/BinanceKline.node.js n8n-main:/home/node/custom-extensions/@stix/n8n-nodes-binance-kline/dist/nodes/BinanceKline/
```

### 3. Restart n8n

```bash
docker compose restart n8n
```

## Key Fix in Code

The node's `ProxyPriceDataPoint` interface was corrected to use the proper field names returned by the proxy API:

```typescript
interface ProxyPriceDataPoint {
	open_time: string;
	open_price: number;
	high_price: number;
	low_price: number;
	close_price: number;
	volume: number;
	close_time: string;
	quote_asset_volume: number;
	number_of_trades: number;
	taker_buy_base_asset_volume: number;
	taker_buy_quote_asset_volume: number;
}
```

And the mapping code handles the proxy response format correctly:

```typescript
if (apiSource === 'proxy' && marketType === 'spot') {
	const priceResponse = response as ProxyPriceResponse;
	klines = priceResponse.data.map((k) => ({
		openTime: new Date(k.open_time).getTime(),
		open: String(k.open_price),
		// ... etc
	}));
}
```

## Verification

- API endpoint `/api/binance/price` returns Spot klines with correct field names (quote_asset_volume, number_of_trades, etc.)
- API endpoint `/api/binance/futures/kline` returns futures klines directly from Binance
- Build local node: `cd nodes/@stix/n8n-nodes-binance-kline && bun run build`
- Check container logs: `docker compose logs -f n8n`
