"""
Base notification service interface.

This module defines the abstract base class for all notification providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(str, Enum):
    """Notification types."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class NotificationMessage:
    """Standard notification message format."""
    title: str
    message: str
    notification_type: NotificationType = NotificationType.INFO
    priority: NotificationPriority = NotificationPriority.NORMAL
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class NotificationResult:
    """Result of a notification attempt."""
    success: bool
    provider: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseNotificationProvider(ABC):
    """Base class for notification providers."""

    def __init__(self, enabled: bool = True):
        """
        Initialize notification provider.

        Args:
            enabled: Whether notifications are enabled for this provider
        """
        self.enabled = enabled

    @abstractmethod
    async def send(self, notification: NotificationMessage) -> NotificationResult:
        """
        Send a notification.

        Args:
            notification: The notification message to send

        Returns:
            NotificationResult with success status and details
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate provider configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        pass

    def is_available(self) -> bool:
        """
        Check if provider is available and properly configured.

        Returns:
            True if provider can send notifications
        """
        return self.enabled and self.validate_config()
