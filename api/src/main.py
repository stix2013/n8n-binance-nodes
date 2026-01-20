"""Main FastAPI application."""

from fastapi import FastAPI
import logging
from dotenv import load_dotenv
import sys
import os

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Pydantic models and settings
try:
    from .models.api_models import RootResponse, HealthResponse, ErrorResponse
    from .models.settings import settings
except ImportError:
    from models.api_models import RootResponse, HealthResponse, ErrorResponse
    from models.settings import settings

# Load environment variables
load_dotenv()

# Set up logging based on settings
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)

# Create FastAPI app with settings
app = FastAPI(
    title="n8n Binance API",
    description="API for fetching cryptocurrency prices from Binance with Pydantic type validation and technical indicators",
    version="1.1.0",
    debug=settings.api_debug,
)

# Import and include routers
try:
    # Try relative import first
    from .routes import binance, indicators
except ImportError:
    # Fall back to absolute import for direct execution
    from routes import binance, indicators

# Include routers
app.include_router(binance.router)
app.include_router(indicators.router)


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
