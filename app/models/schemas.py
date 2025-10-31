"""
Pydantic schemas for request/response validation.

These schemas define the structure of API requests and responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator
from enum import Enum


class PostStatus(str, Enum):
    """Post status enumeration."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ===== Keyword Schemas =====

class KeywordBase(BaseModel):
    """Base keyword schema."""
    keyword: str = Field(..., min_length=1, max_length=255)
    search_volume: int = Field(ge=0)
    competition: float = Field(ge=0.0, le=1.0)
    cpc: float = Field(ge=0.0)
    trend: Optional[float] = Field(default=0.0, ge=-1.0, le=1.0)


class KeywordCreate(KeywordBase):
    """Schema for creating a keyword."""
    pass


class KeywordResponse(KeywordBase):
    """Schema for keyword response."""
    id: int
    golden_score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KeywordResearchRequest(BaseModel):
    """Request schema for keyword research."""
    seed_keywords: List[str] = Field(..., min_length=1, max_length=10)
    language: str = Field(default="ko", pattern="^[a-z]{2}$")
    location: str = Field(default="KR", pattern="^[A-Z]{2}$")
    include_naver: bool = Field(default=True)
    include_autocomplete: bool = Field(default=True)


class KeywordResearchResponse(BaseModel):
    """Response schema for keyword research."""
    keywords: List[KeywordResponse]
    total_found: int
    top_keywords: List[KeywordResponse]
    task_id: Optional[str] = None


# ===== Content Schemas =====

class ContentGenerationRequest(BaseModel):
    """Request schema for content generation."""
    keyword: str = Field(..., min_length=1, max_length=255)
    target_word_count: int = Field(default=2000, ge=1500, le=3000)
    tone: str = Field(default="professional")
    llm_provider: Optional[str] = Field(
        default=None,
        description="LLM provider (claude, chatgpt, gemini). Uses default if not specified."
    )
    include_images: bool = Field(default=True)
    num_images: int = Field(default=4, ge=1, le=10)
    include_schema: bool = Field(default=True)
    include_faq: bool = Field(default=True)

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: Optional[str]) -> Optional[str]:
        """Validate LLM provider."""
        if v is None:
            return v
        valid_providers = ["claude", "chatgpt", "gemini"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Invalid LLM provider: {v}. Must be one of {valid_providers}")
        return v.lower()


class ContentResponse(BaseModel):
    """Response schema for generated content."""
    title: str
    content: str
    meta_description: str
    h1_tag: str
    h2_tags: List[str]
    h3_tags: List[str]
    internal_links: List[str]
    schema_markup: Optional[Dict[str, Any]] = None
    faq_schema: Optional[Dict[str, Any]] = None
    word_count: int
    estimated_reading_time: int


# ===== Image Schemas =====

class ImageGenerationRequest(BaseModel):
    """Request schema for image generation."""
    prompt: str = Field(..., min_length=1, max_length=1000)
    is_hero: bool = Field(default=True)
    style: str = Field(default="realistic")


class ImageResponse(BaseModel):
    """Response schema for image."""
    id: int
    url: str
    local_path: Optional[str] = None
    alt_text: str
    width: int
    height: int
    size_kb: int
    format: str
    is_hero: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Post Schemas =====

class PostBase(BaseModel):
    """Base post schema."""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=100)
    meta_description: str = Field(..., max_length=160)
    slug: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    featured_image_url: Optional[str] = None


class PostCreate(PostBase):
    """Schema for creating a post."""
    keyword_id: Optional[int] = None
    status: PostStatus = PostStatus.DRAFT
    scheduled_for: Optional[datetime] = None


class PostUpdate(BaseModel):
    """Schema for updating a post."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=100)
    meta_description: Optional[str] = Field(None, max_length=160)
    status: Optional[PostStatus] = None
    scheduled_for: Optional[datetime] = None


class PostResponse(PostBase):
    """Schema for post response."""
    id: int
    keyword_id: Optional[int] = None
    status: PostStatus
    scheduled_for: Optional[datetime] = None
    published_at: Optional[datetime] = None
    wp_post_id: Optional[int] = None
    wp_url: Optional[str] = None
    view_count: int
    word_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PostWithImages(PostResponse):
    """Schema for post response with images."""
    images: List[ImageResponse] = []


# ===== Publishing Schemas =====

class PublishRequest(BaseModel):
    """Request schema for publishing."""
    post_id: int = Field(..., gt=0)
    publish_immediately: bool = Field(default=False)
    scheduled_time: Optional[datetime] = None


class PublishResponse(BaseModel):
    """Response schema for publishing."""
    post_id: int
    wp_post_id: int
    wp_url: str
    status: str
    published_at: datetime
    message: str


# ===== Schedule Schemas =====

class ScheduleTaskRequest(BaseModel):
    """Request schema for scheduling a task."""
    task_name: str = Field(..., min_length=1, max_length=255)
    task_type: str = Field(..., min_length=1, max_length=50)
    schedule_time: datetime
    params: Dict[str, Any] = Field(default_factory=dict)


class ScheduleTaskResponse(BaseModel):
    """Response schema for scheduled task."""
    id: int
    task_name: str
    task_type: str
    status: TaskStatus
    schedule_time: datetime
    celery_task_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== AdSense Schemas =====

class AdPlacement(BaseModel):
    """Schema for ad placement."""
    position: str = Field(..., pattern="^(top|middle|bottom|sidebar)$")
    ad_type: str = Field(default="auto")
    ad_slot: Optional[str] = None


class AdInsertionRequest(BaseModel):
    """Request schema for ad insertion."""
    content: str = Field(..., min_length=100)
    placements: List[AdPlacement] = Field(default_factory=list)
    auto_optimize: bool = Field(default=True)


class AdInsertionResponse(BaseModel):
    """Response schema for ad insertion."""
    content: str
    ads_inserted: int
    placements: List[Dict[str, Any]]


# ===== Complete Workflow Schemas =====

class CompleteWorkflowRequest(BaseModel):
    """Request schema for complete automation workflow."""
    seed_keywords: List[str] = Field(..., min_length=1, max_length=5)
    num_posts: int = Field(default=1, ge=1, le=10)
    publish_immediately: bool = Field(default=False)
    schedule_interval_hours: int = Field(default=24, ge=1, le=168)


class CompleteWorkflowResponse(BaseModel):
    """Response schema for complete workflow."""
    task_id: str
    status: str
    message: str
    estimated_completion_time: Optional[datetime] = None


# ===== Statistics Schemas =====

class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_keywords: int
    total_posts: int
    published_posts: int
    scheduled_posts: int
    draft_posts: int
    total_views: int
    avg_word_count: float
    posts_this_month: int
    keywords_researched_today: int


# ===== Health Check Schema =====

class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
    database: bool
    redis: bool
    celery: bool
    services: Dict[str, bool]
