"""
멀티 블로그 관리 API 라우트
여러 WordPress 사이트 동시 관리
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.multi_blog import get_multi_blog_service, MultiBlogService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/multi-blog", tags=["multi-blog"])

# Request Models

class CreateSiteRequest(BaseModel):
    """WordPress 사이트 생성 요청"""
    name: str = Field(..., description="사이트 이름")
    url: str = Field(..., description="WordPress 사이트 URL")
    username: str = Field(..., description="WordPress 사용자명")
    app_password: str = Field(..., description="WordPress Application Password")
    is_active: bool = Field(default=True, description="활성화 상태")
    default_category: str = Field(default="Uncategorized", description="기본 카테고리")
    default_tags: List[str] = Field(default=[], description="기본 태그")
    auto_publish: bool = Field(default=False, description="자동 발행 여부")
    publish_delay_minutes: int = Field(default=0, description="발행 지연 시간(분)")
    description: Optional[str] = Field(default=None, description="사이트 설명")
    language: str = Field(default="ko", description="언어")
    timezone: str = Field(default="Asia/Seoul", description="타임존")


class UpdateSiteRequest(BaseModel):
    """WordPress 사이트 업데이트 요청"""
    name: Optional[str] = Field(default=None, description="사이트 이름")
    url: Optional[str] = Field(default=None, description="WordPress 사이트 URL")
    username: Optional[str] = Field(default=None, description="WordPress 사용자명")
    app_password: Optional[str] = Field(default=None, description="WordPress Application Password")
    is_active: Optional[bool] = Field(default=None, description="활성화 상태")
    default_category: Optional[str] = Field(default=None, description="기본 카테고리")
    default_tags: Optional[List[str]] = Field(default=None, description="기본 태그")
    auto_publish: Optional[bool] = Field(default=None, description="자동 발행 여부")
    publish_delay_minutes: Optional[int] = Field(default=None, description="발행 지연 시간(분)")
    description: Optional[str] = Field(default=None, description="사이트 설명")
    language: Optional[str] = Field(default=None, description="언어")
    timezone: Optional[str] = Field(default=None, description="타임존")


class PublishToSiteRequest(BaseModel):
    """특정 사이트에 발행 요청"""
    site_id: int = Field(..., description="사이트 ID")
    post_id: int = Field(..., description="포스트 ID")
    schedule_time: Optional[datetime] = Field(default=None, description="예약 시간 (없으면 즉시 발행)")


class PublishToMultipleSitesRequest(BaseModel):
    """여러 사이트에 발행 요청"""
    post_id: int = Field(..., description="포스트 ID")
    site_ids: List[int] = Field(..., description="사이트 ID 리스트")
    schedule_time: Optional[datetime] = Field(default=None, description="예약 시간 (없으면 즉시 발행)")


class PublishToAllSitesRequest(BaseModel):
    """모든 활성 사이트에 발행 요청"""
    post_id: int = Field(..., description="포스트 ID")
    schedule_time: Optional[datetime] = Field(default=None, description="예약 시간 (없으면 즉시 발행)")


# API Endpoints

@router.post("/sites")
def create_wordpress_site(
    request: CreateSiteRequest,
    db: Session = Depends(get_db)
):
    """
    새 WordPress 사이트 등록

    - **name**: 사이트 이름
    - **url**: WordPress 사이트 URL (예: https://example.com)
    - **username**: WordPress 사용자명
    - **app_password**: WordPress Application Password

    Returns:
    - 생성된 사이트 정보
    """
    try:
        logger.info(f"Creating new WordPress site: {request.name}")
        service = get_multi_blog_service(db)

        site = service.create_site(
            name=request.name,
            url=request.url,
            username=request.username,
            app_password=request.app_password,
            is_active=request.is_active,
            default_category=request.default_category,
            default_tags=request.default_tags,
            auto_publish=request.auto_publish,
            publish_delay_minutes=request.publish_delay_minutes,
            description=request.description,
            language=request.language,
            timezone=request.timezone
        )

        return {
            "success": True,
            "site": {
                "id": site.id,
                "name": site.name,
                "url": site.url,
                "api_url": site.api_url,
                "is_active": site.is_active,
                "auto_publish": site.auto_publish,
                "created_at": site.created_at.isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Error creating site: {e}")
        raise HTTPException(status_code=500, detail=f"사이트 생성 실패: {str(e)}")


@router.get("/sites")
def list_wordpress_sites(
    is_active: Optional[bool] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    WordPress 사이트 목록 조회

    - **is_active**: 활성화 상태 필터 (선택)
    - **limit**: 최대 조회 개수 (기본 100)

    Returns:
    - 사이트 목록
    """
    try:
        logger.info("Listing WordPress sites")
        service = get_multi_blog_service(db)

        sites = service.list_sites(is_active=is_active, limit=limit)

        return {
            "success": True,
            "total": len(sites),
            "sites": [
                {
                    "id": site.id,
                    "name": site.name,
                    "url": site.url,
                    "is_active": site.is_active,
                    "auto_publish": site.auto_publish,
                    "total_posts_published": site.total_posts_published,
                    "last_published_at": site.last_published_at.isoformat() if site.last_published_at else None,
                    "created_at": site.created_at.isoformat()
                }
                for site in sites
            ]
        }

    except Exception as e:
        logger.error(f"Error listing sites: {e}")
        raise HTTPException(status_code=500, detail=f"사이트 목록 조회 실패: {str(e)}")


@router.get("/sites/{site_id}")
def get_wordpress_site(
    site_id: int,
    db: Session = Depends(get_db)
):
    """
    WordPress 사이트 상세 조회

    - **site_id**: 사이트 ID

    Returns:
    - 사이트 상세 정보
    """
    try:
        logger.info(f"Getting site: {site_id}")
        service = get_multi_blog_service(db)

        site = service.get_site(site_id)
        if not site:
            raise HTTPException(status_code=404, detail="사이트를 찾을 수 없습니다")

        return {
            "success": True,
            "site": {
                "id": site.id,
                "name": site.name,
                "url": site.url,
                "api_url": site.api_url,
                "username": site.username,
                "is_active": site.is_active,
                "default_category": site.default_category,
                "default_tags": site.default_tags,
                "auto_publish": site.auto_publish,
                "publish_delay_minutes": site.publish_delay_minutes,
                "total_posts_published": site.total_posts_published,
                "last_published_at": site.last_published_at.isoformat() if site.last_published_at else None,
                "description": site.description,
                "language": site.language,
                "timezone": site.timezone,
                "created_at": site.created_at.isoformat(),
                "updated_at": site.updated_at.isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting site: {e}")
        raise HTTPException(status_code=500, detail=f"사이트 조회 실패: {str(e)}")


@router.put("/sites/{site_id}")
def update_wordpress_site(
    site_id: int,
    request: UpdateSiteRequest,
    db: Session = Depends(get_db)
):
    """
    WordPress 사이트 정보 업데이트

    - **site_id**: 사이트 ID
    - 업데이트할 필드만 전송

    Returns:
    - 업데이트된 사이트 정보
    """
    try:
        logger.info(f"Updating site: {site_id}")
        service = get_multi_blog_service(db)

        # None이 아닌 필드만 업데이트
        update_data = {k: v for k, v in request.model_dump().items() if v is not None}

        site = service.update_site(site_id, **update_data)
        if not site:
            raise HTTPException(status_code=404, detail="사이트를 찾을 수 없습니다")

        return {
            "success": True,
            "site": {
                "id": site.id,
                "name": site.name,
                "url": site.url,
                "is_active": site.is_active,
                "updated_at": site.updated_at.isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating site: {e}")
        raise HTTPException(status_code=500, detail=f"사이트 업데이트 실패: {str(e)}")


@router.delete("/sites/{site_id}")
def delete_wordpress_site(
    site_id: int,
    db: Session = Depends(get_db)
):
    """
    WordPress 사이트 삭제

    - **site_id**: 사이트 ID

    Returns:
    - 삭제 성공 여부
    """
    try:
        logger.info(f"Deleting site: {site_id}")
        service = get_multi_blog_service(db)

        success = service.delete_site(site_id)
        if not success:
            raise HTTPException(status_code=404, detail="사이트를 찾을 수 없습니다")

        return {
            "success": True,
            "message": "사이트가 삭제되었습니다"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting site: {e}")
        raise HTTPException(status_code=500, detail=f"사이트 삭제 실패: {str(e)}")


@router.post("/sites/{site_id}/test-connection")
def test_wordpress_connection(
    site_id: int,
    db: Session = Depends(get_db)
):
    """
    WordPress 연결 테스트

    - **site_id**: 사이트 ID

    Returns:
    - 연결 테스트 결과
    """
    try:
        logger.info(f"Testing connection for site: {site_id}")
        service = get_multi_blog_service(db)

        result = service.test_connection(site_id)

        return result

    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        raise HTTPException(status_code=500, detail=f"연결 테스트 실패: {str(e)}")


@router.post("/publish/site")
def publish_to_site(
    request: PublishToSiteRequest,
    db: Session = Depends(get_db)
):
    """
    특정 사이트에 포스트 발행

    - **site_id**: 사이트 ID
    - **post_id**: 포스트 ID
    - **schedule_time**: 예약 시간 (선택, 없으면 즉시 발행)

    Returns:
    - 발행 결과
    """
    try:
        logger.info(f"Publishing post {request.post_id} to site {request.site_id}")
        service = get_multi_blog_service(db)

        site_post = service.publish_to_site(
            site_id=request.site_id,
            post_id=request.post_id,
            schedule_time=request.schedule_time
        )

        return {
            "success": True,
            "site_post": {
                "id": site_post.id,
                "site_id": site_post.site_id,
                "post_id": site_post.post_id,
                "status": site_post.status,
                "wp_post_id": site_post.wp_post_id,
                "wp_url": site_post.wp_url,
                "wp_status": site_post.wp_status,
                "scheduled_for": site_post.scheduled_for.isoformat() if site_post.scheduled_for else None,
                "published_at": site_post.published_at.isoformat() if site_post.published_at else None,
                "error_message": site_post.error_message
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error publishing to site: {e}")
        raise HTTPException(status_code=500, detail=f"발행 실패: {str(e)}")


@router.post("/publish/multiple")
def publish_to_multiple_sites(
    request: PublishToMultipleSitesRequest,
    db: Session = Depends(get_db)
):
    """
    여러 사이트에 동시 발행

    - **post_id**: 포스트 ID
    - **site_ids**: 사이트 ID 리스트
    - **schedule_time**: 예약 시간 (선택, 없으면 즉시 발행)

    Returns:
    - 각 사이트별 발행 결과
    """
    try:
        logger.info(f"Publishing post {request.post_id} to {len(request.site_ids)} sites")
        service = get_multi_blog_service(db)

        site_posts = service.publish_to_multiple_sites(
            post_id=request.post_id,
            site_ids=request.site_ids,
            schedule_time=request.schedule_time
        )

        return {
            "success": True,
            "total_sites": len(request.site_ids),
            "published_sites": len(site_posts),
            "site_posts": [
                {
                    "id": sp.id,
                    "site_id": sp.site_id,
                    "status": sp.status,
                    "wp_url": sp.wp_url,
                    "error_message": sp.error_message
                }
                for sp in site_posts
            ]
        }

    except Exception as e:
        logger.error(f"Error publishing to multiple sites: {e}")
        raise HTTPException(status_code=500, detail=f"다중 발행 실패: {str(e)}")


@router.post("/publish/all")
def publish_to_all_sites(
    request: PublishToAllSitesRequest,
    db: Session = Depends(get_db)
):
    """
    모든 활성 사이트에 발행

    - **post_id**: 포스트 ID
    - **schedule_time**: 예약 시간 (선택, 없으면 즉시 발행)

    Returns:
    - 각 사이트별 발행 결과
    """
    try:
        logger.info(f"Publishing post {request.post_id} to all active sites")
        service = get_multi_blog_service(db)

        site_posts = service.publish_to_all_active_sites(
            post_id=request.post_id,
            schedule_time=request.schedule_time
        )

        return {
            "success": True,
            "total_sites": len(site_posts),
            "site_posts": [
                {
                    "id": sp.id,
                    "site_id": sp.site_id,
                    "status": sp.status,
                    "wp_url": sp.wp_url,
                    "error_message": sp.error_message
                }
                for sp in site_posts
            ]
        }

    except Exception as e:
        logger.error(f"Error publishing to all sites: {e}")
        raise HTTPException(status_code=500, detail=f"전체 사이트 발행 실패: {str(e)}")


@router.get("/site-posts")
def get_site_posts(
    site_id: Optional[int] = None,
    post_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    사이트별 포스트 목록 조회

    - **site_id**: 사이트 ID 필터 (선택)
    - **post_id**: 포스트 ID 필터 (선택)
    - **status**: 상태 필터 (pending/published/failed) (선택)
    - **limit**: 최대 조회 개수 (기본 100)

    Returns:
    - 사이트 포스트 목록
    """
    try:
        logger.info("Getting site posts")
        service = get_multi_blog_service(db)

        site_posts = service.get_site_posts(
            site_id=site_id,
            post_id=post_id,
            status=status,
            limit=limit
        )

        return {
            "success": True,
            "total": len(site_posts),
            "site_posts": [
                {
                    "id": sp.id,
                    "site_id": sp.site_id,
                    "post_id": sp.post_id,
                    "wp_post_id": sp.wp_post_id,
                    "wp_url": sp.wp_url,
                    "wp_status": sp.wp_status,
                    "status": sp.status,
                    "scheduled_for": sp.scheduled_for.isoformat() if sp.scheduled_for else None,
                    "published_at": sp.published_at.isoformat() if sp.published_at else None,
                    "views": sp.views,
                    "clicks": sp.clicks,
                    "conversions": sp.conversions,
                    "error_message": sp.error_message,
                    "retry_count": sp.retry_count
                }
                for sp in site_posts
            ]
        }

    except Exception as e:
        logger.error(f"Error getting site posts: {e}")
        raise HTTPException(status_code=500, detail=f"사이트 포스트 조회 실패: {str(e)}")


@router.get("/stats/{site_id}")
def get_site_statistics(
    site_id: int,
    db: Session = Depends(get_db)
):
    """
    사이트 통계 조회

    - **site_id**: 사이트 ID

    Returns:
    - 사이트 통계 정보
    """
    try:
        logger.info(f"Getting statistics for site: {site_id}")
        service = get_multi_blog_service(db)

        stats = service.get_site_statistics(site_id)

        if "error" in stats:
            raise HTTPException(status_code=404, detail=stats["error"])

        return {
            "success": True,
            "statistics": stats
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting site statistics: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.get("/stats")
def get_all_sites_statistics(
    db: Session = Depends(get_db)
):
    """
    전체 사이트 통계 조회

    Returns:
    - 모든 사이트의 통계 정보
    """
    try:
        logger.info("Getting statistics for all sites")
        service = get_multi_blog_service(db)

        stats = service.get_all_sites_statistics()

        return {
            "success": True,
            "total_sites": len(stats),
            "statistics": stats
        }

    except Exception as e:
        logger.error(f"Error getting all sites statistics: {e}")
        raise HTTPException(status_code=500, detail=f"전체 통계 조회 실패: {str(e)}")


@router.get("/best-practices")
def get_multi_blog_best_practices():
    """
    멀티 블로그 관리 모범 사례

    Returns:
    - 설정 권장 사항
    - 발행 전략
    - 성능 최적화 팁
    """
    return {
        "setup_recommendations": {
            "wordpress_configuration": [
                "WordPress Application Password 사용 (보안)",
                "REST API 활성화 확인",
                "적절한 사용자 권한 설정 (Editor 이상)",
                "SSL 인증서 설치 (HTTPS)"
            ],
            "multi_site_strategy": [
                "3-5개의 관련 사이트로 시작",
                "각 사이트별 명확한 타겟 오디언스 설정",
                "사이트별 컨텐츠 차별화 전략 수립",
                "사이트별 성과 지표 추적"
            ],
            "content_distribution": [
                "같은 콘텐츠라도 사이트별 커스터마이징 필요",
                "사이트별 카테고리/태그 최적화",
                "발행 시간 분산 (검색엔진 중복 방지)",
                "각 사이트의 톤앤매너 유지"
            ]
        },
        "publishing_strategies": {
            "immediate_publishing": {
                "use_case": "시간에 민감한 뉴스, 트렌드 주제",
                "pros": "빠른 배포, 실시간 대응",
                "cons": "수동 관리 필요, 품질 검증 시간 부족"
            },
            "scheduled_publishing": {
                "use_case": "정기 콘텐츠, 계획된 캠페인",
                "pros": "일정 관리, 시간대 최적화, 일관성",
                "cons": "유연성 감소"
            },
            "batch_publishing": {
                "use_case": "여러 사이트 동시 런칭",
                "pros": "효율적, 일관된 타이밍",
                "cons": "개별 사이트 최적화 어려움"
            }
        },
        "performance_optimization": [
            {
                "tip": "발행 전 연결 테스트",
                "description": "각 사이트의 API 연결 상태를 주기적으로 확인",
                "benefit": "발행 실패 사전 예방"
            },
            {
                "tip": "재시도 로직 활용",
                "description": "네트워크 오류 시 자동 재시도 (최대 3회)",
                "benefit": "일시적 오류로 인한 실패 방지"
            },
            {
                "tip": "비활성 사이트 제외",
                "description": "유지보수 중이거나 문제 있는 사이트는 비활성화",
                "benefit": "발행 속도 향상, 에러 감소"
            },
            {
                "tip": "통계 기반 최적화",
                "description": "사이트별 성과 데이터로 발행 우선순위 결정",
                "benefit": "ROI 극대화"
            }
        ],
        "security_best_practices": [
            "Application Password를 일반 비밀번호와 분리 관리",
            "API 요청에 항상 HTTPS 사용",
            "사이트 인증 정보를 환경 변수로 관리",
            "정기적으로 Application Password 갱신",
            "사이트별 권한을 최소화 (필요한 권한만)"
        ],
        "monitoring_checklist": [
            "✓ 각 사이트의 발행 성공률 추적",
            "✓ 오류 로그 정기 검토",
            "✓ 사이트별 트래픽 및 전환율 모니터링",
            "✓ WordPress 버전 및 플러그인 호환성 확인",
            "✓ API 응답 시간 모니터링"
        ],
        "common_issues": [
            {
                "issue": "인증 실패 (401 Unauthorized)",
                "solution": "Application Password 재생성, 사용자 권한 확인"
            },
            {
                "issue": "타임아웃 오류",
                "solution": "WordPress 서버 성능 확인, timeout 설정 증가"
            },
            {
                "issue": "중복 콘텐츠 패널티",
                "solution": "사이트별 콘텐츠 커스터마이징, 발행 시간 분산"
            },
            {
                "issue": "카테고리/태그 불일치",
                "solution": "각 사이트의 taxonomy 사전 생성, 매핑 테이블 활용"
            }
        ]
    }
