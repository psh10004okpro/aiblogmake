"""
Slack notification provider using webhooks.

This module provides Slack notifications through incoming webhooks.
"""

import aiohttp
from typing import Optional, Dict, Any
from app.services.notifications.base import (
    BaseNotificationProvider,
    NotificationMessage,
    NotificationResult,
    NotificationType
)
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SlackNotificationProvider(BaseNotificationProvider):
    """Slack notification provider using webhooks."""

    def __init__(
        self,
        enabled: bool = True,
        webhook_url: Optional[str] = None,
        channel: Optional[str] = None,
        username: Optional[str] = None
    ):
        """
        Initialize Slack notification provider.

        Args:
            enabled: Whether Slack notifications are enabled
            webhook_url: Slack webhook URL (defaults to settings)
            channel: Slack channel to post to (defaults to webhook default)
            username: Bot username (defaults to app name)
        """
        super().__init__(enabled)
        self.webhook_url = webhook_url or getattr(settings, "slack_webhook_url", None)
        self.channel = channel or getattr(settings, "slack_channel", None)
        self.username = username or settings.app_name

    def validate_config(self) -> bool:
        """Validate Slack configuration."""
        if not self.webhook_url:
            logger.warning("slack_webhook_url_not_configured")
            return False

        if not self.webhook_url.startswith("https://hooks.slack.com/"):
            logger.warning("slack_webhook_url_invalid")
            return False

        return True

    def _build_slack_payload(self, notification: NotificationMessage) -> Dict[str, Any]:
        """
        Build Slack message payload.

        Args:
            notification: Notification message

        Returns:
            Slack webhook payload
        """
        # Color scheme based on notification type
        colors = {
            NotificationType.INFO: "#3498db",      # Blue
            NotificationType.SUCCESS: "#2ecc71",   # Green
            NotificationType.WARNING: "#f39c12",   # Orange
            NotificationType.ERROR: "#e74c3c"      # Red
        }

        color = colors.get(notification.notification_type, "#95a5a6")

        # Build fields from metadata
        fields = []
        if notification.metadata:
            for key, value in notification.metadata.items():
                fields.append({
                    "title": key.replace("_", " ").title(),
                    "value": str(value),
                    "short": True
                })

        # Add priority field
        fields.append({
            "title": "Priority",
            "value": notification.priority.value.upper(),
            "short": True
        })

        # Build attachment
        attachment = {
            "color": color,
            "title": notification.title,
            "text": notification.message,
            "fields": fields,
            "footer": settings.app_name,
            "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
            "ts": None  # Will use current timestamp
        }

        # Build payload
        payload = {
            "username": self.username,
            "attachments": [attachment]
        }

        # Add channel if specified
        if self.channel:
            payload["channel"] = self.channel

        return payload

    async def send(self, notification: NotificationMessage) -> NotificationResult:
        """
        Send Slack notification.

        Args:
            notification: The notification to send

        Returns:
            NotificationResult with send status
        """
        if not self.is_available():
            return NotificationResult(
                success=False,
                provider="slack",
                error="Slack provider is not available or properly configured"
            )

        logger.info(
            "slack_sending",
            title=notification.title,
            type=notification.notification_type
        )

        try:
            payload = self._build_slack_payload(notification)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_text = await response.text()

                    if response.status == 200 and response_text == "ok":
                        logger.info(
                            "slack_sent",
                            title=notification.title
                        )

                        return NotificationResult(
                            success=True,
                            provider="slack",
                            metadata={
                                "channel": self.channel,
                                "username": self.username
                            }
                        )
                    else:
                        error_msg = f"Slack webhook returned {response.status}: {response_text}"
                        logger.error("slack_webhook_error", error=error_msg)
                        return NotificationResult(
                            success=False,
                            provider="slack",
                            error=error_msg
                        )

        except aiohttp.ClientError as e:
            error_msg = f"HTTP client error: {str(e)}"
            logger.error("slack_http_error", error=error_msg)
            return NotificationResult(
                success=False,
                provider="slack",
                error=error_msg
            )

        except Exception as e:
            error_msg = f"Failed to send Slack notification: {str(e)}"
            logger.error("slack_send_failed", error=error_msg)
            return NotificationResult(
                success=False,
                provider="slack",
                error=error_msg
            )


class SlackMarkdownProvider(SlackNotificationProvider):
    """
    Slack notification provider with Markdown formatting.

    This is an alternative provider that uses Slack's mrkdwn format
    instead of attachments.
    """

    def _build_slack_payload(self, notification: NotificationMessage) -> Dict[str, Any]:
        """
        Build Slack message payload with Markdown formatting.

        Args:
            notification: Notification message

        Returns:
            Slack webhook payload with mrkdwn
        """
        # Emoji based on notification type
        emojis = {
            NotificationType.INFO: ":information_source:",
            NotificationType.SUCCESS: ":white_check_mark:",
            NotificationType.WARNING: ":warning:",
            NotificationType.ERROR: ":x:"
        }

        emoji = emojis.get(notification.notification_type, ":bell:")

        # Build message text with Markdown
        text = f"{emoji} *{notification.title}*\n\n{notification.message}"

        # Add metadata
        if notification.metadata:
            text += "\n\n*Details:*"
            for key, value in notification.metadata.items():
                key_formatted = key.replace("_", " ").title()
                text += f"\n• *{key_formatted}:* {value}"

        # Add priority
        text += f"\n\n*Priority:* {notification.priority.value.upper()}"

        # Build payload
        payload = {
            "username": self.username,
            "text": text,
            "mrkdwn": True
        }

        # Add channel if specified
        if self.channel:
            payload["channel"] = self.channel

        return payload
