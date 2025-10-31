"""
FastAPI application main entry point.

This module initializes the FastAPI application, sets up routes,
middleware, and handles application lifecycle events.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.routes import keywords, content, schedule
from app.utils.logger import get_logger
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


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2)
    )

    return response


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.debug else "An error occurred"
        }
    )


# Include routers
app.include_router(keywords.router, prefix=settings.api_v1_prefix)
app.include_router(content.router, prefix=settings.api_v1_prefix)
app.include_router(schedule.router, prefix=settings.api_v1_prefix)


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns application status and service availability.
    """
    from app.core.database import check_db_connection

    db_status = await check_db_connection()

    health_data = {
        "status": "healthy" if db_status else "degraded",
        "version": "1.0.0",
        "environment": settings.app_env,
        "services": {
            "database": db_status,
            "redis": True,  # TODO: Implement Redis health check
            "celery": True,  # TODO: Implement Celery health check
        }
    }

    status_code = (
        status.HTTP_200_OK if db_status
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(content=health_data, status_code=status_code)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/health",
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
