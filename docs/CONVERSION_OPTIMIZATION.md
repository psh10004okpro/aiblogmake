# 컨버전 최적화 (CRO)

블로그 구독률과 리드 생성을 극대화하는 자동화 기능입니다.

## 주요 기능

1. **CTA 자동 삽입**: 콘텐츠 내 최적 위치에 CTA 자동 배치
2. **리드 마그넷 생성**: PDF, 체크리스트, 템플릿 자동 생성
3. **스마트 팝업**: Exit-intent, 시간 기반, 스크롤 기반 팝업
4. **A/B 테스트**: CTA 변형 테스트 및 최적화

## API 사용법

### CTA 자동 삽입
```bash
curl -X POST "http://localhost:8000/api/v1/conversion/insert-ctas" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "<p>블로그 콘텐츠...</p>",
    "keywords": ["SEO", "마케팅"],
    "content_type": "blog"
  }'
```

### 리드 마그넷 생성
```bash
curl -X POST "http://localhost:8000/api/v1/conversion/lead-magnet" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "SEO 체크리스트",
    "description": "완벽한 SEO를 위한 단계별 가이드",
    "content_type": "pdf",
    "keywords": ["SEO"]
  }'
```

### 팝업 생성
```bash
curl -X POST "http://localhost:8000/api/v1/conversion/popup" \
  -H "Content-Type: application/json" \
  -d '{
    "popup_type": "exit_intent",
    "custom_message": "떠나시기 전에 무료 가이드를 받아가세요!"
  }'
```

## 예상 효과

- 구독률 2-3배 증가
- 리드 생성 증가
- 이탈률 감소
- 체류시간 증가

---

**컨버전 최적화 v1.0.0**
