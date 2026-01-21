import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        extra_data = {}
        for key in (
            "type",
            "event",
            "environment",
            "status_code",
            "method",
            "path",
            "query_params",
            "client_host",
            "process_time_ms",
            "user_agent",
            "exception",
        ):
            if hasattr(record, key):
                extra_data[key] = getattr(record, key)
        if extra_data:
            log_data["extra"] = extra_data
        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO") -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.ERROR)

    for logger_name in ["httpx", "httpcore", "urllib3"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
