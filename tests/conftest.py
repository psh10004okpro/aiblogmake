"""
테스트 설정 및 공통 픽스처
"""

import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import Settings, settings
from app.core.database import Base, get_db
from app.main import app


# ==================== 테스트 설정 ====================

@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 픽스처 (세션 범위)"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """테스트용 설정 픽스처"""
    return Settings(
        app_env="testing",
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/1",
        log_level="DEBUG",
        # API 키는 모킹될 것이므로 더미 값 사용
        anthropic_api_key="test-anthropic-key",
        openai_api_key="test-openai-key",
        google_ads_client_id="test-google-client-id",
        google_ads_client_secret="test-google-client-secret",
        google_ads_developer_token="test-google-dev-token",
        naver_client_id="test-naver-client-id",
        naver_client_secret="test-naver-client-secret",
    )


# ==================== 데이터베이스 픽스처 ====================

@pytest.fixture(scope="function")
async def db_engine(test_settings):
    """테스트용 데이터베이스 엔진"""
    engine = create_async_engine(
        test_settings.database_url,
        echo=False,
        poolclass=NullPool,
    )
    
    # 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # 테이블 삭제
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """테스트용 데이터베이스 세션"""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def override_get_db(db_session):
    """데이터베이스 의존성 오버라이드"""
    async def _override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


# ==================== HTTP 클라이언트 픽스처 ====================

@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """동기 테스트 클라이언트"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """비동기 테스트 클라이언트"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ==================== Mock 서비스 픽스처 ====================

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic API 클라이언트"""
    with patch("anthropic.AsyncAnthropic") as mock:
        mock_instance = AsyncMock()
        mock_instance.messages.create = AsyncMock(return_value=MagicMock(
            content=[MagicMock(text="모킹된 Claude 응답입니다.")]
        ))
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI API 클라이언트"""
    with patch("openai.AsyncOpenAI") as mock:
        mock_instance = AsyncMock()
        
        # DALL-E 이미지 생성 모킹
        mock_instance.images.generate = AsyncMock(return_value=MagicMock(
            data=[MagicMock(url="https://example.com/test-image.png")]
        ))
        
        # GPT Vision 모킹
        mock_instance.chat.completions.create = AsyncMock(return_value=MagicMock(
            choices=[MagicMock(
                message=MagicMock(content="테스트 이미지 설명")
            )]
        ))
        
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_google_ads_client():
    """Mock Google Ads API 클라이언트"""
    mock_client = MagicMock()
    mock_service = MagicMock()
    
    # 키워드 아이디어 서비스 모킹
    mock_service.generate_keyword_ideas.return_value = [
        MagicMock(
            text="테스트 키워드",
            keyword_idea_metrics=MagicMock(
                avg_monthly_searches=1000,
                competition=0.5,
                competition_index=50,
                low_top_of_page_bid_micros=1000000,
                high_top_of_page_bid_micros=5000000,
            )
        )
    ]
    
    mock_client.get_service.return_value = mock_service
    
    with patch("google.ads.googleads.client.GoogleAdsClient.load_from_dict") as mock:
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_naver_api():
    """Mock Naver Search Ad API"""
    with patch("httpx.AsyncClient") as mock:
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value={
                "keywordList": [
                    {
                        "relKeyword": "테스트 키워드",
                        "monthlyPcQcCnt": 1000,
                        "monthlyMobileQcCnt": 2000,
                        "compIdx": "높음",
                    }
                ]
            })
        ))
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_pytrends():
    """Mock Google Trends (pytrends)"""
    with patch("pytrends.request.TrendReq") as mock:
        mock_instance = MagicMock()
        mock_instance.interest_over_time.return_value = MagicMock(
            empty=False,
            mean=MagicMock(return_value={"테스트 키워드": 50})
        )
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_playwright():
    """Mock Playwright for web scraping"""
    with patch("playwright.async_api.async_playwright") as mock:
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        
        # 페이지 동작 모킹
        mock_page.goto = AsyncMock()
        mock_page.fill = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.query_selector_all = AsyncMock(return_value=[
            MagicMock(inner_text=AsyncMock(return_value="추천 키워드 1")),
            MagicMock(inner_text=AsyncMock(return_value="추천 키워드 2")),
        ])
        
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        
        mock.__aenter__ = AsyncMock(return_value=mock_playwright)
        mock.__aexit__ = AsyncMock()
        
        yield mock


@pytest.fixture
def mock_wordpress_client():
    """Mock WordPress XML-RPC 클라이언트"""
    with patch("wordpress_xmlrpc.Client") as mock:
        mock_instance = MagicMock()
        mock_instance.call = MagicMock(return_value=MagicMock(id="123"))
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_redis():
    """Mock Redis 클라이언트"""
    with patch("redis.asyncio.from_url") as mock:
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(return_value=None)
        mock_instance.set = AsyncMock(return_value=True)
        mock_instance.delete = AsyncMock(return_value=1)
        mock_instance.exists = AsyncMock(return_value=0)
        mock.return_value = mock_instance
        yield mock_instance


# ==================== 테스트 데이터 팩토리 ====================

@pytest.fixture
def sample_keyword_data():
    """샘플 키워드 데이터"""
    return {
        "keyword": "블로그 작성법",
        "search_volume": 1000,
        "competition": 0.5,
        "cpc": 1.5,
        "trend": 0.2,
        "golden_score": 65.5,
        "related_keywords": ["블로그", "작성", "방법"],
        "source": "google_ads",
    }


@pytest.fixture
def sample_post_data():
    """샘플 포스트 데이터"""
    return {
        "title": "테스트 블로그 포스트",
        "content": "<h1>제목</h1><p>본문 내용입니다.</p>",
        "meta_description": "테스트 포스트의 메타 설명입니다.",
        "keyword_id": 1,
        "word_count": 1500,
        "status": "draft",
        "seo_score": 85.5,
    }


@pytest.fixture
def sample_content_request():
    """샘플 콘텐츠 생성 요청"""
    return {
        "keyword": "블로그 작성법",
        "target_word_count": 2000,
        "tone": "professional",
        "include_faq": True,
        "additional_context": "초보자를 위한 가이드",
    }


@pytest.fixture
def sample_image_data():
    """샘플 이미지 데이터"""
    return {
        "url": "https://example.com/test-image.png",
        "local_path": "/tmp/test-image.png",
        "alt_text": "테스트 이미지",
        "type": "hero",
        "post_id": 1,
    }


# ==================== 유틸리티 픽스처 ====================

@pytest.fixture
def mock_file_system(tmp_path):
    """임시 파일 시스템 픽스처"""
    # 임시 디렉토리 생성
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    
    return {
        "base": tmp_path,
        "images": images_dir,
        "uploads": uploads_dir,
    }


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """설정 캐시 리셋 (각 테스트마다 자동 실행)"""
    yield
    # 테스트 후 설정 캐시 클리어
    if hasattr(settings, "_instance"):
        delattr(settings, "_instance")


@pytest.fixture
def faker_locale():
    """Faker 한국어 로케일"""
    from faker import Faker
    return Faker("ko_KR")
