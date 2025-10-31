"""
AdSense ad insertion service.

This service automatically inserts Google AdSense ads into blog content
following best practices for ad density and placement.
"""

from typing import Dict, Any, List
from bs4 import BeautifulSoup, Tag
from app.core.config import settings
from app.utils.logger import get_logger
from app.utils.seo import count_words

logger = get_logger(__name__)


class AdInserterService:
    """Service for inserting AdSense ads into content."""

    def __init__(self):
        """Initialize the ad inserter service."""
        pass

    def generate_ad_code(
        self,
        ad_slot: str,
        ad_format: str = "auto",
        full_width_responsive: bool = True
    ) -> str:
        """
        Generate AdSense ad code.

        Args:
            ad_slot: AdSense ad slot ID.
            ad_format: Ad format (auto, rectangle, etc.).
            full_width_responsive: Enable full-width responsive ads.

        Returns:
            str: HTML ad code.
        """
        ad_html = f'''
<div class="adsense-container" style="text-align: center; margin: 20px 0;">
    <ins class="adsbygoogle"
         style="display:block"
         data-ad-client="{settings.adsense_client_id}"
         data-ad-slot="{ad_slot}"
         data-ad-format="{ad_format}"
         {'data-full-width-responsive="true"' if full_width_responsive else ''}></ins>
    <script>
         (adsbygoogle = window.adsbygoogle || []).push({{}});
    </script>
</div>
'''
        return ad_html.strip()

    def calculate_ad_placements(
        self,
        content: str,
        max_ads: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Calculate optimal ad placements based on content.

        Rule: 1 ad per 500 words, maximum 3-4 ads per post.

        Args:
            content: HTML content.
            max_ads: Maximum number of ads.

        Returns:
            List[Dict[str, Any]]: Ad placement positions.
        """
        word_count = count_words(content)

        # Calculate number of ads (1 per 500 words)
        num_ads = min(max_ads, max(1, word_count // 500))

        soup = BeautifulSoup(content, "html.parser")
        paragraphs = soup.find_all("p")

        if len(paragraphs) < 3:
            logger.warning("insufficient_paragraphs_for_ads", count=len(paragraphs))
            return []

        placements = []

        # Placement 1: After 2nd paragraph (introduction)
        if num_ads >= 1 and len(paragraphs) >= 2:
            placements.append({
                "position": "after_paragraph",
                "index": 1,  # 0-indexed, so after 2nd paragraph
                "type": "top"
            })

        # Placement 2: Middle of content
        if num_ads >= 2 and len(paragraphs) >= 5:
            middle_index = len(paragraphs) // 2
            placements.append({
                "position": "after_paragraph",
                "index": middle_index,
                "type": "middle"
            })

        # Placement 3: Before conclusion (3rd paragraph from end)
        if num_ads >= 3 and len(paragraphs) >= 6:
            placements.append({
                "position": "after_paragraph",
                "index": len(paragraphs) - 4,
                "type": "bottom"
            })

        # Placement 4: After conclusion
        if num_ads >= 4 and len(paragraphs) >= 8:
            placements.append({
                "position": "after_paragraph",
                "index": len(paragraphs) - 1,
                "type": "end"
            })

        logger.info(
            "ad_placements_calculated",
            word_count=word_count,
            num_ads=len(placements)
        )

        return placements

    def insert_ads(
        self,
        content: str,
        placements: List[Dict[str, Any]] = None,
        auto_optimize: bool = True
    ) -> Dict[str, Any]:
        """
        Insert AdSense ads into content.

        Args:
            content: HTML content.
            placements: Manual ad placements (None for auto).
            auto_optimize: Automatically optimize placements.

        Returns:
            Dict[str, Any]: Content with ads and metadata.

        Example:
            ```python
            service = AdInserterService()
            result = service.insert_ads(content_html)
            print(result['content'])  # Content with ads
            print(result['ads_inserted'])  # Number of ads
            ```
        """
        logger.info("inserting_ads", auto_optimize=auto_optimize)

        soup = BeautifulSoup(content, "html.parser")
        paragraphs = soup.find_all("p")

        if not paragraphs:
            logger.warning("no_paragraphs_found_for_ad_insertion")
            return {
                "content": content,
                "ads_inserted": 0,
                "placements": []
            }

        # Calculate placements if not provided
        if placements is None or auto_optimize:
            placements = self.calculate_ad_placements(content)

        # Sort placements in reverse order to insert from bottom to top
        # (prevents index shifting)
        placements.sort(key=lambda x: x["index"], reverse=True)

        ads_inserted = 0
        actual_placements = []

        for placement in placements:
            index = placement["index"]

            # Safety check
            if index < 0 or index >= len(paragraphs):
                continue

            # Get ad code
            ad_code = self.generate_ad_code(
                ad_slot=settings.adsense_ad_slot_inline
            )

            # Insert ad after paragraph
            ad_soup = BeautifulSoup(ad_code, "html.parser")
            paragraphs[index].insert_after(ad_soup)

            ads_inserted += 1
            actual_placements.append({
                "position": placement["type"],
                "paragraph_index": index,
            })

        # Add auto ads script if enabled
        if settings.adsense_auto_ads:
            auto_ads_script = f'''
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={settings.adsense_client_id}"
     crossorigin="anonymous"></script>
'''
            script_soup = BeautifulSoup(auto_ads_script, "html.parser")
            if soup.head:
                soup.head.append(script_soup)
            else:
                soup.insert(0, script_soup)

        result = {
            "content": str(soup),
            "ads_inserted": ads_inserted,
            "placements": actual_placements,
        }

        logger.info(
            "ads_inserted",
            count=ads_inserted,
            placements=actual_placements
        )

        return result

    def insert_sidebar_ads(self, content: str) -> str:
        """
        Add sidebar ad placeholder to content.

        Args:
            content: HTML content.

        Returns:
            str: Content with sidebar ad.
        """
        sidebar_ad = self.generate_ad_code(
            ad_slot=settings.adsense_ad_slot_sidebar,
            ad_format="rectangle"
        )

        sidebar_html = f'''
<div class="sidebar-ad" style="float: right; width: 300px; margin: 20px;">
    {sidebar_ad}
</div>
'''

        # Insert after first paragraph
        soup = BeautifulSoup(content, "html.parser")
        first_p = soup.find("p")

        if first_p:
            sidebar_soup = BeautifulSoup(sidebar_html, "html.parser")
            first_p.insert_after(sidebar_soup)

        return str(soup)

    def validate_ad_density(self, content: str) -> Dict[str, Any]:
        """
        Validate ad density to ensure compliance with AdSense policies.

        AdSense policy: Content should not be overwhelmed by ads.
        Recommended: Max 3-4 ads per 1000 words.

        Args:
            content: HTML content with ads.

        Returns:
            Dict[str, Any]: Validation results.
        """
        word_count = count_words(content)
        soup = BeautifulSoup(content, "html.parser")
        ad_count = len(soup.find_all("ins", class_="adsbygoogle"))

        # Calculate density
        ads_per_1000_words = (ad_count / word_count) * 1000 if word_count > 0 else 0

        # Recommended: 3-4 ads per 1000 words
        is_valid = ads_per_1000_words <= 5.0

        result = {
            "valid": is_valid,
            "word_count": word_count,
            "ad_count": ad_count,
            "ads_per_1000_words": round(ads_per_1000_words, 2),
            "recommendation": "OK" if is_valid else "Too many ads, consider reducing"
        }

        logger.info(
            "ad_density_validated",
            valid=is_valid,
            density=ads_per_1000_words
        )

        return result
