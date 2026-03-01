"""
Structured JSON logger — consistent log format across all Lambda functions.
Every log entry includes request_id, function_name, and timestamp.
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON for CloudWatch."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "function": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "local"),
        }
        # Attach request_id from Lambda context if available
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        # Attach extra structured data
        if hasattr(record, "data"):
            log_entry["data"] = record.data
        # Attach exception info
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False, default=str)


def get_logger(name: str, level: str | None = None) -> logging.Logger:
    """
    Create a structured JSON logger.

    Usage:
        logger = get_logger(__name__)
        logger.info("Processing report", extra={"data": {"report_id": "r-123"}})
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    log_level = level or os.environ.get("LOG_LEVEL", "INFO")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    return logger
