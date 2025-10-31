"""add multi-blog management tables

Revision ID: 2025_10_31_0003
Revises: 2025_01_31_0002
Create Date: 2025-10-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_10_31_0003'
down_revision = '2025_01_31_0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create wordpress_sites table
    op.create_table(
        'wordpress_sites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('api_url', sa.String(length=500), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('app_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('default_category', sa.String(length=100), server_default='Uncategorized'),
        sa.Column('default_tags', sa.JSON(), nullable=True),
        sa.Column('auto_publish', sa.Boolean(), server_default='false'),
        sa.Column('publish_delay_minutes', sa.Integer(), server_default='0'),
        sa.Column('total_posts_published', sa.Integer(), server_default='0'),
        sa.Column('last_published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('language', sa.String(length=10), server_default='ko'),
        sa.Column('timezone', sa.String(length=50), server_default='Asia/Seoul'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for wordpress_sites
    op.create_index('ix_wordpress_sites_id', 'wordpress_sites', ['id'])
    op.create_index('ix_wordpress_sites_name', 'wordpress_sites', ['name'])
    op.create_index('ix_wordpress_sites_is_active', 'wordpress_sites', ['is_active'])

    # Create site_posts table
    op.create_table(
        'site_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('wp_post_id', sa.Integer(), nullable=True),
        sa.Column('wp_url', sa.String(length=500), nullable=True),
        sa.Column('wp_status', sa.String(length=20), server_default='draft'),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('max_retries', sa.Integer(), server_default='3'),
        sa.Column('views', sa.Integer(), server_default='0'),
        sa.Column('clicks', sa.Integer(), server_default='0'),
        sa.Column('conversions', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['wordpress_sites.id'], ),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for site_posts
    op.create_index('ix_site_posts_id', 'site_posts', ['id'])
    op.create_index('ix_site_posts_site_id', 'site_posts', ['site_id'])
    op.create_index('ix_site_posts_post_id', 'site_posts', ['post_id'])
    op.create_index('ix_site_posts_wp_post_id', 'site_posts', ['wp_post_id'])
    op.create_index('ix_site_posts_status', 'site_posts', ['status'])
    op.create_index('ix_site_posts_site_status', 'site_posts', ['site_id', 'status'])
    op.create_index('ix_site_posts_scheduled', 'site_posts', ['scheduled_for'])


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop indexes for site_posts
    op.drop_index('ix_site_posts_scheduled', table_name='site_posts')
    op.drop_index('ix_site_posts_site_status', table_name='site_posts')
    op.drop_index('ix_site_posts_status', table_name='site_posts')
    op.drop_index('ix_site_posts_wp_post_id', table_name='site_posts')
    op.drop_index('ix_site_posts_post_id', table_name='site_posts')
    op.drop_index('ix_site_posts_site_id', table_name='site_posts')
    op.drop_index('ix_site_posts_id', table_name='site_posts')

    # Drop site_posts table
    op.drop_table('site_posts')

    # Drop indexes for wordpress_sites
    op.drop_index('ix_wordpress_sites_is_active', table_name='wordpress_sites')
    op.drop_index('ix_wordpress_sites_name', table_name='wordpress_sites')
    op.drop_index('ix_wordpress_sites_id', table_name='wordpress_sites')

    # Drop wordpress_sites table
    op.drop_table('wordpress_sites')
