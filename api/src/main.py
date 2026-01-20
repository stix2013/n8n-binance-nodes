"""Main FastAPI application with best practices."""

import logging
import sys
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ConfigDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from .models.api_models import RootResponse, HealthResponse, ErrorResponse
    from .models.settings import settings
except ImportError:
    from models.api_models import RootResponse, HealthResponse, ErrorResponse
    from models.settings import settings

load_dotenv("/app/.env")

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

API_VERSION = "v1"
API_TITLE = "n8n Binance API"


@asynccontextmanager
async def lifespan_context(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context for startup and shutdown."""
    logger.info(f"Starting {API_TITLE} {API_VERSION}")
    logger.info(f"Debug mode: {settings.api_debug}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Rate limit: {settings.rate_limit_per_minute} requests/minute")
    yield
    logger.info(f"Shutting down {API_TITLE} {API_VERSION}")


app = FastAPI(
    title=API_TITLE,
    description=f"""API for fetching cryptocurrency prices from Binance with Pydantic type validation and technical indicators.

## Features
- **Price Data**: Get historical kline/candlestick data from Binance
- **Technical Indicators**: RSI and MACD analysis with trading recommendations
- **Type Safety**: Full Pydantic v2 validation
- **API Versioning**: {API_VERSION} prefix for all endpoints

## Rate Limiting
- {settings.rate_limit_per_minute} requests per minute per IP

## Environment
- Debug: {settings.api_debug}
- Log Level: {settings.log_level}
""",
    version=API_VERSION,
    debug=settings.api_debug,
    lifespan=lifespan_context,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


try:
    from .routes import binance, indicators
except ImportError:
    from routes import binance, indicators

app.include_router(binance.router, prefix=f"/{API_VERSION}")
app.include_router(indicators.router, prefix=f"/{API_VERSION}")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log all incoming requests and responses."""
    start_time = datetime.utcnow()
    client_ip = request.client.host if request.client else "unknown"
    request_method = request.method
    request_path = request.url.path

    logger.info(f"Request: {request_method} {request_path} from {client_ip}")

    try:
        response = await call_next(request)
        process_time = (datetime.utcnow() - start_time).total_seconds()

        logger.info(
            f"Response: {request_method} {request_path} - {response.status_code} - {process_time:.4f}s"
        )

        response.headers["X-Process-Time"] = str(process_time)
        return response

    except Exception as e:
        logger.error(f"Request failed: {request_method} {request_path} - {str(e)}")
        raise


@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """Global error handling middleware."""
    try:
        return await call_next(request)
    except Exception as e:
        logger.exception(f"Unhandled exception: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal server error",
                "detail": str(e)
                if settings.api_debug
                else "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@app.get("/", response_model=RootResponse, tags=["Health"])
def read_root() -> RootResponse:
    """Root endpoint - API health check."""
    return RootResponse(message=f"Hello from {API_TITLE} {API_VERSION}!")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check() -> HealthResponse:
    """Health check endpoint for monitoring."""
    return HealthResponse(status="healthy")


@app.get(f"/{API_VERSION}/health", response_model=HealthResponse, tags=["Health"])
def health_check_v1() -> HealthResponse:
    """Versioned health check endpoint."""
    return HealthResponse(status="healthy")
