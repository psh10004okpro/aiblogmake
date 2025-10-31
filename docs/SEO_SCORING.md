# SEO 점수 계산 시스템

콘텐츠 품질 검증 - 완전한 SEO 분석 및 최적화 가이드

## 개요

SEO Scoring System은 블로그 콘텐츠의 검색 엔진 최적화 품질을 종합적으로 분석하고 점수화하는 시스템입니다. 6가지 핵심 요소를 분석하여 0-100점 스케일의 점수를 제공하고, 구체적인 개선 제안을 생성합니다.

### 주요 기능

1. **키워드 밀도 분석** (20% 가중치)
   - 키워드 출현 빈도 계산
   - 최적 밀도 1-2% 확인
   - 키워드 위치 분석 (제목, 첫 문단)

2. **제목 최적화** (20% 가중치)
   - 제목 길이 검증 (한국어: 15-30자)
   - 키워드 포함 여부 및 위치
   - 특수문자, 숫자 활용도

3. **메타 태그 검증** (15% 가중치)
   - 메타 설명 길이 (한국어: 60-80자)
   - 키워드 포함 여부
   - 행동 유도 문구 포함

4. **가독성 점수** (20% 가중치)
   - 평균 문장 길이
   - 단락 구조
   - 소제목 분포
   - 목록 사용
   - 텍스트 서식 (굵게, 기울임)

5. **내부 링크 분석** (10% 가중치)
   - 내부 링크 개수 (3-5개 권장)
   - 앵커 텍스트 설명성

6. **이미지 ALT 텍스트** (15% 가중치)
   - ALT 텍스트 존재 여부
   - 설명적인 ALT 텍스트
   - 키워드 포함

## 점수 체계

### 전체 점수 (0-100점)

| 점수 범위 | 등급 | 평가 |
|---------|------|------|
| 90-100 | A+ | 완벽 - 검색 엔진 최적화 우수 |
| 85-89 | A | 우수 - 약간의 개선만 필요 |
| 80-84 | B+ | 양호 - 몇 가지 개선 권장 |
| 75-79 | B | 보통 - 개선 여지 있음 |
| 70-74 | C+ | 미흡 - 여러 개선 필요 |
| 65-69 | C | 부족 - 많은 개선 필요 |
| 60-64 | D | 매우 부족 - 대폭 개선 필요 |
| 0-59 | F | 실패 - 전면 수정 필요 |

### 구성 요소 점수

각 요소는 독립적으로 0-100점으로 평가되며, 가중치를 적용하여 전체 점수를 계산합니다:

```
전체 점수 =
  (키워드 밀도 × 0.20) +
  (제목 최적화 × 0.20) +
  (메타 태그 × 0.15) +
  (가독성 × 0.20) +
  (내부 링크 × 0.10) +
  (이미지 ALT × 0.15)
```

## API 엔드포인트

### 1. 콘텐츠 SEO 분석

**POST** `/api/v1/seo/analyze`

임의의 콘텐츠에 대해 SEO 분석을 수행합니다.

```bash
curl -X POST http://localhost:8000/api/v1/seo/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "title": "완벽한 블로그 SEO 가이드 2025",
    "content": "<p>블로그 SEO는 검색 엔진 최적화의 핵심입니다...</p>",
    "meta_description": "블로그 SEO 최적화 방법을 단계별로 알려드립니다.",
    "target_keyword": "블로그 SEO",
    "h2_tags": ["SEO란 무엇인가", "키워드 리서치"],
    "h3_tags": ["온페이지 SEO", "오프페이지 SEO"],
    "internal_links": ["/seo-basics", "/keyword-research"],
    "images": [
      {"url": "image1.jpg", "alt_text": "블로그 SEO 체크리스트"}
    ]
  }'
```

**응답:**
```json
{
  "overall_score": 85.3,
  "grade": "A",
  "keyword_density_score": 90.0,
  "title_optimization_score": 85.0,
  "meta_tags_score": 80.0,
  "readability_score": 88.0,
  "internal_links_score": 75.0,
  "image_alt_score": 90.0,
  "issues": [
    {
      "severity": "low",
      "category": "internal_links",
      "message": "내부 링크 개수: 2개. 3-5개 권장."
    }
  ],
  "suggestions": [
    "🟡 개선 권장 사항:",
    "  • 내부 링크 개수: 2개. 3-5개 권장.",
    "✅ 훌륭합니다! SEO 최적화가 잘 되어 있습니다."
  ],
  "metrics": {
    "keyword_density": {
      "keyword": "블로그 SEO",
      "keyword_count": 8,
      "word_count": 500,
      "density_percentage": 1.6,
      "in_title": true,
      "in_first_paragraph": true
    },
    "title": {
      "length": 21,
      "keyword_present": true,
      "has_numbers": true,
      "has_punctuation": false
    }
  }
}
```

### 2. 포스트 SEO 분석 및 저장

**POST** `/api/v1/seo/analyze-post/{post_id}`

데이터베이스에 저장된 포스트를 분석하고 점수를 저장합니다.

```bash
curl -X POST "http://localhost:8000/api/v1/seo/analyze-post/1?save_score=true"
```

**Query Parameters:**
- `save_score`: 결과를 데이터베이스에 저장할지 여부 (default: true)

### 3. 포스트 SEO 점수 조회

**GET** `/api/v1/seo/scores/{post_id}`

저장된 SEO 점수를 조회합니다.

```bash
curl http://localhost:8000/api/v1/seo/scores/1
```

**응답:**
```json
{
  "id": 1,
  "post_id": 1,
  "overall_score": 85.3,
  "grade": "A",
  "keyword_density_score": 90.0,
  "title_optimization_score": 85.0,
  "meta_tags_score": 80.0,
  "readability_score": 88.0,
  "internal_links_score": 75.0,
  "image_alt_score": 90.0,
  "issues": [...],
  "suggestions": [...],
  "metrics": {...},
  "target_keyword": "블로그 SEO",
  "analyzed_at": "2025-01-31T10:00:00Z",
  "analyzer_version": "1.0",
  "created_at": "2025-01-31T10:00:00Z"
}
```

### 4. SEO 점수 목록 조회

**GET** `/api/v1/seo/scores`

필터링된 SEO 점수 목록을 조회합니다.

```bash
# 점수 80점 이상인 포스트
curl "http://localhost:8000/api/v1/seo/scores?min_score=80&limit=10"

# A 등급 포스트
curl "http://localhost:8000/api/v1/seo/scores?grade=A&limit=20"

# 60-80점 사이 포스트
curl "http://localhost:8000/api/v1/seo/scores?min_score=60&max_score=80"
```

**Query Parameters:**
- `min_score`: 최소 점수 필터 (0-100)
- `max_score`: 최대 점수 필터 (0-100)
- `grade`: 등급 필터 (A+, A, B+, B, C+, C, D, F)
- `limit`: 결과 개수 (default: 50, max: 100)
- `offset`: 페이지네이션 오프셋

### 5. SEO 통계

**GET** `/api/v1/seo/stats`

전체 SEO 통계를 조회합니다.

```bash
curl http://localhost:8000/api/v1/seo/stats
```

**응답:**
```json
{
  "total_analyzed": 50,
  "average_score": 78.5,
  "grade_distribution": {
    "A+": 5,
    "A": 10,
    "B+": 15,
    "B": 12,
    "C+": 5,
    "C": 2,
    "D": 1,
    "F": 0
  },
  "top_performers": [
    {
      "post_id": 42,
      "score": 95.2,
      "grade": "A+",
      "keyword": "블로그 SEO"
    }
  ],
  "needs_improvement": [
    {
      "post_id": 15,
      "score": 58.3,
      "grade": "F",
      "keyword": "마케팅 전략",
      "issue_count": 8
    }
  ]
}
```

### 6. SEO 점수 삭제

**DELETE** `/api/v1/seo/scores/{post_id}`

포스트의 SEO 점수를 삭제합니다.

```bash
curl -X DELETE http://localhost:8000/api/v1/seo/scores/1
```

## 상세 분석 기준

### 1. 키워드 밀도 (Keyword Density)

**최적 범위:** 1-2%

**점수 계산:**
- **50점**: 밀도 점수
  - 1-2.5%: 50점 (최적)
  - 0.5-1%: 40점 (약간 낮음)
  - 2.5-3.5%: 40점 (약간 높음)
  - 3.5% 이상: 20점 (키워드 스터핑 위험)
  - 0.5% 미만: 20점 (너무 낮음)

- **25점**: 제목에 키워드 포함
- **25점**: 첫 문단에 키워드 포함

**예시:**
```
콘텐츠: 500단어
키워드 출현: 8회
밀도: 1.6% ✅ 최적
제목에 포함: Yes ✅
첫 문단에 포함: Yes ✅
→ 100점
```

### 2. 제목 최적화 (Title Optimization)

**최적 길이:** 한국어 15-30자 (영어 30-60자)

**점수 계산:**
- **40점**: 길이 점수
  - 15-30자: 40점 (최적)
  - 30-40자: 35점 (허용)
  - 10-15자: 30점 (짧음)
  - 40자 이상: 25점 (김)

- **30점**: 키워드 포함 및 위치
  - 앞쪽 30%: 30점
  - 그 외: 25점
  - 없음: 0점

- **15점**: 특수문자, 숫자 사용
- **15점**: 기타 최적화 요소

**예시:**
```
제목: "완벽한 블로그 SEO 가이드 2025" (21자)
✅ 길이 최적
✅ 키워드 "블로그 SEO" 앞쪽에 위치
✅ 숫자 포함 (2025)
→ 95점
```

### 3. 메타 설명 (Meta Description)

**최적 길이:** 한국어 60-80자 (영어 120-160자)

**점수 계산:**
- **50점**: 길이 점수
  - 60-80자: 50점 (최적)
  - 80-100자: 45점 (허용)
  - 40-60자: 40점 (짧음)
  - 100자 이상: 35점 (잘릴 수 있음)

- **30점**: 키워드 포함
- **20점**: 행동 유도 문구 (방법, 가이드, 필수 등)

**예시:**
```
메타 설명: "블로그 SEO 최적화 방법을 단계별로 알려드립니다." (29자)
⚠️ 짧음 (60-80자 권장)
✅ 키워드 포함
✅ "방법" 포함
→ 70점
```

### 4. 가독성 (Readability)

**구성 요소:**

- **평균 문장 길이** (20점)
  - 최적: 15-25자
  - 허용: 10-15자 또는 25-35자
  - 주의: 10자 미만 또는 35자 이상

- **단락 구조** (20점)
  - 5개 이상 단락: 20점
  - 3-4개: 15점
  - 3개 미만: 10점

- **소제목 분포** (20점)
  - 500단어당 3-7개: 20점
  - 2-3개 또는 7-10개: 15점
  - 그 외: 10점

- **목록 사용** (20점)
  - 2개 이상: 20점
  - 1개: 15점
  - 없음: 5점

- **텍스트 서식** (20점)
  - 굵게/기울임 사용: 20점
  - 없음: 10점

### 5. 내부 링크 (Internal Links)

**최적 개수:** 3-5개

**점수 계산:**
- **60점**: 링크 개수
  - 3-5개: 60점 (최적)
  - 2개 또는 5-7개: 50점 (허용)
  - 1개: 30점 (부족)
  - 7개 이상: 40점 (과다)
  - 0개: 20점 (없음)

- **40점**: 앵커 텍스트 설명성
  - 80% 이상 설명적: 40점
  - 60-80%: 30점
  - 60% 미만: 20점

**피해야 할 앵커 텍스트:**
- "여기", "클릭", "링크", "here", "click"

**좋은 앵커 텍스트:**
- "블로그 SEO 기초 가이드"
- "키워드 리서치 방법"

### 6. 이미지 ALT 텍스트 (Image Alt Text)

**점수 계산:**
- **60점**: ALT 텍스트 존재
  - 100% 커버리지: 60점
  - 80% 이상: 50점
  - 50-80%: 35점
  - 50% 미만: 20점

- **20점**: 설명적인 ALT 텍스트
  - 5자 이상 설명적 텍스트

- **20점**: 키워드 포함
  - 최소 1개 이미지에 키워드 포함

**예시:**
```
❌ 나쁜 ALT: "image1", "photo", "pic"
✅ 좋은 ALT: "블로그 SEO 체크리스트 인포그래픽"
```

## 이슈 심각도

### High (높음) 🔴
- 키워드가 제목에 없음
- 키워드 밀도가 매우 낮거나 높음
- 메타 설명에 키워드 없음
- 내부 링크 없음
- 대부분 이미지에 ALT 없음

### Medium (중간) 🟡
- 키워드 밀도 약간 벗어남
- 제목 길이 부적절
- 메타 설명 길이 부적절
- 단락/소제목 부족
- 내부 링크 부족
- 많은 이미지에 ALT 없음

### Low (낮음) 🟢
- 제목 약간 길거나 짧음
- 메타 설명 약간 길거나 짧음
- 목록 미사용
- 일부 링크 앵커 텍스트 비설명적
- 일부 이미지 ALT 없음
- 이미지 ALT에 키워드 없음

## 프로그래밍 방식 사용

### Python 예시

```python
from app.services.seo_analyzer import SEOAnalyzer

# 분석기 초기화
analyzer = SEOAnalyzer()

# 콘텐츠 분석
result = analyzer.analyze(
    title="완벽한 블로그 SEO 가이드 2025",
    content="<p>블로그 SEO는...</p>",
    meta_description="블로그 SEO 최적화 방법을 알려드립니다.",
    target_keyword="블로그 SEO",
    h2_tags=["SEO란 무엇인가", "키워드 리서치"],
    h3_tags=["온페이지 SEO", "오프페이지 SEO"],
    internal_links=["/seo-basics", "/keyword-research"],
    images=[
        {"url": "img1.jpg", "alt_text": "블로그 SEO 체크리스트"}
    ]
)

# 결과 확인
print(f"전체 점수: {result.overall_score}")
print(f"등급: {analyzer._get_grade(result.overall_score)}")

# 이슈 확인
for issue in result.issues:
    print(f"[{issue['severity'].upper()}] {issue['message']}")

# 개선 제안
for suggestion in result.suggestions:
    print(suggestion)
```

### 워크플로우 통합

```python
# 콘텐츠 생성 후 자동 SEO 분석
from app.services.seo_analyzer import SEOAnalyzer
from app.models.database import SEOScore as SEOScoreModel

async def generate_and_analyze_content(keyword: str):
    # 1. 콘텐츠 생성
    content_data = await content_service.generate_content(keyword)

    # 2. SEO 분석
    analyzer = SEOAnalyzer()
    seo_result = analyzer.analyze(
        title=content_data["title"],
        content=content_data["content"],
        meta_description=content_data["meta_description"],
        target_keyword=keyword,
        # ...
    )

    # 3. 점수가 낮으면 재생성
    if seo_result.overall_score < 70:
        logger.warning(f"SEO score low: {seo_result.overall_score}")
        # 재생성 또는 수정

    # 4. 점수 저장
    seo_score = SEOScoreModel(
        post_id=post.id,
        overall_score=seo_result.overall_score,
        grade=analyzer._get_grade(seo_result.overall_score),
        # ...
    )
    db.add(seo_score)
    db.commit()

    return content_data, seo_result
```

## 최적화 체크리스트

### ✅ 필수 항목 (High Priority)

- [ ] 제목에 타겟 키워드 포함
- [ ] 첫 문단에 타겟 키워드 포함
- [ ] 키워드 밀도 1-2% 유지
- [ ] 메타 설명에 키워드 포함
- [ ] 모든 이미지에 ALT 텍스트
- [ ] 최소 3개 내부 링크

### 🟡 권장 항목 (Medium Priority)

- [ ] 제목 길이 15-30자 (한국어)
- [ ] 메타 설명 길이 60-80자 (한국어)
- [ ] 최소 5개 단락
- [ ] 500단어당 3-7개 소제목
- [ ] 최소 2개 목록 (ul/ol)
- [ ] 설명적인 링크 앵커 텍스트

### 🟢 선택 항목 (Low Priority)

- [ ] 제목에 숫자 포함
- [ ] 제목에 특수문자 (!?)
- [ ] 메타 설명에 행동 유도 문구
- [ ] 텍스트 서식 (굵게, 기울임)
- [ ] 이미지 ALT에 키워드 포함
- [ ] 평균 문장 길이 15-25자

## 트러블슈팅

### 점수가 낮게 나옵니다

**원인별 해결 방법:**

1. **키워드 밀도 문제 (F 등급)**
   ```
   문제: 키워드가 1회만 나옴 (밀도 0.2%)
   해결:
   - 제목에 키워드 추가
   - 첫 문단에 키워드 포함
   - 자연스럽게 2-3회 더 사용
   ```

2. **제목 문제 (D 등급)**
   ```
   문제: 제목 너무 김 (45자)
   해결: 15-30자로 줄이기
   예시:
   ❌ "완벽한 블로그 SEO 최적화 가이드: 초보자도 쉽게 따라할 수 있는 방법"
   ✅ "완벽한 블로그 SEO 가이드 2025"
   ```

3. **가독성 문제 (C 등급)**
   ```
   문제: 단락 없이 긴 텍스트
   해결:
   - 5-7개 단락으로 나누기
   - 소제목(H2, H3) 추가
   - 목록 활용
   - 중요한 부분 굵게 표시
   ```

### 특정 카테고리 점수가 0점입니다

**내부 링크 0점:**
```python
# 문제: internal_links가 비어있음
internal_links=[]

# 해결: 최소 3개 추가
internal_links=[
    "/blog-seo-basics",
    "/keyword-research-guide",
    "/content-optimization-tips"
]
```

**이미지 ALT 0점:**
```python
# 문제: ALT 텍스트가 없음
images=[{"url": "img.jpg", "alt_text": ""}]

# 해결: 설명적인 ALT 추가
images=[{"url": "img.jpg", "alt_text": "블로그 SEO 최적화 체크리스트"}]
```

### HTML 파싱 오류

```python
# 문제: 잘못된 HTML
content="<p>텍스트</P>"  # 대소문자 불일치

# 해결: 올바른 HTML 사용
content="<p>텍스트</p>"

# BeautifulSoup이 대부분 자동 수정하지만,
# 유효한 HTML을 사용하는 것이 좋습니다.
```

## 베스트 프랙티스

### 1. 워크플로우에 SEO 분석 통합

```python
# 콘텐츠 생성 → SEO 분석 → 점수 확인 → 발행/수정

def automated_content_workflow(keyword):
    # 생성
    content = generate_content(keyword)

    # 분석
    seo_score = analyze_seo(content, keyword)

    # 점수 확인
    if seo_score.overall_score >= 80:
        # 점수 좋음 → 발행
        publish(content)
    elif seo_score.overall_score >= 70:
        # 점수 보통 → 경고 후 발행
        log.warning("SEO score low but acceptable")
        publish(content)
    else:
        # 점수 낮음 → 재생성 또는 수동 수정
        log.error("SEO score too low, needs improvement")
        # 개선 제안 적용
        improved_content = apply_suggestions(content, seo_score.suggestions)
        return improved_content
```

### 2. 주기적 재분석

```python
# 오래된 포스트 재분석 (SEO 기준 변경 대응)

from datetime import datetime, timedelta

def reanalyze_old_posts():
    # 6개월 이상 된 포스트
    old_threshold = datetime.now() - timedelta(days=180)

    old_posts = Post.query.filter(
        Post.created_at < old_threshold
    ).all()

    for post in old_posts:
        # 재분석
        new_score = analyze_post(post.id, save_score=True)

        # 점수 하락 시 알림
        if post.seo_score and new_score.overall_score < post.seo_score.overall_score - 10:
            notify_admin(f"Post {post.id} SEO score dropped significantly")
```

### 3. A/B 테스트

```python
# 제목 A/B 테스트

titles = [
    "완벽한 블로그 SEO 가이드",
    "블로그 SEO 완벽 가이드 2025",
    "2025 블로그 SEO: 완벽 가이드"
]

best_title = None
best_score = 0

for title in titles:
    score = analyze_seo(
        title=title,
        content=content,
        # ...
    )

    if score.title_optimization_score > best_score:
        best_score = score.title_optimization_score
        best_title = title

print(f"Best title: {best_title} (score: {best_score})")
```

### 4. 자동 개선

```python
# 일부 이슈는 자동으로 수정 가능

def auto_improve_content(content, seo_result):
    improved = content

    for issue in seo_result.issues:
        if issue['category'] == 'keyword_placement':
            # 첫 문단에 키워드 추가
            if 'first_paragraph' in issue['message']:
                improved = add_keyword_to_first_paragraph(
                    improved,
                    seo_result.metrics['keyword_density']['keyword']
                )

        elif issue['category'] == 'readability':
            # 단락 추가
            if 'paragraph' in issue['message'].lower():
                improved = add_paragraphs(improved)

    return improved
```

## 성능 고려사항

### 분석 속도

- 평균 처리 시간: 100-300ms (2000단어 기준)
- HTML 파싱: 50-100ms
- 텍스트 분석: 50-200ms

### 대량 분석

```python
# 여러 포스트 동시 분석

import asyncio

async def analyze_multiple_posts(post_ids):
    tasks = []
    for post_id in post_ids:
        task = asyncio.create_task(analyze_post_async(post_id))
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return results

# 100개 포스트 분석: 약 5-10초
```

### 캐싱

```python
# 동일한 콘텐츠 재분석 방지

from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def analyze_cached(content_hash, title, meta_desc, keyword):
    # 내용이 같으면 캐시된 결과 반환
    return analyzer.analyze(...)

# 사용
content_hash = hashlib.md5(content.encode()).hexdigest()
result = analyze_cached(content_hash, title, meta_desc, keyword)
```

## 다음 단계

SEO 점수 계산 시스템을 더욱 발전시킬 수 있는 방향:

1. **AI 기반 개선 제안**
   - LLM을 활용한 구체적인 수정 제안
   - 자동 콘텐츠 개선

2. **경쟁사 분석**
   - 상위 랭킹 페이지 분석
   - 비교 리포트 생성

3. **실시간 SEO 체크**
   - 작성 중 실시간 점수 표시
   - 즉각적인 개선 제안

4. **SEO 트렌드 추적**
   - 시간에 따른 점수 변화
   - 검색 엔진 알고리즘 업데이트 반영

## 관련 문서

- [원클릭 자동화](./ONE_CLICK_AUTOMATION.md)
- [알림 시스템](./NOTIFICATIONS.md)
- [Celery Beat 스케줄러](./CELERY_BEAT.md)
- [API 문서](http://localhost:8000/docs)
