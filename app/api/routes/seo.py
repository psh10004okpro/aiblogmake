"""
API routes for SEO analysis and scoring.

This module provides endpoints for analyzing content SEO quality and tracking scores.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.database import SEOScore as SEOScoreModel, Post
from app.models.schemas import (
    SEOAnalysisRequest,
    SEOScoreResponse,
    SEOScoreDetail,
    SEOIssue,
    SEOMetrics,
)
from app.services.seo_analyzer import SEOAnalyzer
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/seo", tags=["seo"])


@router.post("/analyze", response_model=SEOScoreResponse)
async def analyze_content(request: SEOAnalysisRequest):
    """
    Analyze content for SEO quality.

    This endpoint performs comprehensive SEO analysis including:
    - Keyword density and placement
    - Title optimization
    - Meta description quality
    - Content readability
    - Internal linking
    - Image alt text optimization

    **Example Request:**
    ```json
    {
        "title": "완벽한 블로그 SEO 가이드",
        "content": "<p>블로그 SEO는 검색 엔진 최적화의 핵심입니다...</p>",
        "meta_description": "블로그 SEO 최적화 방법을 단계별로 알려드립니다.",
        "target_keyword": "블로그 SEO",
        "h2_tags": ["SEO란 무엇인가", "키워드 리서치"],
        "h3_tags": ["온페이지 SEO", "오프페이지 SEO"],
        "internal_links": ["/seo-basics", "/keyword-research"],
        "images": [
            {"url": "image1.jpg", "alt_text": "블로그 SEO 체크리스트"}
        ]
    }
    ```

    **Returns:**
    - Overall SEO score (0-100)
    - Component scores for each category
    - List of issues found
    - Actionable suggestions
    - Detailed metrics
    """
    logger.info("seo_analysis_requested", keyword=request.target_keyword)

    try:
        analyzer = SEOAnalyzer()

        # Perform analysis
        result = analyzer.analyze(
            title=request.title,
            content=request.content,
            meta_description=request.meta_description,
            target_keyword=request.target_keyword,
            h1_tag=request.h1_tag,
            h2_tags=request.h2_tags,
            h3_tags=request.h3_tags,
            internal_links=request.internal_links,
            images=request.images
        )

        # Convert to response format
        grade = analyzer._get_grade(result.overall_score)

        return SEOScoreResponse(
            overall_score=result.overall_score,
            grade=grade,
            keyword_density_score=result.keyword_density_score,
            title_optimization_score=result.title_optimization_score,
            meta_tags_score=result.meta_tags_score,
            readability_score=result.readability_score,
            internal_links_score=result.internal_links_score,
            image_alt_score=result.image_alt_score,
            issues=[SEOIssue(**issue) for issue in result.issues],
            suggestions=result.suggestions,
            metrics=SEOMetrics(**result.metrics)
        )

    except Exception as e:
        logger.error("seo_analysis_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"SEO analysis failed: {str(e)}"
        )


@router.post("/analyze-post/{post_id}", response_model=SEOScoreResponse)
async def analyze_post(
    post_id: int,
    save_score: bool = Query(True, description="Save score to database"),
    db: Session = Depends(get_db)
):
    """
    Analyze an existing post for SEO quality.

    This endpoint retrieves a post from the database and performs SEO analysis.
    Optionally saves the score to the database.

    **Query Parameters:**
    - save_score: Whether to save the analysis result (default: true)

    **Returns:**
    - Complete SEO analysis with scores and suggestions
    """
    logger.info("seo_post_analysis_requested", post_id=post_id)

    # Get post from database
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    try:
        analyzer = SEOAnalyzer()

        # Get keyword from post
        keyword = post.keyword.keyword if post.keyword else "unknown"

        # Perform analysis
        result = analyzer.analyze(
            title=post.title,
            content=post.content,
            meta_description=post.meta_description or "",
            target_keyword=keyword,
            h1_tag=post.h1_tag,
            h2_tags=[],  # TODO: Extract from content
            h3_tags=[],  # TODO: Extract from content
            internal_links=post.internal_links or [],
            images=[{"url": img.url, "alt_text": img.alt_text or ""} for img in post.images]
        )

        # Save to database if requested
        if save_score:
            # Check if score already exists
            existing_score = db.query(SEOScoreModel).filter(
                SEOScoreModel.post_id == post_id
            ).first()

            grade = analyzer._get_grade(result.overall_score)

            if existing_score:
                # Update existing score
                existing_score.overall_score = result.overall_score
                existing_score.grade = grade
                existing_score.keyword_density_score = result.keyword_density_score
                existing_score.title_optimization_score = result.title_optimization_score
                existing_score.meta_tags_score = result.meta_tags_score
                existing_score.readability_score = result.readability_score
                existing_score.internal_links_score = result.internal_links_score
                existing_score.image_alt_score = result.image_alt_score
                existing_score.issues = result.issues
                existing_score.suggestions = result.suggestions
                existing_score.metrics = result.metrics
                existing_score.target_keyword = keyword
                existing_score.analyzed_at = datetime.utcnow()
            else:
                # Create new score
                new_score = SEOScoreModel(
                    post_id=post_id,
                    overall_score=result.overall_score,
                    grade=grade,
                    keyword_density_score=result.keyword_density_score,
                    title_optimization_score=result.title_optimization_score,
                    meta_tags_score=result.meta_tags_score,
                    readability_score=result.readability_score,
                    internal_links_score=result.internal_links_score,
                    image_alt_score=result.image_alt_score,
                    issues=result.issues,
                    suggestions=result.suggestions,
                    metrics=result.metrics,
                    target_keyword=keyword
                )
                db.add(new_score)

            db.commit()

            logger.info("seo_score_saved", post_id=post_id, score=result.overall_score)

        return SEOScoreResponse(
            overall_score=result.overall_score,
            grade=analyzer._get_grade(result.overall_score),
            keyword_density_score=result.keyword_density_score,
            title_optimization_score=result.title_optimization_score,
            meta_tags_score=result.meta_tags_score,
            readability_score=result.readability_score,
            internal_links_score=result.internal_links_score,
            image_alt_score=result.image_alt_score,
            issues=[SEOIssue(**issue) for issue in result.issues],
            suggestions=result.suggestions,
            metrics=SEOMetrics(**result.metrics)
        )

    except Exception as e:
        logger.error("seo_post_analysis_failed", post_id=post_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"SEO analysis failed: {str(e)}"
        )


@router.get("/scores/{post_id}", response_model=SEOScoreDetail)
async def get_post_seo_score(
    post_id: int,
    db: Session = Depends(get_db)
):
    """
    Get SEO score for a post.

    Retrieves the saved SEO score for a specific post.

    **Returns:**
    - Detailed SEO score with all components
    - Analysis metadata (when analyzed, version)
    """
    logger.info("seo_score_requested", post_id=post_id)

    score = db.query(SEOScoreModel).filter(
        SEOScoreModel.post_id == post_id
    ).first()

    if not score:
        raise HTTPException(
            status_code=404,
            detail="SEO score not found for this post. Run analysis first."
        )

    return score


@router.get("/scores", response_model=List[SEOScoreDetail])
async def list_seo_scores(
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum score"),
    max_score: Optional[float] = Query(None, ge=0, le=100, description="Maximum score"),
    grade: Optional[str] = Query(None, description="Filter by grade (A+, A, B+, etc.)"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    List SEO scores with filtering.

    **Query Parameters:**
    - min_score: Filter scores >= this value
    - max_score: Filter scores <= this value
    - grade: Filter by grade (A+, A, B+, B, C+, C, D, F)
    - limit: Number of results to return (default: 50)
    - offset: Pagination offset (default: 0)

    **Example:**
    ```
    GET /seo/scores?min_score=80&limit=10
    GET /seo/scores?grade=A&limit=20
    ```

    **Returns:**
    - List of SEO scores matching filters
    """
    logger.info(
        "seo_scores_list_requested",
        min_score=min_score,
        max_score=max_score,
        grade=grade
    )

    # Build query
    query = db.query(SEOScoreModel)

    if min_score is not None:
        query = query.filter(SEOScoreModel.overall_score >= min_score)

    if max_score is not None:
        query = query.filter(SEOScoreModel.overall_score <= max_score)

    if grade:
        query = query.filter(SEOScoreModel.grade == grade.upper())

    # Order by score (descending) and apply pagination
    scores = query.order_by(desc(SEOScoreModel.overall_score)).offset(offset).limit(limit).all()

    return scores


@router.delete("/scores/{post_id}")
async def delete_seo_score(
    post_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete SEO score for a post.

    This will remove the SEO analysis result for the specified post.

    **Returns:**
    - success: Whether deletion was successful
    - message: Confirmation message
    """
    logger.info("seo_score_delete_requested", post_id=post_id)

    score = db.query(SEOScoreModel).filter(
        SEOScoreModel.post_id == post_id
    ).first()

    if not score:
        raise HTTPException(status_code=404, detail="SEO score not found")

    try:
        db.delete(score)
        db.commit()

        logger.info("seo_score_deleted", post_id=post_id)

        return {
            "success": True,
            "message": f"SEO score for post {post_id} deleted successfully"
        }

    except Exception as e:
        logger.error("seo_score_delete_failed", post_id=post_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete SEO score: {str(e)}"
        )


@router.get("/stats")
async def get_seo_stats(db: Session = Depends(get_db)):
    """
    Get overall SEO statistics.

    **Returns:**
    - total_analyzed: Total number of posts analyzed
    - average_score: Average SEO score across all posts
    - grade_distribution: Count of posts by grade
    - top_performers: List of top 5 posts by SEO score
    - needs_improvement: List of 5 posts with lowest scores
    """
    logger.info("seo_stats_requested")

    try:
        # Total count
        total_analyzed = db.query(SEOScoreModel).count()

        if total_analyzed == 0:
            return {
                "total_analyzed": 0,
                "average_score": 0,
                "grade_distribution": {},
                "top_performers": [],
                "needs_improvement": []
            }

        # Average score
        from sqlalchemy import func as sql_func
        avg_score = db.query(sql_func.avg(SEOScoreModel.overall_score)).scalar()

        # Grade distribution
        grade_counts = db.query(
            SEOScoreModel.grade,
            sql_func.count(SEOScoreModel.id)
        ).group_by(SEOScoreModel.grade).all()

        grade_distribution = {grade: count for grade, count in grade_counts}

        # Top performers
        top_performers = db.query(SEOScoreModel).order_by(
            desc(SEOScoreModel.overall_score)
        ).limit(5).all()

        # Needs improvement
        needs_improvement = db.query(SEOScoreModel).order_by(
            SEOScoreModel.overall_score.asc()
        ).limit(5).all()

        return {
            "total_analyzed": total_analyzed,
            "average_score": round(float(avg_score), 2) if avg_score else 0,
            "grade_distribution": grade_distribution,
            "top_performers": [
                {
                    "post_id": s.post_id,
                    "score": s.overall_score,
                    "grade": s.grade,
                    "keyword": s.target_keyword
                }
                for s in top_performers
            ],
            "needs_improvement": [
                {
                    "post_id": s.post_id,
                    "score": s.overall_score,
                    "grade": s.grade,
                    "keyword": s.target_keyword,
                    "issue_count": len(s.issues) if s.issues else 0
                }
                for s in needs_improvement
            ]
        }

    except Exception as e:
        logger.error("seo_stats_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get SEO stats: {str(e)}"
        )
