"""
Agent factory for creating and configuring SMEFlow agents.

Provides centralized agent creation with proper configuration,
LLM setup, and African market optimizations.
"""

from typing import Dict, Any, List, Optional, Type
from langchain.tools import BaseTool
from langchain_core.language_models import BaseLanguageModel

from .base import BaseAgent, AgentConfig, AgentType
from .automator import AutomatorAgent
from .mentor import MentorAgent
from .supervisor import SupervisorAgent
from .llm_providers import create_llm_for_agent
from ..core.logging import get_logger

logger = get_logger(__name__)


class AgentFactory:
    """Factory for creating SMEFlow agents with proper configuration."""
    
    _agent_classes: Dict[AgentType, Type[BaseAgent]] = {
        AgentType.AUTOMATOR: AutomatorAgent,
        AgentType.MENTOR: MentorAgent,
        AgentType.SUPERVISOR: SupervisorAgent
    }
    
    @classmethod
    def create_agent(
        cls,
        config: AgentConfig,
        tools: Optional[List[BaseTool]] = None,
        llm: Optional[BaseLanguageModel] = None
    ) -> BaseAgent:
        """
        Create an agent instance based on configuration.
        
        Args:
            config: Agent configuration
            tools: Available tools for the agent
            llm: Pre-configured LLM instance (optional)
            
        Returns:
            Configured agent instance
        """
        if config.agent_type not in cls._agent_classes:
            raise ValueError(f"Unsupported agent type: {config.agent_type}")
        
        # Create LLM if not provided
        if llm is None:
            llm_config = {
                "llm_provider": config.llm_provider,
                "model_name": config.model_name,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens
            }
            llm = create_llm_for_agent(llm_config, config.tenant_id, config.region)
        
        # Get agent class and create instance
        agent_class = cls._agent_classes[config.agent_type]
        agent = agent_class(config=config, llm=llm, tools=tools)
        
        logger.info(
            f"Created {config.agent_type} agent",
            extra={
                "agent_id": agent.agent_id,
                "agent_type": config.agent_type,
                "tenant_id": config.tenant_id,
                "region": config.region,
                "llm_provider": config.llm_provider,
                "model_name": config.model_name
            }
        )
        
        return agent
    
    @classmethod
    def create_agent_from_dict(
        cls,
        config_dict: Dict[str, Any],
        tools: Optional[List[BaseTool]] = None,
        llm: Optional[BaseLanguageModel] = None
    ) -> BaseAgent:
        """
        Create an agent from a configuration dictionary.
        
        Args:
            config_dict: Agent configuration as dictionary
            tools: Available tools for the agent
            llm: Pre-configured LLM instance (optional)
            
        Returns:
            Configured agent instance
        """
        config = AgentConfig(**config_dict)
        return cls.create_agent(config, tools, llm)
    
    @classmethod
    def create_automator(
        cls,
        name: str,
        tenant_id: str,
        region: str = "NG",
        tools: Optional[List[BaseTool]] = None,
        **kwargs
    ) -> AutomatorAgent:
        """
        Create an Automator agent with default configuration.
        
        Args:
            name: Agent name
            tenant_id: Tenant identifier
            region: African region code
            tools: Available tools
            **kwargs: Additional configuration
            
        Returns:
            Configured Automator agent
        """
        config_dict = {
            "name": name,
            "agent_type": AgentType.AUTOMATOR,
            "tenant_id": tenant_id,
            "region": region,
            "description": kwargs.get("description", f"Automator agent for {name}"),
            **kwargs
        }
        
        agent = cls.create_agent_from_dict(config_dict, tools)
        return agent
    
    @classmethod
    def create_mentor(
        cls,
        name: str,
        tenant_id: str,
        region: str = "NG",
        expertise_areas: Optional[List[str]] = None,
        tools: Optional[List[BaseTool]] = None,
        **kwargs
    ) -> MentorAgent:
        """
        Create a Mentor agent with default configuration.
        
        Args:
            name: Agent name
            tenant_id: Tenant identifier
            region: African region code
            expertise_areas: Areas of expertise
            tools: Available tools
            **kwargs: Additional configuration
            
        Returns:
            Configured Mentor agent
        """
        custom_instructions = ""
        if expertise_areas:
            custom_instructions = f"Expertise areas: {', '.join(expertise_areas)}"
        
        config_dict = {
            "name": name,
            "agent_type": AgentType.MENTOR,
            "tenant_id": tenant_id,
            "region": region,
            "description": kwargs.get("description", f"Mentor agent for {name}"),
            "custom_instructions": custom_instructions,
            **kwargs
        }
        
        agent = cls.create_agent_from_dict(config_dict, tools)
        return agent
    
    @classmethod
    def create_supervisor(
        cls,
        name: str,
        tenant_id: str,
        region: str = "NG",
        managed_agents: Optional[List[str]] = None,
        tools: Optional[List[BaseTool]] = None,
        **kwargs
    ) -> SupervisorAgent:
        """
        Create a Supervisor agent with default configuration.
        
        Args:
            name: Agent name
            tenant_id: Tenant identifier
            region: African region code
            managed_agents: List of agent IDs to manage
            tools: Available tools
            **kwargs: Additional configuration
            
        Returns:
            Configured Supervisor agent
        """
        config_dict = {
            "name": name,
            "agent_type": AgentType.SUPERVISOR,
            "tenant_id": tenant_id,
            "region": region,
            "description": kwargs.get("description", f"Supervisor agent for {name}"),
            **kwargs
        }
        
        agent = cls.create_agent_from_dict(config_dict, tools)
        
        # Add managed agents if provided
        if managed_agents:
            for agent_id in managed_agents:
                agent.add_managed_agent(agent_id, "unknown", [])
        
        return agent
    
    @classmethod
    def get_supported_agent_types(cls) -> List[str]:
        """Get list of supported agent types."""
        return [agent_type.value for agent_type in cls._agent_classes.keys()]
    
    @classmethod
    def get_default_config(cls, agent_type: AgentType, tenant_id: str, region: str = "NG") -> Dict[str, Any]:
        """
        Get default configuration for an agent type.
        
        Args:
            agent_type: Type of agent
            tenant_id: Tenant identifier
            region: African region code
            
        Returns:
            Default configuration dictionary
        """
        base_config = {
            "name": f"Default {agent_type.value.title()}",
            "description": f"Default {agent_type.value} agent",
            "agent_type": agent_type,
            "tenant_id": tenant_id,
            "region": region,
            "llm_provider": "openai",
            "model_name": "gpt-4o",
            "temperature": 0.7,
            "max_iterations": 10,
            "verbose": False,
            "languages": ["en"],
            "cultural_context": True,
            "enable_monitoring": True,
            "cost_tracking": True,
            "audit_logging": True
        }
        
        # Agent-specific defaults
        if agent_type == AgentType.AUTOMATOR:
            base_config.update({
                "name": "Default Automator",
                "description": "Automated task execution agent",
                "custom_instructions": "sequential"
            })
        elif agent_type == AgentType.MENTOR:
            base_config.update({
                "name": "Default Mentor",
                "description": "Business guidance and mentoring agent",
                "custom_instructions": "business_strategy,financial_planning,market_analysis"
            })
        elif agent_type == AgentType.SUPERVISOR:
            base_config.update({
                "name": "Default Supervisor",
                "description": "Workflow orchestration and supervision agent",
                "custom_instructions": "proactive supervision with escalation"
            })
        
        return base_config
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """
        Validate agent configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields
        required_fields = ["name", "agent_type", "tenant_id"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Agent type validation
        if "agent_type" in config:
            try:
                agent_type = AgentType(config["agent_type"])
                if agent_type not in cls._agent_classes:
                    errors.append(f"Unsupported agent type: {config['agent_type']}")
            except ValueError:
                errors.append(f"Invalid agent type: {config['agent_type']}")
        
        # LLM configuration validation
        if "llm_provider" in config:
            supported_providers = ["openai", "anthropic"]
            if config["llm_provider"] not in supported_providers:
                errors.append(f"Unsupported LLM provider: {config['llm_provider']}")
        
        # Temperature validation
        if "temperature" in config:
            temp = config["temperature"]
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                errors.append("Temperature must be a number between 0 and 2")
        
        # Region validation
        if "region" in config:
            supported_regions = ["NG", "KE", "ZA", "GH", "UG", "TZ", "RW", "ET", "EG", "MA"]
            if config["region"] not in supported_regions:
                errors.append(f"Unsupported region: {config['region']}")
        
        # Languages validation
        if "languages" in config:
            supported_languages = ["en", "sw", "ha", "yo", "ig", "am", "ar", "fr", "pt", "af", "zu", "xh"]
            languages = config["languages"]
            if not isinstance(languages, list):
                errors.append("Languages must be a list")
            else:
                for lang in languages:
                    if lang not in supported_languages:
                        errors.append(f"Unsupported language: {lang}")
        
        return errors
