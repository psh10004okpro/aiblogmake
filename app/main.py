"""
FastAPI application main entry point.

This module initializes the FastAPI application, sets up routes,
middleware, and handles application lifecycle events.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path
from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.exceptions import BlogAutomationException
from app.core.errors import (
    blog_automation_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler,
)
from app.api.routes import keywords, content, schedule, workflow, notifications, seo, analytics, social_media, conversion, email_marketing, content_repurposing, ab_testing, competitor
from app.utils.logger import get_logger
from app.monitoring.sentry import init_sentry
from app.monitoring.metrics import PrometheusMiddleware, REGISTRY
from app.monitoring.healthcheck import HealthCheckService
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import time

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("application_starting", env=settings.app_env)

    # Initialize Sentry error tracking
    if settings.enable_metrics:
        init_sentry()
        logger.info("sentry_initialized")

    # Initialize database
    try:
        await init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))

    yield

    # Shutdown
    logger.info("application_shutting_down")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Korean Blog Automation System with SEO Optimization",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)


# Middleware
# Prometheus metrics (first, to capture all requests)
if settings.enable_metrics:
    app.add_middleware(PrometheusMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request logging middleware (metrics middleware already logs timing)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    # Skip logging for metrics and health endpoints to reduce noise
    if request.url.path in ["/metrics", "/health"]:
        return await call_next(request)

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2)
    )

    return response


# Exception handlers - Order matters! More specific exceptions first
app.add_exception_handler(BlogAutomationException, blog_automation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# Include routers
app.include_router(keywords.router, prefix=settings.api_v1_prefix)
app.include_router(content.router, prefix=settings.api_v1_prefix)
app.include_router(schedule.router, prefix=settings.api_v1_prefix)
app.include_router(workflow.router, prefix=settings.api_v1_prefix)
app.include_router(notifications.router, prefix=settings.api_v1_prefix)
app.include_router(seo.router, prefix=settings.api_v1_prefix)
app.include_router(analytics.router, prefix=settings.api_v1_prefix)
app.include_router(social_media.router, prefix=settings.api_v1_prefix)
app.include_router(conversion.router, prefix=settings.api_v1_prefix)
app.include_router(email_marketing.router, prefix=settings.api_v1_prefix)
app.include_router(content_repurposing.router, prefix=settings.api_v1_prefix)
app.include_router(ab_testing.router, prefix=settings.api_v1_prefix)
app.include_router(competitor.router, prefix=settings.api_v1_prefix)


# Mount static files for frontend
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    logger.info("frontend_static_files_mounted", path=str(FRONTEND_DIR))


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Advanced health check endpoint with detailed service status.

    Returns comprehensive health status including database, Redis,
    disk space, and memory usage.
    """
    health_service = HealthCheckService()
    health_data = await health_service.check_health()

    # Convert HealthStatus enum to string
    health_data["status"] = health_data["status"].value
    for service_name, service_data in health_data["services"].items():
        service_data["status"] = service_data["status"].value

    status_code = (
        status.HTTP_200_OK if health_data["status"] == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(content=health_data, status_code=status_code)


# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns all collected metrics in Prometheus format.
    """
    from fastapi.responses import Response

    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


# Root endpoint - Serve frontend dashboard
@app.get("/")
async def root():
    """Root endpoint - serves the frontend dashboard."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        # Fallback to API information if frontend not available
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
            "docs": "/docs" if settings.debug else "disabled",
            "health": "/health",
            "metrics": "/metrics" if settings.enable_metrics else "disabled",
            "api": settings.api_v1_prefix,
        }


# API information endpoint
@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/health",
        "metrics": "/metrics" if settings.enable_metrics else "disabled",
        "api": settings.api_v1_prefix,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        workers=1 if settings.debug else settings.workers,
    )
