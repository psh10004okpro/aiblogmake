"""
Notification service for managing multiple notification providers.

This module provides a unified interface for sending notifications through
multiple channels (email, Slack, etc.).
"""

from typing import List, Dict, Any, Optional
from app.services.notifications.base import (
    BaseNotificationProvider,
    NotificationMessage,
    NotificationResult,
    NotificationType,
    NotificationPriority
)
from app.services.notifications.email_provider import EmailNotificationProvider
from app.services.notifications.slack_provider import SlackNotificationProvider
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    """
    Unified notification service.

    This service manages multiple notification providers and sends
    notifications through all available channels.
    """

    def __init__(self):
        """Initialize notification service with all providers."""
        self.providers: List[BaseNotificationProvider] = []

        # Initialize email provider
        email_enabled = getattr(settings, "enable_email_notifications", False)
        if email_enabled:
            email_provider = EmailNotificationProvider(enabled=email_enabled)
            if email_provider.is_available():
                self.providers.append(email_provider)
                logger.info("email_notifications_enabled")
            else:
                logger.warning("email_notifications_unavailable")

        # Initialize Slack provider
        slack_enabled = getattr(settings, "enable_slack_notifications", False)
        if slack_enabled:
            slack_provider = SlackNotificationProvider(enabled=slack_enabled)
            if slack_provider.is_available():
                self.providers.append(slack_provider)
                logger.info("slack_notifications_enabled")
            else:
                logger.warning("slack_notifications_unavailable")

        if not self.providers:
            logger.warning("no_notification_providers_available")

    async def send(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[NotificationResult]:
        """
        Send notification through all available providers.

        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, success, warning, error)
            priority: Priority level (low, normal, high, urgent)
            metadata: Additional data to include in notification

        Returns:
            List of NotificationResult from each provider
        """
        notification = NotificationMessage(
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            metadata=metadata
        )

        logger.info(
            "sending_notification",
            title=title,
            type=notification_type,
            providers=len(self.providers)
        )

        results = []
        for provider in self.providers:
            try:
                result = await provider.send(notification)
                results.append(result)

                if result.success:
                    logger.info(
                        "notification_sent",
                        provider=result.provider,
                        title=title
                    )
                else:
                    logger.error(
                        "notification_failed",
                        provider=result.provider,
                        error=result.error
                    )

            except Exception as e:
                logger.error(
                    "notification_exception",
                    provider=provider.__class__.__name__,
                    error=str(e)
                )
                results.append(NotificationResult(
                    success=False,
                    provider=provider.__class__.__name__,
                    error=str(e)
                ))

        return results

    async def send_workflow_started(
        self,
        workflow_id: int,
        seed_keywords: List[str],
        num_posts: int
    ) -> List[NotificationResult]:
        """
        Send notification for workflow start.

        Args:
            workflow_id: Workflow ID
            seed_keywords: Seed keywords
            num_posts: Number of posts to create

        Returns:
            List of notification results
        """
        return await self.send(
            title="Workflow Started",
            message=f"Blog automation workflow #{workflow_id} has been started.",
            notification_type=NotificationType.INFO,
            priority=NotificationPriority.NORMAL,
            metadata={
                "workflow_id": workflow_id,
                "seed_keywords": ", ".join(seed_keywords),
                "num_posts": num_posts,
                "status": "running"
            }
        )

    async def send_workflow_completed(
        self,
        workflow_id: int,
        posts_created: int,
        posts_published: int,
        duration_seconds: float,
        errors: int = 0
    ) -> List[NotificationResult]:
        """
        Send notification for workflow completion.

        Args:
            workflow_id: Workflow ID
            posts_created: Number of posts created
            posts_published: Number of posts published
            duration_seconds: Duration in seconds
            errors: Number of errors

        Returns:
            List of notification results
        """
        notification_type = (
            NotificationType.SUCCESS if errors == 0
            else NotificationType.WARNING
        )

        message = (
            f"Workflow #{workflow_id} completed successfully! "
            f"Created {posts_created} post(s) and published {posts_published} post(s) "
            f"in {duration_seconds:.1f} seconds."
        )

        if errors > 0:
            message += f" ({errors} error(s) occurred)"

        return await self.send(
            title="Workflow Completed",
            message=message,
            notification_type=notification_type,
            priority=NotificationPriority.NORMAL,
            metadata={
                "workflow_id": workflow_id,
                "posts_created": posts_created,
                "posts_published": posts_published,
                "duration_seconds": f"{duration_seconds:.1f}s",
                "errors": errors,
                "status": "completed"
            }
        )

    async def send_workflow_failed(
        self,
        workflow_id: int,
        error: str,
        current_step: Optional[str] = None
    ) -> List[NotificationResult]:
        """
        Send notification for workflow failure.

        Args:
            workflow_id: Workflow ID
            error: Error message
            current_step: Step where failure occurred

        Returns:
            List of notification results
        """
        message = f"Workflow #{workflow_id} has failed."
        if current_step:
            message += f" Failed at step: {current_step}"

        return await self.send(
            title="Workflow Failed",
            message=message,
            notification_type=NotificationType.ERROR,
            priority=NotificationPriority.HIGH,
            metadata={
                "workflow_id": workflow_id,
                "error": error,
                "current_step": current_step or "unknown",
                "status": "failed"
            }
        )

    async def send_post_published(
        self,
        keyword: str,
        title: str,
        wp_url: str,
        word_count: int
    ) -> List[NotificationResult]:
        """
        Send notification for post publication.

        Args:
            keyword: Target keyword
            title: Post title
            wp_url: WordPress URL
            word_count: Word count

        Returns:
            List of notification results
        """
        return await self.send(
            title="New Post Published",
            message=f'Successfully published: "{title}"',
            notification_type=NotificationType.SUCCESS,
            priority=NotificationPriority.LOW,
            metadata={
                "keyword": keyword,
                "title": title,
                "url": wp_url,
                "word_count": word_count
            }
        )

    async def send_health_alert(
        self,
        service_name: str,
        status: str,
        message: str
    ) -> List[NotificationResult]:
        """
        Send notification for health check alert.

        Args:
            service_name: Name of the service
            status: Health status
            message: Alert message

        Returns:
            List of notification results
        """
        notification_type = (
            NotificationType.ERROR if status == "unhealthy"
            else NotificationType.WARNING
        )

        return await self.send(
            title=f"Health Alert: {service_name}",
            message=message,
            notification_type=notification_type,
            priority=NotificationPriority.URGENT,
            metadata={
                "service": service_name,
                "status": status
            }
        )

    async def send_api_error(
        self,
        service: str,
        endpoint: str,
        error: str,
        retry_count: int = 0
    ) -> List[NotificationResult]:
        """
        Send notification for API errors.

        Args:
            service: Service name (openai, anthropic, etc.)
            endpoint: API endpoint
            error: Error message
            retry_count: Number of retries attempted

        Returns:
            List of notification results
        """
        return await self.send(
            title=f"API Error: {service}",
            message=f"Error calling {endpoint}: {error}",
            notification_type=NotificationType.ERROR,
            priority=NotificationPriority.HIGH,
            metadata={
                "service": service,
                "endpoint": endpoint,
                "error": error,
                "retry_count": retry_count
            }
        )

    def get_active_providers(self) -> List[str]:
        """
        Get list of active provider names.

        Returns:
            List of provider names
        """
        return [provider.__class__.__name__ for provider in self.providers]

    def is_available(self) -> bool:
        """
        Check if any notification provider is available.

        Returns:
            True if at least one provider is available
        """
        return len(self.providers) > 0


# Singleton instance
_notification_service = None


def get_notification_service() -> NotificationService:
    """
    Get or create notification service singleton.

    Returns:
        NotificationService instance
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
