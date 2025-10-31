"""
콘텐츠 재활용 API 라우트
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from app.services.content_repurposing import (
    get_content_repurposing_service,
    YouTubeScript,
    InfographicData,
    SocialMediaCard,
    PodcastScript,
    TwitterThread
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content-repurposing", tags=["content-repurposing"])

# Request Models

class BlogPostInput(BaseModel):
    """블로그 포스트 입력 데이터"""
    title: str = Field(..., description="블로그 포스트 제목")
    content: str = Field(..., description="블로그 포스트 HTML 콘텐츠")
    keywords: List[str] = Field(default_factory=list, description="키워드 리스트")


class YouTubeScriptRequest(BlogPostInput):
    """YouTube 스크립트 생성 요청"""
    target_duration: str = Field(default="10-15분", description="목표 영상 길이")


class SocialMediaCardsRequest(BlogPostInput):
    """소셜 미디어 카드 생성 요청"""
    platforms: List[str] = Field(
        default=["instagram", "facebook", "linkedin"],
        description="플랫폼 리스트"
    )


class PodcastScriptRequest(BlogPostInput):
    """팟캐스트 스크립트 생성 요청"""
    episode_number: Optional[int] = Field(default=None, description="에피소드 번호")
    target_duration: str = Field(default="20-30분", description="목표 길이")


class TwitterThreadRequest(BlogPostInput):
    """Twitter 스레드 생성 요청"""
    max_tweets: int = Field(default=10, description="최대 트윗 개수")


# Response Models

class YouTubeScriptResponse(BaseModel):
    """YouTube 스크립트 응답"""
    title: str
    hook: str
    intro: str
    main_points: List[Dict[str, str]]
    outro: str
    cta: str
    estimated_duration: str
    keywords: List[str]
    thumbnail_ideas: List[str]


class InfographicDataResponse(BaseModel):
    """인포그래픽 데이터 응답"""
    title: str
    subtitle: str
    main_stats: List[Dict[str, Any]]
    sections: List[Dict[str, Any]]
    key_takeaways: List[str]
    color_scheme: str
    layout_type: str


class SocialMediaCardResponse(BaseModel):
    """소셜 미디어 카드 응답"""
    platform: str
    headline: str
    subheadline: str
    key_points: List[str]
    call_to_action: str
    hashtags: List[str]
    visual_elements: List[str]
    character_count: int


class PodcastScriptResponse(BaseModel):
    """팟캐스트 스크립트 응답"""
    title: str
    episode_number: Optional[int]
    intro_music_cue: str
    host_intro: str
    segments: List[Dict[str, Any]]
    guest_questions: List[str]
    outro: str
    show_notes: List[str]
    estimated_duration: str


class TwitterThreadResponse(BaseModel):
    """Twitter 스레드 응답"""
    hook_tweet: str
    thread_tweets: List[str]
    conclusion_tweet: str
    cta_tweet: str
    total_tweets: int
    estimated_engagement: str


# API Endpoints

@router.post("/youtube-script", response_model=YouTubeScriptResponse)
async def create_youtube_script(request: YouTubeScriptRequest):
    """
    블로그 포스트를 YouTube 스크립트로 변환

    - **title**: 블로그 포스트 제목
    - **content**: HTML 콘텐츠
    - **keywords**: 키워드 리스트
    - **target_duration**: 목표 영상 길이 (예: "10-15분")

    Returns:
    - 구조화된 YouTube 스크립트 (훅, 인트로, 메인, 아웃트로, CTA)
    - 썸네일 아이디어
    """
    try:
        logger.info(f"Creating YouTube script for: {request.title}")
        service = get_content_repurposing_service()

        script = await service.to_youtube_script(
            title=request.title,
            content=request.content,
            keywords=request.keywords,
            target_duration=request.target_duration
        )

        return YouTubeScriptResponse(
            title=script.title,
            hook=script.hook,
            intro=script.intro,
            main_points=script.main_points,
            outro=script.outro,
            cta=script.cta,
            estimated_duration=script.estimated_duration,
            keywords=script.keywords,
            thumbnail_ideas=script.thumbnail_ideas
        )

    except Exception as e:
        logger.error(f"Error creating YouTube script: {e}")
        raise HTTPException(status_code=500, detail=f"YouTube 스크립트 생성 실패: {str(e)}")


@router.post("/infographic", response_model=InfographicDataResponse)
async def create_infographic_data(request: BlogPostInput):
    """
    블로그 포스트를 인포그래픽 데이터로 변환

    - **title**: 블로그 포스트 제목
    - **content**: HTML 콘텐츠
    - **keywords**: 키워드 리스트

    Returns:
    - 인포그래픽 디자인을 위한 구조화된 데이터
    - 주요 통계, 섹션, 핵심 정리
    - 컬러 스킴 및 레이아웃 제안
    """
    try:
        logger.info(f"Creating infographic data for: {request.title}")
        service = get_content_repurposing_service()

        infographic = await service.to_infographic_data(
            title=request.title,
            content=request.content,
            keywords=request.keywords
        )

        return InfographicDataResponse(
            title=infographic.title,
            subtitle=infographic.subtitle,
            main_stats=infographic.main_stats,
            sections=infographic.sections,
            key_takeaways=infographic.key_takeaways,
            color_scheme=infographic.color_scheme,
            layout_type=infographic.layout_type
        )

    except Exception as e:
        logger.error(f"Error creating infographic data: {e}")
        raise HTTPException(status_code=500, detail=f"인포그래픽 데이터 생성 실패: {str(e)}")


@router.post("/social-media-cards", response_model=List[SocialMediaCardResponse])
async def create_social_media_cards(request: SocialMediaCardsRequest):
    """
    블로그 포스트를 소셜 미디어 카드로 변환 (여러 플랫폼)

    - **title**: 블로그 포스트 제목
    - **content**: HTML 콘텐츠
    - **keywords**: 키워드 리스트
    - **platforms**: 플랫폼 리스트 (instagram, facebook, linkedin)

    Returns:
    - 각 플랫폼에 최적화된 소셜 미디어 카드 데이터
    - 헤드라인, 핵심 포인트, CTA, 해시태그
    - 시각 요소 제안
    """
    try:
        logger.info(f"Creating social media cards for: {request.title}")
        service = get_content_repurposing_service()

        cards = await service.to_social_media_cards(
            title=request.title,
            content=request.content,
            keywords=request.keywords,
            platforms=request.platforms
        )

        return [
            SocialMediaCardResponse(
                platform=card.platform,
                headline=card.headline,
                subheadline=card.subheadline,
                key_points=card.key_points,
                call_to_action=card.call_to_action,
                hashtags=card.hashtags,
                visual_elements=card.visual_elements,
                character_count=card.character_count
            )
            for card in cards
        ]

    except Exception as e:
        logger.error(f"Error creating social media cards: {e}")
        raise HTTPException(status_code=500, detail=f"소셜 미디어 카드 생성 실패: {str(e)}")


@router.post("/podcast-script", response_model=PodcastScriptResponse)
async def create_podcast_script(request: PodcastScriptRequest):
    """
    블로그 포스트를 팟캐스트 스크립트로 변환

    - **title**: 블로그 포스트 제목
    - **content**: HTML 콘텐츠
    - **keywords**: 키워드 리스트
    - **episode_number**: 에피소드 번호 (선택사항)
    - **target_duration**: 목표 길이 (예: "20-30분")

    Returns:
    - 구조화된 팟캐스트 스크립트
    - 세그먼트별 토킹 포인트
    - 쇼노트 (타임스탬프 포함)
    """
    try:
        logger.info(f"Creating podcast script for: {request.title}")
        service = get_content_repurposing_service()

        script = await service.to_podcast_script(
            title=request.title,
            content=request.content,
            keywords=request.keywords,
            episode_number=request.episode_number,
            target_duration=request.target_duration
        )

        return PodcastScriptResponse(
            title=script.title,
            episode_number=script.episode_number,
            intro_music_cue=script.intro_music_cue,
            host_intro=script.host_intro,
            segments=script.segments,
            guest_questions=script.guest_questions,
            outro=script.outro,
            show_notes=script.show_notes,
            estimated_duration=script.estimated_duration
        )

    except Exception as e:
        logger.error(f"Error creating podcast script: {e}")
        raise HTTPException(status_code=500, detail=f"팟캐스트 스크립트 생성 실패: {str(e)}")


@router.post("/twitter-thread", response_model=TwitterThreadResponse)
async def create_twitter_thread(request: TwitterThreadRequest):
    """
    블로그 포스트를 Twitter 스레드로 변환

    - **title**: 블로그 포스트 제목
    - **content**: HTML 콘텐츠
    - **keywords**: 키워드 리스트
    - **max_tweets**: 최대 트윗 개수 (기본값: 10)

    Returns:
    - 연속된 트윗 스레드
    - 각 트윗은 280자 이내
    - 훅, 본문, 결론, CTA 구조
    """
    try:
        logger.info(f"Creating Twitter thread for: {request.title}")
        service = get_content_repurposing_service()

        thread = await service.to_twitter_thread(
            title=request.title,
            content=request.content,
            keywords=request.keywords,
            max_tweets=request.max_tweets
        )

        return TwitterThreadResponse(
            hook_tweet=thread.hook_tweet,
            thread_tweets=thread.thread_tweets,
            conclusion_tweet=thread.conclusion_tweet,
            cta_tweet=thread.cta_tweet,
            total_tweets=thread.total_tweets,
            estimated_engagement=thread.estimated_engagement
        )

    except Exception as e:
        logger.error(f"Error creating Twitter thread: {e}")
        raise HTTPException(status_code=500, detail=f"Twitter 스레드 생성 실패: {str(e)}")


@router.get("/formats")
async def get_available_formats():
    """
    사용 가능한 콘텐츠 변환 형식 조회

    Returns:
    - 지원하는 모든 변환 형식과 설명
    """
    return {
        "formats": [
            {
                "name": "youtube-script",
                "display_name": "YouTube 스크립트",
                "description": "블로그를 YouTube 영상 스크립트로 변환 (훅, 인트로, 메인, 아웃트로)",
                "estimated_time": "2-3분",
                "use_cases": ["영상 콘텐츠 제작", "교육 콘텐츠", "브랜드 스토리텔링"]
            },
            {
                "name": "infographic",
                "display_name": "인포그래픽",
                "description": "블로그를 시각화 가능한 인포그래픽 데이터로 변환",
                "estimated_time": "1-2분",
                "use_cases": ["SNS 공유", "통계 시각화", "빠른 정보 전달"]
            },
            {
                "name": "social-media-cards",
                "display_name": "소셜 미디어 카드",
                "description": "Instagram, Facebook, LinkedIn 등 플랫폼별 최적화 카드",
                "estimated_time": "1-2분",
                "use_cases": ["SNS 마케팅", "브랜드 홍보", "도달 범위 확대"]
            },
            {
                "name": "podcast-script",
                "display_name": "팟캐스트 스크립트",
                "description": "블로그를 오디오 콘텐츠 스크립트로 변환",
                "estimated_time": "2-3분",
                "use_cases": ["팟캐스트", "오디오북", "보이스 콘텐츠"]
            },
            {
                "name": "twitter-thread",
                "display_name": "Twitter 스레드",
                "description": "블로그를 연속 트윗 스레드로 변환 (280자 제한)",
                "estimated_time": "1분",
                "use_cases": ["Twitter 마케팅", "빠른 공유", "바이럴 콘텐츠"]
            }
        ],
        "total_formats": 5,
        "expected_roi": "콘텐츠 생산성 3-5배 증가"
    }


@router.post("/batch-convert")
async def batch_convert_content(request: BlogPostInput):
    """
    하나의 블로그 포스트를 모든 형식으로 일괄 변환

    - **title**: 블로그 포스트 제목
    - **content**: HTML 콘텐츠
    - **keywords**: 키워드 리스트

    Returns:
    - 모든 형식으로 변환된 결과
    """
    try:
        logger.info(f"Batch converting content: {request.title}")
        service = get_content_repurposing_service()

        # 모든 변환 동시 실행
        youtube_script = await service.to_youtube_script(
            request.title, request.content, request.keywords
        )

        infographic = await service.to_infographic_data(
            request.title, request.content, request.keywords
        )

        social_cards = await service.to_social_media_cards(
            request.title, request.content, request.keywords
        )

        podcast_script = await service.to_podcast_script(
            request.title, request.content, request.keywords
        )

        twitter_thread = await service.to_twitter_thread(
            request.title, request.content, request.keywords
        )

        return {
            "youtube_script": {
                "title": youtube_script.title,
                "hook": youtube_script.hook,
                "intro": youtube_script.intro,
                "main_points": youtube_script.main_points,
                "outro": youtube_script.outro,
                "cta": youtube_script.cta,
                "estimated_duration": youtube_script.estimated_duration,
                "thumbnail_ideas": youtube_script.thumbnail_ideas
            },
            "infographic": {
                "title": infographic.title,
                "subtitle": infographic.subtitle,
                "main_stats": infographic.main_stats,
                "sections": infographic.sections,
                "key_takeaways": infographic.key_takeaways,
                "color_scheme": infographic.color_scheme,
                "layout_type": infographic.layout_type
            },
            "social_media_cards": [
                {
                    "platform": card.platform,
                    "headline": card.headline,
                    "key_points": card.key_points,
                    "hashtags": card.hashtags
                }
                for card in social_cards
            ],
            "podcast_script": {
                "title": podcast_script.title,
                "host_intro": podcast_script.host_intro,
                "segments": podcast_script.segments,
                "estimated_duration": podcast_script.estimated_duration
            },
            "twitter_thread": {
                "hook_tweet": twitter_thread.hook_tweet,
                "thread_tweets": twitter_thread.thread_tweets,
                "total_tweets": twitter_thread.total_tweets
            },
            "conversion_time": "약 3-5분",
            "total_outputs": 5
        }

    except Exception as e:
        logger.error(f"Error in batch conversion: {e}")
        raise HTTPException(status_code=500, detail=f"일괄 변환 실패: {str(e)}")
