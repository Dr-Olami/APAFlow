"""
Base agent classes and configurations for SMEFlow agent system.

Provides the foundational architecture for intelligent automation agents
with multi-tenant isolation and African market optimizations.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

from langchain.agents import AgentExecutor
from langchain.agents.agent import BaseMultiActionAgent, BaseSingleActionAgent
from langchain.schema import AgentAction, AgentFinish
from langchain.tools import BaseTool
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import BasePromptTemplate

from ..core.logging import get_logger
from ..database.models import Agent as AgentModel

logger = get_logger(__name__)


class AgentType(str, Enum):
    """Agent types supported by SMEFlow."""
    AUTOMATOR = "automator"
    MENTOR = "mentor" 
    SUPERVISOR = "supervisor"


class AgentStatus(str, Enum):
    """Agent status states."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PAUSED = "paused"


class AgentConfig(BaseModel):
    """Configuration for SMEFlow agents."""
    model_config = ConfigDict(extra="allow")
    
    # Basic configuration
    name: str = Field(..., description="Agent name")
    description: str = Field("", description="Agent description")
    agent_type: AgentType = Field(..., description="Type of agent")
    
    # LLM configuration
    llm_provider: str = Field("openai", description="LLM provider (openai, anthropic, etc.)")
    model_name: str = Field("gpt-4", description="Model name to use")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for responses")
    
    # Agent behavior
    max_iterations: int = Field(10, ge=1, le=50, description="Maximum agent iterations")
    early_stopping_method: str = Field("force", description="Early stopping method")
    verbose: bool = Field(False, description="Enable verbose logging")
    
    # African market optimizations
    languages: List[str] = Field(
        default=["en"], 
        description="Supported languages (en, sw, ha, yo, ig, am, ar, fr, pt, af, zu, xh)"
    )
    region: str = Field("NG", description="African region code (NG, KE, ZA, GH, UG, TZ, RW, ET, EG, MA)")
    cultural_context: bool = Field(True, description="Enable cultural context awareness")
    
    # Multi-tenancy
    tenant_id: str = Field(..., description="Tenant identifier")
    isolation_level: str = Field("strict", description="Tenant isolation level")
    
    # Tools and capabilities
    available_tools: List[str] = Field(default=[], description="Available tool names")
    custom_instructions: str = Field("", description="Custom agent instructions")
    
    # Performance and monitoring
    enable_monitoring: bool = Field(True, description="Enable performance monitoring")
    cost_tracking: bool = Field(True, description="Enable cost tracking")
    
    # Compliance and security
    data_residency: str = Field("local", description="Data residency requirement")
    audit_logging: bool = Field(True, description="Enable audit logging")


class BaseAgent(ABC):
    """
    Base class for all SMEFlow agents.
    
    Provides common functionality for agent lifecycle management,
    multi-tenant isolation, and African market optimizations.
    """
    
    def __init__(
        self,
        config: AgentConfig,
        llm: BaseLanguageModel,
        tools: Optional[List[BaseTool]] = None,
        prompt: Optional[BasePromptTemplate] = None
    ):
        """
        Initialize base agent.
        
        Args:
            config: Agent configuration
            llm: Language model instance
            tools: Available tools for the agent
            prompt: Custom prompt template
        """
        self.config = config
        self.llm = llm
        self.tools = tools or []
        self.prompt = prompt
        
        # Agent metadata
        self.agent_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.status = AgentStatus.INACTIVE
        self.execution_count = 0
        self.last_execution = None
        
        # Performance tracking
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.average_response_time = 0.0
        
        # Initialize agent executor
        self._executor = None
        self._initialize_agent()
        
        logger.info(
            f"Initialized {self.config.agent_type} agent",
            extra={
                "agent_id": self.agent_id,
                "tenant_id": self.config.tenant_id,
                "agent_type": self.config.agent_type,
                "region": self.config.region
            }
        )
    
    @abstractmethod
    def _create_agent(self) -> Union[BaseMultiActionAgent, BaseSingleActionAgent]:
        """Create the specific agent implementation."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent type."""
        pass
    
    def _initialize_agent(self) -> None:
        """Initialize the agent executor."""
        try:
            agent = self._create_agent()
            self._executor = AgentExecutor.from_agent_and_tools(
                agent=agent,
                tools=self.tools,
                verbose=self.config.verbose,
                max_iterations=self.config.max_iterations,
                early_stopping_method=self.config.early_stopping_method,
                return_intermediate_steps=True
            )
            self.status = AgentStatus.ACTIVE
            
        except Exception as e:
            logger.error(
                f"Failed to initialize agent: {e}",
                extra={
                    "agent_id": self.agent_id,
                    "tenant_id": self.config.tenant_id,
                    "error": str(e)
                }
            )
            self.status = AgentStatus.ERROR
            raise
    
    async def execute(
        self, 
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the agent with given input.
        
        Args:
            input_data: Input data for the agent
            context: Additional context information
            
        Returns:
            Agent execution result
        """
        if self.status != AgentStatus.ACTIVE:
            raise ValueError(f"Agent is not active. Status: {self.status}")
        
        start_time = datetime.utcnow()
        
        try:
            # Prepare input with context
            agent_input = self._prepare_input(input_data, context)
            
            # Execute agent
            result = await self._executor.ainvoke(agent_input)
            
            # Update performance metrics
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(execution_time, result)
            
            # Log execution
            if self.config.audit_logging:
                self._log_execution(input_data, result, execution_time)
            
            return self._format_result(result)
            
        except Exception as e:
            logger.error(
                f"Agent execution failed: {e}",
                extra={
                    "agent_id": self.agent_id,
                    "tenant_id": self.config.tenant_id,
                    "error": str(e)
                }
            )
            self.status = AgentStatus.ERROR
            raise
    
    def _prepare_input(
        self, 
        input_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare input data for agent execution."""
        prepared_input = {
            "input": input_data.get("query", ""),
            "agent_id": self.agent_id,
            "tenant_id": self.config.tenant_id,
            "region": self.config.region,
            "languages": self.config.languages,
            "cultural_context": self.config.cultural_context
        }
        
        if context:
            prepared_input.update(context)
            
        return prepared_input
    
    def _format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format agent execution result."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.config.agent_type,
            "tenant_id": self.config.tenant_id,
            "output": result.get("output", ""),
            "intermediate_steps": result.get("intermediate_steps", []),
            "execution_count": self.execution_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _update_metrics(self, execution_time: float, result: Dict[str, Any]) -> None:
        """Update performance metrics."""
        self.execution_count += 1
        self.last_execution = datetime.utcnow()
        
        # Update average response time
        if self.execution_count == 1:
            self.average_response_time = execution_time
        else:
            self.average_response_time = (
                (self.average_response_time * (self.execution_count - 1) + execution_time) 
                / self.execution_count
            )
        
        # Track token usage if available
        if "token_usage" in result:
            self.total_tokens_used += result["token_usage"].get("total_tokens", 0)
    
    def _log_execution(
        self, 
        input_data: Dict[str, Any], 
        result: Dict[str, Any], 
        execution_time: float
    ) -> None:
        """Log agent execution for audit purposes."""
        logger.info(
            "Agent execution completed",
            extra={
                "agent_id": self.agent_id,
                "tenant_id": self.config.tenant_id,
                "agent_type": self.config.agent_type,
                "execution_time": execution_time,
                "execution_count": self.execution_count,
                "input_size": len(str(input_data)),
                "output_size": len(str(result.get("output", ""))),
                "region": self.config.region
            }
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status and metrics."""
        return {
            "agent_id": self.agent_id,
            "name": self.config.name,
            "type": self.config.agent_type,
            "status": self.status,
            "tenant_id": self.config.tenant_id,
            "region": self.config.region,
            "created_at": self.created_at.isoformat(),
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "execution_count": self.execution_count,
            "total_tokens_used": self.total_tokens_used,
            "total_cost": self.total_cost,
            "average_response_time": self.average_response_time,
            "available_tools": [tool.name for tool in self.tools],
            "languages": self.config.languages
        }
    
    def pause(self) -> None:
        """Pause the agent."""
        if self.status == AgentStatus.ACTIVE:
            self.status = AgentStatus.PAUSED
            logger.info(f"Agent {self.agent_id} paused")
    
    def resume(self) -> None:
        """Resume the agent."""
        if self.status == AgentStatus.PAUSED:
            self.status = AgentStatus.ACTIVE
            logger.info(f"Agent {self.agent_id} resumed")
    
    def stop(self) -> None:
        """Stop the agent."""
        self.status = AgentStatus.INACTIVE
        logger.info(f"Agent {self.agent_id} stopped")
    
    def add_tool(self, tool: BaseTool) -> None:
        """Add a tool to the agent."""
        if tool not in self.tools:
            self.tools.append(tool)
            # Reinitialize agent with new tools
            self._initialize_agent()
            logger.info(f"Added tool {tool.name} to agent {self.agent_id}")
    
    def remove_tool(self, tool_name: str) -> None:
        """Remove a tool from the agent."""
        self.tools = [tool for tool in self.tools if tool.name != tool_name]
        # Reinitialize agent with updated tools
        self._initialize_agent()
        logger.info(f"Removed tool {tool_name} from agent {self.agent_id}")
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update agent configuration."""
        for key, value in new_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # Reinitialize if necessary
        if any(key in new_config for key in ["llm_provider", "model_name", "temperature"]):
            self._initialize_agent()
        
        logger.info(f"Updated configuration for agent {self.agent_id}")
