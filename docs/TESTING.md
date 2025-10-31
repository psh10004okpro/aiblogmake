# 테스트 가이드

블로그 자동화 시스템의 테스트 커버리지 및 실행 가이드입니다.

## 📚 목차

- [테스트 구조](#테스트-구조)
- [테스트 실행](#테스트-실행)
- [테스트 마커](#테스트-마커)
- [테스트 작성 가이드](#테스트-작성-가이드)
- [커버리지](#커버리지)
- [CI/CD 통합](#cicd-통합)

## 🏗️ 테스트 구조

```
tests/
├── conftest.py              # 공통 픽스처 및 설정
├── test_keywords.py         # KeywordResearchService 테스트
├── test_content_generator.py # ContentGeneratorService 테스트
├── test_image_generator.py  # ImageGeneratorService 테스트
├── test_exceptions.py       # 예외 처리 테스트
└── logs/                    # 테스트 로그
```

### 테스트 계층

1. **단위 테스트 (Unit Tests)**
   - 개별 함수/메서드 테스트
   - 외부 의존성 모킹
   - 빠른 실행 (<1초)

2. **통합 테스트 (Integration Tests)**
   - 서비스 간 상호작용 테스트
   - 데이터베이스, API 통합
   - 중간 실행 속도 (1-5초)

3. **E2E 테스트 (End-to-End Tests)**
   - 전체 워크플로우 테스트
   - 실제 사용자 시나리오
   - 느린 실행 (5-30초)

## 🚀 테스트 실행

### 기본 실행

```bash
# 모든 테스트 실행
make test

# 단위 테스트만 실행
make test-unit

# 통합 테스트만 실행
make test-integration

# E2E 테스트만 실행
make test-e2e
```

### 특정 마커로 실행

```bash
# 서비스 레이어 테스트
make test-service

# API 엔드포인트 테스트
make test-api

# 빠른 테스트만 (slow, external 제외)
make test-fast

# 느린 테스트만
make test-slow
```

### 커버리지 리포트

```bash
# 커버리지 포함 테스트
make test-cov

# HTML 리포트 열기
make test-cov-report
```

### 기타 유용한 명령어

```bash
# 실패한 테스트만 재실행
make test-failed

# 상세 출력
make test-verbose

# 병렬 실행
make test-parallel

# Watch 모드 (코드 변경 시 자동 재실행)
make test-watch
```

## 🏷️ 테스트 마커

pytest 마커를 사용하여 테스트를 분류합니다.

### 사용 가능한 마커

| 마커 | 설명 | 예시 |
|------|------|------|
| `@pytest.mark.unit` | 단위 테스트 | 순수 함수 테스트 |
| `@pytest.mark.integration` | 통합 테스트 | DB, API 통합 |
| `@pytest.mark.e2e` | E2E 테스트 | 전체 워크플로우 |
| `@pytest.mark.slow` | 느린 테스트 (>5초) | 실제 API 호출 |
| `@pytest.mark.service` | 서비스 레이어 | 비즈니스 로직 |
| `@pytest.mark.api` | API 엔드포인트 | FastAPI 라우트 |
| `@pytest.mark.database` | 데이터베이스 | CRUD 작업 |
| `@pytest.mark.external` | 외부 API | Google, Naver 등 |
| `@pytest.mark.utils` | 유틸리티 함수 | 헬퍼 함수 |

### 마커 사용 예시

```python
import pytest

@pytest.mark.unit
def test_calculate_score():
    """단위 테스트"""
    pass

@pytest.mark.integration
@pytest.mark.service
@pytest.mark.asyncio
async def test_keyword_research():
    """통합 테스트"""
    pass

@pytest.mark.slow
@pytest.mark.external
@pytest.mark.asyncio
async def test_real_api_call():
    """느린 외부 API 테스트"""
    pass
```

## ✍️ 테스트 작성 가이드

### 1. 테스트 파일 명명 규칙

- 파일명: `test_<module_name>.py`
- 클래스명: `Test<FeatureName>`
- 함수명: `test_<what_it_tests>`

```python
# tests/test_keyword_research.py

class TestKeywordResearch:
    """KeywordResearch 서비스 테스트"""
    
    def test_calculate_golden_score(self):
        """황금 키워드 점수 계산 테스트"""
        pass
    
    async def test_get_google_keyword_data(self):
        """Google Ads API 데이터 가져오기 테스트"""
        pass
```

### 2. 픽스처 사용

`conftest.py`에 정의된 공통 픽스처를 활용하세요.

```python
@pytest.mark.asyncio
async def test_with_database(db_session, sample_keyword_data):
    """데이터베이스 세션과 샘플 데이터 사용"""
    # db_session: 테스트용 데이터베이스 세션
    # sample_keyword_data: 샘플 키워드 데이터
    pass
```

### 3. Mock 사용

외부 API는 항상 모킹하세요.

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_claude_api(mock_anthropic_client):
    """Claude API 모킹"""
    # mock_anthropic_client는 conftest.py에 정의됨
    mock_anthropic_client.messages.create.return_value.content = [
        MagicMock(text="모킹된 응답")
    ]
    
    # 테스트 코드...
```

### 4. 비동기 테스트

비동기 함수는 `@pytest.mark.asyncio` 데코레이터를 사용하세요.

```python
@pytest.mark.asyncio
async def test_async_function():
    """비동기 함수 테스트"""
    result = await some_async_function()
    assert result is not None
```

### 5. 예외 테스트

```python
def test_exception_handling():
    """예외 발생 테스트"""
    with pytest.raises(ValueError):
        function_that_raises_error()
```

### 6. 파라미터화 테스트

```python
@pytest.mark.parametrize("input,expected", [
    (1000, 65.5),
    (5000, 78.2),
    (10000, 85.0),
])
def test_score_calculation(input, expected):
    """여러 입력값에 대한 테스트"""
    result = calculate_score(input)
    assert result == pytest.approx(expected, rel=0.1)
```

## 📊 커버리지

### 커버리지 목표

- **최소 목표:** 70%
- **권장 목표:** 80%
- **이상적:** 90%+

### 커버리지 확인

```bash
# 터미널 출력
make test-cov

# HTML 리포트
make test-cov-report
```

### 커버리지 리포트 파일

- **HTML:** `htmlcov/index.html`
- **XML:** `coverage.xml` (CI/CD용)
- **JSON:** `coverage.json`

### 커버리지 제외

다음은 커버리지에서 제외됩니다 (`.coveragerc` 참조):

- `app/main.py` (진입점)
- `app/__init__.py`
- 테스트 파일
- Alembic 마이그레이션
- `if __name__ == "__main__"` 블록

## 🔄 CI/CD 통합

### GitHub Actions 예시

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests with coverage
      run: |
        make test-cov
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 🐛 디버깅

### 테스트 디버깅

```bash
# 특정 테스트만 실행
pytest tests/test_keywords.py::test_calculate_golden_score -v

# pdb 디버거 사용
pytest tests/test_keywords.py -v --pdb

# 로그 출력 활성화
pytest tests/test_keywords.py -v -s --log-cli-level=DEBUG
```

### 테스트 격리

각 테스트는 독립적이어야 합니다:

- 데이터베이스는 테스트마다 롤백
- Mock은 테스트 종료 후 자동 정리
- 파일 시스템은 `tmp_path` 픽스처 사용

## 📝 모범 사례

### DO ✅

- **단일 책임:** 각 테스트는 하나의 기능만 테스트
- **독립성:** 테스트 간 의존성 없음
- **반복 가능:** 언제 실행해도 같은 결과
- **빠른 실행:** 단위 테스트는 1초 이내
- **명확한 이름:** 무엇을 테스트하는지 명확히
- **AAA 패턴:** Arrange, Act, Assert

```python
def test_calculate_score():
    # Arrange (준비)
    input_data = 1000
    expected = 65.5
    
    # Act (실행)
    result = calculate_score(input_data)
    
    # Assert (검증)
    assert result == pytest.approx(expected, rel=0.1)
```

### DON'T ❌

- 실제 API 호출 (항상 모킹)
- 하드코딩된 타임스탬프
- 전역 상태 변경
- 테스트 간 의존성
- 너무 긴 테스트 (>50줄)
- 불명확한 테스트 이름

## 🔧 문제 해결

### 자주 발생하는 문제

#### 1. Import Error

```bash
# 프로젝트 루트에서 실행하세요
cd /path/to/aiblogmake
make test
```

#### 2. Async 테스트 실패

```python
# @pytest.mark.asyncio 데코레이터 확인
@pytest.mark.asyncio
async def test_async_function():
    pass
```

#### 3. Mock이 작동하지 않음

```python
# patch 경로를 정확히 지정
with patch('app.services.keyword_research.GoogleAdsClient'):
    # 테스트 코드
```

#### 4. 데이터베이스 에러

```python
# db_session 픽스처 사용
async def test_with_db(db_session):
    # db_session은 자동으로 롤백됨
    pass
```

## 📚 추가 리소스

- [pytest 공식 문서](https://docs.pytest.org/)
- [pytest-asyncio 문서](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py 문서](https://coverage.readthedocs.io/)
- [FastAPI 테스트 가이드](https://fastapi.tiangolo.com/tutorial/testing/)

## 💡 팁

1. **TDD (Test-Driven Development)** 실천
   - 먼저 테스트 작성
   - 그 다음 구현
   - 리팩토링

2. **커버리지에 집착하지 마세요**
   - 100% 커버리지가 버그 없음을 보장하지 않음
   - 의미 있는 테스트가 더 중요

3. **테스트는 문서**
   - 테스트 코드는 사용 예시
   - 명확하고 읽기 쉽게 작성

4. **지속적으로 개선**
   - 버그 발견 시 테스트 추가
   - 리팩토링 시 테스트 업데이트
   - 정기적인 테스트 리뷰

---

**문의:** 테스트 관련 질문이나 제안이 있으시면 이슈를 등록해주세요.
