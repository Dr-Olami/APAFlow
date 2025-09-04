"""
Database models for SMEFlow multi-tenant architecture.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey,
    JSON, Index, UniqueConstraint, CheckConstraint, Numeric, Float
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from smeflow.database.connection import Base


class Tenant(Base):
    """
    Tenant model for multi-tenancy support.
    """
    __tablename__ = "tenants"
    
    id: Mapped[str] = mapped_column(
        String(50), primary_key=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str] = mapped_column(String(10), nullable=False, default="NG")
    subscription_tier: Mapped[str] = mapped_column(
        String(20), nullable=False, default="free"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Metadata
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="tenant", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="tenant", cascade="all, delete-orphan")
    llm_usage = relationship("LLMUsage", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """
    User model with tenant association.
    """
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("tenants.id"), nullable=False, index=True
    )
    keycloak_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_tenant_user_email"),
    )


class Agent(Base):
    """
    Agent model for AI agents within tenants.
    """
    __tablename__ = "agents"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("tenants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # automator, mentor, supervisor
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Configuration
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    prompts: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="agents")
    executions = relationship("AgentExecution", back_populates="agent", cascade="all, delete-orphan")
    llm_usage = relationship("LLMUsage", back_populates="agent")


class Workflow(Base):
    """
    Workflow model for LangGraph workflows.
    """
    __tablename__ = "workflows"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("tenants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    template_type: Mapped[Optional[str]] = mapped_column(String(100))  # product_recommender, local_discovery, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Workflow definition
    definition: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="workflows")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")


class AgentExecution(Base):
    """
    Agent execution tracking for observability.
    """
    __tablename__ = "agent_executions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # running, completed, failed
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Execution data
    input_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    output_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # LLM usage tracking
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float)
    
    # Relationships
    agent = relationship("Agent", back_populates="executions")


class WorkflowExecution(Base):
    """
    Workflow execution tracking.
    """
    __tablename__ = "workflow_executions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True
    )
    trigger: Mapped[str] = mapped_column(String(100), nullable=False)  # manual, scheduled, webhook
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Execution data
    input_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    output_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")


class Integration(Base):
    """
    Integration configuration for external services.
    """
    __tablename__ = "integrations"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("tenants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)  # mpesa, paystack, jumia, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Configuration (encrypted)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider", name="uq_tenant_integration_provider"),
    )


class LLMUsage(Base):
    """
    LLM usage tracking for cost monitoring and analytics.
    """
    __tablename__ = "llm_usage"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("tenants.id"), nullable=False, index=True
    )
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True, index=True
    )
    
    # LLM provider details
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # openai, anthropic
    model: Mapped[str] = mapped_column(String(100), nullable=False)  # gpt-4o, claude-3-sonnet
    
    # Token usage
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Cost tracking
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    cost_local: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))  # NGN, KES, etc.
    currency: Mapped[str] = mapped_column(String(3), default="USD")  # USD, NGN, KES
    
    # Performance metrics
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Request metadata
    request_hash: Mapped[Optional[str]] = mapped_column(String(64))  # For cache matching
    region: Mapped[str] = mapped_column(String(10), default="NG")  # African region
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    
    # Relationships
    agent = relationship("Agent", back_populates="llm_usage")
    tenant = relationship("Tenant", back_populates="llm_usage")


class LLMCache(Base):
    """
    LLM response caching for cost optimization.
    """
    __tablename__ = "llm_cache"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cache_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("tenants.id"), nullable=True, index=True
    )  # NULL for global cache
    
    # Cache content
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    response_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Provider details
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Cache metadata
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProviderHealth(Base):
    """
    LLM provider health monitoring for fallback decisions.
    """
    __tablename__ = "provider_health"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    region: Mapped[str] = mapped_column(String(10), nullable=False)  # NG, KE, ZA, etc.
    
    # Health metrics
    is_healthy: Mapped[bool] = mapped_column(Boolean, default=True)
    response_time_avg: Mapped[Optional[int]] = mapped_column(Integer)  # milliseconds
    error_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))  # percentage (0.0-1.0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status tracking
    last_success: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_check: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    __table_args__ = (
        UniqueConstraint("provider", "region", name="uq_provider_region_health"),
    )


class WorkflowTemplate(Base):
    """
    Workflow template model for versioned template management.
    """
    __tablename__ = "workflow_templates"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    industry_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Template metadata
    supported_regions: Mapped[list] = mapped_column(JSONB, default=list)
    supported_currencies: Mapped[list] = mapped_column(JSONB, default=list)
    supported_languages: Mapped[list] = mapped_column(JSONB, default=list)
    
    # Relationships
    versions = relationship("WorkflowTemplateVersion", back_populates="template", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("industry_type", name="uq_template_industry"),
    )


class WorkflowTemplateVersion(Base):
    """
    Workflow template version model for template versioning system.
    """
    __tablename__ = "workflow_template_versions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_templates.id"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "1.0.0", "1.1.0"
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deprecated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Version metadata
    changelog: Mapped[Optional[str]] = mapped_column(Text)
    breaking_changes: Mapped[bool] = mapped_column(Boolean, default=False)
    migration_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Template definition
    template_definition: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Relationships
    template = relationship("WorkflowTemplate", back_populates="versions")
    
    __table_args__ = (
        UniqueConstraint("template_id", "version", name="uq_template_version"),
    )


class AuditLog(Base):
    """
    Audit log for compliance tracking.
    """
    __tablename__ = "audit_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("tenants.id"), nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    
    # Event data
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
