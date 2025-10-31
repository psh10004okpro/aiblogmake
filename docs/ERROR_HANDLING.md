# 에러 처리 가이드

이 문서는 블로그 자동화 시스템의 에러 처리 사용 방법을 설명합니다.

## 📚 목차

1. [커스텀 예외 클래스](#커스텀-예외-클래스)
2. [사용 예제](#사용-예제)
3. [에러 응답 형식](#에러-응답-형식)
4. [베스트 프랙티스](#베스트-프랙티스)

## 커스텀 예외 클래스

모든 커스텀 예외는 `BlogAutomationException`을 상속합니다.

### 계층 구조

```
BlogAutomationException (기본 클래스)
├── KeywordResearchException
│   ├── GoogleAdsAPIError
│   ├── NaverAPIError
│   ├── GoogleTrendsError
│   ├── NoKeywordsFoundError
│   └── KeywordLimitExceededError
├── ContentGenerationException
│   ├── ClaudeAPIError
│   ├── ContentTooShortError
│   ├── ContentTooLongError
│   └── SEOValidationError
├── ImageGenerationException
│   ├── DalleAPIError
│   ├── UnsplashAPIError
│   ├── ImageOptimizationError
│   ├── ImageDownloadError
│   └── ImageSizeLimitExceededError
├── PublishingException
│   ├── WordPressAPIError
│   ├── WordPressAuthenticationError
│   ├── PostNotFoundError
│   ├── MediaUploadError
│   └── PublishingLimitError
├── DatabaseException
│   ├── DatabaseConnectionError
│   ├── RecordNotFoundError
│   └── DuplicateRecordError
├── ScrapingException
│   ├── PlaywrightError
│   ├── ScrapingTimeoutError
│   └── ParsingError
├── TaskException
│   ├── CeleryWorkerError
│   ├── TaskNotFoundError
│   └── TaskTimeoutError
├── ConfigurationException
│   ├── MissingAPIKeyError
│   └── InvalidConfigurationError
├── ValidationException
│   ├── InvalidInputError
│   └── RateLimitExceededError
└── ExternalServiceException
    ├── ServiceUnavailableError
    └── APIQuotaExceededError
```

## 사용 예제

### 1. 키워드 리서치 서비스

```python
from app.core.exceptions import (
    GoogleAdsAPIError,
    NaverAPIError,
    NoKeywordsFoundError,
    MissingAPIKeyError
)

async def get_google_keyword_data(keywords: List[str]) -> List[Dict]:
    """Get keyword data from Google Keyword Planner."""

    # API 키 체크
    if not settings.google_ads_developer_token:
        raise MissingAPIKeyError("Google Ads")

    try:
        # API 호출
        response = keyword_plan_idea_service.generate_keyword_ideas(request=request)
        results = []

        for idea in response:
            # 데이터 처리
            results.append({...})

        # 결과가 없는 경우
        if not results:
            raise NoKeywordsFoundError(seed_keywords=keywords)

        return results

    except GoogleAdsException as e:
        # Google Ads API 에러
        raise GoogleAdsAPIError(
            message=f"Google Ads API 호출 실패: {str(e)}",
            details={"keywords": keywords, "error": str(e)}
        )
    except Exception as e:
        # 기타 예외는 그대로 전파 (글로벌 핸들러가 처리)
        logger.error("unexpected_error", error=str(e))
        raise
```

### 2. 콘텐츠 생성 서비스

```python
from app.core.exceptions import (
    ClaudeAPIError,
    ContentTooShortError,
    SEOValidationError
)

async def generate_content(keyword: str, target_word_count: int) -> Dict:
    """Generate SEO-optimized content."""

    try:
        # Claude API 호출
        response = await self.client.messages.create(...)
        content = response.content[0].text

        # 길이 검증
        word_count = count_words(content)
        if word_count < settings.min_content_length:
            raise ContentTooShortError(
                actual_length=word_count,
                min_length=settings.min_content_length
            )

        # SEO 검증
        validation = validate_seo_content(...)
        if not validation["passed"]:
            raise SEOValidationError(
                validation_errors=validation["issues"]
            )

        return {
            "title": title,
            "content": content,
            ...
        }

    except anthropic.APIError as e:
        raise ClaudeAPIError(
            message="콘텐츠 생성 중 오류 발생",
            details={"error": str(e), "keyword": keyword}
        )
```

### 3. 이미지 생성 서비스

```python
from app.core.exceptions import (
    DalleAPIError,
    ImageOptimizationError,
    ImageSizeLimitExceededError
)

async def generate_dalle_image(prompt: str, is_hero: bool = True) -> Dict:
    """Generate image using DALL-E 3."""

    try:
        # DALL-E API 호출
        response = await self.openai_client.images.generate(...)
        image_url = response.data[0].url

        # 이미지 다운로드 및 최적화
        local_path = await self._download_image(image_url)
        optimized_path = await self.optimize_image(local_path, is_hero)

        # 크기 검증
        size_kb = os.path.getsize(optimized_path) // 1024
        if size_kb > settings.image_max_size_kb:
            raise ImageSizeLimitExceededError(
                actual_size=size_kb,
                max_size=settings.image_max_size_kb
            )

        return {
            "url": image_url,
            "local_path": str(optimized_path),
            "size_kb": size_kb,
            ...
        }

    except openai.APIError as e:
        raise DalleAPIError(
            message=f"이미지 생성 실패: {str(e)}",
            details={"prompt": prompt, "error": str(e)}
        )
    except IOError as e:
        raise ImageOptimizationError(
            message="이미지 최적화 실패",
            image_path=str(local_path)
        )
```

### 4. WordPress 발행 서비스

```python
from app.core.exceptions import (
    WordPressAPIError,
    WordPressAuthenticationError,
    MediaUploadError,
    PostNotFoundError
)

async def create_post(title: str, content: str, **kwargs) -> Dict:
    """Create a WordPress post."""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers=self.auth_header,
                timeout=aiohttp.ClientTimeout(total=settings.wp_api_timeout)
            ) as response:

                # 인증 실패
                if response.status == 401:
                    raise WordPressAuthenticationError()

                # API 오류
                if response.status not in (200, 201):
                    error_text = await response.text()
                    raise WordPressAPIError(
                        message=f"WordPress 포스트 생성 실패 (HTTP {response.status})",
                        details={"status": response.status, "error": error_text}
                    )

                post_data = await response.json()
                return {
                    "id": post_data["id"],
                    "url": post_data["link"],
                    ...
                }

    except aiohttp.ClientError as e:
        raise WordPressAPIError(
            message="WordPress API 연결 실패",
            details={"error": str(e)}
        )
```

### 5. API 라우트에서 사용

```python
from fastapi import APIRouter, Depends
from app.core.exceptions import NoKeywordsFoundError

@router.post("/research")
async def research_keywords(
    request: KeywordResearchRequest,
    service: KeywordResearchService = Depends(get_keyword_service)
):
    """
    Research keywords.

    에러는 자동으로 처리됩니다:
    - NoKeywordsFoundError -> 404 응답
    - GoogleAdsAPIError -> 502 응답
    - 기타 예외 -> 500 응답
    """
    # 커스텀 예외는 자동으로 글로벌 핸들러가 처리
    keywords = await service.research_keywords(
        seed_keywords=request.seed_keywords,
        include_naver=request.include_naver
    )

    return {
        "keywords": keywords,
        "total": len(keywords)
    }
```

## 에러 응답 형식

모든 에러는 일관된 JSON 형식으로 응답됩니다:

```json
{
  "success": false,
  "error": {
    "code": "KEYWORD_001",
    "message": "Google Ads API 호출에 실패했습니다. API 키와 설정을 확인해주세요.",
    "timestamp": "2025-01-15T10:30:00.000Z",
    "details": {
      "keywords": ["블로그 SEO"],
      "error": "INVALID_DEVELOPER_TOKEN"
    },
    "path": "/api/v1/keywords/research"
  }
}
```

### 필드 설명

- `success`: 항상 `false`
- `error.code`: 에러 코드 (예: `KEYWORD_001`, `CONTENT_002`)
- `error.message`: 사용자 친화적인 한글 메시지
- `error.timestamp`: 에러 발생 시각 (ISO 8601)
- `error.details`: 추가 상세 정보 (개발 모드에서만 포함되는 경우도 있음)
- `error.path`: 에러가 발생한 API 경로

### 검증 에러 (422)

Pydantic 검증 실패 시:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력 데이터가 올바르지 않습니다. 아래 필드를 확인해주세요.",
    "timestamp": "2025-01-15T10:30:00.000Z",
    "details": {
      "validation_errors": [
        {
          "field": "body -> target_word_count",
          "message": "target_word_count의 값이 너무 작습니다.",
          "type": "value_error.number.not_ge"
        }
      ]
    },
    "path": "/api/v1/content/generate"
  }
}
```

## 베스트 프랙티스

### 1. 적절한 예외 선택

```python
# ✅ 좋은 예
if not api_key:
    raise MissingAPIKeyError("Google Ads")

# ❌ 나쁜 예
if not api_key:
    raise Exception("API key is missing")
```

### 2. 상세 정보 제공

```python
# ✅ 좋은 예
raise GoogleAdsAPIError(
    message="키워드 데이터 조회 실패",
    details={
        "keywords": keywords,
        "customer_id": customer_id,
        "error_code": error.code
    }
)

# ❌ 나쁜 예
raise GoogleAdsAPIError()
```

### 3. 로깅과 함께 사용

```python
# ✅ 좋은 예
try:
    result = await api_call()
except APIError as e:
    logger.error("api_call_failed", error=str(e), details=details)
    raise GoogleAdsAPIError(details={"original_error": str(e)})

# ❌ 나쁜 예 (로깅 없음)
try:
    result = await api_call()
except APIError as e:
    raise GoogleAdsAPIError()
```

### 4. 재시도 로직과 함께 사용

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_data_with_retry():
    try:
        return await external_api_call()
    except Exception as e:
        logger.warning("api_call_retry", attempt=attempt, error=str(e))
        raise ServiceUnavailableError("External API")
```

### 5. 컨텍스트 정보 포함

```python
# ✅ 좋은 예
try:
    content = await generate_content(keyword)
except Exception as e:
    raise ContentGenerationException(
        message=f"'{keyword}' 키워드로 콘텐츠 생성 실패",
        error_code="CONTENT_001",
        status_code=500,
        details={
            "keyword": keyword,
            "target_word_count": target_word_count,
            "error": str(e)
        }
    )
```

## 에러 코드 목록

### 키워드 리서치 (KEYWORD_XXX)
- `KEYWORD_001`: Google Ads API 오류
- `KEYWORD_002`: Naver API 오류
- `KEYWORD_003`: Google Trends 오류
- `KEYWORD_004`: 키워드 없음
- `KEYWORD_005`: 키워드 수 제한 초과

### 콘텐츠 생성 (CONTENT_XXX)
- `CONTENT_001`: Claude API 오류
- `CONTENT_002`: 콘텐츠 너무 짧음
- `CONTENT_003`: 콘텐츠 너무 김
- `CONTENT_004`: SEO 검증 실패

### 이미지 (IMAGE_XXX)
- `IMAGE_001`: DALL-E API 오류
- `IMAGE_002`: Unsplash API 오류
- `IMAGE_003`: 이미지 최적화 실패
- `IMAGE_004`: 이미지 다운로드 실패
- `IMAGE_005`: 이미지 크기 초과

### 발행 (PUBLISH_XXX)
- `PUBLISH_001`: WordPress API 오류
- `PUBLISH_002`: WordPress 인증 실패
- `PUBLISH_003`: 포스트 없음
- `PUBLISH_004`: 미디어 업로드 실패
- `PUBLISH_005`: 발행 횟수 제한

### 데이터베이스 (DB_XXX)
- `DB_001`: DB 연결 실패
- `DB_002`: 레코드 없음
- `DB_003`: 중복 레코드

### 기타
- `HTTP_XXX`: HTTP 에러 (4xx, 5xx)
- `VALIDATION_ERROR`: 입력 검증 실패
- `INTERNAL_ERROR`: 예기치 않은 오류

## 테스트 예제

```python
import pytest
from app.core.exceptions import NoKeywordsFoundError, GoogleAdsAPIError

def test_no_keywords_found():
    """Test NoKeywordsFoundError exception."""
    with pytest.raises(NoKeywordsFoundError) as exc_info:
        raise NoKeywordsFoundError(seed_keywords=["test"])

    assert exc_info.value.error_code == "KEYWORD_004"
    assert exc_info.value.status_code == 404
    assert "키워드를 찾지 못했습니다" in exc_info.value.message

@pytest.mark.asyncio
async def test_google_ads_api_error_handling(client):
    """Test Google Ads API error is properly handled."""
    response = await client.post(
        "/api/v1/keywords/research",
        json={"seed_keywords": ["invalid"]}
    )

    assert response.status_code == 502
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "KEYWORD_001"
    assert "Google Ads API" in data["error"]["message"]
```

## 도움말 메시지

각 에러 코드는 해결 방법을 안내하는 도움말이 있습니다:

```python
from app.core.errors import get_error_help

help_message = get_error_help("KEYWORD_001")
# "Google Ads API 설정 가이드: https://developers.google.com/google-ads/api"
```

## 요약

1. **항상 커스텀 예외 사용**: `Exception` 대신 `BlogAutomationException` 계열 사용
2. **상세 정보 제공**: `details` 파라미터로 디버깅 정보 포함
3. **로깅 함께 사용**: 예외 발생 시 로그도 남기기
4. **사용자 친화적 메시지**: 한글로 명확하게 설명
5. **일관된 패턴**: 모든 서비스에서 동일한 방식으로 에러 처리

이렇게 하면 에러 추적이 쉽고, 사용자에게 명확한 피드백을 제공할 수 있습니다.
