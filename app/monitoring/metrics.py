"""
Prometheus metrics collection.
"""

import time
from typing import Callable
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

# HTTP 요청 메트릭
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method", "endpoint"]
)

# 비즈니스 메트릭
keywords_researched_total = Counter(
    "keywords_researched_total",
    "Total keywords researched",
    ["source"]
)

content_generated_total = Counter(
    "content_generated_total",
    "Total content pieces generated",
    ["status"]
)

images_generated_total = Counter(
    "images_generated_total",
    "Total images generated",
    ["type"]
)

posts_published_total = Counter(
    "posts_published_total",
    "Total posts published",
    ["platform"]
)

# 성능 메트릭
content_generation_duration_seconds = Histogram(
    "content_generation_duration_seconds",
    "Content generation duration in seconds"
)

keyword_research_duration_seconds = Histogram(
    "keyword_research_duration_seconds",
    "Keyword research duration in seconds"
)

image_generation_duration_seconds = Histogram(
    "image_generation_duration_seconds",
    "Image generation duration in seconds"
)

# 에러 메트릭
errors_total = Counter(
    "errors_total",
    "Total errors",
    ["error_type", "service"]
)

api_errors_total = Counter(
    "api_errors_total",
    "Total API errors",
    ["api_name", "status_code"]
)

# 시스템 메트릭
active_tasks = Gauge(
    "active_tasks",
    "Number of active Celery tasks",
    ["task_name"]
)

database_connections = Gauge(
    "database_connections",
    "Number of active database connections"
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Prometheus metrics middleware for FastAPI."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)
        
        method = request.method
        endpoint = request.url.path
        
        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        
        # Measure request duration
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Record error
            errors_total.labels(
                error_type=type(e).__name__,
                service="http"
            ).inc()
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status_code
            ).inc()
            
            http_requests_in_progress.labels(
                method=method,
                endpoint=endpoint
            ).dec()
        
        return response


def metrics_middleware():
    """Get Prometheus middleware instance."""
    return PrometheusMiddleware


def get_metrics_handler():
    """Get metrics endpoint handler."""
    async def metrics_endpoint():
        return StarletteResponse(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    return metrics_endpoint
