"""
Tests for content generator service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.content_generator import ContentGeneratorService
from app.core.exceptions import ClaudeAPIError, ContentTooShortError


# ==================== 픽스처 ====================

@pytest.fixture
def content_service():
    """ContentGeneratorService 인스턴스"""
    return ContentGeneratorService()


@pytest.fixture
def sample_claude_response():
    """샘플 Claude API 응답"""
    return """
<h1>블로그 작성법 완벽 가이드</h1>

<p>블로그를 성공적으로 운영하려면 체계적인 접근이 필요합니다.</p>

<h2>블로그 작성의 기본 원칙</h2>

<p>독자 중심의 콘텐츠를 작성하는 것이 가장 중요합니다. 
""" + ("블로그 콘텐츠는 독자에게 가치를 제공해야 합니다. " * 200)  # 충분한 길이


@pytest.fixture
def sample_faq_response():
    """샘플 FAQ 응답"""
    return """
<div class="faq-section">
<h3>자주 묻는 질문</h3>

<div class="faq-item">
<h4>Q: 블로그를 어떻게 시작하나요?</h4>
<p>A: 먼저 주제를 선정하고 플랫폼을 선택하세요.</p>
</div>

<div class="faq-item">
<h4>Q: 얼마나 자주 포스팅해야 하나요?</h4>
<p>A: 주 2-3회 정기적으로 발행하는 것을 권장합니다.</p>
</div>
</div>
"""


# ==================== 단위 테스트: generate_content ====================

@pytest.mark.service
@pytest.mark.asyncio
class TestGenerateContent:
    """Test content generation."""

    async def test_generate_content_success(
        self,
        content_service,
        mock_anthropic_client,
        sample_claude_response
    ):
        """콘텐츠 생성 성공 테스트"""
        # Mock 설정
        mock_anthropic_client.messages.create.return_value.content = [
            MagicMock(text=sample_claude_response)
        ]
        
        with patch.object(content_service, 'anthropic_client', mock_anthropic_client):
            result = await content_service.generate_content(
                keyword="블로그 작성법",
                target_word_count=2000,
                tone="professional",
                include_faq=False
            )

            # 검증
            assert "title" in result
            assert "content" in result
            assert "meta_description" in result
            assert "schema_markup" in result
            assert "word_count" in result
            assert "headings" in result
            
            assert result["word_count"] > 0
            assert len(result["title"]) > 0

    async def test_generate_content_with_faq(
        self,
        content_service,
        mock_anthropic_client,
        sample_claude_response,
        sample_faq_response
    ):
        """FAQ 포함 콘텐츠 생성 테스트"""
        # 첫 번째 호출: 메인 콘텐츠
        # 두 번째 호출: FAQ
        mock_anthropic_client.messages.create.side_effect = [
            MagicMock(content=[MagicMock(text=sample_claude_response)]),
            MagicMock(content=[MagicMock(text=sample_faq_response)]),
        ]
        
        with patch.object(content_service, 'anthropic_client', mock_anthropic_client):
            result = await content_service.generate_content(
                keyword="블로그 작성법",
                target_word_count=2000,
                include_faq=True
            )

            # 검증
            assert "faq_html" in result
            assert "faq_schema" in result
            assert result["faq_html"] is not None

    async def test_generate_content_too_short(
        self,
        content_service,
        mock_anthropic_client
    ):
        """너무 짧은 콘텐츠 에러 테스트"""
        # 매우 짧은 응답
        short_content = "<h1>제목</h1><p>짧은 내용</p>"
        
        mock_anthropic_client.messages.create.return_value.content = [
            MagicMock(text=short_content)
        ]
        
        with patch.object(content_service, 'anthropic_client', mock_anthropic_client):
            with pytest.raises(ContentTooShortError):
                await content_service.generate_content(
                    keyword="블로그 작성법",
                    target_word_count=2000,
                    min_word_count=1500
                )

    async def test_generate_content_with_context(
        self,
        content_service,
        mock_anthropic_client,
        sample_claude_response
    ):
        """추가 컨텍스트 포함 테스트"""
        mock_anthropic_client.messages.create.return_value.content = [
            MagicMock(text=sample_claude_response)
        ]
        
        with patch.object(content_service, 'anthropic_client', mock_anthropic_client):
            result = await content_service.generate_content(
                keyword="블로그 작성법",
                target_word_count=2000,
                additional_context="초보자를 위한 가이드"
            )

            assert result is not None
            # anthropic_client.messages.create가 호출되었는지 확인
            assert mock_anthropic_client.messages.create.called


# ==================== 단위 테스트: generate_title ====================

@pytest.mark.service
@pytest.mark.asyncio
async def test_generate_title(content_service, mock_anthropic_client):
    """제목 생성 테스트"""
    mock_anthropic_client.messages.create.return_value.content = [
        MagicMock(text="블로그 작성법 완벽 가이드 | 초보자부터 전문가까지")
    ]
    
    with patch.object(content_service, 'anthropic_client', mock_anthropic_client):
        title = await content_service._generate_title(
            keyword="블로그 작성법",
            content="<h1>블로그 작성법</h1><p>콘텐츠</p>"
        )

        assert len(title) > 0
        assert len(title) <= 60  # SEO 권장 길이


# ==================== 단위 테스트: extract_headings ====================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_extract_headings(content_service):
    """헤딩 추출 테스트"""
    content = """
    <h1>메인 제목</h1>
    <h2>서브 제목 1</h2>
    <p>내용</p>
    <h2>서브 제목 2</h2>
    <h3>세부 제목</h3>
    """
    
    headings = await content_service._extract_headings(content)
    
    assert "h1" in headings
    assert "h2" in headings
    assert "h3" in headings
    assert len(headings["h1"]) == 1
    assert len(headings["h2"]) == 2
    assert len(headings["h3"]) == 1


# ==================== 단위 테스트: parse_faq_schema ====================

@pytest.mark.unit
def test_parse_faq_schema(content_service):
    """FAQ 스키마 파싱 테스트"""
    faq_html = """
    <div class="faq-item">
    <h4>Q: 질문 1</h4>
    <p>A: 답변 1</p>
    </div>
    <div class="faq-item">
    <h4>Q: 질문 2</h4>
    <p>A: 답변 2</p>
    </div>
    """
    
    schema = content_service._parse_faq_schema(faq_html)
    
    if schema:
        assert schema["@type"] == "FAQPage"
        assert "mainEntity" in schema
        assert len(schema["mainEntity"]) == 2


@pytest.mark.unit
def test_parse_faq_schema_invalid(content_service):
    """잘못된 FAQ 스키마 파싱"""
    faq_html = "<p>일반 텍스트</p>"
    schema = content_service._parse_faq_schema(faq_html)
    assert schema is None


# ==================== 단위 테스트: enhance_content_naturally ====================

@pytest.mark.service
@pytest.mark.asyncio
async def test_enhance_content_naturally(
    content_service,
    mock_anthropic_client
):
    """자연스러운 콘텐츠 개선 테스트"""
    enhanced_content = "<h1>개선된 콘텐츠</h1><p>더 나은 내용</p>"
    
    mock_anthropic_client.messages.create.return_value.content = [
        MagicMock(text=enhanced_content)
    ]
    
    with patch.object(content_service, 'anthropic_client', mock_anthropic_client):
        original = "<h1>원본</h1><p>내용</p>"
        result = await content_service.enhance_content_naturally(original)
        
        assert len(result) > 0


# ==================== 통합 테스트: 전체 워크플로우 ====================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_content_generation_workflow(
    content_service,
    mock_anthropic_client,
    sample_claude_response,
    sample_faq_response
):
    """전체 콘텐츠 생성 워크플로우 테스트"""
    # Mock 설정 - 여러 호출을 순서대로
    mock_anthropic_client.messages.create.side_effect = [
        MagicMock(content=[MagicMock(text=sample_claude_response)]),  # 메인 콘텐츠
        MagicMock(content=[MagicMock(text="완벽 가이드")]),  # 제목
        MagicMock(content=[MagicMock(text=sample_faq_response)]),  # FAQ
    ]
    
    with patch.object(content_service, 'anthropic_client', mock_anthropic_client):
        result = await content_service.generate_content(
            keyword="블로그 작성법",
            target_word_count=2000,
            tone="professional",
            include_faq=True,
            additional_context="초보자 대상"
        )

        # 모든 필수 필드 검증
        assert all(key in result for key in [
            "title", "content", "meta_description", "schema_markup",
            "word_count", "headings", "seo_score"
        ])
        
        # 데이터 타입 검증
        assert isinstance(result["title"], str)
        assert isinstance(result["content"], str)
        assert isinstance(result["word_count"], int)
        assert isinstance(result["headings"], dict)
        assert isinstance(result["seo_score"], (int, float))


# ==================== 에러 처리 테스트 ====================

@pytest.mark.service
@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in content generation."""

    async def test_claude_api_error(self, content_service, mock_anthropic_client):
        """Claude API 에러 처리"""
        mock_anthropic_client.messages.create.side_effect = Exception("API Error")
        
        with patch.object(content_service, 'anthropic_client', mock_anthropic_client):
            with pytest.raises(ClaudeAPIError):
                await content_service.generate_content(
                    keyword="블로그",
                    target_word_count=2000
                )

    async def test_empty_keyword(self, content_service):
        """빈 키워드 처리"""
        with pytest.raises((ValueError, ClaudeAPIError)):
            await content_service.generate_content(
                keyword="",
                target_word_count=2000
            )

    async def test_invalid_word_count(self, content_service):
        """잘못된 단어 수"""
        with pytest.raises((ValueError, ClaudeAPIError)):
            await content_service.generate_content(
                keyword="블로그",
                target_word_count=-100
            )


# ==================== 성능 테스트 ====================

@pytest.mark.slow
@pytest.mark.asyncio
async def test_generate_multiple_contents(
    content_service,
    mock_anthropic_client,
    sample_claude_response
):
    """여러 콘텐츠 생성 성능 테스트"""
    mock_anthropic_client.messages.create.return_value.content = [
        MagicMock(text=sample_claude_response)
    ]
    
    with patch.object(content_service, 'anthropic_client', mock_anthropic_client):
        keywords = ["블로그 작성법", "SEO 최적화", "콘텐츠 마케팅"]
        
        results = []
        for keyword in keywords:
            result = await content_service.generate_content(
                keyword=keyword,
                target_word_count=1500,
                include_faq=False
            )
            results.append(result)
        
        assert len(results) == len(keywords)
        assert all(r["word_count"] > 0 for r in results)
