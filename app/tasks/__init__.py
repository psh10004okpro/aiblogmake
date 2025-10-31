"""
Celery tasks module.

This module exports all Celery tasks including periodic beat tasks and workflow tasks.
"""

from .celery_tasks import (
    celery_app,
    research_keywords_task,
    generate_content_task,
    generate_images_task,
    publish_to_wordpress_task,
    complete_blog_workflow,
)

# Import beat tasks to register them
from .beat_tasks import (
    daily_auto_publish,
    weekly_keyword_research,
    hourly_health_check,
    cleanup_old_tasks,
)

# Import workflow tasks for one-click automation
from .workflow_tasks import (
    one_click_publish_task,
    get_workflow_status,
    cancel_workflow,
)

__all__ = [
    "celery_app",
    "research_keywords_task",
    "generate_content_task",
    "generate_images_task",
    "publish_to_wordpress_task",
    "complete_blog_workflow",
    "daily_auto_publish",
    "weekly_keyword_research",
    "hourly_health_check",
    "cleanup_old_tasks",
    "one_click_publish_task",
    "get_workflow_status",
    "cancel_workflow",
]
