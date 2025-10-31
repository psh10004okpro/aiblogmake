"""
Image generation and optimization service.

This service handles image generation using DALL-E 3, downloading from Unsplash,
image optimization, watermarking, and alt text generation using GPT-4 Vision.
"""

import os
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import openai
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ImageGeneratorService:
    """Service for generating and optimizing images."""

    def __init__(self):
        """Initialize the image generator service."""
        self.openai_client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key
        )
        self.unsplash_base_url = "https://api.unsplash.com"
        self.temp_dir = Path("temp_images")
        self.temp_dir.mkdir(exist_ok=True)

    async def generate_dalle_image(
        self,
        prompt: str,
        is_hero: bool = True,
        style: str = "realistic"
    ) -> Dict[str, Any]:
        """
        Generate image using DALL-E 3.

        Args:
            prompt: Image generation prompt.
            is_hero: Whether this is a hero image (1792x1024) or thumbnail (1024x1024).
            style: Image style (vivid, natural, realistic).

        Returns:
            Dict[str, Any]: Image data with URL and metadata.

        Example:
            ```python
            service = ImageGeneratorService()
            image = await service.generate_dalle_image(
                prompt="블로그 SEO 최적화 개념을 나타내는 이미지",
                is_hero=True
            )
            ```
        """
        logger.info("generating_dalle_image", prompt=prompt, is_hero=is_hero)

        size = settings.dalle_size if is_hero else "1024x1024"

        try:
            response = await self.openai_client.images.generate(
                model=settings.dalle_model,
                prompt=prompt,
                size=size,
                quality=settings.dalle_quality,
                n=1
            )

            image_url = response.data[0].url

            # Download image
            local_path = await self._download_image(
                image_url,
                prefix="dalle"
            )

            # Optimize image
            optimized_path = await self.optimize_image(
                local_path,
                is_hero=is_hero
            )

            # Get image dimensions and size
            img = Image.open(optimized_path)
            width, height = img.size
            size_kb = os.path.getsize(optimized_path) // 1024

            result = {
                "url": image_url,
                "local_path": str(optimized_path),
                "width": width,
                "height": height,
                "size_kb": size_kb,
                "format": settings.image_format,
                "source": "dalle",
                "prompt": prompt,
                "is_hero": is_hero,
            }

            logger.info(
                "dalle_image_generated",
                size_kb=size_kb,
                dimensions=f"{width}x{height}"
            )

            return result

        except openai.APIError as e:
            logger.error("dalle_api_error", error=str(e), prompt=prompt)
            raise
        except Exception as e:
            logger.error("dalle_generation_error", error=str(e), prompt=prompt)
            raise

    async def search_unsplash_images(
        self,
        query: str,
        count: int = 4,
        orientation: str = "landscape"
    ) -> List[Dict[str, Any]]:
        """
        Search and download images from Unsplash.

        Args:
            query: Search query.
            count: Number of images to fetch.
            orientation: Image orientation (landscape, portrait, squarish).

        Returns:
            List[Dict[str, Any]]: List of image data.
        """
        if not settings.unsplash_access_key:
            logger.warning("unsplash_not_configured")
            return []

        logger.info("searching_unsplash", query=query, count=count)

        url = f"{self.unsplash_base_url}/search/photos"
        headers = {
            "Authorization": f"Client-ID {settings.unsplash_access_key}"
        }
        params = {
            "query": query,
            "per_page": count,
            "orientation": orientation
        }

        results = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        for photo in data.get("results", [])[:count]:
                            image_url = photo["urls"]["regular"]

                            # Download and optimize
                            local_path = await self._download_image(
                                image_url,
                                prefix="unsplash"
                            )

                            optimized_path = await self.optimize_image(
                                local_path,
                                is_hero=False
                            )

                            # Get image dimensions and size
                            img = Image.open(optimized_path)
                            width, height = img.size
                            size_kb = os.path.getsize(optimized_path) // 1024

                            result = {
                                "url": image_url,
                                "local_path": str(optimized_path),
                                "width": width,
                                "height": height,
                                "size_kb": size_kb,
                                "format": settings.image_format,
                                "source": "unsplash",
                                "source_id": photo["id"],
                                "is_hero": False,
                                "alt_text": photo.get("alt_description", ""),
                                "photographer": photo["user"]["name"],
                                "photographer_url": photo["user"]["links"]["html"],
                            }

                            results.append(result)

                        logger.info(
                            "unsplash_images_fetched",
                            count=len(results),
                            query=query
                        )
                    else:
                        logger.error(
                            "unsplash_api_error",
                            status=response.status,
                            query=query
                        )

        except Exception as e:
            logger.error("unsplash_fetch_error", error=str(e), query=query)

        return results

    async def _download_image(
        self,
        url: str,
        prefix: str = "image"
    ) -> Path:
        """
        Download image from URL.

        Args:
            url: Image URL.
            prefix: Filename prefix.

        Returns:
            Path: Path to downloaded image.
        """
        import uuid

        filename = f"{prefix}_{uuid.uuid4().hex[:8]}.jpg"
        filepath = self.temp_dir / filename

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(filepath, "wb") as f:
                        f.write(await response.read())

        logger.debug("image_downloaded", url=url, path=str(filepath))
        return filepath

    async def optimize_image(
        self,
        image_path: Path,
        is_hero: bool = False
    ) -> Path:
        """
        Optimize image: resize, convert to WebP, add watermark.

        Args:
            image_path: Path to input image.
            is_hero: Whether this is a hero image.

        Returns:
            Path: Path to optimized image.
        """
        try:
            img = Image.open(image_path)

            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Resize
            target_width = settings.image_hero_width if is_hero else settings.image_thumbnail_width
            target_height = settings.image_hero_height if is_hero else settings.image_thumbnail_height

            # Maintain aspect ratio
            img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)

            # Add watermark
            img = self._add_watermark(img)

            # Save as WebP
            output_path = image_path.with_suffix(f".{settings.image_format}")
            img.save(
                output_path,
                format=settings.image_format.upper(),
                quality=settings.image_quality,
                optimize=True
            )

            # Check size and reduce quality if needed
            size_kb = os.path.getsize(output_path) // 1024
            quality = settings.image_quality

            while size_kb > settings.image_max_size_kb and quality > 50:
                quality -= 10
                img.save(
                    output_path,
                    format=settings.image_format.upper(),
                    quality=quality,
                    optimize=True
                )
                size_kb = os.path.getsize(output_path) // 1024

            # Remove original
            if image_path != output_path:
                image_path.unlink()

            logger.debug(
                "image_optimized",
                path=str(output_path),
                size_kb=size_kb,
                quality=quality
            )

            return output_path

        except Exception as e:
            logger.error("image_optimization_error", error=str(e), path=str(image_path))
            raise

    def _add_watermark(self, img: Image.Image) -> Image.Image:
        """
        Add watermark to image.

        Args:
            img: PIL Image.

        Returns:
            Image.Image: Image with watermark.
        """
        try:
            draw = ImageDraw.Draw(img)
            width, height = img.size

            # Watermark text
            text = settings.watermark_text

            # Try to load a font, fallback to default
            try:
                font_size = max(20, width // 50)
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                font = ImageFont.load_default()

            # Get text bounding box
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Position (bottom right corner)
            x = width - text_width - 20
            y = height - text_height - 20

            # Draw text with opacity
            from PIL import Image as PILImage
            watermark = PILImage.new("RGBA", img.size, (0, 0, 0, 0))
            watermark_draw = ImageDraw.Draw(watermark)

            watermark_draw.text(
                (x, y),
                text,
                fill=(255, 255, 255, settings.watermark_opacity),
                font=font
            )

            # Composite watermark onto image
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            img = PILImage.alpha_composite(img, watermark)
            img = img.convert("RGB")

            return img

        except Exception as e:
            logger.warning("watermark_addition_failed", error=str(e))
            return img

    async def generate_alt_text(
        self,
        image_path: str,
        keyword: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Generate SEO-optimized alt text using GPT-4 Vision.

        Args:
            image_path: Path to image.
            keyword: Target keyword to include in alt text.
            context: Content context.

        Returns:
            str: Alt text (max 125 characters).
        """
        logger.info("generating_alt_text", image_path=image_path)

        try:
            # Read image and encode to base64
            with open(image_path, "rb") as f:
                image_data = f.read()

            import base64
            base64_image = base64.b64encode(image_data).decode("utf-8")

            prompt = f"""이 이미지에 대한 SEO 최적화 alt 텍스트를 작성해주세요.

요구사항:
- 최대 125자 이내 (공백 포함)
- 이미지 내용을 명확하고 간결하게 설명
- 자연스러운 한국어
{f"- 키워드 포함: {keyword}" if keyword else ""}
{f"- 콘텍스트: {context}" if context else ""}

alt 텍스트만 출력하세요 (부가 설명 없이).
"""

            response = await self.openai_client.chat.completions.create(
                model=settings.gpt_vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=100
            )

            alt_text = response.choices[0].message.content.strip()

            # Truncate to max length
            if len(alt_text) > settings.alt_text_max_length:
                alt_text = alt_text[:settings.alt_text_max_length - 3] + "..."

            logger.info("alt_text_generated", alt_text=alt_text)
            return alt_text

        except Exception as e:
            logger.error("alt_text_generation_error", error=str(e))
            # Fallback alt text
            return keyword if keyword else "블로그 이미지"

    async def generate_images_for_post(
        self,
        keyword: str,
        content: str,
        num_images: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Generate complete set of images for a blog post.

        Args:
            keyword: Target keyword.
            content: Post content.
            num_images: Total number of images (including hero).

        Returns:
            List[Dict[str, Any]]: List of image data.
        """
        logger.info(
            "generating_post_images",
            keyword=keyword,
            num_images=num_images
        )

        images = []

        # Generate hero image with DALL-E
        hero_prompt = f"Professional, high-quality illustration representing '{keyword}', modern and clean design, suitable for blog header"

        try:
            hero_image = await self.generate_dalle_image(
                prompt=hero_prompt,
                is_hero=True
            )

            # Generate alt text
            hero_image["alt_text"] = await self.generate_alt_text(
                hero_image["local_path"],
                keyword=keyword,
                context=content[:200]
            )

            images.append(hero_image)

        except Exception as e:
            logger.error("hero_image_generation_failed", error=str(e))

        # Get supporting images from Unsplash
        if num_images > 1:
            try:
                unsplash_images = await self.search_unsplash_images(
                    query=keyword,
                    count=num_images - 1
                )

                # Generate alt text for each
                for img in unsplash_images:
                    if not img.get("alt_text"):
                        img["alt_text"] = await self.generate_alt_text(
                            img["local_path"],
                            keyword=keyword
                        )

                images.extend(unsplash_images)

            except Exception as e:
                logger.error("unsplash_images_fetch_failed", error=str(e))

        logger.info(
            "post_images_generated",
            total=len(images),
            hero=1,
            supporting=len(images) - 1
        )

        return images

    async def cleanup_temp_images(self) -> None:
        """Clean up temporary images directory."""
        try:
            for file in self.temp_dir.glob("*"):
                file.unlink()
            logger.info("temp_images_cleaned")
        except Exception as e:
            logger.error("temp_cleanup_error", error=str(e))
