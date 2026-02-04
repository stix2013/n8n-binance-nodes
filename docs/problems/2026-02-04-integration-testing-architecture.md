# Integration Testing Architecture: Problems & Solutions
**Date:** 2026-02-04  
**Topic:** Implementation of Integration Tests for n8n Binance Nodes (TypeScript -> Python -> External API)

## 1. The "Invisible Mock" Problem (Process Isolation)

### Issue
We initially attempted to use `nock` (a standard Node.js mocking library) to intercept HTTP requests to the Binance API.
- **Expectation:** `nock` would intercept calls made to `https://api.binance.com`.
- **Reality:** Tests failed with `401 Unauthorized`. The Python backend (`uvicorn`) was spawned as a *child process*. `nock` only intercepts traffic within the Node.js process where it runs. It has no control over external processes or the OS network stack. The Python backend was bypassing the mock and hitting the real Binance API.

### Solution
We pivoted to a **Local Mock Server** architecture.
1. Spun up a real `express` server on a dynamic port (e.g., `127.0.0.1:45769`) during test setup.
2. Modified the Python backend (`api/src/routes/binance.py`) to accept a `BINANCE_BASE_URL` environment variable.
3. Injected the mock server's address into the Python subprocess environment.
4. This forced the Python backend to talk to our local server instead of the real internet.

## 2. ESM vs CommonJS Compatibility (`get-port`)

### Issue
The integration tests required finding free ports dynamically. We installed `get-port` via `bun add get-port`.
- **Error:** `SyntaxError: Cannot use import statement outside a module`
- **Cause:** Recent versions of `get-port` (v6+) are Pure ESM. Our project uses `ts-jest` with a CommonJS configuration. Jest has known friction when mixing CJS and ESM without extensive configuration changes (e.g., `transformIgnorePatterns`).

### Solution
We downgraded the dependency to a stable CommonJS version:
```bash
bun remove get-port
bun add -d get-port@5.1.1
```
This resolved the syntax error immediately without requiring a rewrite of the Jest configuration.

## 3. Hardcoded Service Discovery

### Issue
The n8n nodes contained hardcoded URLs specifically for the Docker environment:
```typescript
url: 'http://api:8000/api/binance/order'
```
This works in production/Docker, but fails locally because the `api` hostname doesn't exist on the host machine, and the port might be occupied (requiring dynamic port assignment in tests).

### Solution
We refactored the nodes to use environment variables with a fallback:
```typescript
const baseUrl = process.env.N8N_BINANCE_API_URL || 'http://api:8000';
```
In integration tests, we set `N8N_BINANCE_API_URL` to `http://127.0.0.1:{dynamic_port}`.

## 4. Pydantic Strictness & Data Contracts

### Issue
FastAPI uses Pydantic for strict response validation.
- **Failure:** Tests failed with `500 Internal Server Error` from the Python backend.
- **Cause:** Our initial mock responses in the test file were missing fields (e.g., `symbol` in an OTOCO response). Pydantic validation failed in the Python layer before sending the response back to Node.js.

### Solution
We updated the mock objects in `BinanceOrder.integration.test.ts` to strictly adhere to the `OrderResponse` Pydantic model defined in `api/src/models/api_models.py`.

## 5. Cross-Language Data Serialization

### Issue
Tests failed assertions when matching request parameters.
- **Assertion:** `expect(params.price).toBe(2000)`
- **Reality:** Received `'2000.0'` (string).
- **Cause:** Python's `httpx` library and the query parameter stringification process convert floating-point numbers to strings, and Python often adds a decimal place to floats (`2000` -> `2000.0`).

### Solution
We adjusted the test expectations to match the specific string format produced by the Python backend's serialization logic:
```typescript
expect(requests[0].query).toMatchObject({
    price: '2000.0',
    // ...
});
```

## 6. Express 5 Routing (Path-to-Regexp)

### Issue
We used `app.all('*', ...)` in the mock server.
- **Error:** `TypeError: Missing parameter name at index 1`
- **Cause:** Express 5 uses a newer version of `path-to-regexp` which handles wildcards differently or is stricter about parsing.

### Solution
We switched to a generic middleware handler which captures all requests robustly:
```typescript
app.use((req, res) => {
    // Catch-all logic
});
```
