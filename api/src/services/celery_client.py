import logging
import os

from celery import Celery

logger = logging.getLogger(__name__)


class CeleryClient:
    """Client for interacting with Celery workers."""

    def __init__(self, broker_url: str = None):
        self.broker_url = broker_url or os.getenv(
            "CELERY_BROKER_URL", "redis://redis_broker:6379/0"
        )
        self.app = Celery("crypto_analysis", broker=self.broker_url)

        # Configure the client to match the worker's expected configuration
        self.app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="UTC",
            enable_utc=True,
        )
        logger.info(f"CeleryClient initialized with broker: {self.broker_url}")

    def send_task(self, task_name: str, args: list = None, kwargs: dict = None):
        """Send a task to the Celery worker."""
        try:
            logger.info(f"Sending task {task_name} with args={args}, kwargs={kwargs}")
            result = self.app.send_task(task_name, args=args or [], kwargs=kwargs or {})
            return result.id
        except Exception as e:
            logger.error(f"Failed to send task {task_name}: {e}")
            raise

    def get_status(self, task_id: str):
        """Get the status and result of a task."""
        try:
            result = self.app.AsyncResult(task_id)
            return {
                "task_id": task_id,
                "status": result.status,
                "result": result.result if result.ready() else None,
                "ready": result.ready(),
                "successful": result.successful() if result.ready() else False,
            }
        except Exception as e:
            logger.error(f"Failed to get status for task {task_id}: {e}")
            raise


# Global instance
celery_client = CeleryClient()
