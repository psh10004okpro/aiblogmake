"""add workflow_runs table

Revision ID: 2025_01_31_0001
Revises: 2025_01_15_0000
Create Date: 2025-01-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_01_31_0001'
down_revision = '2025_01_15_0000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create workflow_runs table
    op.create_table(
        'workflow_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_type', sa.String(length=50), nullable=False),
        sa.Column('celery_task_id', sa.String(length=255), nullable=True),
        sa.Column('seed_keywords', sa.JSON(), nullable=True),
        sa.Column('num_posts', sa.Integer(), nullable=True),
        sa.Column('publish_immediately', sa.Boolean(), nullable=True),
        sa.Column('llm_provider', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('current_step', sa.String(length=50), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), nullable=True),
        sa.Column('steps', sa.JSON(), nullable=True),
        sa.Column('keywords_researched', sa.Integer(), nullable=True),
        sa.Column('posts_created', sa.Integer(), nullable=True),
        sa.Column('posts_published', sa.Integer(), nullable=True),
        sa.Column('errors_count', sa.Integer(), nullable=True),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.Column('errors', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_workflow_runs_id', 'workflow_runs', ['id'])
    op.create_index('ix_workflow_runs_workflow_type', 'workflow_runs', ['workflow_type'])
    op.create_index('ix_workflow_runs_celery_task_id', 'workflow_runs', ['celery_task_id'], unique=True)
    op.create_index('ix_workflow_runs_status', 'workflow_runs', ['status'])
    op.create_index('ix_workflow_runs_status_created', 'workflow_runs', ['status', sa.text('created_at DESC')])
    op.create_index('ix_workflow_runs_type_status', 'workflow_runs', ['workflow_type', 'status'])


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop indexes
    op.drop_index('ix_workflow_runs_type_status', table_name='workflow_runs')
    op.drop_index('ix_workflow_runs_status_created', table_name='workflow_runs')
    op.drop_index('ix_workflow_runs_status', table_name='workflow_runs')
    op.drop_index('ix_workflow_runs_celery_task_id', table_name='workflow_runs')
    op.drop_index('ix_workflow_runs_workflow_type', table_name='workflow_runs')
    op.drop_index('ix_workflow_runs_id', table_name='workflow_runs')

    # Drop table
    op.drop_table('workflow_runs')
