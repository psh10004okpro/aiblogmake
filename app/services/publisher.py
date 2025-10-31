"""
WordPress publishing service.

This service handles publishing blog posts to WordPress via REST API,
including uploading images, setting categories/tags, and scheduling posts.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import base64
from pathlib import Path
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WordPressPublisher:
    """Service for publishing content to WordPress."""

    def __init__(self):
        """Initialize the WordPress publisher."""
        self.api_url = f"{settings.wp_url}/wp-json/wp/v2"
        self.auth_header = self._generate_auth_header()

    def _generate_auth_header(self) -> Dict[str, str]:
        """
        Generate WordPress REST API authentication header.

        Returns:
            Dict[str, str]: Authorization header.
        """
        credentials = f"{settings.wp_username}:{settings.wp_app_password}"
        token = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {token}"}

    async def test_connection(self) -> bool:
        """
        Test WordPress API connection.

        Returns:
            bool: True if connection successful.
        """
        logger.info("testing_wordpress_connection")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{settings.wp_url}/wp-json",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(
                            "wordpress_connection_successful",
                            site_name=data.get("name")
                        )
                        return True

        except Exception as e:
            logger.error("wordpress_connection_failed", error=str(e))

        return False

    async def upload_image(
        self,
        image_path: str,
        alt_text: str = "",
        caption: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Upload image to WordPress media library.

        Args:
            image_path: Path to image file.
            alt_text: Image alt text.
            caption: Image caption.

        Returns:
            Optional[Dict[str, Any]]: Uploaded media data or None.

        Example:
            ```python
            publisher = WordPressPublisher()
            media = await publisher.upload_image(
                "path/to/image.jpg",
                alt_text="SEO optimized alt text"
            )
            print(media['id'])  # WordPress media ID
            ```
        """
        logger.info("uploading_image_to_wordpress", path=image_path)

        url = f"{self.api_url}/media"
        path = Path(image_path)

        if not path.exists():
            logger.error("image_file_not_found", path=image_path)
            return None

        try:
            # Read image file
            with open(path, "rb") as f:
                image_data = f.read()

            headers = {
                **self.auth_header,
                "Content-Disposition": f'attachment; filename="{path.name}"',
                "Content-Type": "image/webp" if path.suffix == ".webp" else "image/jpeg",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    data=image_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=settings.wp_api_timeout)
                ) as response:
                    if response.status in (200, 201):
                        media_data = await response.json()

                        # Update alt text if provided
                        if alt_text:
                            await self._update_media_alt_text(
                                media_data["id"],
                                alt_text
                            )

                        logger.info(
                            "image_uploaded",
                            media_id=media_data["id"],
                            url=media_data["source_url"]
                        )

                        return {
                            "id": media_data["id"],
                            "url": media_data["source_url"],
                            "alt_text": alt_text,
                        }
                    else:
                        error_text = await response.text()
                        logger.error(
                            "image_upload_failed",
                            status=response.status,
                            error=error_text
                        )

        except Exception as e:
            logger.error("image_upload_error", error=str(e), path=image_path)

        return None

    async def _update_media_alt_text(
        self,
        media_id: int,
        alt_text: str
    ) -> bool:
        """
        Update media alt text.

        Args:
            media_id: WordPress media ID.
            alt_text: Alt text.

        Returns:
            bool: Success status.
        """
        url = f"{self.api_url}/media/{media_id}"

        payload = {
            "alt_text": alt_text
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=self.auth_header,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status in (200, 201)

        except Exception as e:
            logger.error("alt_text_update_error", error=str(e), media_id=media_id)
            return False

    async def get_or_create_category(self, category_name: str) -> Optional[int]:
        """
        Get or create a category by name.

        Args:
            category_name: Category name.

        Returns:
            Optional[int]: Category ID or None.
        """
        # Check if category exists
        url = f"{self.api_url}/categories"

        try:
            async with aiohttp.ClientSession() as session:
                # Search for existing category
                async with session.get(
                    url,
                    params={"search": category_name},
                    headers=self.auth_header,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        categories = await response.json()
                        for cat in categories:
                            if cat["name"].lower() == category_name.lower():
                                logger.info(
                                    "category_found",
                                    name=category_name,
                                    id=cat["id"]
                                )
                                return cat["id"]

                # Create new category
                async with session.post(
                    url,
                    json={"name": category_name},
                    headers=self.auth_header,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in (200, 201):
                        cat_data = await response.json()
                        logger.info(
                            "category_created",
                            name=category_name,
                            id=cat_data["id"]
                        )
                        return cat_data["id"]

        except Exception as e:
            logger.error("category_operation_error", error=str(e), name=category_name)

        return None

    async def get_or_create_tag(self, tag_name: str) -> Optional[int]:
        """
        Get or create a tag by name.

        Args:
            tag_name: Tag name.

        Returns:
            Optional[int]: Tag ID or None.
        """
        url = f"{self.api_url}/tags"

        try:
            async with aiohttp.ClientSession() as session:
                # Search for existing tag
                async with session.get(
                    url,
                    params={"search": tag_name},
                    headers=self.auth_header,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        tags = await response.json()
                        for tag in tags:
                            if tag["name"].lower() == tag_name.lower():
                                return tag["id"]

                # Create new tag
                async with session.post(
                    url,
                    json={"name": tag_name},
                    headers=self.auth_header,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in (200, 201):
                        tag_data = await response.json()
                        return tag_data["id"]

        except Exception as e:
            logger.error("tag_operation_error", error=str(e), name=tag_name)

        return None

    async def create_post(
        self,
        title: str,
        content: str,
        status: str = "draft",
        categories: List[str] = None,
        tags: List[str] = None,
        featured_image_id: Optional[int] = None,
        excerpt: Optional[str] = None,
        scheduled_date: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a WordPress post.

        Args:
            title: Post title.
            content: Post content (HTML).
            status: Post status (draft, publish, future).
            categories: List of category names.
            tags: List of tag names.
            featured_image_id: WordPress media ID for featured image.
            excerpt: Post excerpt.
            scheduled_date: Scheduled publication date (for status=future).

        Returns:
            Optional[Dict[str, Any]]: Created post data or None.

        Example:
            ```python
            publisher = WordPressPublisher()
            post = await publisher.create_post(
                title="SEO 최적화 가이드",
                content="<h1>...</h1><p>...</p>",
                status="publish",
                categories=["SEO", "블로그"],
                tags=["키워드", "최적화"]
            )
            ```
        """
        logger.info("creating_wordpress_post", title=title, status=status)

        url = f"{self.api_url}/posts"

        # Get category IDs
        category_ids = []
        if categories:
            for cat_name in categories:
                cat_id = await self.get_or_create_category(cat_name)
                if cat_id:
                    category_ids.append(cat_id)

        # Get tag IDs
        tag_ids = []
        if tags:
            for tag_name in tags:
                tag_id = await self.get_or_create_tag(tag_name)
                if tag_id:
                    tag_ids.append(tag_id)

        # Prepare payload
        payload = {
            "title": title,
            "content": content,
            "status": status,
        }

        if category_ids:
            payload["categories"] = category_ids

        if tag_ids:
            payload["tags"] = tag_ids

        if featured_image_id:
            payload["featured_media"] = featured_image_id

        if excerpt:
            payload["excerpt"] = excerpt

        if scheduled_date and status == "future":
            payload["date"] = scheduled_date.isoformat()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=self.auth_header,
                    timeout=aiohttp.ClientTimeout(total=settings.wp_api_timeout)
                ) as response:
                    if response.status in (200, 201):
                        post_data = await response.json()

                        logger.info(
                            "post_created",
                            post_id=post_data["id"],
                            status=post_data["status"],
                            url=post_data["link"]
                        )

                        return {
                            "id": post_data["id"],
                            "url": post_data["link"],
                            "status": post_data["status"],
                            "date": post_data.get("date"),
                        }
                    else:
                        error_text = await response.text()
                        logger.error(
                            "post_creation_failed",
                            status=response.status,
                            error=error_text
                        )

        except Exception as e:
            logger.error("post_creation_error", error=str(e), title=title)

        return None

    async def update_post(
        self,
        post_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Update an existing WordPress post.

        Args:
            post_id: WordPress post ID.
            title: New title.
            content: New content.
            status: New status.
            categories: New categories.
            tags: New tags.

        Returns:
            bool: Success status.
        """
        logger.info("updating_wordpress_post", post_id=post_id)

        url = f"{self.api_url}/posts/{post_id}"
        payload = {}

        if title:
            payload["title"] = title

        if content:
            payload["content"] = content

        if status:
            payload["status"] = status

        if categories:
            category_ids = []
            for cat_name in categories:
                cat_id = await self.get_or_create_category(cat_name)
                if cat_id:
                    category_ids.append(cat_id)
            payload["categories"] = category_ids

        if tags:
            tag_ids = []
            for tag_name in tags:
                tag_id = await self.get_or_create_tag(tag_name)
                if tag_id:
                    tag_ids.append(tag_id)
            payload["tags"] = tag_ids

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=self.auth_header,
                    timeout=aiohttp.ClientTimeout(total=settings.wp_api_timeout)
                ) as response:
                    if response.status == 200:
                        logger.info("post_updated", post_id=post_id)
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(
                            "post_update_failed",
                            status=response.status,
                            error=error_text
                        )

        except Exception as e:
            logger.error("post_update_error", error=str(e), post_id=post_id)

        return False

    async def delete_post(self, post_id: int, force: bool = False) -> bool:
        """
        Delete a WordPress post.

        Args:
            post_id: WordPress post ID.
            force: Bypass trash and permanently delete.

        Returns:
            bool: Success status.
        """
        logger.info("deleting_wordpress_post", post_id=post_id, force=force)

        url = f"{self.api_url}/posts/{post_id}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    url,
                    params={"force": force},
                    headers=self.auth_header,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("post_deleted", post_id=post_id)
                        return True

        except Exception as e:
            logger.error("post_deletion_error", error=str(e), post_id=post_id)

        return False
