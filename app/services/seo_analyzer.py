"""
SEO analysis service for content quality verification.

This module provides comprehensive SEO scoring and analysis for blog content.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SEOScore:
    """SEO score result."""
    overall_score: float  # 0-100
    keyword_density_score: float  # 0-100
    title_optimization_score: float  # 0-100
    meta_tags_score: float  # 0-100
    readability_score: float  # 0-100
    internal_links_score: float  # 0-100
    image_alt_score: float  # 0-100

    issues: List[Dict[str, Any]]
    suggestions: List[str]

    # Detailed metrics
    metrics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class SEOAnalyzer:
    """
    SEO analyzer for content quality verification.

    Analyzes content and calculates SEO scores based on multiple factors:
    - Keyword density and placement
    - Title optimization
    - Meta tags quality
    - Content readability
    - Internal linking
    - Image optimization
    """

    def __init__(self):
        """Initialize SEO analyzer."""
        # Korean readability weights (adjusted for Korean language)
        self.readability_weights = {
            "avg_sentence_length": 0.2,
            "avg_word_length": 0.15,
            "paragraph_structure": 0.25,
            "heading_distribution": 0.2,
            "list_usage": 0.1,
            "formatting": 0.1
        }

    def analyze(
        self,
        title: str,
        content: str,
        meta_description: str,
        target_keyword: str,
        h1_tag: Optional[str] = None,
        h2_tags: Optional[List[str]] = None,
        h3_tags: Optional[List[str]] = None,
        internal_links: Optional[List[str]] = None,
        images: Optional[List[Dict[str, str]]] = None
    ) -> SEOScore:
        """
        Analyze content and calculate comprehensive SEO score.

        Args:
            title: Post title
            content: Post content (HTML)
            meta_description: Meta description
            target_keyword: Target keyword
            h1_tag: H1 tag
            h2_tags: List of H2 tags
            h3_tags: List of H3 tags
            internal_links: List of internal link URLs
            images: List of image dicts with 'url' and 'alt_text'

        Returns:
            SEOScore with detailed analysis
        """
        logger.info("seo_analysis_started", keyword=target_keyword)

        # Initialize
        issues = []
        suggestions = []
        metrics = {}

        # Parse HTML content
        soup = BeautifulSoup(content, 'html.parser')
        text_content = soup.get_text()

        # 1. Keyword Density Analysis
        keyword_density_score, kd_issues, kd_metrics = self._analyze_keyword_density(
            text_content, title, target_keyword
        )
        issues.extend(kd_issues)
        metrics["keyword_density"] = kd_metrics

        # 2. Title Optimization
        title_score, title_issues, title_metrics = self._analyze_title(
            title, target_keyword
        )
        issues.extend(title_issues)
        metrics["title"] = title_metrics

        # 3. Meta Tags
        meta_score, meta_issues, meta_metrics = self._analyze_meta_tags(
            meta_description, target_keyword
        )
        issues.extend(meta_issues)
        metrics["meta_tags"] = meta_metrics

        # 4. Readability
        readability_score, read_issues, read_metrics = self._analyze_readability(
            text_content, soup, h2_tags or [], h3_tags or []
        )
        issues.extend(read_issues)
        metrics["readability"] = read_metrics

        # 5. Internal Links
        links_score, links_issues, links_metrics = self._analyze_internal_links(
            soup, internal_links or []
        )
        issues.extend(links_issues)
        metrics["internal_links"] = links_metrics

        # 6. Image Alt Text
        image_score, image_issues, image_metrics = self._analyze_images(
            soup, images or [], target_keyword
        )
        issues.extend(image_issues)
        metrics["images"] = image_metrics

        # Calculate overall score (weighted average)
        weights = {
            "keyword_density": 0.20,
            "title": 0.20,
            "meta_tags": 0.15,
            "readability": 0.20,
            "internal_links": 0.10,
            "images": 0.15
        }

        overall_score = (
            keyword_density_score * weights["keyword_density"] +
            title_score * weights["title"] +
            meta_score * weights["meta_tags"] +
            readability_score * weights["readability"] +
            links_score * weights["internal_links"] +
            image_score * weights["images"]
        )

        # Generate suggestions based on issues
        suggestions = self._generate_suggestions(issues, overall_score)

        # Add overall metrics
        metrics["overall"] = {
            "score": overall_score,
            "grade": self._get_grade(overall_score),
            "content_length": len(text_content),
            "word_count": len(text_content.split()),
            "weights": weights
        }

        logger.info(
            "seo_analysis_completed",
            overall_score=overall_score,
            issues_count=len(issues)
        )

        return SEOScore(
            overall_score=round(overall_score, 2),
            keyword_density_score=round(keyword_density_score, 2),
            title_optimization_score=round(title_score, 2),
            meta_tags_score=round(meta_score, 2),
            readability_score=round(readability_score, 2),
            internal_links_score=round(links_score, 2),
            image_alt_score=round(image_score, 2),
            issues=issues,
            suggestions=suggestions,
            metrics=metrics
        )

    def _analyze_keyword_density(
        self,
        text: str,
        title: str,
        keyword: str
    ) -> Tuple[float, List[Dict], Dict]:
        """
        Analyze keyword density and placement.

        Optimal keyword density: 1-2%
        Keyword should appear in: title, first paragraph, headings
        """
        issues = []
        text_lower = text.lower()
        keyword_lower = keyword.lower()

        # Count keyword occurrences
        keyword_count = text_lower.count(keyword_lower)
        word_count = len(text.split())

        # Calculate density
        density = (keyword_count / word_count * 100) if word_count > 0 else 0

        # Check keyword in title
        keyword_in_title = keyword_lower in title.lower()

        # Check keyword in first paragraph (first 200 characters)
        first_para = text[:200].lower()
        keyword_in_first_para = keyword_lower in first_para

        # Score calculation
        score = 0

        # Density score (50 points max)
        if 1 <= density <= 2.5:
            score += 50  # Optimal
        elif 0.5 <= density < 1:
            score += 40  # Slightly low
            issues.append({
                "severity": "medium",
                "category": "keyword_density",
                "message": f"키워드 밀도가 낮습니다 ({density:.2f}%). 1-2% 권장."
            })
        elif 2.5 < density <= 3.5:
            score += 40  # Slightly high
            issues.append({
                "severity": "medium",
                "category": "keyword_density",
                "message": f"키워드 밀도가 높습니다 ({density:.2f}%). 1-2% 권장."
            })
        elif density > 3.5:
            score += 20  # Too high (keyword stuffing)
            issues.append({
                "severity": "high",
                "category": "keyword_density",
                "message": f"키워드 밀도가 너무 높습니다 ({density:.2f}%). 키워드 스터핑 주의!"
            })
        else:
            score += 20  # Too low
            issues.append({
                "severity": "high",
                "category": "keyword_density",
                "message": f"키워드가 거의 없습니다 ({density:.2f}%)."
            })

        # Keyword in title (25 points)
        if keyword_in_title:
            score += 25
        else:
            issues.append({
                "severity": "high",
                "category": "keyword_placement",
                "message": "제목에 타겟 키워드가 없습니다."
            })

        # Keyword in first paragraph (25 points)
        if keyword_in_first_para:
            score += 25
        else:
            issues.append({
                "severity": "medium",
                "category": "keyword_placement",
                "message": "첫 문단에 타겟 키워드가 없습니다."
            })

        metrics = {
            "keyword": keyword,
            "keyword_count": keyword_count,
            "word_count": word_count,
            "density_percentage": round(density, 2),
            "in_title": keyword_in_title,
            "in_first_paragraph": keyword_in_first_para
        }

        return score, issues, metrics

    def _analyze_title(self, title: str, keyword: str) -> Tuple[float, List[Dict], Dict]:
        """
        Analyze title optimization.

        Optimal title length: 30-60 characters (Korean: 15-30 characters)
        Should contain keyword, preferably at the beginning
        """
        issues = []
        title_len = len(title)
        keyword_lower = keyword.lower()
        title_lower = title.lower()

        score = 0

        # Length score (40 points)
        if 15 <= title_len <= 30:
            score += 40  # Optimal for Korean
        elif 30 < title_len <= 40:
            score += 35  # Acceptable
            issues.append({
                "severity": "low",
                "category": "title_length",
                "message": f"제목이 약간 깁니다 ({title_len}자). 15-30자 권장."
            })
        elif 10 <= title_len < 15:
            score += 30  # Too short
            issues.append({
                "severity": "medium",
                "category": "title_length",
                "message": f"제목이 짧습니다 ({title_len}자). 15-30자 권장."
            })
        elif title_len > 40:
            score += 25  # Too long
            issues.append({
                "severity": "medium",
                "category": "title_length",
                "message": f"제목이 깁니다 ({title_len}자). 15-30자 권장."
            })
        else:
            score += 20  # Very short
            issues.append({
                "severity": "high",
                "category": "title_length",
                "message": f"제목이 너무 짧습니다 ({title_len}자)."
            })

        # Keyword presence (30 points)
        if keyword_lower in title_lower:
            # Check keyword position
            keyword_pos = title_lower.find(keyword_lower)
            if keyword_pos < len(title) * 0.3:  # First 30%
                score += 30
            else:
                score += 25
                issues.append({
                    "severity": "low",
                    "category": "title_keyword",
                    "message": "키워드가 제목 앞쪽에 있으면 더 좋습니다."
                })
        else:
            issues.append({
                "severity": "high",
                "category": "title_keyword",
                "message": "제목에 타겟 키워드가 없습니다."
            })

        # Special characters and formatting (15 points)
        if re.search(r'[!?]', title):
            score += 10  # Has engaging punctuation

        # Numbers in title (bonus)
        if re.search(r'\d+', title):
            score += 5  # Numbers attract attention

        # Ensure score doesn't exceed 100
        score = min(score, 100)

        metrics = {
            "length": title_len,
            "keyword_present": keyword_lower in title_lower,
            "has_numbers": bool(re.search(r'\d+', title)),
            "has_punctuation": bool(re.search(r'[!?]', title))
        }

        return score, issues, metrics

    def _analyze_meta_tags(
        self,
        meta_description: str,
        keyword: str
    ) -> Tuple[float, List[Dict], Dict]:
        """
        Analyze meta description.

        Optimal length: 120-160 characters (Korean: 60-80 characters)
        Should contain keyword
        Should be compelling
        """
        issues = []
        desc_len = len(meta_description)
        keyword_lower = keyword.lower()
        desc_lower = meta_description.lower()

        score = 0

        # Length score (50 points)
        if 60 <= desc_len <= 80:
            score += 50  # Optimal for Korean
        elif 80 < desc_len <= 100:
            score += 45  # Acceptable
            issues.append({
                "severity": "low",
                "category": "meta_description_length",
                "message": f"메타 설명이 약간 깁니다 ({desc_len}자). 60-80자 권장."
            })
        elif 40 <= desc_len < 60:
            score += 40  # Too short
            issues.append({
                "severity": "medium",
                "category": "meta_description_length",
                "message": f"메타 설명이 짧습니다 ({desc_len}자). 60-80자 권장."
            })
        elif desc_len > 100:
            score += 35  # Too long
            issues.append({
                "severity": "medium",
                "category": "meta_description_length",
                "message": f"메타 설명이 깁니다 ({desc_len}자). 검색 결과에서 잘릴 수 있습니다."
            })
        else:
            score += 25  # Very short
            issues.append({
                "severity": "high",
                "category": "meta_description_length",
                "message": f"메타 설명이 너무 짧습니다 ({desc_len}자)."
            })

        # Keyword presence (30 points)
        if keyword_lower in desc_lower:
            score += 30
        else:
            issues.append({
                "severity": "high",
                "category": "meta_description_keyword",
                "message": "메타 설명에 타겟 키워드가 없습니다."
            })

        # Call-to-action or engaging language (20 points)
        cta_keywords = ['방법', '가이드', '비법', '완벽', '최고', '추천', '필수', '꼭']
        has_cta = any(word in desc_lower for word in cta_keywords)
        if has_cta:
            score += 20
        else:
            issues.append({
                "severity": "low",
                "category": "meta_description_cta",
                "message": "메타 설명에 행동 유도 문구를 추가하면 좋습니다."
            })

        metrics = {
            "length": desc_len,
            "keyword_present": keyword_lower in desc_lower,
            "has_cta": has_cta
        }

        return score, issues, metrics

    def _analyze_readability(
        self,
        text: str,
        soup: BeautifulSoup,
        h2_tags: List[str],
        h3_tags: List[str]
    ) -> Tuple[float, List[Dict], Dict]:
        """
        Analyze content readability.

        Considers:
        - Sentence length
        - Paragraph structure
        - Heading distribution
        - Use of lists
        - Formatting (bold, italic)
        """
        issues = []
        score = 0

        # Sentence analysis
        sentences = re.split(r'[.!?。！？]', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) == 0:
            return 0, [{"severity": "high", "category": "readability", "message": "콘텐츠가 없습니다."}], {}

        avg_sentence_len = sum(len(s) for s in sentences) / len(sentences)

        # Optimal sentence length for Korean: 15-25 characters
        if 15 <= avg_sentence_len <= 25:
            score += 20
        elif 10 <= avg_sentence_len < 15 or 25 < avg_sentence_len <= 35:
            score += 15
            issues.append({
                "severity": "low",
                "category": "readability",
                "message": f"평균 문장 길이: {avg_sentence_len:.1f}자. 15-25자가 읽기 좋습니다."
            })
        else:
            score += 10
            issues.append({
                "severity": "medium",
                "category": "readability",
                "message": f"문장이 {'너무 짧거나' if avg_sentence_len < 10 else '너무'} 깁니다."
            })

        # Paragraph structure
        paragraphs = soup.find_all('p')
        if len(paragraphs) >= 5:
            score += 20
        elif len(paragraphs) >= 3:
            score += 15
        else:
            score += 10
            issues.append({
                "severity": "medium",
                "category": "readability",
                "message": f"단락이 부족합니다 ({len(paragraphs)}개). 최소 5개 이상 권장."
            })

        # Heading distribution
        total_headings = len(h2_tags) + len(h3_tags)
        words = len(text.split())
        headings_per_500_words = (total_headings / words * 500) if words > 0 else 0

        if 3 <= headings_per_500_words <= 7:
            score += 20
        elif 2 <= headings_per_500_words < 3 or 7 < headings_per_500_words <= 10:
            score += 15
            issues.append({
                "severity": "low",
                "category": "readability",
                "message": "소제목 개수를 조정하면 좋습니다."
            })
        else:
            score += 10
            issues.append({
                "severity": "medium",
                "category": "readability",
                "message": "소제목이 너무 많거나 적습니다."
            })

        # Use of lists
        lists = soup.find_all(['ul', 'ol'])
        if len(lists) >= 2:
            score += 20
        elif len(lists) == 1:
            score += 15
        else:
            score += 5
            issues.append({
                "severity": "low",
                "category": "readability",
                "message": "목록(리스트)을 사용하면 가독성이 향상됩니다."
            })

        # Formatting (bold, italic)
        bold_tags = soup.find_all(['strong', 'b'])
        emphasis_tags = soup.find_all(['em', 'i'])

        if len(bold_tags) > 0 or len(emphasis_tags) > 0:
            score += 20
        else:
            score += 10
            issues.append({
                "severity": "low",
                "category": "readability",
                "message": "중요한 내용을 굵게 표시하면 좋습니다."
            })

        metrics = {
            "avg_sentence_length": round(avg_sentence_len, 1),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "heading_count": total_headings,
            "list_count": len(lists),
            "bold_count": len(bold_tags),
            "emphasis_count": len(emphasis_tags)
        }

        return score, issues, metrics

    def _analyze_internal_links(
        self,
        soup: BeautifulSoup,
        internal_links: List[str]
    ) -> Tuple[float, List[Dict], Dict]:
        """
        Analyze internal linking.

        Optimal: 3-5 internal links per post
        Links should have descriptive anchor text
        """
        issues = []

        # Count internal links
        link_count = len(internal_links)

        # Find all anchor tags
        anchor_tags = soup.find_all('a')

        score = 0

        # Link count score (60 points)
        if 3 <= link_count <= 5:
            score += 60
        elif 2 <= link_count < 3 or 5 < link_count <= 7:
            score += 50
            issues.append({
                "severity": "low",
                "category": "internal_links",
                "message": f"내부 링크 개수: {link_count}개. 3-5개 권장."
            })
        elif 1 <= link_count < 2:
            score += 30
            issues.append({
                "severity": "medium",
                "category": "internal_links",
                "message": f"내부 링크가 부족합니다 ({link_count}개). 최소 3개 권장."
            })
        elif link_count > 7:
            score += 40
            issues.append({
                "severity": "medium",
                "category": "internal_links",
                "message": f"내부 링크가 많습니다 ({link_count}개). 적절히 조절하세요."
            })
        else:
            score += 20
            issues.append({
                "severity": "high",
                "category": "internal_links",
                "message": "내부 링크가 없습니다. 최소 3개 추가하세요."
            })

        # Anchor text analysis (40 points)
        generic_anchors = ['여기', '클릭', '링크', 'here', 'click', 'link']
        descriptive_count = 0

        for tag in anchor_tags:
            anchor_text = tag.get_text().strip().lower()
            if anchor_text and anchor_text not in generic_anchors and len(anchor_text) > 3:
                descriptive_count += 1

        if anchor_tags:
            descriptive_ratio = descriptive_count / len(anchor_tags)
            if descriptive_ratio >= 0.8:
                score += 40
            elif descriptive_ratio >= 0.6:
                score += 30
                issues.append({
                    "severity": "low",
                    "category": "internal_links",
                    "message": "일부 링크가 설명적이지 않습니다 ('여기', '클릭' 등 피하기)."
                })
            else:
                score += 20
                issues.append({
                    "severity": "medium",
                    "category": "internal_links",
                    "message": "링크 앵커 텍스트를 더 설명적으로 작성하세요."
                })

        metrics = {
            "internal_link_count": link_count,
            "total_link_count": len(anchor_tags),
            "descriptive_link_count": descriptive_count
        }

        return score, issues, metrics

    def _analyze_images(
        self,
        soup: BeautifulSoup,
        images: List[Dict[str, str]],
        keyword: str
    ) -> Tuple[float, List[Dict], Dict]:
        """
        Analyze image optimization.

        - All images should have alt text
        - Alt text should be descriptive
        - At least one image should contain keyword
        """
        issues = []

        # Find all img tags
        img_tags = soup.find_all('img')
        image_count = len(images) if images else len(img_tags)

        if image_count == 0:
            return 50, [{
                "severity": "medium",
                "category": "images",
                "message": "이미지가 없습니다. 최소 1개 이상 추가하세요."
            }], {"image_count": 0, "alt_text_count": 0}

        score = 0
        keyword_lower = keyword.lower()

        # Alt text presence (60 points)
        alt_text_count = 0
        keyword_in_alt_count = 0
        descriptive_alt_count = 0

        for img in images:
            alt_text = img.get('alt_text', '').strip()
            if alt_text:
                alt_text_count += 1

                # Check if alt text is descriptive (more than 5 characters)
                if len(alt_text) > 5:
                    descriptive_alt_count += 1

                # Check if keyword in alt text
                if keyword_lower in alt_text.lower():
                    keyword_in_alt_count += 1

        # Check img tags if images list is empty
        if not images and img_tags:
            for img_tag in img_tags:
                alt_text = img_tag.get('alt', '').strip()
                if alt_text:
                    alt_text_count += 1
                    if len(alt_text) > 5:
                        descriptive_alt_count += 1
                    if keyword_lower in alt_text.lower():
                        keyword_in_alt_count += 1

        alt_ratio = alt_text_count / image_count if image_count > 0 else 0

        if alt_ratio == 1.0:
            score += 60
        elif alt_ratio >= 0.8:
            score += 50
            issues.append({
                "severity": "low",
                "category": "images",
                "message": f"일부 이미지에 alt 텍스트가 없습니다 ({alt_text_count}/{image_count})."
            })
        elif alt_ratio >= 0.5:
            score += 35
            issues.append({
                "severity": "medium",
                "category": "images",
                "message": f"많은 이미지에 alt 텍스트가 없습니다 ({alt_text_count}/{image_count})."
            })
        else:
            score += 20
            issues.append({
                "severity": "high",
                "category": "images",
                "message": f"대부분 이미지에 alt 텍스트가 없습니다 ({alt_text_count}/{image_count})."
            })

        # Descriptive alt text (20 points)
        if descriptive_alt_count == alt_text_count and alt_text_count > 0:
            score += 20
        elif descriptive_alt_count >= alt_text_count * 0.7:
            score += 15
        else:
            score += 10
            if alt_text_count > 0:
                issues.append({
                    "severity": "low",
                    "category": "images",
                    "message": "일부 alt 텍스트가 너무 짧습니다. 더 설명적으로 작성하세요."
                })

        # Keyword in alt text (20 points)
        if keyword_in_alt_count > 0:
            score += 20
        else:
            issues.append({
                "severity": "low",
                "category": "images",
                "message": "최소 1개 이미지의 alt 텍스트에 타겟 키워드를 포함하세요."
            })

        metrics = {
            "image_count": image_count,
            "alt_text_count": alt_text_count,
            "descriptive_alt_count": descriptive_alt_count,
            "keyword_in_alt_count": keyword_in_alt_count,
            "alt_text_coverage": round(alt_ratio * 100, 1)
        }

        return score, issues, metrics

    def _generate_suggestions(self, issues: List[Dict], overall_score: float) -> List[str]:
        """Generate actionable suggestions based on issues."""
        suggestions = []

        # Group issues by severity
        high_issues = [i for i in issues if i['severity'] == 'high']
        medium_issues = [i for i in issues if i['severity'] == 'medium']

        # High priority suggestions
        if high_issues:
            suggestions.append("🔴 우선 해결 사항:")
            for issue in high_issues[:3]:  # Top 3
                suggestions.append(f"  • {issue['message']}")

        # Medium priority suggestions
        if medium_issues and len(suggestions) < 8:
            suggestions.append("🟡 개선 권장 사항:")
            for issue in medium_issues[:3]:  # Top 3
                suggestions.append(f"  • {issue['message']}")

        # Overall score based suggestions
        if overall_score < 60:
            suggestions.append("전반적인 SEO 최적화가 필요합니다. 위 사항들을 개선하세요.")
        elif overall_score < 80:
            suggestions.append("기본적인 SEO는 갖췄지만, 더 개선할 여지가 있습니다.")
        else:
            suggestions.append("✅ 훌륭합니다! SEO 최적화가 잘 되어 있습니다.")

        return suggestions

    def _get_grade(self, score: float) -> str:
        """Get letter grade from score."""
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "C+"
        elif score >= 65:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
