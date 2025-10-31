"""
Tests for keyword research service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.keyword_research import KeywordResearchService
from app.core.exceptions import GoogleAdsAPIError, NaverAPIError, NoKeywordsFoundError


# ==================== 픽스처 ====================

@pytest.fixture
def keyword_service():
    """Create keyword service instance."""
    return KeywordResearchService()


@pytest.fixture
def sample_google_keyword_response():
    """샘플 Google Ads API 응답 데이터"""
    return [
        MagicMock(
            text="블로그 작성법",
            keyword_idea_metrics=MagicMock(
                avg_monthly_searches=1000,
                competition=2,  # MEDIUM
                competition_index=50,
                low_top_of_page_bid_micros=1000000,  # 1.0 USD
                high_top_of_page_bid_micros=5000000,  # 5.0 USD
            )
        ),
        MagicMock(
            text="블로그 수익",
            keyword_idea_metrics=MagicMock(
                avg_monthly_searches=2000,
                competition=3,  # HIGH
                competition_index=80,
                low_top_of_page_bid_micros=2000000,  # 2.0 USD
                high_top_of_page_bid_micros=8000000,  # 8.0 USD
            )
        ),
    ]


@pytest.fixture
def sample_naver_keyword_response():
    """샘플 Naver API 응답 데이터"""
    return {
        "keywordList": [
            {
                "relKeyword": "블로그 작성",
                "monthlyPcQcCnt": 500,
                "monthlyMobileQcCnt": 1500,
                "compIdx": "중간",
            },
            {
                "relKeyword": "블로그 만들기",
                "monthlyPcQcCnt": 800,
                "monthlyMobileQcCnt": 2200,
                "compIdx": "높음",
            },
        ]
    }


# ==================== 단위 테스트: calculate_golden_score ====================

@pytest.mark.unit
class TestCalculateGoldenScore:
    """Test golden score calculation."""

    def test_basic_score_calculation(self, keyword_service):
        """기본 점수 계산 테스트"""
        score = keyword_service.calculate_golden_score(
            search_volume=1000,
            competition=0.5,
            cpc=1.5,
            trend=0.2
        )

        assert 0 <= score <= 100
        assert isinstance(score, float)

    def test_high_volume_keyword(self, keyword_service):
        """높은 검색량 키워드 점수"""
        score = keyword_service.calculate_golden_score(
            search_volume=50000,
            competition=0.3,
            cpc=2.0,
            trend=0.5
        )

        assert score > 70  # 높은 점수 예상

    def test_low_competition_keyword(self, keyword_service):
        """낮은 경쟁 키워드 점수"""
        score = keyword_service.calculate_golden_score(
            search_volume=1000,
            competition=0.1,  # 낮은 경쟁
            cpc=1.5,
            trend=0.2
        )

        assert score > 50  # 경쟁이 낮아 점수가 높음

    def test_zero_values(self, keyword_service):
        """제로 값 처리"""
        score = keyword_service.calculate_golden_score(
            search_volume=0,
            competition=0,
            cpc=0,
            trend=0
        )

        assert 0 <= score <= 100
        assert isinstance(score, float)

    def test_extreme_values(self, keyword_service):
        """극단적인 값 처리"""
        score = keyword_service.calculate_golden_score(
            search_volume=1000000,
            competition=1.0,
            cpc=100.0,
            trend=1.0
        )

        assert 0 <= score <= 100


# ==================== 단위 테스트: filter_keywords ====================

@pytest.mark.unit
class TestFilterKeywords:
    """Test keyword filtering."""

    def test_basic_filtering(self, keyword_service):
        """기본 필터링 테스트"""
        keywords = [
            {"keyword": "test1", "search_volume": 100, "competition": 0.3, "cpc": 1.0, "golden_score": 50},
            {"keyword": "test2", "search_volume": 50, "competition": 0.8, "cpc": 0.5, "golden_score": 30},
            {"keyword": "test3", "search_volume": 200, "competition": 0.4, "cpc": 2.0, "golden_score": 70},
        ]

        filtered = keyword_service.filter_keywords(
            keywords,
            min_search_volume=100,
            max_competition=0.5
        )

        assert len(filtered) == 2
        assert all(kw["search_volume"] >= 100 for kw in filtered)
        assert all(kw["competition"] <= 0.5 for kw in filtered)

    def test_min_score_filter(self, keyword_service):
        """최소 점수 필터"""
        keywords = [
            {"keyword": "test1", "search_volume": 100, "competition": 0.3, "cpc": 1.0, "golden_score": 50},
            {"keyword": "test2", "search_volume": 50, "competition": 0.8, "cpc": 0.5, "golden_score": 30},
            {"keyword": "test3", "search_volume": 200, "competition": 0.4, "cpc": 2.0, "golden_score": 70},
        ]

        filtered = keyword_service.filter_keywords(
            keywords,
            min_golden_score=60
        )

        assert len(filtered) == 1
        assert filtered[0]["golden_score"] >= 60

    def test_cpc_filter(self, keyword_service):
        """CPC 필터"""
        keywords = [
            {"keyword": "test1", "search_volume": 100, "competition": 0.3, "cpc": 1.0, "golden_score": 50},
            {"keyword": "test2", "search_volume": 50, "competition": 0.8, "cpc": 0.5, "golden_score": 30},
            {"keyword": "test3", "search_volume": 200, "competition": 0.4, "cpc": 2.0, "golden_score": 70},
        ]

        filtered = keyword_service.filter_keywords(
            keywords,
            min_cpc=1.0
        )

        assert len(filtered) == 2
        assert all(kw["cpc"] >= 1.0 for kw in filtered)

    def test_empty_list(self, keyword_service):
        """빈 리스트 처리"""
        filtered = keyword_service.filter_keywords([])
        assert filtered == []

    def test_no_filters(self, keyword_service):
        """필터 없이 호출"""
        keywords = [
            {"keyword": "test1", "search_volume": 100, "competition": 0.3, "cpc": 1.0, "golden_score": 50},
        ]

        filtered = keyword_service.filter_keywords(keywords)
        assert len(filtered) == len(keywords)

    def test_limit_results(self, keyword_service):
        """결과 개수 제한"""
        keywords = [
            {"keyword": f"test{i}", "search_volume": 100 * i, "competition": 0.3, "cpc": 1.0, "golden_score": 50 + i}
            for i in range(10)
        ]

        filtered = keyword_service.filter_keywords(keywords, limit=5)
        assert len(filtered) <= 5


# ==================== 단위 테스트: convert_competition ====================

@pytest.mark.unit
def test_convert_competition(keyword_service):
    """경쟁 레벨 변환 테스트"""
    # LOW = 2
    assert keyword_service._convert_competition(2) == 0.3

    # MEDIUM = 3
    assert keyword_service._convert_competition(3) == 0.6

    # HIGH = 4
    assert keyword_service._convert_competition(4) == 0.9

    # UNSPECIFIED or unknown
    assert keyword_service._convert_competition(0) == 0.5
    assert keyword_service._convert_competition(999) == 0.5


# ==================== 통합 테스트: Google Ads API ====================

@pytest.mark.integration
@pytest.mark.external
@pytest.mark.asyncio
async def test_get_google_keyword_data_mocked(
    keyword_service,
    mock_google_ads_client,
    sample_google_keyword_response
):
    """Google Ads API 모킹 테스트"""
    # Mock 설정
    mock_service = mock_google_ads_client.get_service.return_value
    mock_service.generate_keyword_ideas.return_value = sample_google_keyword_response

    keyword_service.google_ads_client = mock_google_ads_client

    # 테스트 실행
    results = await keyword_service.get_google_keyword_data(["블로그"])

    # 검증
    assert len(results) == 2
    assert results[0]["keyword"] == "블로그 작성법"
    assert results[0]["search_volume"] == 1000
    assert 0 <= results[0]["competition"] <= 1.0
    assert results[0]["cpc"] > 0


@pytest.mark.integration
@pytest.mark.external
@pytest.mark.asyncio
async def test_get_google_keyword_data_no_client(keyword_service):
    """Google Ads 클라이언트 없을 때 테스트"""
    keyword_service.google_ads_client = None

    with patch.object(keyword_service, '_init_google_ads_client', return_value=None):
        results = await keyword_service.get_google_keyword_data(["블로그"])
        assert results == []


# ==================== 통합 테스트: Naver API ====================

@pytest.mark.integration
@pytest.mark.external
@pytest.mark.asyncio
async def test_get_naver_keyword_data_mocked(
    keyword_service,
    sample_naver_keyword_response
):
    """Naver API 모킹 테스트"""
    with patch("aiohttp.ClientSession") as mock_session:
        # Mock response 설정
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=sample_naver_keyword_response)

        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

        # 테스트 실행
        results = await keyword_service.get_naver_keyword_data(["블로그"])

        # 검증
        assert len(results) == 2
        assert results[0]["keyword"] == "블로그 작성"
        assert results[0]["search_volume"] == 2000  # PC + Mobile
        assert "competition" in results[0]


@pytest.mark.integration
@pytest.mark.external
@pytest.mark.asyncio
async def test_get_naver_keyword_data_api_error(keyword_service):
    """Naver API 에러 처리 테스트"""
    with patch("aiohttp.ClientSession") as mock_session:
        # Mock error response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")

        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

        # 에러 발생 확인
        results = await keyword_service.get_naver_keyword_data(["블로그"])
        assert results == []


# ==================== 통합 테스트: Google Trends ====================

@pytest.mark.integration
@pytest.mark.external
@pytest.mark.asyncio
async def test_get_google_trends_data_mocked(keyword_service, mock_pytrends):
    """Google Trends 모킹 테스트"""
    keywords = ["블로그"]

    with patch("pytrends.request.TrendReq", return_value=mock_pytrends):
        trends = await keyword_service.get_google_trends_data(keywords)

        assert isinstance(trends, dict)
        assert "블로그" in trends
        assert -1 <= trends["블로그"] <= 1


@pytest.mark.integration
@pytest.mark.external
@pytest.mark.slow
@pytest.mark.asyncio
async def test_get_google_trends_data_real(keyword_service):
    """Google Trends 실제 API 테스트 (느림)"""
    # 실제 API 호출 (CI에서는 skip 가능)
    keywords = ["블로그"]
    trends = await keyword_service.get_google_trends_data(keywords)

    assert isinstance(trends, dict)
    assert "블로그" in trends
    assert -1 <= trends["블로그"] <= 1


# ==================== 통합 테스트: research_keywords ====================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_research_keywords_full_flow(
    keyword_service,
    mock_google_ads_client,
    sample_google_keyword_response,
    sample_naver_keyword_response,
    mock_pytrends
):
    """전체 키워드 리서치 플로우 테스트"""
    # Mock 설정
    keyword_service.google_ads_client = mock_google_ads_client
    mock_service = mock_google_ads_client.get_service.return_value
    mock_service.generate_keyword_ideas.return_value = sample_google_keyword_response

    with patch("aiohttp.ClientSession") as mock_session, \
         patch("pytrends.request.TrendReq", return_value=mock_pytrends), \
         patch("app.utils.scraper.scrape_naver_autocomplete", return_value=["블로그 추천"]):

        # Naver API mock
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=sample_naver_keyword_response)
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

        # 테스트 실행
        results = await keyword_service.research_keywords(
            seed_keywords=["블로그"],
            use_google_ads=True,
            use_naver=True,
            use_trends=True,
            use_scraping=False
        )

        # 검증
        assert len(results) > 0
        assert all("keyword" in kw for kw in results)
        assert all("golden_score" in kw for kw in results)
        assert all("search_volume" in kw for kw in results)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_research_keywords_no_results(keyword_service):
    """키워드 없을 때 예외 처리"""
    with patch.object(keyword_service, 'get_google_keyword_data', return_value=[]), \
         patch.object(keyword_service, 'get_naver_keyword_data', return_value=[]), \
         patch.object(keyword_service, 'get_google_trends_data', return_value={}), \
         patch("app.utils.scraper.scrape_naver_autocomplete", return_value=[]):

        with pytest.raises(NoKeywordsFoundError):
            await keyword_service.research_keywords(
                seed_keywords=["존재하지않는키워드"],
                use_google_ads=True,
                use_naver=True,
                use_trends=True,
                use_scraping=True
            )


# ==================== 단위 테스트: 시그니처 생성 ====================

@pytest.mark.unit
def test_generate_naver_signature(keyword_service):
    """Naver API 시그니처 생성 테스트"""
    timestamp = "1234567890"
    signature = keyword_service._generate_naver_signature(timestamp)

    assert isinstance(signature, str)
    assert len(signature) > 0
