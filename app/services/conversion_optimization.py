"""
Conversion Rate Optimization (CRO) Service

Provides CTA insertion, lead magnets, popups, and A/B testing
to maximize blog conversions.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import random

from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class CTAType(Enum):
    """CTA types."""
    SUBSCRIBE = "subscribe"
    DOWNLOAD = "download"
    CONTACT = "contact"
    SHARE = "share"
    READ_MORE = "read_more"


class CTAPosition(Enum):
    """CTA positions in content."""
    BEGINNING = "beginning"
    MIDDLE = "middle"
    END = "end"
    SIDEBAR = "sidebar"
    POPUP = "popup"


@dataclass
class CTAConfig:
    """CTA configuration."""
    type: CTAType
    position: CTAPosition
    text: str
    button_text: str
    style: str = "primary"
    show_after_seconds: int = 0


@dataclass
class LeadMagnet:
    """Lead magnet configuration."""
    title: str
    description: str
    file_type: str  # pdf, ebook, checklist, template
    download_url: str
    required_fields: List[str]  # email, name, etc


@dataclass
class PopupConfig:
    """Popup configuration."""
    trigger: str  # time, scroll, exit
    delay_seconds: int = 0
    scroll_percentage: int = 0
    title: str = ""
    message: str = ""
    cta_text: str = "구독하기"
    show_frequency: str = "once"  # once, daily, always


class ConversionOptimizationService:
    """
    Conversion Rate Optimization Service.

    Automatically inserts CTAs, creates lead magnets, and manages popups.
    """

    def __init__(self):
        """Initialize CRO service."""
        self.cta_templates = self._load_cta_templates()
        self.popup_templates = self._load_popup_templates()

        logger.info("cro_service_initialized")

    def _load_cta_templates(self) -> Dict[CTAType, List[Dict]]:
        """Load CTA templates."""
        return {
            CTAType.SUBSCRIBE: [
                {
                    "text": "이 글이 도움이 되셨나요? 더 많은 인사이트를 받아보세요!",
                    "button": "무료 구독하기",
                    "style": "primary"
                },
                {
                    "text": "매주 새로운 블로그 포스트를 이메일로 받아보세요.",
                    "button": "지금 구독",
                    "style": "success"
                },
                {
                    "text": "🎯 실전에서 바로 쓸 수 있는 팁을 놓치지 마세요!",
                    "button": "이메일로 받기",
                    "style": "primary"
                }
            ],
            CTAType.DOWNLOAD: [
                {
                    "text": "이 가이드를 PDF로 다운로드하여 언제든 참고하세요.",
                    "button": "무료 다운로드",
                    "style": "primary"
                },
                {
                    "text": "📥 체크리스트를 다운로드하고 단계별로 실행하세요!",
                    "button": "체크리스트 받기",
                    "style": "success"
                }
            ],
            CTAType.SHARE: [
                {
                    "text": "유용한 정보라면 친구들과 공유해보세요!",
                    "button": "공유하기",
                    "style": "info"
                }
            ],
            CTAType.READ_MORE: [
                {
                    "text": "이 주제가 흥미롭다면 다음 글도 읽어보세요:",
                    "button": "계속 읽기",
                    "style": "secondary"
                }
            ]
        }

    def _load_popup_templates(self) -> Dict[str, Dict]:
        """Load popup templates."""
        return {
            "exit_intent": {
                "title": "잠깐만요! 👋",
                "message": "떠나시기 전에 최신 콘텐츠를 이메일로 받아보시겠어요?",
                "cta": "네, 구독할게요!",
                "trigger": "exit",
                "show_frequency": "once"
            },
            "timed": {
                "title": "💡 특별 제안!",
                "message": "지금 구독하시면 무료 전자책을 드립니다.",
                "cta": "무료로 받기",
                "trigger": "time",
                "delay_seconds": 30,
                "show_frequency": "daily"
            },
            "scroll": {
                "title": "마음에 드셨나요?",
                "message": "더 많은 유용한 팁을 이메일로 받아보세요!",
                "cta": "구독하기",
                "trigger": "scroll",
                "scroll_percentage": 50,
                "show_frequency": "daily"
            }
        }

    async def insert_ctas_in_content(
        self,
        content: str,
        keywords: List[str],
        content_type: str = "blog"
    ) -> Tuple[str, List[CTAConfig]]:
        """
        Insert CTAs into content at optimal positions.

        Args:
            content: Blog post content (HTML)
            keywords: Target keywords for contextual CTAs
            content_type: Type of content (blog, landing_page, etc)

        Returns:
            Tuple of (modified content, list of CTA configs)
        """
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(content, 'html.parser')

            # Find paragraphs
            paragraphs = soup.find_all('p')

            if len(paragraphs) < 3:
                logger.warning("content_too_short_for_cta")
                return content, []

            ctas_inserted = []

            # Insert CTA at beginning (after 1st paragraph)
            if len(paragraphs) > 1:
                cta_config = await self._generate_cta(
                    CTAType.SUBSCRIBE,
                    CTAPosition.BEGINNING,
                    keywords
                )
                cta_html = self._render_cta_html(cta_config)
                paragraphs[0].insert_after(BeautifulSoup(cta_html, 'html.parser'))
                ctas_inserted.append(cta_config)

            # Insert CTA in middle
            if len(paragraphs) >= 5:
                mid_idx = len(paragraphs) // 2
                cta_config = await self._generate_cta(
                    CTAType.DOWNLOAD,
                    CTAPosition.MIDDLE,
                    keywords
                )
                cta_html = self._render_cta_html(cta_config)
                paragraphs[mid_idx].insert_after(BeautifulSoup(cta_html, 'html.parser'))
                ctas_inserted.append(cta_config)

            # Insert CTA at end
            cta_config = await self._generate_cta(
                CTAType.SUBSCRIBE,
                CTAPosition.END,
                keywords
            )
            cta_html = self._render_cta_html(cta_config)
            paragraphs[-1].insert_after(BeautifulSoup(cta_html, 'html.parser'))
            ctas_inserted.append(cta_config)

            modified_content = str(soup)

            logger.info(
                "ctas_inserted",
                count=len(ctas_inserted),
                positions=[c.position.value for c in ctas_inserted]
            )

            return modified_content, ctas_inserted

        except Exception as e:
            logger.error("cta_insertion_failed", error=str(e))
            return content, []

    async def _generate_cta(
        self,
        cta_type: CTAType,
        position: CTAPosition,
        keywords: List[str]
    ) -> CTAConfig:
        """Generate CTA configuration."""
        templates = self.cta_templates.get(cta_type, [])

        if not templates:
            # Default CTA
            return CTAConfig(
                type=cta_type,
                position=position,
                text="더 많은 정보를 받아보세요!",
                button_text="구독하기",
                style="primary"
            )

        # Select random template
        template = random.choice(templates)

        return CTAConfig(
            type=cta_type,
            position=position,
            text=template["text"],
            button_text=template["button"],
            style=template["style"]
        )

    def _render_cta_html(self, cta: CTAConfig) -> str:
        """Render CTA as HTML."""
        style_classes = {
            "primary": "bg-blue-600 hover:bg-blue-700",
            "success": "bg-green-600 hover:bg-green-700",
            "info": "bg-sky-600 hover:bg-sky-700",
            "secondary": "bg-gray-600 hover:bg-gray-700"
        }

        button_class = style_classes.get(cta.style, style_classes["primary"])

        html = f'''
        <div class="cta-box my-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 border-l-4 border-blue-600 rounded-lg shadow-md">
            <p class="text-lg text-gray-800 mb-4">{cta.text}</p>
            <a href="#subscribe" class="inline-block px-6 py-3 {button_class} text-white font-semibold rounded-lg shadow-lg transform transition hover:scale-105">
                {cta.button_text}
            </a>
        </div>
        '''

        return html

    async def create_lead_magnet(
        self,
        title: str,
        description: str,
        content_type: str,
        keywords: List[str]
    ) -> LeadMagnet:
        """
        Create a lead magnet from blog content.

        Args:
            title: Lead magnet title
            description: Description
            content_type: Type (pdf, ebook, checklist, template)
            keywords: Target keywords

        Returns:
            LeadMagnet configuration
        """
        # Generate download URL (placeholder)
        filename = title.replace(" ", "-").lower()
        download_url = f"/downloads/{filename}.{content_type}"

        lead_magnet = LeadMagnet(
            title=title,
            description=description,
            file_type=content_type,
            download_url=download_url,
            required_fields=["email", "name"]
        )

        logger.info(
            "lead_magnet_created",
            title=title,
            type=content_type
        )

        return lead_magnet

    async def generate_popup_config(
        self,
        popup_type: str = "exit_intent",
        custom_message: Optional[str] = None
    ) -> PopupConfig:
        """
        Generate popup configuration.

        Args:
            popup_type: Type of popup (exit_intent, timed, scroll)
            custom_message: Optional custom message

        Returns:
            PopupConfig
        """
        template = self.popup_templates.get(
            popup_type,
            self.popup_templates["exit_intent"]
        )

        config = PopupConfig(
            trigger=template["trigger"],
            delay_seconds=template.get("delay_seconds", 0),
            scroll_percentage=template.get("scroll_percentage", 0),
            title=template["title"],
            message=custom_message or template["message"],
            cta_text=template["cta"],
            show_frequency=template["show_frequency"]
        )

        logger.info(
            "popup_config_generated",
            type=popup_type,
            trigger=config.trigger
        )

        return config

    async def ab_test_cta(
        self,
        variant_a: CTAConfig,
        variant_b: CTAConfig
    ) -> Dict[str, Any]:
        """
        Set up A/B test for CTAs.

        Args:
            variant_a: First CTA variant
            variant_b: Second CTA variant

        Returns:
            A/B test configuration
        """
        test_config = {
            "test_id": f"cta_test_{datetime.now().timestamp()}",
            "variants": {
                "A": {
                    "text": variant_a.text,
                    "button": variant_a.button_text,
                    "style": variant_a.style
                },
                "B": {
                    "text": variant_b.text,
                    "button": variant_b.button_text,
                    "style": variant_b.style
                }
            },
            "split": 50,  # 50/50 split
            "goal": "conversions",
            "status": "active"
        }

        logger.info(
            "ab_test_created",
            test_id=test_config["test_id"]
        )

        return test_config

    def get_optimal_cta_positions(
        self,
        content_length: int,
        content_type: str = "blog"
    ) -> List[CTAPosition]:
        """
        Get optimal CTA positions based on content length.

        Args:
            content_length: Number of words in content
            content_type: Type of content

        Returns:
            List of recommended positions
        """
        positions = []

        if content_length < 500:
            # Short content: only end CTA
            positions = [CTAPosition.END]
        elif content_length < 1000:
            # Medium content: beginning and end
            positions = [CTAPosition.BEGINNING, CTAPosition.END]
        else:
            # Long content: beginning, middle, end
            positions = [
                CTAPosition.BEGINNING,
                CTAPosition.MIDDLE,
                CTAPosition.END
            ]

        # Add sidebar for all content types
        positions.append(CTAPosition.SIDEBAR)

        logger.info(
            "optimal_positions_calculated",
            content_length=content_length,
            positions=[p.value for p in positions]
        )

        return positions


# Singleton instance
_cro_service = None


def get_cro_service() -> ConversionOptimizationService:
    """Get or create singleton CRO service instance."""
    global _cro_service

    if _cro_service is None:
        _cro_service = ConversionOptimizationService()

    return _cro_service
