# CI/CD 파이프라인 가이드

블로그 자동화 시스템의 지속적 통합/배포(CI/CD) 파이프라인 가이드입니다.

## 📚 목차

- [개요](#개요)
- [GitHub Actions 워크플로우](#github-actions-워크플로우)
- [워크플로우 설명](#워크플로우-설명)
- [배지 설정](#배지-설정)
- [커버리지 리포트](#커버리지-리포트)
- [문제 해결](#문제-해결)

## 🎯 개요

CI/CD 파이프라인은 다음을 자동화합니다:

- ✅ 자동 테스트 실행
- ✅ 코드 품질 검사 (linting, type checking)
- ✅ 보안 취약점 스캔
- ✅ 커버리지 리포트
- ✅ Docker 이미지 빌드
- ✅ PR 품질 체크

## 🔄 GitHub Actions 워크플로우

### 워크플로우 구조

```
.github/workflows/
├── test.yml       # 테스트 자동화
├── lint.yml       # 코드 품질 검사
├── docker.yml     # Docker 이미지 빌드
└── pr-check.yml   # PR 품질 체크
```

### 트리거 조건

| 워크플로우 | 트리거 | 브랜치 |
|-----------|--------|--------|
| test.yml | push, pull_request | main, develop, claude/* |
| lint.yml | push, pull_request | main, develop, claude/* |
| docker.yml | push | main, develop |
| pr-check.yml | pull_request | main, develop |

## 📝 워크플로우 설명

### 1. Tests (test.yml)

**목적**: 전체 테스트 스위트 실행 및 커버리지 측정

**단계**:
1. PostgreSQL, Redis 서비스 시작
2. Python 3.11 설치
3. 의존성 설치
4. Playwright 브라우저 설치
5. 단위 테스트 실행
6. 통합 테스트 실행 (외부 API 제외)
7. 커버리지 포함 전체 테스트
8. Codecov에 커버리지 업로드
9. HTML 커버리지 리포트 아티팩트 업로드

**실행 시간**: 약 5-10분

**환경 변수**:
```yaml
DATABASE_URL: postgresql+asyncpg://test_user:test_password@localhost:5432/test_db
REDIS_URL: redis://localhost:6379/0
ANTHROPIC_API_KEY: test-key
OPENAI_API_KEY: test-key
```

### 2. Code Quality (lint.yml)

**목적**: 코드 품질 및 보안 검사

**단계**:
1. Black (코드 포맷 검사)
2. isort (import 정렬 검사)
3. Flake8 (linting)
4. MyPy (타입 체킹)
5. Bandit (보안 취약점 스캔)
6. Safety (의존성 취약점 검사)

**실행 시간**: 약 2-3분

**리포트**:
- Bandit 보안 리포트 (JSON)
- 30일간 보관

### 3. Docker Build (docker.yml)

**목적**: Docker 이미지 빌드 및 테스트

**단계**:
1. Docker Buildx 설정
2. 메타데이터 추출
3. Docker 이미지 빌드
4. 기본 테스트 실행

**실행 시간**: 약 3-5분

**태그 전략**:
- `main` 브랜치: `latest`
- PR: `pr-{number}`
- 커밋: `{sha}`

### 4. PR Check (pr-check.yml)

**목적**: Pull Request 품질 검사

**단계**:
1. TODO 코멘트 수 확인
2. 대용량 파일 검사
3. 빠른 테스트 실행 (단위 테스트만)
4. 코드 포맷 검사
5. Import 정렬 검사
6. 기본 linting

**실행 시간**: 약 1-2분

## 🏆 배지 설정

### GitHub Actions 배지

README.md에 추가:

```markdown
![Tests](https://github.com/USERNAME/REPO/actions/workflows/test.yml/badge.svg)
![Lint](https://github.com/USERNAME/REPO/actions/workflows/lint.yml/badge.svg)
![Docker](https://github.com/USERNAME/REPO/actions/workflows/docker.yml/badge.svg)
```

### Codecov 배지

```markdown
[![codecov](https://codecov.io/gh/USERNAME/REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/USERNAME/REPO)
```

### 라이선스 배지

```markdown
![License](https://img.shields.io/badge/license-MIT-blue.svg)
```

### Python 버전 배지

```markdown
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
```

## 📊 커버리지 리포트

### Codecov 설정

`codecov.yml` 파일로 커버리지 요구사항 설정:

```yaml
coverage:
  status:
    project:
      default:
        target: 70%
        threshold: 2%
```

### 커버리지 확인

1. **PR에서 확인**:
   - PR에 Codecov 봇이 자동으로 코멘트 추가
   - 변경된 파일의 커버리지 확인

2. **Codecov 웹사이트**:
   - https://codecov.io/gh/USERNAME/REPO
   - 상세한 커버리지 리포트
   - 시간별 트렌드

3. **로컬에서 확인**:
   ```bash
   make test-cov
   make test-cov-report  # HTML 리포트 열기
   ```

### 아티팩트 다운로드

GitHub Actions 실행 페이지에서 아티팩트 다운로드:

- `coverage-report`: HTML 커버리지 리포트
- `test-logs`: 테스트 실패 시 로그
- `bandit-security-report`: 보안 스캔 결과

## 🔧 로컬에서 CI 재현

CI 환경을 로컬에서 재현하여 디버깅:

### 1. Docker Compose로 서비스 실행

```bash
# PostgreSQL + Redis 시작
docker-compose up -d postgres redis

# 테스트 실행
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/blog_automation \
REDIS_URL=redis://localhost:6379/0 \
pytest tests/ -v
```

### 2. act로 GitHub Actions 로컬 실행

```bash
# act 설치 (macOS)
brew install act

# act 설치 (Linux)
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# 워크플로우 실행
act push  # push 이벤트 시뮬레이션
act pull_request  # PR 이벤트 시뮬레이션

# 특정 워크플로우만 실행
act -W .github/workflows/test.yml
```

### 3. 모든 검사 로컬 실행

```bash
# 포맷 검사
make format-check

# Linting
make lint

# 타입 체킹
make type-check

# 전체 테스트
make test-cov

# Docker 빌드
docker build -t blog-automation:test .
```

## 🐛 문제 해결

### 테스트 실패

**문제**: 테스트가 CI에서는 실패하지만 로컬에서는 성공

**해결**:
1. 환경 변수 확인
2. 데이터베이스 상태 확인
3. 타임존 차이 확인
4. 의존성 버전 확인

```bash
# 로컬에서 CI 환경 재현
DATABASE_URL=postgresql+asyncpg://test_user:test_password@localhost:5432/test_db \
pytest tests/ -v
```

### Codecov 업로드 실패

**문제**: 커버리지가 Codecov에 업로드되지 않음

**해결**:
1. Codecov 토큰 확인 (public repo는 불필요)
2. coverage.xml 파일 생성 확인
3. Codecov Action 버전 확인

```yaml
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    file: ./coverage.xml
    fail_ci_if_error: false  # 실패해도 CI는 계속
```

### Docker 빌드 실패

**문제**: Docker 이미지 빌드 실패

**해결**:
1. Dockerfile 문법 확인
2. 의존성 설치 확인
3. 멀티스테이지 빌드 확인

```bash
# 로컬에서 빌드 테스트
docker build -t blog-automation:test .
docker run --rm blog-automation:test python --version
```

### 느린 CI 실행

**문제**: CI가 너무 오래 걸림

**해결**:
1. **캐싱 활용**:
   ```yaml
   - uses: actions/setup-python@v5
     with:
       cache: 'pip'  # pip 캐시
   ```

2. **빠른 테스트만 실행**:
   ```bash
   pytest -m "unit" -v  # 단위 테스트만
   ```

3. **병렬 실행**:
   ```bash
   pytest -n auto  # pytest-xdist 사용
   ```

4. **불필요한 단계 제거**:
   - 외부 API 테스트 제외
   - 느린 테스트 건너뛰기

## 📈 모범 사례

### 1. 작고 빠른 커밋

```bash
# ❌ 나쁨: 거대한 커밋
git commit -am "Massive refactoring"

# ✅ 좋음: 작고 명확한 커밋
git commit -m "feat: add keyword research service"
git commit -m "test: add unit tests for keyword service"
```

### 2. PR 전에 로컬 검사

```bash
# PR 생성 전 체크리스트
make format        # 코드 포맷
make lint          # Linting
make test-fast     # 빠른 테스트
```

### 3. 커밋 메시지 규칙

```
feat: 새로운 기능
fix: 버그 수정
docs: 문서 변경
style: 코드 포맷 (동작 변경 없음)
refactor: 리팩토링
perf: 성능 개선
test: 테스트 추가/수정
chore: 빌드/도구 변경
ci: CI 설정 변경
```

### 4. PR 설명 템플릿

```markdown
## 변경 사항
- 무엇을 변경했는지

## 변경 이유
- 왜 변경했는지

## 테스트
- [ ] 단위 테스트 추가
- [ ] 통합 테스트 추가
- [ ] 로컬에서 테스트 통과

## 스크린샷
(필요시)

## 체크리스트
- [ ] 코드 포맷 (`make format`)
- [ ] Linting 통과 (`make lint`)
- [ ] 테스트 통과 (`make test`)
- [ ] 문서 업데이트
```

## 🚀 프로덕션 배포

### 수동 배포

```bash
# 1. 태그 생성
git tag v1.0.0
git push origin v1.0.0

# 2. Docker 이미지 빌드
docker build -t blog-automation:v1.0.0 .

# 3. 이미지 푸시
docker push blog-automation:v1.0.0
```

### 자동 배포 (준비 중)

향후 추가 예정:
- AWS ECS/Fargate 배포
- Kubernetes 배포
- 자동 롤백
- Canary 배포

## 📚 추가 리소스

- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [Codecov 문서](https://docs.codecov.com/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [pytest 문서](https://docs.pytest.org/)

---

**문의**: CI/CD 관련 질문이나 제안이 있으시면 이슈를 등록해주세요.
