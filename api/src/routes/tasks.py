"""Celery task routes for triggering and monitoring background tasks."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.celery_client import celery_client
from services.task_service import task_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskIDResponse(BaseModel):
    """Response containing a task ID."""
    task_id: str
    status_url: str


class TaskStatusResponse(BaseModel):
    """Response containing task status and result."""
    task_id: str
    status: str
    ready: bool
    successful: bool
    result: Optional[Any] = None


class CeleryCallbackRequest(BaseModel):
    """Payload for Celery task callback webhook."""
    task_id: str
    task_name: str
    status: str
    symbol: Optional[str] = None
    interval: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WebhookResponse(BaseModel):
    """Response for webhook receipt."""
    received: bool
    task_id: str
    status: str


class FetchMarketDataRequest(BaseModel):
    """Request to fetch market data."""
    symbol: str = Field(..., example="BTCUSDT")
    interval: str = Field(default="1h", example="1h")
    bars: int = Field(default=100, ge=1, le=10000)


class TrainModelRequest(BaseModel):
    """Request to train a model."""
    symbol: str = Field(..., example="ETHUSDT")
    interval: str = Field(default="15m", example="15m")
    bars: int = Field(default=5000, ge=500)
    warmup_bars: int = Field(default=1000)
    sequence_length: int = Field(default=60)
    output_dir: Optional[str] = None
    model_dir: Optional[str] = None


class RunPredictionRequest(BaseModel):
    """Request to run a prediction."""
    model_path: str = Field(..., example="/app/models/model_ethusdt_15m.joblib")
    symbol: str = Field(..., example="ETHUSDT")
    interval: str = Field(default="15m", example="15m")
    bars: int = Field(default=210, ge=210)


class RunBacktestRequest(BaseModel):
    """Request to run a backtest."""
    signals_path: str = Field(..., example="/app/signals/signals_ethusdt_15m.csv")
    symbol: str = Field(..., example="ETHUSDT")
    interval: str = Field(default="15m", example="15m")
    initial_capital: float = Field(default=10000.0)
    commission: float = Field(default=0.001)


class TrainAndBacktestRequest(BaseModel):
    """Request for the full training and backtesting pipeline."""
    symbol: str = Field(..., example="BTCUSDT")
    interval: str = Field(default="1h", example="1h")
    bars: int = Field(default=2000, ge=500)
    warmup_bars: int = Field(default=500)


@router.post("/fetch-market-data", response_model=TaskIDResponse)
async def fetch_market_data(request: FetchMarketDataRequest):
    """Trigger the fetch_market_data task."""
    try:
        task_id = celery_client.send_task(
            "fetch_market_data", 
            args=[request.symbol.upper(), request.interval, request.bars]
        )
        return TaskIDResponse(
            task_id=task_id, 
            status_url=f"/api/tasks/{task_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train-model", response_model=TaskIDResponse)
async def train_model(request: TrainModelRequest):
    """Trigger the train_model task."""
    try:
        kwargs = {
            "interval": request.interval,
            "bars": request.bars,
            "warmup_bars": request.warmup_bars,
            "sequence_length": request.sequence_length,
        }
        if request.output_dir:
            kwargs["output_dir"] = request.output_dir
        if request.model_dir:
            kwargs["model_dir"] = request.model_dir

        task_id = celery_client.send_task(
            "train_model", 
            args=[request.symbol.upper()], 
            kwargs=kwargs
        )
        return TaskIDResponse(
            task_id=task_id, 
            status_url=f"/api/tasks/{task_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-prediction", response_model=TaskIDResponse)
async def run_prediction(request: RunPredictionRequest):
    """Trigger the run_prediction task."""
    try:
        task_id = celery_client.send_task(
            "run_prediction", 
            args=[request.model_path, request.symbol.upper(), request.interval, request.bars]
        )
        return TaskIDResponse(
            task_id=task_id, 
            status_url=f"/api/tasks/{task_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-backtest", response_model=TaskIDResponse)
async def run_backtest(request: RunBacktestRequest):
    """Trigger the run_backtest task."""
    try:
        task_id = celery_client.send_task(
            "run_backtest", 
            args=[request.signals_path, request.symbol.upper(), request.interval, request.initial_capital, request.commission]
        )
        return TaskIDResponse(
            task_id=task_id, 
            status_url=f"/api/tasks/{task_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train-and-backtest", response_model=TaskIDResponse)
async def train_and_backtest(request: TrainAndBacktestRequest):
    """Trigger the orchestrated train_and_backtest task."""
    try:
        task_id = celery_client.send_task(
            "train_and_backtest", 
            args=[request.symbol.upper(), request.interval, request.bars, request.warmup_bars]
        )
        return TaskIDResponse(
            task_id=task_id, 
            status_url=f"/api/tasks/{task_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Check the status of a Celery task."""
    try:
        status_info = celery_client.get_status(task_id)
        return TaskStatusResponse(**status_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/celery-callback", response_model=WebhookResponse)
async def celery_task_callback(request: CeleryCallbackRequest):
    """Webhook to receive task results from Celery worker."""
    try:
        # Import task_service here if needed to avoid circular imports, 
        # but we already imported it at the top.
        success = await task_service.save_task_result(
            task_id=request.task_id,
            task_name=request.task_name,
            status=request.status,
            symbol=request.symbol,
            interval=request.interval,
            result=request.result,
            error=request.error
        )
        
        if not success:
            logger.warning(f"Failed to persist task result for {request.task_id} to database")
            
        return WebhookResponse(
            received=True,
            task_id=request.task_id,
            status=request.status
        )
    except Exception as e:
        logger.error(f"Error processing celery callback for {request.task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
