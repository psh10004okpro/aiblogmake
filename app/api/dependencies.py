"""
API dependencies for dependency injection.

This module provides common dependencies for FastAPI routes.
"""

from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.keyword_research import KeywordResearchService
from app.services.content_generator import ContentGeneratorService
from app.services.image_generator import ImageGeneratorService
from app.services.ad_inserter import AdInserterService
from app.services.publisher import WordPressPublisher


async def get_keyword_service() -> KeywordResearchService:
    """Get keyword research service."""
    return KeywordResearchService()


async def get_content_service() -> ContentGeneratorService:
    """Get content generator service."""
    return ContentGeneratorService()


async def get_image_service() -> ImageGeneratorService:
    """Get image generator service."""
    return ImageGeneratorService()


async def get_ad_service() -> AdInserterService:
    """Get ad inserter service."""
    return AdInserterService()


async def get_publisher_service() -> WordPressPublisher:
    """Get WordPress publisher service."""
    return WordPressPublisher()
