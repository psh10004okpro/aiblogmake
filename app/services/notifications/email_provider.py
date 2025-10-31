"""
Email notification provider using SMTP.

This module provides email notifications through SMTP servers.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import asyncio
from app.services.notifications.base import (
    BaseNotificationProvider,
    NotificationMessage,
    NotificationResult,
    NotificationType
)
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmailNotificationProvider(BaseNotificationProvider):
    """Email notification provider using SMTP."""

    def __init__(
        self,
        enabled: bool = True,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        to_emails: Optional[List[str]] = None
    ):
        """
        Initialize email notification provider.

        Args:
            enabled: Whether email notifications are enabled
            smtp_host: SMTP server host (defaults to settings)
            smtp_port: SMTP server port (defaults to settings)
            smtp_user: SMTP username (defaults to settings)
            smtp_password: SMTP password (defaults to settings)
            from_email: Sender email address (defaults to settings)
            to_emails: List of recipient emails (defaults to settings)
        """
        super().__init__(enabled)
        self.smtp_host = smtp_host or settings.smtp_host
        self.smtp_port = smtp_port or settings.smtp_port
        self.smtp_user = smtp_user or settings.smtp_user
        self.smtp_password = smtp_password or settings.smtp_password
        self.from_email = from_email or settings.smtp_from
        self.to_emails = to_emails or self._parse_notify_emails()

    def _parse_notify_emails(self) -> List[str]:
        """Parse notify emails from settings."""
        if not settings.notify_emails:
            return []
        return [email.strip() for email in settings.notify_emails.split(",")]

    def validate_config(self) -> bool:
        """Validate email configuration."""
        required_fields = [
            self.smtp_host,
            self.smtp_port,
            self.smtp_user,
            self.smtp_password,
            self.from_email,
        ]

        if not all(required_fields):
            logger.warning("email_config_incomplete")
            return False

        if not self.to_emails:
            logger.warning("email_no_recipients")
            return False

        return True

    def _build_html_message(self, notification: NotificationMessage) -> str:
        """
        Build HTML email message.

        Args:
            notification: Notification message

        Returns:
            HTML formatted message
        """
        # Color scheme based on notification type
        colors = {
            NotificationType.INFO: "#3498db",      # Blue
            NotificationType.SUCCESS: "#2ecc71",   # Green
            NotificationType.WARNING: "#f39c12",   # Orange
            NotificationType.ERROR: "#e74c3c"      # Red
        }

        color = colors.get(notification.notification_type, "#95a5a6")

        # Build metadata section
        metadata_html = ""
        if notification.metadata:
            metadata_html = "<h3>Details:</h3><ul>"
            for key, value in notification.metadata.items():
                metadata_html += f"<li><strong>{key}:</strong> {value}</li>"
            metadata_html += "</ul>"

        html = f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background-color: {color};
                        color: white;
                        padding: 20px;
                        border-radius: 5px 5px 0 0;
                    }}
                    .content {{
                        background-color: #f9f9f9;
                        padding: 20px;
                        border: 1px solid #ddd;
                        border-radius: 0 0 5px 5px;
                    }}
                    .footer {{
                        margin-top: 20px;
                        padding: 10px;
                        text-align: center;
                        font-size: 12px;
                        color: #999;
                    }}
                    ul {{
                        list-style-type: none;
                        padding-left: 0;
                    }}
                    li {{
                        padding: 5px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{notification.title}</h1>
                        <p>Type: {notification.notification_type.value.upper()} | Priority: {notification.priority.value.upper()}</p>
                    </div>
                    <div class="content">
                        <p>{notification.message}</p>
                        {metadata_html}
                    </div>
                    <div class="footer">
                        <p>This is an automated notification from {settings.app_name}</p>
                    </div>
                </div>
            </body>
        </html>
        """
        return html

    async def send(self, notification: NotificationMessage) -> NotificationResult:
        """
        Send email notification.

        Args:
            notification: The notification to send

        Returns:
            NotificationResult with send status
        """
        if not self.is_available():
            return NotificationResult(
                success=False,
                provider="email",
                error="Email provider is not available or properly configured"
            )

        logger.info(
            "email_sending",
            title=notification.title,
            type=notification.notification_type,
            recipients=len(self.to_emails)
        )

        try:
            # Build email message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"[{settings.app_name}] {notification.title}"
            message["From"] = self.from_email
            message["To"] = ", ".join(self.to_emails)

            # Plain text version
            text_part = MIMEText(notification.message, "plain")
            message.attach(text_part)

            # HTML version
            html_part = MIMEText(self._build_html_message(notification), "html")
            message.attach(html_part)

            # Send email in thread pool to avoid blocking
            def _send_sync():
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(
                        self.from_email,
                        self.to_emails,
                        message.as_string()
                    )

            # Run in executor to avoid blocking
            await asyncio.to_thread(_send_sync)

            logger.info(
                "email_sent",
                title=notification.title,
                recipients=len(self.to_emails)
            )

            return NotificationResult(
                success=True,
                provider="email",
                metadata={
                    "recipients": self.to_emails,
                    "subject": message["Subject"]
                }
            )

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed: {str(e)}"
            logger.error("email_auth_failed", error=error_msg)
            return NotificationResult(
                success=False,
                provider="email",
                error=error_msg
            )

        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error("email_smtp_error", error=error_msg)
            return NotificationResult(
                success=False,
                provider="email",
                error=error_msg
            )

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error("email_send_failed", error=error_msg)
            return NotificationResult(
                success=False,
                provider="email",
                error=error_msg
            )
