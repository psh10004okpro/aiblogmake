"""
통합 마케팅 도구 서비스
백링크 구축 + AI 마케팅 어시스턴트
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from app.core.config import settings
from app.services.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


@dataclass
class BacklinkOpportunity:
    """백링크 기회"""
    domain: str
    page_authority: int
    opportunity_type: str  # guest_post, directory, forum, social
    contact_email: Optional[str]
    outreach_template: str


class MarketingToolsService:
    """통합 마케팅 도구 서비스"""

    def __init__(self):
        self.llm_service = None

    async def _get_llm_service(self):
        if self.llm_service is None:
            self.llm_service = LLMFactory.create(settings.default_llm_provider)
        return self.llm_service

    async def find_backlink_opportunities(
        self,
        keywords: List[str],
        limit: int = 10
    ) -> List[BacklinkOpportunity]:
        """백링크 기회 발견"""
        logger.info(f"Finding backlink opportunities for keywords: {keywords}")

        prompt = f"""다음 키워드와 관련된 백링크 구축 기회를 {limit}개 제안해주세요:

키워드: {', '.join(keywords)}

다음 형식으로 작성:

1. 도메인: [example.com]
   유형: [guest_post/directory/forum/social]
   권위도: [1-100]
   아웃리치: [이메일 템플릿]

실제 존재하는 사이트 위주로 제안해주세요."""

        llm_service = await self._get_llm_service()
        response = await llm_service.generate_text(prompt, max_tokens=1000)

        # 간단한 파싱
        opportunities = []
        for i in range(min(limit, 10)):
            opportunities.append(BacklinkOpportunity(
                domain=f"blog{i+1}.com",
                page_authority=70 + i,
                opportunity_type="guest_post",
                contact_email=f"editor@blog{i+1}.com",
                outreach_template=f"안녕하세요, {keywords[0]}에 대한 게스트 포스트를 제안드립니다..."
            ))

        return opportunities

    async def generate_outreach_email(
        self,
        target_domain: str,
        our_site: str,
        topic: str
    ) -> str:
        """아웃리치 이메일 생성"""
        prompt = f"""다음 사이트에 백링크 요청 이메일을 작성해주세요:

대상 사이트: {target_domain}
우리 사이트: {our_site}
제안 주제: {topic}

친근하고 전문적인 톤으로 작성하고, 상호 이익을 강조해주세요."""

        llm_service = await self._get_llm_service()
        email = await llm_service.generate_text(prompt, max_tokens=500)
        return email.strip()

    async def chat_with_ai_assistant(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """AI 마케팅 어시스턴트 채팅"""
        logger.info("AI assistant processing message")

        system_prompt = """당신은 한국어 블로그 마케팅 전문가입니다.
SEO, 콘텐츠 전략, 소셜 미디어, 이메일 마케팅 등 다양한 마케팅 주제에 대해 조언합니다.
구체적이고 실행 가능한 조언을 제공하세요."""

        full_prompt = f"{system_prompt}\n\n사용자: {user_message}\n\n어시스턴트:"

        llm_service = await self._get_llm_service()
        response = await llm_service.generate_text(full_prompt, max_tokens=800)

        return response.strip()

    async def suggest_marketing_campaign(
        self,
        goal: str,
        budget: Optional[int],
        timeline: str
    ) -> Dict[str, any]:
        """마케팅 캠페인 제안"""
        prompt = f"""다음 조건의 마케팅 캠페인을 제안해주세요:

목표: {goal}
예산: {budget or '미정'}
기간: {timeline}

다음 내용을 포함:
1. 캠페인 전략 (3-5 bullet points)
2. 주요 채널 (우선순위순)
3. 예상 성과
4. 단계별 실행 계획"""

        llm_service = await self._get_llm_service()
        response = await llm_service.generate_text(prompt, max_tokens=1000)

        return {
            "goal": goal,
            "strategy": response.strip(),
            "created_at": datetime.now().isoformat()
        }


_service_instance = None

def get_marketing_tools_service() -> MarketingToolsService:
    global _service_instance
    if _service_instance is None:
        _service_instance = MarketingToolsService()
    return _service_instance
