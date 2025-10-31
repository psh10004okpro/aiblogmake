# 경쟁자 분석 대시보드

## 개요

경쟁자 블로그를 자동 모니터링하고 키워드 갭, 콘텐츠 갭을 분석하여 전략적 인사이트를 제공합니다.

### 주요 기능

1. **RSS 피드 모니터링** - 경쟁 블로그 자동 추적
2. **키워드 갭 분석** - 놓친 키워드 발견
3. **콘텐츠 갭 분석** - 미다룬 주제 파악
4. **SEO 비교** - 도메인 권위도, 발행 빈도 비교
5. **콘텐츠 아이디어** - AI 기반 차별화 제안

### 예상 효과

- **키워드 기회**: 30-50% 증가
- **콘텐츠 아이디어**: 지속적 공급
- **트래픽**: 20-40% 증가
- **경쟁력**: 데이터 기반 의사결정

---

## API 사용법

### 1. 경쟁자 포스트 가져오기

**Endpoint**: `POST /api/v1/competitor/fetch-posts`

**Request**:
```json
{
  "rss_feed_url": "https://competitor.com/feed",
  "days": 30
}
```

**Response**:
```json
{
  "success": true,
  "total_posts": 15,
  "posts": [
    {
      "title": "AI 블로그 자동화 가이드",
      "url": "https://competitor.com/post/1",
      "published_date": "2024-01-15T10:00:00Z",
      "excerpt": "AI를 활용한 블로그 자동화 방법...",
      "keywords": ["AI", "블로그", "자동화"],
      "estimated_traffic": null
    }
  ]
}
```

### 2. 키워드 갭 분석

**Endpoint**: `POST /api/v1/competitor/keyword-gaps`

**Request**:
```json
{
  "our_keywords": ["블로그", "SEO", "마케팅"],
  "competitor_keywords": ["블로그", "SEO", "마케팅", "AI", "자동화", "수익화"]
}
```

**Response**:
```json
{
  "success": true,
  "total_gaps": 3,
  "keyword_gaps": [
    {
      "keyword": "AI",
      "opportunity_score": 85,
      "difficulty": "Medium",
      "suggested_topics": [
        "AI 완벽 가이드",
        "AI 초보자 튜토리얼",
        "AI 베스트 프랙티스"
      ]
    }
  ]
}
```

### 3. 콘텐츠 갭 분석

**Endpoint**: `POST /api/v1/competitor/content-gaps`

### 4. 종합 리포트 생성

**Endpoint**: `POST /api/v1/competitor/generate-report`

**Request**:
```json
{
  "competitor_name": "경쟁사 A",
  "competitor_url": "https://competitor.com",
  "rss_feed_url": "https://competitor.com/feed",
  "domain_authority": 65,
  "our_keywords": ["블로그", "SEO"],
  "our_topics": ["블로그 운영", "SEO 최적화"]
}
```

**Response**:
```json
{
  "success": true,
  "competitor_name": "경쟁사 A",
  "analysis_date": "2024-01-15T12:00:00Z",
  "recent_posts": [...],
  "keyword_gaps": [...],
  "content_gaps": [...],
  "seo_comparison": {
    "our_domain_authority": 45,
    "competitor_domain_authority": 65,
    "our_monthly_posts": 20,
    "competitor_monthly_posts": 25
  },
  "recommendations": [
    "키워드 'AI'에 대한 콘텐츠 작성 권장",
    "월간 포스트 수를 25개 이상으로 증가 권장"
  ]
}
```

### 5. 콘텐츠 아이디어 제안

**Endpoint**: `POST /api/v1/competitor/suggest-content-ideas`

---

## 모범 사례

### 분석 주기

- **추천**: 주간 (Weekly)
- **최소**: 월간 (Monthly)
- **트렌드 주제**: 매일

### 추적할 경쟁자 수

- **최적**: 3-5개
- **최대**: 10개
- **선정 기준**: 트래픽, 도메인 권위도, 주제 유사성

### 주요 지표

| 지표 | 설명 | 좋은 값 | 개선 방법 |
|------|------|---------|----------|
| Domain Authority | 도메인 권위도 | > 50 | 백링크 구축 |
| Content Frequency | 발행 빈도 | > 3/week | 자동화 |
| Keyword Coverage | 키워드 커버리지 | > 100 | 롱테일 공략 |
| Backlinks | 백링크 수 | > 1000 | 게스트 포스팅 |

---

## 활용 전략

### 1. Content Gap 우선순위

경쟁자가 다루지만 우리는 없는 주제를 먼저 공략:

```
1. 키워드 갭 분석 실행
2. 기회 점수 높은 순으로 정렬
3. 상위 10개 주제 선정
4. 차별화 각도로 콘텐츠 작성
```

### 2. 차별화 전략

같은 주제라도 다른 관점:

- **깊이**: 경쟁자보다 2배 더 상세하게
- **시각화**: 인포그래픽, 차트 추가
- **실용성**: 실전 예제, 템플릿 제공
- **최신성**: 최신 트렌드 반영

### 3. 속도 경쟁

트렌드 주제를 빠르게:

- RSS 피드로 매일 모니터링
- 새 주제 발견 시 24시간 내 작성
- First-mover advantage 확보

---

## 도구 추천

### 필수 도구

1. **SEMrush** - 키워드 및 백링크 분석
2. **Ahrefs** - 트래픽 및 순위 추적
3. **BuzzSumo** - 인기 콘텐츠 발견
4. **Google Search Console** - 검색 성과
5. **Feedly** - RSS 피드 리더

### 자동화 팁

- RSS 피드를 Slack/이메일로 자동 전송
- 주간 리포트 자동 생성
- 키워드 갭 알림 설정

---

## 결론

경쟁자 분석은 전략적 콘텐츠 기획의 핵심입니다.

**주요 이점**:
- ✅ 키워드 기회 30-50% 증가
- ✅ 콘텐츠 아이디어 지속 공급
- ✅ 데이터 기반 의사결정
- ✅ 경쟁 우위 확보

**시작하기**: API로 첫 분석을 시작하세요!
