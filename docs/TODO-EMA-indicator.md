# TODO: Add EMA Indicator to API

## Overview

Add Exponential Moving Average (EMA) indicator calculation to the API, mirroring the existing SMA implementation but with timeframe-specific configurations based on `docs/EMA-strategy-configuration.md`.

## EMA Configuration by Timeframe

| Timeframe | Primary EMAs | Purpose              | Signal Type           |
| --------- | ------------ | -------------------- | --------------------- |
| **1m**    | 9 & 21 EMA   | Scalping/Micro-trend | Quick entries/exits   |
| **15m**   | 12 & 26 EMA  | Day trading          | Momentum shifts       |
| **1h**    | 20 & 50 EMA  | Swing trading        | Trend confirmation    |
| **4h**    | 50 & 200 EMA | Position/Macro trend | Major trend direction |

---

## Implementation Steps

### 1. Update Models (`api/src/models/indicators.py`)

- **Update `IndicatorType` Enum:** Add `EMA = "ema"`
- **Create `EMAResult` Model:**
  ```python
  class EMAResult(BaseModel):
      ema_5: Optional[float] = Field(None, description="5-period EMA (Scalping)")
      ema_8: Optional[float] = Field(None, description="8-period EMA (Scalping)")
      ema_9: Optional[float] = Field(None, description="9-period EMA (1m)")
      ema_12: Optional[float] = Field(None, description="12-period EMA (15m)")
      ema_20: Optional[float] = Field(None, description="20-period EMA (1h)")
      ema_21: Optional[float] = Field(None, description="21-period EMA (1m)")
      ema_26: Optional[float] = Field(None, description="26-period EMA (15m)")
      ema_50: Optional[float] = Field(None, description="50-period EMA (1h/4h)")
      ema_200: Optional[float] = Field(None, description="200-period EMA (4h)")
      signal: Literal["BULLISH", "BEARISH", "NEUTRAL"]
  ```
- **Update `TechnicalAnalysisResponse`:** Add `ema: EMAResult` field.

---

### 2. Core Logic (`api/src/utils/indicators.py`)

- **Implement `calculate_emas`**:
  - Validate inputs (prices not empty, windows not empty, sufficient data)
  - Use `pandas.Series.ewm(span=window, adjust=False, min_periods=window).mean()` for calculation
  - Return `Dict[int, float]` mapping window size to current EMA value
  - Round to 6 decimal places

- **Implement `generate_ema_signal`**:
  - Find shortest and longest EMA from the provided dictionary
  - Signal logic (mirrors SMA):
    - **BULLISH**: `current_price > longest_ema AND shortest_ema > longest_ema` (Golden Cross)
    - **BEARISH**: `current_price < longest_ema AND shortest_ema < longest_ema` (Death Cross)
    - **NEUTRAL**: Everything else

---

### 3. Endpoints (`api/src/routes/indicators.py`)

- **Configuration**:
  ```python
  INTERVAL_EMA_WINDOWS = {
      "1m": [9, 21],
      "5m": [5, 8],
      "15m": [12, 26],
      "1h": [20, 50],
      "4h": [50, 200],
      "1d": [50, 200],
  }
  ```
- **Helper Function**: `get_ema_windows(interval)` returns the window list (default: `[20, 50]`)

- **New Endpoint: `GET /api/indicators/ema`**:
  - Query params: `symbol`, `interval`, `limit` (optional)
  - Fetches price data from Binance
  - Calculates EMAs based on interval
  - Returns `EMAResult`

- **Update `GET /api/indicators/analysis`**:
  - Call `calculate_emas` and `generate_ema_signal`
  - Include `ema` field in response

- **Update `GET /api/indicators/{indicator_name}`**:
  - Add support for `"ema"` indicator type

---

## Unit Testing (`api/tests/test_technical_indicators.py`)

### Core Logic Tests

- `test_calculate_emas_valid_data`: Verify correct keys in returned dictionary
- `test_calculate_emas_insufficient_data`: Verify ValueError when data < max window
- `test_calculate_emas_empty_prices`: Verify ValueError for empty list
- `test_calculate_emas_empty_windows`: Verify ValueError for empty windows list
- `test_mathematical_accuracy_emas`: Compare against direct pandas calculation

### Signal Logic Tests

- `test_generate_ema_signal_bullish`: Price > long AND short > long
- `test_generate_ema_signal_bearish`: Price < long AND short < long
- `test_generate_ema_signal_neutral`: Mixed/matched conditions
- `test_generate_ema_signal_empty`: Returns NEUTRAL when empty dict

### Endpoint Integration Tests

- `test_ema_endpoint_success`: Test `/api/indicators/ema` returns correct structure
- `test_ema_endpoint_15m`: Verify 15m interval populates ema_12 and ema_26
- `test_ema_endpoint_4h`: Verify 4h interval populates ema_50 and ema_200
- `test_analysis_endpoint_includes_ema`: Verify combined response has EMA data
- `test_single_indicator_ema_endpoint`: Verify dynamic endpoint works with "ema"

---

## Notes

- Use `pandas.Series.ewm(span=window, adjust=False, min_periods=window).mean()` for EMA calculation
- Signal logic mirrors existing SMA implementation
- All EMA values rounded to 6 decimal places
