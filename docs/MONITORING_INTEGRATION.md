# 모니터링 시스템 통합 가이드

블로그 자동화 시스템에 모니터링 컴포넌트가 어떻게 통합되어 있는지 설명합니다.

## 📋 개요

모니터링 시스템은 FastAPI 애플리케이션에 다음과 같이 통합되어 있습니다:

1. **Prometheus 메트릭 수집** - Middleware를 통한 자동 메트릭 수집
2. **고급 헬스체크** - 데이터베이스, Redis, 시스템 리소스 모니터링
3. **Sentry 에러 추적** - 애플리케이션 시작 시 자동 초기화

## 🏗️ 통합 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                   │
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │            Prometheus Middleware                    │ │
│  │  • HTTP 요청/응답 메트릭 수집                       │ │
│  │  • 요청 처리 시간 측정                              │ │
│  │  • 진행 중인 요청 추적                              │ │
│  └────────────────────────────────────────────────────┘ │
│                          │                                │
│  ┌────────────────────────────────────────────────────┐ │
│  │            Business Logic Layer                     │ │
│  │  • KeywordResearchService                           │ │
│  │  • ContentGeneratorService                          │ │
│  │  • ImageGeneratorService                            │ │
│  │  → 비즈니스 메트릭 기록                             │ │
│  └────────────────────────────────────────────────────┘ │
│                          │                                │
│  ┌────────────────────────────────────────────────────┐ │
│  │            Error Handling Layer                     │ │
│  │  • Global Exception Handlers                        │ │
│  │  → Sentry로 에러 전송                               │ │
│  │  → 에러 메트릭 기록                                 │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
            │                 │                 │
            ▼                 ▼                 ▼
    ┌───────────┐     ┌──────────┐     ┌──────────┐
    │ /metrics  │     │ /health  │     │  Sentry  │
    │ endpoint  │     │ endpoint │     │   Cloud  │
    └───────────┘     └──────────┘     └──────────┘
            │                 │
            ▼                 ▼
    ┌───────────┐     ┌──────────┐
    │Prometheus │     │ Grafana  │
    └───────────┘     └──────────┘
```

## 🔧 통합 세부사항

### 1. FastAPI 애플리케이션 초기화 (`app/main.py`)

#### Lifespan 이벤트

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("application_starting", env=settings.app_env)

    # Sentry 초기화
    if settings.enable_metrics:
        init_sentry()
        logger.info("sentry_initialized")

    # 데이터베이스 초기화
    await init_db()

    yield

    # Shutdown
    await close_db()
```

**주요 포인트:**
- `enable_metrics` 설정에 따라 Sentry 선택적 초기화
- 데이터베이스 초기화 전에 모니터링 시스템 초기화
- Graceful shutdown 지원

#### Middleware 스택

```python
# Prometheus metrics (가장 먼저, 모든 요청 캡처)
if settings.enable_metrics:
    app.add_middleware(PrometheusMiddleware)

# CORS
app.add_middleware(CORSMiddleware, ...)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request logging (metrics 엔드포인트 제외)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.url.path in ["/metrics", "/health"]:
        return await call_next(request)
    # ... 로깅 로직
```

**Middleware 순서 중요:**
1. **PrometheusMiddleware**: 가장 먼저 실행되어 모든 요청 캡처
2. **CORSMiddleware**: CORS 헤더 처리
3. **GZipMiddleware**: 응답 압축
4. **log_requests**: 애플리케이션 로깅

### 2. 엔드포인트

#### Health Check (`GET /health`)

```python
@app.get("/health")
async def health_check():
    """고급 헬스체크 엔드포인트"""
    health_service = HealthCheckService()
    health_data = await health_service.check_health()

    # HealthStatus enum을 문자열로 변환
    health_data["status"] = health_data["status"].value
    for service_name, service_data in health_data["services"].items():
        service_data["status"] = service_data["status"].value

    status_code = (
        200 if health_data["status"] == "healthy"
        else 503
    )

    return JSONResponse(content=health_data, status_code=status_code)
```

**제공 정보:**
- 전체 시스템 상태 (healthy/degraded/unhealthy)
- 데이터베이스 연결 상태 및 레이턴시
- Redis 연결 상태 및 레이턴시
- 디스크 사용률 (%, GB)
- 메모리 사용률 (%, GB)
- 타임스탬프 및 버전 정보

#### Metrics Endpoint (`GET /metrics`)

```python
@app.get("/metrics")
async def metrics():
    """Prometheus 메트릭 엔드포인트"""
    from fastapi.responses import Response

    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )
```

**제공 메트릭:**
- HTTP 요청 메트릭 (총 요청, 처리 시간, 진행 중인 요청)
- 비즈니스 메트릭 (키워드, 콘텐츠, 이미지, 포스트)
- 성능 메트릭 (생성 시간, 처리 시간)
- 에러 메트릭 (에러 수, API 에러)

#### Root Endpoint (`GET /`)

```python
@app.get("/")
async def root():
    """API 정보 엔드포인트"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/health",
        "metrics": "/metrics" if settings.enable_metrics else "disabled",
        "api": settings.api_v1_prefix,
    }
```

### 3. 모니터링 모듈 구조 (`app/monitoring/`)

```
app/monitoring/
├── __init__.py          # 모듈 공개 API
├── metrics.py           # Prometheus 메트릭 수집
├── healthcheck.py       # 고급 헬스체크
└── sentry.py           # Sentry 에러 추적
```

#### `__init__.py` - 공개 API

```python
from .metrics import (
    PrometheusMiddleware,
    REGISTRY,
    http_requests_total,
    http_request_duration_seconds,
    http_requests_in_progress,
    keywords_researched_total,
    content_generated_total,
    images_generated_total,
    posts_published_total,
    errors_total,
)
from .healthcheck import HealthCheckService, HealthStatus
from .sentry import init_sentry, capture_exception, capture_message
```

**사용 예시:**

```python
# Metrics 기록
from app.monitoring import keywords_researched_total
keywords_researched_total.labels(status="success").inc()

# 에러 캡처
from app.monitoring import capture_exception
try:
    # 작업 수행
    pass
except Exception as e:
    capture_exception(e, context={"user_id": user_id})

# 헬스체크
from app.monitoring import HealthCheckService
health_service = HealthCheckService()
health_status = await health_service.check_health()
```

## 📊 비즈니스 로직에서 메트릭 사용

### KeywordResearchService 예시

```python
from app.monitoring import (
    keywords_researched_total,
    keyword_research_duration_seconds,
    errors_total
)

class KeywordResearchService:
    async def research_keywords(self, seed_keyword: str):
        with keyword_research_duration_seconds.time():
            try:
                # 키워드 리서치 로직
                keywords = await self._do_research(seed_keyword)

                # 성공 메트릭 기록
                keywords_researched_total.labels(
                    status="success"
                ).inc(len(keywords))

                return keywords

            except Exception as e:
                # 에러 메트릭 기록
                errors_total.labels(
                    error_type=type(e).__name__,
                    service="keyword_research"
                ).inc()

                raise
```

### ContentGeneratorService 예시

```python
from app.monitoring import (
    content_generated_total,
    content_generation_duration_seconds
)

class ContentGeneratorService:
    async def generate_content(self, keyword: str):
        start_time = time.time()

        try:
            content = await self._generate(keyword)

            # 성능 및 성공 메트릭
            duration = time.time() - start_time
            content_generation_duration_seconds.observe(duration)
            content_generated_total.labels(status="success").inc()

            return content

        except Exception as e:
            content_generated_total.labels(status="error").inc()
            raise
```

## ⚙️ 환경 설정

### 필수 설정 (`.env`)

```bash
# 모니터링 활성화
ENABLE_METRICS=true

# Sentry (선택사항)
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1

# 애플리케이션 정보
APP_VERSION=1.0.0
APP_ENV=production
```

### Docker Compose 설정

```yaml
services:
  api:
    environment:
      - ENABLE_METRICS=true
      - SENTRY_DSN=${SENTRY_DSN}
    ports:
      - "8000:8000"

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
```

## 🧪 통합 테스트

### 1. 애플리케이션 시작

```bash
# 로컬 개발
uvicorn app.main:app --reload

# Docker
docker-compose up -d
```

### 2. 엔드포인트 테스트

```bash
# Health check
curl http://localhost:8000/health | jq

# Metrics
curl http://localhost:8000/metrics

# Root
curl http://localhost:8000/ | jq
```

### 3. 예상 응답

**Health Check:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T12:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": {
      "status": "healthy",
      "message": "Database is healthy",
      "latency_ms": 5.2
    },
    "redis": {
      "status": "healthy",
      "message": "Redis is healthy",
      "latency_ms": 2.1
    },
    "disk": {
      "status": "healthy",
      "message": "Disk space is healthy (45.2% used)",
      "percent_used": 45.2,
      "total_gb": 500,
      "free_gb": 274
    },
    "memory": {
      "status": "healthy",
      "message": "Memory usage is healthy (62.3% used)",
      "percent_used": 62.3,
      "total_gb": 16,
      "available_gb": 6.03
    }
  }
}
```

**Metrics (샘플):**
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/health",status="200"} 42.0
http_requests_total{method="POST",endpoint="/api/v1/keywords/research",status="200"} 15.0

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/health",le="0.1"} 40.0
http_request_duration_seconds_bucket{method="GET",endpoint="/health",le="0.5"} 42.0
http_request_duration_seconds_sum{method="GET",endpoint="/health"} 2.1
http_request_duration_seconds_count{method="GET",endpoint="/health"} 42.0

# HELP keywords_researched_total Total keywords researched
# TYPE keywords_researched_total counter
keywords_researched_total{status="success"} 120.0
```

## 🔍 모니터링 대시보드 설정

### Prometheus

1. Prometheus UI 접속: `http://localhost:9090`
2. Targets 확인: Status → Targets
3. 쿼리 예시:
   ```promql
   # 요청 비율
   rate(http_requests_total[5m])

   # 95번째 백분위 응답 시간
   histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

   # 에러 비율
   rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
   ```

### Grafana

1. Grafana UI 접속: `http://localhost:3000`
2. 로그인: admin / admin
3. Data Source 확인: Configuration → Data Sources → Prometheus
4. Dashboard 가져오기: Dashboards → Import → `monitoring/grafana/dashboards/api-overview.json`

### Sentry

1. Sentry 프로젝트 생성
2. DSN 복사 → `.env`에 추가
3. 애플리케이션 재시작
4. Sentry Dashboard에서 에러 확인

## 🚨 알림 설정

### Prometheus Alert Rules

`monitoring/prometheus/alerts.yml`에 정의된 알림:

- **HighErrorRate**: 5분간 에러율 > 5%
- **SlowResponseTime**: p95 응답 시간 > 2초
- **ServiceDown**: 서비스 다운 2분 이상
- **DatabaseConnectionIssues**: DB 에러율 > 0.1/s
- **HighMemoryUsage**: 메모리 사용률 > 90%
- **LowDiskSpace**: 디스크 여유 공간 < 10%

### Grafana 알림 채널

1. Configuration → Notification channels
2. Add channel (Slack, Email, Webhook 등)
3. Dashboard → Panel → Alert → Create alert

## 📈 성능 고려사항

### 1. Metrics 수집 오버헤드

- **PrometheusMiddleware**: 요청당 ~0.1-0.5ms 추가
- **메트릭 업데이트**: 메모리 연산으로 매우 빠름 (~0.01ms)
- **권장사항**: 프로덕션에서 항상 활성화

### 2. Health Check 레이턴시

- **데이터베이스 체크**: ~5-10ms
- **Redis 체크**: ~1-3ms
- **시스템 리소스 체크**: ~1-2ms
- **총 레이턴시**: ~10-20ms
- **권장사항**: 로드밸런서 헬스체크 간격 10초 이상

### 3. Sentry 오버헤드

- **에러 캡처**: 비동기로 처리되어 요청에 영향 없음
- **트랜잭션 샘플링**: 10% 권장 (프로덕션)
- **프로파일 샘플링**: 10% 권장
- **권장사항**: `before_send`로 불필요한 에러 필터링

## 🐛 문제 해결

### 메트릭이 수집되지 않음

1. `ENABLE_METRICS=true` 확인
2. `/metrics` 엔드포인트 접속 가능 확인
3. Prometheus targets 상태 확인 (`http://localhost:9090/targets`)
4. PrometheusMiddleware 등록 확인

### Health Check가 unhealthy

1. 데이터베이스 연결 확인
2. Redis 연결 확인
3. 디스크 여유 공간 확인
4. 메모리 사용률 확인
5. 로그에서 상세 에러 확인

### Sentry에 에러가 전송되지 않음

1. `SENTRY_DSN` 설정 확인
2. `ENABLE_METRICS=true` 확인
3. `before_send` 필터링 로직 확인
4. 네트워크 연결 확인
5. Sentry project settings 확인

## 📚 추가 리소스

- [MONITORING.md](./MONITORING.md) - 모니터링 시스템 전체 가이드
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Sentry Documentation](https://docs.sentry.io/)
- [FastAPI Middleware](https://fastapi.tiangolo.com/advanced/middleware/)

---

**문의**: 모니터링 통합 관련 질문이 있으시면 이슈를 등록해주세요.
