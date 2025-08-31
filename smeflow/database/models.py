"""
Database models for SMEFlow multi-tenant architecture.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
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
