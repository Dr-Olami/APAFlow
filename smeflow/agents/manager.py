"""
Agent manager for SMEFlow agent lifecycle and coordination.

Manages agent creation, configuration, monitoring, and coordination
with multi-tenant isolation and African market optimizations.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from uuid import uuid4
import uuid

from .base import BaseAgent, AgentConfig, AgentType, AgentStatus
from .factory import AgentFactory
from .persistence import agent_persistence_service, AgentPersistenceData, AgentPersistenceConfig
from ..core.logging import get_logger
from ..core.cache import cache_manager
from ..database.connection import get_db_session

logger = get_logger(__name__)


class AgentManager:
    """
    Manager for SMEFlow agent lifecycle and coordination.
    
    Provides centralized management of agents with:
    - Agent creation and configuration
    - Lifecycle management (start, stop, pause, resume)
    - Performance monitoring and metrics
    - Multi-tenant isolation
    - Resource optimization
    """
    
    def __init__(self, tenant_id: str, region: str = "NG"):
        """
        Initialize Agent Manager.
        
        Args:
            tenant_id: Tenant identifier for isolation
            region: African region code
        """
        self.tenant_id = tenant_id
        self.region = region
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_groups: Dict[str, Set[str]] = {}
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Manager metadata
        self.manager_id = str(uuid4())
        self.created_at = datetime.utcnow()
        self.last_cleanup = datetime.utcnow()
        
        # Persistence service
        self.persistence = agent_persistence_service
        
        # Load existing agents from database
        self._load_agents_from_db()
        
        logger.info(
            "Agent manager initialized",
            tenant_id=self.tenant_id,
            region=self.region,
            manager_id=self.manager_id,
            loaded_agents=len(self.agents)
        )
    
    def _load_agents_from_db(self) -> None:
        """
        Load existing agents from database on manager initialization.
        """
        try:
            # Get all active agents for this tenant
            persisted_agents = self.persistence.list_agents(
                tenant_id=self.tenant_id,
                active_only=True
            )
            
            for agent_data in persisted_agents:
                try:
                    # Convert persistence data to AgentConfig
                    config = self._persistence_config_to_agent_config(agent_data.config)
                    config.agent_id = str(agent_data.id)
                    
                    # Create agent using factory
                    agent = AgentFactory.create_agent(
                        agent_type=agent_data.agent_type,
                        config=config
                    )
                    
                    # Add to manager
                    self.agents[str(agent_data.id)] = agent
                    
                    logger.info(
                        "Loaded agent from database",
                        agent_id=str(agent_data.id),
                        agent_type=agent_data.agent_type.value,
                        tenant_id=self.tenant_id
                    )
                    
                except Exception as e:
                    logger.error(
                        "Failed to load agent from database",
                        agent_id=str(agent_data.id),
                        error=str(e)
                    )
                    
        except Exception as e:
            logger.error(
                "Failed to load agents from database",
                tenant_id=self.tenant_id,
                error=str(e)
            )
    
    def _persistence_config_to_agent_config(self, persistence_config: AgentPersistenceConfig) -> AgentConfig:
        """
        Convert persistence configuration to agent configuration.
        
        Args:
            persistence_config: Persistence configuration
        
        Returns:
            Agent configuration
        """
        return AgentConfig(
            agent_id="",  # Will be set by caller
            tenant_id=self.tenant_id,
            agent_type=persistence_config.agent_type,
            llm_provider=persistence_config.llm_provider,
            llm_model=persistence_config.llm_model,
            temperature=persistence_config.temperature,
            max_tokens=persistence_config.max_tokens,
            tools=persistence_config.tools,
            system_prompt=persistence_config.system_prompt,
            region=persistence_config.region,
            timezone=persistence_config.timezone,
            languages=persistence_config.languages,
            currency=persistence_config.currency,
            timeout_seconds=persistence_config.timeout_seconds,
            max_retries=persistence_config.max_retries,
            enable_caching=persistence_config.enable_caching
        )
    
    def _agent_config_to_persistence_config(self, config: AgentConfig) -> AgentPersistenceConfig:
        """
        Convert agent configuration to persistence configuration.
        
        Args:
            config: Agent configuration
        
        Returns:
            Persistence configuration
        """
        return AgentPersistenceConfig(
            agent_type=config.agent_type,
            llm_provider=config.llm_provider,
            llm_model=config.llm_model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            tools=config.tools,
            system_prompt=config.system_prompt,
            region=config.region,
            timezone=config.timezone,
            languages=config.languages,
            currency=config.currency,
            timeout_seconds=config.timeout_seconds,
            max_retries=config.max_retries,
            enable_caching=config.enable_caching
        )
    
    async def create_agent(
        self,
        config: Dict[str, Any],
        tools: Optional[List] = None,
        group: Optional[str] = None,
        persist: bool = True
    ) -> str:
        """
        Create a new agent with optional persistence.
        
        Args:
            config: Agent configuration
            tools: Available tools for the agent
            group: Optional group to assign the agent to
            persist: Whether to persist agent to database
            
        Returns:
            Agent ID
        """
        # Ensure tenant isolation
        config["tenant_id"] = self.tenant_id
        if "region" not in config:
            config["region"] = self.region
        
        # Validate configuration
        validation_errors = AgentFactory.validate_config(config)
        if validation_errors:
            raise ValueError(f"Invalid agent configuration: {', '.join(validation_errors)}")
        
        try:
            # Create agent
            agent = AgentFactory.create_agent_from_dict(config, tools)
            
            # Persist to database if requested
            if persist:
                try:
                    # Convert to persistence format
                    persistence_config = self._agent_config_to_persistence_config(agent.config)
                    
                    agent_data = AgentPersistenceData(
                        tenant_id=self.tenant_id,
                        name=config.get("name", f"{agent.config.agent_type.value}_agent"),
                        description=config.get("description"),
                        agent_type=agent.config.agent_type,
                        config=persistence_config,
                        prompts=config.get("prompts", {}),
                        is_active=True
                    )
                    
                    # Save to database
                    persisted_agent = self.persistence.create_agent(agent_data)
                    
                    # Update agent ID to match database
                    agent.agent_id = str(persisted_agent.id)
                    agent.config.agent_id = str(persisted_agent.id)
                    
                    logger.info(
                        "Agent persisted to database",
                        agent_id=agent.agent_id,
                        tenant_id=self.tenant_id
                    )
                    
                except Exception as e:
                    logger.error(
                        "Failed to persist agent to database",
                        agent_id=agent.agent_id,
                        error=str(e)
                    )
                    # Continue without persistence
            
            # Register agent
            self.agents[agent.agent_id] = agent
            
            # Add to group if specified
            if group:
                self._add_agent_to_group(agent.agent_id, group)
            
            # Initialize performance tracking
            self.performance_metrics[agent.agent_id] = {
                "created_at": datetime.utcnow().isoformat(),
                "total_executions": 0,
                "total_cost": 0.0,
                "average_response_time": 0.0,
                "error_count": 0,
                "last_execution": None
            }
            
            # Cache agent metadata
            await self._cache_agent_metadata(agent)
            
            logger.info(
                f"Created agent {agent.agent_id}",
                extra={
                    "manager_id": self.manager_id,
                    "agent_id": agent.agent_id,
                    "agent_type": config["agent_type"],
                    "tenant_id": self.tenant_id,
                    "group": group
                }
            )
            
            return agent.agent_id
            
        except Exception as e:
            logger.error(
                "Failed to create agent",
                agent_id=getattr(agent, 'agent_id', 'unknown'),
                tenant_id=self.tenant_id,
                error=str(e)
            )
            raise
    
    async def update_agent_config(
        self, 
        agent_id: str, 
        config_updates: Dict[str, Any],
        persist: bool = True
    ) -> bool:
        """
        Update agent configuration with optional persistence.
        
        Args:
            agent_id: Agent ID
            config_updates: Configuration updates
            persist: Whether to persist changes to database
            
        Returns:
            True if successful, False otherwise
        """
        if agent_id not in self.agents:
            logger.warning("Agent not found for update", agent_id=agent_id)
            return False
        
        try:
            agent = self.agents[agent_id]
            
            # Update in-memory configuration
            for key, value in config_updates.items():
                if hasattr(agent.config, key):
                    setattr(agent.config, key, value)
            
            # Persist to database if requested
            if persist:
                try:
                    # Convert updates to persistence format
                    if 'config' not in config_updates:
                        config_updates['config'] = self._agent_config_to_persistence_config(agent.config).dict()
                    
                    self.persistence.update_agent(
                        agent_id=uuid.UUID(agent_id),
                        tenant_id=self.tenant_id,
                        updates=config_updates
                    )
                    
                    logger.info(
                        "Agent configuration updated in database",
                        agent_id=agent_id,
                        tenant_id=self.tenant_id
                    )
                    
                except Exception as e:
                    logger.error(
                        "Failed to persist agent configuration update",
                        agent_id=agent_id,
                        error=str(e)
                    )
                    # Continue with in-memory update
            
            # Update cache
            await self._cache_agent_metadata(agent)
            
            logger.info(
                "Agent configuration updated",
                agent_id=agent_id,
                updates=list(config_updates.keys())
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to update agent configuration",
                agent_id=agent_id,
                error=str(e)
            )
            return False
    
    async def delete_agent(
        self, 
        agent_id: str,
        soft_delete: bool = True,
        persist: bool = True
    ) -> bool:
        """
        Delete agent with optional persistence.
        
        Args:
            agent_id: Agent ID
            soft_delete: Whether to soft delete (deactivate) or hard delete
            persist: Whether to persist deletion to database
            
        Returns:
            True if successful, False otherwise
        """
        if agent_id not in self.agents:
            logger.warning("Agent not found for deletion", agent_id=agent_id)
            return False
        
        try:
            # Stop agent if running
            await self.stop_agent(agent_id)
            
            # Persist deletion if requested
            if persist:
                try:
                    self.persistence.delete_agent(
                        agent_id=uuid.UUID(agent_id),
                        tenant_id=self.tenant_id,
                        soft_delete=soft_delete
                    )
                    
                    logger.info(
                        "Agent deletion persisted to database",
                        agent_id=agent_id,
                        soft_delete=soft_delete
                    )
                    
                except Exception as e:
                    logger.error(
                        "Failed to persist agent deletion",
                        agent_id=agent_id,
                        error=str(e)
                    )
            
            # Remove from memory
            if soft_delete:
                # Mark as inactive
                self.agents[agent_id].status = AgentStatus.INACTIVE
            else:
                # Remove completely
                del self.agents[agent_id]
                if agent_id in self.performance_metrics:
                    del self.performance_metrics[agent_id]
            
            # Remove from groups
            for group_agents in self.agent_groups.values():
                group_agents.discard(agent_id)
            
            # Clear cache
            await self._clear_agent_cache(agent_id)
            
            logger.info(
                "Agent deleted successfully",
                agent_id=agent_id,
                soft_delete=soft_delete
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to delete agent",
                agent_id=agent_id,
                error=str(e)
            )
            return False
    
    async def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent instance or None if not found
        """
        agent = self.agents.get(agent_id)
        if agent and agent.config.tenant_id != self.tenant_id:
            logger.warning(
                f"Attempted cross-tenant agent access: {agent_id}",
                extra={
                    "manager_id": self.manager_id,
                    "tenant_id": self.tenant_id,
                    "agent_tenant": agent.config.tenant_id
                }
            )
            return None
        
        return agent
    
    async def execute_agent(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an agent with input data.
        
        Args:
            agent_id: Agent identifier
            input_data: Input data for execution
            context: Additional context
            
        Returns:
            Execution result
        """
        agent = await self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        start_time = datetime.utcnow()
        
        try:
            # Execute agent
            result = await agent.execute(input_data, context)
            
            # Update performance metrics
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            await self._update_performance_metrics(agent_id, execution_time, result, success=True)
            
            return result
            
        except Exception as e:
            # Update error metrics
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            await self._update_performance_metrics(agent_id, execution_time, {}, success=False)
            
            logger.error(
                f"Agent execution failed: {e}",
                extra={
                    "manager_id": self.manager_id,
                    "agent_id": agent_id,
                    "tenant_id": self.tenant_id,
                    "error": str(e)
                }
            )
            raise
    
    async def list_agents(
        self,
        agent_type: Optional[AgentType] = None,
        status: Optional[AgentStatus] = None,
        group: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List agents with optional filtering.
        
        Args:
            agent_type: Filter by agent type
            status: Filter by agent status
            group: Filter by group
            
        Returns:
            List of agent information
        """
        agents_info = []
        
        for agent_id, agent in self.agents.items():
            # Apply filters
            if agent_type and agent.config.agent_type != agent_type:
                continue
            if status and agent.status != status:
                continue
            if group and not self._is_agent_in_group(agent_id, group):
                continue
            
            # Get agent info
            agent_info = agent.get_status()
            agent_info.update({
                "performance_metrics": self.performance_metrics.get(agent_id, {}),
                "groups": self._get_agent_groups(agent_id)
            })
            
            agents_info.append(agent_info)
        
        return agents_info
    
    async def pause_agent(self, agent_id: str) -> bool:
        """
        Pause an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Success status
        """
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        
        agent.pause()
        await self._cache_agent_metadata(agent)
        
        logger.info(
            f"Paused agent {agent_id}",
            extra={
                "manager_id": self.manager_id,
                "agent_id": agent_id,
                "tenant_id": self.tenant_id
            }
        )
        
        return True
    
    async def resume_agent(self, agent_id: str) -> bool:
        """
        Resume a paused agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Success status
        """
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        
        agent.resume()
        await self._cache_agent_metadata(agent)
        
        logger.info(
            f"Resumed agent {agent_id}",
            extra={
                "manager_id": self.manager_id,
                "agent_id": agent_id,
                "tenant_id": self.tenant_id
            }
        )
        
        return True
    
    async def stop_agent(self, agent_id: str) -> bool:
        """
        Stop an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Success status
        """
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        
        agent.stop()
        await self._cache_agent_metadata(agent)
        
        logger.info(
            f"Stopped agent {agent_id}",
            extra={
                "manager_id": self.manager_id,
                "agent_id": agent_id,
                "tenant_id": self.tenant_id
            }
        )
        
        return True
    
    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Success status
        """
        if agent_id not in self.agents:
            return False
        
        # Remove from groups
        for group_name in list(self.agent_groups.keys()):
            self.agent_groups[group_name].discard(agent_id)
            if not self.agent_groups[group_name]:
                del self.agent_groups[group_name]
        
        # Remove agent and metrics
        del self.agents[agent_id]
        self.performance_metrics.pop(agent_id, None)
        
        # Remove from cache
        cache_key = f"agent_metadata:{self.tenant_id}:{agent_id}"
        await cache_manager.delete(cache_key)
        
        logger.info(
            f"Deleted agent {agent_id}",
            extra={
                "manager_id": self.manager_id,
                "agent_id": agent_id,
                "tenant_id": self.tenant_id
            }
        )
        
        return True
    
    async def create_agent_group(self, group_name: str, agent_ids: List[str]) -> bool:
        """
        Create a group of agents.
        
        Args:
            group_name: Name of the group
            agent_ids: List of agent IDs to include
            
        Returns:
            Success status
        """
        # Validate agents exist and belong to tenant
        valid_agents = []
        for agent_id in agent_ids:
            agent = await self.get_agent(agent_id)
            if agent:
                valid_agents.append(agent_id)
        
        if not valid_agents:
            return False
        
        self.agent_groups[group_name] = set(valid_agents)
        
        logger.info(
            f"Created agent group {group_name}",
            extra={
                "manager_id": self.manager_id,
                "group_name": group_name,
                "agent_count": len(valid_agents),
                "tenant_id": self.tenant_id
            }
        )
        
        return True
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary for all agents.
        
        Returns:
            Performance summary
        """
        total_agents = len(self.agents)
        active_agents = len([a for a in self.agents.values() if a.status == AgentStatus.ACTIVE])
        
        total_executions = sum(metrics.get("total_executions", 0) for metrics in self.performance_metrics.values())
        total_cost = sum(metrics.get("total_cost", 0.0) for metrics in self.performance_metrics.values())
        total_errors = sum(metrics.get("error_count", 0) for metrics in self.performance_metrics.values())
        
        avg_response_times = [
            metrics.get("average_response_time", 0.0) 
            for metrics in self.performance_metrics.values()
        ]
        avg_response_time = sum(avg_response_times) / len(avg_response_times) if avg_response_times else 0.0
        
        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "total_executions": total_executions,
            "total_cost_usd": total_cost,
            "total_errors": total_errors,
            "average_response_time_ms": avg_response_time,
            "manager_id": self.manager_id,
            "tenant_id": self.tenant_id,
            "last_cleanup": self.last_cleanup.isoformat()
        }
    
    async def cleanup_inactive_agents(self, max_age_hours: int = 24) -> int:
        """
        Clean up inactive agents older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours for inactive agents
            
        Returns:
            Number of agents cleaned up
        """
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0
        
        agents_to_delete = []
        for agent_id, agent in self.agents.items():
            if (agent.status == AgentStatus.INACTIVE and 
                agent.created_at.timestamp() < cutoff_time and
                agent.execution_count == 0):
                agents_to_delete.append(agent_id)
        
        for agent_id in agents_to_delete:
            await self.delete_agent(agent_id)
            cleaned_count += 1
        
        self.last_cleanup = datetime.utcnow()
        
        if cleaned_count > 0:
            logger.info(
                f"Cleaned up {cleaned_count} inactive agents",
                extra={
                    "manager_id": self.manager_id,
                    "tenant_id": self.tenant_id,
                    "cleaned_count": cleaned_count
                }
            )
        
        return cleaned_count
    
    def _add_agent_to_group(self, agent_id: str, group_name: str) -> None:
        """Add agent to a group."""
        if group_name not in self.agent_groups:
            self.agent_groups[group_name] = set()
        self.agent_groups[group_name].add(agent_id)
    
    def _is_agent_in_group(self, agent_id: str, group_name: str) -> bool:
        """Check if agent is in a group."""
        return group_name in self.agent_groups and agent_id in self.agent_groups[group_name]
    
    def _get_agent_groups(self, agent_id: str) -> List[str]:
        """Get groups that contain the agent."""
        return [group for group, agents in self.agent_groups.items() if agent_id in agents]
    
    async def _update_performance_metrics(
        self,
        agent_id: str,
        execution_time: float,
        result: Dict[str, Any],
        success: bool
    ) -> None:
        """Update performance metrics for an agent."""
        if agent_id not in self.performance_metrics:
            return
        
        metrics = self.performance_metrics[agent_id]
        metrics["total_executions"] += 1
        metrics["last_execution"] = datetime.utcnow().isoformat()
        
        if not success:
            metrics["error_count"] += 1
        
        # Update average response time
        if metrics["total_executions"] == 1:
            metrics["average_response_time"] = execution_time
        else:
            metrics["average_response_time"] = (
                (metrics["average_response_time"] * (metrics["total_executions"] - 1) + execution_time) 
                / metrics["total_executions"]
            )
        
        # Update cost if available
        if "cost" in result:
            metrics["total_cost"] += result["cost"]
    
    async def _cache_agent_metadata(self, agent: BaseAgent) -> None:
        """Cache agent metadata for quick access."""
        cache_key = f"agent_metadata:{self.tenant_id}:{agent.agent_id}"
        metadata = {
            "agent_id": agent.agent_id,
            "name": agent.config.name,
            "type": agent.config.agent_type,
            "status": agent.status,
            "tenant_id": agent.config.tenant_id,
            "region": agent.config.region,
            "created_at": agent.created_at.isoformat(),
            "last_execution": agent.last_execution.isoformat() if agent.last_execution else None
        }
        
        await cache_manager.set(cache_key, metadata, ttl=3600)  # Cache for 1 hour
