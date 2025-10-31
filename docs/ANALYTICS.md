# Google Analytics 연동

Google Analytics 4 (GA4) API 통합 완전 가이드

## 개요

Google Analytics 연동 기능은 블로그의 성과를 측정하고 분석할 수 있는 강력한 도구입니다. GA4 Data API를 통해 실시간 방문자, 트래픽 소스, 인기 포스트 등의 데이터를 대시보드에서 확인할 수 있습니다.

### 주요 기능

1. **실시간 방문자 추적**: 현재 활성 사용자 수, 디바이스별/국가별 분포
2. **전체 개요**: 페이지뷰, 세션, 사용자, 참여율, 이탈률
3. **트래픽 소스 분석**: Organic, Social, Direct, Referral 트래픽
4. **인기 포스트 TOP 10**: 페이지뷰 기준 상위 포스트
5. **포스트별 성과**: 개별 포스트의 상세 분석
6. **기간 비교**: 현재 vs 이전 기간 비교 및 증감률

## 사전 준비

### 1. Google Cloud 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. 프로젝트 이름: "Blog Automation Analytics"

### 2. Google Analytics Data API 활성화

1. [API Library](https://console.cloud.google.com/apis/library) 이동
2. "Google Analytics Data API" 검색
3. "사용 설정" 클릭

### 3. 서비스 계정 생성

1. [서비스 계정](https://console.cloud.google.com/iam-admin/serviceaccounts) 페이지 이동
2. "+ 서비스 계정 만들기" 클릭
3. 서비스 계정 세부정보:
   - 이름: `blog-analytics-reader`
   - 설명: `Read-only access to Google Analytics`
4. "만들고 계속하기" 클릭
5. 역할: "없음" (GA 속성에서 직접 권한 부여)
6. "완료" 클릭

### 4. 서비스 계정 키 생성

1. 생성한 서비스 계정 클릭
2. "키" 탭으로 이동
3. "키 추가" > "새 키 만들기"
4. 키 유형: **JSON** 선택
5. "만들기" 클릭
6. JSON 키 파일 다운로드
7. 안전한 위치에 저장 (예: `/home/user/aiblogmake/credentials/ga-service-account.json`)

**⚠️ 중요**: 이 JSON 파일은 절대 Git에 커밋하지 마세요!

### 5. Google Analytics 속성에 서비스 계정 추가

1. [Google Analytics](https://analytics.google.com/) 접속
2. 관리 (왼쪽 하단 톱니바퀴 아이콘) 클릭
3. "속성" 열에서 "속성 액세스 관리" 선택
4. 우측 상단 "+ 추가" 클릭
5. 서비스 계정 이메일 주소 입력:
   ```
   blog-analytics-reader@YOUR-PROJECT-ID.iam.gserviceaccount.com
   ```
6. 역할: **뷰어** 선택
7. "추가" 클릭

### 6. GA4 속성 ID 확인

1. Google Analytics 관리 페이지
2. "속성" 열에서 "속성 세부정보" 선택
3. "속성 ID" 복사 (형식: `123456789`)

## 설치 및 설정

### 1. Python 라이브러리 설치

```bash
pip install google-analytics-data google-auth
```

또는 `requirements.txt`에 추가:
```txt
google-analytics-data==0.18.0
google-auth==2.25.2
```

### 2. 환경 변수 설정

`.env` 파일에 다음 설정 추가:

```env
# Google Analytics 4 설정
GA_PROPERTY_ID=123456789
GA_CREDENTIALS_PATH=/home/user/aiblogmake/credentials/ga-service-account.json
GA_CACHE_TTL=300  # 캐시 TTL (초), 기본값: 5분
```

**설정 값 설명:**
- `GA_PROPERTY_ID`: GA4 속성 ID (숫자만)
- `GA_CREDENTIALS_PATH`: 서비스 계정 JSON 키 파일 절대 경로
- `GA_CACHE_TTL`: API 응답 캐시 유지 시간 (초)

### 3. 서비스 계정 키 파일 보호

`.gitignore`에 추가:
```
credentials/
*.json
!package.json
```

파일 권한 설정 (Linux/Mac):
```bash
chmod 600 /home/user/aiblogmake/credentials/ga-service-account.json
```

### 4. 서버 재시작

```bash
# Docker Compose 사용 시
docker-compose restart

# 직접 실행 시
python -m app.main
```

## API 사용법

### 1. Analytics 상태 확인

```python
from app.services.analytics import get_analytics_service

analytics_service = get_analytics_service()
status = analytics_service.get_status()

print(status)
# {
#     "configured": True,
#     "property_id": "123456789",
#     "credentials_exists": True,
#     "api_available": True
# }
```

### 2. 전체 개요 메트릭

```python
metrics = await analytics_service.get_overview_metrics(
    start_date="30daysAgo",
    end_date="today"
)

print(f"페이지뷰: {metrics.page_views}")
print(f"사용자: {metrics.users}")
print(f"참여율: {metrics.engagement_rate}%")
```

### 3. 실시간 방문자

```python
realtime = await analytics_service.get_realtime_metrics()

print(f"현재 활성 사용자: {realtime['active_users']}")
print(f"국가별: {realtime['active_users_by_country']}")
print(f"디바이스별: {realtime['active_users_by_device']}")
```

### 4. 트래픽 소스

```python
sources = await analytics_service.get_traffic_sources(
    start_date="30daysAgo",
    end_date="today",
    limit=10
)

for source in sources:
    print(f"{source.source} ({source.medium}): {source.sessions} sessions")
```

### 5. 인기 포스트

```python
top_posts = await analytics_service.get_top_posts(
    start_date="30daysAgo",
    end_date="today",
    limit=10
)

for post in top_posts:
    print(f"{post.page_title}: {post.page_views} views")
```

### 6. 특정 포스트 성과

```python
post = await analytics_service.get_post_performance(
    post_path="/blog/my-post",
    start_date="30daysAgo",
    end_date="today"
)

if post:
    print(f"페이지뷰: {post.page_views}")
    print(f"평균 체류시간: {post.avg_time_on_page}초")
    print(f"참여율: {post.engagement_rate}%")
```

### 7. 기간 비교

```python
comparison = await analytics_service.get_comparison_data(
    current_start="30daysAgo",
    current_end="today",
    previous_start="60daysAgo",
    previous_end="31daysAgo"
)

print(f"페이지뷰 증감: {comparison['changes']['page_views']['percentage']}%")
print(f"사용자 증감: {comparison['changes']['users']['percentage']}%")
```

## REST API 엔드포인트

### GET /api/v1/analytics/status

Analytics 설정 상태 확인

**응답:**
```json
{
    "success": true,
    "data": {
        "configured": true,
        "property_id": "123456789",
        "credentials_exists": true,
        "api_available": true
    }
}
```

### GET /api/v1/analytics/overview

전체 개요 메트릭

**쿼리 파라미터:**
- `start_date`: 시작 날짜 (기본값: "30daysAgo")
- `end_date`: 종료 날짜 (기본값: "today")

**날짜 형식:**
- 상대: "today", "yesterday", "7daysAgo", "30daysAgo"
- 절대: "2025-01-01", "2025-01-31"

**예시:**
```bash
curl "http://localhost:8000/api/v1/analytics/overview?start_date=30daysAgo&end_date=today"
```

**응답:**
```json
{
    "success": true,
    "data": {
        "date_range": {
            "start": "30daysAgo",
            "end": "today"
        },
        "metrics": {
            "page_views": 15234,
            "sessions": 8901,
            "users": 6543,
            "new_users": 4321,
            "bounce_rate": 45.67,
            "avg_session_duration": 180.5,
            "engagement_rate": 65.43
        }
    }
}
```

### GET /api/v1/analytics/realtime

실시간 Analytics 데이터

**예시:**
```bash
curl "http://localhost:8000/api/v1/analytics/realtime"
```

**응답:**
```json
{
    "success": true,
    "data": {
        "active_users": 42,
        "active_users_by_country": [
            {"country": "South Korea", "active_users": 25},
            {"country": "United States", "active_users": 10},
            {"country": "Japan", "active_users": 7}
        ],
        "active_users_by_device": [
            {"device": "mobile", "active_users": 28},
            {"device": "desktop", "active_users": 12},
            {"device": "tablet", "active_users": 2}
        ],
        "timestamp": "2025-01-31T10:30:00Z"
    }
}
```

### GET /api/v1/analytics/traffic-sources

트래픽 소스 분석

**쿼리 파라미터:**
- `start_date`: 시작 날짜
- `end_date`: 종료 날짜
- `limit`: 반환할 소스 수 (기본값: 10, 최대: 100)

**예시:**
```bash
curl "http://localhost:8000/api/v1/analytics/traffic-sources?limit=10"
```

**응답:**
```json
{
    "success": true,
    "data": {
        "sources": [
            {
                "source": "google",
                "medium": "organic",
                "sessions": 5432,
                "users": 4321,
                "page_views": 8765
            },
            {
                "source": "facebook",
                "medium": "social",
                "sessions": 1234,
                "users": 987,
                "page_views": 2345
            }
        ],
        "total_count": 10
    }
}
```

### GET /api/v1/analytics/top-posts

인기 포스트 TOP N

**쿼리 파라미터:**
- `start_date`: 시작 날짜
- `end_date`: 종료 날짜
- `limit`: 반환할 포스트 수 (기본값: 10, 최대: 100)

**예시:**
```bash
curl "http://localhost:8000/api/v1/analytics/top-posts?limit=10"
```

**응답:**
```json
{
    "success": true,
    "data": {
        "posts": [
            {
                "page_path": "/blog/seo-guide",
                "page_title": "SEO 완벽 가이드 2025",
                "page_views": 3456,
                "unique_users": 2345,
                "avg_time_on_page": 245.5,
                "bounce_rate": 35.2,
                "engagement_rate": 72.5
            }
        ],
        "total_count": 10
    }
}
```

### GET /api/v1/analytics/post/{post_path}

특정 포스트 성과

**경로 파라미터:**
- `post_path`: 포스트 URL 경로 (예: `/blog/my-post`)

**쿼리 파라미터:**
- `start_date`: 시작 날짜
- `end_date`: 종료 날짜

**예시:**
```bash
curl "http://localhost:8000/api/v1/analytics/post//blog/my-post"
```

### GET /api/v1/analytics/comparison

기간 비교 데이터

**쿼리 파라미터:**
- `current_start`: 현재 기간 시작
- `current_end`: 현재 기간 종료
- `previous_start`: 이전 기간 시작
- `previous_end`: 이전 기간 종료

**예시:**
```bash
curl "http://localhost:8000/api/v1/analytics/comparison"
```

**응답:**
```json
{
    "success": true,
    "data": {
        "current_period": {
            "start_date": "30daysAgo",
            "end_date": "today",
            "metrics": {
                "page_views": 15234,
                "sessions": 8901,
                "users": 6543
            }
        },
        "previous_period": {
            "start_date": "60daysAgo",
            "end_date": "31daysAgo",
            "metrics": {
                "page_views": 12345,
                "sessions": 7890,
                "users": 5432
            }
        },
        "changes": {
            "page_views": {
                "value": 2889,
                "percentage": 23.4
            },
            "users": {
                "value": 1111,
                "percentage": 20.5
            }
        }
    }
}
```

## 대시보드 사용법

### 1. Analytics 페이지 접속

```
http://localhost:8000/
```

네비게이션 바에서 "Analytics" 클릭

### 2. 실시간 방문자

페이지 상단에서 현재 활성 사용자 수와 디바이스/국가별 분포를 실시간으로 확인할 수 있습니다.

### 3. 개요 메트릭

4개의 통계 카드:
- **페이지뷰**: 총 페이지뷰 수 및 증감률
- **사용자**: 총 사용자 수 및 증감률
- **참여율**: 사용자 참여율 및 증감률
- **평균 세션 시간**: 세션당 평균 시간 및 이탈률

### 4. 차트

**트래픽 추이 차트**
- 이전 기간 vs 현재 기간 비교
- 페이지뷰, 세션, 사용자 라인 차트

**트래픽 소스 차트**
- 도넛 차트로 소스별 세션 비율 시각화

**인기 포스트 차트**
- 가로 막대 차트로 TOP 10 포스트 표시

### 5. 테이블

**트래픽 소스 상세 테이블**
- 소스, 매체, 세션, 사용자, 페이지뷰, 비율

**인기 포스트 상세 테이블**
- 제목, 페이지뷰, 방문자, 평균 체류시간, 참여율, 이탈률

### 6. 날짜 범위 선택

우측 상단 드롭다운에서 날짜 범위 선택:
- 최근 7일
- 최근 30일
- 최근 90일

### 7. 자동 새로고침

실시간 데이터는 5분마다 자동으로 새로고침됩니다.

## 성능 최적화

### 1. 캐싱

Google Analytics API는 할당량이 제한되어 있으므로 캐싱을 적극 활용해야 합니다.

**Redis 캐싱 예시:**
```python
from app.core.redis import get_redis
import json

async def get_cached_overview(start_date, end_date):
    redis = await get_redis()
    cache_key = f"analytics:overview:{start_date}:{end_date}"

    # Check cache
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Fetch from API
    analytics_service = get_analytics_service()
    metrics = await analytics_service.get_overview_metrics(start_date, end_date)

    # Cache for 5 minutes
    await redis.setex(
        cache_key,
        300,
        json.dumps(metrics.__dict__)
    )

    return metrics
```

### 2. API 할당량 관리

GA4 Data API 할당량:
- **일일 요청**: 25,000
- **동시 요청**: 10

**할당량 초과 방지:**
1. 캐싱 활용 (최소 5분)
2. 배치 처리 (여러 메트릭을 한 번에)
3. 필요한 데이터만 요청
4. 오프피크 시간에 대량 데이터 수집

### 3. 비동기 처리

```python
import asyncio

async def fetch_all_analytics():
    analytics_service = get_analytics_service()

    # Parallel requests
    overview, realtime, sources, posts = await asyncio.gather(
        analytics_service.get_overview_metrics(),
        analytics_service.get_realtime_metrics(),
        analytics_service.get_traffic_sources(),
        analytics_service.get_top_posts()
    )

    return {
        "overview": overview,
        "realtime": realtime,
        "sources": sources,
        "posts": posts
    }
```

## 트러블슈팅

### 1. "Analytics is not configured" 오류

**원인:**
- `GA_PROPERTY_ID`가 설정되지 않음
- `GA_CREDENTIALS_PATH`가 잘못됨
- 서비스 계정 JSON 파일이 없음

**해결:**
1. `.env` 파일 확인
2. 서비스 계정 JSON 파일 경로 확인
3. 파일 권한 확인 (`chmod 600`)

### 2. "Permission denied" 오류

**원인:**
- 서비스 계정이 GA 속성에 추가되지 않음
- 서비스 계정에 충분한 권한이 없음

**해결:**
1. Google Analytics 관리 > 속성 액세스 관리
2. 서비스 계정 이메일 추가
3. "뷰어" 역할 부여

### 3. "Invalid credentials" 오류

**원인:**
- 서비스 계정 JSON 파일이 손상됨
- 잘못된 프로젝트의 JSON 파일

**해결:**
1. Google Cloud Console에서 새 키 생성
2. JSON 파일 다시 다운로드
3. `.env`의 `GA_CREDENTIALS_PATH` 업데이트

### 4. "Property not found" 오류

**원인:**
- 잘못된 `GA_PROPERTY_ID`
- GA4 대신 Universal Analytics 속성 ID 사용

**해결:**
1. Google Analytics에서 GA4 속성 ID 확인
2. 속성 ID는 숫자만 포함 (예: `123456789`)
3. "UA-" 접두사가 있으면 Universal Analytics (지원 안 됨)

### 5. "Quota exceeded" 오류

**원인:**
- API 일일 할당량 초과
- 너무 많은 동시 요청

**해결:**
1. 캐싱 TTL 증가 (`GA_CACHE_TTL=600`)
2. 요청 빈도 감소
3. 배치 처리 사용
4. Google Cloud Console에서 할당량 확인

### 6. "No data found" 오류

**원인:**
- 지정한 날짜 범위에 데이터 없음
- GA 추적 코드가 설치되지 않음
- 데이터 수집이 아직 시작되지 않음

**해결:**
1. GA4 추적 코드가 웹사이트에 설치되었는지 확인
2. 실시간 보고서에서 데이터 수집 확인
3. 날짜 범위를 더 넓게 설정

## 보안 Best Practices

### 1. 서비스 계정 키 보호

```bash
# 파일 권한 설정
chmod 600 /path/to/service-account.json

# 소유자만 읽기
chown app-user:app-user /path/to/service-account.json
```

### 2. 환경 변수 사용

**절대 하지 말 것:**
```python
# ❌ 하드코딩
PROPERTY_ID = "123456789"
CREDENTIALS_PATH = "/path/to/key.json"
```

**권장 방법:**
```python
# ✅ 환경 변수
from app.core.config import settings

property_id = settings.ga_property_id
credentials_path = settings.ga_credentials_path
```

### 3. 최소 권한 원칙

서비스 계정에는 필요한 최소한의 권한만 부여:
- GA 속성: **뷰어** 역할만
- 편집자, 관리자 역할 불필요

### 4. 키 로테이션

정기적으로 서비스 계정 키 교체 (권장: 90일):

```bash
# 새 키 생성
gcloud iam service-accounts keys create new-key.json \
  --iam-account=blog-analytics-reader@PROJECT-ID.iam.gserviceaccount.com

# 기존 키 삭제
gcloud iam service-accounts keys delete OLD-KEY-ID \
  --iam-account=blog-analytics-reader@PROJECT-ID.iam.gserviceaccount.com
```

## 고급 사용법

### 1. 커스텀 디멘션 추가

```python
from google.analytics.data_v1beta.types import Dimension

# 커스텀 디멘션
request = RunReportRequest(
    property=f"properties/{property_id}",
    dimensions=[
        Dimension(name="customEvent:post_category"),
        Dimension(name="customEvent:author")
    ],
    metrics=[Metric(name="eventCount")]
)
```

### 2. 필터 적용

```python
from google.analytics.data_v1beta.types import FilterExpression, Filter

# 특정 페이지만 필터링
filter_expression = FilterExpression(
    filter=Filter(
        field_name="pagePath",
        string_filter=Filter.StringFilter(
            match_type=Filter.StringFilter.MatchType.BEGINS_WITH,
            value="/blog/"
        )
    )
)
```

### 3. 세그먼트 분석

```python
# 신규 vs 재방문 사용자
dimensions=[
    Dimension(name="newVsReturning")
]
```

### 4. 이벤트 추적

```python
# 커스텀 이벤트 조회
metrics=[
    Metric(name="eventCount"),
    Metric(name="eventValue")
],
dimensions=[
    Dimension(name="eventName")
]
```

## 관련 문서

- [Google Analytics Data API 문서](https://developers.google.com/analytics/devguides/reporting/data/v1)
- [GA4 디멘션 및 메트릭](https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema)
- [서비스 계정 가이드](https://cloud.google.com/iam/docs/service-accounts)
- [대시보드 UI 문서](./DASHBOARD.md)

## 지원

문제가 발생하거나 제안 사항이 있으면 GitHub Issues를 통해 알려주세요.

---

**Google Analytics Integration v1.0.0**
AI 블로그 자동화 시스템
