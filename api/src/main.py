"""Main FastAPI application."""

from fastapi import FastAPI
import logging
from dotenv import load_dotenv
import sys
import os

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="n8n Binance API",
    description="API for fetching cryptocurrency prices from Binance",
    version="1.0.0",
)

# Import and include routers
try:
    # Try relative import first
    from .routes import binance
except ImportError:
    # Fall back to absolute import for direct execution
    from routes import binance

# Include routers
app.include_router(binance.router)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Hello from FastAPI!"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
