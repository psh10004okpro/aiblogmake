"""
Monitoring and observability module.

This module provides comprehensive monitoring capabilities including:
- Prometheus metrics collection
- Advanced health checks
- Sentry error tracking
"""

from .metrics import (
    PrometheusMiddleware,
    REGISTRY,
    http_requests_total,
    http_request_duration_seconds,
    http_requests_in_progress,
    keywords_researched_total,
    content_generated_total,
    images_generated_total,
    posts_published_total,
    errors_total,
)
from .healthcheck import HealthCheckService, HealthStatus
from .sentry import init_sentry, capture_exception, capture_message

__all__ = [
    # Metrics
    "PrometheusMiddleware",
    "REGISTRY",
    "http_requests_total",
    "http_request_duration_seconds",
    "http_requests_in_progress",
    "keywords_researched_total",
    "content_generated_total",
    "images_generated_total",
    "posts_published_total",
    "errors_total",
    # Health checks
    "HealthCheckService",
    "HealthStatus",
    # Sentry
    "init_sentry",
    "capture_exception",
    "capture_message",
]
