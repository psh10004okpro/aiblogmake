"""
Conversion Rate Optimization API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.conversion_optimization import (
    get_cro_service,
    CTAType,
    CTAPosition
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/conversion", tags=["conversion"])


class InsertCTAsRequest(BaseModel):
    """Request to insert CTAs into content."""
    content: str = Field(..., description="HTML content")
    keywords: List[str] = Field(..., description="Target keywords")
    content_type: str = Field(default="blog", description="Content type")


class CreateLeadMagnetRequest(BaseModel):
    """Request to create lead magnet."""
    title: str
    description: str
    content_type: str = Field(..., description="pdf, ebook, checklist, template")
    keywords: List[str]


class GeneratePopupRequest(BaseModel):
    """Request to generate popup config."""
    popup_type: str = Field(default="exit_intent", description="exit_intent, timed, scroll")
    custom_message: Optional[str] = None


@router.post("/insert-ctas")
async def insert_ctas(request: InsertCTAsRequest):
    """
    Insert CTAs into content at optimal positions.

    Automatically determines best positions and generates contextual CTAs.
    """
    try:
        cro_service = get_cro_service()

        modified_content, ctas = await cro_service.insert_ctas_in_content(
            request.content,
            request.keywords,
            request.content_type
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "content": modified_content,
                    "ctas_inserted": len(ctas),
                    "positions": [cta.position.value for cta in ctas]
                }
            }
        )

    except Exception as e:
        logger.error("cta_insertion_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to insert CTAs: {str(e)}"
        )


@router.post("/lead-magnet")
async def create_lead_magnet(request: CreateLeadMagnetRequest):
    """Create lead magnet configuration."""
    try:
        cro_service = get_cro_service()

        lead_magnet = await cro_service.create_lead_magnet(
            request.title,
            request.description,
            request.content_type,
            request.keywords
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "title": lead_magnet.title,
                    "description": lead_magnet.description,
                    "file_type": lead_magnet.file_type,
                    "download_url": lead_magnet.download_url,
                    "required_fields": lead_magnet.required_fields
                }
            }
        )

    except Exception as e:
        logger.error("lead_magnet_creation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lead magnet: {str(e)}"
        )


@router.post("/popup")
async def generate_popup(request: GeneratePopupRequest):
    """Generate popup configuration."""
    try:
        cro_service = get_cro_service()

        popup_config = await cro_service.generate_popup_config(
            request.popup_type,
            request.custom_message
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "trigger": popup_config.trigger,
                    "delay_seconds": popup_config.delay_seconds,
                    "scroll_percentage": popup_config.scroll_percentage,
                    "title": popup_config.title,
                    "message": popup_config.message,
                    "cta_text": popup_config.cta_text,
                    "show_frequency": popup_config.show_frequency
                }
            }
        )

    except Exception as e:
        logger.error("popup_generation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate popup: {str(e)}"
        )


@router.get("/optimal-positions")
async def get_optimal_positions(content_length: int, content_type: str = "blog"):
    """Get optimal CTA positions for given content length."""
    try:
        cro_service = get_cro_service()

        positions = cro_service.get_optimal_cta_positions(content_length, content_type)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "content_length": content_length,
                    "recommended_positions": [p.value for p in positions],
                    "count": len(positions)
                }
            }
        )

    except Exception as e:
        logger.error("optimal_positions_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get optimal positions: {str(e)}"
        )
