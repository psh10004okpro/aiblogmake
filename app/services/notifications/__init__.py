"""
Notification services module.

This module provides notification functionality through multiple channels.
"""

from app.services.notifications.base import (
    BaseNotificationProvider,
    NotificationMessage,
    NotificationResult,
    NotificationType,
    NotificationPriority,
)
from app.services.notifications.email_provider import EmailNotificationProvider
from app.services.notifications.slack_provider import (
    SlackNotificationProvider,
    SlackMarkdownProvider,
)
from app.services.notifications.notification_service import (
    NotificationService,
    get_notification_service,
)

__all__ = [
    "BaseNotificationProvider",
    "NotificationMessage",
    "NotificationResult",
    "NotificationType",
    "NotificationPriority",
    "EmailNotificationProvider",
    "SlackNotificationProvider",
    "SlackMarkdownProvider",
    "NotificationService",
    "get_notification_service",
]
