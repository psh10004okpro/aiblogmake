"""
Web scraping utilities using Playwright.

This module provides functions for scraping Naver autocomplete suggestions
and other web scraping tasks.
"""

import asyncio
import random
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NaverAutocompleteScraper:
    """Scraper for Naver search autocomplete suggestions."""

    def __init__(self):
        """Initialize the scraper."""
        self.browser: Optional[Browser] = None
        self.base_url = "https://search.naver.com/search.naver"

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self) -> None:
        """Start the browser."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=settings.playwright_headless
        )
        logger.info("browser_started", headless=settings.playwright_headless)

    async def close(self) -> None:
        """Close the browser."""
        if self.browser:
            await self.browser.close()
            logger.info("browser_closed")

    async def _random_delay(self) -> None:
        """Add random delay to avoid detection."""
        delay = random.uniform(
            settings.scraping_delay_min,
            settings.scraping_delay_max
        )
        await asyncio.sleep(delay)

    async def get_autocomplete_suggestions(
        self,
        keyword: str,
        max_suggestions: int = 10
    ) -> List[str]:
        """
        Get Naver autocomplete suggestions for a keyword.

        Args:
            keyword: The seed keyword to search for.
            max_suggestions: Maximum number of suggestions to return.

        Returns:
            List[str]: List of autocomplete suggestions.

        Example:
            ```python
            async with NaverAutocompleteScraper() as scraper:
                suggestions = await scraper.get_autocomplete_suggestions("블로그")
                print(suggestions)
            ```
        """
        if not self.browser:
            await self.start()

        suggestions = []

        try:
            page = await self.browser.new_page(
                user_agent=settings.user_agent
            )

            # Navigate to Naver search
            await page.goto(self.base_url, timeout=settings.playwright_timeout)
            logger.info("navigated_to_naver", keyword=keyword)

            # Type keyword into search box
            search_input = await page.wait_for_selector(
                "input.search_input",
                timeout=settings.playwright_timeout
            )
            await search_input.fill(keyword)

            # Wait for autocomplete dropdown
            await self._random_delay()

            # Try to get autocomplete suggestions
            try:
                autocomplete_items = await page.query_selector_all(
                    "ul.lst_relate li a"
                )

                for item in autocomplete_items[:max_suggestions]:
                    text = await item.inner_text()
                    if text and text.strip():
                        suggestions.append(text.strip())

                logger.info(
                    "autocomplete_scraped",
                    keyword=keyword,
                    count=len(suggestions)
                )

            except PlaywrightTimeout:
                logger.warning(
                    "autocomplete_timeout",
                    keyword=keyword
                )

            await page.close()

        except Exception as e:
            logger.error(
                "autocomplete_scraping_error",
                keyword=keyword,
                error=str(e)
            )

        return suggestions

    async def get_related_searches(self, keyword: str) -> List[str]:
        """
        Get Naver related searches for a keyword.

        Args:
            keyword: The keyword to search for.

        Returns:
            List[str]: List of related search terms.
        """
        if not self.browser:
            await self.start()

        related_searches = []

        try:
            page = await self.browser.new_page(
                user_agent=settings.user_agent
            )

            # Navigate to Naver search with keyword
            url = f"{self.base_url}?query={keyword}"
            await page.goto(url, timeout=settings.playwright_timeout)

            await self._random_delay()

            # Get related searches
            try:
                related_items = await page.query_selector_all(
                    ".related_srch a"
                )

                for item in related_items:
                    text = await item.inner_text()
                    if text and text.strip():
                        related_searches.append(text.strip())

                logger.info(
                    "related_searches_scraped",
                    keyword=keyword,
                    count=len(related_searches)
                )

            except PlaywrightTimeout:
                logger.warning(
                    "related_searches_timeout",
                    keyword=keyword
                )

            await page.close()

        except Exception as e:
            logger.error(
                "related_searches_error",
                keyword=keyword,
                error=str(e)
            )

        return related_searches


async def scrape_naver_autocomplete(
    keywords: List[str],
    max_suggestions_per_keyword: int = 10
) -> Dict[str, List[str]]:
    """
    Scrape Naver autocomplete suggestions for multiple keywords.

    Args:
        keywords: List of seed keywords.
        max_suggestions_per_keyword: Maximum suggestions per keyword.

    Returns:
        Dict[str, List[str]]: Dictionary mapping keywords to their suggestions.

    Example:
        ```python
        results = await scrape_naver_autocomplete(["블로그", "SEO"])
        print(results)
        # {'블로그': ['블로그 만들기', '블로그 시작'], 'SEO': ['SEO 최적화', ...]}
        ```
    """
    results: Dict[str, List[str]] = {}

    async with NaverAutocompleteScraper() as scraper:
        for keyword in keywords:
            try:
                suggestions = await scraper.get_autocomplete_suggestions(
                    keyword,
                    max_suggestions=max_suggestions_per_keyword
                )
                results[keyword] = suggestions

                # Random delay between keywords
                await scraper._random_delay()

            except Exception as e:
                logger.error(
                    "keyword_scraping_failed",
                    keyword=keyword,
                    error=str(e)
                )
                results[keyword] = []

    return results


async def scrape_webpage_content(url: str) -> Dict[str, Any]:
    """
    Scrape content from a webpage.

    Args:
        url: The URL to scrape.

    Returns:
        Dict[str, Any]: Dictionary containing title, content, and metadata.
    """
    result = {
        "url": url,
        "title": "",
        "content": "",
        "meta_description": "",
        "h1_tags": [],
        "h2_tags": [],
        "images": [],
        "links": [],
        "success": False,
        "error": None,
    }

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.playwright_headless
            )
            page = await browser.new_page(
                user_agent=settings.user_agent
            )

            await page.goto(url, timeout=settings.playwright_timeout)

            # Extract title
            result["title"] = await page.title()

            # Extract meta description
            meta_desc = await page.query_selector('meta[name="description"]')
            if meta_desc:
                result["meta_description"] = await meta_desc.get_attribute("content") or ""

            # Extract headings
            h1_elements = await page.query_selector_all("h1")
            result["h1_tags"] = [
                await elem.inner_text() for elem in h1_elements
            ]

            h2_elements = await page.query_selector_all("h2")
            result["h2_tags"] = [
                await elem.inner_text() for elem in h2_elements
            ]

            # Extract main content
            content_element = await page.query_selector("article, main, .content")
            if content_element:
                result["content"] = await content_element.inner_text()

            # Extract images
            images = await page.query_selector_all("img")
            for img in images[:10]:  # Limit to 10 images
                src = await img.get_attribute("src")
                alt = await img.get_attribute("alt")
                if src:
                    result["images"].append({"src": src, "alt": alt or ""})

            # Extract links
            links = await page.query_selector_all("a")
            for link in links[:20]:  # Limit to 20 links
                href = await link.get_attribute("href")
                text = await link.inner_text()
                if href:
                    result["links"].append({"href": href, "text": text})

            result["success"] = True
            logger.info("webpage_scraped", url=url)

            await browser.close()

    except Exception as e:
        result["error"] = str(e)
        logger.error("webpage_scraping_error", url=url, error=str(e))

    return result
