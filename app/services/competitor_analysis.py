"""
경쟁자 분석 서비스
RSS 피드 모니터링, 키워드 갭 분석, 콘텐츠 갭 분석
"""
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import feedparser
import re
from bs4 import BeautifulSoup
from collections import Counter
import requests

from app.core.config import settings
from app.services.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


@dataclass
class CompetitorBlog:
    """경쟁 블로그 정보"""
    name: str
    url: str
    rss_feed: str
    domain_authority: Optional[int] = None
    monthly_traffic: Optional[int] = None


@dataclass
class BlogPost:
    """블로그 포스트"""
    title: str
    url: str
    published_date: str
    excerpt: str
    keywords: List[str]
    estimated_traffic: Optional[int] = None


@dataclass
class KeywordGap:
    """키워드 갭 분석 결과"""
    keyword: str
    competitor_rank: int
    our_rank: Optional[int]
    search_volume: int
    difficulty: str
    opportunity_score: float
    suggested_topics: List[str]


@dataclass
class ContentGap:
    """콘텐츠 갭 분석 결과"""
    topic: str
    competitor_posts: List[BlogPost]
    our_coverage: str  # none, partial, full
    opportunity_score: float
    suggested_angle: str
    estimated_traffic: int


@dataclass
class CompetitorReport:
    """경쟁자 분석 리포트"""
    competitor_name: str
    analysis_date: str
    recent_posts: List[BlogPost]
    keyword_gaps: List[KeywordGap]
    content_gaps: List[ContentGap]
    seo_comparison: Dict[str, Any]
    recommendations: List[str]


class CompetitorAnalysisService:
    """경쟁자 분석 서비스"""

    def __init__(self):
        self.llm_service = None

    async def _get_llm_service(self):
        """LLM 서비스 인스턴스 가져오기"""
        if self.llm_service is None:
            self.llm_service = LLMFactory.create(settings.default_llm_provider)
        return self.llm_service

    def _extract_keywords_from_text(self, text: str, max_keywords: int = 10) -> List[str]:
        """텍스트에서 키워드 추출 (간단한 버전)"""
        # 불용어 제거
        stop_words = {'은', '는', '이', '가', '을', '를', '의', '에', '와', '과', '도', '로', '으로', '에서', '하다', '있다', '되다', '않다', '없다', '것'}

        # 한글 단어만 추출 (2글자 이상)
        words = re.findall(r'[가-힣]{2,}', text.lower())

        # 불용어 제거 및 빈도 계산
        filtered_words = [w for w in words if w not in stop_words]
        word_freq = Counter(filtered_words)

        # 상위 키워드 반환
        top_keywords = [word for word, _ in word_freq.most_common(max_keywords)]

        return top_keywords

    async def fetch_competitor_posts(
        self,
        rss_feed_url: str,
        days: int = 30
    ) -> List[BlogPost]:
        """경쟁자 블로그의 최근 포스트 가져오기 (RSS)"""
        logger.info(f"Fetching posts from RSS feed: {rss_feed_url}")

        try:
            # RSS 피드 파싱
            feed = feedparser.parse(rss_feed_url)

            posts = []
            cutoff_date = datetime.now() - timedelta(days=days)

            for entry in feed.entries[:20]:  # 최대 20개
                try:
                    # 발행일 파싱
                    published = entry.get('published_parsed') or entry.get('updated_parsed')
                    if published:
                        pub_date = datetime(*published[:6])
                        if pub_date < cutoff_date:
                            continue
                        pub_date_str = pub_date.isoformat()
                    else:
                        pub_date_str = datetime.now().isoformat()

                    # 요약문 추출
                    excerpt = entry.get('summary', entry.get('description', ''))
                    if excerpt:
                        # HTML 태그 제거
                        soup = BeautifulSoup(excerpt, 'html.parser')
                        excerpt = soup.get_text()[:200]

                    # 제목과 요약에서 키워드 추출
                    text = f"{entry.title} {excerpt}"
                    keywords = self._extract_keywords_from_text(text, max_keywords=5)

                    post = BlogPost(
                        title=entry.title,
                        url=entry.link,
                        published_date=pub_date_str,
                        excerpt=excerpt,
                        keywords=keywords,
                        estimated_traffic=None
                    )

                    posts.append(post)

                except Exception as e:
                    logger.warning(f"Error parsing entry: {e}")
                    continue

            logger.info(f"Fetched {len(posts)} posts from competitor")
            return posts

        except Exception as e:
            logger.error(f"Error fetching RSS feed: {e}")
            return []

    async def analyze_keyword_gaps(
        self,
        our_keywords: List[str],
        competitor_keywords: List[str]
    ) -> List[KeywordGap]:
        """키워드 갭 분석"""
        logger.info("Analyzing keyword gaps")

        our_keywords_set = set(k.lower() for k in our_keywords)
        competitor_keywords_set = set(k.lower() for k in competitor_keywords)

        # 경쟁자는 있지만 우리는 없는 키워드
        gap_keywords = competitor_keywords_set - our_keywords_set

        gaps = []
        for keyword in list(gap_keywords)[:20]:  # 최대 20개
            # 기회 점수 계산 (간단한 버전)
            keyword_length = len(keyword)
            opportunity_score = min(100, (keyword_length * 10) + 50)

            # 난이도 추정
            if keyword_length <= 3:
                difficulty = "Easy"
            elif keyword_length <= 5:
                difficulty = "Medium"
            else:
                difficulty = "Hard"

            gap = KeywordGap(
                keyword=keyword,
                competitor_rank=1,  # 시뮬레이션
                our_rank=None,
                search_volume=1000,  # 시뮬레이션
                difficulty=difficulty,
                opportunity_score=opportunity_score,
                suggested_topics=[
                    f"{keyword} 완벽 가이드",
                    f"{keyword} 초보자 튜토리얼",
                    f"{keyword} 베스트 프랙티스"
                ]
            )
            gaps.append(gap)

        # 기회 점수로 정렬
        gaps.sort(key=lambda x: x.opportunity_score, reverse=True)

        logger.info(f"Found {len(gaps)} keyword gaps")
        return gaps

    async def analyze_content_gaps(
        self,
        competitor_posts: List[BlogPost],
        our_topics: List[str]
    ) -> List[ContentGap]:
        """콘텐츠 갭 분석"""
        logger.info("Analyzing content gaps")

        # 경쟁자 포스트를 주제별로 그룹화
        topic_groups = {}
        for post in competitor_posts:
            # 주요 키워드를 주제로 사용
            if post.keywords:
                main_topic = post.keywords[0]
                if main_topic not in topic_groups:
                    topic_groups[main_topic] = []
                topic_groups[main_topic].append(post)

        gaps = []
        our_topics_lower = [t.lower() for t in our_topics]

        for topic, posts in topic_groups.items():
            # 우리가 다루지 않은 주제인지 확인
            coverage = "none"
            for our_topic in our_topics_lower:
                if topic.lower() in our_topic or our_topic in topic.lower():
                    coverage = "partial"
                    break

            if coverage == "none":
                # 기회 점수 계산
                post_count = len(posts)
                opportunity_score = min(100, post_count * 20 + 40)

                # AI로 제안 각도 생성
                llm_service = await self._get_llm_service()
                angle_prompt = f"""다음 주제에 대한 차별화된 콘텐츠 각도를 제안해주세요:

주제: {topic}
경쟁자 포스트 수: {post_count}

한 문장으로 간결하게 제안해주세요."""

                suggested_angle = await llm_service.generate_text(angle_prompt, max_tokens=100)

                gap = ContentGap(
                    topic=topic,
                    competitor_posts=posts[:3],  # 최대 3개만
                    our_coverage=coverage,
                    opportunity_score=opportunity_score,
                    suggested_angle=suggested_angle.strip(),
                    estimated_traffic=post_count * 500  # 시뮬레이션
                )
                gaps.append(gap)

        # 기회 점수로 정렬
        gaps.sort(key=lambda x: x.opportunity_score, reverse=True)

        logger.info(f"Found {len(gaps)} content gaps")
        return gaps[:10]  # 상위 10개만

    async def generate_competitor_report(
        self,
        competitor: CompetitorBlog,
        our_keywords: List[str],
        our_topics: List[str]
    ) -> CompetitorReport:
        """경쟁자 종합 분석 리포트 생성"""
        logger.info(f"Generating report for competitor: {competitor.name}")

        # 1. 최근 포스트 가져오기
        recent_posts = await self.fetch_competitor_posts(competitor.rss_feed, days=30)

        # 2. 경쟁자 키워드 추출
        competitor_keywords = []
        for post in recent_posts:
            competitor_keywords.extend(post.keywords)
        competitor_keywords = list(set(competitor_keywords))

        # 3. 키워드 갭 분석
        keyword_gaps = await self.analyze_keyword_gaps(our_keywords, competitor_keywords)

        # 4. 콘텐츠 갭 분석
        content_gaps = await self.analyze_content_gaps(recent_posts, our_topics)

        # 5. SEO 비교 (간단한 버전)
        seo_comparison = {
            "our_domain_authority": 45,  # 시뮬레이션
            "competitor_domain_authority": competitor.domain_authority or 60,
            "our_monthly_posts": 20,
            "competitor_monthly_posts": len(recent_posts),
            "our_avg_post_length": 1500,
            "competitor_avg_post_length": 1200
        }

        # 6. 권장 사항 생성
        recommendations = []

        if len(keyword_gaps) > 0:
            top_gap = keyword_gaps[0]
            recommendations.append(f"키워드 '{top_gap.keyword}'에 대한 콘텐츠 작성 권장 (기회 점수: {top_gap.opportunity_score:.0f})")

        if len(content_gaps) > 0:
            top_content_gap = content_gaps[0]
            recommendations.append(f"주제 '{top_content_gap.topic}'에 대한 심화 콘텐츠 작성 권장")

        if seo_comparison["competitor_monthly_posts"] > seo_comparison["our_monthly_posts"]:
            recommendations.append(f"월간 포스트 수를 {seo_comparison['competitor_monthly_posts']}개 이상으로 증가 권장")

        recommendations.append("경쟁자의 인기 포스트 주제를 참고하여 유사 콘텐츠 작성")
        recommendations.append("백링크 구축을 통해 도메인 권위도 향상")

        report = CompetitorReport(
            competitor_name=competitor.name,
            analysis_date=datetime.now().isoformat(),
            recent_posts=recent_posts[:10],  # 최대 10개
            keyword_gaps=keyword_gaps[:10],
            content_gaps=content_gaps,
            seo_comparison=seo_comparison,
            recommendations=recommendations
        )

        logger.info(f"Generated comprehensive report for {competitor.name}")
        return report

    async def suggest_content_ideas(
        self,
        competitor_posts: List[BlogPost],
        num_ideas: int = 5
    ) -> List[Dict[str, str]]:
        """경쟁자 포스트 기반 콘텐츠 아이디어 제안"""
        logger.info("Suggesting content ideas based on competitor posts")

        # 경쟁자 포스트 제목들 수집
        titles = [post.title for post in competitor_posts[:10]]
        titles_text = "\n".join(f"- {title}" for title in titles)

        prompt = f"""다음은 경쟁 블로그의 최근 인기 포스트 제목들입니다:

{titles_text}

이를 참고하여 차별화된 콘텐츠 아이디어 {num_ideas}개를 제안해주세요.

다음 형식으로 작성해주세요:

1. [제목]
   각도: [차별화 포인트]

2. [제목]
   각도: [차별화 포인트]

각 아이디어는 경쟁 포스트와 다른 독특한 관점을 제시해야 합니다."""

        llm_service = await self._get_llm_service()
        response = await llm_service.generate_text(prompt, max_tokens=1000)

        # 응답 파싱
        ideas = []
        lines = response.strip().split('\n')

        current_title = ""
        current_angle = ""

        for line in lines:
            line = line.strip()

            if re.match(r'^\d+\.', line):
                # 이전 아이디어 저장
                if current_title:
                    ideas.append({
                        "title": current_title,
                        "angle": current_angle
                    })

                # 새 아이디어 시작
                current_title = re.sub(r'^\d+\.\s*', '', line)
                current_angle = ""

            elif line.startswith('각도:'):
                current_angle = line.replace('각도:', '').strip()

        # 마지막 아이디어 저장
        if current_title:
            ideas.append({
                "title": current_title,
                "angle": current_angle
            })

        logger.info(f"Generated {len(ideas)} content ideas")
        return ideas[:num_ideas]


# 싱글톤 인스턴스
_service_instance = None

def get_competitor_analysis_service() -> CompetitorAnalysisService:
    """경쟁자 분석 서비스 싱글톤 인스턴스 반환"""
    global _service_instance
    if _service_instance is None:
        _service_instance = CompetitorAnalysisService()
    return _service_instance
