"""
SQLAlchemy database models.

These models define the database schema and relationships.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Keyword(Base):
    """Keyword model for storing researched keywords."""

    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), unique=True, index=True, nullable=False)
    search_volume = Column(Integer, default=0, nullable=False)
    competition = Column(Float, default=0.0, nullable=False)
    cpc = Column(Float, default=0.0, nullable=False)
    trend = Column(Float, default=0.0, nullable=False)
    golden_score = Column(Float, default=0.0, nullable=False, index=True)

    # Naver specific data
    naver_monthly_pc_search = Column(Integer, default=0)
    naver_monthly_mobile_search = Column(Integer, default=0)

    # Metadata
    source = Column(String(50), default="manual")  # google, naver, autocomplete, manual
    language = Column(String(10), default="ko")
    location = Column(String(10), default="KR")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    posts = relationship("Post", back_populates="keyword")

    # Indexes
    __table_args__ = (
        Index("ix_keywords_golden_score_desc", golden_score.desc()),
        Index("ix_keywords_search_volume_desc", search_volume.desc()),
    )

    def __repr__(self) -> str:
        return f"<Keyword(id={self.id}, keyword='{self.keyword}', score={self.golden_score})>"


class Post(Base):
    """Post model for storing blog posts."""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    slug = Column(String(500), unique=True, index=True)
    content = Column(Text, nullable=False)
    meta_description = Column(String(160))
    h1_tag = Column(String(500))

    # SEO Data
    word_count = Column(Integer, default=0)
    internal_links = Column(JSON)  # List of internal link URLs
    schema_markup = Column(JSON)  # Structured data
    faq_schema = Column(JSON)  # FAQ schema

    # WordPress data
    wp_post_id = Column(Integer, unique=True, index=True)
    wp_url = Column(String(500))

    # Publishing data
    status = Column(String(20), default="draft", index=True)  # draft, scheduled, published, failed
    scheduled_for = Column(DateTime(timezone=True), index=True)
    published_at = Column(DateTime(timezone=True))

    # Categories and tags
    categories = Column(JSON)  # List of category names
    tags = Column(JSON)  # List of tag names

    # Featured image
    featured_image_url = Column(String(500))

    # Analytics
    view_count = Column(Integer, default=0)

    # Foreign keys
    keyword_id = Column(Integer, ForeignKey("keywords.id"), index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    keyword = relationship("Keyword", back_populates="posts")
    images = relationship("Image", back_populates="post", cascade="all, delete-orphan")
    publish_history = relationship(
        "PublishHistory",
        back_populates="post",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_posts_status_scheduled", status, scheduled_for),
        Index("ix_posts_published_at_desc", published_at.desc()),
    )

    def __repr__(self) -> str:
        return f"<Post(id={self.id}, title='{self.title[:50]}...', status='{self.status}')>"


class Image(Base):
    """Image model for storing generated/downloaded images."""

    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), nullable=False)
    local_path = Column(String(500))
    alt_text = Column(String(125))

    # Image properties
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    size_kb = Column(Integer, default=0)
    format = Column(String(10), default="webp")
    is_hero = Column(Boolean, default=False)

    # Source information
    source = Column(String(50), default="dalle")  # dalle, unsplash, manual
    source_id = Column(String(255))  # ID from source API
    prompt = Column(Text)  # Generation prompt for DALL-E

    # WordPress data
    wp_media_id = Column(Integer)
    wp_url = Column(String(500))

    # Foreign keys
    post_id = Column(Integer, ForeignKey("posts.id"), index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    post = relationship("Post", back_populates="images")

    # Indexes
    __table_args__ = (
        Index("ix_images_post_id_is_hero", post_id, is_hero),
    )

    def __repr__(self) -> str:
        return f"<Image(id={self.id}, source='{self.source}', is_hero={self.is_hero})>"


class PublishHistory(Base):
    """Publishing history model for tracking post publishing attempts."""

    __tablename__ = "publish_history"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)

    # Publishing details
    status = Column(String(20), nullable=False, index=True)  # success, failed
    wp_post_id = Column(Integer)
    wp_url = Column(String(500))
    error_message = Column(Text)

    # Timing
    attempted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    duration_seconds = Column(Float)

    # Retry information
    attempt_number = Column(Integer, default=1)
    retry_after = Column(DateTime(timezone=True))

    # Relationships
    post = relationship("Post", back_populates="publish_history")

    # Indexes
    __table_args__ = (
        Index("ix_publish_history_status_attempted", status, attempted_at.desc()),
    )

    def __repr__(self) -> str:
        return f"<PublishHistory(id={self.id}, post_id={self.post_id}, status='{self.status}')>"


class ScheduledTask(Base):
    """Scheduled task model for managing Celery tasks."""

    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(255), nullable=False, index=True)
    task_type = Column(String(50), nullable=False, index=True)
    celery_task_id = Column(String(255), unique=True, index=True)

    # Scheduling
    schedule_time = Column(DateTime(timezone=True), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Status
    status = Column(
        String(20),
        default="pending",
        nullable=False,
        index=True
    )  # pending, running, completed, failed, cancelled

    # Task parameters and results
    params = Column(JSON)  # Task parameters
    result = Column(JSON)  # Task result
    error = Column(Text)  # Error message if failed

    # Retry information
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("ix_scheduled_tasks_status_schedule", status, schedule_time),
        Index("ix_scheduled_tasks_type_status", task_type, status),
    )

    def __repr__(self) -> str:
        return f"<ScheduledTask(id={self.id}, task_name='{self.task_name}', status='{self.status}')>"


class SystemConfig(Base):
    """System configuration model for storing application settings."""

    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    description = Column(Text)
    category = Column(String(50), default="general")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __repr__(self) -> str:
        return f"<SystemConfig(key='{self.key}', category='{self.category}')>"


class APILog(Base):
    """API log model for tracking external API calls."""

    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True, index=True)
    service = Column(String(50), nullable=False, index=True)  # openai, anthropic, google_ads, etc.
    endpoint = Column(String(255))
    method = Column(String(10))

    # Request/Response
    request_data = Column(JSON)
    response_data = Column(JSON)
    status_code = Column(Integer)

    # Performance
    duration_ms = Column(Integer)
    tokens_used = Column(Integer)  # For AI APIs
    cost_usd = Column(Float)  # Estimated cost

    # Result
    success = Column(Boolean, default=True, index=True)
    error_message = Column(Text)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Indexes
    __table_args__ = (
        Index("ix_api_logs_service_created", service, created_at.desc()),
        Index("ix_api_logs_success_created", success, created_at.desc()),
    )

    def __repr__(self) -> str:
        return f"<APILog(id={self.id}, service='{self.service}', success={self.success})>"


class WorkflowRun(Base):
    """Workflow run model for tracking complete automation workflows."""

    __tablename__ = "workflow_runs"

    id = Column(Integer, primary_key=True, index=True)
    workflow_type = Column(String(50), nullable=False, index=True)  # one_click, scheduled, manual
    celery_task_id = Column(String(255), unique=True, index=True)

    # Configuration
    seed_keywords = Column(JSON)  # List of seed keywords
    num_posts = Column(Integer, default=1)
    publish_immediately = Column(Boolean, default=False)
    llm_provider = Column(String(20))  # claude, chatgpt, gemini

    # Status tracking
    status = Column(
        String(20),
        default="pending",
        nullable=False,
        index=True
    )  # pending, running, completed, failed, cancelled
    current_step = Column(String(50))  # Current step name
    progress_percentage = Column(Integer, default=0)  # 0-100

    # Step tracking (JSON with detailed progress)
    steps = Column(JSON, default={})  # Dict of step_name: {status, started_at, completed_at, result, error}

    # Results
    keywords_researched = Column(Integer, default=0)
    posts_created = Column(Integer, default=0)
    posts_published = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)

    # Detailed results
    results = Column(JSON)  # Complete workflow results
    errors = Column(JSON)  # List of errors that occurred

    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Float)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("ix_workflow_runs_status_created", status, created_at.desc()),
        Index("ix_workflow_runs_type_status", workflow_type, status),
    )

    def __repr__(self) -> str:
        return f"<WorkflowRun(id={self.id}, type='{self.workflow_type}', status='{self.status}')>"


class SEOScore(Base):
    """SEO score model for content quality tracking."""

    __tablename__ = "seo_scores"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), unique=True, nullable=False, index=True)

    # Overall score
    overall_score = Column(Float, nullable=False, index=True)
    grade = Column(String(5))  # A+, A, B+, B, C+, C, D, F

    # Component scores
    keyword_density_score = Column(Float, nullable=False)
    title_optimization_score = Column(Float, nullable=False)
    meta_tags_score = Column(Float, nullable=False)
    readability_score = Column(Float, nullable=False)
    internal_links_score = Column(Float, nullable=False)
    image_alt_score = Column(Float, nullable=False)

    # Issues and suggestions
    issues = Column(JSON)  # List of issues found
    suggestions = Column(JSON)  # List of improvement suggestions

    # Detailed metrics
    metrics = Column(JSON)  # Detailed analysis metrics

    # Analysis metadata
    target_keyword = Column(String(255))
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    analyzer_version = Column(String(20), default="1.0")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationship
    post = relationship("Post", backref="seo_score")

    # Indexes
    __table_args__ = (
        Index("ix_seo_scores_overall_score_desc", overall_score.desc()),
        Index("ix_seo_scores_post_id_analyzed", post_id, analyzed_at.desc()),
    )

    def __repr__(self) -> str:
        return f"<SEOScore(id={self.id}, post_id={self.post_id}, score={self.overall_score}, grade='{self.grade}')>"


class WordPressSite(Base):
    """WordPress 사이트 모델 - 멀티 블로그 관리"""

    __tablename__ = "wordpress_sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    api_url = Column(String(500), nullable=False)
    
    # WordPress 인증 정보 (암호화 권장)
    username = Column(String(255), nullable=False)
    app_password = Column(String(255), nullable=False)  # Application Password
    
    # 사이트 설정
    is_active = Column(Boolean, default=True, nullable=False)
    default_category = Column(String(100), default="Uncategorized")
    default_tags = Column(JSON)  # List of default tags
    
    # 자동 발행 설정
    auto_publish = Column(Boolean, default=False)
    publish_delay_minutes = Column(Integer, default=0)  # 발행 지연 시간
    
    # 통계
    total_posts_published = Column(Integer, default=0)
    last_published_at = Column(DateTime(timezone=True))
    
    # 사이트 메타데이터
    description = Column(Text)
    language = Column(String(10), default="ko")
    timezone = Column(String(50), default="Asia/Seoul")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationships
    site_posts = relationship("SitePost", back_populates="site", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("ix_wordpress_sites_is_active", is_active),
        Index("ix_wordpress_sites_name", name),
    )
    
    def __repr__(self) -> str:
        return f"<WordPressSite(id={self.id}, name='{self.name}', url='{self.url}', active={self.is_active})>"


class SitePost(Base):
    """사이트별 포스트 배포 추적 모델"""

    __tablename__ = "site_posts"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    site_id = Column(Integer, ForeignKey("wordpress_sites.id"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    
    # WordPress 데이터
    wp_post_id = Column(Integer, index=True)
    wp_url = Column(String(500))
    wp_status = Column(String(20), default="draft")  # draft, published, scheduled
    
    # 발행 상태
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, publishing, published, failed
    scheduled_for = Column(DateTime(timezone=True))
    published_at = Column(DateTime(timezone=True))
    
    # 오류 추적
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # 성과 데이터 (Google Analytics 연동)
    views = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationships
    site = relationship("WordPressSite", back_populates="site_posts")
    post = relationship("Post", backref="site_posts")
    
    # Indexes
    __table_args__ = (
        Index("ix_site_posts_site_status", site_id, status),
        Index("ix_site_posts_post_id", post_id),
        Index("ix_site_posts_scheduled", scheduled_for),
    )
    
    def __repr__(self) -> str:
        return f"<SitePost(id={self.id}, site_id={self.site_id}, post_id={self.post_id}, status='{self.status}')>"
