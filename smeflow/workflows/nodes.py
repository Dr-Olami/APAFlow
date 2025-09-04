"""
Workflow Nodes for LangGraph workflows.
"""

from typing import Dict, Any, Optional, Callable, List
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
import uuid
import logging
from datetime import datetime

from .state import WorkflowState

logger = logging.getLogger(__name__)


class NodeConfig(BaseModel):
    """Configuration for workflow nodes."""
    
    name: str
    description: Optional[str] = None
    timeout_seconds: int = 300
    retry_on_failure: bool = True
    required_inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    
    # African market specific
    region_specific: bool = False
    supported_regions: List[str] = Field(default_factory=list)
    supported_languages: List[str] = Field(default_factory=list)


class WorkflowNode(ABC):
    """
    Abstract base class for workflow nodes.
    
    All workflow nodes must inherit from this class and implement
    the execute method.
    """
    
    def __init__(self, config: NodeConfig):
        self.config = config
        self.id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
    
    @abstractmethod
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the node logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        pass
    
    def validate_inputs(self, state: WorkflowState) -> bool:
        """
        Validate that required inputs are present in the state.
        
        Args:
            state: Workflow state to validate
            
        Returns:
            True if all required inputs are present
        """
        for required_input in self.config.required_inputs:
            if required_input not in state.data:
                logger.error(f"Missing required input '{required_input}' for node {self.config.name}")
                return False
        return True
    
    def validate_region(self, state: WorkflowState) -> bool:
        """
        Validate region compatibility for African market nodes.
        
        Args:
            state: Workflow state to validate
            
        Returns:
            True if region is supported or not region-specific
        """
        if not self.config.region_specific:
            return True
            
        if not state.region:
            logger.warning(f"No region specified for region-specific node {self.config.name}")
            return True
            
        if state.region not in self.config.supported_regions:
            logger.error(f"Region '{state.region}' not supported by node {self.config.name}")
            return False
            
        return True
    
    async def pre_execute(self, state: WorkflowState) -> bool:
        """
        Pre-execution validation and setup.
        
        Args:
            state: Workflow state
            
        Returns:
            True if node can proceed with execution
        """
        # Set current node
        state.set_current_node(self.config.name)
        
        # Validate inputs
        if not self.validate_inputs(state):
            state.add_error(f"Input validation failed for node {self.config.name}")
            return False
        
        # Validate region
        if not self.validate_region(state):
            state.add_error(f"Region validation failed for node {self.config.name}")
            return False
        
        logger.info(f"Executing node: {self.config.name}")
        return True
    
    async def post_execute(self, state: WorkflowState, success: bool) -> None:
        """
        Post-execution cleanup and logging.
        
        Args:
            state: Workflow state
            success: Whether execution was successful
        """
        if success:
            logger.info(f"Node {self.config.name} completed successfully")
        else:
            logger.error(f"Node {self.config.name} failed")
            
        # Update state timestamp
        state.updated_at = datetime.utcnow()


class BaseNode(WorkflowNode):
    """
    Base implementation of WorkflowNode with common functionality.
    """
    
    def __init__(self, config: NodeConfig, execute_func: Optional[Callable] = None):
        super().__init__(config)
        self.execute_func = execute_func
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the node with pre/post execution hooks.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        # Pre-execution validation
        if not await self.pre_execute(state):
            return state
        
        success = False
        try:
            # Execute the node logic
            if self.execute_func:
                state = await self.execute_func(state)
            else:
                state = await self._execute_logic(state)
            success = True
            
        except Exception as e:
            logger.exception(f"Error in node {self.config.name}: {str(e)}")
            state.add_error(f"Execution error in {self.config.name}: {str(e)}")
            
        finally:
            await self.post_execute(state, success)
        
        return state
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Default execution logic - override in subclasses.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        # Default implementation does nothing
        return state


class StartNode(BaseNode):
    """Start node for workflow initialization."""
    
    def __init__(self):
        config = NodeConfig(
            name="start",
            description="Workflow start node",
            required_inputs=[],
            outputs=["initialized"]
        )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """Initialize workflow state."""
        state.data["initialized"] = True
        state.data["start_time"] = datetime.utcnow().isoformat()
        return state


class EndNode(BaseNode):
    """End node for workflow completion."""
    
    def __init__(self):
        config = NodeConfig(
            name="end",
            description="Workflow end node",
            required_inputs=[],
            outputs=[]
        )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """Complete workflow execution."""
        state.complete()
        state.data["end_time"] = datetime.utcnow().isoformat()
        return state


class AgentNode(BaseNode):
    """Node that executes an agent."""
    
    def __init__(self, agent_id: uuid.UUID, agent_config: Dict[str, Any]):
        config = NodeConfig(
            name=f"agent_{agent_id}",
            description=f"Execute agent {agent_id}",
            required_inputs=["agent_input"],
            outputs=["agent_output"]
        )
        super().__init__(config)
        self.agent_id = agent_id
        self.agent_config = agent_config
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """Execute agent and capture results."""
        # This would integrate with the existing agent system
        # For now, we'll simulate agent execution
        
        agent_input = state.data.get("agent_input", {})
        
        # Simulate agent execution
        agent_result = {
            "agent_id": str(self.agent_id),
            "input": agent_input,
            "output": f"Agent {self.agent_id} processed: {agent_input}",
            "timestamp": datetime.utcnow().isoformat(),
            "cost_usd": 0.01,  # Simulated cost
            "tokens_used": 100  # Simulated tokens
        }
        
        # Store results
        state.data["agent_output"] = agent_result
        state.agent_results[str(self.agent_id)] = agent_result
        
        # Track costs
        state.add_cost(agent_result["cost_usd"], agent_result["tokens_used"])
        
        return state


class ConditionalNode(BaseNode):
    """Node that provides conditional routing."""
    
    def __init__(self, condition_func: Callable[[WorkflowState], str]):
        config = NodeConfig(
            name="conditional",
            description="Conditional routing node",
            required_inputs=["condition_data"],
            outputs=["route"]
        )
        super().__init__(config)
        self.condition_func = condition_func
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """Evaluate condition and set routing."""
        try:
            route = self.condition_func(state)
            state.data["route"] = route
            logger.info(f"Conditional node routing to: {route}")
        except Exception as e:
            logger.exception(f"Error in conditional evaluation: {str(e)}")
            state.add_error(f"Conditional evaluation failed: {str(e)}")
            state.data["route"] = "error"
        
        return state
