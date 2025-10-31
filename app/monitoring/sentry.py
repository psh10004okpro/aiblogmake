"""
Sentry error tracking integration.
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def init_sentry():
    """Initialize Sentry error tracking."""
    if not settings.sentry_dsn:
        logger.info("sentry_disabled", reason="no_dsn_configured")
        return
    
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        release=f"blog-automation@{settings.app_version}",
        
        # Performance monitoring
        traces_sample_rate=settings.sentry_traces_sample_rate,
        
        # Profile monitoring
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        
        # Integrations
        integrations=[
            FastApiIntegration(
                transaction_style="endpoint",
            ),
            SqlalchemyIntegration(),
            RedisIntegration(),
            CeleryIntegration(
                monitor_beat_tasks=True,
            ),
            LoggingIntegration(
                level=None,  # Don't capture logs as breadcrumbs
                event_level=None,  # Don't send logs as events
            ),
        ],
        
        # Error sampling
        sample_rate=1.0,  # Capture all errors
        
        # Additional options
        send_default_pii=False,  # Don't send personally identifiable information
        attach_stacktrace=True,
        before_send=before_send,
    )
    
    logger.info(
        "sentry_initialized",
        environment=settings.app_env,
        traces_sample_rate=settings.sentry_traces_sample_rate
    )


def before_send(event, hint):
    """Process events before sending to Sentry."""
    # Don't send health check errors
    if "healthcheck" in event.get("request", {}).get("url", ""):
        return None
    
    # Don't send expected errors
    exception = hint.get("exc_info", [None, None, None])[1]
    if exception:
        exception_type = type(exception).__name__
        if exception_type in ["ValidationError", "HTTPException"]:
            return None
    
    # Add custom tags
    event.setdefault("tags", {})
    event["tags"]["app_env"] = settings.app_env
    
    return event


def capture_exception(error: Exception, context: dict = None):
    """Capture exception with additional context."""
    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_context(key, value)
        
        sentry_sdk.capture_exception(error)
        logger.error(
            "exception_captured_to_sentry",
            error_type=type(error).__name__,
            error_message=str(error)
        )


def capture_message(message: str, level: str = "info", context: dict = None):
    """Capture message with additional context."""
    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_context(key, value)
        
        sentry_sdk.capture_message(message, level=level)
