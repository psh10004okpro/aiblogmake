# 블로그 자동화 시스템 (Blog Automation System)

한국 시장을 타겟으로 하는 완전 자동화된 SEO 최적화 블로그 시스템입니다. 키워드 리서치부터 콘텐츠 생성, 이미지 생성, AdSense 광고 삽입, WordPress 발행까지 전체 워크플로우를 자동화합니다.

## 주요 기능

### 🔍 황금키워드 발견
- **Google Keyword Planner API**: 검색량, 경쟁도, CPC 데이터
- **Naver Search Ad API**: 네이버 월간 PC/모바일 검색수
- **Playwright**: 네이버 자동완성 스크래핑
- **Google Trends**: 트렌드 분석
- **황금키워드 점수**: 데이터 기반 키워드 평가 시스템

### ✍️ SEO 최적화 콘텐츠 생성
- **Claude 3.5 Sonnet**: 자연스러운 한국어 콘텐츠 생성
- **E-E-A-T 원칙**: 2025 Google SEO 기준 준수
- **구조화된 콘텐츠**: H1/H2/H3 계층, 내부 링크, FAQ
- **스키마 마크업**: BlogPosting, FAQPage 자동 생성
- **자연스러운 AI 콘텐츠**: 한국 문화 맥락 반영

### 🖼️ 자동 이미지 생성 및 최적화
- **DALL-E 3**: 고품질 히어로 이미지 생성 (1792x1024)
- **Unsplash API**: 보조 이미지 (3-4개/포스트)
- **이미지 최적화**: WebP 변환, 리사이징, 200KB 이하
- **GPT-4 Vision**: SEO alt 텍스트 자동 생성 (125자 이내)
- **워터마크**: 자동 워터마크 삽입

### 💰 AdSense 광고 자동 배치
- **최적 배치**: 도입부 후, 중간, 결론 전
- **광고 밀도**: 500단어당 1개 (최대 3-4개)
- **반응형 광고**: 데스크톱/모바일 자동 최적화
- **AdSense 정책 준수**: 자동 밀도 검증

### 🚀 WordPress 자동 발행
- **WordPress REST API**: 포스트, 이미지, 카테고리/태그
- **스케줄링**: 미래 시간 예약 발행
- **이미지 업로드**: WordPress 미디어 라이브러리 자동 업로드
- **메타데이터**: SEO 최적화 메타 태그

## 기술 스택

- **Backend**: FastAPI 0.120 (비동기, 타입 힌트)
- **Database**: PostgreSQL 15 + SQLAlchemy (비동기)
- **Cache/Queue**: Redis + Celery
- **AI Services**:
  - Anthropic Claude API (콘텐츠 생성)
  - OpenAI API (DALL-E 3, GPT-4 Vision)
- **Web Scraping**: Playwright + BeautifulSoup4
- **Image Processing**: Pillow
- **Deployment**: Docker + Docker Compose

## 프로젝트 구조

```
blog-automation/
├── app/
│   ├── main.py                    # FastAPI 진입점
│   ├── core/
│   │   ├── config.py             # 설정 관리
│   │   ├── database.py           # DB 연결 (비동기)
│   │   └── security.py           # 인증/보안
│   ├── models/
│   │   ├── schemas.py            # Pydantic 모델
│   │   └── database.py           # SQLAlchemy 모델
│   ├── services/
│   │   ├── keyword_research.py  # 키워드 리서치
│   │   ├── content_generator.py # 콘텐츠 생성
│   │   ├── image_generator.py   # 이미지 생성
│   │   ├── ad_inserter.py       # 광고 배치
│   │   └── publisher.py         # WordPress 발행
│   ├── api/
│   │   ├── dependencies.py      # 의존성 주입
│   │   └── routes/
│   │       ├── keywords.py      # 키워드 엔드포인트
│   │       ├── content.py       # 콘텐츠 엔드포인트
│   │       └── schedule.py      # 스케줄링 엔드포인트
│   ├── utils/
│   │   ├── scraper.py           # Playwright 스크래핑
│   │   ├── seo.py               # SEO 유틸리티
│   │   └── logger.py            # 로깅 설정
│   └── tasks/
│       └── celery_tasks.py      # Celery 태스크
├── tests/                        # 테스트
├── docker-compose.yml            # Docker Compose 설정
├── Dockerfile                    # Docker 이미지
├── requirements.txt              # Python 의존성
├── .env.example                  # 환경 변수 예제
└── README.md                     # 프로젝트 문서
```

## 설치 및 실행

### 1. 사전 요구사항

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis

### 2. 저장소 클론

```bash
git clone https://github.com/yourusername/blog-automation.git
cd blog-automation
```

### 3. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 편집하여 API 키를 설정하세요:

```env
# AI Services
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Google Ads API
GOOGLE_ADS_DEVELOPER_TOKEN=your-token
GOOGLE_ADS_CLIENT_ID=your-client-id
GOOGLE_ADS_CLIENT_SECRET=your-secret
GOOGLE_ADS_REFRESH_TOKEN=your-refresh-token
GOOGLE_ADS_CUSTOMER_ID=123-456-7890

# Naver Search Ad API
NAVER_API_KEY=your-naver-api-key
NAVER_SECRET_KEY=your-naver-secret-key

# Unsplash API
UNSPLASH_ACCESS_KEY=your-unsplash-key

# WordPress
WP_URL=https://your-blog.com
WP_USERNAME=your-username
WP_APP_PASSWORD=your-app-password

# AdSense
ADSENSE_CLIENT_ID=ca-pub-1234567890123456
ADSENSE_AD_SLOT_INLINE=1234567890
```

### 4. Docker로 실행 (권장)

```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 특정 서비스만 재시작
docker-compose restart api

# 서비스 중지
docker-compose down
```

서비스 접근:
- API: http://localhost:8000
- API 문서: http://localhost:8000/docs
- Flower (Celery 모니터링): http://localhost:5555

### 5. 로컬 개발 환경

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium

# 데이터베이스 마이그레이션
# (프로덕션에서는 Alembic 사용 권장)

# FastAPI 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 별도 터미널: Celery Worker 실행
celery -A app.tasks.celery_tasks worker --loglevel=info

# 별도 터미널: Celery Beat 실행
celery -A app.tasks.celery_tasks beat --loglevel=info
```

## API 사용 예제

### 키워드 리서치

```bash
curl -X POST "http://localhost:8000/api/v1/keywords/research" \
  -H "Content-Type: application/json" \
  -d '{
    "seed_keywords": ["블로그 SEO", "키워드 리서치"],
    "include_naver": true,
    "include_autocomplete": true
  }'
```

### 콘텐츠 생성

```bash
curl -X POST "http://localhost:8000/api/v1/content/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "블로그 SEO 최적화",
    "target_word_count": 2000,
    "tone": "professional",
    "include_images": true,
    "include_faq": true
  }'
```

### 전체 워크플로우 실행

```bash
curl -X POST "http://localhost:8000/api/v1/content/complete-workflow" \
  -H "Content-Type: application/json" \
  -d '{
    "seed_keywords": ["블로그", "SEO"],
    "num_posts": 3,
    "publish_immediately": false,
    "schedule_interval_hours": 24
  }'
```

## 황금키워드 점수 알고리즘

```python
score = (
    (search_volume_score * 0.30) +
    ((100 - competition) * 0.40) +
    (cpc_score * 0.20) +
    (trend * 10)
) * trend_multiplier
```

- **검색량 (30%)**: 월간 검색 볼륨 (로그 스케일)
- **경쟁도 (40%)**: 낮을수록 좋음 (역수)
- **CPC (20%)**: 높을수록 가치 있는 키워드
- **트렌드 (10%)**: 상승 트렌드에 가중치

## SEO 최적화 체크리스트

- ✅ 제목에 주요 키워드 포함 (30-60자)
- ✅ H1 태그 1개만 사용
- ✅ H2-H3 계층 구조 (3-5개 H2)
- ✅ 1500-3000자 분량
- ✅ 이미지 3-5개 (WebP, 200KB 이하)
- ✅ 모든 이미지에 alt 텍스트 (125자 이내)
- ✅ 내부 링크 3-5개
- ✅ BlogPosting 스키마 마크업
- ✅ FAQ 스키마 (선택)
- ✅ Open Graph / Twitter Cards

## 테스트

```bash
# 모든 테스트 실행
pytest

# 커버리지 포함
pytest --cov=app --cov-report=html

# 특정 테스트만
pytest tests/test_keywords.py
```

## 문제 해결

### Google Ads API 설정

1. [Google Ads API 문서](https://developers.google.com/google-ads/api) 참조
2. Developer Token 신청
3. OAuth 2.0 인증 설정
4. Refresh Token 생성

### Naver Search Ad API 설정

1. [네이버 검색광고 API](https://naver.github.io/searchad-apidoc/) 참조
2. API 계정 생성
3. API Key 및 Secret Key 발급

### WordPress REST API 설정

1. WordPress 관리자 > 사용자 > 프로필
2. "애플리케이션 비밀번호" 생성
3. `.env`에 `WP_APP_PASSWORD` 설정

## 프로덕션 배포

### Docker Swarm / Kubernetes

프로덕션 환경에서는 다음을 고려하세요:

- **스케일링**: Celery worker 수평 확장
- **모니터링**: Sentry, Prometheus, Grafana
- **로그 수집**: ELK Stack 또는 Loki
- **백업**: PostgreSQL 자동 백업
- **SSL/TLS**: Nginx 리버스 프록시
- **Rate Limiting**: Redis 기반 rate limiter

### 환경 변수

```bash
# 프로덕션 설정
APP_ENV=production
DEBUG=False
LOG_LEVEL=INFO

# 보안
SECRET_KEY=<강력한-랜덤-키>

# 데이터베이스
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100
```

## 라이선스

MIT License

## 기여

Pull Request를 환영합니다! 다음을 확인해주세요:

1. 코드 스타일: Black, Flake8
2. 타입 힌트: Mypy
3. 테스트: Pytest
4. 문서화: Docstring (Google 스타일)

## 지원

문제가 발생하면 [GitHub Issues](https://github.com/yourusername/blog-automation/issues)에 보고해주세요.

## 참고 자료

- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [Celery 문서](https://docs.celeryq.dev/)
- [WordPress REST API](https://developer.wordpress.org/rest-api/)
- [Google Search Central](https://developers.google.com/search)
- [Schema.org](https://schema.org/)

## 로드맵

- [ ] 다국어 지원 (영어, 일본어)
- [ ] Blogger API 통합
- [ ] 커스텀 AI 모델 파인튜닝
- [ ] A/B 테스트 기능
- [ ] 분석 대시보드
- [ ] 소셜 미디어 자동 공유
- [ ] SEO 성능 추적
- [ ] 키워드 순위 모니터링

---

**Made with ❤️ for Korean Bloggers**
