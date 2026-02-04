# TODO: BinanceOrder Node Integration Tests

Implementation plan for the `BinanceOrder` node integration tests.

## Architecture

Integration tests verify the complete flow from the n8n node -> FastAPI service -> (Mocked) Binance API.

```
┌─────────────────────────────────────────────────────────────┐
│                    Integration Test Runner                    │
├─────────────────────────────────────────────────────────────┤
│  1. Start FastAPI Service (uvicorn subprocess)               │
│     └── Port: 8001+ (Auto-selected)                         │
│                                                              │
│  2. Setup Binance API Mock (nock)                          │
│     └── Intercepts calls to api.binance.com                │
│                                                              │
│  3. Execute Node Tests                                       │
│     └── HTTP calls to localhost:8000/api/binance/order       │
│                                                              │
│  4. Cleanup                                                  │
│     └── Stop FastAPI service (after all tests)               │
│     └── Clean nock mocks (after each test)                   │
└─────────────────────────────────────────────────────────────┘
```

## Coverage (11 Tests)

### Standard Orders
1. **Market BUY**: Basic market order placement.
2. **Limit SELL**: Limit order with price parameter.
3. **Stop Loss**: Order with stopPrice parameter.

### Bracket Orders (TP/SL)
4. **Market + Bracket**: Sequential flow (Market Entry -> fill -> OCO Exit).
5. **Limit + Bracket**: Atomic flow (OTOCO endpoint).
6. **SL Limit Type**: Bracket with limit-based stop loss (stopLimitPrice).
7. **Symbol Normalization**: Verify "btcusdt" (lowercase) is sent as "BTCUSDT".

### Error Handling
8. **Binance API Error (400)**: Proper propagation of errors like "Insufficient balance".
9. **Network Timeout**: Graceful handling of slow responses (>30s).
10. **Validation Error (422)**: FastAPI rejection of malformed payloads.

### Batch Processing
11. **Multiple Items**: Processing 3 different orders in a single node execution.

## Implementation Details

### Service Management
- **Lifecycle**: Start FastAPI once before all tests (`beforeAll`), stop after all tests (`afterAll`).
- **Port**: Use `get-port` to find an available port to avoid conflicts.
- **Process**: Use `spawn` to run `uvicorn` and `tree-kill` for clean shutdown.
- **Health Check**: Wait for `/health` endpoint to be ready before starting tests.

### Mocking Strategy
- **Library**: `nock` to intercept HTTP requests from the FastAPI service to Binance.
- **Isolation**: Clean all mocks after each test (`nock.cleanAll()`).

### Dependencies to Add
```json
"devDependencies": {
  "jest": "^29.7.0",
  "@types/jest": "^29.5.0",
  "axios": "^1.6.0",
  "nock": "^13.5.0",
  "@types/nock": "^11.1.0",
  "tree-kill": "^1.2.2",
  "get-port": "^7.0.0"
}
```

## Test Commands

```bash
# Install dependencies
cd nodes/@stix/n8n-nodes-binance-kline
bun install

# Run all integration tests
bun run test:integration

# Run in watch mode
bun run test:integration:watch
```

## Files to Create
- `test/integration/BinanceOrder.integration.test.ts`
- `test/integration/setup.ts`
- `test/integration/helpers.ts`
- `jest.integration.config.js`
