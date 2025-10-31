"""
경쟁자 분석 API 라우트
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
import logging

from app.services.competitor_analysis import (
    get_competitor_analysis_service,
    CompetitorBlog,
    BlogPost,
    KeywordGap,
    ContentGap,
    CompetitorReport
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/competitor", tags=["competitor"])

# Request Models

class FetchPostsRequest(BaseModel):
    """포스트 가져오기 요청"""
    rss_feed_url: str = Field(..., description="RSS 피드 URL")
    days: int = Field(default=30, ge=1, le=90, description="조회 기간 (일)")


class AnalyzeKeywordGapsRequest(BaseModel):
    """키워드 갭 분석 요청"""
    our_keywords: List[str] = Field(..., description="우리 키워드 리스트")
    competitor_keywords: List[str] = Field(..., description="경쟁자 키워드 리스트")


class AnalyzeContentGapsRequest(BaseModel):
    """콘텐츠 갭 분석 요청"""
    competitor_posts: List[Dict[str, Any]] = Field(..., description="경쟁자 포스트 리스트")
    our_topics: List[str] = Field(..., description="우리가 다룬 주제 리스트")


class GenerateReportRequest(BaseModel):
    """종합 리포트 생성 요청"""
    competitor_name: str = Field(..., description="경쟁자 이름")
    competitor_url: str = Field(..., description="경쟁자 블로그 URL")
    rss_feed_url: str = Field(..., description="RSS 피드 URL")
    domain_authority: Optional[int] = Field(default=None, description="도메인 권위도")
    monthly_traffic: Optional[int] = Field(default=None, description="월간 트래픽")
    our_keywords: List[str] = Field(..., description="우리 키워드")
    our_topics: List[str] = Field(..., description="우리 주제")


class SuggestContentIdeasRequest(BaseModel):
    """콘텐츠 아이디어 제안 요청"""
    competitor_posts: List[Dict[str, Any]] = Field(..., description="경쟁자 포스트")
    num_ideas: int = Field(default=5, ge=1, le=10, description="아이디어 개수")


# API Endpoints

@router.post("/fetch-posts")
async def fetch_competitor_posts(request: FetchPostsRequest):
    """
    경쟁자 블로그의 최근 포스트 가져오기 (RSS)

    - **rss_feed_url**: RSS 피드 URL
    - **days**: 조회 기간 (기본 30일)

    Returns:
    - 최근 포스트 리스트
    - 각 포스트의 제목, URL, 발행일, 요약, 키워드
    """
    try:
        logger.info(f"Fetching posts from: {request.rss_feed_url}")
        service = get_competitor_analysis_service()

        posts = await service.fetch_competitor_posts(
            rss_feed_url=request.rss_feed_url,
            days=request.days
        )

        return {
            "success": True,
            "total_posts": len(posts),
            "posts": [
                {
                    "title": post.title,
                    "url": post.url,
                    "published_date": post.published_date,
                    "excerpt": post.excerpt,
                    "keywords": post.keywords,
                    "estimated_traffic": post.estimated_traffic
                }
                for post in posts
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching competitor posts: {e}")
        raise HTTPException(status_code=500, detail=f"포스트 가져오기 실패: {str(e)}")


@router.post("/keyword-gaps")
async def analyze_keyword_gaps(request: AnalyzeKeywordGapsRequest):
    """
    키워드 갭 분석

    - **our_keywords**: 우리 블로그의 키워드
    - **competitor_keywords**: 경쟁자 블로그의 키워드

    Returns:
    - 경쟁자는 있지만 우리는 없는 키워드
    - 각 키워드의 기회 점수 및 난이도
    - 추천 주제
    """
    try:
        logger.info("Analyzing keyword gaps")
        service = get_competitor_analysis_service()

        gaps = await service.analyze_keyword_gaps(
            our_keywords=request.our_keywords,
            competitor_keywords=request.competitor_keywords
        )

        return {
            "success": True,
            "total_gaps": len(gaps),
            "keyword_gaps": [
                {
                    "keyword": gap.keyword,
                    "competitor_rank": gap.competitor_rank,
                    "our_rank": gap.our_rank,
                    "search_volume": gap.search_volume,
                    "difficulty": gap.difficulty,
                    "opportunity_score": gap.opportunity_score,
                    "suggested_topics": gap.suggested_topics
                }
                for gap in gaps
            ]
        }

    except Exception as e:
        logger.error(f"Error analyzing keyword gaps: {e}")
        raise HTTPException(status_code=500, detail=f"키워드 갭 분석 실패: {str(e)}")


@router.post("/content-gaps")
async def analyze_content_gaps(request: AnalyzeContentGapsRequest):
    """
    콘텐츠 갭 분석

    - **competitor_posts**: 경쟁자 포스트 리스트
    - **our_topics**: 우리가 다룬 주제 리스트

    Returns:
    - 경쟁자는 다루지만 우리는 다루지 않은 주제
    - 각 주제의 기회 점수
    - 차별화 각도 제안
    """
    try:
        logger.info("Analyzing content gaps")
        service = get_competitor_analysis_service()

        # 포스트 데이터 변환
        blog_posts = []
        for post_data in request.competitor_posts:
            blog_posts.append(BlogPost(
                title=post_data.get('title', ''),
                url=post_data.get('url', ''),
                published_date=post_data.get('published_date', ''),
                excerpt=post_data.get('excerpt', ''),
                keywords=post_data.get('keywords', []),
                estimated_traffic=post_data.get('estimated_traffic')
            ))

        gaps = await service.analyze_content_gaps(
            competitor_posts=blog_posts,
            our_topics=request.our_topics
        )

        return {
            "success": True,
            "total_gaps": len(gaps),
            "content_gaps": [
                {
                    "topic": gap.topic,
                    "competitor_posts": [
                        {
                            "title": post.title,
                            "url": post.url,
                            "published_date": post.published_date
                        }
                        for post in gap.competitor_posts
                    ],
                    "our_coverage": gap.our_coverage,
                    "opportunity_score": gap.opportunity_score,
                    "suggested_angle": gap.suggested_angle,
                    "estimated_traffic": gap.estimated_traffic
                }
                for gap in gaps
            ]
        }

    except Exception as e:
        logger.error(f"Error analyzing content gaps: {e}")
        raise HTTPException(status_code=500, detail=f"콘텐츠 갭 분석 실패: {str(e)}")


@router.post("/generate-report")
async def generate_competitor_report(request: GenerateReportRequest):
    """
    경쟁자 종합 분석 리포트 생성

    - **competitor_name**: 경쟁자 이름
    - **competitor_url**: 경쟁자 블로그 URL
    - **rss_feed_url**: RSS 피드 URL
    - **our_keywords**: 우리 키워드
    - **our_topics**: 우리 주제

    Returns:
    - 종합 분석 리포트
    - 최근 포스트, 키워드 갭, 콘텐츠 갭
    - SEO 비교 및 권장 사항
    """
    try:
        logger.info(f"Generating report for: {request.competitor_name}")
        service = get_competitor_analysis_service()

        competitor = CompetitorBlog(
            name=request.competitor_name,
            url=request.competitor_url,
            rss_feed=request.rss_feed_url,
            domain_authority=request.domain_authority,
            monthly_traffic=request.monthly_traffic
        )

        report = await service.generate_competitor_report(
            competitor=competitor,
            our_keywords=request.our_keywords,
            our_topics=request.our_topics
        )

        return {
            "success": True,
            "competitor_name": report.competitor_name,
            "analysis_date": report.analysis_date,
            "recent_posts": [
                {
                    "title": post.title,
                    "url": post.url,
                    "published_date": post.published_date,
                    "excerpt": post.excerpt,
                    "keywords": post.keywords
                }
                for post in report.recent_posts
            ],
            "keyword_gaps": [
                {
                    "keyword": gap.keyword,
                    "opportunity_score": gap.opportunity_score,
                    "difficulty": gap.difficulty,
                    "suggested_topics": gap.suggested_topics
                }
                for gap in report.keyword_gaps
            ],
            "content_gaps": [
                {
                    "topic": gap.topic,
                    "opportunity_score": gap.opportunity_score,
                    "suggested_angle": gap.suggested_angle,
                    "estimated_traffic": gap.estimated_traffic
                }
                for gap in report.content_gaps
            ],
            "seo_comparison": report.seo_comparison,
            "recommendations": report.recommendations
        }

    except Exception as e:
        logger.error(f"Error generating competitor report: {e}")
        raise HTTPException(status_code=500, detail=f"리포트 생성 실패: {str(e)}")


@router.post("/suggest-content-ideas")
async def suggest_content_ideas(request: SuggestContentIdeasRequest):
    """
    경쟁자 포스트 기반 콘텐츠 아이디어 제안

    - **competitor_posts**: 경쟁자 포스트 리스트
    - **num_ideas**: 생성할 아이디어 개수 (1-10)

    Returns:
    - 차별화된 콘텐츠 아이디어
    - 각 아이디어의 제목과 차별화 각도
    """
    try:
        logger.info("Suggesting content ideas")
        service = get_competitor_analysis_service()

        # 포스트 데이터 변환
        blog_posts = []
        for post_data in request.competitor_posts:
            blog_posts.append(BlogPost(
                title=post_data.get('title', ''),
                url=post_data.get('url', ''),
                published_date=post_data.get('published_date', ''),
                excerpt=post_data.get('excerpt', ''),
                keywords=post_data.get('keywords', [])
            ))

        ideas = await service.suggest_content_ideas(
            competitor_posts=blog_posts,
            num_ideas=request.num_ideas
        )

        return {
            "success": True,
            "total_ideas": len(ideas),
            "content_ideas": ideas
        }

    except Exception as e:
        logger.error(f"Error suggesting content ideas: {e}")
        raise HTTPException(status_code=500, detail=f"아이디어 제안 실패: {str(e)}")


@router.get("/best-practices")
async def get_best_practices():
    """
    경쟁자 분석 모범 사례

    Returns:
    - 분석 주기 및 방법
    - 주요 지표
    - 권장 사항
    """
    return {
        "analysis_frequency": {
            "recommended": "Weekly",
            "minimum": "Monthly",
            "description": "경쟁자 동향을 주간 단위로 모니터링하는 것이 이상적"
        },
        "key_metrics": [
            {
                "metric": "Domain Authority",
                "description": "도메인 권위도 - SEO 순위에 영향",
                "good_value": "> 50",
                "how_to_improve": "백링크 구축, 고품질 콘텐츠"
            },
            {
                "metric": "Content Frequency",
                "description": "콘텐츠 발행 빈도",
                "good_value": "> 3 posts/week",
                "how_to_improve": "콘텐츠 자동화, 팀 확장"
            },
            {
                "metric": "Keyword Coverage",
                "description": "키워드 커버리지",
                "good_value": "> 100 keywords",
                "how_to_improve": "키워드 리서치, 롱테일 키워드 공략"
            },
            {
                "metric": "Backlink Profile",
                "description": "백링크 프로필",
                "good_value": "> 1000 backlinks",
                "how_to_improve": "게스트 포스팅, PR 활동"
            }
        ],
        "competitive_strategies": [
            {
                "strategy": "Content Gap 우선순위",
                "description": "경쟁자가 다루지만 우리는 없는 주제를 먼저 공략",
                "expected_impact": "빠른 트래픽 증가"
            },
            {
                "strategy": "차별화 각도",
                "description": "같은 주제라도 다른 관점으로 접근",
                "expected_impact": "고유 가치 제공"
            },
            {
                "strategy": "품질 우선",
                "description": "경쟁자보다 더 깊이 있고 유용한 콘텐츠 작성",
                "expected_impact": "높은 체류 시간, 낮은 이탈률"
            },
            {
                "strategy": "속도 경쟁",
                "description": "트렌드 주제를 경쟁자보다 빠르게 다루기",
                "expected_impact": "First-mover advantage"
            }
        ],
        "tools_recommendations": [
            "SEMrush - 키워드 및 백링크 분석",
            "Ahrefs - 경쟁자 트래픽 분석",
            "BuzzSumo - 인기 콘텐츠 발견",
            "Google Search Console - 검색 성과 추적",
            "RSS Feed Reader - 경쟁자 모니터링"
        ],
        "common_mistakes": [
            "경쟁자를 단순히 복사하기 (차별화 없음)",
            "너무 많은 경쟁자 추적 (3-5개로 제한)",
            "분석만 하고 실행하지 않기",
            "장기적 관점 없이 단기 트렌드만 쫓기"
        ]
    }
