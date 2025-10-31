# One-Click Blog Automation System

완전 자동 파이프라인 시스템 - 키워드부터 발행까지 원클릭으로 자동화

## 개요

One-Click Automation은 블로그 콘텐츠 생성 전체 과정을 단 하나의 API 호출로 자동화하는 시스템입니다.

### 주요 기능

1. **완전 자동화**: 키워드 리서치부터 WordPress 발행까지 자동 처리
2. **실시간 진행률 추적**: 각 단계별 진행 상황을 실시간으로 확인
3. **상태 관리**: 데이터베이스에 워크플로우 상태 저장 및 복구
4. **에러 핸들링**: 개별 포스트 실패 시에도 다른 포스트는 계속 처리
5. **멀티 LLM 지원**: Claude, ChatGPT, Gemini 중 선택 가능

## 워크플로우 프로세스

```
1. 키워드 리서치 (Keyword Research)
   ↓
2. 키워드 선택 (Select Top Keywords by Golden Score)
   ↓
3. 각 키워드별로:
   a. 콘텐츠 생성 (Content Generation)
   ↓
   b. 이미지 생성 (Image Generation)
   ↓
   c. 광고 삽입 (AdSense Insertion)
   ↓
   d. 워드프레스 발행 (WordPress Publishing)
   ↓
4. 완료 (Completed)
```

## API 엔드포인트

### 1. 워크플로우 시작

**POST** `/api/v1/workflow/one-click-publish`

```json
{
  "seed_keywords": ["블로그 SEO", "콘텐츠 마케팅", "디지털 마케팅"],
  "num_posts": 2,
  "publish_immediately": true,
  "llm_provider": "claude"
}
```

**응답:**
```json
{
  "workflow_id": 1,
  "celery_task_id": "abc123...",
  "status": "running",
  "message": "Workflow started successfully. Generating 2 post(s) from 3 seed keyword(s).",
  "estimated_duration_minutes": 10
}
```

### 2. 진행 상황 확인

**GET** `/api/v1/workflow/{workflow_id}/status`

```json
{
  "id": 1,
  "workflow_type": "one_click",
  "status": "running",
  "current_step": "post_1_generate_content",
  "progress_percentage": 45,
  "steps": {
    "research_keywords": {
      "status": "completed",
      "started_at": "2025-01-31T09:00:00Z",
      "completed_at": "2025-01-31T09:01:30Z",
      "result": {"count": 20}
    },
    "post_1_generate_content": {
      "status": "running",
      "started_at": "2025-01-31T09:01:35Z"
    }
  },
  "statistics": {
    "keywords_researched": 20,
    "posts_created": 0,
    "posts_published": 0,
    "errors": 0
  },
  "started_at": "2025-01-31T09:00:00Z",
  "duration_seconds": 95.5
}
```

### 3. 워크플로우 취소

**POST** `/api/v1/workflow/{workflow_id}/cancel`

```json
{
  "success": true,
  "workflow_id": 1,
  "status": "cancelled",
  "message": "Workflow cancelled successfully"
}
```

### 4. 워크플로우 목록 조회

**GET** `/api/v1/workflow/list?page=1&page_size=20&status=completed`

```json
{
  "workflows": [
    {
      "id": 1,
      "workflow_type": "one_click",
      "status": "completed",
      "progress_percentage": 100,
      "statistics": {
        "keywords_researched": 20,
        "posts_created": 2,
        "posts_published": 2,
        "errors": 0
      },
      "created_at": "2025-01-31T09:00:00Z",
      "completed_at": "2025-01-31T09:15:30Z",
      "duration_seconds": 930
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

### 5. 워크플로우 삭제

**DELETE** `/api/v1/workflow/{workflow_id}`

```json
{
  "success": true,
  "workflow_id": 1,
  "message": "Workflow deleted successfully"
}
```

## 데이터베이스 모델

### WorkflowRun 테이블

```python
class WorkflowRun(Base):
    """워크플로우 실행 추적 모델"""
    id: int                          # Primary key
    workflow_type: str               # one_click, scheduled, manual
    celery_task_id: str              # Celery task ID

    # 설정
    seed_keywords: List[str]         # 시드 키워드
    num_posts: int                   # 생성할 포스트 수
    publish_immediately: bool        # 즉시 발행 여부
    llm_provider: str                # LLM 제공자

    # 상태 추적
    status: str                      # pending, running, completed, failed, cancelled
    current_step: str                # 현재 진행 중인 단계
    progress_percentage: int         # 진행률 (0-100)
    steps: Dict                      # 각 단계별 상세 정보

    # 결과
    keywords_researched: int         # 리서치한 키워드 수
    posts_created: int               # 생성된 포스트 수
    posts_published: int             # 발행된 포스트 수
    errors_count: int                # 에러 수
    results: Dict                    # 전체 결과
    errors: List[Dict]               # 에러 목록

    # 타이밍
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
```

## 사용 예시

### Python 클라이언트

```python
import requests
import time

# 1. 워크플로우 시작
response = requests.post(
    "http://localhost:8000/api/v1/workflow/one-click-publish",
    json={
        "seed_keywords": ["블로그 SEO", "콘텐츠 마케팅"],
        "num_posts": 2,
        "publish_immediately": True,
        "llm_provider": "claude"
    }
)

workflow_data = response.json()
workflow_id = workflow_data["workflow_id"]
print(f"Workflow started: {workflow_id}")

# 2. 진행 상황 모니터링
while True:
    status_response = requests.get(
        f"http://localhost:8000/api/v1/workflow/{workflow_id}/status"
    )
    status = status_response.json()

    print(f"Progress: {status['progress_percentage']}% - {status['current_step']}")

    if status["status"] in ["completed", "failed", "cancelled"]:
        break

    time.sleep(5)

# 3. 최종 결과 확인
print(f"Workflow {status['status']}")
print(f"Posts created: {status['statistics']['posts_created']}")
print(f"Posts published: {status['statistics']['posts_published']}")
print(f"Duration: {status['duration_seconds']}s")
```

### cURL 예시

```bash
# 워크플로우 시작
curl -X POST http://localhost:8000/api/v1/workflow/one-click-publish \
  -H "Content-Type: application/json" \
  -d '{
    "seed_keywords": ["블로그 SEO"],
    "num_posts": 1,
    "publish_immediately": true,
    "llm_provider": "claude"
  }'

# 진행 상황 확인
curl http://localhost:8000/api/v1/workflow/1/status

# 워크플로우 취소
curl -X POST http://localhost:8000/api/v1/workflow/1/cancel

# 워크플로우 목록 조회
curl http://localhost:8000/api/v1/workflow/list?page=1&status=completed
```

## 진행률 추적

워크플로우는 다음과 같은 단계로 구성되며, 각 단계는 전체 진행률에 기여합니다:

- **키워드 리서치**: 0% → 20%
- **각 포스트 처리**: 20% → 95% (포스트 수에 따라 분배)
  - 콘텐츠 생성: 25%
  - 이미지 생성: 25%
  - 광고 삽입: 25%
  - 발행: 25%
- **완료**: 95% → 100%

## 에러 처리

### 개별 포스트 실패

특정 포스트 생성이 실패해도 다른 포스트는 계속 처리됩니다:

```json
{
  "status": "completed",
  "statistics": {
    "posts_created": 1,
    "posts_published": 1,
    "errors": 1
  },
  "errors": [
    {
      "post_number": 2,
      "keyword": "실패한 키워드",
      "error": "Content generation failed: API rate limit exceeded"
    }
  ]
}
```

### 전체 워크플로우 실패

키워드 리서치와 같은 초기 단계가 실패하면 전체 워크플로우가 실패합니다:

```json
{
  "status": "failed",
  "current_step": "research_keywords",
  "errors": [
    {
      "error": "Keyword research failed: API key not configured"
    }
  ]
}
```

## 성능 고려사항

### 예상 소요 시간

포스트 1개당 평균 5분 소요:
- 키워드 리서치: 30초
- 콘텐츠 생성: 2분
- 이미지 생성: 1.5분
- 광고 삽입: 5초
- 발행: 1분

### 동시 실행

여러 워크플로우를 동시에 실행할 수 있습니다. Celery Worker의 concurrency 설정에 따라 결정됩니다.

```bash
# 기본값: 4개의 worker
celery -A app.tasks.celery_tasks worker --concurrency=4
```

### 리소스 사용

- CPU: 콘텐츠 생성 시 높음
- 메모리: 포스트당 약 200MB
- 네트워크: API 호출이 많음 (LLM, 이미지 생성, WordPress)
- 디스크: 이미지 저장 시 포스트당 약 5MB

## 모니터링

### Celery Flower

Celery 작업 모니터링:

```bash
# Flower 시작
make celery-flower

# 브라우저에서 확인
# http://localhost:5555
```

### 로그 확인

```bash
# Celery worker 로그
tail -f logs/celery-worker.log

# Beat scheduler 로그
tail -f logs/celery-beat.log

# FastAPI 로그
tail -f logs/app.log
```

### Prometheus 메트릭

```bash
# 메트릭 확인
curl http://localhost:8000/metrics

# Grafana 대시보드
# http://localhost:3000
```

## 트러블슈팅

### 워크플로우가 시작되지 않음

1. Celery Worker가 실행 중인지 확인:
   ```bash
   make celery-status
   ```

2. Redis 연결 확인:
   ```bash
   redis-cli ping
   ```

3. 로그 확인:
   ```bash
   tail -f logs/celery-worker.log
   ```

### 워크플로우가 멈춤

1. 워크플로우 상태 확인:
   ```bash
   curl http://localhost:8000/api/v1/workflow/{id}/status
   ```

2. Celery 작업 확인:
   ```bash
   # Flower에서 확인
   http://localhost:5555
   ```

3. 필요 시 재시작:
   ```bash
   make celery-stop
   make celery-all
   ```

### API 호출 실패

1. API 키 확인:
   ```bash
   # .env 파일에서 확인
   grep API_KEY .env
   ```

2. 네트워크 연결 확인

3. Rate limit 확인 (특히 OpenAI, Anthropic)

## 베스트 프랙티스

### 1. 시드 키워드 선택

- 3-5개의 관련 키워드 사용
- 너무 광범위하거나 너무 구체적이지 않게
- 한국어 키워드 사용 시 자연스러운 표현 사용

```json
{
  "seed_keywords": [
    "블로그 SEO",      // Good
    "콘텐츠 마케팅",    // Good
    "검색엔진 최적화"   // Good
  ]
}
```

### 2. 포스트 수 설정

- 처음에는 1-2개로 테스트
- 안정적으로 동작하면 3-5개로 증가
- API rate limit 고려

### 3. LLM 제공자 선택

- **Claude (기본)**: 가장 자연스러운 한국어, 긴 콘텐츠에 강함
- **ChatGPT**: 빠른 응답, 다양한 스타일
- **Gemini**: 무료 tier 제공, 멀티모달 기능

### 4. 모니터링

- 워크플로우 목록을 주기적으로 확인
- 실패한 워크플로우는 에러 메시지 분석
- 성공률 추적

## 다음 단계

이 시스템은 계속 발전하고 있습니다. 다음 기능이 추가될 예정입니다:

1. **알림 시스템**: 이메일/Slack 알림
2. **SEO 점수 계산**: 콘텐츠 품질 검증
3. **Google Analytics 연동**: 성과 측정
4. **대시보드 UI**: 시각적 관리 인터페이스

## 관련 문서

- [멀티 LLM 지원](./MULTI_LLM_SUPPORT.md)
- [Celery Beat 스케줄러](./CELERY_BEAT.md)
- [모니터링 시스템](./MONITORING.md)
- [API 문서](http://localhost:8000/docs)
