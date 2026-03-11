import logging
import json
from datetime import UTC, datetime
from typing import Any, Dict, Optional

from .database import db

logger = logging.getLogger(__name__)

class TaskService:
    """Service for managing Celery task results and status."""

    async def save_task_result(
        self,
        task_id: str,
        task_name: str,
        status: str,
        symbol: Optional[str] = None,
        interval: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> bool:
        """Save a Celery task result to the database."""
        completed_at = datetime.now(UTC) if status.upper() in ("SUCCESS", "FAILURE") else None
        
        # Serialize dict to JSON string for JSONB column
        json_result = json.dumps(result) if result is not None else None
        
        query = """
        INSERT INTO celery_task_results (
            task_id, task_name, status, symbol, interval, result, error, completed_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (task_id) DO UPDATE SET
            status = EXCLUDED.status,
            symbol = COALESCE(EXCLUDED.symbol, celery_task_results.symbol),
            interval = COALESCE(EXCLUDED.interval, celery_task_results.interval),
            result = COALESCE(EXCLUDED.result, celery_task_results.result),
            error = COALESCE(EXCLUDED.error, celery_task_results.error),
            completed_at = COALESCE(EXCLUDED.completed_at, celery_task_results.completed_at)
        """
        
        try:
            # Use db.pool directly as in trading_service.py
            await db.pool.execute(
                query,
                task_id,
                task_name,
                status.upper(),
                symbol,
                interval,
                json_result,
                error,
                completed_at
            )
            logger.info(f"Saved task result for {task_id} ({task_name}) with status {status}")
            return True
        except Exception as e:
            logger.error(f"Failed to save task result for {task_id}: {e}")
            return False

# Global instance
task_service = TaskService()
