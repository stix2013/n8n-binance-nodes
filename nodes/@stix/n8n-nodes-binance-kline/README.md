# @stix/n8n-nodes-binance-kline

This n8n community node fetches cryptocurrency candlestick (kline) data from Binance API. It supports both single symbol queries and watchlist-based multi-symbol fetching for efficient market analysis workflows.

[n8n](https://n8n.io/) is a [fair-code licensed](https://docs.n8n.io/sustainable-use-license/) workflow automation platform.

[Installation](#installation)
[Operations](#operations)
[Credentials](#credentials)
[Compatibility](#compatibility)
[Usage](#usage)
[Resources](#resources)
[Version history](#version-history)

## Installation

Follow the [installation guide](https://docs.n8n.io/integrations/community-nodes/installation/) in the n8n community nodes documentation.

## Operations

### Kline Data

Fetch candlestick data from Binance for cryptocurrency trading pairs.

**Input Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| Symbol Source | options | Yes | Choose "Single Symbol" or "Watchlist" |
| Symbol | string | No* | Trading pair (e.g., BTCUSDT, ETHUSDT) - *required for Single Symbol mode |
| Watchlist | credentials | No* | Comma-separated list of symbols - *required for Watchlist mode |
| Interval | options | Yes | Candlestick timeframe (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M) |
| Limit | number | Yes | Number of candles to return (1-1000, default: 50) |

**Output:**

Each execution produces one or more items (one per symbol) containing:

```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "limit": 50,
  "currentPrice": "42000.00",
  "klineCount": 50,
  "klines": [
    {
      "openTime": 1706000000000,
      "open": "41900.00",
      "high": "42200.00",
      "low": "41800.00",
      "close": "42000.00",
      "volume": "1250.5",
      "closeTime": 1706006399000,
      "quoteVolume": "52500000.00",
      "trades": 15234,
      "takerBuyBaseVolume": "521.24",
      "takerBuyQuoteVolume": "21892000.00"
    }
  ],
  "fetchedAt": "2026-01-26T10:30:00.000Z"
}
```

## Credentials

### Binance API

Authentication for Binance API access.

**Required Fields:**

| Field | Type | Description |
|-------|------|-------------|
| API Key | string | Binance API key with read permissions |
| API Secret | string | Binance API secret key |
| Watchlist | string | Comma-separated list of favorite crypto pairs (e.g., BTCUSDT, ETHUSDT, SOLUSDT) |

**Setup:**

1. Log in to your [Binance account](https://www.binance.com/)
2. Go to API Management under your account settings
3. Create a new API key with read permissions (do not enable trading permissions for security)
4. Copy the API Key and Secret to the credentials
5. Add your watchlist symbols as a comma-separated list

**Security Note:** Never share your API credentials. The node uses read-only access to protect your account.

## Compatibility

- **n8n version:** 1.0.0 or higher (tested with n8n 2.5.0)
- **Node version:** 1.0.0
- **Binance API:** Spot API v3

## Usage

### Single Symbol Mode

Fetch klines for a specific trading pair:

```
1. Add "Binance Kline" node to your workflow
2. Set Symbol Source to "Single Symbol"
3. Enter symbol (e.g., BTCUSDT)
4. Select interval (e.g., 1 Hour)
5. Set limit (e.g., 100 candles)
6. Connect to next node or execute
```

### Watchlist Mode

Fetch klines for all your favorite cryptos at once:

```
1. Configure your watchlist in Binance API credentials (e.g., BTCUSDT, ETHUSDT, SOLUSDT, DOGEUSDT)
2. Add "Binance Kline" node to your workflow
3. Set Symbol Source to "Watchlist"
4. Select interval and limit
5. Execute - node outputs one item per symbol
```

### Example Workflow

```
[Binance Kline (Watchlist)] → [Code Node (Calculate RSI)] → [If (RSI < 30)] → [Slack Notification]
```

## Resources

- [Binance Spot API Documentation](https://binance-docs.github.io/apidocs/spot/en/)
- [n8n Community Nodes Documentation](https://docs.n8n.io/integrations/#community-nodes)
- [n8n Workflow Documentation](https://docs.n8n.io/workflows/)

## Version history

See [CHANGELOG.md](./CHANGELOG.md) for detailed version history.