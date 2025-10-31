"""add seo_scores table

Revision ID: 2025_01_31_0002
Revises: 2025_01_31_0001
Create Date: 2025-01-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_01_31_0002'
down_revision = '2025_01_31_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create seo_scores table
    op.create_table(
        'seo_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('grade', sa.String(length=5), nullable=True),
        sa.Column('keyword_density_score', sa.Float(), nullable=False),
        sa.Column('title_optimization_score', sa.Float(), nullable=False),
        sa.Column('meta_tags_score', sa.Float(), nullable=False),
        sa.Column('readability_score', sa.Float(), nullable=False),
        sa.Column('internal_links_score', sa.Float(), nullable=False),
        sa.Column('image_alt_score', sa.Float(), nullable=False),
        sa.Column('issues', sa.JSON(), nullable=True),
        sa.Column('suggestions', sa.JSON(), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('target_keyword', sa.String(length=255), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('analyzer_version', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_seo_scores_id', 'seo_scores', ['id'])
    op.create_index('ix_seo_scores_post_id', 'seo_scores', ['post_id'], unique=True)
    op.create_index('ix_seo_scores_overall_score', 'seo_scores', ['overall_score'])
    op.create_index('ix_seo_scores_overall_score_desc', 'seo_scores', [sa.text('overall_score DESC')])
    op.create_index('ix_seo_scores_post_id_analyzed', 'seo_scores', ['post_id', sa.text('analyzed_at DESC')])


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop indexes
    op.drop_index('ix_seo_scores_post_id_analyzed', table_name='seo_scores')
    op.drop_index('ix_seo_scores_overall_score_desc', table_name='seo_scores')
    op.drop_index('ix_seo_scores_overall_score', table_name='seo_scores')
    op.drop_index('ix_seo_scores_post_id', table_name='seo_scores')
    op.drop_index('ix_seo_scores_id', table_name='seo_scores')

    # Drop table
    op.drop_table('seo_scores')
