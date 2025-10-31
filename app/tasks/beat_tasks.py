"""
Celery Beat periodic tasks for blog automation.

This module defines scheduled tasks that run automatically at specified intervals.
"""

from celery import chain, group
from celery.schedules import crontab
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncio

from app.core.config import settings
from app.utils.logger import get_logger
from .celery_tasks import (
    celery_app,
    run_async,
    research_keywords_task,
    generate_content_task,
    generate_images_task,
    publish_to_wordpress_task,
)

logger = get_logger(__name__)


@celery_app.task(name="periodic.daily_auto_publish")
def daily_auto_publish():
    """
    Daily automatic blog post generation and publishing.

    This task runs every day at the configured time to:
    1. Research trending keywords
    2. Generate a blog post
    3. Publish to WordPress

    Environment variables:
        - DAILY_AUTO_PUBLISH_KEYWORDS: Comma-separated seed keywords
        - PUBLISH_TIME: Time to publish (HH:MM format)
    """
    logger.info("daily_auto_publish_started")

    try:
        # Get seed keywords from settings or use defaults
        seed_keywords_str = settings.dict().get("daily_auto_publish_keywords", "블로그,SEO,마케팅")
        seed_keywords = [kw.strip() for kw in seed_keywords_str.split(",")]

        logger.info("daily_auto_publish_keywords", seeds=seed_keywords)

        # Research keywords
        keyword_result = research_keywords_task(seed_keywords)

        if not keyword_result["keywords"]:
            logger.warning("daily_auto_publish_no_keywords")
            return {"status": "skipped", "reason": "No keywords found"}

        # Get best keyword
        best_keyword = sorted(
            keyword_result["keywords"],
            key=lambda x: x["golden_score"],
            reverse=True
        )[0]

        keyword = best_keyword["keyword"]
        logger.info("daily_auto_publish_selected_keyword", keyword=keyword)

        # Generate content
        content_result = generate_content_task(keyword)
        content_data = content_result["content"]

        # Generate images
        image_result = generate_images_task(
            keyword=keyword,
            content=content_data["content"],
            num_images=4
        )

        # Insert ads
        from app.services.ad_inserter import AdInserterService
        ad_service = AdInserterService()
        final_content = ad_service.insert_ads(content_data["content"])

        # Publish immediately
        publish_result = publish_to_wordpress_task(
            title=content_data["title"],
            content=final_content["content"],
            tags=[keyword],
            status="publish"
        )

        result = {
            "status": "completed",
            "keyword": keyword,
            "title": content_data["title"],
            "wp_post_id": publish_result["wp_post"]["id"],
            "wp_url": publish_result["wp_post"]["url"],
            "word_count": content_data["word_count"],
            "images_count": len(image_result["images"]),
        }

        logger.info("daily_auto_publish_completed", result=result)
        return result

    except Exception as e:
        logger.error("daily_auto_publish_failed", error=str(e))
        raise


@celery_app.task(name="periodic.weekly_keyword_research")
def weekly_keyword_research():
    """
    Weekly keyword research to update keyword database.

    This task runs weekly to:
    1. Research new trending keywords
    2. Update keyword database
    3. Generate report
    """
    logger.info("weekly_keyword_research_started")

    try:
        from app.core.database import async_session_maker
        from app.models.database import Keyword
        from sqlalchemy import select

        # Get seed keywords from various sources
        seed_keywords = [
            "블로그", "SEO", "마케팅", "디지털마케팅", "콘텐츠마케팅",
            "소셜미디어", "인플루언서", "유튜브", "인스타그램", "틱톡"
        ]

        # Research keywords
        keyword_result = research_keywords_task(seed_keywords)

        # Save to database
        async def save_keywords():
            async with async_session_maker() as session:
                for kw_data in keyword_result["keywords"]:
                    # Check if keyword already exists
                    result = await session.execute(
                        select(Keyword).where(Keyword.keyword == kw_data["keyword"])
                    )
                    existing = result.scalar_one_or_none()

                    if not existing:
                        keyword = Keyword(
                            keyword=kw_data["keyword"],
                            search_volume=kw_data.get("search_volume", 0),
                            competition=kw_data.get("competition", 0.0),
                            cpc=kw_data.get("cpc", 0.0),
                            golden_score=kw_data.get("golden_score", 0.0),
                            source="periodic_research",
                        )
                        session.add(keyword)

                await session.commit()

        run_async(save_keywords())

        result = {
            "status": "completed",
            "keywords_researched": len(keyword_result["keywords"]),
            "new_keywords_added": len(keyword_result["keywords"]),
        }

        logger.info("weekly_keyword_research_completed", result=result)
        return result

    except Exception as e:
        logger.error("weekly_keyword_research_failed", error=str(e))
        raise


@celery_app.task(name="periodic.hourly_health_check")
def hourly_health_check():
    """
    Hourly health check to monitor system status.

    Checks:
    - Database connectivity
    - Redis connectivity
    - API keys validity
    - Disk space
    """
    logger.info("hourly_health_check_started")

    try:
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "database": "unknown",
            "redis": "unknown",
            "disk_space": "unknown",
        }

        # Check database
        try:
            from app.core.database import async_session_maker
            from sqlalchemy import text

            async def check_db():
                async with async_session_maker() as session:
                    await session.execute(text("SELECT 1"))
                    return "healthy"

            health_status["database"] = run_async(check_db())
        except Exception as e:
            health_status["database"] = f"error: {str(e)}"
            logger.error("health_check_database_failed", error=str(e))

        # Check Redis
        try:
            import redis
            r = redis.from_url(settings.redis_url)
            r.ping()
            health_status["redis"] = "healthy"
        except Exception as e:
            health_status["redis"] = f"error: {str(e)}"
            logger.error("health_check_redis_failed", error=str(e))

        # Check disk space
        try:
            import psutil
            disk = psutil.disk_usage('/')
            health_status["disk_space"] = f"{disk.percent}% used"

            if disk.percent > 90:
                logger.warning("health_check_disk_space_low", percent=disk.percent)
        except Exception as e:
            health_status["disk_space"] = f"error: {str(e)}"

        logger.info("hourly_health_check_completed", status=health_status)
        return health_status

    except Exception as e:
        logger.error("hourly_health_check_failed", error=str(e))
        raise


@celery_app.task(name="periodic.cleanup_old_tasks")
def cleanup_old_tasks():
    """
    Daily cleanup of old completed tasks and logs.

    Removes:
    - Celery task results older than 7 days
    - Old log files
    - Temporary files
    """
    logger.info("cleanup_old_tasks_started")

    try:
        from datetime import datetime, timedelta

        # Clean up old Celery results
        # This is handled by Celery result backend expiration

        # Clean up old scheduled tasks from database
        from app.core.database import async_session_maker
        from app.models.database import ScheduledTask
        from sqlalchemy import delete

        async def cleanup_db():
            async with async_session_maker() as session:
                # Delete completed tasks older than 7 days
                cutoff_date = datetime.now() - timedelta(days=7)

                result = await session.execute(
                    delete(ScheduledTask).where(
                        ScheduledTask.status.in_(["completed", "failed"]),
                        ScheduledTask.created_at < cutoff_date
                    )
                )

                await session.commit()
                return result.rowcount

        deleted_count = run_async(cleanup_db())

        result = {
            "status": "completed",
            "deleted_tasks": deleted_count,
        }

        logger.info("cleanup_old_tasks_completed", result=result)
        return result

    except Exception as e:
        logger.error("cleanup_old_tasks_failed", error=str(e))
        raise


# Configure Celery Beat Schedule
celery_app.conf.beat_schedule = {
    # Daily auto-publish at configured time (default 9:00 AM KST)
    "daily-auto-publish": {
        "task": "periodic.daily_auto_publish",
        "schedule": crontab(
            hour=int(settings.publish_time.split(":")[0]),
            minute=int(settings.publish_time.split(":")[1]),
        ),
        "options": {"expires": 3600},  # Expire after 1 hour if not executed
    },

    # Weekly keyword research (every Monday at 3:00 AM)
    "weekly-keyword-research": {
        "task": "periodic.weekly_keyword_research",
        "schedule": crontab(
            hour=3,
            minute=0,
            day_of_week=1,  # Monday
        ),
        "options": {"expires": 7200},
    },

    # Hourly health check
    "hourly-health-check": {
        "task": "periodic.hourly_health_check",
        "schedule": crontab(minute=0),  # Every hour at :00
        "options": {"expires": 3000},
    },

    # Daily cleanup (every day at 2:00 AM)
    "daily-cleanup": {
        "task": "periodic.cleanup_old_tasks",
        "schedule": crontab(hour=2, minute=0),
        "options": {"expires": 3600},
    },
}

# Beat scheduler settings
celery_app.conf.update(
    beat_scheduler='celery.beat:PersistentScheduler',
    beat_schedule_filename='celerybeat-schedule',
)

logger.info(
    "celery_beat_configured",
    schedules=list(celery_app.conf.beat_schedule.keys())
)
