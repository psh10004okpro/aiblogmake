# 멀티 LLM 지원 (Multi-LLM Support)

블로그 자동화 시스템은 여러 LLM (Large Language Model) 제공자를 지원하여 유연한 콘텐츠 생성을 가능하게 합니다.

## 📋 지원하는 LLM 제공자

### 1. **Claude (Anthropic)**
- **모델**: Claude 3.5 Sonnet
- **장점**:
  - 자연스러운 한국어 생성에 최적화
  - 긴 컨텍스트 지원
  - 높은 품질의 SEO 콘텐츠
- **추천**: 한국어 블로그 콘텐츠 생성에 최적
- **API 키**: [Anthropic Console](https://console.anthropic.com/)에서 발급

### 2. **ChatGPT (OpenAI)**
- **모델**: GPT-4o, GPT-4-turbo
- **장점**:
  - 빠른 응답 속도
  - 다양한 스타일 지원
  - 안정적인 API
- **추천**: 빠른 콘텐츠 생성이 필요한 경우
- **API 키**: [OpenAI Platform](https://platform.openai.com/)에서 발급

### 3. **Gemini (Google)**
- **모델**: Gemini 1.5 Pro
- **장점**:
  - 강력한 멀티모달 기능
  - Google 생태계 통합
  - 무료 할당량 제공
- **추천**: 비용 효율적인 대량 생성
- **API 키**: [Google AI Studio](https://makersuite.google.com/)에서 발급

## 🔧 설정

### 1. 환경 변수 설정

`.env` 파일에 다음 설정을 추가하세요:

```bash
# OpenAI API (ChatGPT)
OPENAI_API_KEY=sk-your-openai-api-key-here
CHATGPT_MODEL=gpt-4o
CHATGPT_MAX_TOKENS=4000
CHATGPT_TEMPERATURE=0.7

# Anthropic API (Claude)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4000
CLAUDE_TEMPERATURE=0.7

# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-pro-latest
GEMINI_MAX_TOKENS=4000
GEMINI_TEMPERATURE=0.7

# 기본 LLM 제공자 (claude, chatgpt, gemini 중 하나)
DEFAULT_LLM_PROVIDER=claude
```

### 2. API 키 발급

#### Claude (Anthropic)
1. [Anthropic Console](https://console.anthropic.com/) 접속
2. API Keys 섹션에서 새 키 생성
3. `ANTHROPIC_API_KEY`에 설정

#### ChatGPT (OpenAI)
1. [OpenAI Platform](https://platform.openai.com/) 접속
2. API keys에서 새 키 생성
3. `OPENAI_API_KEY`에 설정
4. (선택) Organization ID 설정: `OPENAI_ORG_ID`

#### Gemini (Google)
1. [Google AI Studio](https://makersuite.google.com/) 접속
2. Get API key 클릭
3. `GEMINI_API_KEY`에 설정

## 📡 API 사용법

### 1. 사용 가능한 제공자 확인

```bash
GET /api/v1/content/llm-providers
```

**응답 예시:**
```json
{
  "default_provider": "claude",
  "providers": {
    "claude": {
      "available": true,
      "model": "claude-3-5-sonnet-20241022",
      "description": "Anthropic Claude - Best for natural Korean content"
    },
    "chatgpt": {
      "available": true,
      "model": "gpt-4o",
      "description": "OpenAI ChatGPT - Versatile and fast"
    },
    "gemini": {
      "available": false,
      "model": null,
      "description": "Google Gemini - Powerful and multilingual"
    }
  }
}
```

### 2. 콘텐츠 생성 (기본 제공자 사용)

```bash
POST /api/v1/content/generate
Content-Type: application/json

{
  "keyword": "블로그 SEO 최적화",
  "target_word_count": 2000,
  "tone": "professional",
  "include_faq": true
}
```

### 3. 콘텐츠 생성 (특정 제공자 지정)

```bash
POST /api/v1/content/generate
Content-Type: application/json

{
  "keyword": "블로그 SEO 최적화",
  "target_word_count": 2000,
  "tone": "professional",
  "llm_provider": "chatgpt",
  "include_faq": true
}
```

### 4. Python 클라이언트 예시

```python
import httpx

# 기본 제공자로 콘텐츠 생성
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/content/generate",
        json={
            "keyword": "블로그 SEO 최적화",
            "target_word_count": 2000,
            "tone": "professional"
        }
    )
    content = response.json()

# ChatGPT로 콘텐츠 생성
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/content/generate",
        json={
            "keyword": "블로그 SEO 최적화",
            "target_word_count": 2000,
            "llm_provider": "chatgpt"
        }
    )
    content = response.json()

# Gemini로 콘텐츠 생성
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/content/generate",
        json={
            "keyword": "블로그 SEO 최적화",
            "target_word_count": 2000,
            "llm_provider": "gemini"
        }
    )
    content = response.json()
```

## 💻 코드 사용법

### 1. ContentGeneratorService 직접 사용

```python
from app.services.content_generator import ContentGeneratorService

# 기본 제공자 사용
service = ContentGeneratorService()
content = await service.generate_content(
    keyword="블로그 SEO 최적화",
    target_word_count=2000
)

# Claude 사용
claude_service = ContentGeneratorService(provider="claude")
content = await claude_service.generate_content(
    keyword="블로그 SEO 최적화",
    target_word_count=2000
)

# ChatGPT 사용
chatgpt_service = ContentGeneratorService(provider="chatgpt")
content = await chatgpt_service.generate_content(
    keyword="블로그 SEO 최적화",
    target_word_count=2000
)

# Gemini 사용
gemini_service = ContentGeneratorService(provider="gemini")
content = await gemini_service.generate_content(
    keyword="블로그 SEO 최적화",
    target_word_count=2000
)
```

### 2. LLM Provider 직접 사용

```python
from app.services.llm import get_llm_provider

# 기본 제공자
provider = get_llm_provider()
response = await provider.generate(
    prompt="블로그 SEO 최적화에 대한 글을 작성해주세요.",
    max_tokens=2000,
    temperature=0.7
)
print(response.content)

# 특정 제공자 with retry
claude = get_llm_provider("claude")
response = await claude.generate_with_retry(
    prompt="블로그 SEO 최적화에 대한 글을 작성해주세요.",
    max_retries=3
)
print(f"Provider: {response.provider}")
print(f"Model: {response.model}")
print(f"Tokens used: {response.tokens_used}")
print(f"Content: {response.content}")
```

### 3. Factory 패턴 사용

```python
from app.services.llm.factory import LLMProviderFactory

# 모든 가능한 제공자 확인
available = LLMProviderFactory.list_available_providers()
print(available)  # {"claude": True, "chatgpt": True, "gemini": False}

# 제공자 생성
claude = LLMProviderFactory.create_provider("claude")
chatgpt = LLMProviderFactory.create_provider(
    "chatgpt",
    temperature=0.9,  # Override default
    max_tokens=3000   # Override default
)

# 캐시된 제공자 사용 (성능 최적화)
provider1 = LLMProviderFactory.get_cached_provider("claude")
provider2 = LLMProviderFactory.get_cached_provider("claude")  # Same instance

# 캐시 초기화
LLMProviderFactory.clear_cache()
```

## 🎯 제공자 선택 가이드

### Claude를 사용하는 경우:
- 한국어 블로그 콘텐츠 생성 (최고 품질)
- 긴 형식의 콘텐츠 (3000+ 단어)
- E-E-A-T 원칙이 중요한 SEO 콘텐츠
- 자연스럽고 인간적인 톤

### ChatGPT를 사용하는 경우:
- 빠른 응답이 필요한 경우
- 대량 콘텐츠 생성
- 다양한 스타일 실험
- 안정적인 API가 필요한 경우

### Gemini를 사용하는 경우:
- 비용 절감 (무료 할당량)
- Google 서비스와 통합
- 멀티모달 기능 활용
- 대규모 배치 작업

## 🔄 폴백 및 로드 밸런싱

### 폴백 전략

하나의 제공자가 실패하면 다른 제공자로 자동 전환:

```python
from app.services.llm import get_llm_provider

async def generate_with_fallback(prompt: str, providers: list = None):
    """폴백 전략으로 콘텐츠 생성"""
    if providers is None:
        providers = ["claude", "chatgpt", "gemini"]

    last_error = None

    for provider_name in providers:
        try:
            provider = get_llm_provider(provider_name)
            if not provider.is_available:
                continue

            response = await provider.generate_with_retry(
                prompt=prompt,
                max_retries=2
            )
            return response

        except Exception as e:
            last_error = e
            print(f"{provider_name} failed: {e}")
            continue

    raise Exception(f"All providers failed. Last error: {last_error}")

# 사용 예시
response = await generate_with_fallback("블로그 글 작성")
```

### 로드 밸런싱

여러 제공자 간 부하 분산:

```python
import random
from app.services.llm.factory import LLMProviderFactory

async def generate_with_load_balancing(prompt: str):
    """사용 가능한 제공자 중 랜덤 선택"""
    available = LLMProviderFactory.list_available_providers()
    active_providers = [p for p, avail in available.items() if avail]

    if not active_providers:
        raise ValueError("No LLM providers available")

    # 랜덤 선택
    provider_name = random.choice(active_providers)
    provider = LLMProviderFactory.create_provider(provider_name)

    return await provider.generate(prompt)
```

## 📊 비용 및 성능 비교

| 제공자 | 모델 | 비용 (1M tokens) | 평균 응답 시간 | 한국어 품질 |
|--------|------|-----------------|---------------|------------|
| Claude | claude-3-5-sonnet | $3-15 | 10-15초 | ⭐⭐⭐⭐⭐ |
| ChatGPT | gpt-4o | $2.50-10 | 5-10초 | ⭐⭐⭐⭐ |
| Gemini | gemini-1.5-pro | $0-7 | 8-12초 | ⭐⭐⭐⭐ |

*비용은 input/output 토큰에 따라 다름*

## 🐛 문제 해결

### API 키가 작동하지 않음

```bash
# 제공자 상태 확인
curl http://localhost:8000/api/v1/content/llm-providers | jq
```

### "Provider not available" 오류

1. `.env` 파일에 API 키가 설정되어 있는지 확인
2. API 키가 유효한지 확인
3. 해당 제공자의 API 사용량 제한 확인

### "Invalid LLM provider" 오류

`llm_provider` 필드는 `claude`, `chatgpt`, `gemini` 중 하나여야 합니다.

### Rate Limit 오류

모든 제공자는 자동 재시도 (exponential backoff) 기능을 내장하고 있습니다:

```python
# 최대 5번 재시도
response = await provider.generate_with_retry(
    prompt=prompt,
    max_retries=5
)
```

## 🔐 보안 모범 사례

1. **API 키 관리**
   - 환경 변수 사용 (`.env` 파일)
   - Git에 커밋하지 않기 (`.gitignore` 설정)
   - 프로덕션 환경에서는 secret manager 사용

2. **비용 모니터링**
   - 각 제공자의 대시보드에서 사용량 모니터링
   - 알림 설정 (사용량 임계값)
   - 토큰 사용량 로깅

3. **Rate Limiting**
   - 애플리케이션 레벨 rate limiting 구현
   - 동시 요청 제한
   - 큐잉 시스템 사용 (Celery)

## 📚 추가 리소스

- [Claude API Documentation](https://docs.anthropic.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [LLM Provider 구현 가이드](./LLM_PROVIDER_IMPLEMENTATION.md) (개발자용)

---

**문의**: LLM 제공자 관련 질문이 있으시면 이슈를 등록해주세요.
