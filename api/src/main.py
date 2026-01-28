"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import sys
import os

from fastapi import FastAPI

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv("/app/.env")

# Import Pydantic models and settings
try:
    from .models.api_models import RootResponse, HealthResponse, ErrorResponse
    from .models.settings import settings
    from .config.logging_config import setup_logging
    from .middleware.logging_middleware import ErrorLoggingMiddleware
except ImportError:
    from models.api_models import RootResponse, HealthResponse, ErrorResponse
    from models.settings import settings
    from config.logging_config import setup_logging
    from middleware.logging_middleware import ErrorLoggingMiddleware

# Set up logging
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    """Lifespan context manager for startup/shutdown events."""
    logger.info(
        "API starting up",
        extra={
            "event": "startup",
            "environment": os.getenv("ENVIRONMENT", "development"),
        },
    )
    yield
    logger.info("API shutting down", extra={"event": "shutdown"})


# Create FastAPI app with settings
app = FastAPI(
    title="n8n Binance API",
    description="API for fetching cryptocurrency prices from Binance with Pydantic type validation and technical indicators",
    version="1.1.0",
    debug=settings.api_debug,
    lifespan=lifespan,
)

# Register middleware
app.add_middleware(ErrorLoggingMiddleware)

# Import and include routers
try:
    # Try relative import first
    from .routes import binance, indicators, ingest
except ImportError:
    # Fall back to absolute import for direct execution
    from routes import binance, indicators, ingest

# Include routers
app.include_router(binance.router)
app.include_router(indicators.router)
app.include_router(ingest.router)


@app.get("/", response_model=RootResponse)
def read_root():
    """Root endpoint."""
    return RootResponse(message="Hello from FastAPI with Pydantic type checking!")


@app.get(
    "/health", response_model=HealthResponse, responses={500: {"model": ErrorResponse}}
)
def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy")
