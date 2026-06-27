"""Logging configuration."""
import logging
import sys
from contextvars import ContextVar

from app.core.config import settings

# Context var to propagate request ids into logs
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    """Attach request_id from contextvars onto log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        rid = request_id_var.get()
        record.request_id = rid or "-"
        return True


def setup_logging() -> None:
    """Configure application logging."""
    log_level = logging.DEBUG if settings.env == "dev" else logging.INFO
    # On Windows, default console encodings (cp1252) can crash logging when messages
    # include Arabic/Unicode. Force UTF-8 where supported.
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(request_id)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Attach the request id filter to all handlers
    for handler in logging.getLogger().handlers:
        handler.addFilter(RequestIdFilter())
    
    # Set specific log levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def set_request_id(request_id: str | None, token=None):
    """
    Set the request id context for logging.
    If token is provided (from previous set), it will reset the context.
    """
    if token:
        request_id_var.reset(token)
        return token
    return request_id_var.set(request_id)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module."""
    return logging.getLogger(name)


def kv(**fields: object) -> str:
    """
    Format key-value fields for log messages.

    Example:
      logger.info(f\"event=processing_start {kv(session_id=..., step=...)}\")
    """
    parts: list[str] = []
    for key in sorted(fields.keys()):
        value = fields[key]
        if value is None:
            continue
        parts.append(f"{key}={value}")
    return " ".join(parts)
