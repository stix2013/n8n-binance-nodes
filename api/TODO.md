# API Improvement TODO List

## Completed Improvements

### 1. Bug Fixes
- [x] Fixed duplicate code block in `api/src/routes/indicators.py` (removed 50 duplicate lines)
- [x] Fixed incorrect User-Agent version string (was using `api_host` field default `"0.0.0.0"` instead of version)
- [x] Removed redundant `or ""` fallback in API key headers

### 2. API Versioning & Structure
- [x] Added `/v1` prefix to all API routes
- [x] Created lifespan context for proper startup/shutdown in `main.py`
- [x] Added request/response logging middleware
- [x] Added global error handling middleware
- [x] Added `X-Process-Time` header to all responses

### 3. HTTP Client Management
- [x] Implemented connection pooling with `httpx.Limits`
- [x] Added configurable timeouts via settings
- [x] Created reusable HTTP client dependencies (`get_http_client`)
- [x] Added User-Agent header to external API requests

### 4. Pydantic Models (v2 Best Practices)
- [x] Added `ConfigDict` with modern options:
  - `str_strip_whitespace=True`
  - `str_to_upper=True`
  - `validate_assignment=True`
- [x] Replaced deprecated `json_encoders` with `field_serializer`
- [x] Added proper field validation and documentation
- [x] Standardized response models with consistent structure

### 5. Settings Configuration
- [x] Extended settings with all configuration options
- [x] Added API versioning, timeouts, connection limits
- [x] Added indicator period configurations
- [x] Added configurable Binance base URL

### 6. Error Handling
- [x] Consistent error response format:
  - `success` (boolean)
  - `error` (string)
  - `detail` (optional string)
  - `timestamp` (ISO format datetime)
- [x] Fixed deprecated status code constants
- [x] Added structured logging

### 7. Type Safety
- [x] Used `Annotated` types for better type hints
- [x] Created reusable type aliases:
  - `SymbolQuery`
  - `IntervalQuery`
  - `LimitQuery`
  - `PeriodQuery`
  - `MACD*Query`

## Remaining Tasks & Future Improvements

### High Priority
- [ ] Fix remaining test failures (6 tests failing due to mocking pattern changes)
- [ ] Update test mocking to use FastAPI dependency override pattern consistently
- [ ] Add integration tests for the new lifespan context
- [ ] Add version constant to settings for single source of truth

### Medium Priority
- [ ] Add rate limiting middleware (currently configured but not implemented)
- [ ] Add request ID tracking for debugging
- [ ] Implement caching layer for frequently requested data
- [ ] Add API response compression
- [ ] Refactor shared Binance API logic to common module to avoid duplication

### Low Priority
- [ ] Add OpenAPI schema customization
- [ ] Add custom exception handlers for specific error types
- [ ] Implement pagination for large datasets
- [ ] Add WebSocket support for real-time updates
- [ ] Add API key rotation support
- [ ] Implement request validation middleware

### Documentation
- [ ] Update README.md with new API version endpoints
- [ ] Add API changelog
- [ ] Document environment variables
- [ ] Add API usage examples

## Testing Improvements Needed

### Unit Tests
- [ ] Add unit tests for new middleware
- [ ] Add unit tests for settings validation
- [ ] Add unit tests for type aliases

### Integration Tests
- [ ] Add integration tests for dependency injection
- [ ] Add integration tests for error handling middleware
- [ ] Add integration tests for lifespan context

### Performance Tests
- [ ] Add load testing configuration
- [ ] Add connection pool sizing tests
- [ ] Add timeout handling tests

## Code Quality

### Refactoring Opportunities
- [ ] Extract common Binance API logic to shared module
- [ ] Create base router class with common functionality
- [ ] Extract validation utilities to separate module
- [ ] Add type stubs for better IDE support
- [ ] Define API version constant in settings for single source of truth

### Documentation
- [ ] Add docstrings to all public functions
- [ ] Add type hints to all function signatures
- [ ] Create API endpoint documentation
- [ ] Add architecture decision records (ADRs)

## Security Enhancements

### Already Implemented
- [x] API key validation
- [x] Input validation
- [x] Error message sanitization
- [x] Request logging

### Future Enhancements
- [ ] Add request signing for authenticated endpoints
- [ ] Implement API key permissions/scopes
- [ ] Add IP-based rate limiting
- [ ] Implement request validation signatures
- [ ] Add audit logging
- [ ] Implement CORS configuration
- [ ] Add request size limits

## Monitoring & Observability

### Already Implemented
- [x] Request logging
- [x] Process time tracking
- [x] Error logging

### Future Enhancements
- [ ] Add metrics endpoint (Prometheus format)
- [ ] Add distributed tracing support
- [ ] Implement health check details
- [ ] Add custom metrics for API usage
- [ ] Implement alerting on error rates
- [ ] Add logging context enrichment
