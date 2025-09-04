"""
Agent lifecycle management API routes for SMEFlow.

Provides REST endpoints for agent CRUD operations with multi-tenant isolation
and comprehensive validation.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, validator
import structlog

from smeflow.agents.manager import AgentManager
from smeflow.agents.persistence import AgentPersistenceData, AgentPersistenceConfig
from smeflow.agents.base import AgentType, AgentStatus
from smeflow.auth.tenant_auth import get_current_tenant
from smeflow.core.logging import get_logger

logger = get_logger(__name__)
security = HTTPBearer()

# Initialize router
router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


class CreateAgentRequest(BaseModel):
    """Request model for creating an agent."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    agent_type: AgentType
    
    # LLM Configuration
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
    
    # Optional grouping
    group: Optional[str] = None
    
    @validator('tools')
    def validate_tools_for_automator(cls, v, values):
        """Validate that automator agents have tools."""
        if values.get('agent_type') == AgentType.AUTOMATOR and not v:
            raise ValueError("Automator agents must have at least one tool")
        return v

    class Config:
        use_enum_values = True


class UpdateAgentRequest(BaseModel):
    """Request model for updating an agent."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    
    # LLM Configuration updates
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    
    # Agent-specific settings updates
    tools: Optional[List[str]] = None
    system_prompt: Optional[str] = None
    custom_prompts: Optional[Dict[str, str]] = None
    
    # Performance settings updates
    timeout_seconds: Optional[int] = Field(None, gt=0, le=300)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    enable_caching: Optional[bool] = None


class AgentResponse(BaseModel):
    """Response model for agent data."""
    
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    agent_type: AgentType
    status: AgentStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Configuration summary
    llm_provider: str
    llm_model: str
    region: str
    languages: List[str]
    
    class Config:
        use_enum_values = True


class AgentListResponse(BaseModel):
    """Response model for agent list."""
    
    agents: List[AgentResponse]
    total: int
    page: int
    page_size: int


# Global agent managers cache (tenant_id -> AgentManager)
_agent_managers: Dict[str, AgentManager] = {}


def get_agent_manager(tenant_id: str) -> AgentManager:
    """
    Get or create agent manager for tenant.
    
    Args:
        tenant_id: Tenant identifier
        
    Returns:
        Agent manager instance
    """
    if tenant_id not in _agent_managers:
        _agent_managers[tenant_id] = AgentManager(tenant_id=tenant_id)
    return _agent_managers[tenant_id]


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(
    request: CreateAgentRequest,
    tenant_id: str = Depends(get_current_tenant),
    token: str = Depends(security)
) -> AgentResponse:
    """
    Create a new agent for the tenant.
    
    Args:
        request: Agent creation request
        tenant_id: Current tenant ID
        token: Authentication token
        
    Returns:
        Created agent data
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        # Get agent manager for tenant
        manager = get_agent_manager(tenant_id)
        
        # Convert request to config dict
        config_dict = {
            "name": request.name,
            "description": request.description,
            "agent_type": request.agent_type,
            "llm_provider": request.llm_provider,
            "llm_model": request.llm_model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "tools": request.tools,
            "system_prompt": request.system_prompt,
            "prompts": request.custom_prompts,
            "region": request.region,
            "timezone": request.timezone,
            "languages": request.languages,
            "currency": request.currency,
            "timeout_seconds": request.timeout_seconds,
            "max_retries": request.max_retries,
            "enable_caching": request.enable_caching,
            "tenant_id": tenant_id
        }
        
        # Create agent
        agent_id = await manager.create_agent(
            config=config_dict,
            group=request.group,
            persist=True
        )
        
        # Get created agent for response
        agent = manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=500, detail="Failed to retrieve created agent")
        
        # Convert to response format
        response = AgentResponse(
            id=agent.agent_id,
            tenant_id=agent.config.tenant_id,
            name=request.name,
            description=request.description,
            agent_type=agent.config.agent_type,
            status=agent.status,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            llm_provider=agent.config.llm_provider,
            llm_model=agent.config.llm_model,
            region=agent.config.region,
            languages=agent.config.languages
        )
        
        logger.info(
            "Agent created via API",
            agent_id=agent_id,
            tenant_id=tenant_id,
            agent_type=request.agent_type.value
        )
        
        return response
        
    except ValueError as e:
        logger.warning("Invalid agent configuration", error=str(e), tenant_id=tenant_id)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create agent via API", error=str(e), tenant_id=tenant_id)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    agent_type: Optional[AgentType] = Query(None, description="Filter by agent type"),
    active_only: bool = Query(True, description="Include only active agents"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    tenant_id: str = Depends(get_current_tenant),
    token: str = Depends(security)
) -> AgentListResponse:
    """
    List agents for the tenant with optional filtering and pagination.
    
    Args:
        agent_type: Optional agent type filter
        active_only: Whether to include only active agents
        page: Page number (1-based)
        page_size: Number of agents per page
        tenant_id: Current tenant ID
        token: Authentication token
        
    Returns:
        Paginated list of agents
    """
    try:
        # Get agent manager for tenant
        manager = get_agent_manager(tenant_id)
        
        # Get all agents from persistence
        from smeflow.agents.persistence import agent_persistence_service
        
        persisted_agents = agent_persistence_service.list_agents(
            tenant_id=tenant_id,
            agent_type=agent_type,
            active_only=active_only
        )
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_agents = persisted_agents[start_idx:end_idx]
        
        # Convert to response format
        agent_responses = []
        for agent_data in paginated_agents:
            response = AgentResponse(
                id=str(agent_data.id),
                tenant_id=agent_data.tenant_id,
                name=agent_data.name,
                description=agent_data.description,
                agent_type=agent_data.agent_type,
                status=agent_data.status,
                is_active=agent_data.is_active,
                created_at=agent_data.created_at,
                updated_at=agent_data.updated_at,
                llm_provider=agent_data.config.llm_provider,
                llm_model=agent_data.config.llm_model,
                region=agent_data.config.region,
                languages=agent_data.config.languages
            )
            agent_responses.append(response)
        
        return AgentListResponse(
            agents=agent_responses,
            total=len(persisted_agents),
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error("Failed to list agents via API", error=str(e), tenant_id=tenant_id)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str = Path(..., description="Agent ID"),
    tenant_id: str = Depends(get_current_tenant),
    token: str = Depends(security)
) -> AgentResponse:
    """
    Get a specific agent by ID.
    
    Args:
        agent_id: Agent identifier
        tenant_id: Current tenant ID
        token: Authentication token
        
    Returns:
        Agent data
        
    Raises:
        HTTPException: If agent not found
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(agent_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent ID format")
        
        # Get agent from persistence
        from smeflow.agents.persistence import agent_persistence_service
        
        agent_data = agent_persistence_service.get_agent(
            agent_id=uuid.UUID(agent_id),
            tenant_id=tenant_id
        )
        
        if not agent_data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Convert to response format
        response = AgentResponse(
            id=str(agent_data.id),
            tenant_id=agent_data.tenant_id,
            name=agent_data.name,
            description=agent_data.description,
            agent_type=agent_data.agent_type,
            status=agent_data.status,
            is_active=agent_data.is_active,
            created_at=agent_data.created_at,
            updated_at=agent_data.updated_at,
            llm_provider=agent_data.config.llm_provider,
            llm_model=agent_data.config.llm_model,
            region=agent_data.config.region,
            languages=agent_data.config.languages
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get agent via API", error=str(e), agent_id=agent_id, tenant_id=tenant_id)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    request: UpdateAgentRequest,
    tenant_id: str = Depends(get_current_tenant),
    token: str = Depends(security)
) -> AgentResponse:
    """
    Update an agent configuration.
    
    Args:
        agent_id: Agent identifier
        request: Agent update request
        tenant_id: Current tenant ID
        token: Authentication token
        
    Returns:
        Updated agent data
        
    Raises:
        HTTPException: If agent not found or update fails
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(agent_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent ID format")
        
        # Get agent manager for tenant
        manager = get_agent_manager(tenant_id)
        
        # Build update dictionary (only include non-None values)
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.llm_provider is not None:
            updates["llm_provider"] = request.llm_provider
        if request.llm_model is not None:
            updates["llm_model"] = request.llm_model
        if request.temperature is not None:
            updates["temperature"] = request.temperature
        if request.max_tokens is not None:
            updates["max_tokens"] = request.max_tokens
        if request.tools is not None:
            updates["tools"] = request.tools
        if request.system_prompt is not None:
            updates["system_prompt"] = request.system_prompt
        if request.custom_prompts is not None:
            updates["prompts"] = request.custom_prompts
        if request.timeout_seconds is not None:
            updates["timeout_seconds"] = request.timeout_seconds
        if request.max_retries is not None:
            updates["max_retries"] = request.max_retries
        if request.enable_caching is not None:
            updates["enable_caching"] = request.enable_caching
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        # Update agent
        success = await manager.update_agent_config(
            agent_id=agent_id,
            config_updates=updates,
            persist=True
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get updated agent for response
        from smeflow.agents.persistence import agent_persistence_service
        
        agent_data = agent_persistence_service.get_agent(
            agent_id=uuid.UUID(agent_id),
            tenant_id=tenant_id
        )
        
        if not agent_data:
            raise HTTPException(status_code=404, detail="Agent not found after update")
        
        # Convert to response format
        response = AgentResponse(
            id=str(agent_data.id),
            tenant_id=agent_data.tenant_id,
            name=agent_data.name,
            description=agent_data.description,
            agent_type=agent_data.agent_type,
            status=agent_data.status,
            is_active=agent_data.is_active,
            created_at=agent_data.created_at,
            updated_at=agent_data.updated_at,
            llm_provider=agent_data.config.llm_provider,
            llm_model=agent_data.config.llm_model,
            region=agent_data.config.region,
            languages=agent_data.config.languages
        )
        
        logger.info(
            "Agent updated via API",
            agent_id=agent_id,
            tenant_id=tenant_id,
            updates=list(updates.keys())
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update agent via API", error=str(e), agent_id=agent_id, tenant_id=tenant_id)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    soft_delete: bool = Query(True, description="Whether to soft delete (deactivate) the agent"),
    tenant_id: str = Depends(get_current_tenant),
    token: str = Depends(security)
) -> None:
    """
    Delete an agent.
    
    Args:
        agent_id: Agent identifier
        soft_delete: Whether to soft delete (deactivate) or hard delete
        tenant_id: Current tenant ID
        token: Authentication token
        
    Raises:
        HTTPException: If agent not found or deletion fails
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(agent_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent ID format")
        
        # Get agent manager for tenant
        manager = get_agent_manager(tenant_id)
        
        # Delete agent
        success = await manager.delete_agent(
            agent_id=agent_id,
            soft_delete=soft_delete,
            persist=True
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        logger.info(
            "Agent deleted via API",
            agent_id=agent_id,
            tenant_id=tenant_id,
            soft_delete=soft_delete
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete agent via API", error=str(e), agent_id=agent_id, tenant_id=tenant_id)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{agent_id}/activate", response_model=AgentResponse)
async def activate_agent(
    agent_id: str,
    tenant_id: str = Depends(get_current_tenant),
    token: str = Depends(security)
) -> AgentResponse:
    """
    Activate an agent.
    
    Args:
        agent_id: Agent identifier
        tenant_id: Current tenant ID
        token: Authentication token
        
    Returns:
        Updated agent data
        
    Raises:
        HTTPException: If agent not found or activation fails
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(agent_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent ID format")
        
        # Get agent manager for tenant
        manager = get_agent_manager(tenant_id)
        
        # Start agent
        success = await manager.start_agent(agent_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found or failed to activate")
        
        # Get updated agent for response
        from smeflow.agents.persistence import agent_persistence_service
        
        agent_data = agent_persistence_service.get_agent(
            agent_id=uuid.UUID(agent_id),
            tenant_id=tenant_id
        )
        
        if not agent_data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Convert to response format
        response = AgentResponse(
            id=str(agent_data.id),
            tenant_id=agent_data.tenant_id,
            name=agent_data.name,
            description=agent_data.description,
            agent_type=agent_data.agent_type,
            status=AgentStatus.ACTIVE,  # Should be active after start
            is_active=agent_data.is_active,
            created_at=agent_data.created_at,
            updated_at=agent_data.updated_at,
            llm_provider=agent_data.config.llm_provider,
            llm_model=agent_data.config.llm_model,
            region=agent_data.config.region,
            languages=agent_data.config.languages
        )
        
        logger.info(
            "Agent activated via API",
            agent_id=agent_id,
            tenant_id=tenant_id
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to activate agent via API", error=str(e), agent_id=agent_id, tenant_id=tenant_id)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{agent_id}/deactivate", response_model=AgentResponse)
async def deactivate_agent(
    agent_id: str,
    tenant_id: str = Depends(get_current_tenant),
    token: str = Depends(security)
) -> AgentResponse:
    """
    Deactivate an agent.
    
    Args:
        agent_id: Agent identifier
        tenant_id: Current tenant ID
        token: Authentication token
        
    Returns:
        Updated agent data
        
    Raises:
        HTTPException: If agent not found or deactivation fails
    """
    try:
        # Validate UUID format
        try:
            uuid.UUID(agent_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent ID format")
        
        # Get agent manager for tenant
        manager = get_agent_manager(tenant_id)
        
        # Stop agent
        success = await manager.stop_agent(agent_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found or failed to deactivate")
        
        # Get updated agent for response
        from smeflow.agents.persistence import agent_persistence_service
        
        agent_data = agent_persistence_service.get_agent(
            agent_id=uuid.UUID(agent_id),
            tenant_id=tenant_id
        )
        
        if not agent_data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Convert to response format
        response = AgentResponse(
            id=str(agent_data.id),
            tenant_id=agent_data.tenant_id,
            name=agent_data.name,
            description=agent_data.description,
            agent_type=agent_data.agent_type,
            status=AgentStatus.INACTIVE,  # Should be inactive after stop
            is_active=agent_data.is_active,
            created_at=agent_data.created_at,
            updated_at=agent_data.updated_at,
            llm_provider=agent_data.config.llm_provider,
            llm_model=agent_data.config.llm_model,
            region=agent_data.config.region,
            languages=agent_data.config.languages
        )
        
        logger.info(
            "Agent deactivated via API",
            agent_id=agent_id,
            tenant_id=tenant_id
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to deactivate agent via API", error=str(e), agent_id=agent_id, tenant_id=tenant_id)
        raise HTTPException(status_code=500, detail="Internal server error")
