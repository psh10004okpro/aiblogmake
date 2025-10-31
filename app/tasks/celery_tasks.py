"""
Celery tasks for background job processing.

This module defines asynchronous tasks for the blog automation workflow.
"""

from celery import Celery
from typing import List, Dict, Any
import asyncio
from datetime import datetime, timedelta
from app.core.config import settings
from app.services.keyword_research import KeywordResearchService
from app.services.content_generator import ContentGeneratorService
from app.services.image_generator import ImageGeneratorService
from app.services.ad_inserter import AdInserterService
from app.services.publisher import WordPressPublisher
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize Celery
celery_app = Celery(
    "blog_automation",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=[settings.celery_accept_content],
    timezone=settings.celery_timezone,
    enable_utc=settings.celery_enable_utc,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
)


def run_async(coro):
    """Helper to run async functions in Celery tasks."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def research_keywords_task(
    self,
    seed_keywords: List[str],
    include_google: bool = True,
    include_naver: bool = True,
    include_autocomplete: bool = True
) -> Dict[str, Any]:
    """
    Celery task for keyword research.

    Args:
        seed_keywords: Initial keywords to expand.
        include_google: Include Google Keyword Planner.
        include_naver: Include Naver Search Ad API.
        include_autocomplete: Include Naver autocomplete.

    Returns:
        Dict[str, Any]: Research results.
    """
    logger.info("celery_task_started", task="research_keywords", seeds=seed_keywords)

    try:
        service = KeywordResearchService()

        keywords = run_async(
            service.research_keywords(
                seed_keywords=seed_keywords,
                include_google=include_google,
                include_naver=include_naver,
                include_autocomplete=include_autocomplete
            )
        )

        logger.info(
            "celery_task_completed",
            task="research_keywords",
            keywords_found=len(keywords)
        )

        return {
            "status": "completed",
            "keywords": keywords,
            "count": len(keywords)
        }

    except Exception as e:
        logger.error("celery_task_failed", task="research_keywords", error=str(e))
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def generate_content_task(
    self,
    keyword: str,
    target_word_count: int = 2000,
    tone: str = "professional"
) -> Dict[str, Any]:
    """
    Celery task for content generation.

    Args:
        keyword: Target keyword.
        target_word_count: Target word count.
        tone: Content tone.

    Returns:
        Dict[str, Any]: Generated content.
    """
    logger.info("celery_task_started", task="generate_content", keyword=keyword)

    try:
        service = ContentGeneratorService()

        content = run_async(
            service.generate_content(
                keyword=keyword,
                target_word_count=target_word_count,
                tone=tone
            )
        )

        logger.info(
            "celery_task_completed",
            task="generate_content",
            word_count=content["word_count"]
        )

        return {
            "status": "completed",
            "content": content
        }

    except Exception as e:
        logger.error("celery_task_failed", task="generate_content", error=str(e))
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def generate_images_task(
    self,
    keyword: str,
    content: str,
    num_images: int = 4
) -> Dict[str, Any]:
    """
    Celery task for image generation.

    Args:
        keyword: Target keyword.
        content: Post content.
        num_images: Number of images to generate.

    Returns:
        Dict[str, Any]: Generated images data.
    """
    logger.info("celery_task_started", task="generate_images", keyword=keyword)

    try:
        service = ImageGeneratorService()

        images = run_async(
            service.generate_images_for_post(
                keyword=keyword,
                content=content,
                num_images=num_images
            )
        )

        logger.info(
            "celery_task_completed",
            task="generate_images",
            images_count=len(images)
        )

        return {
            "status": "completed",
            "images": images
        }

    except Exception as e:
        logger.error("celery_task_failed", task="generate_images", error=str(e))
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def publish_to_wordpress_task(
    self,
    title: str,
    content: str,
    categories: List[str] = None,
    tags: List[str] = None,
    status: str = "publish"
) -> Dict[str, Any]:
    """
    Celery task for publishing to WordPress.

    Args:
        title: Post title.
        content: Post content.
        categories: Categories.
        tags: Tags.
        status: Post status.

    Returns:
        Dict[str, Any]: Publishing result.
    """
    logger.info("celery_task_started", task="publish_to_wordpress", title=title)

    try:
        publisher = WordPressPublisher()

        result = run_async(
            publisher.create_post(
                title=title,
                content=content,
                categories=categories or [],
                tags=tags or [],
                status=status
            )
        )

        logger.info(
            "celery_task_completed",
            task="publish_to_wordpress",
            wp_post_id=result["id"]
        )

        return {
            "status": "completed",
            "wp_post": result
        }

    except Exception as e:
        logger.error("celery_task_failed", task="publish_to_wordpress", error=str(e))
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True)
def complete_blog_workflow(
    self,
    seed_keywords: List[str],
    num_posts: int = 1,
    publish_immediately: bool = False,
    schedule_interval_hours: int = 24
) -> Dict[str, Any]:
    """
    Complete blog automation workflow.

    This task orchestrates the entire workflow:
    1. Research keywords
    2. Generate content for top keywords
    3. Generate images
    4. Insert ads
    5. Publish to WordPress

    Args:
        seed_keywords: Initial keywords.
        num_posts: Number of posts to create.
        publish_immediately: Whether to publish immediately.
        schedule_interval_hours: Interval between scheduled posts.

    Returns:
        Dict[str, Any]: Workflow results.
    """
    logger.info(
        "celery_workflow_started",
        seeds=seed_keywords,
        num_posts=num_posts
    )

    try:
        results = {
            "keywords": [],
            "posts": [],
            "errors": []
        }

        # Step 1: Research keywords
        logger.info("workflow_step", step=1, action="researching_keywords")
        keyword_result = research_keywords_task(seed_keywords)
        results["keywords"] = keyword_result["keywords"]

        # Get top N keywords
        top_keywords = sorted(
            keyword_result["keywords"],
            key=lambda x: x["golden_score"],
            reverse=True
        )[:num_posts]

        # Step 2-5: For each keyword, generate and publish post
        for i, kw_data in enumerate(top_keywords):
            keyword = kw_data["keyword"]
            logger.info("workflow_step", step=2 + i, keyword=keyword)

            try:
                # Generate content
                content_result = generate_content_task(keyword)
                content_data = content_result["content"]

                # Generate images
                image_result = generate_images_task(
                    keyword,
                    content_data["content"]
                )

                # Insert ads
                ad_service = AdInserterService()
                ad_result = ad_service.insert_ads(content_data["content"])

                # Publish
                if publish_immediately:
                    publish_result = publish_to_wordpress_task(
                        title=content_data["title"],
                        content=ad_result["content"],
                        tags=[keyword],
                        status="publish"
                    )
                else:
                    # Schedule for future
                    scheduled_time = datetime.now() + timedelta(
                        hours=schedule_interval_hours * i
                    )
                    publish_result = publish_to_wordpress_task(
                        title=content_data["title"],
                        content=ad_result["content"],
                        tags=[keyword],
                        status="future"
                    )

                results["posts"].append({
                    "keyword": keyword,
                    "title": content_data["title"],
                    "wp_post_id": publish_result["wp_post"]["id"],
                    "wp_url": publish_result["wp_post"]["url"],
                })

            except Exception as e:
                logger.error("workflow_post_failed", keyword=keyword, error=str(e))
                results["errors"].append({
                    "keyword": keyword,
                    "error": str(e)
                })

        logger.info(
            "celery_workflow_completed",
            posts_created=len(results["posts"]),
            errors=len(results["errors"])
        )

        return results

    except Exception as e:
        logger.error("celery_workflow_failed", error=str(e))
        raise


# Periodic tasks
@celery_app.task
def daily_publish_task():
    """
    Daily scheduled publishing task.

    This task runs daily at the configured time to publish scheduled posts.
    """
    logger.info("daily_publish_task_started")

    # TODO: Implement logic to check for scheduled posts and publish them

    logger.info("daily_publish_task_completed")


# Celery beat schedule
celery_app.conf.beat_schedule = {
    "daily-publish": {
        "task": "app.tasks.celery_tasks.daily_publish_task",
        "schedule": 86400.0,  # Every 24 hours
    },
}
