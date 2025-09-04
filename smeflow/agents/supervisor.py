"""
Supervisor agent implementation for SMEFlow.

Supervisors orchestrate workflows, coordinate multiple agents,
and manage complex business processes with oversight and control.
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


class SupervisorAgent(BaseAgent):
    """
    Supervisor agent for workflow orchestration and multi-agent coordination.
    
    Designed for African SMEs with focus on:
    - Workflow orchestration and management
    - Multi-agent coordination and delegation
    - Process oversight and quality control
    - Exception handling and escalation
    - Performance monitoring and optimization
    """
    
    def __init__(
        self,
        config: AgentConfig,
        llm: BaseLanguageModel,
        tools: Optional[List[BaseTool]] = None,
        prompt: Optional[PromptTemplate] = None
    ):
        """
        Initialize Supervisor agent.
        
        Args:
            config: Agent configuration
            llm: Language model instance
            tools: Available tools for supervision
            prompt: Custom prompt template
        """
        super().__init__(config, llm, tools, prompt)
        
        # Supervisor-specific configuration
        self.managed_agents = []
        self.workflow_templates = {}
        self.escalation_rules = self._parse_escalation_rules(config.custom_instructions)
        self.supervision_mode = "proactive"
        
        logger.info(
            f"Initialized Supervisor agent for tenant {config.tenant_id}",
            extra={
                "agent_id": self.agent_id,
                "tenant_id": config.tenant_id,
                "region": config.region,
                "supervision_mode": self.supervision_mode,
                "escalation_rules": len(self.escalation_rules)
            }
        )
    
    def _create_agent(self) -> Union[BaseMultiActionAgent, BaseSingleActionAgent]:
        """Create the supervisor agent implementation."""
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=self.config.verbose,
            max_iterations=self.config.max_iterations,
            early_stopping_method=self.config.early_stopping_method,
            handle_parsing_errors=True
        )
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for Supervisor agents."""
        base_prompt = f"""You are a Supervisor agent for SMEFlow, designed to orchestrate workflows and coordinate multiple agents for African SMEs.

AGENT IDENTITY:
- Type: Supervisor
- Region: {self.config.region}
- Tenant: {self.config.tenant_id}
- Languages: {', '.join(self.config.languages)}
- Supervision Mode: {self.supervision_mode}

CORE CAPABILITIES:
- Orchestrate complex business workflows and processes
- Coordinate multiple agents (Automators, Mentors, other Supervisors)
- Monitor task execution and performance metrics
- Handle exceptions, errors, and escalations
- Optimize workflow efficiency and resource allocation
- Ensure quality control and compliance standards

SUPERVISION PRINCIPLES:
1. Plan and decompose complex tasks into manageable steps
2. Delegate appropriate tasks to specialized agents
3. Monitor progress and performance continuously
4. Intervene when issues arise or quality standards are not met
5. Escalate critical issues according to defined rules
6. Optimize workflows based on performance data
7. Ensure compliance with regional regulations and standards

AFRICAN BUSINESS CONTEXT:
- Understand multi-cultural team dynamics and communication styles
- Account for varying infrastructure and connectivity challenges
- Respect local business hours and cultural practices across regions
- Optimize for mobile-first and offline-capable workflows
- Consider regulatory compliance across different African markets
- Support multiple languages and local business practices

WORKFLOW MANAGEMENT:
- Break down complex business processes into executable steps
- Assign tasks based on agent capabilities and current workload
- Monitor execution timelines and resource utilization
- Implement quality gates and approval processes
- Handle parallel and sequential task dependencies
- Manage workflow state and recovery from failures

ESCALATION FRAMEWORK:
{self._format_escalation_rules()}

AVAILABLE TOOLS:
{self._format_tools_description()}

COORDINATION GUIDELINES:
- Communicate clearly with managed agents using structured instructions
- Provide context and objectives for each delegated task
- Set realistic timelines considering regional constraints
- Monitor agent performance and provide feedback
- Maintain audit trails for compliance and optimization
- Balance automation with human oversight where appropriate

Remember: You're orchestrating business success for African SMEs. Be strategic, efficient, and culturally aware in your supervision approach."""

        if self.config.custom_instructions:
            base_prompt += f"\n\nCUSTOM SUPERVISION RULES:\n{self.config.custom_instructions}"
        
        return base_prompt
    
    def _parse_escalation_rules(self, custom_instructions: str) -> Dict[str, Any]:
        """Parse escalation rules from custom instructions."""
        default_rules = {
            "high_value_transactions": {"threshold": 10000, "action": "human_approval"},
            "compliance_violations": {"threshold": 1, "action": "immediate_escalation"},
            "system_errors": {"threshold": 3, "action": "technical_support"},
            "performance_degradation": {"threshold": 0.5, "action": "optimization_review"},
            "security_incidents": {"threshold": 1, "action": "security_team"}
        }
        
        if not custom_instructions:
            return default_rules
        
        # Parse custom escalation rules from instructions
        # This is a simplified parser - in production, you'd want more sophisticated parsing
        return default_rules
    
    def _format_escalation_rules(self) -> str:
        """Format escalation rules for the prompt."""
        if not self.escalation_rules:
            return "No specific escalation rules defined."
        
        rules_text = []
        for rule_name, rule_config in self.escalation_rules.items():
            threshold = rule_config.get("threshold", "N/A")
            action = rule_config.get("action", "escalate")
            rules_text.append(f"- {rule_name.replace('_', ' ').title()}: Threshold {threshold} → {action.replace('_', ' ').title()}")
        
        return "\n".join(rules_text)
    
    def _format_tools_description(self) -> str:
        """Format available tools for the prompt."""
        if not self.tools:
            return "No specialized tools currently available. Use coordination and communication capabilities."
        
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(tool_descriptions)
    
    async def orchestrate_workflow(
        self,
        workflow_definition: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate a complex business workflow.
        
        Args:
            workflow_definition: Definition of the workflow steps and dependencies
            input_data: Input data for the workflow
            execution_context: Additional execution context
            
        Returns:
            Workflow execution result
        """
        workflow_input = {
            "query": f"Orchestrate the workflow: {workflow_definition.get('name', 'Unnamed Workflow')}",
            "workflow_definition": workflow_definition,
            "input_data": input_data,
            "execution_mode": "supervised"
        }
        
        context = {
            "operation_type": "workflow_orchestration",
            "workflow_complexity": len(workflow_definition.get("steps", [])),
            "parallel_execution": workflow_definition.get("allow_parallel", False),
            "quality_gates": workflow_definition.get("quality_gates", []),
            "regional_compliance": True
        }
        
        if execution_context:
            context.update(execution_context)
        
        return await self.execute(workflow_input, context)
    
    async def coordinate_agents(
        self,
        task_description: str,
        agent_assignments: List[Dict[str, Any]],
        coordination_strategy: str = "sequential"
    ) -> Dict[str, Any]:
        """
        Coordinate multiple agents to complete a complex task.
        
        Args:
            task_description: Description of the overall task
            agent_assignments: List of agent assignments with tasks
            coordination_strategy: Strategy for coordination (sequential, parallel, hybrid)
            
        Returns:
            Coordination result
        """
        coordination_input = {
            "query": f"Coordinate multiple agents to complete: {task_description}",
            "task_description": task_description,
            "agent_assignments": agent_assignments,
            "coordination_strategy": coordination_strategy,
            "managed_agents": len(self.managed_agents)
        }
        
        context = {
            "operation_type": "agent_coordination",
            "coordination_complexity": len(agent_assignments),
            "strategy": coordination_strategy,
            "monitoring_required": True,
            "escalation_enabled": True
        }
        
        return await self.execute(coordination_input, context)
    
    async def monitor_performance(
        self,
        monitoring_scope: str,
        metrics_config: Dict[str, Any],
        alert_thresholds: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Monitor performance of agents, workflows, or processes.
        
        Args:
            monitoring_scope: Scope of monitoring (agent, workflow, system)
            metrics_config: Configuration for metrics collection
            alert_thresholds: Thresholds for alerts and escalations
            
        Returns:
            Performance monitoring result
        """
        if alert_thresholds is None:
            alert_thresholds = {
                "response_time": 30.0,
                "error_rate": 0.05,
                "success_rate": 0.95,
                "cost_per_operation": 1.0
            }
        
        monitoring_input = {
            "query": f"Monitor performance for {monitoring_scope} with specified metrics and thresholds",
            "monitoring_scope": monitoring_scope,
            "metrics_config": metrics_config,
            "alert_thresholds": alert_thresholds,
            "escalation_rules": self.escalation_rules
        }
        
        context = {
            "operation_type": "performance_monitoring",
            "monitoring_duration": metrics_config.get("duration", "continuous"),
            "alert_enabled": True,
            "dashboard_update": True
        }
        
        return await self.execute(monitoring_input, context)
    
    async def handle_escalation(
        self,
        incident_data: Dict[str, Any],
        escalation_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Handle escalated issues and incidents.
        
        Args:
            incident_data: Data about the incident or issue
            escalation_level: Level of escalation (standard, urgent, critical)
            
        Returns:
            Escalation handling result
        """
        escalation_input = {
            "query": f"Handle {escalation_level} escalation for incident: {incident_data.get('title', 'Unknown Incident')}",
            "incident_data": incident_data,
            "escalation_level": escalation_level,
            "escalation_rules": self.escalation_rules,
            "regional_context": self.config.region
        }
        
        context = {
            "operation_type": "escalation_handling",
            "severity": incident_data.get("severity", "medium"),
            "business_impact": incident_data.get("business_impact", "low"),
            "compliance_risk": incident_data.get("compliance_risk", False),
            "notification_required": True
        }
        
        return await self.execute(escalation_input, context)
    
    async def optimize_workflow(
        self,
        workflow_id: str,
        performance_data: Dict[str, Any],
        optimization_goals: List[str]
    ) -> Dict[str, Any]:
        """
        Optimize workflow based on performance data and goals.
        
        Args:
            workflow_id: Identifier of the workflow to optimize
            performance_data: Historical performance data
            optimization_goals: List of optimization objectives
            
        Returns:
            Workflow optimization recommendations
        """
        optimization_input = {
            "query": f"Optimize workflow {workflow_id} based on performance data and goals",
            "workflow_id": workflow_id,
            "performance_data": performance_data,
            "optimization_goals": optimization_goals,
            "regional_constraints": self._get_regional_constraints()
        }
        
        context = {
            "operation_type": "workflow_optimization",
            "data_period": performance_data.get("period", "30_days"),
            "optimization_scope": "full_workflow",
            "cost_consideration": True,
            "compliance_preservation": True
        }
        
        return await self.execute(optimization_input, context)
    
    def add_managed_agent(self, agent_id: str, agent_type: str, capabilities: List[str]) -> None:
        """Add an agent to the supervision scope."""
        agent_info = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "capabilities": capabilities,
            "status": "active",
            "added_at": self.created_at.isoformat()
        }
        
        self.managed_agents.append(agent_info)
        
        logger.info(
            f"Added agent {agent_id} to supervision scope",
            extra={
                "supervisor_id": self.agent_id,
                "managed_agent_id": agent_id,
                "agent_type": agent_type,
                "tenant_id": self.config.tenant_id
            }
        )
    
    def remove_managed_agent(self, agent_id: str) -> None:
        """Remove an agent from the supervision scope."""
        self.managed_agents = [
            agent for agent in self.managed_agents 
            if agent["agent_id"] != agent_id
        ]
        
        logger.info(
            f"Removed agent {agent_id} from supervision scope",
            extra={
                "supervisor_id": self.agent_id,
                "removed_agent_id": agent_id,
                "tenant_id": self.config.tenant_id
            }
        )
    
    def get_managed_agents(self) -> List[Dict[str, Any]]:
        """Get list of managed agents."""
        return self.managed_agents.copy()
    
    def _get_regional_constraints(self) -> Dict[str, Any]:
        """Get regional constraints for optimization."""
        return {
            "connectivity": self._get_connectivity_profile(),
            "business_hours": self._get_business_hours(),
            "compliance_requirements": self._get_compliance_requirements(),
            "cost_optimization": True,
            "mobile_optimization": True
        }
    
    def _get_connectivity_profile(self) -> Dict[str, Any]:
        """Get connectivity profile for the region."""
        profiles = {
            "NG": {"reliability": "medium", "speed": "medium", "cost": "high"},
            "KE": {"reliability": "high", "speed": "high", "cost": "medium"},
            "ZA": {"reliability": "high", "speed": "high", "cost": "low"},
            "GH": {"reliability": "medium", "speed": "medium", "cost": "medium"},
            "UG": {"reliability": "medium", "speed": "low", "cost": "high"},
            "TZ": {"reliability": "medium", "speed": "medium", "cost": "medium"},
            "RW": {"reliability": "high", "speed": "high", "cost": "medium"},
            "ET": {"reliability": "low", "speed": "low", "cost": "high"},
            "EG": {"reliability": "medium", "speed": "medium", "cost": "medium"},
            "MA": {"reliability": "high", "speed": "high", "cost": "low"}
        }
        
        return profiles.get(self.config.region, profiles["NG"])
    
    def _get_business_hours(self) -> Dict[str, str]:
        """Get local business hours."""
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
    
    def _get_compliance_requirements(self) -> List[str]:
        """Get regional compliance requirements."""
        requirements = {
            "NG": ["cbn_guidelines", "data_protection", "local_content"],
            "KE": ["data_protection_act", "cma_regulations", "kra_compliance"],
            "ZA": ["popia", "fic_act", "companies_act"],
            "GH": ["data_protection_act", "sec_regulations", "gra_compliance"],
            "UG": ["data_protection_act", "cma_regulations", "ura_compliance"],
            "TZ": ["data_protection_act", "cmsa_regulations", "tra_compliance"],
            "RW": ["data_protection_law", "bnr_regulations", "rra_compliance"],
            "ET": ["data_protection_proclamation", "nbe_directives"],
            "EG": ["data_protection_law", "cbe_regulations", "eta_compliance"],
            "MA": ["data_protection_law", "bank_al_maghrib", "tax_compliance"]
        }
        
        return requirements.get(self.config.region, ["general_compliance"])
