"""
Content generation service with multi-LLM support.

This service generates SEO-optimized Korean blog content following
2025 Google SEO best practices and E-E-A-T principles.

Supports multiple LLM providers:
- Claude (Anthropic)
- ChatGPT (OpenAI)
- Gemini (Google)
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.core.config import settings
from app.utils.logger import get_logger
from app.utils.seo import (
    count_words,
    estimate_reading_time,
    generate_slug,
    generate_meta_description,
    generate_blog_posting_schema,
    generate_faq_schema,
)
from app.services.llm import get_llm_provider, BaseLLMProvider

logger = get_logger(__name__)


class ContentGeneratorService:
    """Service for generating SEO-optimized blog content with multi-LLM support."""

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize the content generator service.

        Args:
            provider: LLM provider name (claude, chatgpt, gemini).
                     If None, uses default from settings.
        """
        self.provider = get_llm_provider(provider)
        logger.info(
            "content_generator_initialized",
            provider=self.provider.provider_name,
            model=self.provider.model
        )

    async def generate_content(
        self,
        keyword: str,
        target_word_count: int = 2000,
        tone: str = "professional",
        include_faq: bool = True,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive blog content for a keyword.

        Args:
            keyword: Target keyword for the content.
            target_word_count: Target word count (1500-3000).
            tone: Content tone (professional, casual, friendly, authoritative).
            include_faq: Whether to include FAQ section.
            additional_context: Additional context for content generation.

        Returns:
            Dict[str, Any]: Generated content with metadata.

        Example:
            ```python
            service = ContentGeneratorService()
            content = await service.generate_content(
                keyword="블로그 SEO 최적화",
                target_word_count=2000,
                tone="professional"
            )
            ```
        """
        logger.info(
            "generating_content",
            keyword=keyword,
            target_word_count=target_word_count
        )

        # Generate main content
        content_html = await self._generate_main_content(
            keyword=keyword,
            target_word_count=target_word_count,
            tone=tone,
            additional_context=additional_context
        )

        # Generate title and metadata
        title = await self._generate_title(keyword, content_html)

        # Generate H2 and H3 tags
        headings = await self._extract_headings(content_html)

        # Generate meta description
        meta_description = generate_meta_description(
            content_html,
            max_length=settings.meta_description_length
        )

        # Generate FAQ if requested
        faq_content = None
        faq_schema = None
        if include_faq:
            faq_content = await self._generate_faq(keyword, content_html)
            if faq_content:
                content_html += f"\n\n{faq_content}"
                faq_schema = self._parse_faq_schema(faq_content)

        # Generate internal links suggestions
        internal_links = await self._suggest_internal_links(keyword, content_html)

        # Calculate metrics
        word_count = count_words(content_html)
        reading_time = estimate_reading_time(word_count)

        # Generate schema markup
        schema_markup = generate_blog_posting_schema(
            title=title,
            description=meta_description,
            content=content_html,
            author_name="Blog Author",  # Should be configurable
            published_date=datetime.now(),
        )

        result = {
            "title": title,
            "content": content_html,
            "meta_description": meta_description,
            "h1_tag": title,
            "h2_tags": headings.get("h2", []),
            "h3_tags": headings.get("h3", []),
            "internal_links": internal_links,
            "schema_markup": schema_markup,
            "faq_schema": faq_schema,
            "word_count": word_count,
            "estimated_reading_time": reading_time,
        }

        logger.info(
            "content_generated",
            keyword=keyword,
            word_count=word_count,
            reading_time=reading_time
        )

        return result

    async def _generate_main_content(
        self,
        keyword: str,
        target_word_count: int,
        tone: str,
        additional_context: Optional[str]
    ) -> str:
        """
        Generate main blog content using Claude.

        Args:
            keyword: Target keyword.
            target_word_count: Target word count.
            tone: Content tone.
            additional_context: Additional context.

        Returns:
            str: Generated HTML content.
        """
        prompt = f"""당신은 한국 시장의 SEO 전문가이자 전문 블로그 작가입니다.
다음 키워드에 대한 블로그 포스트를 작성해주세요: "{keyword}"

요구사항:
1. 목표 단어 수: 약 {target_word_count}자
2. 톤: {tone}
3. 2025년 구글 SEO 최신 기준 적용 (E-E-A-T 원칙)
4. 한국 독자를 위한 문화적 맥락과 실제 경험 포함
5. 자연스러운 한국어 작문 (AI 생성처럼 보이지 않도록)

구조:
- H1: 제목 (1개만, 키워드 포함)
- 도입부: 독자의 관심을 끄는 흥미로운 서론 (2-3 문단)
- H2: 주요 섹션 (3-5개)
  - 각 H2 아래에 H3 하위 섹션 (2-3개)
  - 구체적인 예시와 실용적인 팁 포함
- 결론: 핵심 요약 및 행동 유도 (CTA)

SEO 최적화:
- 자연스럽게 타겟 키워드 포함 (키워드 밀도 1-2%)
- 관련 LSI 키워드 사용
- 짧고 명확한 문장 (가독성 향상)
- 글머리 기호와 번호 목록 활용
- 구체적인 데이터와 통계 포함 (가능하면)

톤 가이드:
- professional: 전문적이고 신뢰할 수 있는 어조
- casual: 편안하고 친근한 대화체
- friendly: 따뜻하고 도움이 되는 어조
- authoritative: 권위 있고 전문가적인 어조

{f"추가 컨텍스트: {additional_context}" if additional_context else ""}

HTML 형식으로 작성해주세요. <h1>, <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <em> 태그만 사용하세요.
이미지나 링크는 포함하지 마세요 (나중에 자동으로 추가됩니다).
"""

        try:
            response = await self.provider.generate_with_retry(
                prompt=prompt,
                max_retries=3
            )

            logger.info(
                "main_content_generated",
                keyword=keyword,
                provider=response.provider,
                model=response.model,
                tokens=response.tokens_used
            )

            return response.content

        except Exception as e:
            logger.error(
                "content_generation_error",
                error=str(e),
                keyword=keyword,
                provider=self.provider.provider_name
            )
            raise

    async def _generate_title(self, keyword: str, content: str) -> str:
        """
        Generate SEO-optimized title.

        Args:
            keyword: Target keyword.
            content: Generated content.

        Returns:
            str: SEO-optimized title.
        """
        # Extract H1 from content if present
        import re
        h1_match = re.search(r"<h1>(.*?)</h1>", content, re.IGNORECASE)
        if h1_match:
            return h1_match.group(1)

        # Otherwise generate title
        prompt = f"""다음 키워드에 대한 SEO 최적화 블로그 제목을 작성해주세요: "{keyword}"

요구사항:
- 30-60자 길이
- 키워드 포함 (가능하면 앞부분에)
- 클릭을 유도하는 흥미로운 제목
- 한국어로 자연스럽게 작성
- 과장되지 않고 정확한 표현

제목만 출력하세요 (부가 설명 없이).
"""

        try:
            response = await self.provider.generate(
                prompt=prompt,
                max_tokens=100,
                temperature=0.7
            )

            title = response.content.strip()
            return title

        except Exception as e:
            logger.error(
                "title_generation_error",
                error=str(e),
                keyword=keyword,
                provider=self.provider.provider_name
            )
            return f"{keyword} - 완벽 가이드"

    async def _extract_headings(self, content: str) -> Dict[str, List[str]]:
        """
        Extract H2 and H3 headings from content.

        Args:
            content: HTML content.

        Returns:
            Dict[str, List[str]]: Headings by level.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(content, "html.parser")

        headings = {
            "h2": [h.get_text().strip() for h in soup.find_all("h2")],
            "h3": [h.get_text().strip() for h in soup.find_all("h3")],
        }

        return headings

    async def _generate_faq(self, keyword: str, content: str) -> Optional[str]:
        """
        Generate FAQ section.

        Args:
            keyword: Target keyword.
            content: Main content.

        Returns:
            Optional[str]: FAQ HTML or None.
        """
        prompt = f"""다음 키워드와 콘텐츠를 바탕으로 FAQ 섹션을 작성해주세요.

키워드: {keyword}

콘텐츠 요약:
{content[:500]}...

요구사항:
- 3-5개의 자주 묻는 질문과 답변
- 질문은 독자가 실제로 궁금해할 만한 내용
- 답변은 간결하고 명확하게 (2-3 문장)
- 키워드와 관련된 추가 정보 제공

HTML 형식:
<h2>자주 묻는 질문 (FAQ)</h2>
<div class="faq-item">
  <h3>질문 1</h3>
  <p>답변 1</p>
</div>
...

FAQ 섹션만 출력하세요.
"""

        try:
            response = await self.provider.generate(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7
            )

            faq_html = response.content.strip()
            return faq_html

        except Exception as e:
            logger.error(
                "faq_generation_error",
                error=str(e),
                keyword=keyword,
                provider=self.provider.provider_name
            )
            return None

    def _parse_faq_schema(self, faq_html: str) -> Optional[Dict[str, Any]]:
        """
        Parse FAQ HTML into schema markup.

        Args:
            faq_html: FAQ HTML content.

        Returns:
            Optional[Dict[str, Any]]: FAQ schema or None.
        """
        from bs4 import BeautifulSoup

        try:
            soup = BeautifulSoup(faq_html, "html.parser")
            faq_items = soup.find_all("div", class_="faq-item")

            faqs = []
            for item in faq_items:
                question_tag = item.find("h3")
                answer_tag = item.find("p")

                if question_tag and answer_tag:
                    faqs.append({
                        "question": question_tag.get_text().strip(),
                        "answer": answer_tag.get_text().strip()
                    })

            if faqs:
                return generate_faq_schema(faqs)

        except Exception as e:
            logger.error("faq_schema_parsing_error", error=str(e))

        return None

    async def _suggest_internal_links(
        self,
        keyword: str,
        content: str
    ) -> List[str]:
        """
        Suggest internal link anchor texts.

        Args:
            keyword: Target keyword.
            content: Content HTML.

        Returns:
            List[str]: List of suggested anchor texts for internal links.
        """
        prompt = f"""다음 키워드와 콘텐츠를 바탕으로 내부 링크를 삽입할 수 있는 앵커 텍스트를 3-5개 제안해주세요.

키워드: {keyword}

요구사항:
- 관련된 주제나 하위 주제를 위한 앵커 텍스트
- 자연스럽게 콘텐츠에 삽입 가능한 문구
- SEO 친화적인 표현

예시:
- "블로그 글쓰기 팁"
- "SEO 최적화 방법"
- "키워드 리서치 도구"

앵커 텍스트만 리스트로 출력하세요 (한 줄에 하나씩).
"""

        try:
            response = await self.provider.generate(
                prompt=prompt,
                max_tokens=200,
                temperature=0.7
            )

            links_text = response.content.strip()
            links = [
                line.strip().lstrip("-•*").strip()
                for line in links_text.split("\n")
                if line.strip()
            ]

            return links[:5]

        except Exception as e:
            logger.error(
                "internal_links_suggestion_error",
                error=str(e),
                provider=self.provider.provider_name
            )
            return []

    async def enhance_content_naturally(self, content: str) -> str:
        """
        Enhance AI-generated content to make it more natural.

        This adds personal experiences, Korean cultural context,
        and makes the content feel less AI-generated (40-60% modification).

        Args:
            content: Original AI-generated content.

        Returns:
            str: Enhanced content.
        """
        prompt = f"""다음 AI 생성 콘텐츠를 더 자연스럽고 인간적으로 개선해주세요.

원본 콘텐츠:
{content}

개선 요구사항:
- 40-60% 정도의 수정 (과도하지 않게)
- 개인적인 경험이나 일화 추가 (자연스럽게)
- 한국 문화적 맥락 반영
- AI 생성처럼 보이는 반복적인 패턴 제거
- 더 자연스러운 문장 흐름
- 구어체 표현 적절히 섞기
- 감정과 뉘앙스 추가

주의사항:
- 원래 구조와 핵심 정보는 유지
- SEO 최적화 요소는 그대로 유지
- 과장하거나 부정확한 정보 추가하지 않기

개선된 콘텐츠를 HTML 형식으로 출력하세요.
"""

        try:
            response = await self.provider.generate(
                prompt=prompt,
                max_tokens=self.provider.max_tokens,
                temperature=0.8  # Higher temperature for more creativity
            )

            enhanced_content = response.content.strip()

            logger.info(
                "content_enhanced_naturally",
                provider=self.provider.provider_name,
                tokens=response.tokens_used
            )
            return enhanced_content

        except Exception as e:
            logger.error(
                "content_enhancement_error",
                error=str(e),
                provider=self.provider.provider_name
            )
            return content  # Return original if enhancement fails
