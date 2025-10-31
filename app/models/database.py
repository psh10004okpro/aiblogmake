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
