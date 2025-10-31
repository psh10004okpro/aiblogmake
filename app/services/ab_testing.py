"""
A/B 테스팅 자동화 서비스
제목, 썸네일, CTA 등을 A/B 테스트하여 최적화
"""
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import random
import hashlib

from app.core.config import settings
from app.services.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


@dataclass
class TestVariant:
    """A/B 테스트 변형"""
    id: str
    label: str  # A, B, C, etc.
    content: str
    description: str
    created_at: str


@dataclass
class TitleVariants:
    """제목 A/B 테스트 변형들"""
    original: str
    variants: List[TestVariant]
    test_type: str = "title"
    recommendations: List[str] = None


@dataclass
class CTAVariants:
    """CTA A/B 테스트 변형들"""
    original: str
    variants: List[TestVariant]
    test_type: str = "cta"
    placement: str  # beginning, middle, end, sidebar, popup
    recommendations: List[str] = None


@dataclass
class ThumbnailVariants:
    """썸네일 A/B 테스트 변형들"""
    original_description: str
    variants: List[TestVariant]
    test_type: str = "thumbnail"
    design_specs: Dict[str, Any] = None


@dataclass
class ABTestReport:
    """A/B 테스트 리포트"""
    test_id: str
    test_type: str
    variants: List[Dict[str, Any]]
    winner: Optional[str]
    confidence_level: str
    improvement_percentage: float
    sample_size: int
    duration_days: int
    insights: List[str]
    recommendations: List[str]


class ABTestingService:
    """A/B 테스팅 자동화 서비스"""

    def __init__(self):
        self.llm_service = None

    async def _get_llm_service(self):
        """LLM 서비스 인스턴스 가져오기"""
        if self.llm_service is None:
            self.llm_service = LLMFactory.create(settings.default_llm_provider)
        return self.llm_service

    def _generate_variant_id(self, content: str) -> str:
        """변형 ID 생성"""
        return hashlib.md5(content.encode()).hexdigest()[:8]

    async def generate_title_variants(
        self,
        original_title: str,
        keywords: List[str],
        content_summary: str,
        num_variants: int = 3
    ) -> TitleVariants:
        """제목 A/B 테스트 변형 생성"""
        logger.info(f"Generating {num_variants} title variants for: {original_title}")

        prompt = f"""다음 블로그 포스트 제목의 A/B 테스트용 변형을 {num_variants}개 생성해주세요.

원본 제목: {original_title}
키워드: {', '.join(keywords)}
콘텐츠 요약: {content_summary[:200]}

각 변형은 다른 접근 방식을 사용해야 합니다:
1. 숫자 사용형 (예: "10가지 방법", "5분 만에")
2. 질문형 (예: "어떻게 ~할까?", "왜 ~인가?")
3. 감성형 (예: "놀라운", "완벽한", "최고의")
4. 호기심 유발형 (예: "아무도 모르는", "숨겨진 비밀")
5. 혜택 강조형 (예: "~하여 성공하는 법", "~로 돈 버는 법")

다음 형식으로 작성해주세요:

변형 1: [제목]
설명: [이 제목이 왜 효과적인지]

변형 2: [제목]
설명: [이 제목이 왜 효과적인지]

변형 3: [제목]
설명: [이 제목이 왜 효과적인지]

각 제목은 SEO를 고려하여 50-60자 이내로 작성하고, 핵심 키워드를 포함해야 합니다."""

        llm_service = await self._get_llm_service()
        response = await llm_service.generate_text(prompt, max_tokens=1000)

        # 응답 파싱
        variants = []
        lines = response.strip().split('\n')

        current_variant = None
        current_description = ""

        for line in lines:
            line = line.strip()

            if line.startswith('변형') and ':' in line:
                # 이전 변형 저장
                if current_variant:
                    variant_id = self._generate_variant_id(current_variant)
                    label = chr(65 + len(variants))  # A, B, C, ...
                    variants.append(TestVariant(
                        id=variant_id,
                        label=label,
                        content=current_variant,
                        description=current_description.strip(),
                        created_at=datetime.utcnow().isoformat()
                    ))

                # 새 변형 시작
                current_variant = line.split(':', 1)[1].strip()
                current_description = ""

            elif line.startswith('설명:'):
                current_description = line.split(':', 1)[1].strip()

        # 마지막 변형 저장
        if current_variant:
            variant_id = self._generate_variant_id(current_variant)
            label = chr(65 + len(variants))
            variants.append(TestVariant(
                id=variant_id,
                label=label,
                content=current_variant,
                description=current_description.strip(),
                created_at=datetime.utcnow().isoformat()
            ))

        # 충분한 변형이 없으면 간단한 변형 추가
        while len(variants) < num_variants:
            simple_variant = f"{original_title} - 변형 {len(variants) + 1}"
            variant_id = self._generate_variant_id(simple_variant)
            label = chr(65 + len(variants))
            variants.append(TestVariant(
                id=variant_id,
                label=label,
                content=simple_variant,
                description="AI 생성 변형",
                created_at=datetime.utcnow().isoformat()
            ))

        # 추천 사항
        recommendations = [
            "각 변형을 최소 100회 이상 노출시켜 통계적 유의성 확보",
            "클릭률(CTR)을 주요 지표로 사용",
            "테스트 기간은 최소 7일 권장",
            "모바일과 데스크톱 성과를 분리하여 분석"
        ]

        logger.info(f"Generated {len(variants)} title variants")

        return TitleVariants(
            original=original_title,
            variants=variants,
            recommendations=recommendations
        )

    async def generate_cta_variants(
        self,
        original_cta: str,
        goal: str,
        placement: str = "end",
        num_variants: int = 3
    ) -> CTAVariants:
        """CTA A/B 테스트 변형 생성"""
        logger.info(f"Generating {num_variants} CTA variants for placement: {placement}")

        prompt = f"""다음 CTA(Call-to-Action)의 A/B 테스트용 변형을 {num_variants}개 생성해주세요.

원본 CTA: {original_cta}
목표: {goal}
배치 위치: {placement}

각 변형은 다른 심리적 전략을 사용해야 합니다:
1. 긴급성 강조 (예: "지금 바로", "오늘만")
2. 혜택 강조 (예: "무료로", "간단하게")
3. 호기심 유발 (예: "확인하기", "알아보기")
4. 사회적 증거 (예: "1만명이 선택한", "인기 있는")
5. 간단함 강조 (예: "클릭 한 번으로", "5초 만에")

다음 형식으로 작성해주세요:

변형 1: [CTA 문구]
설명: [이 CTA가 왜 효과적인지]

변형 2: [CTA 문구]
설명: [이 CTA가 왜 효과적인지]

변형 3: [CTA 문구]
설명: [이 CTA가 왜 효과적인지]

각 CTA는 간결하게 10-15자 이내로 작성하고, 동사로 시작해야 합니다."""

        llm_service = await self._get_llm_service()
        response = await llm_service.generate_text(prompt, max_tokens=800)

        # 응답 파싱 (제목 변형과 동일한 로직)
        variants = []
        lines = response.strip().split('\n')

        current_variant = None
        current_description = ""

        for line in lines:
            line = line.strip()

            if line.startswith('변형') and ':' in line:
                if current_variant:
                    variant_id = self._generate_variant_id(current_variant)
                    label = chr(65 + len(variants))
                    variants.append(TestVariant(
                        id=variant_id,
                        label=label,
                        content=current_variant,
                        description=current_description.strip(),
                        created_at=datetime.utcnow().isoformat()
                    ))

                current_variant = line.split(':', 1)[1].strip()
                current_description = ""

            elif line.startswith('설명:'):
                current_description = line.split(':', 1)[1].strip()

        if current_variant:
            variant_id = self._generate_variant_id(current_variant)
            label = chr(65 + len(variants))
            variants.append(TestVariant(
                id=variant_id,
                label=label,
                content=current_variant,
                description=current_description.strip(),
                created_at=datetime.utcnow().isoformat()
            ))

        while len(variants) < num_variants:
            simple_variant = f"{original_cta} (변형 {len(variants) + 1})"
            variant_id = self._generate_variant_id(simple_variant)
            label = chr(65 + len(variants))
            variants.append(TestVariant(
                id=variant_id,
                label=label,
                content=simple_variant,
                description="AI 생성 변형",
                created_at=datetime.utcnow().isoformat()
            ))

        recommendations = [
            "클릭률(CTR)을 주요 지표로 측정",
            "배치 위치별로 별도로 테스트",
            "버튼 색상과 크기도 함께 테스트 고려",
            "전환율까지 추적하여 최종 성과 확인"
        ]

        logger.info(f"Generated {len(variants)} CTA variants")

        return CTAVariants(
            original=original_cta,
            variants=variants,
            placement=placement,
            recommendations=recommendations
        )

    async def generate_thumbnail_variants(
        self,
        post_title: str,
        keywords: List[str],
        content_summary: str,
        num_variants: int = 3
    ) -> ThumbnailVariants:
        """썸네일 A/B 테스트 변형 생성 (디자인 설명)"""
        logger.info(f"Generating {num_variants} thumbnail design variants")

        prompt = f"""다음 블로그 포스트의 썸네일 디자인 A/B 테스트용 변형을 {num_variants}개 생성해주세요.

포스트 제목: {post_title}
키워드: {', '.join(keywords)}
내용 요약: {content_summary[:200]}

각 변형은 다른 디자인 전략을 사용해야 합니다:
1. 최소주의 (Minimalist) - 깔끔하고 단순한 디자인
2. 대담한 텍스트 (Bold Text) - 큰 글씨와 강한 대비
3. 이미지 중심 (Image-Focused) - 시각적 요소 강조
4. 인포그래픽 스타일 (Infographic) - 아이콘과 통계
5. 감성적 (Emotional) - 사람 얼굴이나 감정 표현

다음 형식으로 작성해주세요:

변형 1:
- 스타일: [디자인 스타일]
- 메인 텍스트: [썸네일에 들어갈 텍스트]
- 색상: [추천 색상 조합]
- 이미지/아이콘: [사용할 시각 요소]
- 레이아웃: [요소 배치 방법]

변형 2:
[동일한 형식]

변형 3:
[동일한 형식]

각 디자인은 1280x720 픽셀(16:9 비율)을 기준으로 하고, 모바일에서도 잘 보여야 합니다."""

        llm_service = await self._get_llm_service()
        response = await llm_service.generate_text(prompt, max_tokens=1200)

        # 응답 파싱
        variants = []
        variant_blocks = response.split('변형')[1:]  # 첫 번째는 빈 문자열

        for i, block in enumerate(variant_blocks):
            if not block.strip():
                continue

            lines = block.strip().split('\n')

            # 각 필드 추출
            variant_data = {}
            for line in lines:
                if ':' in line:
                    key = line.split(':')[0].strip().replace('-', '').strip()
                    value = line.split(':', 1)[1].strip()
                    variant_data[key] = value

            # 설명 문자열 생성
            description = f"""스타일: {variant_data.get('스타일', 'N/A')}
메인 텍스트: {variant_data.get('메인 텍스트', 'N/A')}
색상: {variant_data.get('색상', 'N/A')}
이미지/아이콘: {variant_data.get('이미지/아이콘', variant_data.get('이미지', 'N/A'))}
레이아웃: {variant_data.get('레이아웃', 'N/A')}"""

            variant_id = self._generate_variant_id(description)
            label = chr(65 + len(variants))

            variants.append(TestVariant(
                id=variant_id,
                label=label,
                content=description,
                description=f"{variant_data.get('스타일', '')} 스타일의 썸네일",
                created_at=datetime.utcnow().isoformat()
            ))

        # 충분한 변형이 없으면 기본 변형 추가
        while len(variants) < num_variants:
            simple_desc = f"기본 썸네일 디자인 {len(variants) + 1}"
            variant_id = self._generate_variant_id(simple_desc)
            label = chr(65 + len(variants))
            variants.append(TestVariant(
                id=variant_id,
                label=label,
                content=simple_desc,
                description="AI 생성 기본 디자인",
                created_at=datetime.utcnow().isoformat()
            ))

        design_specs = {
            "dimensions": "1280x720",
            "aspect_ratio": "16:9",
            "file_format": "JPG or PNG",
            "max_file_size": "200KB",
            "text_readability": "Mobile-optimized (legible at small sizes)"
        }

        logger.info(f"Generated {len(variants)} thumbnail design variants")

        return ThumbnailVariants(
            original_description=f"Original design for: {post_title}",
            variants=variants,
            design_specs=design_specs
        )

    def calculate_winner(
        self,
        variant_results: List[Dict[str, Any]],
        metric: str = "ctr"
    ) -> ABTestReport:
        """A/B 테스트 결과 분석 및 승자 선정"""
        logger.info("Calculating A/B test winner")

        # 시뮬레이션 데이터 (실제로는 Google Analytics 등에서 가져옴)
        test_id = self._generate_variant_id(str(datetime.utcnow()))

        # 가장 높은 성과를 낸 변형 찾기
        winner_data = max(variant_results, key=lambda x: x.get(metric, 0))
        winner_label = winner_data.get('label', 'A')

        # 개선율 계산
        baseline = variant_results[0].get(metric, 0)  # A를 기준으로
        winner_value = winner_data.get(metric, 0)

        if baseline > 0:
            improvement = ((winner_value - baseline) / baseline) * 100
        else:
            improvement = 0.0

        # 신뢰도 계산 (간단한 버전)
        total_samples = sum(v.get('impressions', 0) for v in variant_results)

        if total_samples >= 1000:
            confidence = "High"
        elif total_samples >= 500:
            confidence = "Medium"
        else:
            confidence = "Low"

        # 인사이트 생성
        insights = []

        if improvement > 20:
            insights.append(f"승자 변형은 기준 대비 {improvement:.1f}% 높은 성과를 보였습니다.")
        elif improvement > 10:
            insights.append(f"승자 변형은 기준 대비 {improvement:.1f}% 개선되었습니다.")
        else:
            insights.append("변형 간 성과 차이가 크지 않습니다.")

        if total_samples < 500:
            insights.append("표본 크기가 작아 결과의 신뢰도가 낮을 수 있습니다.")

        # 권장 사항
        recommendations = [
            f"변형 {winner_label}을 기본으로 채택하는 것을 권장합니다.",
            "승자 변형을 기반으로 추가 최적화를 진행하세요.",
            "정기적으로 새로운 A/B 테스트를 실행하여 지속적으로 개선하세요."
        ]

        if confidence != "High":
            recommendations.append("더 많은 샘플 데이터를 수집하여 신뢰도를 높이세요.")

        report = ABTestReport(
            test_id=test_id,
            test_type=variant_results[0].get('test_type', 'unknown'),
            variants=[
                {
                    "label": v.get('label'),
                    "impressions": v.get('impressions', 0),
                    "clicks": v.get('clicks', 0),
                    "ctr": v.get('ctr', 0),
                    "conversions": v.get('conversions', 0)
                }
                for v in variant_results
            ],
            winner=winner_label,
            confidence_level=confidence,
            improvement_percentage=round(improvement, 2),
            sample_size=total_samples,
            duration_days=variant_results[0].get('duration_days', 7),
            insights=insights,
            recommendations=recommendations
        )

        logger.info(f"Winner: Variant {winner_label} with {improvement:.2f}% improvement")

        return report

    async def suggest_test_strategy(
        self,
        content_type: str,
        target_metric: str,
        current_performance: Dict[str, float]
    ) -> Dict[str, Any]:
        """A/B 테스트 전략 추천"""
        logger.info(f"Suggesting test strategy for {content_type}")

        prompt = f"""다음 콘텐츠 타입에 대한 A/B 테스트 전략을 추천해주세요.

콘텐츠 타입: {content_type}
목표 지표: {target_metric}
현재 성과:
- 클릭률: {current_performance.get('ctr', 0)}%
- 전환율: {current_performance.get('conversion_rate', 0)}%
- 평균 체류 시간: {current_performance.get('avg_time', 0)}초

다음 내용을 포함하여 전략을 작성해주세요:

1. 우선순위 테스트 항목 (3가지):
   - [항목 1]
   - [항목 2]
   - [항목 3]

2. 각 테스트의 예상 효과:
   - [항목 1]: [예상 개선율]
   - [항목 2]: [예상 개선율]
   - [항목 3]: [예상 개선율]

3. 테스트 순서 및 기간:
   - [항목 1]: [기간]
   - [항목 2]: [기간]
   - [항목 3]: [기간]

4. 주의사항 및 팁:
   - [팁 1]
   - [팁 2]

현실적이고 실행 가능한 전략을 제시해주세요."""

        llm_service = await self._get_llm_service()
        response = await llm_service.generate_text(prompt, max_tokens=1000)

        return {
            "content_type": content_type,
            "target_metric": target_metric,
            "current_performance": current_performance,
            "strategy": response,
            "generated_at": datetime.utcnow().isoformat()
        }


# 싱글톤 인스턴스
_service_instance = None

def get_ab_testing_service() -> ABTestingService:
    """A/B 테스팅 서비스 싱글톤 인스턴스 반환"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ABTestingService()
    return _service_instance
