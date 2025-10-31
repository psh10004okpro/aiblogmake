"""
Google Analytics API Routes

Provides endpoints for fetching and analyzing Google Analytics data.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.services.analytics import get_analytics_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/status")
async def get_analytics_status():
    """
    Get Google Analytics configuration status.

    Returns configuration status and whether API is available.
    """
    try:
        analytics_service = get_analytics_service()
        status_data = analytics_service.get_status()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": status_data
            }
        )

    except Exception as e:
        logger.error("analytics_status_check_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check analytics status: {str(e)}"
        )


@router.get("/overview")
async def get_overview(
    start_date: str = Query(default="30daysAgo", description="Start date (e.g., '30daysAgo', '2025-01-01')"),
    end_date: str = Query(default="today", description="End date (e.g., 'today', '2025-01-31')")
):
    """
    Get overview analytics metrics for the specified date range.

    Returns page views, sessions, users, bounce rate, engagement rate, etc.

    **Date formats:**
    - Relative: "today", "yesterday", "7daysAgo", "30daysAgo"
    - Absolute: "2025-01-01", "2025-01-31"

    **Example:**
    ```
    GET /api/v1/analytics/overview?start_date=30daysAgo&end_date=today
    ```
    """
    try:
        analytics_service = get_analytics_service()

        if not analytics_service.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google Analytics is not configured. Please set GA_PROPERTY_ID and GA_CREDENTIALS_PATH in .env"
            )

        metrics = await analytics_service.get_overview_metrics(start_date, end_date)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "date_range": {
                        "start": start_date,
                        "end": end_date
                    },
                    "metrics": {
                        "page_views": metrics.page_views,
                        "sessions": metrics.sessions,
                        "users": metrics.users,
                        "new_users": metrics.new_users,
                        "bounce_rate": round(metrics.bounce_rate, 2),
                        "avg_session_duration": round(metrics.avg_session_duration, 2),
                        "engagement_rate": round(metrics.engagement_rate, 2)
                    }
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("analytics_overview_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch overview metrics: {str(e)}"
        )


@router.get("/realtime")
async def get_realtime():
    """
    Get realtime analytics data.

    Returns:
    - Current active users
    - Active users by country (top 10)
    - Active users by device category

    **Example:**
    ```
    GET /api/v1/analytics/realtime
    ```
    """
    try:
        analytics_service = get_analytics_service()

        if not analytics_service.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google Analytics is not configured"
            )

        realtime_data = await analytics_service.get_realtime_metrics()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": realtime_data
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("analytics_realtime_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch realtime metrics: {str(e)}"
        )


@router.get("/traffic-sources")
async def get_traffic_sources(
    start_date: str = Query(default="30daysAgo"),
    end_date: str = Query(default="today"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of sources to return")
):
    """
    Get traffic sources breakdown.

    Returns top traffic sources by sessions, including:
    - Source (e.g., google, facebook, direct)
    - Medium (e.g., organic, social, referral)
    - Sessions, users, and page views

    **Example:**
    ```
    GET /api/v1/analytics/traffic-sources?start_date=30daysAgo&end_date=today&limit=10
    ```
    """
    try:
        analytics_service = get_analytics_service()

        if not analytics_service.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google Analytics is not configured"
            )

        sources = await analytics_service.get_traffic_sources(start_date, end_date, limit)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "date_range": {
                        "start": start_date,
                        "end": end_date
                    },
                    "sources": [
                        {
                            "source": source.source,
                            "medium": source.medium,
                            "sessions": source.sessions,
                            "users": source.users,
                            "page_views": source.page_views
                        }
                        for source in sources
                    ],
                    "total_count": len(sources)
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("analytics_traffic_sources_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch traffic sources: {str(e)}"
        )


@router.get("/top-posts")
async def get_top_posts(
    start_date: str = Query(default="30daysAgo"),
    end_date: str = Query(default="today"),
    limit: int = Query(default=10, ge=1, le=100, description="Number of posts to return")
):
    """
    Get top performing blog posts.

    Returns posts ranked by page views, including:
    - Page path and title
    - Page views and unique users
    - Average time on page
    - Bounce rate and engagement rate

    **Example:**
    ```
    GET /api/v1/analytics/top-posts?start_date=30daysAgo&end_date=today&limit=10
    ```
    """
    try:
        analytics_service = get_analytics_service()

        if not analytics_service.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google Analytics is not configured"
            )

        posts = await analytics_service.get_top_posts(start_date, end_date, limit)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "date_range": {
                        "start": start_date,
                        "end": end_date
                    },
                    "posts": [
                        {
                            "page_path": post.page_path,
                            "page_title": post.page_title,
                            "page_views": post.page_views,
                            "unique_users": post.unique_users,
                            "avg_time_on_page": round(post.avg_time_on_page, 2),
                            "bounce_rate": round(post.bounce_rate, 2),
                            "engagement_rate": round(post.engagement_rate, 2)
                        }
                        for post in posts
                    ],
                    "total_count": len(posts)
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("analytics_top_posts_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch top posts: {str(e)}"
        )


@router.get("/post/{post_path:path}")
async def get_post_performance(
    post_path: str,
    start_date: str = Query(default="30daysAgo"),
    end_date: str = Query(default="today")
):
    """
    Get performance metrics for a specific blog post.

    Returns detailed analytics for a single post by its URL path.

    **Example:**
    ```
    GET /api/v1/analytics/post//blog/my-post?start_date=30daysAgo&end_date=today
    ```

    **Parameters:**
    - post_path: URL path of the post (e.g., "/blog/my-post")
    - start_date: Start date for metrics
    - end_date: End date for metrics
    """
    try:
        analytics_service = get_analytics_service()

        if not analytics_service.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google Analytics is not configured"
            )

        # Ensure post_path starts with /
        if not post_path.startswith('/'):
            post_path = '/' + post_path

        post = await analytics_service.get_post_performance(post_path, start_date, end_date)

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No analytics data found for post: {post_path}"
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "date_range": {
                        "start": start_date,
                        "end": end_date
                    },
                    "post": {
                        "page_path": post.page_path,
                        "page_title": post.page_title,
                        "page_views": post.page_views,
                        "unique_users": post.unique_users,
                        "avg_time_on_page": round(post.avg_time_on_page, 2),
                        "bounce_rate": round(post.bounce_rate, 2),
                        "engagement_rate": round(post.engagement_rate, 2)
                    }
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("analytics_post_performance_failed", error=str(e), post_path=post_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch post performance: {str(e)}"
        )


@router.get("/comparison")
async def get_comparison(
    current_start: str = Query(default="30daysAgo", description="Current period start"),
    current_end: str = Query(default="today", description="Current period end"),
    previous_start: str = Query(default="60daysAgo", description="Previous period start"),
    previous_end: str = Query(default="31daysAgo", description="Previous period end")
):
    """
    Get comparison data between two periods.

    Compares metrics between current and previous periods and calculates
    percentage changes.

    **Example:**
    ```
    GET /api/v1/analytics/comparison?current_start=30daysAgo&current_end=today&previous_start=60daysAgo&previous_end=31daysAgo
    ```

    **Returns:**
    - Current period metrics
    - Previous period metrics
    - Change values and percentages for all metrics
    """
    try:
        analytics_service = get_analytics_service()

        if not analytics_service.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google Analytics is not configured"
            )

        comparison = await analytics_service.get_comparison_data(
            current_start, current_end,
            previous_start, previous_end
        )

        # Convert dataclass to dict for JSON serialization
        comparison["current_period"]["metrics"] = {
            "page_views": comparison["current_period"]["metrics"].page_views,
            "sessions": comparison["current_period"]["metrics"].sessions,
            "users": comparison["current_period"]["metrics"].users,
            "new_users": comparison["current_period"]["metrics"].new_users,
            "bounce_rate": round(comparison["current_period"]["metrics"].bounce_rate, 2),
            "avg_session_duration": round(comparison["current_period"]["metrics"].avg_session_duration, 2),
            "engagement_rate": round(comparison["current_period"]["metrics"].engagement_rate, 2)
        }

        comparison["previous_period"]["metrics"] = {
            "page_views": comparison["previous_period"]["metrics"].page_views,
            "sessions": comparison["previous_period"]["metrics"].sessions,
            "users": comparison["previous_period"]["metrics"].users,
            "new_users": comparison["previous_period"]["metrics"].new_users,
            "bounce_rate": round(comparison["previous_period"]["metrics"].bounce_rate, 2),
            "avg_session_duration": round(comparison["previous_period"]["metrics"].avg_session_duration, 2),
            "engagement_rate": round(comparison["previous_period"]["metrics"].engagement_rate, 2)
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": comparison
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("analytics_comparison_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch comparison data: {str(e)}"
        )
