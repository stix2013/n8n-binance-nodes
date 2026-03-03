# TODO: Prediction API Feature

## Overview
Add inference capability to predict trading signals using trained models via REST API.

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `api/src/routes/crypto.py` | Create | New route file with `/api/crypto/predict` endpoint |
| `api/src/main.py` | Modify | Register the new `crypto` router |

## Implementation Steps

### Step 1: Setup Worktree
- Create worktree: `feat/prediction-api`
- Copy `.env` file to worktree

### Step 2: Create Prediction Route
**File**: `api/src/routes/crypto.py`

- **Endpoint**: `POST /api/crypto/predict`
- **Request Body**:
  ```json
  {
    "symbol": "BNBUSDT",
    "interval": "1m",
    "bars": 200
  }
  ```
- **Response**:
  ```json
  {
    "symbol": "BNBUSDT",
    "signal": "LONG"
  }
  ```

### Step 3: Register Router
**File**: `api/src/main.py`
- Import and include `crypto` router

### Step 4: Test
```bash
curl -X POST http://localhost:8000/api/crypto/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BNBUSDT", "interval": "1m"}'
```

## Signal Mapping
| Generator Signal | API Response |
|-----------------|-------------|
| `ENTRY_LONG` | `"LONG"` |
| `ENTRY_SHORT` | `"SHORT"` |
| No signal | `"WAIT"` |

## Model Filename Convention
`model_{symbol.lower()}_{interval.replace('m', 'min')}.joblib`

Example: `BNBUSDT` + `1m` → `model_bnbusdt_1min.joblib`
