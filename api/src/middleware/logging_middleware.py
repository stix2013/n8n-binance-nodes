import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            if response.status_code >= 400:
                self._log_error(request, response.status_code, process_time, None)
            return response
        except Exception as exc:
            process_time = (time.time() - start_time) * 1000
            self._log_error(request, 500, process_time, exc)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )

    def _log_error(
        self,
        request: Request,
        status_code: int,
        process_time: float,
        exc: Exception | None,
    ) -> None:
        logger = logging.getLogger("api.request")
        extra = {
            "type": "request_error",
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "status_code": status_code,
            "client_host": request.client.host if request.client else None,
            "process_time_ms": round(process_time, 2),
            "user_agent": request.headers.get("user-agent"),
        }
        if exc:
            extra["exception"] = f"{type(exc).__name__}: {str(exc)}"
        logger.error("Request failed", extra=extra)
