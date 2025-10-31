# 멀티 블로그 관리 (Multi-Blog Management)

여러 WordPress 사이트를 하나의 시스템에서 동시에 관리하는 고급 기능입니다.

## 목차
- [개요](#개요)
- [주요 기능](#주요-기능)
- [사용 시나리오](#사용-시나리오)
- [WordPress 설정](#wordpress-설정)
- [API 사용법](#api-사용법)
- [데이터베이스 모델](#데이터베이스-모델)
- [모범 사례](#모범-사례)
- [문제 해결](#문제-해결)

## 개요

멀티 블로그 관리 기능을 사용하면 하나의 콘텐츠를 여러 WordPress 사이트에 동시에 발행할 수 있습니다. 이를 통해 다양한 타겟 오디언스에게 동시에 도달하고, 브랜드 존재감을 확대할 수 있습니다.

### 주요 이점
- **효율성**: 한 번 작성한 콘텐츠를 여러 사이트에 즉시 배포
- **중앙 관리**: 모든 사이트를 하나의 대시보드에서 관리
- **성과 추적**: 사이트별 성과 데이터 통합 분석
- **유연성**: 사이트별 커스터마이징 및 스케줄링 지원

## 주요 기능

### 1. 사이트 관리
- WordPress 사이트 등록/수정/삭제
- 사이트별 설정 (카테고리, 태그, 자동 발행)
- 연결 테스트 및 상태 모니터링

### 2. 콘텐츠 발행
- **단일 사이트 발행**: 특정 사이트에 포스트 발행
- **다중 사이트 발행**: 여러 사이트에 동시 발행
- **전체 사이트 발행**: 모든 활성 사이트에 일괄 발행
- **예약 발행**: 원하는 시간에 자동 발행

### 3. 성과 추적
- 사이트별 발행 통계
- 조회수, 클릭수, 전환율 추적
- 전체 사이트 통합 리포트

### 4. 오류 관리
- 실패한 발행 자동 재시도
- 상세한 오류 로그
- 사이트별 상태 모니터링

## 사용 시나리오

### 시나리오 1: 다중 니치 사이트 운영
```
상황: 여행, 음식, 라이프스타일 등 3개의 블로그 운영
목표: 각 블로그에 맞는 콘텐츠를 효율적으로 배포

해결:
1. 3개 WordPress 사이트 등록
2. 사이트별 카테고리/태그 설정
3. 콘텐츠 작성 후 관련 사이트들에만 선택 발행
```

### 시나리오 2: 지역별 블로그 네트워크
```
상황: 서울, 부산, 제주 등 지역별 블로그 운영
목표: 공통 콘텐츠는 모든 사이트에, 지역 콘텐츠는 해당 사이트에만 발행

해결:
1. 지역별 WordPress 사이트 등록
2. 전국 콘텐츠는 "전체 사이트 발행" 사용
3. 지역 콘텐츠는 "다중 사이트 발행"으로 특정 사이트만 선택
```

### 시나리오 3: 테스트 및 프로덕션 분리
```
상황: 테스트 블로그와 실제 서비스 블로그 분리 운영
목표: 콘텐츠를 테스트 후 프로덕션 배포

해결:
1. 테스트 사이트와 프로덕션 사이트 등록
2. 테스트 사이트에 먼저 발행 후 검증
3. 검증 완료 후 프로덕션 사이트에 발행
```

## WordPress 설정

### 1. Application Password 생성

WordPress에서 Application Password를 생성해야 합니다:

```
1. WordPress 관리자 페이지 로그인
2. 사용자 → 프로필 이동
3. "Application Passwords" 섹션 찾기
4. 애플리케이션 이름 입력 (예: "Blog Automation")
5. "Add New Application Password" 클릭
6. 생성된 비밀번호 복사 (공백 포함)
```

⚠️ **중요**: Application Password는 한 번만 표시됩니다. 안전한 곳에 저장하세요.

### 2. REST API 활성화 확인

```bash
# WordPress REST API 테스트
curl https://your-wordpress-site.com/wp-json/wp/v2/posts

# 정상 응답: 포스트 목록 JSON
# 오류 응답: REST API가 비활성화되었거나 접근 불가
```

### 3. 사용자 권한 설정

Application Password를 사용하는 계정에 적절한 권한이 필요합니다:
- **최소 권한**: Editor (포스트 발행 가능)
- **권장 권한**: Administrator (모든 기능 접근)

### 4. SSL 인증서 (HTTPS)

보안을 위해 HTTPS가 필수입니다:
```bash
# Let's Encrypt를 사용한 무료 SSL 인증서
sudo certbot --nginx -d your-wordpress-site.com
```

## API 사용법

### 1. 사이트 등록

새 WordPress 사이트를 등록합니다:

```bash
curl -X POST "http://localhost:8000/api/v1/multi-blog/sites" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "여행 블로그",
    "url": "https://travel-blog.com",
    "username": "admin",
    "app_password": "xxxx xxxx xxxx xxxx xxxx xxxx",
    "is_active": true,
    "default_category": "Travel",
    "default_tags": ["여행", "맛집", "관광"],
    "auto_publish": false,
    "publish_delay_minutes": 0,
    "description": "국내외 여행 정보 블로그",
    "language": "ko",
    "timezone": "Asia/Seoul"
  }'
```

**응답:**
```json
{
  "success": true,
  "site": {
    "id": 1,
    "name": "여행 블로그",
    "url": "https://travel-blog.com",
    "api_url": "https://travel-blog.com/wp-json/wp/v2",
    "is_active": true,
    "auto_publish": false,
    "created_at": "2025-10-31T10:00:00"
  }
}
```

### 2. 사이트 목록 조회

등록된 모든 사이트를 조회합니다:

```bash
curl -X GET "http://localhost:8000/api/v1/multi-blog/sites?is_active=true&limit=10"
```

**응답:**
```json
{
  "success": true,
  "total": 3,
  "sites": [
    {
      "id": 1,
      "name": "여행 블로그",
      "url": "https://travel-blog.com",
      "is_active": true,
      "auto_publish": false,
      "total_posts_published": 42,
      "last_published_at": "2025-10-31T09:30:00",
      "created_at": "2025-10-30T10:00:00"
    }
  ]
}
```

### 3. 연결 테스트

WordPress 사이트 연결을 테스트합니다:

```bash
curl -X POST "http://localhost:8000/api/v1/multi-blog/sites/1/test-connection"
```

**응답:**
```json
{
  "success": true,
  "message": "Connection successful",
  "site_info": {
    "name": "여행 블로그",
    "url": "https://travel-blog.com",
    "posts_count": "127"
  }
}
```

### 4. 특정 사이트에 발행

하나의 사이트에만 포스트를 발행합니다:

```bash
curl -X POST "http://localhost:8000/api/v1/multi-blog/publish/site" \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": 1,
    "post_id": 100,
    "schedule_time": null
  }'
```

**응답:**
```json
{
  "success": true,
  "site_post": {
    "id": 1,
    "site_id": 1,
    "post_id": 100,
    "status": "published",
    "wp_post_id": 456,
    "wp_url": "https://travel-blog.com/2025/10/31/post-title/",
    "wp_status": "publish",
    "scheduled_for": null,
    "published_at": "2025-10-31T10:15:00",
    "error_message": null
  }
}
```

### 5. 여러 사이트에 동시 발행

여러 사이트에 동시에 발행합니다:

```bash
curl -X POST "http://localhost:8000/api/v1/multi-blog/publish/multiple" \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 100,
    "site_ids": [1, 2, 3],
    "schedule_time": null
  }'
```

**응답:**
```json
{
  "success": true,
  "total_sites": 3,
  "published_sites": 3,
  "site_posts": [
    {
      "id": 1,
      "site_id": 1,
      "status": "published",
      "wp_url": "https://travel-blog.com/...",
      "error_message": null
    },
    {
      "id": 2,
      "site_id": 2,
      "status": "published",
      "wp_url": "https://food-blog.com/...",
      "error_message": null
    },
    {
      "id": 3,
      "site_id": 3,
      "status": "published",
      "wp_url": "https://lifestyle-blog.com/...",
      "error_message": null
    }
  ]
}
```

### 6. 모든 활성 사이트에 발행

모든 활성 상태인 사이트에 발행합니다:

```bash
curl -X POST "http://localhost:8000/api/v1/multi-blog/publish/all" \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 100,
    "schedule_time": null
  }'
```

### 7. 예약 발행

원하는 시간에 자동으로 발행되도록 예약합니다:

```bash
curl -X POST "http://localhost:8000/api/v1/multi-blog/publish/site" \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": 1,
    "post_id": 100,
    "schedule_time": "2025-11-01T09:00:00"
  }'
```

**응답:**
```json
{
  "success": true,
  "site_post": {
    "id": 1,
    "site_id": 1,
    "post_id": 100,
    "status": "pending",
    "scheduled_for": "2025-11-01T09:00:00",
    "published_at": null,
    "error_message": null
  }
}
```

### 8. 사이트별 포스트 조회

특정 사이트에 발행된 포스트 목록을 조회합니다:

```bash
curl -X GET "http://localhost:8000/api/v1/multi-blog/site-posts?site_id=1&status=published&limit=20"
```

**응답:**
```json
{
  "success": true,
  "total": 42,
  "site_posts": [
    {
      "id": 1,
      "site_id": 1,
      "post_id": 100,
      "wp_post_id": 456,
      "wp_url": "https://travel-blog.com/...",
      "wp_status": "publish",
      "status": "published",
      "scheduled_for": null,
      "published_at": "2025-10-31T10:15:00",
      "views": 1250,
      "clicks": 87,
      "conversions": 12,
      "error_message": null,
      "retry_count": 0
    }
  ]
}
```

### 9. 사이트 통계 조회

특정 사이트의 통계를 조회합니다:

```bash
curl -X GET "http://localhost:8000/api/v1/multi-blog/stats/1"
```

**응답:**
```json
{
  "success": true,
  "statistics": {
    "site_id": 1,
    "site_name": "여행 블로그",
    "total_posts": 42,
    "published": 40,
    "pending": 1,
    "failed": 1,
    "total_views": 52000,
    "total_clicks": 3500,
    "total_conversions": 420,
    "last_published": "2025-10-31T10:15:00"
  }
}
```

### 10. 전체 사이트 통계

모든 사이트의 통계를 조회합니다:

```bash
curl -X GET "http://localhost:8000/api/v1/multi-blog/stats"
```

**응답:**
```json
{
  "success": true,
  "total_sites": 3,
  "statistics": [
    {
      "site_id": 1,
      "site_name": "여행 블로그",
      "total_posts": 42,
      "published": 40,
      "pending": 1,
      "failed": 1,
      "total_views": 52000,
      "total_clicks": 3500,
      "total_conversions": 420,
      "last_published": "2025-10-31T10:15:00"
    },
    {
      "site_id": 2,
      "site_name": "음식 블로그",
      "total_posts": 38,
      "published": 38,
      "pending": 0,
      "failed": 0,
      "total_views": 48000,
      "total_clicks": 3200,
      "total_conversions": 380,
      "last_published": "2025-10-31T09:00:00"
    }
  ]
}
```

### 11. 사이트 업데이트

사이트 정보를 업데이트합니다:

```bash
curl -X PUT "http://localhost:8000/api/v1/multi-blog/sites/1" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false,
    "default_category": "New Category",
    "auto_publish": true
  }'
```

### 12. 사이트 삭제

사이트를 삭제합니다 (관련 포스트 데이터도 함께 삭제):

```bash
curl -X DELETE "http://localhost:8000/api/v1/multi-blog/sites/1"
```

## 데이터베이스 모델

### WordPressSite 모델

WordPress 사이트 정보를 저장합니다.

```python
class WordPressSite:
    id: int                          # 사이트 ID
    name: str                        # 사이트 이름
    url: str                         # WordPress URL
    api_url: str                     # REST API URL
    username: str                    # WordPress 사용자명
    app_password: str                # Application Password
    is_active: bool                  # 활성화 상태
    default_category: str            # 기본 카테고리
    default_tags: List[str]          # 기본 태그
    auto_publish: bool               # 자동 발행 여부
    publish_delay_minutes: int       # 발행 지연 시간(분)
    total_posts_published: int       # 총 발행 포스트 수
    last_published_at: datetime      # 마지막 발행 시간
    description: str                 # 사이트 설명
    language: str                    # 언어
    timezone: str                    # 타임존
    created_at: datetime             # 생성일
    updated_at: datetime             # 수정일
```

### SitePost 모델

사이트별 포스트 발행 상태를 추적합니다.

```python
class SitePost:
    id: int                          # SitePost ID
    site_id: int                     # 사이트 ID (FK)
    post_id: int                     # 포스트 ID (FK)
    wp_post_id: int                  # WordPress 포스트 ID
    wp_url: str                      # WordPress 포스트 URL
    wp_status: str                   # WordPress 상태
    status: str                      # 발행 상태 (pending/published/failed)
    scheduled_for: datetime          # 예약 시간
    published_at: datetime           # 발행 시간
    error_message: str               # 오류 메시지
    retry_count: int                 # 재시도 횟수
    max_retries: int                 # 최대 재시도 횟수
    views: int                       # 조회수
    clicks: int                      # 클릭수
    conversions: int                 # 전환수
    created_at: datetime             # 생성일
    updated_at: datetime             # 수정일
```

## 모범 사례

### 1. 사이트 설정

```python
# ✅ 좋은 예: 명확한 사이트 이름과 설정
{
    "name": "여행 블로그 - 국내 여행",
    "url": "https://travel-korea.com",
    "username": "api_user",
    "app_password": "xxxx xxxx xxxx xxxx",
    "default_category": "Domestic Travel",
    "default_tags": ["국내여행", "관광지", "맛집"],
    "auto_publish": false,  # 수동 검토 후 발행
    "description": "국내 여행 정보 전문 블로그"
}

# ❌ 나쁜 예: 모호한 설정
{
    "name": "Blog1",
    "url": "https://example.com",
    "username": "admin",  # 보안 취약
    "app_password": "simple_password",
    "default_category": "Uncategorized",
    "auto_publish": true  # 검증 없이 자동 발행
}
```

### 2. 발행 전략

```python
# ✅ 좋은 예: 단계적 발행
# 1. 테스트 사이트에 먼저 발행
publish_to_site(site_id=test_site_id, post_id=100)

# 2. 검증 후 프로덕션 사이트에 발행
if validation_passed:
    publish_to_multiple_sites(
        post_id=100,
        site_ids=[prod_site1, prod_site2],
        schedule_time="2025-11-01T09:00:00"  # 최적 시간에 예약
    )

# ❌ 나쁜 예: 검증 없이 즉시 전체 발행
publish_to_all_sites(post_id=100)  # 오류 발생 시 모든 사이트 영향
```

### 3. 오류 처리

```python
# ✅ 좋은 예: 개별 사이트 오류 격리
for site_id in site_ids:
    try:
        publish_to_site(site_id, post_id)
    except Exception as e:
        log_error(f"Site {site_id} failed: {e}")
        continue  # 다른 사이트는 계속 진행

# ❌ 나쁜 예: 전체 작업 중단
for site_id in site_ids:
    publish_to_site(site_id, post_id)  # 하나 실패하면 전체 중단
```

### 4. 콘텐츠 차별화

```python
# ✅ 좋은 예: 사이트별 커스터마이징
for site in sites:
    customized_post = customize_for_site(post, site)
    publish_to_site(site.id, customized_post.id)

# 사이트별 다른 카테고리/태그 사용
# 사이트의 독자층에 맞게 톤앤매너 조정
# 발행 시간 분산 (중복 콘텐츠 패널티 방지)

# ❌ 나쁜 예: 완전히 동일한 콘텐츠
publish_to_all_sites(post_id=100)  # 검색엔진 중복 콘텐츠 패널티 위험
```

### 5. 성과 모니터링

```python
# ✅ 좋은 예: 정기적 성과 확인
def monitor_sites():
    stats = get_all_sites_statistics()

    for site_stats in stats:
        if site_stats['failed'] > 5:
            alert(f"Site {site_stats['site_name']} has high failure rate")

        if site_stats['total_views'] < threshold:
            analyze_low_performance(site_stats['site_id'])

# 매일 실행
schedule.every().day.at("09:00").do(monitor_sites)

# ❌ 나쁜 예: 모니터링 없음
publish_to_all_sites(post_id=100)
# ... 발행 후 확인하지 않음
```

## 문제 해결

### 문제 1: 인증 실패 (401 Unauthorized)

**증상:**
```json
{
  "success": false,
  "error": "HTTP 401: Unauthorized"
}
```

**원인:**
- 잘못된 Application Password
- 사용자 권한 부족
- Application Password 기능 비활성화

**해결 방법:**
```bash
# 1. Application Password 재생성
# WordPress → 사용자 → 프로필 → Application Passwords

# 2. 사용자 권한 확인
# 최소 Editor 권한 필요

# 3. 연결 테스트
curl -X POST "http://localhost:8000/api/v1/multi-blog/sites/1/test-connection"

# 4. 사이트 정보 업데이트
curl -X PUT "http://localhost:8000/api/v1/multi-blog/sites/1" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "correct_username",
    "app_password": "xxxx xxxx xxxx xxxx"
  }'
```

### 문제 2: 타임아웃 오류

**증상:**
```json
{
  "success": false,
  "error": "Connection timeout"
}
```

**원인:**
- WordPress 서버 응답 지연
- 네트워크 문제
- WordPress 플러그인 충돌

**해결 방법:**
```python
# 1. 타임아웃 설정 증가 (서비스 코드에서)
response = requests.post(
    f"{site.api_url}/posts",
    timeout=60  # 30초 → 60초로 증가
)

# 2. WordPress 서버 성능 확인
# - PHP 메모리 제한 증가
# - 캐싱 플러그인 설치
# - 불필요한 플러그인 비활성화

# 3. 재시도 로직 활용
# SitePost의 retry_count가 자동으로 관리됨
```

### 문제 3: 중복 콘텐츠 패널티

**증상:**
- 검색 순위 하락
- Google Search Console 경고

**원인:**
- 여러 사이트에 동일한 콘텐츠 발행
- 발행 시간이 동일

**해결 방법:**
```python
# 1. 사이트별 콘텐츠 커스터마이징
# - 서론/결론 다르게 작성
# - 사이트별 독특한 관점 추가
# - 다른 이미지 사용

# 2. 발행 시간 분산
schedule_times = [
    "2025-11-01T09:00:00",  # 사이트 1
    "2025-11-01T14:00:00",  # 사이트 2
    "2025-11-02T09:00:00",  # 사이트 3
]

for i, site_id in enumerate(site_ids):
    publish_to_site(
        site_id=site_id,
        post_id=post_id,
        schedule_time=schedule_times[i]
    )

# 3. Canonical URL 설정
# 원본 사이트를 canonical로 지정
```

### 문제 4: 카테고리/태그 불일치

**증상:**
```json
{
  "success": false,
  "error": "Invalid category"
}
```

**원인:**
- 대상 WordPress 사이트에 카테고리가 존재하지 않음
- 카테고리 ID가 다름

**해결 방법:**
```bash
# 1. 각 사이트에서 카테고리 사전 생성
# WordPress → 포스트 → 카테고리

# 2. 사이트별 기본 카테고리 설정
curl -X PUT "http://localhost:8000/api/v1/multi-blog/sites/1" \
  -H "Content-Type: application/json" \
  -d '{
    "default_category": "Travel",
    "default_tags": ["여행", "관광"]
  }'

# 3. 카테고리 매핑 테이블 사용
# 사이트 1: "Travel" → WordPress 카테고리 ID: 5
# 사이트 2: "여행" → WordPress 카테고리 ID: 3
```

### 문제 5: 발행 실패 후 재시도

**증상:**
- 일부 사이트에 발행 실패
- status: "failed"

**해결 방법:**
```bash
# 1. 실패한 포스트 조회
curl -X GET "http://localhost:8000/api/v1/multi-blog/site-posts?status=failed"

# 2. 오류 메시지 확인
# error_message 필드에서 원인 파악

# 3. 문제 해결 후 재발행
curl -X POST "http://localhost:8000/api/v1/multi-blog/publish/site" \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": 1,
    "post_id": 100
  }'

# 자동 재시도는 최대 3회까지 수행됨
```

## 보안 고려사항

### 1. Application Password 관리

```python
# ✅ 좋은 예: 환경 변수 사용
import os

app_password = os.getenv('WP_SITE1_APP_PASSWORD')

# ❌ 나쁜 예: 하드코딩
app_password = "xxxx xxxx xxxx xxxx"  # 절대 금지!
```

### 2. HTTPS 사용

```python
# ✅ 좋은 예: HTTPS만 허용
if not site.url.startswith('https://'):
    raise ValueError("Only HTTPS URLs are allowed")

# ❌ 나쁜 예: HTTP 허용
# HTTP로 인증 정보 전송 (보안 취약)
```

### 3. 권한 최소화

```
✅ 좋은 예:
- 발행만 필요한 경우: Editor 권한
- 사이트 설정이 필요한 경우: Administrator 권한

❌ 나쁜 예:
- 모든 사이트에 Administrator 권한 (과도한 권한)
```

### 4. 정기적 비밀번호 갱신

```bash
# 매 3개월마다 Application Password 갱신
# 1. WordPress에서 새 Application Password 생성
# 2. 시스템에서 사이트 정보 업데이트
# 3. 기존 Application Password 삭제
```

## 성능 최적화

### 1. 배치 크기 제한

```python
# ✅ 좋은 예: 사이트를 그룹으로 나눠 발행
site_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
batch_size = 3

for i in range(0, len(site_ids), batch_size):
    batch = site_ids[i:i + batch_size]
    publish_to_multiple_sites(post_id, batch)
    time.sleep(2)  # 서버 부하 분산

# ❌ 나쁜 예: 한 번에 모든 사이트
publish_to_multiple_sites(post_id, site_ids)  # 서버 과부하
```

### 2. 비동기 발행

```python
# 향후 기능: 비동기 발행 지원 예정
async def publish_async():
    tasks = [
        publish_to_site_async(site_id, post_id)
        for site_id in site_ids
    ]
    await asyncio.gather(*tasks)
```

### 3. 캐싱 활용

```python
# 사이트 정보 캐싱
# 매번 DB 조회 대신 캐시 사용
# Redis 또는 메모리 캐시 활용 권장
```

## 관련 문서

- [WordPress REST API 공식 문서](https://developer.wordpress.org/rest-api/)
- [Application Passwords 가이드](https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/)
- [콘텐츠 최적화 가이드](./CONTENT_OPTIMIZATION.md)
- [경쟁자 분석 가이드](./COMPETITOR_ANALYSIS.md)

## 추가 지원

문제가 발생하거나 기능 요청이 있으시면 이슈를 등록해주세요:
- GitHub Issues: [여기에 이슈 등록]
- 이메일 지원: support@example.com
