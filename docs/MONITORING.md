# 모니터링 시스템 가이드

블로그 자동화 시스템의 모니터링 및 관찰 가능성(Observability) 가이드입니다.

## 📊 개요

시스템은 다음 세 가지 핵심 관찰 가능성 기둥을 제공합니다:

- **메트릭 (Metrics)**: Prometheus + Grafana
- **로그 (Logs)**: Structlog (JSON 형식)
- **추적 (Traces)**: Sentry

## 🏗️ 아키텍처

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   FastAPI    │────▶│  Prometheus  │────▶│   Grafana    │
│     App      │     │   (Metrics)  │     │  (Dashboa rds)│
└──────────────┘     └──────────────┘     └──────────────┘
       │
       │             ┌──────────────┐
       └────────────▶│    Sentry    │
                     │   (Errors)   │
                     └──────────────┘
```

## 📈 Prometheus 메트릭

### 수집되는 메트릭

#### HTTP 메트릭
- `http_requests_total`: 총 HTTP 요청 수 (메서드, 엔드포인트, 상태별)
- `http_request_duration_seconds`: HTTP 요청 처리 시간
- `http_requests_in_progress`: 현재 처리 중인 요청 수

#### 비즈니스 메트릭
- `keywords_researched_total`: 리서치된 키워드 수
- `content_generated_total`: 생성된 콘텐츠 수
- `images_generated_total`: 생성된 이미지 수
- `posts_published_total`: 발행된 포스트 수

#### 성능 메트릭
- `content_generation_duration_seconds`: 콘텐츠 생성 시간
- `keyword_research_duration_seconds`: 키워드 리서치 시간
- `image_generation_duration_seconds`: 이미지 생성 시간

#### 에러 메트릭
- `errors_total`: 총 에러 수 (타입, 서비스별)
- `api_errors_total`: API 에러 수 (API명, 상태 코드별)

### Prometheus 접속

```bash
# 로컬
http://localhost:9090

# Docker
http://localhost:9090
```

### 메트릭 쿼리 예제

```promql
# 요청 비율 (5분 평균)
rate(http_requests_total[5m])

# 95번째 백분위 응답 시간
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# 에러 비율
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# 생성된 콘텐츠 수 (시간당)
increase(content_generated_total[1h])
```

## 📊 Grafana 대시보드

### 접속 정보

```bash
URL: http://localhost:3000
Username: admin
Password: admin (초기 비밀번호)
```

### 사전 구성된 대시보드

1. **API Overview**: HTTP 메트릭, 요청 비율, 에러 비율
2. **Business Metrics**: 키워드, 콘텐츠, 이미지, 발행 통계
3. **Performance**: 응답 시간, 처리 시간, 대기열 상태

### 커스텀 대시보드 생성

```bash
# Grafana UI에서
1. + 버튼 → Dashboard
2. Add Panel
3. Prometheus 데이터소스 선택
4. 쿼리 작성
5. 시각화 타입 선택
6. 저장
```

## 🔴 Sentry 에러 추적

### 설정

`.env` 파일에 Sentry DSN 추가:

```bash
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% 트랜잭션 샘플링
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 10% 프로파일 샘플링
APP_VERSION=1.0.0
APP_ENV=production
```

### 기능

- ✅ 자동 에러 캡처
- ✅ 스택 트레이스 포함
- ✅ 요청 컨텍스트 포함
- ✅ 사용자 식별
- ✅ 성능 모니터링 (트랜잭션)
- ✅ 프로파일링

### 수동 에러 캡처

```python
from app.monitoring.sentry import capture_exception, capture_message

try:
    # 작업 수행
    pass
except Exception as e:
    capture_exception(e, context={"user_id": user.id})
```

## 🏥 헬스체크

### 엔드포인트

```bash
GET /health
```

### 응답 형식

```json
{
  "status": "healthy",  # healthy | degraded | unhealthy
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

### 상태 코드

- `200`: healthy
- `503`: degraded 또는 unhealthy

## 🚀 Docker로 모니터링 시작

```bash
# 전체 스택 시작 (모니터링 포함)
docker-compose up -d

# 모니터링만 시작
docker-compose up -d prometheus grafana

# 로그 확인
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

### 포트 매핑

| 서비스 | 포트 | 설명 |
|--------|------|------|
| Prometheus | 9090 | 메트릭 수집 및 쿼리 |
| Grafana | 3000 | 대시보드 |
| Redis Exporter | 9121 | Redis 메트릭 |
| Postgres Exporter | 9187 | PostgreSQL 메트릭 |
| API Metrics | 8000/metrics | FastAPI 메트릭 엔드포인트 |

## 📊 알림 규칙

### 구성된 알림

**monitoring/prometheus/alerts.yml**에 정의:

1. **HighErrorRate**: 5분간 에러율 > 5%
2. **SlowResponseTime**: p95 응답 시간 > 2초
3. **ServiceDown**: 서비스 다운 2분 이상
4. **DatabaseConnectionIssues**: DB 에러율 > 0.1/s
5. **HighMemoryUsage**: 메모리 사용률 > 90%
6. **LowDiskSpace**: 디스크 여유 공간 < 10%

### 알림 채널 설정 (Grafana)

```bash
# Grafana UI에서
1. Configuration → Notification channels
2. Add channel
3. 타입 선택 (Slack, Email, Webhook 등)
4. 설정 입력
5. Test → Save
```

## 🔍 문제 해결

### Prometheus가 메트릭을 수집하지 못함

```bash
# 타겟 상태 확인
http://localhost:9090/targets

# API 메트릭 엔드포인트 확인
curl http://localhost:8000/metrics

# Prometheus 로그 확인
docker logs blog-automation-prometheus
```

### Grafana가 데이터소스에 연결하지 못함

```bash
# 데이터소스 테스트
Grafana UI → Configuration → Data Sources → Prometheus → Test

# 네트워크 확인
docker exec blog-automation-grafana ping prometheus

# Grafana 로그 확인
docker logs blog-automation-grafana
```

### Sentry 에러가 전송되지 않음

```bash
# DSN 확인
echo $SENTRY_DSN

# 수동 테스트
python -c "from app.monitoring.sentry import capture_message; capture_message('Test')"

# 로그 확인
grep "sentry" logs/*.log
```

## 📚 모범 사례

### 1. 적절한 메트릭 선택

- **Counter**: 증가만 하는 값 (요청 수, 에러 수)
- **Gauge**: 증감하는 값 (메모리, 큐 크기)
- **Histogram**: 분포 측정 (응답 시간, 크기)

### 2. 라벨 사용

```python
from app.monitoring.metrics import content_generated_total

# ✅ 좋음
content_generated_total.labels(status="success").inc()

# ❌ 나쁨 (라벨이 너무 많음 - 카디널리티 폭발)
content_generated_total.labels(
    user_id=user_id,  # 고유 값이 너무 많음
    timestamp=datetime.now()  # 타임스탬프는 라벨로 부적절
).inc()
```

### 3. 알림 피로 방지

- 중요한 알림만 설정
- 적절한 임계값 설정
- For 기간 설정 (일시적 스파이크 무시)

### 4. 대시보드 구성

- 핵심 메트릭 우선 표시
- 관련 메트릭 그룹화
- 적절한 시간 범위 설정

## 📖 추가 리소스

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Sentry Documentation](https://docs.sentry.io/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)

---

**문의**: 모니터링 관련 질문이나 제안이 있으시면 이슈를 등록해주세요.
