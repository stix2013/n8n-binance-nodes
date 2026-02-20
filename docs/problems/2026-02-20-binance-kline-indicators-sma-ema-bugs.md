# Binance Kline Indicators - SMA/EMA Calculation and Output Bugs

**Date:** 2026-02-20
**Components:** `BinanceKlineIndicators` (n8n node), `/api/ingest/analyze` (FastAPI backend)

## Problems Encountered

1. **400 Bad Request on Insufficient Data:** 
   When using the `BinanceKlineIndicators` node, if the previous `BinanceKline` node returned fewer candles (e.g., default `limit=50`) than required for a long-period indicator (e.g., `sma_200` requires 200 candles), the FastAPI backend would throw a `400 Bad Request` error: `"Insufficient data for SMA calculation. Need at least 200 prices, got 50"`.
   Additionally, the n8n node surfaced this as a generic `NodeOperationError: Request failed with status code 400` without revealing the underlying cause.

2. **Indicators Calculated When Disabled:** 
   Setting the `sma_enabled` or `ema_enabled` parameters to `false` in the n8n node UI had no effect; the API backend still calculated and returned them.

3. **Empty Indicator Objects in Output:**
   Even after fixing the backend to skip calculations when disabled, the API still returned the `sma` and `ema` properties in the JSON response (e.g., containing `null` or default values). The requirement was to completely omit these properties from the JSON output if they were disabled.

## Root Causes

1. **Strict Window Requirements:** The `get_sma_windows` and `get_ema_windows` functions defined static arrays of windows (like `[20, 50, 200]`) based on the interval. The `TechnicalIndicators.calculate_sma` method strictly validated that `len(prices) >= max(windows)`.
2. **Missing Node Error Parsing:** The `try/catch` block in the n8n node's `execute` method swallowed the specific API error message payload, throwing a generic HTTP request error.
3. **Missing Parameter Logic & Strict Serialization:** The API's `analyze_n8n_data` route did not check `params.sma_enabled` or `params.ema_enabled` before calculation. Furthermore, FastAPI/Pydantic serializes all defined response model properties by default, even if they are `None`.

## Solutions Implemented

### 1. Dynamic Window Filtering (API)
Modified the calculation logic in `api/src/routes/ingest.py` to filter out windows that are larger than the available dataset:
```python
sma_windows = get_sma_windows(request.data.interval)
valid_sma_windows = [w for w in sma_windows if w <= len(prices)]
if valid_sma_windows:
    sma_values = TechnicalIndicators.calculate_sma(prices, valid_sma_windows)
```

### 2. Improved Error Surfacing (n8n Node)
Updated `BinanceKlineIndicators.node.ts` to use `NodeApiError` when an HTTP status code is present. This correctly maps the API's JSON error response to the n8n UI, showing the exact reason for the failure.
```typescript
if (error.statusCode) {
    throw new NodeApiError(this.getNode(), error as any, { itemIndex: i });
}
```

### 3. Conditional Execution (API)
Wrapped the SMA and EMA calculations in `if params.sma_enabled:` and `if params.ema_enabled:` checks to skip processing completely when disabled.

### 4. Optional Properties & Exclude None (API/Pydantic)
1. In `api/src/models/ingest_models.py`, updated `IngestResponse` to make `sma` and `ema` truly optional:
   ```python
   sma: Optional[SMAResult] = None
   ema: Optional[EMAResult] = None
   ```
2. In `api/src/routes/ingest.py`, updated the route decorator to exclude `None` values from the serialized JSON:
   ```python
   @router.post("/analyze", response_model=IngestResponse, response_model_exclude_none=True)
   ```
3. Assigned `None` to `sma_result` and `ema_result` variables when their respective `enabled` flags were false, resulting in complete omission from the n8n output.