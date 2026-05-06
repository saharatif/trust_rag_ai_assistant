# Configures structured JSON logging for the application.
#
# Why JSON logs? In production (AWS CloudWatch, Datadog, etc.) logs are ingested
# by log aggregators that parse JSON automatically. Structured logs make it easy
# to filter by level, search by logger name, or extract error traces without
# writing regex patterns against plain text.

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    """Formats every log record as a single-line JSON object.

    Each log line contains: timestamp, level, logger name, message,
    and optionally a full exception traceback if one was captured.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),  # UTC so all environments align
            "level": record.levelname,
            "logger": record.name,       # e.g. "src.rag.ingest" — shows which module logged
            "message": record.getMessage(),
        }
        # Only include the exception key when there is actually an exception to report
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: str = "INFO") -> None:
    """Replace all existing log handlers with a single JSON handler writing to stdout.

    Called once at application startup (in main.py).
    Removes existing handlers first to avoid duplicate log lines if this
    function is called more than once (e.g. during testing).
    """
    root_logger = logging.getLogger()

    # Remove handlers one by one — .clear() is not used because it can disrupt
    # handlers added by third-party libraries before this function runs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Write to stdout (not stderr) so Docker and AWS CloudWatch capture logs cleanly
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger.addHandler(handler)
    root_logger.setLevel(level.upper())
