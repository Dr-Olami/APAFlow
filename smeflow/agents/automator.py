"""
Automator agent implementation for SMEFlow.

Automators execute specific tasks like data processing, API calls,
and workflow automation with African market optimizations.
"""

from typing import Dict, Any, List, Optional, Union
from langchain.agents import AgentType, initialize_agent
from langchain.agents.agent import BaseMultiActionAgent, BaseSingleActionAgent
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from langchain_core.language_models import BaseLanguageModel

from .base import BaseAgent, AgentConfig
from ..core.logging import get_logger

logger = get_logger(__name__)


class AutomatorAgent(BaseAgent):
    """
    Automator agent for executing specific tasks and workflows.
    
    Designed for African SMEs with focus on:
    - Data processing and transformation
    - API integrations (M-Pesa, Jumia, Paystack)
    - Workflow automation
    - Task execution with error handling
    """
    
    def __init__(
        self,
        config: AgentConfig,
        llm: BaseLanguageModel,
        tools: Optional[List[BaseTool]] = None,
        prompt: Optional[PromptTemplate] = None
    ):
        """
        Initialize Automator agent.
        
        Args:
            config: Agent configuration
            llm: Language model instance
            tools: Available tools for automation
            prompt: Custom prompt template
        """
        super().__init__(config, llm, tools, prompt)
        
        # Automator-specific configuration
        self.execution_mode = config.custom_instructions or "sequential"
        self.error_handling = "retry_with_fallback"
        self.max_retries = 3
        
        logger.info(
            f"Initialized Automator agent for tenant {config.tenant_id}",
            extra={
                "agent_id": self.agent_id,
                "tenant_id": config.tenant_id,
                "region": config.region,
                "tools_count": len(self.tools),
                "execution_mode": self.execution_mode
            }
        )
    
    def _create_agent(self) -> Union[BaseMultiActionAgent, BaseSingleActionAgent]:
        """Create the automator agent implementation."""
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=self.config.verbose,
            max_iterations=self.config.max_iterations,
            early_stopping_method=self.config.early_stopping_method,
            handle_parsing_errors=True
        )
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for Automator agents."""
        base_prompt = f"""You are an Automator agent for SMEFlow, designed to help African SMEs automate their business processes.

AGENT IDENTITY:
- Type: Automator
- Region: {self.config.region}
- Tenant: {self.config.tenant_id}
- Languages: {', '.join(self.config.languages)}

CORE CAPABILITIES:
- Execute specific tasks and workflows
- Process and transform data
- Integrate with African market APIs (M-Pesa, Jumia, Paystack)
- Automate repetitive business processes
- Handle errors gracefully with retry mechanisms

AFRICAN MARKET CONTEXT:
- Understand local business practices and cultural nuances
- Support multiple African languages and currencies
- Optimize for varying internet connectivity
- Consider mobile-first approach for user interactions
- Respect local business hours and holidays

EXECUTION PRINCIPLES:
1. Be precise and efficient in task execution
2. Provide clear status updates and error messages
3. Use available tools to accomplish tasks
4. Retry failed operations with intelligent backoff
5. Log all actions for audit and compliance
6. Maintain data privacy and security standards

AVAILABLE TOOLS:
{self._format_tools_description()}

INSTRUCTIONS:
- Always confirm task parameters before execution
- Break complex tasks into smaller, manageable steps
- Provide progress updates for long-running operations
- Use appropriate error handling and recovery strategies
- Consider offline/low-connectivity scenarios
- Respect rate limits and API quotas

Remember: You're helping African SMEs grow their businesses through intelligent automation. Be reliable, efficient, and culturally aware."""

        if self.config.custom_instructions:
            base_prompt += f"\n\nCUSTOM INSTRUCTIONS:\n{self.config.custom_instructions}"
        
        return base_prompt
    
    def _format_tools_description(self) -> str:
        """Format available tools for the prompt."""
        if not self.tools:
            return "No tools currently available."
        
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(tool_descriptions)
    
    async def execute_task(
        self,
        task_description: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a specific automation task.
        
        Args:
            task_description: Description of the task to execute
            parameters: Task parameters and configuration
            context: Additional context information
            
        Returns:
            Task execution result
        """
        input_data = {
            "query": f"Execute the following task: {task_description}",
            "parameters": parameters,
            "execution_mode": self.execution_mode,
            "max_retries": self.max_retries
        }
        
        # Add African market context
        if context is None:
            context = {}
        
        context.update({
            "region": self.config.region,
            "languages": self.config.languages,
            "cultural_context": self.config.cultural_context,
            "business_hours": self._get_business_hours(),
            "local_currency": self._get_local_currency(),
            "timezone": self._get_timezone()
        })
        
        return await self.execute(input_data, context)
    
    async def process_data(
        self,
        data: Dict[str, Any],
        transformation_rules: List[Dict[str, Any]],
        output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Process and transform data according to rules.
        
        Args:
            data: Input data to process
            transformation_rules: List of transformation rules
            output_format: Desired output format
            
        Returns:
            Processed data result
        """
        input_data = {
            "query": "Process and transform the provided data according to the specified rules",
            "data": data,
            "transformation_rules": transformation_rules,
            "output_format": output_format
        }
        
        context = {
            "operation_type": "data_processing",
            "data_size": len(str(data)),
            "rules_count": len(transformation_rules)
        }
        
        return await self.execute(input_data, context)
    
    async def integrate_api(
        self,
        api_name: str,
        operation: str,
        parameters: Dict[str, Any],
        retry_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Integrate with external APIs (M-Pesa, Jumia, etc.).
        
        Args:
            api_name: Name of the API to integrate with
            operation: Operation to perform
            parameters: API parameters
            retry_config: Retry configuration for African connectivity
            
        Returns:
            API integration result
        """
        if retry_config is None:
            retry_config = {
                "max_retries": 5,  # Higher for African connectivity
                "backoff_factor": 2,
                "timeout": 30
            }
        
        input_data = {
            "query": f"Integrate with {api_name} API to perform {operation}",
            "api_name": api_name,
            "operation": operation,
            "parameters": parameters,
            "retry_config": retry_config
        }
        
        context = {
            "operation_type": "api_integration",
            "api_provider": api_name,
            "connectivity_optimization": True
        }
        
        return await self.execute(input_data, context)
    
    def _get_business_hours(self) -> Dict[str, str]:
        """Get local business hours based on region."""
        business_hours = {
            "NG": {"start": "08:00", "end": "17:00", "timezone": "WAT"},
            "KE": {"start": "08:00", "end": "17:00", "timezone": "EAT"},
            "ZA": {"start": "08:00", "end": "17:00", "timezone": "SAST"},
            "GH": {"start": "08:00", "end": "17:00", "timezone": "GMT"},
            "UG": {"start": "08:00", "end": "17:00", "timezone": "EAT"},
            "TZ": {"start": "08:00", "end": "17:00", "timezone": "EAT"},
            "RW": {"start": "08:00", "end": "17:00", "timezone": "CAT"},
            "ET": {"start": "08:00", "end": "17:00", "timezone": "EAT"},
            "EG": {"start": "09:00", "end": "17:00", "timezone": "EET"},
            "MA": {"start": "09:00", "end": "18:00", "timezone": "WET"}
        }
        
        return business_hours.get(self.config.region, business_hours["NG"])
    
    def _get_local_currency(self) -> str:
        """Get local currency based on region."""
        currencies = {
            "NG": "NGN",
            "KE": "KES", 
            "ZA": "ZAR",
            "GH": "GHS",
            "UG": "UGX",
            "TZ": "TZS",
            "RW": "RWF",
            "ET": "ETB",
            "EG": "EGP",
            "MA": "MAD"
        }
        
        return currencies.get(self.config.region, "USD")
    
    def _get_timezone(self) -> str:
        """Get timezone based on region."""
        timezones = {
            "NG": "Africa/Lagos",
            "KE": "Africa/Nairobi",
            "ZA": "Africa/Johannesburg", 
            "GH": "Africa/Accra",
            "UG": "Africa/Kampala",
            "TZ": "Africa/Dar_es_Salaam",
            "RW": "Africa/Kigali",
            "ET": "Africa/Addis_Ababa",
            "EG": "Africa/Cairo",
            "MA": "Africa/Casablanca"
        }
        
        return timezones.get(self.config.region, "UTC")
