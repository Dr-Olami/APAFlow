"""Add template versioning system

Revision ID: 002_add_template_versioning
Revises: 001_initial_schema
Create Date: 2025-01-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_template_versioning'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add workflow template versioning tables."""
    # Create workflow_templates table
    op.create_table('workflow_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('industry_type', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('supported_regions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('supported_currencies', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('supported_languages', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('industry_type', name='uq_template_industry')
    )
    op.create_index(op.f('ix_workflow_templates_industry_type'), 'workflow_templates', ['industry_type'], unique=False)

    # Create workflow_template_versions table
    op.create_table('workflow_template_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=True),
        sa.Column('is_deprecated', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('changelog', sa.Text(), nullable=True),
        sa.Column('breaking_changes', sa.Boolean(), nullable=True),
        sa.Column('migration_notes', sa.Text(), nullable=True),
        sa.Column('template_definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['template_id'], ['workflow_templates.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('template_id', 'version', name='uq_template_version')
    )
    op.create_index(op.f('ix_workflow_template_versions_template_id'), 'workflow_template_versions', ['template_id'], unique=False)


def downgrade() -> None:
    """Remove workflow template versioning tables."""
    op.drop_index(op.f('ix_workflow_template_versions_template_id'), table_name='workflow_template_versions')
    op.drop_table('workflow_template_versions')
    op.drop_index(op.f('ix_workflow_templates_industry_type'), table_name='workflow_templates')
    op.drop_table('workflow_templates')
