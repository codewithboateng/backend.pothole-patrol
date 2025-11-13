import json
import logging
import sys
import traceback
from typing import Any


class JSONFormatter(logging.Formatter):
    """
    Enterprise-grade structured JSON log formatter.

    - 12-Factor compliant (stdout logging)
    - Includes request context, user context, and performance metadata
    - Full exception traceback support for error-level logs
    """

    def format(self, record: logging.LogRecord) -> str:
        log: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # --- Optional environment info (service name, environment, git version, etc.) ---
        for field in ("service", "env", "version"):
            value = getattr(record, field, None)
            if value is not None:
                log[field] = value

        # --- Request context (added by middleware if configured) ---
        for field in ("request_id", "user_id", "method", "path", "ip", "duration_ms"):
            value = getattr(record, field, None)
            if value is not None:
                log[field] = value

        # --- Exception details (stack trace, type, message) ---
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            log["exception_type"] = exc_type.__name__
            log["exception_message"] = str(exc_value)
            log["traceback"] = "".join(
                traceback.format_exception(exc_type, exc_value, exc_tb)
            )

        return json.dumps(log)


def default_logging_config(level: str = "INFO") -> dict[str, Any]:
    return {
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "json": {"()": "mainProj.settings.logging.JSONFormatter"},
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": sys.stdout,
            },
        },

        "root": {
            "handlers": ["console"],
            "level": level,
        },

        "loggers": {
            "django.server": {
                "handlers": ["console"],
                "level": level,
                "propagate": False,
            },
        },
    }
