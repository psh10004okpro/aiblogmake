"""
Keyword research service for discovering golden keywords.

This service integrates with Google Keyword Planner, Naver Search Ad API,
and web scraping to find high-value keywords for content creation.
"""

import asyncio
import hashlib
import hmac
import base64
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from pytrends.request import TrendReq
from app.core.config import settings
from app.utils.logger import get_logger
from app.utils.scraper import scrape_naver_autocomplete

logger = get_logger(__name__)


class KeywordResearchService:
    """Service for researching and scoring keywords."""

    def __init__(self):
        """Initialize the keyword research service."""
        self.naver_api_url = "https://api.naver.com"
        self.google_ads_client = None

    def _init_google_ads_client(self) -> Optional[GoogleAdsClient]:
        """
        Initialize Google Ads API client.

        Returns:
            Optional[GoogleAdsClient]: Google Ads client or None if not configured.
        """
        if not settings.google_ads_developer_token:
            logger.warning("google_ads_not_configured")
            return None

        try:
            credentials = {
                "developer_token": settings.google_ads_developer_token,
                "client_id": settings.google_ads_client_id,
                "client_secret": settings.google_ads_client_secret,
                "refresh_token": settings.google_ads_refresh_token,
                "login_customer_id": settings.google_ads_login_customer_id,
            }

            client = GoogleAdsClient.load_from_dict(credentials)
            logger.info("google_ads_client_initialized")
            return client

        except Exception as e:
            logger.error("google_ads_client_init_error", error=str(e))
            return None

    async def get_google_keyword_data(
        self,
        keywords: List[str],
        language: str = "ko",
        location: str = "KR"
    ) -> List[Dict[str, Any]]:
        """
        Get keyword data from Google Keyword Planner.

        Args:
            keywords: List of keywords to research.
            language: Language code (default: ko).
            location: Location code (default: KR for South Korea).

        Returns:
            List[Dict[str, Any]]: Keyword data with search volume, competition, CPC.
        """
        if not self.google_ads_client:
            self.google_ads_client = self._init_google_ads_client()

        if not self.google_ads_client:
            logger.warning("google_ads_unavailable")
            return []

        results = []

        try:
            keyword_plan_idea_service = self.google_ads_client.get_service(
                "KeywordPlanIdeaService"
            )

            # Set location (South Korea: 2410)
            location_id = "2410" if location == "KR" else "2840"

            # Set language (Korean: 1012)
            language_id = "1012" if language == "ko" else "1000"

            request = self.google_ads_client.get_type("GenerateKeywordIdeasRequest")
            request.customer_id = settings.google_ads_customer_id.replace("-", "")
            request.language = f"languageConstants/{language_id}"
            request.geo_target_constants.append(f"geoTargetConstants/{location_id}")

            # Add seed keywords
            request.keyword_seed.keywords.extend(keywords)

            # Execute request
            response = keyword_plan_idea_service.generate_keyword_ideas(request=request)

            for idea in response:
                keyword_data = {
                    "keyword": idea.text,
                    "search_volume": idea.keyword_idea_metrics.avg_monthly_searches,
                    "competition": self._convert_competition(
                        idea.keyword_idea_metrics.competition
                    ),
                    "cpc": idea.keyword_idea_metrics.average_cpc_micros / 1_000_000
                    if idea.keyword_idea_metrics.average_cpc_micros else 0.0,
                    "source": "google",
                }
                results.append(keyword_data)

            logger.info(
                "google_keyword_data_fetched",
                count=len(results),
                keywords=keywords
            )

        except GoogleAdsException as e:
            logger.error(
                "google_ads_api_error",
                error=str(e),
                keywords=keywords
            )
        except Exception as e:
            logger.error(
                "google_keyword_fetch_error",
                error=str(e),
                keywords=keywords
            )

        return results

    def _convert_competition(self, competition_enum) -> float:
        """
        Convert Google Ads competition enum to 0-1 scale.

        Args:
            competition_enum: Google Ads competition enum.

        Returns:
            float: Competition score (0.0 to 1.0).
        """
        competition_map = {
            0: 0.0,  # UNSPECIFIED
            1: 0.3,  # LOW
            2: 0.5,  # MEDIUM
            3: 0.8,  # HIGH
        }
        return competition_map.get(competition_enum, 0.5)

    async def get_naver_keyword_data(
        self,
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get keyword data from Naver Search Ad API.

        Args:
            keywords: List of keywords to research.

        Returns:
            List[Dict[str, Any]]: Naver keyword data.
        """
        if not settings.naver_api_key or not settings.naver_secret_key:
            logger.warning("naver_api_not_configured")
            return []

        results = []
        url = f"{self.naver_api_url}/keywordstool"

        try:
            # Generate signature
            timestamp = str(int(time.time() * 1000))
            signature = self._generate_naver_signature(timestamp)

            headers = {
                "X-Naver-Client-Id": settings.naver_api_key,
                "X-Naver-Client-Secret": settings.naver_secret_key,
                "X-Timestamp": timestamp,
                "X-Signature": signature,
                "Content-Type": "application/json",
            }

            payload = {
                "hintKeywords": keywords,
                "showDetail": 1,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        for item in data.get("keywordList", []):
                            keyword_data = {
                                "keyword": item.get("relKeyword"),
                                "search_volume": item.get("monthlyPcQcCnt", 0)
                                + item.get("monthlyMobileQcCnt", 0),
                                "naver_monthly_pc_search": item.get("monthlyPcQcCnt", 0),
                                "naver_monthly_mobile_search": item.get("monthlyMobileQcCnt", 0),
                                "competition": item.get("compIdx", 50) / 100.0,
                                "source": "naver",
                            }
                            results.append(keyword_data)

                        logger.info(
                            "naver_keyword_data_fetched",
                            count=len(results),
                            keywords=keywords
                        )
                    else:
                        logger.error(
                            "naver_api_error",
                            status=response.status,
                            keywords=keywords
                        )

        except Exception as e:
            logger.error(
                "naver_keyword_fetch_error",
                error=str(e),
                keywords=keywords
            )

        return results

    def _generate_naver_signature(self, timestamp: str) -> str:
        """
        Generate signature for Naver API authentication.

        Args:
            timestamp: Timestamp string.

        Returns:
            str: Base64-encoded HMAC signature.
        """
        secret = settings.naver_secret_key.encode("utf-8")
        message = f"{timestamp}.{settings.naver_api_key}".encode("utf-8")
        signature = hmac.new(secret, message, hashlib.sha256).digest()
        return base64.b64encode(signature).decode("utf-8")

    async def get_google_trends_data(
        self,
        keywords: List[str],
        timeframe: str = "today 12-m",
        geo: str = "KR"
    ) -> Dict[str, float]:
        """
        Get trend data from Google Trends.

        Args:
            keywords: List of keywords to check trends.
            timeframe: Timeframe for trends (default: last 12 months).
            geo: Geographic location (default: KR).

        Returns:
            Dict[str, float]: Keyword to trend score mapping (-1 to 1).
        """
        trends = {}

        try:
            pytrends = TrendReq(hl="ko", tz=540)

            for keyword in keywords:
                try:
                    pytrends.build_payload(
                        [keyword],
                        timeframe=timeframe,
                        geo=geo
                    )

                    interest_over_time = pytrends.interest_over_time()

                    if not interest_over_time.empty:
                        # Calculate trend: compare recent vs older data
                        values = interest_over_time[keyword].values
                        if len(values) >= 2:
                            recent_avg = values[-3:].mean()
                            older_avg = values[:-3].mean()

                            if older_avg > 0:
                                trend = (recent_avg - older_avg) / older_avg
                                trends[keyword] = max(-1.0, min(1.0, trend))
                            else:
                                trends[keyword] = 0.0
                        else:
                            trends[keyword] = 0.0
                    else:
                        trends[keyword] = 0.0

                    # Rate limiting
                    await asyncio.sleep(1)

                except Exception as e:
                    logger.warning(
                        "google_trends_keyword_error",
                        keyword=keyword,
                        error=str(e)
                    )
                    trends[keyword] = 0.0

            logger.info("google_trends_data_fetched", count=len(trends))

        except Exception as e:
            logger.error("google_trends_error", error=str(e))

        return trends

    def calculate_golden_score(
        self,
        search_volume: int,
        competition: float,
        cpc: float,
        trend: float = 0.0
    ) -> float:
        """
        Calculate golden keyword score.

        Formula:
        score = (search_volume_score * 0.30) +
                ((100 - competition) * 0.40) +
                (cpc_score * 0.20) +
                (trend * 10) * trend_multiplier

        Args:
            search_volume: Monthly search volume.
            competition: Competition level (0-1).
            cpc: Cost per click in USD.
            trend: Trend score (-1 to 1).

        Returns:
            float: Golden keyword score (0-100).
        """
        # Normalize search volume (log scale, cap at 100k)
        import math
        search_volume_score = (
            math.log10(max(search_volume, 1)) / math.log10(100000) * 100
        )
        search_volume_score = min(100, search_volume_score)

        # Normalize CPC (cap at $10)
        cpc_score = min(100, (cpc / 10.0) * 100)

        # Competition score (inverse - lower is better)
        competition_score = (1.0 - competition) * 100

        # Trend multiplier
        trend_multiplier = 1.0 + (trend * 0.2)  # -20% to +20%

        # Calculate weighted score
        score = (
            (search_volume_score * 0.30) +
            (competition_score * 0.40) +
            (cpc_score * 0.20) +
            (trend * 10)
        ) * trend_multiplier

        return round(max(0, min(100, score)), 2)

    async def research_keywords(
        self,
        seed_keywords: List[str],
        include_google: bool = True,
        include_naver: bool = True,
        include_autocomplete: bool = True,
        include_trends: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform comprehensive keyword research.

        Args:
            seed_keywords: Initial keywords to expand.
            include_google: Include Google Keyword Planner.
            include_naver: Include Naver Search Ad API.
            include_autocomplete: Include Naver autocomplete scraping.
            include_trends: Include Google Trends data.

        Returns:
            List[Dict[str, Any]]: List of keyword data with golden scores.
        """
        all_keywords = set(seed_keywords)
        keyword_data = {}

        # Scrape Naver autocomplete
        if include_autocomplete and settings.enable_naver_autocomplete:
            logger.info("scraping_naver_autocomplete", seeds=seed_keywords)
            autocomplete_results = await scrape_naver_autocomplete(
                seed_keywords,
                max_suggestions_per_keyword=10
            )
            for suggestions in autocomplete_results.values():
                all_keywords.update(suggestions)

        # Fetch from multiple sources in parallel
        tasks = []

        if include_google and settings.google_ads_developer_token:
            tasks.append(
                self.get_google_keyword_data(list(all_keywords))
            )

        if include_naver and settings.naver_api_key:
            tasks.append(
                self.get_naver_keyword_data(list(all_keywords))
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge results
        for result in results:
            if isinstance(result, list):
                for kw_data in result:
                    keyword = kw_data["keyword"]
                    if keyword not in keyword_data:
                        keyword_data[keyword] = kw_data
                    else:
                        # Merge data (prefer more complete data)
                        for key, value in kw_data.items():
                            if value and not keyword_data[keyword].get(key):
                                keyword_data[keyword][key] = value

        # Get trends data
        trends = {}
        if include_trends:
            trends = await self.get_google_trends_data(list(keyword_data.keys()))

        # Calculate golden scores
        scored_keywords = []
        for keyword, data in keyword_data.items():
            trend = trends.get(keyword, 0.0)
            score = self.calculate_golden_score(
                search_volume=data.get("search_volume", 0),
                competition=data.get("competition", 0.5),
                cpc=data.get("cpc", 0.0),
                trend=trend
            )

            keyword_item = {
                "keyword": keyword,
                "search_volume": data.get("search_volume", 0),
                "competition": data.get("competition", 0.5),
                "cpc": data.get("cpc", 0.0),
                "trend": trend,
                "golden_score": score,
                "source": data.get("source", "manual"),
                "naver_monthly_pc_search": data.get("naver_monthly_pc_search", 0),
                "naver_monthly_mobile_search": data.get("naver_monthly_mobile_search", 0),
            }
            scored_keywords.append(keyword_item)

        # Sort by golden score
        scored_keywords.sort(key=lambda x: x["golden_score"], reverse=True)

        logger.info(
            "keyword_research_completed",
            total_keywords=len(scored_keywords),
            top_score=scored_keywords[0]["golden_score"] if scored_keywords else 0
        )

        return scored_keywords

    def filter_keywords(
        self,
        keywords: List[Dict[str, Any]],
        min_search_volume: Optional[int] = None,
        max_competition: Optional[float] = None,
        min_cpc: Optional[float] = None,
        min_golden_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter keywords based on criteria.

        Args:
            keywords: List of keyword data.
            min_search_volume: Minimum search volume.
            max_competition: Maximum competition level.
            min_cpc: Minimum CPC.
            min_golden_score: Minimum golden score.

        Returns:
            List[Dict[str, Any]]: Filtered keywords.
        """
        filtered = keywords

        if min_search_volume is not None:
            filtered = [
                kw for kw in filtered
                if kw.get("search_volume", 0) >= min_search_volume
            ]

        if max_competition is not None:
            filtered = [
                kw for kw in filtered
                if kw.get("competition", 1.0) <= max_competition
            ]

        if min_cpc is not None:
            filtered = [
                kw for kw in filtered
                if kw.get("cpc", 0.0) >= min_cpc
            ]

        if min_golden_score is not None:
            filtered = [
                kw for kw in filtered
                if kw.get("golden_score", 0.0) >= min_golden_score
            ]

        logger.info(
            "keywords_filtered",
            original_count=len(keywords),
            filtered_count=len(filtered)
        )

        return filtered
