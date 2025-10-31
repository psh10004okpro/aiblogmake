"""
Email Marketing Automation Service

Provides newsletter generation, subscriber segmentation,
and automated email campaigns.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


@dataclass
class NewsletterTemplate:
    """Newsletter template."""
    subject: str
    body_html: str
    preview_text: str


@dataclass
class EmailCampaign:
    """Email campaign configuration."""
    name: str
    subject: str
    content: str
    segment: str
    schedule_time: Optional[datetime] = None
    ab_test: bool = False


class EmailMarketingService:
    """
    Email Marketing Automation Service.

    Automatically generates newsletters, manages subscribers,
    and sends targeted email campaigns.
    """

    def __init__(self):
        """Initialize email marketing service."""
        self.smtp_configured = self._check_smtp_config()
        logger.info("email_marketing_service_initialized", configured=self.smtp_configured)

    def _check_smtp_config(self) -> bool:
        """Check if SMTP is configured."""
        return bool(
            settings.smtp_host and
            settings.smtp_user and
            settings.smtp_password
        )

    async def generate_newsletter(
        self,
        posts: List[Dict],
        template_type: str = "weekly_digest"
    ) -> NewsletterTemplate:
        """
        Generate newsletter from recent posts using AI.

        Args:
            posts: List of blog posts
            template_type: Type of newsletter (weekly_digest, monthly, etc)

        Returns:
            NewsletterTemplate with subject and HTML body
        """
        try:
            from app.services.llm_factory import LLMFactory

            # Build posts summary
            posts_text = ""
            for i, post in enumerate(posts[:5], 1):
                posts_text += f"""
{i}. {post['title']}
   {post.get('excerpt', '')[:100]}...
   링크: {post.get('url', '')}

"""

            prompt = f"""
다음 블로그 포스트들로 이메일 뉴스레터를 작성해주세요.

포스트 목록:
{posts_text}

요구사항:
- 매력적인 제목
- 친근한 인사말
- 각 포스트를 간략히 소개
- CTA (블로그 방문 유도)
- HTML 형식

뉴스레터:"""

            llm_service = LLMFactory.create(settings.default_llm_provider)
            newsletter_html = await llm_service.generate_text(prompt, max_tokens=1000)

            # Generate subject
            subject_prompt = f"""
다음 뉴스레터에 어울리는 매력적인 제목을 작성해주세요 (50자 이내):

{newsletter_html[:200]}...

제목:"""

            subject = await llm_service.generate_text(subject_prompt, max_tokens=50)
            subject = subject.strip().strip('"')

            template = NewsletterTemplate(
                subject=subject,
                body_html=newsletter_html,
                preview_text=f"{len(posts)}개의 새로운 포스트를 확인하세요!"
            )

            logger.info("newsletter_generated", posts_count=len(posts))

            return template

        except Exception as e:
            logger.error("newsletter_generation_failed", error=str(e))
            # Fallback template
            return NewsletterTemplate(
                subject="이번 주 블로그 업데이트",
                body_html="<p>새로운 포스트를 확인해보세요!</p>",
                preview_text="새로운 콘텐츠가 준비되었습니다"
            )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str
    ) -> bool:
        """
        Send email via SMTP.

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML content

        Returns:
            True if sent successfully
        """
        if not self.smtp_configured:
            logger.warning("smtp_not_configured")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = settings.smtp_from or settings.smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject

            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)

            logger.info("email_sent", to=to_email, subject=subject)
            return True

        except Exception as e:
            logger.error("email_send_failed", error=str(e), to=to_email)
            return False

    async def send_newsletter(
        self,
        newsletter: NewsletterTemplate,
        subscribers: List[str]
    ) -> Dict[str, int]:
        """
        Send newsletter to subscribers.

        Args:
            newsletter: Newsletter template
            subscribers: List of subscriber emails

        Returns:
            Stats (sent, failed)
        """
        sent = 0
        failed = 0

        for email in subscribers:
            success = await self.send_email(
                email,
                newsletter.subject,
                newsletter.body_html
            )

            if success:
                sent += 1
            else:
                failed += 1

        logger.info(
            "newsletter_sent",
            sent=sent,
            failed=failed,
            total=len(subscribers)
        )

        return {"sent": sent, "failed": failed, "total": len(subscribers)}

    def get_status(self) -> Dict[str, bool]:
        """Get email marketing status."""
        return {
            "smtp_configured": self.smtp_configured,
            "ready": self.smtp_configured
        }


# Singleton
_email_service = None


def get_email_marketing_service() -> EmailMarketingService:
    """Get singleton email marketing service."""
    global _email_service
    if _email_service is None:
        _email_service = EmailMarketingService()
    return _email_service
