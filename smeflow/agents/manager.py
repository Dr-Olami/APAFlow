"""
Agent manager for SMEFlow agent lifecycle and coordination.

Manages agent creation, configuration, monitoring, and coordination
with multi-tenant isolation and African market optimizations.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from uuid import uuid4

from .base import BaseAgent, AgentConfig, AgentType, AgentStatus
from .factory import AgentFactory
from ..core.logging import get_logger
from ..core.cache import cache_manager

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
        
        logger.info(
            f"Initialized Agent Manager for tenant {tenant_id}",
            extra={
                "manager_id": self.manager_id,
                "tenant_id": tenant_id,
                "region": region
            }
        )
    
    async def create_agent(
        self,
        config: Dict[str, Any],
        tools: Optional[List] = None,
        group: Optional[str] = None
    ) -> str:
        """
        Create a new agent.
        
        Args:
            config: Agent configuration
            tools: Available tools for the agent
            group: Optional group to assign the agent to
            
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
                f"Failed to create agent: {e}",
                extra={
                    "manager_id": self.manager_id,
                    "tenant_id": self.tenant_id,
                    "config": config,
                    "error": str(e)
                }
            )
            raise
    
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
            if metrics.get("average_response_time", 0.0) > 0
        ]
        overall_avg_response_time = sum(avg_response_times) / len(avg_response_times) if avg_response_times else 0.0
        
        return {
            "manager_id": self.manager_id,
            "tenant_id": self.tenant_id,
            "region": self.region,
            "total_agents": total_agents,
            "active_agents": active_agents,
            "total_executions": total_executions,
            "total_cost": round(total_cost, 4),
            "total_errors": total_errors,
            "error_rate": round(total_errors / total_executions, 4) if total_executions > 0 else 0.0,
            "average_response_time": round(overall_avg_response_time, 2),
            "groups": list(self.agent_groups.keys()),
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
