"""
콘텐츠 재활용 엔진 서비스
블로그 포스트를 다양한 형식으로 자동 변환
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from bs4 import BeautifulSoup
import re

from app.core.config import settings
from app.services.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


@dataclass
class YouTubeScript:
    """YouTube 스크립트 데이터"""
    title: str
    hook: str  # 첫 15초 훅
    intro: str  # 인트로
    main_points: List[Dict[str, str]]  # [{timestamp, content, visual_cue}]
    outro: str  # 아웃트로
    cta: str  # Call to action
    estimated_duration: str  # 예상 길이
    keywords: List[str]
    thumbnail_ideas: List[str]


@dataclass
class InfographicData:
    """인포그래픽 데이터"""
    title: str
    subtitle: str
    main_stats: List[Dict[str, Any]]  # [{label, value, icon}]
    sections: List[Dict[str, Any]]  # [{title, points, visual_type}]
    key_takeaways: List[str]
    color_scheme: str  # 추천 컬러 스킴
    layout_type: str  # vertical, horizontal, timeline


@dataclass
class SocialMediaCard:
    """소셜 미디어 카드 데이터"""
    platform: str
    headline: str
    subheadline: str
    key_points: List[str]
    call_to_action: str
    hashtags: List[str]
    visual_elements: List[str]  # 시각 요소 제안
    character_count: int


@dataclass
class PodcastScript:
    """팟캐스트 스크립트"""
    title: str
    episode_number: Optional[int]
    intro_music_cue: str
    host_intro: str
    segments: List[Dict[str, Any]]  # [{title, talking_points, duration}]
    guest_questions: List[str]  # 게스트 인터뷰 질문 (있다면)
    outro: str
    show_notes: List[str]
    estimated_duration: str


@dataclass
class TwitterThread:
    """Twitter 스레드"""
    hook_tweet: str  # 첫 트윗 (훅)
    thread_tweets: List[str]  # 연속 트윗
    conclusion_tweet: str  # 마지막 트윗
    cta_tweet: str  # CTA 트윗
    total_tweets: int
    estimated_engagement: str


class ContentRepurposingService:
    """콘텐츠 재활용 서비스"""

    def __init__(self):
        self.llm_service = None

    async def _get_llm_service(self):
        """LLM 서비스 인스턴스 가져오기 (lazy loading)"""
        if self.llm_service is None:
            self.llm_service = LLMFactory.create(settings.default_llm_provider)
        return self.llm_service

    def _extract_text_from_html(self, html_content: str) -> str:
        """HTML에서 텍스트만 추출"""
        soup = BeautifulSoup(html_content, 'html.parser')

        # 스크립트와 스타일 제거
        for script in soup(["script", "style"]):
            script.decompose()

        # 텍스트 추출
        text = soup.get_text()

        # 줄바꿈 정리
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    def _extract_key_points(self, content: str, max_points: int = 5) -> List[str]:
        """콘텐츠에서 주요 포인트 추출"""
        soup = BeautifulSoup(content, 'html.parser')

        # 헤딩, 리스트 아이템 등에서 주요 포인트 추출
        key_points = []

        # 헤딩 추출
        for heading in soup.find_all(['h2', 'h3']):
            text = heading.get_text().strip()
            if text and len(text) > 10:
                key_points.append(text)

        # 리스트 아이템 추출
        for li in soup.find_all('li'):
            text = li.get_text().strip()
            if text and len(text) > 20 and len(text) < 200:
                key_points.append(text)

        return key_points[:max_points]

    async def to_youtube_script(
        self,
        title: str,
        content: str,
        keywords: List[str],
        target_duration: str = "10-15분"
    ) -> YouTubeScript:
        """블로그 포스트를 YouTube 스크립트로 변환"""
        logger.info(f"Converting blog post to YouTube script: {title}")

        text_content = self._extract_text_from_html(content)
        key_points = self._extract_key_points(content)

        prompt = f"""다음 블로그 포스트를 {target_duration} 길이의 YouTube 영상 스크립트로 변환해주세요.

제목: {title}
키워드: {', '.join(keywords)}
주요 포인트: {', '.join(key_points[:3])}

콘텐츠:
{text_content[:2000]}

다음 형식으로 작성해주세요:

1. HOOK (첫 15초, 시청자 주목 끌기):
[훅 내용]

2. INTRO (30초-1분):
[인트로 내용]

3. MAIN CONTENT (섹션별로):
[00:00-00:00] 섹션 제목
- 설명할 내용
- 화면에 보여줄 것 (visual cue)

4. OUTRO:
[아웃트로 내용]

5. CTA (Call to Action):
[구독, 좋아요, 댓글 유도]

6. 썸네일 아이디어 3가지:
- 아이디어 1
- 아이디어 2
- 아이디어 3

한국어로 작성하고, 구어체로 자연스럽게 작성해주세요."""

        llm_service = await self._get_llm_service()
        response = await llm_service.generate_text(prompt, max_tokens=2000)

        # 응답 파싱 (간단한 파싱)
        lines = response.strip().split('\n')

        # 기본 구조 생성 (실제로는 더 정교한 파싱 필요)
        script = YouTubeScript(
            title=title,
            hook=self._extract_section(response, "HOOK", "INTRO"),
            intro=self._extract_section(response, "INTRO", "MAIN"),
            main_points=self._parse_main_points(response),
            outro=self._extract_section(response, "OUTRO", "CTA"),
            cta=self._extract_section(response, "CTA", "썸네일"),
            estimated_duration=target_duration,
            keywords=keywords,
            thumbnail_ideas=self._extract_list_items(response, "썸네일")
        )

        logger.info(f"YouTube script created with {len(script.main_points)} main points")
        return script

    async def to_infographic_data(
        self,
        title: str,
        content: str,
        keywords: List[str]
    ) -> InfographicData:
        """블로그 포스트를 인포그래픽 데이터로 변환"""
        logger.info(f"Converting blog post to infographic data: {title}")

        text_content = self._extract_text_from_html(content)

        prompt = f"""다음 블로그 포스트를 인포그래픽으로 만들기 위한 데이터로 변환해주세요.

제목: {title}
키워드: {', '.join(keywords)}

콘텐츠:
{text_content[:1500]}

다음 형식으로 작성해주세요:

1. 메인 제목:
[짧고 임팩트 있는 제목]

2. 서브 제목:
[부연 설명 한 줄]

3. 주요 통계/수치 (3-5개):
- 통계1: 수치 (예: 80% 증가)
- 통계2: 수치
- 통계3: 수치

4. 섹션 (3-4개):
섹션1 제목:
- 포인트 1
- 포인트 2
- 포인트 3

5. 핵심 정리 (Key Takeaways, 3개):
- 핵심 1
- 핵심 2
- 핵심 3

6. 추천 컬러 스킴:
[예: 파란색-오렌지, 녹색-회색 등]

7. 레이아웃 타입:
[vertical/horizontal/timeline 중 하나]

숫자와 통계를 강조하고, 시각적으로 표현하기 쉬운 형태로 작성해주세요."""

        llm_service = await self._get_llm_service()
        response = await llm_service.generate_text(prompt, max_tokens=1500)

        # 응답 파싱
        infographic = InfographicData(
            title=self._extract_section(response, "메인 제목", "서브 제목").strip(),
            subtitle=self._extract_section(response, "서브 제목", "주요 통계").strip(),
            main_stats=self._parse_stats(response),
            sections=self._parse_sections(response),
            key_takeaways=self._extract_list_items(response, "핵심 정리"),
            color_scheme=self._extract_section(response, "추천 컬러", "레이아웃").strip(),
            layout_type=self._extract_section(response, "레이아웃 타입", "").strip().split()[0].lower()
        )

        logger.info(f"Infographic data created with {len(infographic.sections)} sections")
        return infographic

    async def to_social_media_cards(
        self,
        title: str,
        content: str,
        keywords: List[str],
        platforms: List[str] = ["instagram", "facebook", "linkedin"]
    ) -> List[SocialMediaCard]:
        """블로그 포스트를 소셜 미디어 카드로 변환 (여러 버전)"""
        logger.info(f"Converting blog post to social media cards: {title}")

        text_content = self._extract_text_from_html(content)
        cards = []

        for platform in platforms:
            platform_specs = {
                "instagram": {"max_chars": 2200, "style": "시각적이고 감성적인", "format": "정사각형"},
                "facebook": {"max_chars": 5000, "style": "친근하고 대화체", "format": "가로형"},
                "linkedin": {"max_chars": 3000, "style": "전문적이고 인사이트 있는", "format": "가로형"}
            }

            spec = platform_specs.get(platform, platform_specs["instagram"])

            prompt = f"""다음 블로그 포스트를 {platform.upper()} 소셜 미디어 카드 텍스트로 변환해주세요.

제목: {title}
키워드: {', '.join(keywords)}

콘텐츠:
{text_content[:1000]}

요구사항:
- 스타일: {spec['style']}
- 최대 길이: {spec['max_chars']} 자
- 형식: {spec['format']} 이미지에 어울리는 텍스트

다음 형식으로 작성해주세요:

1. 메인 헤드라인 (한 줄, 임팩트):
[헤드라인]

2. 서브 헤드라인 (부연 설명):
[서브헤드라인]

3. 핵심 포인트 (3-4개, 짧게):
- 포인트 1
- 포인트 2
- 포인트 3

4. Call to Action:
[CTA 문구]

5. 해시태그 (5-7개):
#태그1 #태그2 #태그3

6. 시각 요소 제안:
- 배경 이미지/색상 제안
- 아이콘/그래픽 제안
- 텍스트 배치 제안

{platform}에 최적화된 내용으로 작성해주세요."""

            llm_service = await self._get_llm_service()
            response = await llm_service.generate_text(prompt, max_tokens=1000)

            # 응답 파싱
            headline = self._extract_section(response, "메인 헤드라인", "서브 헤드라인").strip()
            subheadline = self._extract_section(response, "서브 헤드라인", "핵심 포인트").strip()
            key_points = self._extract_list_items(response, "핵심 포인트", "Call to Action")
            cta = self._extract_section(response, "Call to Action", "해시태그").strip()
            hashtags = self._extract_hashtags(response)
            visual_elements = self._extract_list_items(response, "시각 요소")

            full_text = f"{headline}\n\n{subheadline}\n\n" + "\n".join(f"✓ {p}" for p in key_points) + f"\n\n{cta}\n\n" + " ".join(hashtags)

            card = SocialMediaCard(
                platform=platform,
                headline=headline,
                subheadline=subheadline,
                key_points=key_points,
                call_to_action=cta,
                hashtags=hashtags,
                visual_elements=visual_elements,
                character_count=len(full_text)
            )

            cards.append(card)
            logger.info(f"Created {platform} card with {card.character_count} characters")

        return cards

    async def to_podcast_script(
        self,
        title: str,
        content: str,
        keywords: List[str],
        episode_number: Optional[int] = None,
        target_duration: str = "20-30분"
    ) -> PodcastScript:
        """블로그 포스트를 팟캐스트 스크립트로 변환"""
        logger.info(f"Converting blog post to podcast script: {title}")

        text_content = self._extract_text_from_html(content)
        key_points = self._extract_key_points(content)

        prompt = f"""다음 블로그 포스트를 {target_duration} 팟캐스트 에피소드 스크립트로 변환해주세요.

제목: {title}
키워드: {', '.join(keywords)}
주요 포인트: {', '.join(key_points[:3])}

콘텐츠:
{text_content[:2000]}

다음 형식으로 작성해주세요:

1. 인트로 음악 큐:
[음악 스타일 설명]

2. 호스트 인트로:
[환영 멘트와 에피소드 소개]

3. 세그먼트 (3-5개):
세그먼트1 (5분):
- 토킹 포인트 1
- 토킹 포인트 2

세그먼트2 (7분):
- 토킹 포인트 1
- 토킹 포인트 2

4. 게스트 인터뷰 질문 (있다면, 5개):
- 질문 1
- 질문 2

5. 아웃트로:
[마무리 멘트]

6. 쇼노트 (Show Notes, 5-7개):
- [00:00] 인트로
- [02:30] 토픽 1
- [10:15] 토픽 2

자연스러운 구어체로 작성하고, 청취자와 대화하는 느낌으로 작성해주세요."""

        llm_service = await self._get_llm_service()
        response = await llm_service.generate_text(prompt, max_tokens=2000)

        # 응답 파싱
        script = PodcastScript(
            title=title,
            episode_number=episode_number,
            intro_music_cue=self._extract_section(response, "인트로 음악", "호스트 인트로").strip(),
            host_intro=self._extract_section(response, "호스트 인트로", "세그먼트").strip(),
            segments=self._parse_podcast_segments(response),
            guest_questions=self._extract_list_items(response, "게스트 인터뷰"),
            outro=self._extract_section(response, "아웃트로", "쇼노트").strip(),
            show_notes=self._extract_list_items(response, "쇼노트"),
            estimated_duration=target_duration
        )

        logger.info(f"Podcast script created with {len(script.segments)} segments")
        return script

    async def to_twitter_thread(
        self,
        title: str,
        content: str,
        keywords: List[str],
        max_tweets: int = 10
    ) -> TwitterThread:
        """블로그 포스트를 Twitter 스레드로 변환"""
        logger.info(f"Converting blog post to Twitter thread: {title}")

        text_content = self._extract_text_from_html(content)
        key_points = self._extract_key_points(content)

        prompt = f"""다음 블로그 포스트를 Twitter 스레드로 변환해주세요.

제목: {title}
키워드: {', '.join(keywords)}
주요 포인트: {', '.join(key_points[:5])}

콘텐츠:
{text_content[:1500]}

요구사항:
- 최대 {max_tweets}개 트윗
- 각 트윗은 280자 이내
- 첫 트윗은 강력한 훅
- 마지막 트윗은 CTA
- 이모지 적절히 사용

다음 형식으로 작성해주세요:

1/ (훅 트윗 - 주목 끌기)
[첫 트윗 내용]

2/
[두 번째 트윗]

3/
[세 번째 트윗]

...

[마지막 트윗 - CTA]

각 트윗은 독립적으로도 의미가 있어야 하고, 연결되어도 흐름이 자연스러워야 합니다."""

        llm_service = await self._get_llm_service()
        response = await llm_service.generate_text(prompt, max_tokens=1500)

        # 트윗 파싱
        tweets = self._parse_tweets(response)

        if len(tweets) < 3:
            # 최소 3개 트윗 보장
            tweets = [
                f"🧵 {title}",
                text_content[:250] + "...",
                "자세한 내용은 블로그에서 확인하세요! 👇"
            ]

        thread = TwitterThread(
            hook_tweet=tweets[0],
            thread_tweets=tweets[1:-2] if len(tweets) > 3 else tweets[1:-1],
            conclusion_tweet=tweets[-2] if len(tweets) > 2 else tweets[-1],
            cta_tweet=tweets[-1] if len(tweets) > 2 else f"더 알아보기 👉 {' '.join('#' + k for k in keywords[:3])}",
            total_tweets=len(tweets),
            estimated_engagement="High" if len(tweets) >= 5 else "Medium"
        )

        logger.info(f"Twitter thread created with {thread.total_tweets} tweets")
        return thread

    # Helper methods for parsing

    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> str:
        """텍스트에서 특정 섹션 추출"""
        try:
            start_idx = text.find(start_marker)
            if start_idx == -1:
                return ""

            start_idx = text.find('\n', start_idx) + 1

            if end_marker:
                end_idx = text.find(end_marker, start_idx)
                if end_idx == -1:
                    return text[start_idx:].strip()
                return text[start_idx:end_idx].strip()
            else:
                return text[start_idx:].strip()
        except Exception as e:
            logger.error(f"Error extracting section: {e}")
            return ""

    def _extract_list_items(self, text: str, section_marker: str, end_marker: str = None) -> List[str]:
        """섹션에서 리스트 아이템 추출"""
        section = self._extract_section(text, section_marker, end_marker or "")

        items = []
        for line in section.split('\n'):
            line = line.strip()
            # - 또는 숫자로 시작하는 리스트 아이템
            if line.startswith('-') or line.startswith('•') or (len(line) > 2 and line[0].isdigit() and line[1] in '.):'):
                # 리스트 마커 제거
                item = re.sub(r'^[-•\d.):]\s*', '', line).strip()
                if item:
                    items.append(item)

        return items

    def _extract_hashtags(self, text: str) -> List[str]:
        """텍스트에서 해시태그 추출"""
        hashtags = re.findall(r'#\w+', text)
        return hashtags[:7]  # 최대 7개

    def _parse_main_points(self, text: str) -> List[Dict[str, str]]:
        """YouTube 스크립트의 메인 포인트 파싱"""
        points = []

        # [00:00-00:00] 패턴 찾기
        pattern = r'\[(\d{2}:\d{2})-(\d{2}:\d{2})\]\s*(.*?)(?=\[|$)'
        matches = re.finditer(pattern, text, re.DOTALL)

        for match in matches:
            start_time, end_time, content = match.groups()
            points.append({
                "timestamp": f"{start_time}-{end_time}",
                "content": content.strip()[:200],
                "visual_cue": "화면 전환"
            })

        # 패턴이 없으면 기본 구조 생성
        if not points:
            points = [
                {"timestamp": "00:00-02:00", "content": "인트로", "visual_cue": "타이틀 화면"},
                {"timestamp": "02:00-10:00", "content": "메인 콘텐츠", "visual_cue": "슬라이드"},
                {"timestamp": "10:00-12:00", "content": "아웃트로", "visual_cue": "구독 유도"}
            ]

        return points

    def _parse_stats(self, text: str) -> List[Dict[str, Any]]:
        """인포그래픽 통계 파싱"""
        stats = []
        section = self._extract_section(text, "주요 통계", "섹션")

        for line in section.split('\n'):
            if ':' in line:
                parts = line.split(':', 1)
                label = parts[0].strip('- •').strip()
                value = parts[1].strip()

                if label and value:
                    stats.append({
                        "label": label,
                        "value": value,
                        "icon": "📊"  # 기본 아이콘
                    })

        return stats[:5]

    def _parse_sections(self, text: str) -> List[Dict[str, Any]]:
        """인포그래픽 섹션 파싱"""
        sections = []

        # 섹션 패턴 찾기
        pattern = r'섹션\d+\s+(.*?):\s*((?:[-•]\s*.*?\n?)+)'
        matches = re.finditer(pattern, text, re.MULTILINE)

        for match in matches:
            title, points_text = match.groups()
            points = [p.strip('- •\n ') for p in points_text.split('\n') if p.strip()]

            sections.append({
                "title": title.strip(),
                "points": points[:4],  # 최대 4개 포인트
                "visual_type": "bullet"
            })

        return sections

    def _parse_podcast_segments(self, text: str) -> List[Dict[str, Any]]:
        """팟캐스트 세그먼트 파싱"""
        segments = []

        # 세그먼트 패턴 찾기
        pattern = r'세그먼트\d+\s*\((\d+)분\):\s*((?:[-•]\s*.*?\n?)+)'
        matches = re.finditer(pattern, text, re.MULTILINE)

        for match in matches:
            duration, points_text = match.groups()
            points = [p.strip('- •\n ') for p in points_text.split('\n') if p.strip()]

            segments.append({
                "title": f"세그먼트 {len(segments) + 1}",
                "talking_points": points,
                "duration": f"{duration}분"
            })

        return segments

    def _parse_tweets(self, text: str) -> List[str]:
        """Twitter 스레드 파싱"""
        tweets = []

        # 숫자/ 패턴으로 트윗 분리
        lines = text.split('\n')
        current_tweet = ""

        for line in lines:
            # 새 트윗 시작
            if re.match(r'^\d+/', line):
                if current_tweet:
                    # 280자로 제한
                    tweet = current_tweet.strip()[:280]
                    tweets.append(tweet)
                current_tweet = re.sub(r'^\d+/\s*', '', line)
            else:
                current_tweet += " " + line

        # 마지막 트윗 추가
        if current_tweet:
            tweet = current_tweet.strip()[:280]
            tweets.append(tweet)

        return tweets


# 싱글톤 인스턴스
_service_instance = None

def get_content_repurposing_service() -> ContentRepurposingService:
    """콘텐츠 재활용 서비스 싱글톤 인스턴스 반환"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ContentRepurposingService()
    return _service_instance
