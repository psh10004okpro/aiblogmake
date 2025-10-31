"""
API routes for notification management and testing.

This module provides endpoints for managing notification settings and sending test notifications.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.services.notifications import (
    get_notification_service,
    NotificationType,
    NotificationPriority,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


class TestNotificationRequest(BaseModel):
    """Request schema for sending a test notification."""
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    notification_type: str = Field(default="info", pattern="^(info|success|warning|error)$")
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    metadata: Optional[Dict[str, Any]] = None


class NotificationStatusResponse(BaseModel):
    """Response schema for notification service status."""
    available: bool
    active_providers: List[str]
    email_configured: bool
    slack_configured: bool


@router.get("/status", response_model=NotificationStatusResponse)
async def get_notification_status():
    """
    Get notification service status.

    Returns information about which notification providers are configured
    and available.

    **Example Response:**
    ```json
    {
        "available": true,
        "active_providers": ["EmailNotificationProvider", "SlackNotificationProvider"],
        "email_configured": true,
        "slack_configured": true
    }
    ```
    """
    logger.info("notification_status_check")

    notification_service = get_notification_service()

    # Check which providers are configured
    email_configured = False
    slack_configured = False

    for provider_name in notification_service.get_active_providers():
        if "Email" in provider_name:
            email_configured = True
        elif "Slack" in provider_name:
            slack_configured = True

    return NotificationStatusResponse(
        available=notification_service.is_available(),
        active_providers=notification_service.get_active_providers(),
        email_configured=email_configured,
        slack_configured=slack_configured
    )


@router.post("/test")
async def send_test_notification(request: TestNotificationRequest):
    """
    Send a test notification to verify configuration.

    This endpoint allows you to test your notification settings by sending
    a test message through all configured notification channels.

    **Example Request:**
    ```json
    {
        "title": "Test Notification",
        "message": "This is a test message to verify notification configuration.",
        "notification_type": "info",
        "priority": "normal",
        "metadata": {
            "test": true,
            "timestamp": "2025-01-31T10:00:00Z"
        }
    }
    ```

    **Returns:**
    - success: Whether at least one notification was sent successfully
    - results: List of results from each provider
    - providers_attempted: Number of providers that attempted to send
    - providers_succeeded: Number of providers that succeeded
    """
    logger.info(
        "notification_test_requested",
        title=request.title,
        type=request.notification_type
    )

    notification_service = get_notification_service()

    if not notification_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="No notification providers are configured or available. "
                   "Please configure at least one notification provider (email or Slack) "
                   "in your environment variables."
        )

    try:
        # Convert string enum to actual enum
        notification_type = NotificationType(request.notification_type)
        priority = NotificationPriority(request.priority)

        # Send test notification
        results = await notification_service.send(
            title=request.title,
            message=request.message,
            notification_type=notification_type,
            priority=priority,
            metadata=request.metadata
        )

        # Count successful sends
        succeeded = sum(1 for r in results if r.success)
        attempted = len(results)

        # Format results for response
        formatted_results = []
        for result in results:
            formatted_results.append({
                "provider": result.provider,
                "success": result.success,
                "error": result.error,
                "metadata": result.metadata
            })

        logger.info(
            "notification_test_completed",
            succeeded=succeeded,
            attempted=attempted
        )

        return {
            "success": succeeded > 0,
            "results": formatted_results,
            "providers_attempted": attempted,
            "providers_succeeded": succeeded,
            "message": f"Successfully sent to {succeeded}/{attempted} provider(s)"
        }

    except Exception as e:
        logger.error("notification_test_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send test notification: {str(e)}"
        )


@router.post("/test/workflow-complete")
async def send_test_workflow_complete():
    """
    Send a test workflow completion notification.

    This is a convenience endpoint to test the workflow completion notification format.
    """
    notification_service = get_notification_service()

    if not notification_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="No notification providers are configured"
        )

    try:
        results = await notification_service.send_workflow_completed(
            workflow_id=999,
            posts_created=2,
            posts_published=2,
            duration_seconds=450.5,
            errors=0
        )

        succeeded = sum(1 for r in results if r.success)

        return {
            "success": succeeded > 0,
            "message": f"Test workflow completion notification sent to {succeeded} provider(s)"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send test notification: {str(e)}"
        )


@router.post("/test/workflow-failed")
async def send_test_workflow_failed():
    """
    Send a test workflow failure notification.

    This is a convenience endpoint to test the workflow failure notification format.
    """
    notification_service = get_notification_service()

    if not notification_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="No notification providers are configured"
        )

    try:
        results = await notification_service.send_workflow_failed(
            workflow_id=999,
            error="Test error: Simulated workflow failure",
            current_step="generate_content"
        )

        succeeded = sum(1 for r in results if r.success)

        return {
            "success": succeeded > 0,
            "message": f"Test workflow failure notification sent to {succeeded} provider(s)"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send test notification: {str(e)}"
        )
