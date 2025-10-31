"""
Content generation and publishing API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.schemas import (
    ContentGenerationRequest,
    ContentResponse,
    PostCreate,
    PostResponse,
    PublishRequest,
    PublishResponse,
    CompleteWorkflowRequest,
    CompleteWorkflowResponse,
)
from app.models.database import Post, Keyword, Image
from app.services.content_generator import ContentGeneratorService
from app.services.image_generator import ImageGeneratorService
from app.services.ad_inserter import AdInserterService
from app.services.publisher import WordPressPublisher
from app.api.dependencies import (
    get_content_service,
    get_image_service,
    get_ad_service,
    get_publisher_service
)
from app.utils.seo import generate_slug
from app.utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)
router = APIRouter(prefix="/content", tags=["content"])


@router.get("/llm-providers")
async def list_llm_providers():
    """
    List available LLM providers and their configuration status.

    Returns information about which LLM providers are available
    based on API key configuration.
    """
    from app.services.llm.factory import LLMProviderFactory
    from app.core.config import settings

    providers = LLMProviderFactory.list_available_providers()

    return {
        "default_provider": settings.default_llm_provider,
        "providers": {
            "claude": {
                "available": providers["claude"],
                "model": settings.claude_model if providers["claude"] else None,
                "description": "Anthropic Claude - Best for natural Korean content"
            },
            "chatgpt": {
                "available": providers["chatgpt"],
                "model": settings.chatgpt_model if providers["chatgpt"] else None,
                "description": "OpenAI ChatGPT - Versatile and fast"
            },
            "gemini": {
                "available": providers["gemini"],
                "model": settings.gemini_model if providers["gemini"] else None,
                "description": "Google Gemini - Powerful and multilingual"
            }
        }
    }


@router.post("/generate", response_model=ContentResponse)
async def generate_content(
    request: ContentGenerationRequest
):
    """
    Generate SEO-optimized content for a keyword.

    This endpoint generates complete blog content including:
    - Title and meta description
    - Structured HTML content with proper headings
    - Internal link suggestions
    - FAQ section (optional)
    - Schema markup

    You can specify the LLM provider (claude, chatgpt, gemini) in the request.
    If not specified, the default provider from settings will be used.
    """
    logger.info(
        "content_generation_requested",
        keyword=request.keyword,
        provider=request.llm_provider or "default"
    )

    try:
        # Create content service with specified provider
        content_service = ContentGeneratorService(provider=request.llm_provider)

        content = await content_service.generate_content(
            keyword=request.keyword,
            target_word_count=request.target_word_count,
            tone=request.tone,
            include_faq=request.include_faq
        )

        return ContentResponse(**content)

    except ValueError as e:
        # Provider configuration errors
        logger.error("invalid_provider_configuration", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("content_generation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content generation failed: {str(e)}"
        )


@router.post("/create-post", response_model=PostResponse)
async def create_post(
    request: PostCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new blog post in the database."""
    logger.info("creating_post", title=request.title)

    try:
        # Generate slug from title
        slug = generate_slug(request.title)

        # Check if slug already exists
        result = await db.execute(select(Post).where(Post.slug == slug))
        if result.scalar_one_or_none():
            # Add timestamp to make unique
            slug = f"{slug}-{int(datetime.now().timestamp())}"

        # Calculate word count
        from app.utils.seo import count_words
        word_count = count_words(request.content)

        # Create post
        post = Post(
            title=request.title,
            slug=slug,
            content=request.content,
            meta_description=request.meta_description,
            keyword_id=request.keyword_id,
            status=request.status.value,
            scheduled_for=request.scheduled_for,
            categories=request.categories,
            tags=request.tags,
            featured_image_url=request.featured_image_url,
            word_count=word_count,
        )

        db.add(post)
        await db.commit()
        await db.refresh(post)

        return PostResponse.model_validate(post)

    except Exception as e:
        logger.error("post_creation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Post creation failed: {str(e)}"
        )


@router.post("/publish", response_model=PublishResponse)
async def publish_post(
    request: PublishRequest,
    db: AsyncSession = Depends(get_db),
    publisher: WordPressPublisher = Depends(get_publisher_service)
):
    """
    Publish a post to WordPress.

    This endpoint:
    1. Retrieves the post from database
    2. Uploads images to WordPress
    3. Creates the post on WordPress
    4. Updates the database with WordPress post ID and URL
    """
    logger.info("publishing_post", post_id=request.post_id)

    try:
        # Get post from database
        result = await db.execute(select(Post).where(Post.id == request.post_id))
        post = result.scalar_one_or_none()

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with ID {request.post_id} not found"
            )

        # Upload images
        featured_media_id = None
        if post.featured_image_url:
            # Upload featured image
            # This is simplified - in production, handle image paths properly
            pass

        # Determine status
        wp_status = "publish" if request.publish_immediately else "future"

        # Create post on WordPress
        wp_post = await publisher.create_post(
            title=post.title,
            content=post.content,
            status=wp_status,
            categories=post.categories or [],
            tags=post.tags or [],
            featured_image_id=featured_media_id,
            excerpt=post.meta_description,
            scheduled_date=request.scheduled_time
        )

        if not wp_post:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish post to WordPress"
            )

        # Update post in database
        post.wp_post_id = wp_post["id"]
        post.wp_url = wp_post["url"]
        post.status = "published"
        post.published_at = datetime.now()

        await db.commit()

        return PublishResponse(
            post_id=post.id,
            wp_post_id=wp_post["id"],
            wp_url=wp_post["url"],
            status="published",
            published_at=datetime.now(),
            message="Post published successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("publishing_failed", error=str(e), post_id=request.post_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Publishing failed: {str(e)}"
        )


@router.post("/complete-workflow", response_model=CompleteWorkflowResponse)
async def complete_workflow(
    request: CompleteWorkflowRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute complete blog automation workflow.

    This endpoint triggers a Celery task that will:
    1. Research keywords
    2. Generate content for top keywords
    3. Generate and optimize images
    4. Insert AdSense ads
    5. Publish to WordPress

    Returns a task ID for tracking progress.
    """
    logger.info("complete_workflow_requested", seeds=request.seed_keywords)

    try:
        # Import Celery task
        from app.tasks.celery_tasks import complete_blog_workflow

        # Trigger Celery task
        task = complete_blog_workflow.delay(
            seed_keywords=request.seed_keywords,
            num_posts=request.num_posts,
            publish_immediately=request.publish_immediately,
            schedule_interval_hours=request.schedule_interval_hours
        )

        return CompleteWorkflowResponse(
            task_id=task.id,
            status="queued",
            message="Workflow task queued successfully",
            estimated_completion_time=None  # Could calculate based on queue
        )

    except Exception as e:
        logger.error("workflow_trigger_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow trigger failed: {str(e)}"
        )
