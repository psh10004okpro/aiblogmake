# Dashboard UI

대시보드 UI - 시각적 관리 완전 가이드

## 개요

Dashboard UI는 AI 블로그 자동화 시스템을 시각적으로 관리할 수 있는 웹 기반 인터페이스입니다. Vue.js 3로 구축된 SPA(Single Page Application)로, 실시간 워크플로우 모니터링, SEO 점수 관리, 시스템 설정 등을 제공합니다.

### 주요 기능

1. **대시보드**: 전체 시스템 현황 한눈에 보기
2. **워크플로우 관리**: 워크플로우 시작, 모니터링, 관리
3. **SEO 점수**: 포스트 SEO 분석 및 최적화 제안
4. **설정**: 알림 시스템 및 시스템 설정 관리

## 기술 스택

### Frontend
- **Vue.js 3**: Progressive JavaScript framework (Composition API)
- **Tailwind CSS**: Utility-first CSS framework
- **Chart.js**: 데이터 시각화 라이브러리
- **Axios**: HTTP 클라이언트
- **Font Awesome**: 아이콘 라이브러리

### Backend Integration
- **FastAPI**: RESTful API 서버
- **WebSocket**: 실시간 업데이트 (향후 구현)

## 설치 및 실행

### 1. 기본 설정

Dashboard는 FastAPI 애플리케이션과 함께 자동으로 서빙됩니다. 별도의 설치가 필요없습니다.

```bash
# FastAPI 서버 시작
python -m app.main

# 또는
make run
```

### 2. 브라우저에서 접속

```
http://localhost:8000/
```

서버가 시작되면 자동으로 대시보드 UI가 로드됩니다.

### 3. API 문서 확인

```
http://localhost:8000/docs    # Swagger UI
http://localhost:8000/redoc   # ReDoc
```

## 페이지 구성

### 1. 대시보드 (Dashboard)

홈페이지로, 시스템의 전체 현황을 한눈에 볼 수 있습니다.

#### 주요 위젯

**통계 카드**
- 총 워크플로우 수
- 생성된 포스트 수
- 평균 SEO 점수
- 성공률

**SEO 점수 분포 차트**
- Doughnut 차트로 등급별 분포 시각화
- A+부터 F까지 8단계 등급

**최근 워크플로우**
- 최근 5개 워크플로우 목록
- 실시간 진행률 표시
- 상태별 색상 코드

**성과 지표**
- 최고 성과 포스트 Top 5
- 개선 필요 포스트 5개

#### 빠른 액션
- 새 워크플로우 시작
- SEO 분석 실행
- 설정 페이지로 이동

### 2. 워크플로우 (Workflows)

워크플로우 생성, 모니터링 및 관리 페이지입니다.

#### 기능

**필터링**
```
- 상태별: 전체, 대기 중, 실행 중, 완료, 실패, 취소됨
- 타입별: 전체, 수동, 예약, 자동
- 페이지 크기: 10, 20, 50개
```

**워크플로우 카드**
- 워크플로우 ID 및 상태
- 시드 키워드 목록
- 진행률 바 (실시간 업데이트)
- 생성된 포스트 수 / 발행된 포스트 수
- 소요 시간

**워크플로우 타임라인**
- 각 단계별 상태 시각화
  - ✓ 키워드 리서치
  - ✓ 콘텐츠 생성
  - ✓ SEO 최적화
  - ✓ WordPress 발행
- 현재 진행 중인 단계 표시

**액션**
- 상세보기: 워크플로우 상세 정보
- 취소: 실행 중인 워크플로우 중단
- 삭제: 워크플로우 삭제

#### 실시간 폴링

실행 중인 워크플로우는 3초마다 자동으로 상태가 업데이트됩니다.

```javascript
// 자동 폴링 시스템
setInterval(() => {
    if (hasRunningWorkflows) {
        fetchWorkflowStatus();
    }
}, 3000);
```

### 3. SEO 점수 (SEO Scores)

포스트의 SEO 점수를 조회하고 분석 결과를 확인하는 페이지입니다.

#### 통계 대시보드

**주요 지표**
- 분석된 포스트 총 수
- 전체 평균 점수
- 최고 등급 포스트

**등급별 분포 차트**
- Bar 차트로 등급별 포스트 수 시각화
- 8단계 등급 (A+, A, B+, B, C+, C, D, F)

#### 필터링

```
- 최소/최대 점수: 0-100 범위
- 등급: A+, A, B+, B, C+, C, D, F
- 키워드 검색: 타겟 키워드 또는 포스트 ID
```

#### SEO 점수 카드

각 포스트의 SEO 분석 결과를 카드 형태로 표시합니다.

**기본 정보**
- 등급 배지 (A+ ~ F)
- 전체 점수 (0-100)
- 포스트 ID
- 타겟 키워드
- 분석 일시

**세부 점수** (6개 항목)
1. **키워드 밀도** (20% 가중치)
   - 타겟 키워드의 적절한 사용 빈도
   - 최적 범위: 1-2%

2. **제목 최적화** (20% 가중치)
   - 제목에 키워드 포함 여부
   - 한글 기준 15-30자

3. **메타 태그** (15% 가중치)
   - Meta description 품질
   - 한글 기준 60-80자

4. **가독성** (20% 가중치)
   - 문장 길이 및 단락 구조
   - 헤딩 태그 사용

5. **내부 링크** (10% 가중치)
   - 내부 링크 수 및 품질
   - 권장: 3-5개

6. **이미지 Alt** (15% 가중치)
   - 이미지 alt 텍스트 최적화
   - 키워드 포함 여부

**발견된 이슈**
- 이슈 카테고리 및 심각도
- 최대 3개까지 미리보기
- 나머지는 상세보기에서 확인

**액션**
- 상세보기: 전체 분석 결과 및 개선 제안
- 삭제: SEO 점수 삭제

#### SEO 분석 상세 모달

**점수 개요**
- 큰 등급 배지 및 점수
- 포스트 정보

**세부 점수 진행률**
- 6개 항목별 점수 및 진행률 바
- 색상 코드:
  - 녹색: 90점 이상 (우수)
  - 라임: 80-89점 (양호)
  - 노란색: 70-79점 (보통)
  - 주황색: 60-69점 (주의)
  - 빨간색: 60점 미만 (개선 필요)

**발견된 이슈**
- 전체 이슈 목록
- 심각도별 배지 (critical, high, medium, low, info)
- 이슈 카테고리 및 메시지

**개선 제안**
- 구체적인 최적화 제안
- 실행 가능한 액션 아이템

**메트릭**
- 상세 분석 메트릭
- 키워드 밀도, 문장 수, 단락 수 등

#### 포스트 분석

**새 포스트 분석**
1. "포스트 분석" 버튼 클릭
2. 분석할 포스트 ID 입력
3. 자동으로 SEO 분석 실행
4. 결과가 목록에 추가됨

### 4. 설정 (Settings)

시스템 설정 및 알림 관리 페이지입니다.

#### 알림 시스템 상태

**전체 상태**
- 알림 시스템 활성/비활성 표시
- 활성 제공자 수

**활성 제공자**
- 이메일 (EmailNotificationProvider)
- Slack (SlackNotificationProvider)

**설정 상태**
- 이메일 설정 여부
- Slack 설정 여부
- 설정 가이드 및 예시

#### 알림 설정 가이드

**이메일 미설정 시**
```env
# .env 파일 예시
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFY_EMAILS=admin@yourblog.com

ENABLE_EMAIL_NOTIFICATIONS=True
```

**Slack 미설정 시**
```env
# .env 파일 예시
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_CHANNEL=#blog-automation

ENABLE_SLACK_NOTIFICATIONS=True
```

#### 알림 테스트

**커스텀 테스트 알림**
- 제목, 메시지 입력
- 알림 타입 선택 (info, success, warning, error)
- 우선순위 선택 (low, normal, high, urgent)
- "커스텀 알림 전송" 버튼 클릭

**사전 정의 테스트**
- "워크플로우 완료 알림" 버튼
- "워크플로우 실패 알림" 버튼

**테스트 결과**
- 전송 성공/실패 여부
- 제공자별 상세 결과
- 오류 메시지 (실패 시)

#### 시스템 정보

- API 버전
- 환경 (Development/Production)
- 데이터베이스 (PostgreSQL)
- 작업 큐 (Celery + Redis)

#### 문서 링크

- API 문서 (Swagger UI)
- 알림 시스템 가이드
- SEO 점수 계산 가이드
- 원클릭 자동화 가이드

## 워크플로우 시작하기

### 1. "워크플로우 시작" 버튼 클릭

상단 네비게이션 바의 "워크플로우 시작" 버튼을 클릭합니다.

### 2. 워크플로우 설정

**시드 키워드** (필수)
```
예: 블로그 SEO, 콘텐츠 마케팅, 키워드 리서치
```
쉼표(,)로 구분하여 여러 키워드를 입력할 수 있습니다.

**생성할 포스트 수** (필수)
```
범위: 1-10개
기본값: 2개
```

**자동 발행**
```
☑ 자동으로 WordPress에 발행
```
체크하면 생성된 포스트를 자동으로 WordPress에 발행합니다.

**예약 시간** (선택사항)
```
날짜 및 시간 선택
```
지정한 시간에 워크플로우를 시작합니다. 비워두면 즉시 시작됩니다.

### 3. "시작" 버튼 클릭

워크플로우가 시작되고 자동으로 워크플로우 페이지로 이동합니다.

### 4. 진행 상황 모니터링

워크플로우 카드에서 실시간으로 진행 상황을 확인할 수 있습니다:
- 진행률 바
- 타임라인 단계별 상태
- 생성된 포스트 수
- 소요 시간

## UI 컴포넌트

### 상태 배지

**워크플로우 상태**
```
- 대기 중: 회색
- 실행 중: 파란색
- 완료: 녹색
- 실패: 빨간색
- 취소됨: 주황색
```

**SEO 등급**
```
- A+: 진한 녹색 (95-100)
- A:  녹색 (90-94)
- B+: 라임 (85-89)
- B:  노란색 (80-84)
- C+: 주황색 (70-79)
- C:  진한 주황색 (60-69)
- D:  빨간색 (50-59)
- F:  진한 빨간색 (0-49)
```

**알림 타입**
```
- info: 파란색
- success: 녹색
- warning: 노란색
- error: 빨간색
```

### 진행률 바

```css
.progress-bar {
    width: 100%;
    height: 8px;
    background: linear-gradient(to right, #3b82f6, #8b5cf6);
}
```

그라데이션 효과가 적용된 진행률 바로 시각적 피드백을 제공합니다.

### 토스트 알림

화면 우측 하단에 표시되는 알림입니다:
- 자동으로 5초 후 사라짐
- 수동으로 닫기 가능
- 최대 3개까지 동시 표시

## API 클라이언트

`frontend/js/utils/api.js`에서 모든 API 호출을 관리합니다.

### 워크플로우 API

```javascript
// 워크플로우 목록
await api.workflows.list({
    status: 'running',
    limit: 20
});

// 워크플로우 상태 조회
await api.workflows.getStatus(workflowId);

// 워크플로우 시작
await api.workflows.start({
    seed_keywords: ['키워드1', '키워드2'],
    num_posts: 2,
    auto_publish: true
});

// 워크플로우 취소
await api.workflows.cancel(workflowId);

// 워크플로우 삭제
await api.workflows.delete(workflowId);
```

### SEO API

```javascript
// SEO 점수 목록
await api.seo.list({
    min_score: 80,
    grade: 'A'
});

// SEO 점수 조회
await api.seo.getScore(postId);

// SEO 통계
await api.seo.getStats();

// 포스트 분석
await api.seo.analyzePost(postId, true);

// SEO 점수 삭제
await api.seo.deleteScore(postId);
```

### 알림 API

```javascript
// 알림 상태 확인
await api.notifications.getStatus();

// 테스트 알림 전송
await api.notifications.sendTest({
    title: 'Test',
    message: 'Test message',
    notification_type: 'info',
    priority: 'normal'
});

// 워크플로우 완료 알림 테스트
await api.notifications.sendTestWorkflowComplete();

// 워크플로우 실패 알림 테스트
await api.notifications.sendTestWorkflowFailed();
```

## 유틸리티 함수

### 날짜 포맷팅

```javascript
api.formatDate('2025-01-31T10:30:00Z');
// "방금 전"
// "5분 전"
// "2시간 전"
// "1일 전"
// "2025-01-31 10:30"
```

### 시간 포맷팅

```javascript
api.formatDuration(450);
// "7분 30초"

api.formatDuration(3665);
// "1시간 1분 5초"
```

### 상태 색상

```javascript
api.getStatusColor('running');
// "blue"

api.getStatusColor('completed');
// "green"
```

### 등급 색상

```javascript
api.getGradeColor('A+');
// "text-emerald-600"

api.getGradeColor('F');
// "text-red-800"
```

### 워크플로우 폴링

```javascript
// 워크플로우 상태를 주기적으로 확인
api.pollWorkflowStatus(
    workflowId,
    (status) => {
        console.log('Status:', status);
        if (status.status === 'completed') {
            // 완료 처리
        }
    },
    3000  // 3초마다
);
```

## 커스터마이징

### 색상 테마 변경

`frontend/css/style.css`에서 CSS 변수를 수정하여 테마를 변경할 수 있습니다:

```css
:root {
    --primary-color: #3b82f6;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --error-color: #ef4444;
}
```

### 폴링 간격 변경

`frontend/js/components/Workflows.js`에서 폴링 간격을 조정할 수 있습니다:

```javascript
// 기본값: 3000ms (3초)
this.pollingInterval = setInterval(() => {
    // ...
}, 5000);  // 5초로 변경
```

### 페이지 크기 옵션

`frontend/js/components/Workflows.js`에서 페이지 크기 옵션을 추가할 수 있습니다:

```javascript
pageSizeOptions: [10, 20, 50, 100]  // 100 추가
```

## 트러블슈팅

### 대시보드가 로드되지 않음

1. **FastAPI 서버 확인**
   ```bash
   curl http://localhost:8000/health
   ```

2. **정적 파일 마운트 확인**
   ```bash
   # 로그에서 확인
   grep "frontend_static_files_mounted" logs/app.log
   ```

3. **브라우저 콘솔 확인**
   - F12 → Console 탭
   - 404 에러 확인

### API 호출 실패

1. **CORS 설정 확인**
   ```python
   # app/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **API 엔드포인트 확인**
   ```bash
   curl http://localhost:8000/api/v1/workflows/list
   ```

### 실시간 업데이트가 작동하지 않음

1. **폴링 간격 확인**
   - 브라우저 개발자 도구 → Network 탭
   - 3초마다 API 호출이 있는지 확인

2. **워크플로우 상태 확인**
   - `running` 또는 `pending` 상태일 때만 폴링 활성

### 차트가 표시되지 않음

1. **Chart.js 로드 확인**
   ```html
   <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
   ```

2. **Canvas 요소 확인**
   ```javascript
   const canvas = this.$refs.gradeChart;
   console.log(canvas);  // null이 아니어야 함
   ```

## 성능 최적화

### 1. 폴링 최적화

실행 중인 워크플로우가 없을 때는 폴링을 중단합니다:

```javascript
startPolling() {
    this.pollingInterval = setInterval(() => {
        const runningWorkflows = this.workflows.filter(
            w => w.status === 'running' || w.status === 'pending'
        );

        // 실행 중인 워크플로우가 없으면 스킵
        if (runningWorkflows.length === 0) {
            return;
        }

        this.$emit('poll-workflows');
    }, 3000);
}
```

### 2. 데이터 캐싱

API 응답을 로컬에 캐싱하여 불필요한 요청을 줄입니다:

```javascript
const cache = new Map();

async function fetchWithCache(url, ttl = 60000) {
    const cached = cache.get(url);
    if (cached && Date.now() - cached.timestamp < ttl) {
        return cached.data;
    }

    const data = await fetch(url);
    cache.set(url, { data, timestamp: Date.now() });
    return data;
}
```

### 3. 이미지 최적화

아이콘은 Font Awesome을 사용하여 HTTP 요청을 줄입니다:

```html
<i class="fas fa-check-circle"></i>
```

### 4. 코드 스플리팅

Vue 컴포넌트를 동적으로 로드하여 초기 로딩 시간을 단축할 수 있습니다:

```javascript
const Dashboard = () => import('./components/Dashboard.js');
const Workflows = () => import('./components/Workflows.js');
```

## 보안 고려사항

### 1. CSRF 보호

FastAPI는 기본적으로 CSRF 토큰을 요구하지 않지만, 프로덕션 환경에서는 설정을 권장합니다.

### 2. 인증 및 권한

현재는 인증이 구현되어 있지 않습니다. 프로덕션 환경에서는 JWT 또는 OAuth2 인증을 추가해야 합니다.

### 3. XSS 방지

Vue.js는 기본적으로 XSS를 방지하지만, `v-html`을 사용할 때는 주의가 필요합니다.

### 4. API Rate Limiting

프로덕션 환경에서는 API rate limiting을 설정해야 합니다:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/v1/workflows/list")
@limiter.limit("100/minute")
async def list_workflows():
    ...
```

## 향후 개선 계획

### 1. WebSocket 지원

실시간 업데이트를 위한 WebSocket 연결:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'workflow_update') {
        updateWorkflow(data.workflow);
    }
};
```

### 2. 다크 모드

사용자 선호에 따라 다크 모드 지원:
```javascript
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
document.body.classList.toggle('dark', prefersDark.matches);
```

### 3. 모바일 반응형

모바일 환경에 최적화된 UI:
```css
@media (max-width: 768px) {
    .navbar-menu {
        flex-direction: column;
    }
}
```

### 4. 오프라인 지원

Service Worker를 사용한 오프라인 기능:
```javascript
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
}
```

### 5. 고급 필터링

복합 필터 및 저장된 필터 프리셋:
```javascript
const filters = {
    status: ['running', 'pending'],
    date_range: [startDate, endDate],
    keywords: ['SEO', '마케팅']
};
```

## 관련 문서

- [SEO 점수 계산](./SEO_SCORING.md) - SEO 분석 엔진 가이드
- [알림 시스템](./NOTIFICATIONS.md) - 이메일/Slack 알림 설정
- [원클릭 자동화](./ONE_CLICK_AUTOMATION.md) - 완전 자동 파이프라인
- [Celery Beat](./CELERY_BEAT.md) - 자동 스케줄러 설정
- [API 문서](http://localhost:8000/docs) - FastAPI Swagger UI

## 지원

문제가 발생하거나 제안 사항이 있으면 GitHub Issues를 통해 알려주세요.

---

**Dashboard UI v1.0.0**
AI 블로그 자동화 시스템
