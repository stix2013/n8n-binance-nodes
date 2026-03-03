"""Training API routes for model training management."""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from celery.result import AsyncResult

from src.config.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/training", tags=["training"])


class TrainingRequest(BaseModel):
    """Request model for starting a training task."""

    symbol: str = Field(..., description="Trading pair symbol (e.g., ETHUSDT, BTCUSDT)")
    interval: str = Field(
        default="15m", description="Kline interval (e.g., 15m, 1h, 4h)"
    )
    bars: int = Field(
        default=5000, description="Number of historical bars to fetch", ge=100, le=10000
    )
    warmup_bars: int = Field(
        default=1000, description="Number of bars for initial training", ge=100, le=5000
    )
    sequence_length: int = Field(
        default=60, description="Sequence length for LSTM models", ge=10, le=200
    )


class TrainingResponse(BaseModel):
    """Response model for training task submission."""

    task_id: str
    status: str
    message: str


class TrainingStatusResponse(BaseModel):
    """Response model for training task status."""

    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
    progress: Optional[int] = None


class ModelInfo(BaseModel):
    """Model information."""

    symbol: str
    interval: str
    path: str
    filename: str
    size_bytes: Optional[int] = None


@router.post("/train", response_model=TrainingResponse)
def start_training(request: TrainingRequest):
    """
    Start a background training task for a specific symbol and interval.

    The training runs asynchronously using Celery workers.
    Use the returned task_id to check the status.
    """
    logger.info(f"Received training request for {request.symbol} {request.interval}")

    try:
        # Queue the training task
        task = celery_app.send_task(
            "src.tasks.training.train_online_model",
            args=[
                request.symbol.upper(),
                request.interval,
                request.bars,
                request.warmup_bars,
                request.sequence_length,
            ],
        )

        logger.info(f"Training task queued: {task.id}")

        return TrainingResponse(
            task_id=task.id,
            status="PENDING",
            message=f"Training task for {request.symbol.upper()} {request.interval} has been queued",
        )

    except Exception as e:
        logger.error(f"Failed to queue training task: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start training: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=TrainingStatusResponse)
def get_training_status(task_id: str):
    """
    Get the status of a training task.

    Returns:
        - PENDING: Task is waiting to be executed
        - STARTED: Task is currently executing
        - PROGRESS: Task is executing with progress information
        - SUCCESS: Task completed successfully
        - FAILURE: Task failed
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        response = TrainingStatusResponse(
            task_id=task_id,
            status=task_result.state,
        )

        if task_result.state == "PENDING":
            response.message = "Task is waiting to be executed"

        elif task_result.state == "STARTED":
            response.message = "Task is currently executing"

        elif task_result.state == "PROGRESS":
            response.status = "PROGRESS"
            if task_result.info and isinstance(task_result.info, dict):
                response.progress = task_result.info.get("progress", 0)
                response.message = f"Training in progress: {response.progress}%"

        elif task_result.state == "SUCCESS":
            response.status = "SUCCESS"
            response.result = task_result.result
            response.message = "Training completed successfully"

        elif task_result.state == "FAILURE":
            response.status = "FAILURE"
            response.error = (
                str(task_result.result) if task_result.result else "Unknown error"
            )
            response.message = "Training failed"

        else:
            response.message = f"Task state: {task_result.state}"

        return response

    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/models", response_model=List[ModelInfo])
def list_trained_models():
    """
    List all available trained models.

    Scans the /app/models directory for .joblib files and returns metadata.
    """
    import os
    from pathlib import Path

    models_dir = Path("/app/models")
    models = []

    try:
        if not models_dir.exists():
            logger.info("Models directory does not exist yet")
            return []

        for model_file in models_dir.glob("*.joblib"):
            # Parse filename: model_{symbol}_{interval}.joblib
            filename = model_file.name
            parts = filename.replace(".joblib", "").split("_")

            if len(parts) >= 3 and parts[0] == "model":
                symbol = parts[1].upper()
                interval = parts[2].replace("min", "m")

                models.append(
                    ModelInfo(
                        symbol=symbol,
                        interval=interval,
                        path=str(model_file),
                        filename=filename,
                        size_bytes=model_file.stat().st_size,
                    )
                )
            else:
                # Try to extract what we can
                models.append(
                    ModelInfo(
                        symbol="UNKNOWN",
                        interval="UNKNOWN",
                        path=str(model_file),
                        filename=filename,
                        size_bytes=model_file.stat().st_size,
                    )
                )

        logger.info(f"Found {len(models)} trained models")
        return models

    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.delete("/models/{filename}")
def delete_model(filename: str):
    """
    Delete a trained model file.

    Args:
        filename: The model filename (e.g., model_ethusdt_15min.joblib)
    """
    from pathlib import Path

    models_dir = Path("/app/models")
    model_path = models_dir / filename

    if not model_path.exists():
        raise HTTPException(status_code=404, detail=f"Model {filename} not found")

    try:
        model_path.unlink()
        logger.info(f"Deleted model: {filename}")
        return {"message": f"Model {filename} deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete model {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")
