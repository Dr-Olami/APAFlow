"""Add n8N credentials table

Revision ID: 003_add_n8n_credentials_table
Revises: 002_add_workflow_templates
Create Date: 2025-10-04 12:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_n8n_credentials_table'
down_revision = '002_add_workflow_templates'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add n8N credentials table with multi-tenant isolation."""
    op.create_table(
        'n8n_credentials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('credential_name', sa.String(255), nullable=False),
        sa.Column('service_type', sa.String(100), nullable=False),
        sa.Column('encrypted_data', sa.Text, nullable=False),
        sa.Column('credential_metadata', postgresql.JSONB, default={}),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
    )
    
    # Create indexes for performance
    op.create_index('idx_n8n_credentials_tenant_id', 'n8n_credentials', ['tenant_id'])
    op.create_index('idx_n8n_credentials_service_type', 'n8n_credentials', ['service_type'])
    op.create_index('idx_n8n_credentials_active', 'n8n_credentials', ['is_active'])
    op.create_index('idx_n8n_credentials_tenant_name', 'n8n_credentials', ['tenant_id', 'credential_name'])
    
    # Create unique constraint for active credentials per tenant
    op.create_index(
        'idx_n8n_credentials_unique_active',
        'n8n_credentials',
        ['tenant_id', 'credential_name'],
        unique=True,
        postgresql_where=sa.text('is_active = true')
    )


def downgrade() -> None:
    """Remove n8N credentials table."""
    op.drop_table('n8n_credentials')
