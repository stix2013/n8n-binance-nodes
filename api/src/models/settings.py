"""Pydantic settings for environment configuration."""

from typing import Optional
from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings using Pydantic v2."""

    model_config = ConfigDict(
        env_file="/app/.env",
        case_sensitive=False,
        extra="allow",
        populate_by_name=True,
    )

    binance_api_key: Optional[str] = Field(
        default=None,
        alias="BINANCE_API_KEY",
        description="Binance API key for authenticated requests",
    )
    binance_api_secret: Optional[str] = Field(
        default=None,
        alias="BINANCE_API_SECRET",
        description="Binance API secret for authenticated requests",
    )

    binance_base_url: str = Field(
        default="https://api.binance.com",
        alias="BINANCE_BASE_URL",
        description="Base URL for Binance API",
    )

    api_host: str = Field(
        default="0.0.0.0",
        alias="API_HOST",
        description="API server host",
    )
    api_port: int = Field(
        default=8000,
        alias="API_PORT",
        ge=1,
        le=65535,
        description="API server port",
    )
    api_debug: bool = Field(
        default=False,
        alias="API_DEBUG",
        description="Enable debug mode",
    )

    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    rate_limit_per_minute: int = Field(
        default=1200,
        alias="RATE_LIMIT_PER_MINUTE",
        ge=1,
        description="Rate limit requests per minute",
    )

    request_timeout: float = Field(
        default=30.0,
        alias="REQUEST_TIMEOUT",
        ge=1.0,
        le=120.0,
        description="Request timeout in seconds",
    )

    http_client_max_connections: int = Field(
        default=10,
        alias="HTTP_CLIENT_MAX_CONNECTIONS",
        ge=1,
        description="Maximum HTTP client connections",
    )
    http_client_max_keepalive_connections: int = Field(
        default=5,
        alias="HTTP_CLIENT_MAX_KEEPALIVE_CONNECTIONS",
        ge=0,
        description="Maximum keep-alive connections",
    )

    default_kline_limit: int = Field(
        default=100,
        alias="DEFAULT_KLINE_LIMIT",
        ge=1,
        le=1000,
        description="Default number of klines to return",
    )
    max_kline_limit: int = Field(
        default=1000,
        alias="MAX_KLINE_LIMIT",
        ge=1,
        le=1000,
        description="Maximum number of klines allowed",
    )

    min_rsi_period: int = Field(
        default=2,
        alias="MIN_RSI_PERIOD",
        ge=2,
        le=100,
        description="Minimum RSI calculation period",
    )
    default_rsi_period: int = Field(
        default=14,
        alias="DEFAULT_RSI_PERIOD",
        ge=2,
        le=100,
        description="Default RSI calculation period",
    )

    min_macd_fast: int = Field(
        default=2,
        alias="MIN_MACD_FAST",
        ge=2,
        le=50,
        description="Minimum MACD fast period",
    )
    min_macd_slow: int = Field(
        default=31,
        alias="MIN_MACD_SLOW",
        ge=31,
        le=100,
        description="Minimum MACD slow period (must be > fast)",
    )
    default_macd_fast: int = Field(
        default=12,
        alias="DEFAULT_MACD_FAST",
        ge=2,
        le=50,
        description="Default MACD fast period",
    )
    default_macd_slow: int = Field(
        default=26,
        alias="DEFAULT_MACD_SLOW",
        ge=26,
        le=100,
        description="Default MACD slow period",
    )
    default_macd_signal: int = Field(
        default=9,
        alias="DEFAULT_MACD_SIGNAL",
        ge=2,
        le=50,
        description="Default MACD signal line period",
    )

    min_candles_for_analysis: int = Field(
        default=30,
        alias="MIN_CANDLES_FOR_ANALYSIS",
        ge=10,
        description="Minimum candles required for technical analysis",
    )


settings = Settings()
