"""
Custom exception classes for Blog Automation System.

이 모듈은 시스템 전체에서 사용할 커스텀 예외 클래스들을 정의합니다.
각 예외는 명확한 에러 코드와 사용자 친화적인 메시지를 제공합니다.
"""

from typing import Any, Dict, Optional


class BlogAutomationException(Exception):
    """
    Base exception class for Blog Automation System.

    모든 커스텀 예외의 기본 클래스입니다.
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize exception.

        Args:
            message: 사용자에게 표시할 에러 메시지 (한글)
            error_code: 시스템 에러 코드 (예: KEYWORD_001)
            status_code: HTTP 상태 코드
            details: 추가 상세 정보
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details
            }
        }


# ==================== Keyword Research Exceptions ====================

class KeywordResearchException(BlogAutomationException):
    """키워드 리서치 관련 예외의 기본 클래스."""
    pass


class GoogleAdsAPIError(KeywordResearchException):
    """Google Ads API 호출 실패."""

    def __init__(self, message: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message or "Google Ads API 호출에 실패했습니다. API 키와 설정을 확인해주세요.",
            error_code="KEYWORD_001",
            status_code=502,
            details=details
        )


class NaverAPIError(KeywordResearchException):
    """Naver Search Ad API 호출 실패."""

    def __init__(self, message: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message or "네이버 검색광고 API 호출에 실패했습니다. API 키를 확인해주세요.",
            error_code="KEYWORD_002",
            status_code=502,
            details=details
        )


class GoogleTrendsError(KeywordResearchException):
    """Google Trends API 호출 실패."""

    def __init__(self, message: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message or "Google Trends 데이터를 가져오는데 실패했습니다.",
            error_code="KEYWORD_003",
            status_code=502,
            details=details
        )


class NoKeywordsFoundError(KeywordResearchException):
    """키워드 검색 결과가 없음."""

    def __init__(self, seed_keywords: list = None):
        super().__init__(
            message="검색 조건에 맞는 키워드를 찾지 못했습니다. 다른 시드 키워드를 시도해보세요.",
            error_code="KEYWORD_004",
            status_code=404,
            details={"seed_keywords": seed_keywords} if seed_keywords else {}
        )


class KeywordLimitExceededError(KeywordResearchException):
    """키워드 수 제한 초과."""

    def __init__(self, limit: int, requested: int):
        super().__init__(
            message=f"키워드 요청 수가 제한을 초과했습니다. (요청: {requested}, 최대: {limit})",
            error_code="KEYWORD_005",
            status_code=400,
            details={"limit": limit, "requested": requested}
        )


# ==================== Content Generation Exceptions ====================

class ContentGenerationException(BlogAutomationException):
    """콘텐츠 생성 관련 예외의 기본 클래스."""
    pass


class ClaudeAPIError(ContentGenerationException):
    """Claude API 호출 실패."""

    def __init__(self, message: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message or "Claude API 호출에 실패했습니다. API 키와 크레딧을 확인해주세요.",
            error_code="CONTENT_001",
            status_code=502,
            details=details
        )


class ContentTooShortError(ContentGenerationException):
    """생성된 콘텐츠가 최소 길이 미달."""

    def __init__(self, actual_length: int, min_length: int):
        super().__init__(
            message=f"생성된 콘텐츠가 너무 짧습니다. (현재: {actual_length}자, 최소: {min_length}자)",
            error_code="CONTENT_002",
            status_code=400,
            details={"actual_length": actual_length, "min_length": min_length}
        )


class ContentTooLongError(ContentGenerationException):
    """생성된 콘텐츠가 최대 길이 초과."""

    def __init__(self, actual_length: int, max_length: int):
        super().__init__(
            message=f"생성된 콘텐츠가 너무 깁니다. (현재: {actual_length}자, 최대: {max_length}자)",
            error_code="CONTENT_003",
            status_code=400,
            details={"actual_length": actual_length, "max_length": max_length}
        )


class SEOValidationError(ContentGenerationException):
    """SEO 검증 실패."""

    def __init__(self, validation_errors: list):
        super().__init__(
            message="콘텐츠가 SEO 기준을 충족하지 못했습니다.",
            error_code="CONTENT_004",
            status_code=400,
            details={"validation_errors": validation_errors}
        )


# ==================== Image Generation Exceptions ====================

class ImageGenerationException(BlogAutomationException):
    """이미지 생성 관련 예외의 기본 클래스."""
    pass


class DalleAPIError(ImageGenerationException):
    """DALL-E API 호출 실패."""

    def __init__(self, message: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message or "DALL-E 이미지 생성에 실패했습니다. API 키와 크레딧을 확인해주세요.",
            error_code="IMAGE_001",
            status_code=502,
            details=details
        )


class UnsplashAPIError(ImageGenerationException):
    """Unsplash API 호출 실패."""

    def __init__(self, message: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message or "Unsplash 이미지 검색에 실패했습니다. API 키를 확인해주세요.",
            error_code="IMAGE_002",
            status_code=502,
            details=details
        )


class ImageOptimizationError(ImageGenerationException):
    """이미지 최적화 실패."""

    def __init__(self, message: str = None, image_path: str = None):
        super().__init__(
            message=message or "이미지 최적화 중 오류가 발생했습니다.",
            error_code="IMAGE_003",
            status_code=500,
            details={"image_path": image_path} if image_path else {}
        )


class ImageDownloadError(ImageGenerationException):
    """이미지 다운로드 실패."""

    def __init__(self, url: str, message: str = None):
        super().__init__(
            message=message or f"이미지 다운로드에 실패했습니다: {url}",
            error_code="IMAGE_004",
            status_code=502,
            details={"url": url}
        )


class ImageSizeLimitExceededError(ImageGenerationException):
    """이미지 크기 제한 초과."""

    def __init__(self, actual_size: int, max_size: int):
        super().__init__(
            message=f"이미지 크기가 제한을 초과했습니다. (현재: {actual_size}KB, 최대: {max_size}KB)",
            error_code="IMAGE_005",
            status_code=400,
            details={"actual_size_kb": actual_size, "max_size_kb": max_size}
        )


# ==================== WordPress Publishing Exceptions ====================

class PublishingException(BlogAutomationException):
    """발행 관련 예외의 기본 클래스."""
    pass


class WordPressAPIError(PublishingException):
    """WordPress API 호출 실패."""

    def __init__(self, message: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message or "WordPress API 호출에 실패했습니다. URL과 인증 정보를 확인해주세요.",
            error_code="PUBLISH_001",
            status_code=502,
            details=details
        )


class WordPressAuthenticationError(PublishingException):
    """WordPress 인증 실패."""

    def __init__(self, message: str = None):
        super().__init__(
            message=message or "WordPress 인증에 실패했습니다. 사용자명과 애플리케이션 비밀번호를 확인해주세요.",
            error_code="PUBLISH_002",
            status_code=401,
            details={}
        )


class PostNotFoundError(PublishingException):
    """포스트를 찾을 수 없음."""

    def __init__(self, post_id: int):
        super().__init__(
            message=f"ID {post_id}인 포스트를 찾을 수 없습니다.",
            error_code="PUBLISH_003",
            status_code=404,
            details={"post_id": post_id}
        )


class MediaUploadError(PublishingException):
    """미디어 업로드 실패."""

    def __init__(self, file_path: str, message: str = None):
        super().__init__(
            message=message or f"미디어 업로드에 실패했습니다: {file_path}",
            error_code="PUBLISH_004",
            status_code=500,
            details={"file_path": file_path}
        )


class PublishingLimitError(PublishingException):
    """발행 횟수 제한 초과."""

    def __init__(self, limit: int, period: str):
        super().__init__(
            message=f"발행 횟수 제한을 초과했습니다. ({period}당 최대 {limit}건)",
            error_code="PUBLISH_005",
            status_code=429,
            details={"limit": limit, "period": period}
        )


# ==================== Database Exceptions ====================

class DatabaseException(BlogAutomationException):
    """데이터베이스 관련 예외의 기본 클래스."""
    pass


class DatabaseConnectionError(DatabaseException):
    """데이터베이스 연결 실패."""

    def __init__(self, message: str = None):
        super().__init__(
            message=message or "데이터베이스 연결에 실패했습니다. 연결 정보를 확인해주세요.",
            error_code="DB_001",
            status_code=503,
            details={}
        )


class RecordNotFoundError(DatabaseException):
    """레코드를 찾을 수 없음."""

    def __init__(self, model: str, identifier: Any):
        super().__init__(
            message=f"{model}을(를) 찾을 수 없습니다. (ID: {identifier})",
            error_code="DB_002",
            status_code=404,
            details={"model": model, "id": identifier}
        )


class DuplicateRecordError(DatabaseException):
    """중복 레코드."""

    def __init__(self, model: str, field: str, value: Any):
        super().__init__(
            message=f"이미 존재하는 {model}입니다. ({field}: {value})",
            error_code="DB_003",
            status_code=409,
            details={"model": model, "field": field, "value": value}
        )


# ==================== Web Scraping Exceptions ====================

class ScrapingException(BlogAutomationException):
    """웹 스크래핑 관련 예외의 기본 클래스."""
    pass


class PlaywrightError(ScrapingException):
    """Playwright 오류."""

    def __init__(self, message: str = None, url: str = None):
        super().__init__(
            message=message or "웹 페이지 로드에 실패했습니다.",
            error_code="SCRAPE_001",
            status_code=502,
            details={"url": url} if url else {}
        )


class ScrapingTimeoutError(ScrapingException):
    """스크래핑 타임아웃."""

    def __init__(self, url: str, timeout: int):
        super().__init__(
            message=f"웹 페이지 로드 시간이 초과되었습니다. ({timeout}ms)",
            error_code="SCRAPE_002",
            status_code=504,
            details={"url": url, "timeout_ms": timeout}
        )


class ParsingError(ScrapingException):
    """HTML 파싱 오류."""

    def __init__(self, message: str = None, url: str = None):
        super().__init__(
            message=message or "웹 페이지 파싱에 실패했습니다.",
            error_code="SCRAPE_003",
            status_code=500,
            details={"url": url} if url else {}
        )


# ==================== Task/Queue Exceptions ====================

class TaskException(BlogAutomationException):
    """작업 큐 관련 예외의 기본 클래스."""
    pass


class CeleryWorkerError(TaskException):
    """Celery Worker 오류."""

    def __init__(self, message: str = None, task_id: str = None):
        super().__init__(
            message=message or "백그라운드 작업 실행에 실패했습니다.",
            error_code="TASK_001",
            status_code=500,
            details={"task_id": task_id} if task_id else {}
        )


class TaskNotFoundError(TaskException):
    """작업을 찾을 수 없음."""

    def __init__(self, task_id: str):
        super().__init__(
            message=f"작업을 찾을 수 없습니다. (ID: {task_id})",
            error_code="TASK_002",
            status_code=404,
            details={"task_id": task_id}
        )


class TaskTimeoutError(TaskException):
    """작업 실행 시간 초과."""

    def __init__(self, task_name: str, timeout: int):
        super().__init__(
            message=f"작업 실행 시간이 초과되었습니다: {task_name} ({timeout}초)",
            error_code="TASK_003",
            status_code=504,
            details={"task_name": task_name, "timeout_seconds": timeout}
        )


# ==================== Configuration Exceptions ====================

class ConfigurationException(BlogAutomationException):
    """설정 관련 예외의 기본 클래스."""
    pass


class MissingAPIKeyError(ConfigurationException):
    """API 키 누락."""

    def __init__(self, service: str):
        super().__init__(
            message=f"{service} API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.",
            error_code="CONFIG_001",
            status_code=500,
            details={"service": service}
        )


class InvalidConfigurationError(ConfigurationException):
    """잘못된 설정."""

    def __init__(self, field: str, message: str = None):
        super().__init__(
            message=message or f"잘못된 설정입니다: {field}",
            error_code="CONFIG_002",
            status_code=500,
            details={"field": field}
        )


# ==================== Validation Exceptions ====================

class ValidationException(BlogAutomationException):
    """검증 관련 예외의 기본 클래스."""
    pass


class InvalidInputError(ValidationException):
    """잘못된 입력."""

    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"잘못된 입력입니다: {field} - {message}",
            error_code="VALID_001",
            status_code=400,
            details={"field": field}
        )


class RateLimitExceededError(ValidationException):
    """요청 횟수 제한 초과."""

    def __init__(self, limit: int, period: int, retry_after: int = None):
        super().__init__(
            message=f"요청 횟수 제한을 초과했습니다. ({period}초당 최대 {limit}건)",
            error_code="VALID_002",
            status_code=429,
            details={
                "limit": limit,
                "period_seconds": period,
                "retry_after_seconds": retry_after
            }
        )


# ==================== External Service Exceptions ====================

class ExternalServiceException(BlogAutomationException):
    """외부 서비스 관련 예외의 기본 클래스."""
    pass


class ServiceUnavailableError(ExternalServiceException):
    """서비스 이용 불가."""

    def __init__(self, service: str, message: str = None):
        super().__init__(
            message=message or f"{service} 서비스를 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요.",
            error_code="SERVICE_001",
            status_code=503,
            details={"service": service}
        )


class APIQuotaExceededError(ExternalServiceException):
    """API 할당량 초과."""

    def __init__(self, service: str, reset_time: str = None):
        super().__init__(
            message=f"{service} API 할당량을 초과했습니다. 나중에 다시 시도해주세요.",
            error_code="SERVICE_002",
            status_code=429,
            details={"service": service, "reset_time": reset_time}
        )
