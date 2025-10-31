"""
Database configuration module.

This module sets up async SQLAlchemy engine, session factory,
and base class for declarative models.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

# Create declarative base for models
Base = declarative_base()

# Global engine and session maker
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Get or create the async database engine.

    Returns:
        AsyncEngine: SQLAlchemy async engine instance.
    """
    global _engine

    if _engine is None:
        # Choose pool class based on environment
        pool_class = NullPool if settings.is_development else QueuePool

        _engine = create_async_engine(
            settings.database_url,
            echo=settings.db_echo,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            poolclass=pool_class,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
        )

        logger.info(
            "database_engine_created",
            url=settings.database_url.split("@")[-1],  # Hide credentials
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
        )

    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """
    Get or create the async session maker.

    Returns:
        async_sessionmaker: SQLAlchemy async session maker.
    """
    global _async_session_maker

    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info("session_maker_created")

    return _async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Yields:
        AsyncSession: Database session for dependency injection.

    Example:
        ```python
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
        ```
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("database_session_error", error=str(e))
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database by creating all tables.

    This should be called on application startup.
    In production, use Alembic migrations instead.
    """
    engine = get_engine()

    try:
        async with engine.begin() as conn:
            # Import all models here to ensure they're registered
            from app.models.database import (
                Keyword,
                Post,
                Image,
                PublishHistory,
                ScheduledTask,
            )

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)

        logger.info("database_tables_created")
    except Exception as e:
        logger.error("database_init_error", error=str(e))
        raise


async def close_db() -> None:
    """
    Close database connections.

    This should be called on application shutdown.
    """
    global _engine, _async_session_maker

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
        logger.info("database_connections_closed")


async def check_db_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection is successful, False otherwise.
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        logger.info("database_connection_check_passed")
        return True
    except Exception as e:
        logger.error("database_connection_check_failed", error=str(e))
        return False
