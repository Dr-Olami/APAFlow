"""
Agent persistence service for SMEFlow multi-tenant architecture.

This module provides database persistence for agent configurations,
lifecycle management, and tenant isolation.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import BaseModel, Field, validator
import structlog

from smeflow.database.connection import get_db_session
from smeflow.database.models import Agent as AgentModel, Tenant
from smeflow.agents.base import AgentConfig, AgentType, AgentStatus
from smeflow.core.logging import get_logger

logger = get_logger(__name__)


class AgentPersistenceConfig(BaseModel):
    """
    Pydantic model for agent configuration persistence.
    
    This model handles serialization/deserialization of agent configurations
    to/from the database JSONB field with proper validation.
    """
    
    # Core configuration
    agent_type: AgentType
    llm_provider: str = Field(..., min_length=1)
    llm_model: str = Field(..., min_length=1)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    
    # Agent-specific settings
    tools: List[str] = Field(default_factory=list)
    system_prompt: Optional[str] = None
    custom_prompts: Dict[str, str] = Field(default_factory=dict)
    
    # African market optimizations
    region: str = Field("NG", pattern=r"^[A-Z]{2}$")
    timezone: str = Field("Africa/Lagos")
    languages: List[str] = Field(default_factory=lambda: ["en"])
    currency: str = Field("NGN", pattern=r"^[A-Z]{3}$")
    
    # Performance settings
    timeout_seconds: int = Field(30, gt=0, le=300)
    max_retries: int = Field(3, ge=0, le=10)
    enable_caching: bool = True
    
    # Tenant-specific settings
    tenant_settings: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('tools')
    def validate_tools_for_automator(cls, v, values):
        """Validate that automator agents have tools."""
        if values.get('agent_type') == AgentType.AUTOMATOR and not v:
            raise ValueError("Automator agents must have at least one tool")
        return v
    
    @validator('languages')
    def validate_languages(cls, v):
        """Validate language codes."""
        valid_languages = {
            'en', 'sw', 'ha', 'yo', 'ig', 'am', 'fr', 'ar', 'pt'  # African languages
        }
        for lang in v:
            if lang not in valid_languages:
                raise ValueError(f"Unsupported language: {lang}")
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class AgentPersistenceData(BaseModel):
    """
    Complete agent data model for persistence operations.
    """
    
    id: Optional[uuid.UUID] = None
    tenant_id: str
    name: str
    description: Optional[str] = None
    agent_type: AgentType
    status: AgentStatus = AgentStatus.INACTIVE
    config: AgentPersistenceConfig
    prompts: Dict[str, str] = Field(default_factory=dict)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class AgentPersistenceService:
    """
    Service for agent persistence operations with multi-tenant isolation.
    
    Provides CRUD operations for agent configurations with proper tenant
    isolation, validation, and error handling.
    """
    
    def __init__(self):
        """Initialize the persistence service."""
        self.logger = structlog.get_logger(__name__)
    
    def create_agent(
        self, 
        agent_data: AgentPersistenceData,
        db: Optional[Session] = None
    ) -> AgentPersistenceData:
        """
        Create a new agent in the database.
        
        Args:
            agent_data: Agent data to persist
            db: Optional database session
            
        Returns:
            Created agent data with generated ID and timestamps
            
        Raises:
            ValueError: If tenant doesn't exist or validation fails
            IntegrityError: If agent name conflicts within tenant
        """
        should_close_db = db is None
        if db is None:
            db = get_db_session()
        
        try:
            # Validate tenant exists
            tenant = db.query(Tenant).filter(Tenant.id == agent_data.tenant_id).first()
            if not tenant:
                raise ValueError(f"Tenant {agent_data.tenant_id} not found")
            
            # Check for name conflicts within tenant
            existing = db.query(AgentModel).filter(
                AgentModel.tenant_id == agent_data.tenant_id,
                AgentModel.name == agent_data.name,
                AgentModel.is_active == True
            ).first()
            
            if existing:
                raise IntegrityError(
                    f"Agent with name '{agent_data.name}' already exists for tenant {agent_data.tenant_id}",
                    None, None
                )
            
            # Create database model
            db_agent = AgentModel(
                tenant_id=agent_data.tenant_id,
                name=agent_data.name,
                type=agent_data.agent_type if isinstance(agent_data.agent_type, str) else agent_data.agent_type.value,
                description=agent_data.description,
                config=agent_data.config.model_dump(),
                prompts=agent_data.prompts,
                is_active=agent_data.is_active
            )
            
            db.add(db_agent)
            db.commit()
            db.refresh(db_agent)
            
            # Convert back to persistence data
            result = self._db_model_to_persistence_data(db_agent)
            
            self.logger.info(
                "Agent created successfully",
                agent_id=str(result.id),
                tenant_id=agent_data.tenant_id,
                agent_type=agent_data.agent_type if isinstance(agent_data.agent_type, str) else agent_data.agent_type.value
            )
            
            return result
            
        except (IntegrityError, ValueError) as e:
            db.rollback()
            raise e
        except SQLAlchemyError as e:
            db.rollback()
            self.logger.error("Database error creating agent", error=str(e))
            raise ValueError(f"Failed to create agent: {str(e)}")
        finally:
            if should_close_db:
                db.close()
    
    def get_agent(
        self, 
        agent_id: uuid.UUID, 
        tenant_id: str,
        db: Optional[Session] = None
    ) -> Optional[AgentPersistenceData]:
        """
        Retrieve an agent by ID with tenant isolation.
        
        Args:
            agent_id: Agent UUID
            tenant_id: Tenant ID for isolation
            db: Optional database session
            
        Returns:
            Agent data if found, None otherwise
        """
        should_close_db = db is None
        if db is None:
            db = get_db_session()
        
        try:
            db_agent = db.query(AgentModel).filter(
                AgentModel.id == agent_id,
                AgentModel.tenant_id == tenant_id,
                AgentModel.is_active == True
            ).first()
            
            if not db_agent:
                return None
            
            return self._db_model_to_persistence_data(db_agent)
            
        except SQLAlchemyError as e:
            self.logger.error("Database error retrieving agent", error=str(e))
            return None
        finally:
            if should_close_db:
                db.close()
    
    def list_agents(
        self, 
        tenant_id: str,
        agent_type: Optional[AgentType] = None,
        active_only: bool = True,
        db: Optional[Session] = None
    ) -> List[AgentPersistenceData]:
        """
        List agents for a tenant with optional filtering.
        
        Args:
            tenant_id: Tenant ID for isolation
            agent_type: Optional agent type filter
            active_only: Whether to include only active agents
            db: Optional database session
            
        Returns:
            List of agent data
        """
        should_close_db = db is None
        if db is None:
            db = get_db_session()
        
        try:
            query = db.query(AgentModel).filter(AgentModel.tenant_id == tenant_id)
            
            if agent_type:
                query = query.filter(AgentModel.type == agent_type.value)
            
            if active_only:
                query = query.filter(AgentModel.is_active == True)
            
            db_agents = query.order_by(AgentModel.created_at.desc()).all()
            
            return [self._db_model_to_persistence_data(agent) for agent in db_agents]
            
        except SQLAlchemyError as e:
            self.logger.error("Database error listing agents", error=str(e))
            return []
        finally:
            if should_close_db:
                db.close()
    
    def update_agent(
        self, 
        agent_id: uuid.UUID, 
        tenant_id: str,
        updates: Dict[str, Any],
        db: Optional[Session] = None
    ) -> Optional[AgentPersistenceData]:
        """
        Update an agent configuration.
        
        Args:
            agent_id: Agent UUID
            tenant_id: Tenant ID for isolation
            updates: Dictionary of fields to update
            db: Optional database session
            
        Returns:
            Updated agent data if successful, None if not found
            
        Raises:
            ValueError: If validation fails
        """
        should_close_db = db is None
        if db is None:
            db = get_db_session()
        
        try:
            # Get existing agent
            db_agent = db.query(AgentModel).filter(
                AgentModel.id == agent_id,
                AgentModel.tenant_id == tenant_id,
                AgentModel.is_active == True
            ).first()
            
            if not db_agent:
                return None
            
            # Validate and apply updates
            for field, value in updates.items():
                if field == 'config':
                    # Validate configuration
                    if isinstance(value, dict):
                        config = AgentPersistenceConfig(**value)
                        db_agent.config = config.dict()
                    else:
                        raise ValueError(f"Invalid config format: {type(value)}")
                elif field in ['name', 'description', 'prompts']:
                    setattr(db_agent, field, value)
                elif field == 'is_active':
                    db_agent.is_active = bool(value)
                else:
                    raise ValueError(f"Cannot update field: {field}")
            
            db_agent.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_agent)
            
            result = self._db_model_to_persistence_data(db_agent)
            
            self.logger.info(
                "Agent updated successfully",
                agent_id=str(agent_id),
                tenant_id=tenant_id,
                updated_fields=list(updates.keys())
            )
            
            return result
            
        except ValueError as e:
            db.rollback()
            raise e
        except SQLAlchemyError as e:
            db.rollback()
            self.logger.error("Database error updating agent", error=str(e))
            raise ValueError(f"Failed to update agent: {str(e)}")
        finally:
            if should_close_db:
                db.close()
    
    def delete_agent(
        self, 
        agent_id: uuid.UUID, 
        tenant_id: str,
        soft_delete: bool = True,
        db: Optional[Session] = None
    ) -> bool:
        """
        Delete an agent (soft delete by default).
        
        Args:
            agent_id: Agent UUID
            tenant_id: Tenant ID for isolation
            soft_delete: Whether to soft delete (set is_active=False)
            db: Optional database session
            
        Returns:
            True if deleted successfully, False if not found
        """
        should_close_db = db is None
        if db is None:
            db = get_db_session()
        
        try:
            db_agent = db.query(AgentModel).filter(
                AgentModel.id == agent_id,
                AgentModel.tenant_id == tenant_id
            ).first()
            
            if not db_agent:
                return False
            
            if soft_delete:
                db_agent.is_active = False
                db_agent.updated_at = datetime.utcnow()
            else:
                db.delete(db_agent)
            
            db.commit()
            
            self.logger.info(
                "Agent deleted successfully",
                agent_id=str(agent_id),
                tenant_id=tenant_id,
                soft_delete=soft_delete
            )
            
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            self.logger.error("Database error deleting agent", error=str(e))
            return False
        finally:
            if should_close_db:
                db.close()
    
    def _db_model_to_persistence_data(self, db_agent: AgentModel) -> AgentPersistenceData:
        """
        Convert database model to persistence data.
        
        Args:
            db_agent: Database agent model
            
        Returns:
            Agent persistence data
        """
        # Convert config dict to AgentPersistenceConfig
        config = AgentPersistenceConfig(**db_agent.config)
        
        return AgentPersistenceData(
            id=db_agent.id,
            tenant_id=db_agent.tenant_id,
            name=db_agent.name,
            description=db_agent.description,
            agent_type=AgentType(db_agent.type),
            status=AgentStatus.ACTIVE if db_agent.is_active else AgentStatus.INACTIVE,
            config=config,
            prompts=db_agent.prompts or {},
            is_active=db_agent.is_active,
            created_at=db_agent.created_at,
            updated_at=db_agent.updated_at
        )


# Global persistence service instance
agent_persistence_service = AgentPersistenceService()
