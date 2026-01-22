"""Pydantic settings for environment configuration."""

from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import ConfigDict


class Settings(BaseSettings):
    """Application settings using Pydantic."""

    env_prefix = "API_"

    # Binance API settings
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False

    # Logging settings
    log_level: str = "INFO"

    # API rate limiting
    rate_limit_per_minute: int = 1200

    # Allow extra environment variables to support shared .env file
    # The API shares the root .env with n8n and other services
    model_config = ConfigDict(env_file="/app/.env", case_sensitive=False, extra="allow")


# Global settings instance
settings = Settings()
