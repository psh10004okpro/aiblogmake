"""
Tests for custom exceptions and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.exceptions import (
    BlogAutomationException,
    GoogleAdsAPIError,
    NaverAPIError,
    NoKeywordsFoundError,
    ClaudeAPIError,
    ContentTooShortError,
    DalleAPIError,
    WordPressAPIError,
    WordPressAuthenticationError,
    MissingAPIKeyError,
    InvalidInputError,
    RateLimitExceededError,
)


client = TestClient(app)


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_blog_automation_exception_base(self):
        """Test base exception class."""
        exc = BlogAutomationException(
            message="테스트 에러",
            error_code="TEST_001",
            status_code=400,
            details={"key": "value"}
        )

        assert exc.message == "테스트 에러"
        assert exc.error_code == "TEST_001"
        assert exc.status_code == 400
        assert exc.details == {"key": "value"}

        # Test to_dict method
        error_dict = exc.to_dict()
        assert error_dict["error"]["code"] == "TEST_001"
        assert error_dict["error"]["message"] == "테스트 에러"
        assert error_dict["error"]["details"]["key"] == "value"

    def test_google_ads_api_error(self):
        """Test Google Ads API error."""
        exc = GoogleAdsAPIError(details={"keywords": ["test"]})

        assert exc.error_code == "KEYWORD_001"
        assert exc.status_code == 502
        assert "Google Ads API" in exc.message
        assert exc.details["keywords"] == ["test"]

    def test_naver_api_error(self):
        """Test Naver API error."""
        exc = NaverAPIError()

        assert exc.error_code == "KEYWORD_002"
        assert exc.status_code == 502
        assert "네이버" in exc.message

    def test_no_keywords_found_error(self):
        """Test no keywords found error."""
        exc = NoKeywordsFoundError(seed_keywords=["블로그", "SEO"])

        assert exc.error_code == "KEYWORD_004"
        assert exc.status_code == 404
        assert "키워드를 찾지 못했습니다" in exc.message
        assert exc.details["seed_keywords"] == ["블로그", "SEO"]

    def test_claude_api_error(self):
        """Test Claude API error."""
        exc = ClaudeAPIError(message="커스텀 메시지")

        assert exc.error_code == "CONTENT_001"
        assert exc.status_code == 502
        assert exc.message == "커스텀 메시지"

    def test_content_too_short_error(self):
        """Test content too short error."""
        exc = ContentTooShortError(actual_length=500, min_length=1500)

        assert exc.error_code == "CONTENT_002"
        assert exc.status_code == 400
        assert "500" in exc.message
        assert "1500" in exc.message
        assert exc.details["actual_length"] == 500
        assert exc.details["min_length"] == 1500

    def test_dalle_api_error(self):
        """Test DALL-E API error."""
        exc = DalleAPIError(details={"prompt": "test image"})

        assert exc.error_code == "IMAGE_001"
        assert exc.status_code == 502
        assert "DALL-E" in exc.message

    def test_wordpress_api_error(self):
        """Test WordPress API error."""
        exc = WordPressAPIError()

        assert exc.error_code == "PUBLISH_001"
        assert exc.status_code == 502
        assert "WordPress" in exc.message

    def test_wordpress_authentication_error(self):
        """Test WordPress authentication error."""
        exc = WordPressAuthenticationError()

        assert exc.error_code == "PUBLISH_002"
        assert exc.status_code == 401
        assert "인증" in exc.message

    def test_missing_api_key_error(self):
        """Test missing API key error."""
        exc = MissingAPIKeyError("Google Ads")

        assert exc.error_code == "CONFIG_001"
        assert exc.status_code == 500
        assert "Google Ads" in exc.message
        assert "API 키가 설정되지 않았습니다" in exc.message

    def test_rate_limit_exceeded_error(self):
        """Test rate limit exceeded error."""
        exc = RateLimitExceededError(limit=100, period=60, retry_after=30)

        assert exc.error_code == "VALID_002"
        assert exc.status_code == 429
        assert exc.details["limit"] == 100
        assert exc.details["period_seconds"] == 60
        assert exc.details["retry_after_seconds"] == 30


class TestErrorHandlers:
    """Test global error handlers."""

    def test_health_check_endpoint(self):
        """Test that health check endpoint works."""
        response = client.get("/health")
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "services" in data

    def test_404_not_found(self):
        """Test 404 error handling."""
        response = client.get("/nonexistent-endpoint")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "HTTP_404"
        assert "찾을 수 없습니다" in data["error"]["message"]

    def test_422_validation_error(self):
        """Test validation error handling."""
        # Send invalid data to trigger validation error
        response = client.post(
            "/api/v1/keywords/research",
            json={
                "seed_keywords": [],  # Empty list (should fail validation)
            }
        )

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "validation_errors" in data["error"]["details"]

    def test_405_method_not_allowed(self):
        """Test 405 error handling."""
        # Try to use wrong HTTP method
        response = client.delete("/")

        assert response.status_code == 405
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "HTTP_405"


class TestErrorResponseFormat:
    """Test error response format consistency."""

    def test_error_response_structure(self):
        """Test that all error responses have consistent structure."""
        response = client.get("/nonexistent")

        assert response.status_code == 404
        data = response.json()

        # Required fields
        assert "success" in data
        assert data["success"] is False
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "timestamp" in data["error"]
        assert "path" in data["error"]

    def test_validation_error_response_format(self):
        """Test validation error response format."""
        response = client.post(
            "/api/v1/keywords/research",
            json={"seed_keywords": []}
        )

        assert response.status_code == 422
        data = response.json()

        assert data["success"] is False
        assert "validation_errors" in data["error"]["details"]
        assert isinstance(data["error"]["details"]["validation_errors"], list)

        # Check validation error structure
        if data["error"]["details"]["validation_errors"]:
            error = data["error"]["details"]["validation_errors"][0]
            assert "field" in error
            assert "message" in error
            assert "type" in error


class TestKoreanErrorMessages:
    """Test that error messages are in Korean."""

    def test_404_korean_message(self):
        """Test 404 error has Korean message."""
        response = client.get("/nonexistent")
        data = response.json()

        # Check for Korean characters
        message = data["error"]["message"]
        assert any('\uac00' <= char <= '\ud7a3' for char in message), \
            "Error message should contain Korean characters"

    def test_validation_error_korean_message(self):
        """Test validation error has Korean message."""
        response = client.post(
            "/api/v1/keywords/research",
            json={"seed_keywords": []}
        )
        data = response.json()

        message = data["error"]["message"]
        assert any('\uac00' <= char <= '\ud7a3' for char in message), \
            "Error message should contain Korean characters"


@pytest.mark.asyncio
class TestExceptionInServices:
    """Test exception handling in service layer."""

    @pytest.mark.skip(reason="Requires mock service setup")
    async def test_keyword_service_raises_custom_exception(self):
        """Test that keyword service raises custom exceptions."""
        # This would require mocking the service
        # Example structure:
        # from app.services.keyword_research import KeywordResearchService
        # service = KeywordResearchService()
        # with pytest.raises(GoogleAdsAPIError):
        #     await service.get_google_keyword_data([])
        pass

    @pytest.mark.skip(reason="Requires mock service setup")
    async def test_content_service_raises_custom_exception(self):
        """Test that content service raises custom exceptions."""
        pass
