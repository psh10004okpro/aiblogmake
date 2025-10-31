"""
Structured logging configuration using structlog.

This module sets up JSON-formatted structured logging for production
and human-readable logging for development.
"""

import sys
import logging
from typing import Any
import structlog
from structlog.types import EventDict, Processor
from app.core.config import settings


def add_app_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: EventDict
) -> EventDict:
    """
    Add application context to log entries.

    Args:
        logger: The logger instance.
        method_name: The method name.
        event_dict: The event dictionary.

    Returns:
        EventDict: Modified event dictionary with app context.
    """
    event_dict["app"] = settings.app_name
    event_dict["env"] = settings.app_env
    return event_dict


def censor_sensitive_data(
    logger: logging.Logger,
    method_name: str,
    event_dict: EventDict
) -> EventDict:
    """
    Censor sensitive data from logs (API keys, passwords, etc.).

    Args:
        logger: The logger instance.
        method_name: The method name.
        event_dict: The event dictionary.

    Returns:
        EventDict: Modified event dictionary with censored data.
    """
    sensitive_keys = [
        "password",
        "api_key",
        "token",
        "secret",
        "authorization",
        "credentials",
    ]

    for key in list(event_dict.keys()):
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            event_dict[key] = "***REDACTED***"

    return event_dict


def setup_logging() -> None:
    """
    Configure structured logging for the application.

    Sets up different log formats for development and production:
    - Development: Human-readable colored output
    - Production: JSON-formatted logs for log aggregation
    """
    # Common processors for both dev and prod
    shared_processors: list[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        add_app_context,
        censor_sensitive_data,
    ]

    if settings.is_development:
        # Development: Colorized console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # Production: JSON output for log aggregation
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ]
        renderer = structlog.processors.JSONRenderer()

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )

    # Set log levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> Any:
    """
    Get a structured logger instance.

    Args:
        name: The logger name (typically __name__).

    Returns:
        A structlog logger instance.

    Example:
        ```python
        logger = get_logger(__name__)
        logger.info("user_logged_in", user_id=123, ip_address="192.168.1.1")
        ```
    """
    return structlog.get_logger(name)


# Initialize logging on module import
setup_logging()
