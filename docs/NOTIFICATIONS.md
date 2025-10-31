# Notification System

알림 시스템 - 이메일/Slack 알림 완전 가이드

## 개요

Notification System은 블로그 자동화 워크플로우의 주요 이벤트를 이메일과 Slack을 통해 실시간으로 알림하는 시스템입니다.

### 주요 기능

1. **멀티 채널 지원**: 이메일, Slack 동시 알림
2. **이벤트 기반 알림**: 워크플로우 시작/완료/실패, 포스트 발행 등
3. **우선순위 관리**: Low, Normal, High, Urgent 4단계
4. **알림 타입 분류**: Info, Success, Warning, Error
5. **유연한 설정**: 알림 채널 및 이벤트별 켜기/끄기 가능

## 지원하는 알림 이벤트

### 1. 워크플로우 시작
워크플로우가 시작될 때 알림 (기본값: OFF)

**포함 정보:**
- Workflow ID
- Seed keywords
- Number of posts to create
- Status

### 2. 워크플로우 완료
워크플로우가 성공적으로 완료될 때 알림 (기본값: ON)

**포함 정보:**
- Workflow ID
- Posts created
- Posts published
- Duration
- Errors (if any)

### 3. 워크플로우 실패
워크플로우가 실패할 때 알림 (기본값: ON)

**포함 정보:**
- Workflow ID
- Error message
- Failed step
- Status

### 4. 포스트 발행
개별 포스트가 발행될 때 알림 (기본값: OFF)

**포함 정보:**
- Keyword
- Post title
- WordPress URL
- Word count

## 설정 방법

### 1. 이메일 알림 설정

#### Gmail 사용 예시

1. **Gmail App Password 생성**
   - Google Account → Security → 2-Step Verification 활성화
   - App passwords → Generate new password
   - 생성된 비밀번호 복사

2. **.env 파일 설정**

```env
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-digit-app-password
SMTP_FROM=your-email@gmail.com
NOTIFY_EMAILS=admin@yourblog.com,team@yourblog.com

# Enable email notifications
ENABLE_EMAIL_NOTIFICATIONS=True
```

#### 다른 SMTP 서버 사용

```env
# Outlook/Hotmail
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password

# Naver
SMTP_HOST=smtp.naver.com
SMTP_PORT=587
SMTP_USER=your-id
SMTP_PASSWORD=your-password

# AWS SES
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
```

### 2. Slack 알림 설정

#### Slack Incoming Webhook 생성

1. **Slack Workspace 설정**
   - https://api.slack.com/apps 접속
   - "Create New App" → "From scratch"
   - App 이름 입력 및 Workspace 선택

2. **Incoming Webhook 활성화**
   - "Incoming Webhooks" 메뉴 선택
   - "Activate Incoming Webhooks" ON
   - "Add New Webhook to Workspace"
   - 알림을 받을 채널 선택
   - Webhook URL 복사

3. **.env 파일 설정**

```env
# Slack Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
SLACK_CHANNEL=#blog-automation

# Enable Slack notifications
ENABLE_SLACK_NOTIFICATIONS=True
```

### 3. 알림 이벤트 설정

```env
# Notification Event Settings
NOTIFY_ON_WORKFLOW_START=False
NOTIFY_ON_WORKFLOW_COMPLETE=True
NOTIFY_ON_WORKFLOW_FAIL=True
NOTIFY_ON_POST_PUBLISH=False
```

## API 엔드포인트

### 1. 알림 상태 확인

**GET** `/api/v1/notifications/status`

현재 알림 서비스 상태 및 설정된 제공자 확인

```bash
curl http://localhost:8000/api/v1/notifications/status
```

**응답:**
```json
{
  "available": true,
  "active_providers": ["EmailNotificationProvider", "SlackNotificationProvider"],
  "email_configured": true,
  "slack_configured": true
}
```

### 2. 테스트 알림 전송

**POST** `/api/v1/notifications/test`

알림 설정을 테스트하기 위한 테스트 메시지 전송

```bash
curl -X POST http://localhost:8000/api/v1/notifications/test \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Notification",
    "message": "This is a test message to verify notification configuration.",
    "notification_type": "info",
    "priority": "normal",
    "metadata": {
      "test": true
    }
  }'
```

**응답:**
```json
{
  "success": true,
  "results": [
    {
      "provider": "email",
      "success": true,
      "error": null,
      "metadata": {
        "recipients": ["admin@yourblog.com"],
        "subject": "[Blog Automation System] Test Notification"
      }
    },
    {
      "provider": "slack",
      "success": true,
      "error": null,
      "metadata": {
        "channel": "#blog-automation",
        "username": "Blog Automation System"
      }
    }
  ],
  "providers_attempted": 2,
  "providers_succeeded": 2,
  "message": "Successfully sent to 2/2 provider(s)"
}
```

### 3. 워크플로우 완료 알림 테스트

**POST** `/api/v1/notifications/test/workflow-complete`

```bash
curl -X POST http://localhost:8000/api/v1/notifications/test/workflow-complete
```

### 4. 워크플로우 실패 알림 테스트

**POST** `/api/v1/notifications/test/workflow-failed`

```bash
curl -X POST http://localhost:8000/api/v1/notifications/test/workflow-failed
```

## 알림 예시

### 이메일 알림

![Email Notification Example](https://via.placeholder.com/600x400?text=Email+Notification)

**제목:** [Blog Automation System] Workflow Completed

**내용:**
```
Workflow #1 completed successfully!

Created 2 post(s) and published 2 post(s) in 450.5 seconds.

Details:
• Workflow ID: 1
• Posts Created: 2
• Posts Published: 2
• Duration: 450.5s
• Errors: 0
• Status: completed
```

### Slack 알림

**Workflow Started:**
```
ℹ️ Workflow Started

Workflow #1 has been started.

Details:
• Workflow ID: 1
• Seed Keywords: 블로그 SEO, 콘텐츠 마케팅
• Num Posts: 2
• Status: running
```

**Workflow Completed:**
```
✅ Workflow Completed

Workflow #1 completed successfully! Created 2 post(s) and published 2 post(s) in 450.5 seconds.

Details:
• Workflow ID: 1
• Posts Created: 2
• Posts Published: 2
• Duration: 450.5s
• Errors: 0
• Status: completed
```

**Workflow Failed:**
```
❌ Workflow Failed

Workflow #1 has failed. Failed at step: generate_content

Details:
• Workflow ID: 1
• Error: Content generation failed: API rate limit exceeded
• Current Step: generate_content
• Status: failed
```

## 프로그래밍 방식으로 알림 전송

### Python 예시

```python
from app.services.notifications import get_notification_service, NotificationType, NotificationPriority

# Get notification service
notification_service = get_notification_service()

# Send custom notification
results = await notification_service.send(
    title="Custom Alert",
    message="This is a custom notification message.",
    notification_type=NotificationType.WARNING,
    priority=NotificationPriority.HIGH,
    metadata={
        "custom_field": "value",
        "timestamp": datetime.now().isoformat()
    }
)

# Check results
for result in results:
    if result.success:
        print(f"✅ Sent via {result.provider}")
    else:
        print(f"❌ Failed to send via {result.provider}: {result.error}")
```

### 특정 이벤트 알림

```python
# Workflow started
await notification_service.send_workflow_started(
    workflow_id=1,
    seed_keywords=["keyword1", "keyword2"],
    num_posts=2
)

# Workflow completed
await notification_service.send_workflow_completed(
    workflow_id=1,
    posts_created=2,
    posts_published=2,
    duration_seconds=450.5,
    errors=0
)

# Workflow failed
await notification_service.send_workflow_failed(
    workflow_id=1,
    error="API rate limit exceeded",
    current_step="generate_content"
)

# Post published
await notification_service.send_post_published(
    keyword="블로그 SEO",
    title="완벽한 블로그 SEO 가이드",
    wp_url="https://yourblog.com/blog-seo-guide",
    word_count=2500
)
```

## 커스텀 Notification Provider 생성

자신만의 알림 채널을 추가하고 싶다면 `BaseNotificationProvider`를 상속하여 구현할 수 있습니다.

### 예시: Discord Provider

```python
from app.services.notifications.base import (
    BaseNotificationProvider,
    NotificationMessage,
    NotificationResult
)
import aiohttp

class DiscordNotificationProvider(BaseNotificationProvider):
    """Discord notification provider using webhooks."""

    def __init__(self, webhook_url: str, enabled: bool = True):
        super().__init__(enabled)
        self.webhook_url = webhook_url

    def validate_config(self) -> bool:
        return bool(self.webhook_url)

    async def send(self, notification: NotificationMessage) -> NotificationResult:
        if not self.is_available():
            return NotificationResult(
                success=False,
                provider="discord",
                error="Discord provider not configured"
            )

        # Build Discord payload
        payload = {
            "content": f"**{notification.title}**\n{notification.message}"
        }

        # Send to Discord
        async with aiohttp.ClientSession() as session:
            async with session.post(self.webhook_url, json=payload) as response:
                if response.status == 204:
                    return NotificationResult(
                        success=True,
                        provider="discord"
                    )
                else:
                    return NotificationResult(
                        success=False,
                        provider="discord",
                        error=f"Discord returned status {response.status}"
                    )
```

## 트러블슈팅

### 이메일이 전송되지 않음

1. **SMTP 인증 실패**
   - Gmail: App Password 사용하는지 확인
   - 2단계 인증이 활성화되어 있는지 확인

2. **포트 차단**
   - 방화벽에서 587 포트가 열려있는지 확인
   - 대안: 포트 465 (SSL) 시도

3. **메일이 스팸함으로 이동**
   - 스팸함 확인
   - SPF, DKIM 레코드 설정

### Slack 알림이 전송되지 않음

1. **Webhook URL 확인**
   - URL이 `https://hooks.slack.com/`으로 시작하는지 확인
   - URL에 특수문자가 올바르게 escape되었는지 확인

2. **채널 권한**
   - Bot이 해당 채널에 메시지를 보낼 권한이 있는지 확인
   - Private 채널인 경우 Bot을 초대했는지 확인

3. **Rate Limiting**
   - Slack는 1초당 1개의 메시지 제한
   - 너무 많은 알림 전송 시 rate limit 발생

### 테스트 알림은 되는데 실제 워크플로우 알림이 안 됨

1. **Feature Flag 확인**
   ```env
   ENABLE_EMAIL_NOTIFICATIONS=True
   ENABLE_SLACK_NOTIFICATIONS=True
   NOTIFY_ON_WORKFLOW_COMPLETE=True  # 해당 이벤트 활성화
   ```

2. **서비스 재시작**
   ```bash
   # 환경 변수 변경 후 서비스 재시작 필요
   make celery-stop
   make celery-all
   ```

3. **로그 확인**
   ```bash
   tail -f logs/celery-worker.log | grep notification
   ```

## 베스트 프랙티스

### 1. 알림 피로 방지

**너무 많은 알림은 무시하게 됩니다. 중요한 이벤트만 켜세요:**

```env
# ✅ 권장 설정 (중요한 것만)
NOTIFY_ON_WORKFLOW_START=False      # OFF
NOTIFY_ON_WORKFLOW_COMPLETE=True    # ON
NOTIFY_ON_WORKFLOW_FAIL=True        # ON
NOTIFY_ON_POST_PUBLISH=False        # OFF (너무 많을 수 있음)
```

### 2. 채널 분리

**다른 우선순위는 다른 채널로:**

```env
# 일반 알림
SLACK_CHANNEL=#blog-automation

# 긴급 알림 (에러)
SLACK_ERROR_CHANNEL=#blog-automation-errors
```

### 3. 메타데이터 활용

**유용한 정보를 메타데이터에 포함:**

```python
await notification_service.send(
    title="Workflow Completed",
    message="2 posts created",
    metadata={
        "workflow_id": 1,
        "duration": "7m 30s",
        "cost_estimate": "$0.45",  # API 비용
        "next_scheduled": "2025-02-01 09:00"
    }
)
```

### 4. 에러 그룹화

**같은 에러가 반복될 때 그룹화:**

```python
# 1시간 내 같은 에러는 한 번만 알림
if should_notify(error_type, cooldown_minutes=60):
    await notification_service.send_api_error(...)
```

## 비용 고려사항

### 이메일

- **Gmail**: 무료 (일일 500개 제한)
- **AWS SES**: $0.10/1000개
- **SendGrid**: 무료 티어 100개/일

### Slack

- **Incoming Webhooks**: 무료 (rate limit 존재)
- **Block Kit messages**: 무료

## 다음 단계

- **Telegram Bot 지원** 추가 예정
- **Webhook 일반화** (임의의 웹훅 URL 지원)
- **알림 템플릿 커스터마이징**
- **알림 히스토리 및 통계**

## 관련 문서

- [원클릭 자동화](./ONE_CLICK_AUTOMATION.md)
- [Celery Beat 스케줄러](./CELERY_BEAT.md)
- [모니터링 시스템](./MONITORING.md)
- [API 문서](http://localhost:8000/docs)
