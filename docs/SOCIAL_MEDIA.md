# 소셜 미디어 자동 포스팅

Facebook, Twitter, LinkedIn에 블로그 포스트를 자동으로 공유하는 마케팅 자동화 기능입니다.

## 주요 기능

1. **AI 기반 메시지 생성**: 플랫폼별로 최적화된 포스트 메시지 자동 생성
2. **자동 해시태그 생성**: 키워드 기반 해시태그 자동 생성
3. **멀티 플랫폼 지원**: Facebook, Twitter, LinkedIn 동시 포스팅
4. **예약 포스팅**: 최적 시간대 자동 포스팅 (향후 구현)
5. **성과 추적**: 포스트별 결과 및 URL 확인

## 설정 방법

### 1. Facebook 설정

**Facebook 페이지 Access Token 생성:**
1. [Facebook Developers](https://developers.facebook.com/) 접속
2. 앱 생성 → "Pages API" 추가
3. 페이지 선택 후 Access Token 생성
4. Token에 `pages_manage_posts` 권한 부여

**환경 변수 설정 (.env):**
```env
FACEBOOK_PAGE_ID=your-page-id
FACEBOOK_ACCESS_TOKEN=your-access-token
```

### 2. Twitter 설정

**Twitter API 키 생성:**
1. [Twitter Developer Portal](https://developer.twitter.com/) 접속
2. 앱 생성 → "Read and Write" 권한 설정
3. API Key, API Secret, Access Token 생성

**환경 변수 설정 (.env):**
```env
TWITTER_API_KEY=your-api-key
TWITTER_API_SECRET=your-api-secret
TWITTER_ACCESS_TOKEN=your-access-token
TWITTER_ACCESS_SECRET=your-access-secret
```

### 3. LinkedIn 설정

**LinkedIn Access Token 생성:**
1. [LinkedIn Developers](https://www.linkedin.com/developers/) 접속
2. 앱 생성 → "Share on LinkedIn" 권한 신청
3. OAuth 2.0 인증으로 Access Token 생성

**환경 변수 설정 (.env):**
```env
LINKEDIN_ACCESS_TOKEN=your-access-token
LINKEDIN_ORGANIZATION_ID=your-organization-id
```

### 4. 기능 활성화

```env
ENABLE_SOCIAL_AUTO_POST=True
SOCIAL_AUTO_POST_ON_PUBLISH=True
SOCIAL_PLATFORMS=facebook,twitter,linkedin
```

## 사용 방법

### 1. 대시보드에서 포스팅

```
http://localhost:8000/ → 소셜 미디어 메뉴
```

1. 제목, 요약, 키워드, 링크 입력
2. 포스팅할 플랫폼 선택
3. "소셜 미디어에 포스팅" 버튼 클릭

### 2. API로 포스팅

**모든 플랫폼에 포스팅:**
```bash
curl -X POST "http://localhost:8000/api/v1/social-media/post" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "SEO 완벽 가이드 2025",
    "excerpt": "검색 엔진 최적화를 위한 완벽한 가이드입니다.",
    "keywords": ["SEO", "마케팅", "블로그"],
    "link": "https://yourblog.com/seo-guide",
    "platforms": ["facebook", "twitter"]
  }'
```

**특정 플랫폼에 포스팅:**
```bash
curl -X POST "http://localhost:8000/api/v1/social-media/post/facebook" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "SEO 완벽 가이드",
    "excerpt": "검색 엔진 최적화...",
    "keywords": ["SEO"],
    "link": "https://yourblog.com/seo-guide"
  }'
```

### 3. Python에서 사용

```python
from app.services.social_media import get_social_media_service

social_service = get_social_media_service()

# 모든 플랫폼에 포스팅
results = await social_service.post_to_all(
    title="SEO 완벽 가이드",
    excerpt="검색 엔진 최적화...",
    keywords=["SEO", "마케팅"],
    link="https://yourblog.com/seo-guide",
    image_url="https://yourblog.com/images/seo.jpg"
)

# 결과 확인
for platform, result in results.items():
    if result.success:
        print(f"{platform}: {result.url}")
    else:
        print(f"{platform} 실패: {result.error}")
```

## 플랫폼별 특성

### Facebook
- **메시지 형식**: 친근하고 매력적인 톤
- **이모지**: 적절히 사용
- **최적 길이**: 2-3문장
- **해시태그**: 3-5개 권장

### Twitter
- **메시지 형식**: 임팩트 있는 한 문장
- **최대 길이**: 280자 (자동 truncate)
- **해시태그**: 2-3개 권장
- **링크**: 자동으로 단축 URL 생성

### LinkedIn
- **메시지 형식**: 전문적이고 인사이트 있는 톤
- **최적 길이**: 3-4문장
- **비즈니스 가치 강조**
- **해시태그**: 5-7개 권장

## 자동화 워크플로우 통합

WordPress 발행 시 자동으로 소셜 미디어에 포스팅하려면:

```python
# app/services/workflow_engine.py에서

async def publish_post(self, post_id):
    # WordPress 발행
    result = await self.wordpress_service.publish_post(post_id)

    # 소셜 미디어 자동 포스팅
    if settings.social_auto_post_on_publish:
        from app.services.social_media import get_social_media_service

        social_service = get_social_media_service()
        await social_service.post_to_all(
            title=post.title,
            excerpt=post.excerpt,
            keywords=post.keywords,
            link=result['url'],
            image_url=post.hero_image_url
        )
```

## 트러블슈팅

### Facebook 오류
- **"Invalid OAuth access token"**: Access Token 갱신 필요
- **"Missing permissions"**: `pages_manage_posts` 권한 확인

### Twitter 오류
- **"Unauthorized"**: API 키 및 OAuth 서명 확인
- **"Rate limit exceeded"**: 15분 대기 후 재시도

### LinkedIn 오류
- **"Access token expired"**: OAuth 재인증 필요
- **"Permission denied"**: "Share on LinkedIn" 권한 확인

## Best Practices

1. **포스팅 빈도**: 플랫폼당 하루 2-3회 권장
2. **최적 시간대**:
   - Facebook: 오전 9시, 오후 1시, 오후 7시
   - Twitter: 오전 8시, 정오, 오후 5시
   - LinkedIn: 오전 10시, 정오, 오후 5시
3. **이미지 사용**: 이미지가 있는 포스트가 참여율 2배 높음
4. **해시태그**: 너무 많으면 스팸으로 보일 수 있음
5. **A/B 테스트**: 여러 메시지 버전 테스트

## 성과 측정

향후 업데이트에서 추가될 기능:
- 포스트별 클릭 수, 참여율 추적
- 최적 시간대 자동 분석
- 자동 A/B 테스트
- 성과 리포트 생성

---

**소셜 미디어 자동 포스팅 v1.0.0**
AI 블로그 자동화 시스템
