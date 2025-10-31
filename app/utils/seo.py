"""
SEO utilities for content optimization and schema markup generation.

This module provides functions for SEO optimization, schema markup,
and content analysis following 2025 Google SEO best practices.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re
from slugify import slugify
from bs4 import BeautifulSoup
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_slug(text: str, max_length: int = 60) -> str:
    """
    Generate SEO-friendly URL slug from text.

    Args:
        text: The text to slugify.
        max_length: Maximum length of the slug.

    Returns:
        str: URL-safe slug.

    Example:
        ```python
        slug = generate_slug("한글 블로그 포스트 제목")
        print(slug)  # "hangul-beulrogeu-poseuteu-jemog"
        ```
    """
    slug = slugify(
        text,
        max_length=max_length,
        word_boundary=True,
        separator="-"
    )
    logger.debug("slug_generated", original=text, slug=slug)
    return slug


def generate_meta_description(content: str, max_length: int = 160) -> str:
    """
    Generate meta description from content.

    Args:
        content: The content text.
        max_length: Maximum length (default 160 chars for Google).

    Returns:
        str: Meta description.
    """
    # Remove HTML tags
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text()

    # Clean whitespace
    text = " ".join(text.split())

    # Truncate to max length, breaking at word boundary
    if len(text) <= max_length:
        return text

    truncated = text[:max_length].rsplit(" ", 1)[0]
    return truncated + "..."


def count_words(text: str) -> int:
    """
    Count words in text (Korean-aware).

    Args:
        text: The text to count.

    Returns:
        int: Word count.
    """
    # Remove HTML tags
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text()

    # For Korean, count characters / 2 as approximate word count
    # For English/mixed, count spaces
    korean_chars = len(re.findall(r"[가-힣]", text))
    other_words = len(re.findall(r"\b\w+\b", text))

    # Approximate: Korean chars / 2 + other words
    return (korean_chars // 2) + other_words


def estimate_reading_time(word_count: int, wpm: int = 200) -> int:
    """
    Estimate reading time in minutes.

    Args:
        word_count: Number of words.
        wpm: Words per minute (default 200 for Korean).

    Returns:
        int: Estimated reading time in minutes.
    """
    return max(1, round(word_count / wpm))


def extract_headings(html_content: str) -> Dict[str, List[str]]:
    """
    Extract all headings from HTML content.

    Args:
        html_content: HTML content.

    Returns:
        Dict[str, List[str]]: Dictionary with h1, h2, h3 tags.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    headings = {
        "h1": [h.get_text().strip() for h in soup.find_all("h1")],
        "h2": [h.get_text().strip() for h in soup.find_all("h2")],
        "h3": [h.get_text().strip() for h in soup.find_all("h3")],
    }

    return headings


def validate_seo_content(
    title: str,
    content: str,
    meta_description: str,
    keyword: str
) -> Dict[str, Any]:
    """
    Validate content against SEO best practices.

    Args:
        title: The post title.
        content: The post content (HTML).
        meta_description: Meta description.
        keyword: Target keyword.

    Returns:
        Dict[str, Any]: Validation results with score and issues.
    """
    issues = []
    score = 100
    warnings = []

    # Check title
    if not keyword.lower() in title.lower():
        issues.append("Title does not contain target keyword")
        score -= 20
    if len(title) < 30 or len(title) > 60:
        warnings.append(f"Title length ({len(title)}) should be 30-60 characters")
        score -= 5

    # Check meta description
    if len(meta_description) > settings.meta_description_length:
        issues.append(f"Meta description too long ({len(meta_description)} > {settings.meta_description_length})")
        score -= 10
    if not keyword.lower() in meta_description.lower():
        warnings.append("Meta description does not contain target keyword")
        score -= 5

    # Check content
    word_count = count_words(content)
    if word_count < settings.min_content_length:
        issues.append(f"Content too short ({word_count} < {settings.min_content_length} words)")
        score -= 20
    elif word_count > settings.max_content_length:
        warnings.append(f"Content very long ({word_count} > {settings.max_content_length} words)")

    # Check headings
    headings = extract_headings(content)
    if len(headings["h1"]) == 0:
        issues.append("No H1 tag found")
        score -= 15
    elif len(headings["h1"]) > 1:
        issues.append(f"Multiple H1 tags found ({len(headings['h1'])})")
        score -= 10

    if len(headings["h2"]) < 2:
        warnings.append("Less than 2 H2 tags (recommend 3-5)")
        score -= 5

    # Check images
    soup = BeautifulSoup(content, "html.parser")
    images = soup.find_all("img")
    if len(images) < settings.min_images_per_post:
        warnings.append(f"Only {len(images)} images (recommend {settings.min_images_per_post}+)")
        score -= 5

    # Check alt tags
    images_without_alt = [img for img in images if not img.get("alt")]
    if images_without_alt:
        issues.append(f"{len(images_without_alt)} images missing alt text")
        score -= 10

    # Check internal links
    internal_links = [
        a for a in soup.find_all("a")
        if a.get("href") and not a.get("href").startswith(("http://", "https://"))
    ]
    if len(internal_links) < settings.internal_links_min:
        warnings.append(f"Only {len(internal_links)} internal links (recommend {settings.internal_links_min}+)")
        score -= 5

    result = {
        "score": max(0, score),
        "passed": score >= 70,
        "issues": issues,
        "warnings": warnings,
        "metrics": {
            "word_count": word_count,
            "title_length": len(title),
            "meta_description_length": len(meta_description),
            "h1_count": len(headings["h1"]),
            "h2_count": len(headings["h2"]),
            "h3_count": len(headings["h3"]),
            "image_count": len(images),
            "images_with_alt": len(images) - len(images_without_alt),
            "internal_links": len(internal_links),
        }
    }

    logger.info("seo_validation_completed", score=score, passed=result["passed"])
    return result


def generate_blog_posting_schema(
    title: str,
    description: str,
    content: str,
    author_name: str,
    published_date: datetime,
    modified_date: Optional[datetime] = None,
    image_url: Optional[str] = None,
    url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate BlogPosting schema markup (JSON-LD).

    Args:
        title: Post title.
        description: Post description.
        content: Post content (text).
        author_name: Author name.
        published_date: Publication date.
        modified_date: Last modified date.
        image_url: Featured image URL.
        url: Post URL.

    Returns:
        Dict[str, Any]: BlogPosting schema markup.

    Example:
        ```python
        schema = generate_blog_posting_schema(
            title="SEO 최적화 가이드",
            description="2025 SEO 최적화 방법",
            content="...",
            author_name="John Doe",
            published_date=datetime.now(),
            image_url="https://example.com/image.jpg",
            url="https://example.com/seo-guide"
        )
        ```
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": description,
        "articleBody": content,
        "author": {
            "@type": "Person",
            "name": author_name
        },
        "datePublished": published_date.isoformat(),
        "dateModified": (modified_date or published_date).isoformat(),
    }

    if image_url:
        schema["image"] = {
            "@type": "ImageObject",
            "url": image_url
        }

    if url:
        schema["url"] = url
        schema["mainEntityOfPage"] = {
            "@type": "WebPage",
            "@id": url
        }

    return schema


def generate_faq_schema(faqs: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Generate FAQPage schema markup (JSON-LD).

    Args:
        faqs: List of FAQ dictionaries with 'question' and 'answer' keys.

    Returns:
        Dict[str, Any]: FAQPage schema markup.

    Example:
        ```python
        schema = generate_faq_schema([
            {"question": "SEO란 무엇인가요?", "answer": "검색엔진 최적화..."},
            {"question": "키워드는 어떻게 선정하나요?", "answer": "..."}
        ])
        ```
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": []
    }

    for faq in faqs:
        schema["mainEntity"].append({
            "@type": "Question",
            "name": faq["question"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": faq["answer"]
            }
        })

    return schema


def generate_breadcrumb_schema(items: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Generate BreadcrumbList schema markup.

    Args:
        items: List of breadcrumb items with 'name' and 'url' keys.

    Returns:
        Dict[str, Any]: BreadcrumbList schema markup.

    Example:
        ```python
        schema = generate_breadcrumb_schema([
            {"name": "홈", "url": "https://example.com"},
            {"name": "블로그", "url": "https://example.com/blog"},
            {"name": "SEO", "url": "https://example.com/blog/seo"}
        ])
        ```
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": []
    }

    for i, item in enumerate(items, 1):
        schema["itemListElement"].append({
            "@type": "ListItem",
            "position": i,
            "name": item["name"],
            "item": item["url"]
        })

    return schema


def generate_open_graph_tags(
    title: str,
    description: str,
    url: str,
    image_url: Optional[str] = None,
    site_name: Optional[str] = None,
    article_published_time: Optional[datetime] = None,
    article_author: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate Open Graph meta tags for social sharing.

    Args:
        title: Page title.
        description: Page description.
        url: Page URL.
        image_url: Image URL.
        site_name: Site name.
        article_published_time: Publication time.
        article_author: Author name.

    Returns:
        Dict[str, str]: Dictionary of OG tags.
    """
    tags = {
        "og:type": "article",
        "og:title": title,
        "og:description": description,
        "og:url": url,
    }

    if image_url:
        tags["og:image"] = image_url

    if site_name:
        tags["og:site_name"] = site_name

    if article_published_time:
        tags["article:published_time"] = article_published_time.isoformat()

    if article_author:
        tags["article:author"] = article_author

    return tags


def generate_twitter_card_tags(
    title: str,
    description: str,
    image_url: Optional[str] = None,
    card_type: str = "summary_large_image"
) -> Dict[str, str]:
    """
    Generate Twitter Card meta tags.

    Args:
        title: Card title.
        description: Card description.
        image_url: Image URL.
        card_type: Card type (summary, summary_large_image, etc.).

    Returns:
        Dict[str, str]: Dictionary of Twitter Card tags.
    """
    tags = {
        "twitter:card": card_type,
        "twitter:title": title,
        "twitter:description": description,
    }

    if image_url:
        tags["twitter:image"] = image_url

    return tags
