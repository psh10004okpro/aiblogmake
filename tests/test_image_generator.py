"""
Tests for image generator service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path
from PIL import Image
from io import BytesIO

from app.services.image_generator import ImageGeneratorService
from app.core.exceptions import DalleAPIError, UnsplashAPIError, ImageOptimizationError


# ==================== 픽스처 ====================

@pytest.fixture
def image_service():
    """ImageGeneratorService 인스턴스"""
    return ImageGeneratorService()


@pytest.fixture
def sample_image():
    """샘플 이미지 생성"""
    img = Image.new('RGB', (1792, 1024), color='blue')
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


# ==================== 단위 테스트: DALL-E ====================

@pytest.mark.service
@pytest.mark.external
@pytest.mark.asyncio
class TestDalleImageGeneration:
    """Test DALL-E image generation."""

    async def test_generate_dalle_image_success(
        self,
        image_service,
        mock_openai_client,
        sample_image,
        tmp_path
    ):
        """DALL-E 이미지 생성 성공"""
        # Mock 설정
        image_url = "https://example.com/test-image.png"
        mock_openai_client.images.generate.return_value.data = [
            MagicMock(url=image_url)
        ]
        
        with patch.object(image_service, 'openai_client', mock_openai_client), \
             patch('aiohttp.ClientSession') as mock_session, \
             patch.object(image_service, 'images_dir', tmp_path):
            
            # Download mock
            mock_response = AsyncMock()
            mock_response.read = AsyncMock(return_value=sample_image.read())
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            result = await image_service.generate_dalle_image(
                prompt="블로그 헤더 이미지",
                is_hero=True
            )
            
            assert "url" in result
            assert "local_path" in result
            assert result["url"] == image_url

    async def test_generate_dalle_image_api_error(
        self,
        image_service,
        mock_openai_client
    ):
        """DALL-E API 에러 처리"""
        mock_openai_client.images.generate.side_effect = Exception("API Error")
        
        with patch.object(image_service, 'openai_client', mock_openai_client):
            with pytest.raises(DalleAPIError):
                await image_service.generate_dalle_image(
                    prompt="테스트",
                    is_hero=True
                )


# ==================== 단위 테스트: Unsplash ====================

@pytest.mark.service
@pytest.mark.external
@pytest.mark.asyncio
class TestUnsplashImageSearch:
    """Test Unsplash image search."""

    async def test_search_unsplash_images_success(self, image_service):
        """Unsplash 이미지 검색 성공"""
        mock_response_data = {
            "results": [
                {
                    "urls": {"regular": "https://example.com/image1.jpg"},
                    "alt_description": "테스트 이미지 1",
                    "user": {"name": "작가1"},
                    "width": 1920,
                    "height": 1080,
                },
                {
                    "urls": {"regular": "https://example.com/image2.jpg"},
                    "alt_description": "테스트 이미지 2",
                    "user": {"name": "작가2"},
                    "width": 1920,
                    "height": 1080,
                }
            ]
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            results = await image_service.search_unsplash_images(
                query="블로그",
                count=2
            )
            
            assert len(results) == 2
            assert all("url" in r for r in results)
            assert all("alt_text" in r for r in results)

    async def test_search_unsplash_images_no_results(self, image_service):
        """Unsplash 검색 결과 없음"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"results": []})
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            results = await image_service.search_unsplash_images(
                query="존재하지않는검색어",
                count=5
            )
            
            assert results == []


# ==================== 단위 테스트: 이미지 최적화 ====================

@pytest.mark.unit
@pytest.mark.asyncio
class TestImageOptimization:
    """Test image optimization."""

    async def test_optimize_image_hero(self, image_service, tmp_path):
        """히어로 이미지 최적화"""
        # 테스트 이미지 생성
        test_img = Image.new('RGB', (2000, 1500), color='red')
        test_path = tmp_path / "test.png"
        test_img.save(test_path)
        
        optimized_path = await image_service.optimize_image(
            str(test_path),
            is_hero=True
        )
        
        assert optimized_path.exists()
        assert optimized_path.suffix == '.webp'
        
        # 크기 확인
        optimized_img = Image.open(optimized_path)
        assert optimized_img.width <= 1792
        assert optimized_img.height <= 1024

    async def test_optimize_image_supporting(self, image_service, tmp_path):
        """서포팅 이미지 최적화"""
        test_img = Image.new('RGB', (1500, 1000), color='green')
        test_path = tmp_path / "test.png"
        test_img.save(test_path)
        
        optimized_path = await image_service.optimize_image(
            str(test_path),
            is_hero=False
        )
        
        optimized_img = Image.open(optimized_path)
        assert optimized_img.width <= 1200
        assert optimized_img.height <= 800

    async def test_optimize_image_file_size(self, image_service, tmp_path):
        """이미지 파일 크기 확인"""
        test_img = Image.new('RGB', (1792, 1024), color='blue')
        test_path = tmp_path / "test.png"
        test_img.save(test_path)
        
        optimized_path = await image_service.optimize_image(
            str(test_path),
            is_hero=True
        )
        
        # WebP로 변환 후 크기가 줄어들어야 함
        file_size = optimized_path.stat().st_size
        assert file_size < 200 * 1024  # 200KB 이하


# ==================== 단위 테스트: Alt Text 생성 ====================

@pytest.mark.service
@pytest.mark.asyncio
async def test_generate_alt_text(
    image_service,
    mock_openai_client,
    tmp_path
):
    """Alt text 생성 테스트"""
    # Mock GPT-4 Vision 응답
    mock_openai_client.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="블로그 작성 중인 사람의 손과 노트북"))
    ]
    
    # 테스트 이미지
    test_img = Image.new('RGB', (800, 600), color='white')
    test_path = tmp_path / "test.jpg"
    test_img.save(test_path)
    
    with patch.object(image_service, 'openai_client', mock_openai_client):
        alt_text = await image_service.generate_alt_text(
            str(test_path),
            context="블로그 작성법"
        )
        
        assert len(alt_text) > 0
        assert len(alt_text) <= 125  # SEO 권장 길이


# ==================== 통합 테스트 ====================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_image_generation_workflow(
    image_service,
    mock_openai_client,
    sample_image,
    tmp_path
):
    """전체 이미지 생성 워크플로우"""
    with patch.object(image_service, 'openai_client', mock_openai_client), \
         patch.object(image_service, 'images_dir', tmp_path), \
         patch('aiohttp.ClientSession') as mock_session:
        
        # DALL-E mock
        mock_openai_client.images.generate.return_value.data = [
            MagicMock(url="https://example.com/test.png")
        ]
        
        # Download mock
        mock_response = AsyncMock()
        mock_response.read = AsyncMock(return_value=sample_image.read())
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        # Alt text mock
        mock_openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="테스트 이미지"))
        ]
        
        # 1. 이미지 생성
        result = await image_service.generate_dalle_image(
            prompt="블로그 헤더",
            is_hero=True
        )
        
        assert "local_path" in result
