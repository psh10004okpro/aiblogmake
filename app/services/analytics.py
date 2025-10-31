"""
Google Analytics 4 (GA4) Integration Service

Provides methods to fetch analytics data from Google Analytics 4 API
and analyze blog post performance.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import os
from pathlib import Path

from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


@dataclass
class AnalyticsMetrics:
    """Container for analytics metrics."""
    page_views: int = 0
    sessions: int = 0
    users: int = 0
    new_users: int = 0
    bounce_rate: float = 0.0
    avg_session_duration: float = 0.0
    engagement_rate: float = 0.0


@dataclass
class TrafficSource:
    """Traffic source data."""
    source: str
    medium: str
    sessions: int
    users: int
    page_views: int


@dataclass
class PostPerformance:
    """Post performance metrics."""
    page_path: str
    page_title: str
    page_views: int
    unique_users: int
    avg_time_on_page: float
    bounce_rate: float
    engagement_rate: float


class GoogleAnalyticsService:
    """
    Google Analytics 4 Data API service.

    Fetches and processes analytics data for blog posts.
    """

    def __init__(self):
        """Initialize Google Analytics service."""
        self.property_id = settings.ga_property_id
        self.credentials_path = settings.ga_credentials_path
        self.client = None

        # Check if GA is configured
        self.is_configured = bool(
            self.property_id and
            self.credentials_path and
            Path(self.credentials_path).exists()
        )

        if self.is_configured:
            try:
                self._initialize_client()
            except Exception as e:
                logger.error("ga_initialization_failed", error=str(e))
                self.is_configured = False

    def _initialize_client(self):
        """Initialize the Google Analytics Data API client."""
        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.oauth2 import service_account

            # Load credentials
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/analytics.readonly']
            )

            # Create client
            self.client = BetaAnalyticsDataClient(credentials=credentials)

            logger.info("ga_client_initialized", property_id=self.property_id)

        except ImportError:
            logger.warning(
                "ga_library_not_installed",
                message="Install google-analytics-data: pip install google-analytics-data"
            )
            raise
        except Exception as e:
            logger.error("ga_client_initialization_failed", error=str(e))
            raise

    async def get_overview_metrics(
        self,
        start_date: str = "30daysAgo",
        end_date: str = "today"
    ) -> AnalyticsMetrics:
        """
        Get overview metrics for the specified date range.

        Args:
            start_date: Start date (e.g., "30daysAgo", "2025-01-01")
            end_date: End date (e.g., "today", "2025-01-31")

        Returns:
            AnalyticsMetrics object with overview data
        """
        if not self.is_configured:
            logger.warning("ga_not_configured")
            return AnalyticsMetrics()

        try:
            from google.analytics.data_v1beta.types import (
                RunReportRequest,
                DateRange,
                Dimension,
                Metric
            )

            # Create report request
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                metrics=[
                    Metric(name="screenPageViews"),
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="newUsers"),
                    Metric(name="bounceRate"),
                    Metric(name="averageSessionDuration"),
                    Metric(name="engagementRate")
                ]
            )

            # Run report
            response = self.client.run_report(request)

            # Extract metrics
            if response.rows:
                row = response.rows[0]
                metrics = AnalyticsMetrics(
                    page_views=int(row.metric_values[0].value),
                    sessions=int(row.metric_values[1].value),
                    users=int(row.metric_values[2].value),
                    new_users=int(row.metric_values[3].value),
                    bounce_rate=float(row.metric_values[4].value) * 100,
                    avg_session_duration=float(row.metric_values[5].value),
                    engagement_rate=float(row.metric_values[6].value) * 100
                )

                logger.info(
                    "ga_overview_metrics_fetched",
                    date_range=f"{start_date} to {end_date}",
                    page_views=metrics.page_views
                )

                return metrics

            return AnalyticsMetrics()

        except Exception as e:
            logger.error("ga_overview_metrics_failed", error=str(e))
            return AnalyticsMetrics()

    async def get_realtime_metrics(self) -> Dict[str, Any]:
        """
        Get realtime analytics data.

        Returns:
            Dictionary with realtime metrics
        """
        if not self.is_configured:
            logger.warning("ga_not_configured")
            return {
                "active_users": 0,
                "active_users_by_country": [],
                "active_users_by_device": []
            }

        try:
            from google.analytics.data_v1beta.types import (
                RunRealtimeReportRequest,
                Dimension,
                Metric
            )

            # Get active users
            request = RunRealtimeReportRequest(
                property=f"properties/{self.property_id}",
                metrics=[Metric(name="activeUsers")]
            )

            response = self.client.run_realtime_report(request)

            active_users = 0
            if response.rows:
                active_users = int(response.rows[0].metric_values[0].value)

            # Get active users by country
            request_country = RunRealtimeReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[Dimension(name="country")],
                metrics=[Metric(name="activeUsers")],
                limit=10
            )

            response_country = self.client.run_realtime_report(request_country)

            users_by_country = []
            for row in response_country.rows:
                users_by_country.append({
                    "country": row.dimension_values[0].value,
                    "active_users": int(row.metric_values[0].value)
                })

            # Get active users by device
            request_device = RunRealtimeReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[Dimension(name="deviceCategory")],
                metrics=[Metric(name="activeUsers")]
            )

            response_device = self.client.run_realtime_report(request_device)

            users_by_device = []
            for row in response_device.rows:
                users_by_device.append({
                    "device": row.dimension_values[0].value,
                    "active_users": int(row.metric_values[0].value)
                })

            result = {
                "active_users": active_users,
                "active_users_by_country": users_by_country,
                "active_users_by_device": users_by_device,
                "timestamp": datetime.utcnow().isoformat()
            }

            logger.info("ga_realtime_metrics_fetched", active_users=active_users)

            return result

        except Exception as e:
            logger.error("ga_realtime_metrics_failed", error=str(e))
            return {
                "active_users": 0,
                "active_users_by_country": [],
                "active_users_by_device": [],
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_traffic_sources(
        self,
        start_date: str = "30daysAgo",
        end_date: str = "today",
        limit: int = 10
    ) -> List[TrafficSource]:
        """
        Get traffic sources breakdown.

        Args:
            start_date: Start date
            end_date: End date
            limit: Maximum number of sources to return

        Returns:
            List of TrafficSource objects
        """
        if not self.is_configured:
            logger.warning("ga_not_configured")
            return []

        try:
            from google.analytics.data_v1beta.types import (
                RunReportRequest,
                DateRange,
                Dimension,
                Metric,
                OrderBy
            )

            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimensions=[
                    Dimension(name="sessionSource"),
                    Dimension(name="sessionMedium")
                ],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="screenPageViews")
                ],
                order_bys=[
                    OrderBy(
                        metric=OrderBy.MetricOrderBy(metric_name="sessions"),
                        desc=True
                    )
                ],
                limit=limit
            )

            response = self.client.run_report(request)

            sources = []
            for row in response.rows:
                source = TrafficSource(
                    source=row.dimension_values[0].value,
                    medium=row.dimension_values[1].value,
                    sessions=int(row.metric_values[0].value),
                    users=int(row.metric_values[1].value),
                    page_views=int(row.metric_values[2].value)
                )
                sources.append(source)

            logger.info(
                "ga_traffic_sources_fetched",
                count=len(sources),
                date_range=f"{start_date} to {end_date}"
            )

            return sources

        except Exception as e:
            logger.error("ga_traffic_sources_failed", error=str(e))
            return []

    async def get_top_posts(
        self,
        start_date: str = "30daysAgo",
        end_date: str = "today",
        limit: int = 10
    ) -> List[PostPerformance]:
        """
        Get top performing posts.

        Args:
            start_date: Start date
            end_date: End date
            limit: Number of posts to return

        Returns:
            List of PostPerformance objects
        """
        if not self.is_configured:
            logger.warning("ga_not_configured")
            return []

        try:
            from google.analytics.data_v1beta.types import (
                RunReportRequest,
                DateRange,
                Dimension,
                Metric,
                OrderBy,
                FilterExpression,
                Filter
            )

            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimensions=[
                    Dimension(name="pagePath"),
                    Dimension(name="pageTitle")
                ],
                metrics=[
                    Metric(name="screenPageViews"),
                    Metric(name="totalUsers"),
                    Metric(name="userEngagementDuration"),
                    Metric(name="bounceRate"),
                    Metric(name="engagementRate")
                ],
                dimension_filter=FilterExpression(
                    filter=Filter(
                        field_name="pagePath",
                        string_filter=Filter.StringFilter(
                            match_type=Filter.StringFilter.MatchType.CONTAINS,
                            value="/"
                        )
                    )
                ),
                order_bys=[
                    OrderBy(
                        metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"),
                        desc=True
                    )
                ],
                limit=limit
            )

            response = self.client.run_report(request)

            posts = []
            for row in response.rows:
                page_views = int(row.metric_values[0].value)
                unique_users = int(row.metric_values[1].value)
                total_engagement = float(row.metric_values[2].value)

                # Calculate average time on page
                avg_time_on_page = (
                    total_engagement / page_views if page_views > 0 else 0
                )

                post = PostPerformance(
                    page_path=row.dimension_values[0].value,
                    page_title=row.dimension_values[1].value,
                    page_views=page_views,
                    unique_users=unique_users,
                    avg_time_on_page=avg_time_on_page,
                    bounce_rate=float(row.metric_values[3].value) * 100,
                    engagement_rate=float(row.metric_values[4].value) * 100
                )
                posts.append(post)

            logger.info(
                "ga_top_posts_fetched",
                count=len(posts),
                date_range=f"{start_date} to {end_date}"
            )

            return posts

        except Exception as e:
            logger.error("ga_top_posts_failed", error=str(e))
            return []

    async def get_post_performance(
        self,
        post_path: str,
        start_date: str = "30daysAgo",
        end_date: str = "today"
    ) -> Optional[PostPerformance]:
        """
        Get performance metrics for a specific post.

        Args:
            post_path: URL path of the post (e.g., "/blog/my-post")
            start_date: Start date
            end_date: End date

        Returns:
            PostPerformance object or None
        """
        if not self.is_configured:
            logger.warning("ga_not_configured")
            return None

        try:
            from google.analytics.data_v1beta.types import (
                RunReportRequest,
                DateRange,
                Dimension,
                Metric,
                FilterExpression,
                Filter
            )

            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimensions=[
                    Dimension(name="pagePath"),
                    Dimension(name="pageTitle")
                ],
                metrics=[
                    Metric(name="screenPageViews"),
                    Metric(name="totalUsers"),
                    Metric(name="userEngagementDuration"),
                    Metric(name="bounceRate"),
                    Metric(name="engagementRate")
                ],
                dimension_filter=FilterExpression(
                    filter=Filter(
                        field_name="pagePath",
                        string_filter=Filter.StringFilter(
                            match_type=Filter.StringFilter.MatchType.EXACT,
                            value=post_path
                        )
                    )
                )
            )

            response = self.client.run_report(request)

            if response.rows:
                row = response.rows[0]
                page_views = int(row.metric_values[0].value)
                unique_users = int(row.metric_values[1].value)
                total_engagement = float(row.metric_values[2].value)

                avg_time_on_page = (
                    total_engagement / page_views if page_views > 0 else 0
                )

                post = PostPerformance(
                    page_path=row.dimension_values[0].value,
                    page_title=row.dimension_values[1].value,
                    page_views=page_views,
                    unique_users=unique_users,
                    avg_time_on_page=avg_time_on_page,
                    bounce_rate=float(row.metric_values[3].value) * 100,
                    engagement_rate=float(row.metric_values[4].value) * 100
                )

                logger.info(
                    "ga_post_performance_fetched",
                    post_path=post_path,
                    page_views=page_views
                )

                return post

            return None

        except Exception as e:
            logger.error("ga_post_performance_failed", error=str(e), post_path=post_path)
            return None

    async def get_comparison_data(
        self,
        current_start: str = "30daysAgo",
        current_end: str = "today",
        previous_start: str = "60daysAgo",
        previous_end: str = "31daysAgo"
    ) -> Dict[str, Any]:
        """
        Get comparison data between two periods.

        Args:
            current_start: Current period start date
            current_end: Current period end date
            previous_start: Previous period start date
            previous_end: Previous period end date

        Returns:
            Dictionary with current, previous, and change data
        """
        current_metrics = await self.get_overview_metrics(current_start, current_end)
        previous_metrics = await self.get_overview_metrics(previous_start, previous_end)

        def calculate_change(current: float, previous: float) -> Dict[str, Any]:
            """Calculate percentage change."""
            if previous == 0:
                return {"value": 0.0, "percentage": 0.0}

            change = current - previous
            percentage = (change / previous) * 100

            return {
                "value": change,
                "percentage": round(percentage, 2)
            }

        return {
            "current_period": {
                "start_date": current_start,
                "end_date": current_end,
                "metrics": current_metrics
            },
            "previous_period": {
                "start_date": previous_start,
                "end_date": previous_end,
                "metrics": previous_metrics
            },
            "changes": {
                "page_views": calculate_change(
                    current_metrics.page_views,
                    previous_metrics.page_views
                ),
                "sessions": calculate_change(
                    current_metrics.sessions,
                    previous_metrics.sessions
                ),
                "users": calculate_change(
                    current_metrics.users,
                    previous_metrics.users
                ),
                "engagement_rate": calculate_change(
                    current_metrics.engagement_rate,
                    previous_metrics.engagement_rate
                )
            }
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Get Google Analytics configuration status.

        Returns:
            Dictionary with configuration status
        """
        return {
            "configured": self.is_configured,
            "property_id": self.property_id if self.is_configured else None,
            "credentials_exists": (
                Path(self.credentials_path).exists()
                if self.credentials_path else False
            ),
            "api_available": self.client is not None
        }


# Singleton instance
_analytics_service = None


def get_analytics_service() -> GoogleAnalyticsService:
    """Get or create singleton GoogleAnalyticsService instance."""
    global _analytics_service

    if _analytics_service is None:
        _analytics_service = GoogleAnalyticsService()

    return _analytics_service
