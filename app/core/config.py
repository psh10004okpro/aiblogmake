"""
Configuration module for Blog Automation System.

This module handles all application settings using Pydantic Settings,
loading configuration from environment variables.
"""

from typing import Optional, List
from pydantic import Field, field_validator, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # Application Settings
    app_name: str = Field(default="Blog Automation System", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    workers: int = Field(default=4, alias="WORKERS")

    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/blog_automation",
        alias="DATABASE_URL"
    )
    db_echo: bool = Field(default=False, alias="DB_ECHO")
    db_pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=40, alias="DB_MAX_OVERFLOW")

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_cache_expire: int = Field(default=3600, alias="REDIS_CACHE_EXPIRE")

    # Celery Configuration
    celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/1", alias="CELERY_RESULT_BACKEND")
    celery_task_serializer: str = Field(default="json", alias="CELERY_TASK_SERIALIZER")
    celery_result_serializer: str = Field(default="json", alias="CELERY_RESULT_SERIALIZER")
    celery_accept_content: str = Field(default="json", alias="CELERY_ACCEPT_CONTENT")
    celery_timezone: str = Field(default="Asia/Seoul", alias="CELERY_TIMEZONE")
    celery_enable_utc: bool = Field(default=True, alias="CELERY_ENABLE_UTC")

    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # OpenAI API
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_org_id: Optional[str] = Field(default=None, alias="OPENAI_ORG_ID")
    dalle_model: str = Field(default="dall-e-3", alias="DALLE_MODEL")
    dalle_size: str = Field(default="1792x1024", alias="DALLE_SIZE")
    dalle_quality: str = Field(default="hd", alias="DALLE_QUALITY")
    gpt_vision_model: str = Field(default="gpt-4-vision-preview", alias="GPT_VISION_MODEL")

    # Anthropic API
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-3-5-sonnet-20241022", alias="CLAUDE_MODEL")
    claude_max_tokens: int = Field(default=4000, alias="CLAUDE_MAX_TOKENS")
    claude_temperature: float = Field(default=0.7, alias="CLAUDE_TEMPERATURE")

    # Google Ads API
    google_ads_developer_token: str = Field(default="", alias="GOOGLE_ADS_DEVELOPER_TOKEN")
    google_ads_client_id: str = Field(default="", alias="GOOGLE_ADS_CLIENT_ID")
    google_ads_client_secret: str = Field(default="", alias="GOOGLE_ADS_CLIENT_SECRET")
    google_ads_refresh_token: str = Field(default="", alias="GOOGLE_ADS_REFRESH_TOKEN")
    google_ads_customer_id: str = Field(default="", alias="GOOGLE_ADS_CUSTOMER_ID")
    google_ads_login_customer_id: str = Field(default="", alias="GOOGLE_ADS_LOGIN_CUSTOMER_ID")

    # Naver Search Ad API
    naver_api_key: str = Field(default="", alias="NAVER_API_KEY")
    naver_secret_key: str = Field(default="", alias="NAVER_SECRET_KEY")
    naver_customer_id: str = Field(default="", alias="NAVER_CUSTOMER_ID")

    # Unsplash API
    unsplash_access_key: str = Field(default="", alias="UNSPLASH_ACCESS_KEY")
    unsplash_secret_key: Optional[str] = Field(default=None, alias="UNSPLASH_SECRET_KEY")

    # WordPress Configuration
    wp_url: str = Field(default="", alias="WP_URL")
    wp_username: str = Field(default="", alias="WP_USERNAME")
    wp_app_password: str = Field(default="", alias="WP_APP_PASSWORD")
    wp_api_timeout: int = Field(default=30, alias="WP_API_TIMEOUT")

    # AdSense Configuration
    adsense_client_id: str = Field(default="", alias="ADSENSE_CLIENT_ID")
    adsense_ad_slot_inline: str = Field(default="", alias="ADSENSE_AD_SLOT_INLINE")
    adsense_ad_slot_sidebar: str = Field(default="", alias="ADSENSE_AD_SLOT_SIDEBAR")
    adsense_auto_ads: bool = Field(default=True, alias="ADSENSE_AUTO_ADS")

    # Content Generation Settings
    min_content_length: int = Field(default=1500, alias="MIN_CONTENT_LENGTH")
    max_content_length: int = Field(default=3000, alias="MAX_CONTENT_LENGTH")
    target_word_count: int = Field(default=2000, alias="TARGET_WORD_COUNT")
    min_images_per_post: int = Field(default=3, alias="MIN_IMAGES_PER_POST")
    max_images_per_post: int = Field(default=5, alias="MAX_IMAGES_PER_POST")
    internal_links_min: int = Field(default=3, alias="INTERNAL_LINKS_MIN")
    internal_links_max: int = Field(default=5, alias="INTERNAL_LINKS_MAX")

    # Keyword Research Settings
    min_search_volume: int = Field(default=100, alias="MIN_SEARCH_VOLUME")
    max_competition: float = Field(default=0.7, alias="MAX_COMPETITION")
    min_cpc: float = Field(default=0.1, alias="MIN_CPC")
    top_keywords_count: int = Field(default=20, alias="TOP_KEYWORDS_COUNT")

    # Image Settings
    image_hero_width: int = Field(default=1792, alias="IMAGE_HERO_WIDTH")
    image_hero_height: int = Field(default=1024, alias="IMAGE_HERO_HEIGHT")
    image_thumbnail_width: int = Field(default=800, alias="IMAGE_THUMBNAIL_WIDTH")
    image_thumbnail_height: int = Field(default=600, alias="IMAGE_THUMBNAIL_HEIGHT")
    image_max_size_kb: int = Field(default=200, alias="IMAGE_MAX_SIZE_KB")
    image_format: str = Field(default="webp", alias="IMAGE_FORMAT")
    image_quality: int = Field(default=85, alias="IMAGE_QUALITY")
    watermark_text: str = Field(default="YourBlog.com", alias="WATERMARK_TEXT")
    watermark_opacity: int = Field(default=128, alias="WATERMARK_OPACITY")

    # SEO Settings
    sitemap_update_frequency: str = Field(default="daily", alias="SITEMAP_UPDATE_FREQUENCY")
    meta_description_length: int = Field(default=160, alias="META_DESCRIPTION_LENGTH")
    alt_text_max_length: int = Field(default=125, alias="ALT_TEXT_MAX_LENGTH")
    enable_schema_markup: bool = Field(default=True, alias="ENABLE_SCHEMA_MARKUP")
    enable_open_graph: bool = Field(default=True, alias="ENABLE_OPEN_GRAPH")
    enable_twitter_cards: bool = Field(default=True, alias="ENABLE_TWITTER_CARDS")

    # Scheduling Settings
    publish_time: str = Field(default="09:00", alias="PUBLISH_TIME")
    publish_timezone: str = Field(default="Asia/Seoul", alias="PUBLISH_TIMEZONE")
    auto_publish_enabled: bool = Field(default=True, alias="AUTO_PUBLISH_ENABLED")
    post_frequency_days: int = Field(default=1, alias="POST_FREQUENCY_DAYS")

    # Scraping Settings
    playwright_headless: bool = Field(default=True, alias="PLAYWRIGHT_HEADLESS")
    playwright_timeout: int = Field(default=30000, alias="PLAYWRIGHT_TIMEOUT")
    scraping_delay_min: int = Field(default=1, alias="SCRAPING_DELAY_MIN")
    scraping_delay_max: int = Field(default=3, alias="SCRAPING_DELAY_MAX")
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        alias="USER_AGENT"
    )

    # Rate Limiting
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, alias="RATE_LIMIT_PERIOD")

    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    sentry_traces_sample_rate: float = Field(default=0.1, alias="SENTRY_TRACES_SAMPLE_RATE")
    sentry_profiles_sample_rate: float = Field(default=0.1, alias="SENTRY_PROFILES_SAMPLE_RATE")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")
    metrics_port: int = Field(default=8000, alias="METRICS_PORT")

    # Email Notifications
    smtp_host: Optional[str] = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, alias="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: Optional[str] = Field(default=None, alias="SMTP_FROM")
    notify_emails: Optional[str] = Field(default=None, alias="NOTIFY_EMAILS")

    # Feature Flags
    enable_keyword_research: bool = Field(default=True, alias="ENABLE_KEYWORD_RESEARCH")
    enable_auto_images: bool = Field(default=True, alias="ENABLE_AUTO_IMAGES")
    enable_adsense_auto_insert: bool = Field(default=True, alias="ENABLE_ADSENSE_AUTO_INSERT")
    enable_auto_publish: bool = Field(default=True, alias="ENABLE_AUTO_PUBLISH")
    enable_naver_autocomplete: bool = Field(default=True, alias="ENABLE_NAVER_AUTOCOMPLETE")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        """Validate application environment."""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid_envs}")
        return v.lower()

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.app_env == "development"

    @property
    def notify_email_list(self) -> List[str]:
        """Parse notification emails into a list."""
        if not self.notify_emails:
            return []
        return [email.strip() for email in self.notify_emails.split(",")]

    class Config:
        """Pydantic config."""
        case_sensitive = False


# Global settings instance
settings = Settings()
