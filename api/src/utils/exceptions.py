"""Custom exceptions for Binance API and trading operations."""


class BinanceAPIError(Exception):
    """Base exception for Binance API errors."""

    def __init__(
        self, message: str, status_code: int = None, response_data: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"[HTTP {self.status_code}] {self.message}"
        return self.message


class BinanceAuthError(BinanceAPIError):
    """Authentication error (invalid API key, signature, etc.)."""

    def __init__(
        self, message: str = "Authentication failed", response_data: dict = None
    ):
        super().__init__(message, status_code=401, response_data=response_data)


class BinanceRateLimitError(BinanceAPIError):
    """Rate limit exceeded error."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message, status_code=429)


class BinanceValidationError(BinanceAPIError):
    """Validation error (invalid parameters, etc.)."""

    def __init__(self, message: str, response_data: dict = None):
        super().__init__(message, status_code=400, response_data=response_data)


class BinanceOrderError(BinanceAPIError):
    """Order-specific error (insufficient balance, invalid symbol, etc.)."""

    def __init__(self, message: str, response_data: dict = None):
        super().__init__(message, status_code=400, response_data=response_data)


class BinanceServerError(BinanceAPIError):
    """Binance server error (5xx errors)."""

    def __init__(
        self, message: str = "Binance server error", response_data: dict = None
    ):
        super().__init__(message, status_code=500, response_data=response_data)


class OrderValidationError(Exception):
    """Validation error for order parameters."""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)

    def __str__(self):
        if self.field:
            return f"[{self.field}] {self.message}"
        return self.message


class DatabaseError(Exception):
    """Database operation error."""

    def __init__(self, message: str, operation: str = None):
        self.message = message
        self.operation = operation
        super().__init__(self.message)

    def __str__(self):
        if self.operation:
            return f"[DB {self.operation}] {self.message}"
        return self.message


class SyncError(Exception):
    """Candlestick sync error."""

    def __init__(self, message: str, symbol: str = None, interval: str = None):
        self.message = message
        self.symbol = symbol
        self.interval = interval
        super().__init__(self.message)

    def __str__(self):
        context = []
        if self.symbol:
            context.append(f"symbol={self.symbol}")
        if self.interval:
            context.append(f"interval={self.interval}")

        if context:
            return f"[{' '.join(context)}] {self.message}"
        return self.message
