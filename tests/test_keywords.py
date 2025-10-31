"""
Tests for keyword research service.
"""

import pytest
from app.services.keyword_research import KeywordResearchService


@pytest.fixture
def keyword_service():
    """Create keyword service instance."""
    return KeywordResearchService()


def test_calculate_golden_score(keyword_service):
    """Test golden keyword score calculation."""
    score = keyword_service.calculate_golden_score(
        search_volume=1000,
        competition=0.5,
        cpc=1.5,
        trend=0.2
    )

    assert 0 <= score <= 100
    assert isinstance(score, float)


def test_filter_keywords(keyword_service):
    """Test keyword filtering."""
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


@pytest.mark.asyncio
async def test_get_google_trends_data(keyword_service):
    """Test Google Trends data fetching."""
    # This is a basic test - in production you'd mock the API
    keywords = ["블로그"]
    trends = await keyword_service.get_google_trends_data(keywords)

    assert isinstance(trends, dict)
    assert "블로그" in trends
    assert -1 <= trends["블로그"] <= 1
