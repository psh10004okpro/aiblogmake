"""
Social Media Auto-Posting Service

Provides automated posting to Facebook, Twitter, and LinkedIn
with AI-generated messages and hashtags.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import hashlib
import hmac
import base64

from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


@dataclass
class SocialPost:
    """Container for social media post data."""
    platform: str
    message: str
    hashtags: List[str]
    image_url: Optional[str] = None
    link: Optional[str] = None
    scheduled_time: Optional[datetime] = None


@dataclass
class PostResult:
    """Result of a social media post."""
    success: bool
    platform: str
    post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


class SocialMediaService:
    """
    Social Media Auto-Posting Service.

    Supports Facebook, Twitter (X), and LinkedIn.
    """

    def __init__(self):
        """Initialize social media service."""
        self.platforms = {}

        # Check which platforms are configured
        if self._is_facebook_configured():
            self.platforms['facebook'] = FacebookPoster()

        if self._is_twitter_configured():
            self.platforms['twitter'] = TwitterPoster()

        if self._is_linkedin_configured():
            self.platforms['linkedin'] = LinkedInPoster()

        logger.info(
            "social_media_service_initialized",
            platforms=list(self.platforms.keys())
        )

    def _is_facebook_configured(self) -> bool:
        """Check if Facebook is configured."""
        return bool(
            settings.facebook_page_id and
            settings.facebook_access_token
        )

    def _is_twitter_configured(self) -> bool:
        """Check if Twitter is configured."""
        return bool(
            settings.twitter_api_key and
            settings.twitter_api_secret and
            settings.twitter_access_token and
            settings.twitter_access_secret
        )

    def _is_linkedin_configured(self) -> bool:
        """Check if LinkedIn is configured."""
        return bool(
            settings.linkedin_access_token and
            settings.linkedin_organization_id
        )

    async def generate_post_message(
        self,
        title: str,
        excerpt: str,
        keywords: List[str],
        platform: str
    ) -> str:
        """
        Generate platform-specific post message using AI.

        Args:
            title: Post title
            excerpt: Post excerpt/summary
            keywords: Target keywords
            platform: Target platform (facebook, twitter, linkedin)

        Returns:
            Generated message text
        """
        try:
            from app.services.llm_factory import LLMFactory

            # Platform-specific prompts
            prompts = {
                'facebook': f"""
다음 블로그 포스트를 Facebook 게시물로 변환해주세요.

제목: {title}
요약: {excerpt}
키워드: {', '.join(keywords)}

요구사항:
- 매력적이고 친근한 톤
- 2-3문장으로 간결하게
- 클릭 유도 문구 포함
- 이모지 적절히 사용
- 한글로 작성

게시물:""",
                'twitter': f"""
다음 블로그 포스트를 트위터 게시물로 변환해주세요.

제목: {title}
요약: {excerpt}
키워드: {', '.join(keywords)}

요구사항:
- 280자 이내 (한글 기준)
- 임팩트 있는 한 문장
- 클릭 유도
- 이모지 사용
- 한글로 작성

트윗:""",
                'linkedin': f"""
다음 블로그 포스트를 LinkedIn 게시물로 변환해주세요.

제목: {title}
요약: {excerpt}
키워드: {', '.join(keywords)}

요구사항:
- 전문적이고 인사이트 있는 톤
- 3-4문장
- 비즈니스 가치 강조
- 한글로 작성

게시물:"""
            }

            prompt = prompts.get(platform, prompts['facebook'])

            # Generate using default LLM
            llm_service = LLMFactory.create(settings.default_llm_provider)
            message = await llm_service.generate_text(prompt, max_tokens=300)

            # Clean up
            message = message.strip()

            logger.info(
                "social_post_message_generated",
                platform=platform,
                length=len(message)
            )

            return message

        except Exception as e:
            logger.error("social_post_message_generation_failed", error=str(e))
            # Fallback to simple format
            return f"{title}\n\n{excerpt[:100]}..."

    async def generate_hashtags(
        self,
        keywords: List[str],
        platform: str,
        max_count: int = 5
    ) -> List[str]:
        """
        Generate hashtags from keywords.

        Args:
            keywords: Target keywords
            platform: Target platform
            max_count: Maximum number of hashtags

        Returns:
            List of hashtags (without # prefix)
        """
        try:
            from app.services.llm_factory import LLMFactory

            prompt = f"""
다음 키워드들을 바탕으로 소셜 미디어 해시태그를 생성해주세요.

키워드: {', '.join(keywords)}
플랫폼: {platform}
최대 개수: {max_count}

요구사항:
- 인기 있고 관련성 높은 해시태그
- 한글 또는 영문
- # 없이 텍스트만
- 한 줄에 하나씩

해시태그:"""

            llm_service = LLMFactory.create(settings.default_llm_provider)
            response = await llm_service.generate_text(prompt, max_tokens=200)

            # Parse hashtags
            hashtags = []
            for line in response.strip().split('\n'):
                tag = line.strip().replace('#', '').strip()
                if tag and len(hashtags) < max_count:
                    hashtags.append(tag)

            logger.info(
                "hashtags_generated",
                platform=platform,
                count=len(hashtags)
            )

            return hashtags[:max_count]

        except Exception as e:
            logger.error("hashtag_generation_failed", error=str(e))
            # Fallback to keywords
            return keywords[:max_count]

    async def post_to_platform(
        self,
        platform: str,
        message: str,
        hashtags: List[str],
        link: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> PostResult:
        """
        Post to a specific platform.

        Args:
            platform: Platform name (facebook, twitter, linkedin)
            message: Post message
            hashtags: List of hashtags
            link: Optional link to include
            image_url: Optional image URL

        Returns:
            PostResult with success status and details
        """
        if platform not in self.platforms:
            return PostResult(
                success=False,
                platform=platform,
                error=f"Platform {platform} not configured"
            )

        try:
            poster = self.platforms[platform]
            result = await poster.post(message, hashtags, link, image_url)

            logger.info(
                "social_post_published",
                platform=platform,
                success=result.success,
                post_id=result.post_id
            )

            return result

        except Exception as e:
            logger.error(
                "social_post_failed",
                platform=platform,
                error=str(e)
            )
            return PostResult(
                success=False,
                platform=platform,
                error=str(e)
            )

    async def post_to_all(
        self,
        title: str,
        excerpt: str,
        keywords: List[str],
        link: str,
        image_url: Optional[str] = None,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, PostResult]:
        """
        Post to all configured platforms.

        Args:
            title: Post title
            excerpt: Post excerpt
            keywords: Target keywords
            link: Post URL
            image_url: Optional image URL
            platforms: Optional list of specific platforms to post to

        Returns:
            Dictionary of platform -> PostResult
        """
        if platforms is None:
            platforms = list(self.platforms.keys())

        results = {}

        for platform in platforms:
            if platform not in self.platforms:
                results[platform] = PostResult(
                    success=False,
                    platform=platform,
                    error="Platform not configured"
                )
                continue

            # Generate platform-specific message
            message = await self.generate_post_message(
                title, excerpt, keywords, platform
            )

            # Generate hashtags
            hashtags = await self.generate_hashtags(keywords, platform)

            # Post
            result = await self.post_to_platform(
                platform, message, hashtags, link, image_url
            )

            results[platform] = result

        logger.info(
            "social_posts_batch_completed",
            total=len(platforms),
            succeeded=sum(1 for r in results.values() if r.success)
        )

        return results

    def get_status(self) -> Dict[str, Any]:
        """
        Get social media configuration status.

        Returns:
            Dictionary with platform statuses
        """
        return {
            "configured_platforms": list(self.platforms.keys()),
            "available_platforms": ["facebook", "twitter", "linkedin"],
            "facebook_configured": self._is_facebook_configured(),
            "twitter_configured": self._is_twitter_configured(),
            "linkedin_configured": self._is_linkedin_configured()
        }


class FacebookPoster:
    """Facebook page posting."""

    async def post(
        self,
        message: str,
        hashtags: List[str],
        link: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> PostResult:
        """Post to Facebook page."""
        try:
            import aiohttp

            # Add hashtags to message
            full_message = f"{message}\n\n" + " ".join(f"#{tag}" for tag in hashtags)

            # Facebook Graph API
            url = f"https://graph.facebook.com/v18.0/{settings.facebook_page_id}/feed"

            params = {
                "message": full_message,
                "access_token": settings.facebook_access_token
            }

            if link:
                params["link"] = link

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        post_id = data.get("id")

                        return PostResult(
                            success=True,
                            platform="facebook",
                            post_id=post_id,
                            url=f"https://www.facebook.com/{post_id}"
                        )
                    else:
                        error_text = await response.text()
                        return PostResult(
                            success=False,
                            platform="facebook",
                            error=error_text
                        )

        except Exception as e:
            return PostResult(
                success=False,
                platform="facebook",
                error=str(e)
            )


class TwitterPoster:
    """Twitter (X) posting."""

    async def post(
        self,
        message: str,
        hashtags: List[str],
        link: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> PostResult:
        """Post to Twitter."""
        try:
            import aiohttp
            import json

            # Add hashtags and link to message
            tweet_parts = [message]

            if hashtags:
                tweet_parts.append(" ".join(f"#{tag}" for tag in hashtags))

            if link:
                tweet_parts.append(link)

            tweet_text = " ".join(tweet_parts)

            # Ensure within 280 character limit
            if len(tweet_text) > 280:
                # Truncate message, keep hashtags and link
                max_message_len = 280 - len(" ".join(tweet_parts[1:])) - 5
                tweet_text = f"{message[:max_message_len]}... " + " ".join(tweet_parts[1:])

            # Twitter API v2
            url = "https://api.twitter.com/2/tweets"

            headers = self._get_auth_headers("POST", url)
            headers["Content-Type"] = "application/json"

            payload = {
                "text": tweet_text
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    data=json.dumps(payload)
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        tweet_id = data.get("data", {}).get("id")

                        return PostResult(
                            success=True,
                            platform="twitter",
                            post_id=tweet_id,
                            url=f"https://twitter.com/i/web/status/{tweet_id}"
                        )
                    else:
                        error_text = await response.text()
                        return PostResult(
                            success=False,
                            platform="twitter",
                            error=error_text
                        )

        except Exception as e:
            return PostResult(
                success=False,
                platform="twitter",
                error=str(e)
            )

    def _get_auth_headers(self, method: str, url: str) -> Dict[str, str]:
        """Generate OAuth 1.0a headers for Twitter."""
        import time
        import secrets
        from urllib.parse import quote

        oauth_params = {
            "oauth_consumer_key": settings.twitter_api_key,
            "oauth_token": settings.twitter_access_token,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": secrets.token_hex(16),
            "oauth_version": "1.0"
        }

        # Generate signature
        signature = self._generate_signature(method, url, oauth_params)
        oauth_params["oauth_signature"] = signature

        # Build authorization header
        auth_header = "OAuth " + ", ".join(
            f'{k}="{quote(str(v), safe="")}"'
            for k, v in sorted(oauth_params.items())
        )

        return {"Authorization": auth_header}

    def _generate_signature(
        self,
        method: str,
        url: str,
        oauth_params: Dict[str, str]
    ) -> str:
        """Generate OAuth signature."""
        from urllib.parse import quote

        # Parameter string
        param_string = "&".join(
            f"{quote(str(k), safe='')}={quote(str(v), safe='')}"
            for k, v in sorted(oauth_params.items())
        )

        # Signature base string
        base_string = "&".join([
            method.upper(),
            quote(url, safe=''),
            quote(param_string, safe='')
        ])

        # Signing key
        signing_key = (
            f"{quote(settings.twitter_api_secret, safe='')}&"
            f"{quote(settings.twitter_access_secret, safe='')}"
        )

        # Generate signature
        signature = hmac.new(
            signing_key.encode(),
            base_string.encode(),
            hashlib.sha1
        ).digest()

        return base64.b64encode(signature).decode()


class LinkedInPoster:
    """LinkedIn posting."""

    async def post(
        self,
        message: str,
        hashtags: List[str],
        link: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> PostResult:
        """Post to LinkedIn."""
        try:
            import aiohttp
            import json

            # Add hashtags to message
            full_message = f"{message}\n\n" + " ".join(f"#{tag}" for tag in hashtags)

            # LinkedIn API
            url = "https://api.linkedin.com/v2/ugcPosts"

            headers = {
                "Authorization": f"Bearer {settings.linkedin_access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }

            # Build post payload
            payload = {
                "author": f"urn:li:organization:{settings.linkedin_organization_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": full_message
                        },
                        "shareMediaCategory": "ARTICLE" if link else "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }

            # Add link if provided
            if link:
                payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                    "status": "READY",
                    "originalUrl": link
                }]

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    data=json.dumps(payload)
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        post_id = data.get("id")

                        return PostResult(
                            success=True,
                            platform="linkedin",
                            post_id=post_id,
                            url=f"https://www.linkedin.com/feed/update/{post_id}"
                        )
                    else:
                        error_text = await response.text()
                        return PostResult(
                            success=False,
                            platform="linkedin",
                            error=error_text
                        )

        except Exception as e:
            return PostResult(
                success=False,
                platform="linkedin",
                error=str(e)
            )


# Singleton instance
_social_media_service = None


def get_social_media_service() -> SocialMediaService:
    """Get or create singleton SocialMediaService instance."""
    global _social_media_service

    if _social_media_service is None:
        _social_media_service = SocialMediaService()

    return _social_media_service
