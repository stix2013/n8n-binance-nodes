# Plan: Add Data Ingestion from n8n

This document outlines the plan to enable the API to receive and analyze kline data directly from the `@stix/n8n-nodes-binance-kline` node.

## 1. Data Modeling (`api/src/models/ingest_models.py`)
- [x] Create `N8NKline` model to match the string-based JSON output of the n8n node.
- [x] Create `N8NNodeOutput` model to represent the full payload.
- [x] Create `AnalysisParameters` model for optional RSI/MACD configuration.
- [x] Create `IngestRequest` and `IngestResponse` models.

## 2. Ingestion Route (`api/src/routes/ingest.py`)
- [x] Create `POST /api/ingest/analyze` endpoint.
- [x] Implement logic to:
    - Receive n8n payload.
    - Convert string prices to floats.
    - Calculate RSI and MACD using `TechnicalIndicators` utility.
    - Generate trading recommendation.
    - Return structured analysis response.

## 3. API Registration (`api/src/main.py`)
- [x] Import the new `ingest` router.
- [x] Mount the router with `app.include_router(ingest.router)`.

## 4. Verification & Testing
- [x] Create unit tests in `api/tests/test_ingest.py`.
- [x] Fix import issues in tests.
- [x] Run `pytest` to verify success.

## 5. Documentation
- [x] Update API documentation if necessary.
