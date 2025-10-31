"""
Email Marketing API Routes
"""

from typing import List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr

from app.services.email_marketing import get_email_marketing_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/email-marketing", tags=["email-marketing"])


class GenerateNewsletterRequest(BaseModel):
    """Request to generate newsletter."""
    posts: List[dict] = Field(..., description="List of blog posts")
    template_type: str = Field(default="weekly_digest")


class SendNewsletterRequest(BaseModel):
    """Request to send newsletter."""
    subject: str
    body_html: str
    subscribers: List[EmailStr]


@router.get("/status")
async def get_status():
    """Get email marketing status."""
    try:
        service = get_email_marketing_service()
        status_data = service.get_status()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "data": status_data}
        )
    except Exception as e:
        logger.error("email_marketing_status_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


@router.post("/generate-newsletter")
async def generate_newsletter(request: GenerateNewsletterRequest):
    """Generate newsletter from posts using AI."""
    try:
        service = get_email_marketing_service()

        newsletter = await service.generate_newsletter(
            request.posts,
            request.template_type
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "subject": newsletter.subject,
                    "body_html": newsletter.body_html,
                    "preview_text": newsletter.preview_text
                }
            }
        )

    except Exception as e:
        logger.error("newsletter_generation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate newsletter: {str(e)}"
        )


@router.post("/send-newsletter")
async def send_newsletter(request: SendNewsletterRequest):
    """Send newsletter to subscribers."""
    try:
        service = get_email_marketing_service()

        from app.services.email_marketing import NewsletterTemplate

        newsletter = NewsletterTemplate(
            subject=request.subject,
            body_html=request.body_html,
            preview_text=""
        )

        stats = await service.send_newsletter(newsletter, request.subscribers)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": stats,
                "message": f"Sent to {stats['sent']}/{stats['total']} subscribers"
            }
        )

    except Exception as e:
        logger.error("newsletter_send_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send newsletter: {str(e)}"
        )
