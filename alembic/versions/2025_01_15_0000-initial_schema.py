"""Initial database schema

Revision ID: 2025_01_15_0000
Revises:
Create Date: 2025-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2025_01_15_0000'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""

    # Create keywords table
    op.create_table(
        'keywords',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('keyword', sa.String(length=255), nullable=False),
        sa.Column('search_volume', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('competition', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('cpc', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('trend', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('golden_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('naver_monthly_pc_search', sa.Integer(), server_default='0'),
        sa.Column('naver_monthly_mobile_search', sa.Integer(), server_default='0'),
        sa.Column('source', sa.String(length=50), server_default='manual'),
        sa.Column('language', sa.String(length=10), server_default='ko'),
        sa.Column('location', sa.String(length=10), server_default='KR'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_keywords_keyword', 'keywords', ['keyword'], unique=True)
    op.create_index('ix_keywords_id', 'keywords', ['id'], unique=False)
    op.create_index('ix_keywords_golden_score', 'keywords', ['golden_score'], unique=False)
    op.create_index('ix_keywords_golden_score_desc', 'keywords', [sa.text('golden_score DESC')], unique=False)
    op.create_index('ix_keywords_search_volume_desc', 'keywords', [sa.text('search_volume DESC')], unique=False)

    # Create posts table
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('slug', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('meta_description', sa.String(length=160), nullable=True),
        sa.Column('h1_tag', sa.String(length=500), nullable=True),
        sa.Column('word_count', sa.Integer(), server_default='0'),
        sa.Column('internal_links', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('schema_markup', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('faq_schema', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('wp_post_id', sa.Integer(), nullable=True),
        sa.Column('wp_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='draft'),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('categories', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('featured_image_url', sa.String(length=500), nullable=True),
        sa.Column('view_count', sa.Integer(), server_default='0'),
        sa.Column('keyword_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['keyword_id'], ['keywords.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_posts_id', 'posts', ['id'], unique=False)
    op.create_index('ix_posts_title', 'posts', ['title'], unique=False)
    op.create_index('ix_posts_slug', 'posts', ['slug'], unique=True)
    op.create_index('ix_posts_wp_post_id', 'posts', ['wp_post_id'], unique=True)
    op.create_index('ix_posts_status', 'posts', ['status'], unique=False)
    op.create_index('ix_posts_scheduled_for', 'posts', ['scheduled_for'], unique=False)
    op.create_index('ix_posts_keyword_id', 'posts', ['keyword_id'], unique=False)
    op.create_index('ix_posts_status_scheduled', 'posts', ['status', 'scheduled_for'], unique=False)
    op.create_index('ix_posts_published_at_desc', 'posts', [sa.text('published_at DESC')], unique=False)

    # Create images table
    op.create_table(
        'images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('local_path', sa.String(length=500), nullable=True),
        sa.Column('alt_text', sa.String(length=125), nullable=True),
        sa.Column('width', sa.Integer(), server_default='0'),
        sa.Column('height', sa.Integer(), server_default='0'),
        sa.Column('size_kb', sa.Integer(), server_default='0'),
        sa.Column('format', sa.String(length=10), server_default='webp'),
        sa.Column('is_hero', sa.Boolean(), server_default='false'),
        sa.Column('source', sa.String(length=50), server_default='dalle'),
        sa.Column('source_id', sa.String(length=255), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('wp_media_id', sa.Integer(), nullable=True),
        sa.Column('wp_url', sa.String(length=500), nullable=True),
        sa.Column('post_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_images_id', 'images', ['id'], unique=False)
    op.create_index('ix_images_post_id', 'images', ['post_id'], unique=False)
    op.create_index('ix_images_post_id_is_hero', 'images', ['post_id', 'is_hero'], unique=False)

    # Create publish_history table
    op.create_table(
        'publish_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('wp_post_id', sa.Integer(), nullable=True),
        sa.Column('wp_url', sa.String(length=500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('attempted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('attempt_number', sa.Integer(), server_default='1'),
        sa.Column('retry_after', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_publish_history_id', 'publish_history', ['id'], unique=False)
    op.create_index('ix_publish_history_post_id', 'publish_history', ['post_id'], unique=False)
    op.create_index('ix_publish_history_status', 'publish_history', ['status'], unique=False)
    op.create_index('ix_publish_history_status_attempted', 'publish_history', ['status', sa.text('attempted_at DESC')], unique=False)

    # Create scheduled_tasks table
    op.create_table(
        'scheduled_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_name', sa.String(length=255), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('celery_task_id', sa.String(length=255), nullable=True),
        sa.Column('schedule_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('params', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('max_retries', sa.Integer(), server_default='3'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scheduled_tasks_id', 'scheduled_tasks', ['id'], unique=False)
    op.create_index('ix_scheduled_tasks_task_name', 'scheduled_tasks', ['task_name'], unique=False)
    op.create_index('ix_scheduled_tasks_task_type', 'scheduled_tasks', ['task_type'], unique=False)
    op.create_index('ix_scheduled_tasks_celery_task_id', 'scheduled_tasks', ['celery_task_id'], unique=True)
    op.create_index('ix_scheduled_tasks_schedule_time', 'scheduled_tasks', ['schedule_time'], unique=False)
    op.create_index('ix_scheduled_tasks_status', 'scheduled_tasks', ['status'], unique=False)
    op.create_index('ix_scheduled_tasks_status_schedule', 'scheduled_tasks', ['status', 'schedule_time'], unique=False)
    op.create_index('ix_scheduled_tasks_type_status', 'scheduled_tasks', ['task_type', 'status'], unique=False)

    # Create system_config table
    op.create_table(
        'system_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), server_default='general'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_system_config_id', 'system_config', ['id'], unique=False)
    op.create_index('ix_system_config_key', 'system_config', ['key'], unique=True)

    # Create api_logs table
    op.create_table(
        'api_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service', sa.String(length=50), nullable=False),
        sa.Column('endpoint', sa.String(length=255), nullable=True),
        sa.Column('method', sa.String(length=10), nullable=True),
        sa.Column('request_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('response_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.Float(), nullable=True),
        sa.Column('success', sa.Boolean(), server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_api_logs_id', 'api_logs', ['id'], unique=False)
    op.create_index('ix_api_logs_service', 'api_logs', ['service'], unique=False)
    op.create_index('ix_api_logs_success', 'api_logs', ['success'], unique=False)
    op.create_index('ix_api_logs_created_at', 'api_logs', ['created_at'], unique=False)
    op.create_index('ix_api_logs_service_created', 'api_logs', ['service', sa.text('created_at DESC')], unique=False)
    op.create_index('ix_api_logs_success_created', 'api_logs', ['success', sa.text('created_at DESC')], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""

    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('api_logs')
    op.drop_table('system_config')
    op.drop_table('scheduled_tasks')
    op.drop_table('publish_history')
    op.drop_table('images')
    op.drop_table('posts')
    op.drop_table('keywords')
