"""
Keyword research API routes.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.schemas import (
    KeywordResearchRequest,
    KeywordResearchResponse,
    KeywordResponse,
    KeywordCreate,
)
from app.models.database import Keyword
from app.services.keyword_research import KeywordResearchService
from app.api.dependencies import get_keyword_service
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/keywords", tags=["keywords"])


@router.post("/research", response_model=KeywordResearchResponse)
async def research_keywords(
    request: KeywordResearchRequest,
    db: AsyncSession = Depends(get_db),
    keyword_service: KeywordResearchService = Depends(get_keyword_service)
):
    """
    Research keywords based on seed keywords.

    This endpoint performs comprehensive keyword research using:
    - Google Keyword Planner (if configured)
    - Naver Search Ad API (if configured)
    - Naver autocomplete scraping
    - Google Trends

    Returns scored and sorted keywords by golden score.
    """
    logger.info("keyword_research_requested", seeds=request.seed_keywords)

    try:
        # Perform keyword research
        keywords = await keyword_service.research_keywords(
            seed_keywords=request.seed_keywords,
            include_naver=request.include_naver,
            include_autocomplete=request.include_autocomplete
        )

        # Filter keywords
        filtered_keywords = keyword_service.filter_keywords(
            keywords,
            min_search_volume=100,
            max_competition=0.7
        )

        # Save to database
        saved_keywords = []
        for kw_data in filtered_keywords:
            # Check if keyword already exists
            result = await db.execute(
                select(Keyword).where(Keyword.keyword == kw_data["keyword"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing keyword
                for key, value in kw_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                saved_keywords.append(existing)
            else:
                # Create new keyword
                new_keyword = Keyword(**kw_data)
                db.add(new_keyword)
                saved_keywords.append(new_keyword)

        await db.commit()

        # Refresh to get IDs
        for kw in saved_keywords:
            await db.refresh(kw)

        # Convert to response models
        keyword_responses = [KeywordResponse.model_validate(kw) for kw in saved_keywords]

        # Get top keywords
        top_keywords = keyword_responses[:20]

        return KeywordResearchResponse(
            keywords=keyword_responses,
            total_found=len(keyword_responses),
            top_keywords=top_keywords
        )

    except Exception as e:
        logger.error("keyword_research_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Keyword research failed: {str(e)}"
        )


@router.get("/", response_model=List[KeywordResponse])
async def get_keywords(
    skip: int = 0,
    limit: int = 100,
    min_score: float = 0.0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all keywords, sorted by golden score.

    Query parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - min_score: Minimum golden score filter
    """
    query = (
        select(Keyword)
        .where(Keyword.golden_score >= min_score)
        .order_by(Keyword.golden_score.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    keywords = result.scalars().all()

    return [KeywordResponse.model_validate(kw) for kw in keywords]


@router.get("/{keyword_id}", response_model=KeywordResponse)
async def get_keyword(
    keyword_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific keyword by ID."""
    result = await db.execute(
        select(Keyword).where(Keyword.id == keyword_id)
    )
    keyword = result.scalar_one_or_none()

    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Keyword with ID {keyword_id} not found"
        )

    return KeywordResponse.model_validate(keyword)


@router.delete("/{keyword_id}")
async def delete_keyword(
    keyword_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a keyword."""
    result = await db.execute(
        select(Keyword).where(Keyword.id == keyword_id)
    )
    keyword = result.scalar_one_or_none()

    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Keyword with ID {keyword_id} not found"
        )

    await db.delete(keyword)
    await db.commit()

    return {"message": f"Keyword {keyword_id} deleted successfully"}
