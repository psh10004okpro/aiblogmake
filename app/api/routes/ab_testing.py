"""
A/B 테스팅 API 라우트
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from app.services.ab_testing import (
    get_ab_testing_service,
    TitleVariants,
    CTAVariants,
    ThumbnailVariants,
    ABTestReport,
    TestVariant
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ab-testing", tags=["ab-testing"])

# Request Models

class GenerateTitleVariantsRequest(BaseModel):
    """제목 변형 생성 요청"""
    original_title: str = Field(..., description="원본 제목")
    keywords: List[str] = Field(default_factory=list, description="키워드 리스트")
    content_summary: str = Field(..., description="콘텐츠 요약")
    num_variants: int = Field(default=3, ge=2, le=5, description="생성할 변형 개수")


class GenerateCTAVariantsRequest(BaseModel):
    """CTA 변형 생성 요청"""
    original_cta: str = Field(..., description="원본 CTA")
    goal: str = Field(..., description="목표 (예: 구독, 다운로드, 문의)")
    placement: str = Field(default="end", description="배치 위치")
    num_variants: int = Field(default=3, ge=2, le=5, description="생성할 변형 개수")


class GenerateThumbnailVariantsRequest(BaseModel):
    """썸네일 변형 생성 요청"""
    post_title: str = Field(..., description="포스트 제목")
    keywords: List[str] = Field(default_factory=list, description="키워드")
    content_summary: str = Field(..., description="콘텐츠 요약")
    num_variants: int = Field(default=3, ge=2, le=5, description="생성할 변형 개수")


class CalculateWinnerRequest(BaseModel):
    """승자 계산 요청"""
    variant_results: List[Dict[str, Any]] = Field(..., description="변형별 결과 데이터")
    metric: str = Field(default="ctr", description="주요 지표 (ctr, conversion_rate, etc.)")


class SuggestStrategyRequest(BaseModel):
    """전략 추천 요청"""
    content_type: str = Field(..., description="콘텐츠 타입")
    target_metric: str = Field(..., description="목표 지표")
    current_performance: Dict[str, float] = Field(..., description="현재 성과 데이터")


# API Endpoints

@router.post("/title-variants")
async def generate_title_variants(request: GenerateTitleVariantsRequest):
    """
    제목 A/B 테스트 변형 생성

    - **original_title**: 원본 제목
    - **keywords**: 키워드 리스트
    - **content_summary**: 콘텐츠 요약
    - **num_variants**: 생성할 변형 개수 (2-5)

    Returns:
    - 원본 제목과 여러 변형들
    - 각 변형의 설명과 권장 사항
    """
    try:
        logger.info(f"Generating title variants for: {request.original_title}")
        service = get_ab_testing_service()

        result = await service.generate_title_variants(
            original_title=request.original_title,
            keywords=request.keywords,
            content_summary=request.content_summary,
            num_variants=request.num_variants
        )

        return {
            "original": result.original,
            "variants": [
                {
                    "id": v.id,
                    "label": v.label,
                    "content": v.content,
                    "description": v.description,
                    "created_at": v.created_at
                }
                for v in result.variants
            ],
            "test_type": result.test_type,
            "recommendations": result.recommendations
        }

    except Exception as e:
        logger.error(f"Error generating title variants: {e}")
        raise HTTPException(status_code=500, detail=f"제목 변형 생성 실패: {str(e)}")


@router.post("/cta-variants")
async def generate_cta_variants(request: GenerateCTAVariantsRequest):
    """
    CTA A/B 테스트 변형 생성

    - **original_cta**: 원본 CTA 문구
    - **goal**: 목표 (구독, 다운로드 등)
    - **placement**: 배치 위치
    - **num_variants**: 생성할 변형 개수

    Returns:
    - CTA 변형들과 배치 권장 사항
    """
    try:
        logger.info(f"Generating CTA variants for goal: {request.goal}")
        service = get_ab_testing_service()

        result = await service.generate_cta_variants(
            original_cta=request.original_cta,
            goal=request.goal,
            placement=request.placement,
            num_variants=request.num_variants
        )

        return {
            "original": result.original,
            "variants": [
                {
                    "id": v.id,
                    "label": v.label,
                    "content": v.content,
                    "description": v.description,
                    "created_at": v.created_at
                }
                for v in result.variants
            ],
            "test_type": result.test_type,
            "placement": result.placement,
            "recommendations": result.recommendations
        }

    except Exception as e:
        logger.error(f"Error generating CTA variants: {e}")
        raise HTTPException(status_code=500, detail=f"CTA 변형 생성 실패: {str(e)}")


@router.post("/thumbnail-variants")
async def generate_thumbnail_variants(request: GenerateThumbnailVariantsRequest):
    """
    썸네일 A/B 테스트 변형 생성 (디자인 설명)

    - **post_title**: 포스트 제목
    - **keywords**: 키워드
    - **content_summary**: 콘텐츠 요약
    - **num_variants**: 생성할 변형 개수

    Returns:
    - 썸네일 디자인 변형들
    - 디자인 사양 및 권장 사항
    """
    try:
        logger.info(f"Generating thumbnail variants for: {request.post_title}")
        service = get_ab_testing_service()

        result = await service.generate_thumbnail_variants(
            post_title=request.post_title,
            keywords=request.keywords,
            content_summary=request.content_summary,
            num_variants=request.num_variants
        )

        return {
            "original_description": result.original_description,
            "variants": [
                {
                    "id": v.id,
                    "label": v.label,
                    "content": v.content,
                    "description": v.description,
                    "created_at": v.created_at
                }
                for v in result.variants
            ],
            "test_type": result.test_type,
            "design_specs": result.design_specs
        }

    except Exception as e:
        logger.error(f"Error generating thumbnail variants: {e}")
        raise HTTPException(status_code=500, detail=f"썸네일 변형 생성 실패: {str(e)}")


@router.post("/calculate-winner")
async def calculate_winner(request: CalculateWinnerRequest):
    """
    A/B 테스트 결과 분석 및 승자 선정

    - **variant_results**: 각 변형의 성과 데이터
      - label: 변형 라벨 (A, B, C)
      - impressions: 노출 수
      - clicks: 클릭 수
      - ctr: 클릭률 (%)
      - conversions: 전환 수
      - test_type: 테스트 타입
      - duration_days: 테스트 기간
    - **metric**: 주요 지표 (ctr, conversion_rate)

    Returns:
    - 승자 변형
    - 신뢰도 수준
    - 개선율
    - 인사이트 및 권장 사항
    """
    try:
        logger.info("Calculating A/B test winner")
        service = get_ab_testing_service()

        result = service.calculate_winner(
            variant_results=request.variant_results,
            metric=request.metric
        )

        return {
            "test_id": result.test_id,
            "test_type": result.test_type,
            "variants": result.variants,
            "winner": result.winner,
            "confidence_level": result.confidence_level,
            "improvement_percentage": result.improvement_percentage,
            "sample_size": result.sample_size,
            "duration_days": result.duration_days,
            "insights": result.insights,
            "recommendations": result.recommendations
        }

    except Exception as e:
        logger.error(f"Error calculating winner: {e}")
        raise HTTPException(status_code=500, detail=f"승자 계산 실패: {str(e)}")


@router.post("/suggest-strategy")
async def suggest_test_strategy(request: SuggestStrategyRequest):
    """
    A/B 테스트 전략 추천

    - **content_type**: 콘텐츠 타입 (blog, landing_page, email 등)
    - **target_metric**: 목표 지표
    - **current_performance**: 현재 성과 데이터

    Returns:
    - 맞춤형 A/B 테스트 전략
    - 우선순위 테스트 항목
    - 예상 효과 및 주의사항
    """
    try:
        logger.info(f"Suggesting test strategy for: {request.content_type}")
        service = get_ab_testing_service()

        result = await service.suggest_test_strategy(
            content_type=request.content_type,
            target_metric=request.target_metric,
            current_performance=request.current_performance
        )

        return result

    except Exception as e:
        logger.error(f"Error suggesting strategy: {e}")
        raise HTTPException(status_code=500, detail=f"전략 추천 실패: {str(e)}")


@router.get("/best-practices")
async def get_best_practices():
    """
    A/B 테스팅 모범 사례

    Returns:
    - A/B 테스팅 가이드라인
    - 통계적 유의성 기준
    - 권장 테스트 기간
    """
    return {
        "guidelines": {
            "minimum_sample_size": 100,
            "recommended_sample_size": 1000,
            "minimum_duration_days": 7,
            "confidence_threshold": 95,
            "statistical_power": 80
        },
        "test_types": [
            {
                "type": "title",
                "description": "제목 A/B 테스트",
                "primary_metric": "CTR (클릭률)",
                "recommended_variants": 3,
                "expected_improvement": "10-30%"
            },
            {
                "type": "cta",
                "description": "CTA 버튼 테스트",
                "primary_metric": "Conversion Rate",
                "recommended_variants": 3,
                "expected_improvement": "5-20%"
            },
            {
                "type": "thumbnail",
                "description": "썸네일 이미지 테스트",
                "primary_metric": "CTR",
                "recommended_variants": 2,
                "expected_improvement": "15-40%"
            }
        ],
        "common_mistakes": [
            "샘플 크기가 너무 작음 (< 100)",
            "테스트 기간이 너무 짧음 (< 7일)",
            "여러 요소를 동시에 변경 (멀티변량 테스트 필요)",
            "통계적 유의성 확인 없이 승자 선정",
            "모바일/데스크톱 분리 분석하지 않음"
        ],
        "best_practices": [
            "한 번에 하나의 요소만 테스트",
            "충분한 샘플 크기 확보 (최소 100회 이상)",
            "최소 1주일 이상 테스트 실행",
            "통계적 유의성 95% 이상 확보",
            "모바일/데스크톱 별도 분석",
            "시즌성 고려 (요일, 월별 차이)",
            "승자 변형을 기반으로 지속적 개선"
        ]
    }


@router.get("/metrics")
async def get_metrics_guide():
    """
    A/B 테스팅 지표 가이드

    Returns:
    - 주요 지표 설명
    - 계산 방법
    - 권장 사용 시나리오
    """
    return {
        "metrics": [
            {
                "name": "CTR (Click-Through Rate)",
                "description": "클릭률 - 노출 대비 클릭 비율",
                "formula": "(클릭 수 / 노출 수) × 100",
                "good_value": "> 2%",
                "use_case": "제목, 썸네일 테스트"
            },
            {
                "name": "Conversion Rate",
                "description": "전환율 - 방문 대비 전환 비율",
                "formula": "(전환 수 / 방문 수) × 100",
                "good_value": "> 3%",
                "use_case": "CTA, 랜딩 페이지 테스트"
            },
            {
                "name": "Bounce Rate",
                "description": "이탈률 - 한 페이지만 보고 나간 비율",
                "formula": "(단일 페이지 세션 / 전체 세션) × 100",
                "good_value": "< 50%",
                "use_case": "콘텐츠 품질, 로딩 속도 테스트"
            },
            {
                "name": "Average Time on Page",
                "description": "평균 체류 시간",
                "formula": "전체 체류 시간 / 방문 수",
                "good_value": "> 2분",
                "use_case": "콘텐츠 참여도 테스트"
            },
            {
                "name": "Pages per Session",
                "description": "세션당 페이지 뷰",
                "formula": "전체 페이지 뷰 / 전체 세션",
                "good_value": "> 2",
                "use_case": "내부 링크, 관련 콘텐츠 테스트"
            }
        ],
        "recommended_combinations": [
            {
                "test_type": "title",
                "primary_metric": "CTR",
                "secondary_metrics": ["Average Time on Page", "Bounce Rate"]
            },
            {
                "test_type": "cta",
                "primary_metric": "Conversion Rate",
                "secondary_metrics": ["CTR", "Pages per Session"]
            },
            {
                "test_type": "thumbnail",
                "primary_metric": "CTR",
                "secondary_metrics": ["Average Time on Page"]
            }
        ]
    }
