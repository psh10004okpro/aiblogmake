# 이메일 마케팅 자동화

AI 기반 뉴스레터 생성 및 자동 발송 시스템입니다.

## 주요 기능

1. **AI 뉴스레터 생성**: 최신 포스트로 자동 뉴스레터 생성
2. **자동 발송**: 구독자 목록에 자동 발송
3. **스마트 제목**: AI가 클릭률 높은 제목 생성
4. **HTML 템플릿**: 반응형 이메일 템플릿

## API 사용법

### 뉴스레터 생성
```bash
curl -X POST "http://localhost:8000/api/v1/email-marketing/generate-newsletter" \
  -H "Content-Type: application/json" \
  -d '{
    "posts": [
      {"title": "SEO 가이드", "excerpt": "...", "url": "https://..."},
      {"title": "마케팅 팁", "excerpt": "...", "url": "https://..."}
    ],
    "template_type": "weekly_digest"
  }'
```

### 뉴스레터 발송
```bash
curl -X POST "http://localhost:8000/api/v1/email-marketing/send-newsletter" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "이번 주 블로그 업데이트",
    "body_html": "<p>...</p>",
    "subscribers": ["user@example.com"]
  }'
```

## 예상 효과

- 재방문율 40-60% 증가
- 직접 트래픽 증가
- 고객 충성도 향상
- 블로그 성장 가속화

---

**이메일 마케팅 v1.0.0**
