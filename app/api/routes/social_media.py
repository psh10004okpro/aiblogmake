"""
Social Media API Routes

Provides endpoints for automated social media posting.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.social_media import get_social_media_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/social-media", tags=["social-media"])


class PostToSocialRequest(BaseModel):
    """Request to post to social media."""
    title: str = Field(..., description="Post title")
    excerpt: str = Field(..., description="Post excerpt/summary")
    keywords: List[str] = Field(..., description="Target keywords")
    link: str = Field(..., description="Post URL")
    image_url: Optional[str] = Field(None, description="Optional image URL")
    platforms: Optional[List[str]] = Field(None, description="Platforms to post to (facebook, twitter, linkedin)")


class GenerateMessageRequest(BaseModel):
    """Request to generate social media message."""
    title: str
    excerpt: str
    keywords: List[str]
    platform: str = Field(..., description="Platform: facebook, twitter, or linkedin")


class GenerateHashtagsRequest(BaseModel):
    """Request to generate hashtags."""
    keywords: List[str]
    platform: str
    max_count: int = Field(default=5, ge=1, le=10)


@router.get("/status")
async def get_status():
    """
    Get social media configuration status.

    Returns which platforms are configured and ready to use.
    """
    try:
        social_service = get_social_media_service()
        status_data = social_service.get_status()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": status_data
            }
        )

    except Exception as e:
        logger.error("social_media_status_check_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check social media status: {str(e)}"
        )


@router.post("/post")
async def post_to_social_media(request: PostToSocialRequest):
    """
    Post to social media platforms.

    Automatically generates platform-specific messages and hashtags,
    then posts to the specified platforms.

    **Example:**
    ```json
    {
        "title": "SEO 완벽 가이드 2025",
        "excerpt": "검색 엔진 최적화를 위한 완벽한 가이드...",
        "keywords": ["SEO", "검색최적화", "마케팅"],
        "link": "https://yourblog.com/seo-guide",
        "image_url": "https://yourblog.com/images/seo.jpg",
        "platforms": ["facebook", "twitter"]
    }
    ```
    """
    try:
        social_service = get_social_media_service()

        # Post to all platforms
        results = await social_service.post_to_all(
            title=request.title,
            excerpt=request.excerpt,
            keywords=request.keywords,
            link=request.link,
            image_url=request.image_url,
            platforms=request.platforms
        )

        # Convert PostResult objects to dicts
        results_dict = {}
        for platform, result in results.items():
            results_dict[platform] = {
                "success": result.success,
                "platform": result.platform,
                "post_id": result.post_id,
                "url": result.url,
                "error": result.error
            }

        # Count successes
        success_count = sum(1 for r in results.values() if r.success)
        total_count = len(results)

        return JSONResponse(
            status_code=status.HTTP_200_OK if success_count > 0 else status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": success_count > 0,
                "message": f"Posted to {success_count}/{total_count} platforms",
                "results": results_dict,
                "summary": {
                    "total_platforms": total_count,
                    "succeeded": success_count,
                    "failed": total_count - success_count
                }
            }
        )

    except Exception as e:
        logger.error("social_media_post_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to post to social media: {str(e)}"
        )


@router.post("/post/{platform}")
async def post_to_platform(
    platform: str,
    request: PostToSocialRequest
):
    """
    Post to a specific social media platform.

    **Parameters:**
    - platform: facebook, twitter, or linkedin

    **Example:**
    ```bash
    POST /api/v1/social-media/post/facebook
    ```
    """
    try:
        if platform not in ['facebook', 'twitter', 'linkedin']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {platform}. Must be facebook, twitter, or linkedin"
            )

        social_service = get_social_media_service()

        # Generate message
        message = await social_service.generate_post_message(
            request.title,
            request.excerpt,
            request.keywords,
            platform
        )

        # Generate hashtags
        hashtags = await social_service.generate_hashtags(
            request.keywords,
            platform
        )

        # Post
        result = await social_service.post_to_platform(
            platform,
            message,
            hashtags,
            request.link,
            request.image_url
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK if result.success else status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": result.success,
                "data": {
                    "platform": result.platform,
                    "post_id": result.post_id,
                    "url": result.url,
                    "error": result.error,
                    "message": message,
                    "hashtags": hashtags
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("platform_post_failed", platform=platform, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to post to {platform}: {str(e)}"
        )


@router.post("/generate-message")
async def generate_message(request: GenerateMessageRequest):
    """
    Generate platform-specific social media message using AI.

    Does not post, only generates the message text.

    **Example:**
    ```json
    {
        "title": "SEO 완벽 가이드",
        "excerpt": "검색 엔진 최적화...",
        "keywords": ["SEO", "마케팅"],
        "platform": "facebook"
    }
    ```
    """
    try:
        if request.platform not in ['facebook', 'twitter', 'linkedin']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {request.platform}"
            )

        social_service = get_social_media_service()

        message = await social_service.generate_post_message(
            request.title,
            request.excerpt,
            request.keywords,
            request.platform
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "platform": request.platform,
                    "message": message,
                    "length": len(message)
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("message_generation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate message: {str(e)}"
        )


@router.post("/generate-hashtags")
async def generate_hashtags(request: GenerateHashtagsRequest):
    """
    Generate hashtags from keywords.

    **Example:**
    ```json
    {
        "keywords": ["SEO", "마케팅", "블로그"],
        "platform": "twitter",
        "max_count": 5
    }
    ```
    """
    try:
        if request.platform not in ['facebook', 'twitter', 'linkedin']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {request.platform}"
            )

        social_service = get_social_media_service()

        hashtags = await social_service.generate_hashtags(
            request.keywords,
            request.platform,
            request.max_count
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "platform": request.platform,
                    "hashtags": hashtags,
                    "count": len(hashtags),
                    "formatted": [f"#{tag}" for tag in hashtags]
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("hashtag_generation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate hashtags: {str(e)}"
        )


@router.post("/test")
async def test_post():
    """
    Send a test post to all configured platforms.

    Useful for testing configuration.
    """
    try:
        social_service = get_social_media_service()

        test_data = {
            "title": "테스트 포스트",
            "excerpt": "소셜 미디어 자동 포스팅 테스트입니다. 이 메시지는 테스트용입니다.",
            "keywords": ["테스트", "자동화", "블로그"],
            "link": "https://example.com",
            "image_url": None
        }

        results = await social_service.post_to_all(**test_data)

        # Convert to dict
        results_dict = {}
        for platform, result in results.items():
            results_dict[platform] = {
                "success": result.success,
                "post_id": result.post_id,
                "url": result.url,
                "error": result.error
            }

        success_count = sum(1 for r in results.values() if r.success)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": success_count > 0,
                "message": f"Test post sent to {success_count}/{len(results)} platforms",
                "results": results_dict
            }
        )

    except Exception as e:
        logger.error("test_post_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test post: {str(e)}"
        )
