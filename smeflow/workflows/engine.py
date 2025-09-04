"""
LangGraph Workflow Engine for SMEFlow.

This module provides the core workflow execution engine using LangGraph
for stateful workflow orchestration with persistence and recovery.
"""

from typing import Dict, Any, Optional, List, Callable
import uuid
import logging
from datetime import datetime
import asyncio

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import WorkflowState
from .nodes import WorkflowNode, StartNode, EndNode
from ..database.models import Workflow, WorkflowExecution
from ..database.connection import get_db_session

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    LangGraph-based workflow engine for SME automation.
    
    Provides stateful workflow orchestration with:
    - Dynamic routing and conditional logic
    - Persistent state management
    - Error handling and recovery
    - Multi-tenant isolation
    - African market optimizations
    """
    
    def __init__(self, tenant_id: str, db_session=None):
        """
        Initialize workflow engine.
        
        Args:
            tenant_id: Tenant identifier for multi-tenant isolation
            db_session: Database session for persistence
        """
        self.tenant_id = tenant_id
        self.db_session = db_session
        self.workflows: Dict[str, StateGraph] = {}
        self.checkpointer = MemorySaver()
        
        # Workflow registry
        self.node_registry: Dict[str, WorkflowNode] = {}
        self.edge_registry: Dict[str, List[str]] = {}
        
        logger.info(f"Initialized WorkflowEngine for tenant: {tenant_id}")
    
    def register_node(self, name: str, node: WorkflowNode) -> None:
        """
        Register a workflow node.
        
        Args:
            name: Node name/identifier
            node: WorkflowNode instance
        """
        self.node_registry[name] = node
        logger.debug(f"Registered node: {name}")
    
    def add_edge(self, from_node: str, to_node: str) -> None:
        """
        Add an edge between workflow nodes.
        
        Args:
            from_node: Source node name
            to_node: Target node name
        """
        if from_node not in self.edge_registry:
            self.edge_registry[from_node] = []
        self.edge_registry[from_node].append(to_node)
        logger.debug(f"Added edge: {from_node} -> {to_node}")
    
    def add_conditional_edge(
        self, 
        from_node: str, 
        condition_func: Callable[[WorkflowState], str],
        edge_mapping: Dict[str, str]
    ) -> None:
        """
        Add a conditional edge with routing logic.
        
        Args:
            from_node: Source node name
            condition_func: Function that returns routing decision
            edge_mapping: Map of condition results to target nodes
        """
        # Store conditional logic for later use in graph building
        if not hasattr(self, 'conditional_edges'):
            self.conditional_edges = {}
        
        self.conditional_edges[from_node] = {
            'condition_func': condition_func,
            'edge_mapping': edge_mapping
        }
        logger.debug(f"Added conditional edge from: {from_node}")
    
    def build_workflow(self, workflow_name: str) -> StateGraph:
        """
        Build a LangGraph workflow from registered nodes and edges.
        
        Args:
            workflow_name: Name of the workflow to build
            
        Returns:
            Configured StateGraph instance
        """
        # Create state graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        for node_name, node in self.node_registry.items():
            workflow.add_node(node_name, self._create_node_executor(node))
        
        # Add regular edges
        for from_node, to_nodes in self.edge_registry.items():
            for to_node in to_nodes:
                workflow.add_edge(from_node, to_node)
        
        # Add conditional edges
        if hasattr(self, 'conditional_edges'):
            for from_node, config in self.conditional_edges.items():
                workflow.add_conditional_edges(
                    from_node,
                    config['condition_func'],
                    config['edge_mapping']
                )
        
        # Set entry point (assume 'start' node exists)
        if 'start' in self.node_registry:
            workflow.set_entry_point('start')
        
        # Add finish edge from 'end' node if it exists
        if 'end' in self.node_registry:
            workflow.add_edge('end', END)
        
        # Compile the workflow
        compiled_workflow = workflow.compile(checkpointer=self.checkpointer)
        self.workflows[workflow_name] = compiled_workflow
        
        logger.info(f"Built workflow: {workflow_name} with {len(self.node_registry)} nodes")
        return compiled_workflow
    
    def _create_node_executor(self, node: WorkflowNode) -> Callable:
        """
        Create an executor function for a workflow node.
        
        Args:
            node: WorkflowNode to create executor for
            
        Returns:
            Async function that executes the node
        """
        async def node_executor(state: WorkflowState) -> WorkflowState:
            """Execute the workflow node."""
            try:
                return await node.execute(state)
            except Exception as e:
                logger.exception(f"Error executing node {node.config.name}: {str(e)}")
                state.add_error(f"Node execution failed: {str(e)}")
                return state
        
        return node_executor
    
    async def execute_workflow(
        self, 
        workflow_name: str, 
        initial_state: WorkflowState,
        config: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """
        Execute a workflow with the given initial state.
        
        Args:
            workflow_name: Name of workflow to execute
            initial_state: Initial workflow state
            config: Optional execution configuration
            
        Returns:
            Final workflow state
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        workflow = self.workflows[workflow_name]
        
        # Create workflow execution record
        execution_record = await self._create_execution_record(
            initial_state.workflow_id,
            "manual",  # trigger type
            initial_state.data
        )
        
        initial_state.execution_id = execution_record.id
        
        try:
            logger.info(f"Starting workflow execution: {workflow_name}")
            
            # Execute workflow with checkpointing
            final_state = None
            async for state in workflow.astream(
                initial_state,
                config=config or {"configurable": {"thread_id": str(initial_state.execution_id)}}
            ):
                final_state = state
                # Update execution record periodically
                await self._update_execution_record(execution_record, state)
            
            if final_state:
                # Final update
                await self._complete_execution_record(execution_record, final_state)
                logger.info(f"Workflow execution completed: {workflow_name}")
                
                # Convert dict back to WorkflowState if needed
                if isinstance(final_state, dict):
                    # LangGraph returns nested dict, extract the actual state
                    # Usually nested under the last node name (e.g., 'end')
                    if len(final_state) == 1:
                        # Get the nested state from the single key
                        nested_state = list(final_state.values())[0]
                        if isinstance(nested_state, dict) and 'workflow_id' in nested_state:
                            return WorkflowState(**nested_state)
                    # If direct conversion fails, return initial state marked as completed
                    initial_state.complete()
                    return initial_state
                return final_state
            else:
                raise RuntimeError("Workflow execution produced no final state")
                
        except Exception as e:
            logger.exception(f"Workflow execution failed: {str(e)}")
            initial_state.fail(str(e))
            await self._fail_execution_record(execution_record, str(e))
            return initial_state
    
    async def resume_workflow(
        self, 
        workflow_name: str, 
        execution_id: uuid.UUID,
        config: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """
        Resume a paused or interrupted workflow.
        
        Args:
            workflow_name: Name of workflow to resume
            execution_id: Execution ID to resume
            config: Optional execution configuration
            
        Returns:
            Final workflow state
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        workflow = self.workflows[workflow_name]
        
        try:
            logger.info(f"Resuming workflow execution: {execution_id}")
            
            # Resume from checkpoint
            final_state = None
            async for state in workflow.astream(
                None,  # No initial state needed for resume
                config=config or {"configurable": {"thread_id": str(execution_id)}}
            ):
                final_state = state
            
            if final_state:
                logger.info(f"Workflow resume completed: {execution_id}")
                return final_state
            else:
                raise RuntimeError("Workflow resume produced no final state")
                
        except Exception as e:
            logger.exception(f"Workflow resume failed: {str(e)}")
            raise
    
    async def _create_execution_record(
        self, 
        workflow_id: uuid.UUID, 
        trigger: str, 
        input_data: Dict[str, Any]
    ) -> WorkflowExecution:
        """Create workflow execution record in database."""
        if not self.db_session:
            # Return mock execution for testing
            execution = WorkflowExecution()
            execution.id = uuid.uuid4()
            execution.workflow_id = workflow_id
            execution.trigger = trigger
            execution.status = "running"
            execution.input_data = input_data
            execution.started_at = datetime.utcnow()
            return execution
        
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            trigger=trigger,
            status="running",
            input_data=input_data
        )
        
        self.db_session.add(execution)
        await self.db_session.commit()
        await self.db_session.refresh(execution)
        
        return execution
    
    async def _update_execution_record(
        self, 
        execution: WorkflowExecution, 
        state
    ) -> None:
        """Update workflow execution record with current state."""
        if not self.db_session:
            return
        
        # Handle both dict and WorkflowState objects
        if isinstance(state, dict):
            execution.status = state.get("status", "running")
            execution.output_data = state.get("data", {})
            errors = state.get("errors", [])
        else:
            execution.status = state.status
            execution.output_data = state.data
            errors = state.errors
        
        if errors:
            execution.error_message = "; ".join([e.get("error", "") for e in errors])
        
        await self.db_session.commit()
    
    async def _complete_execution_record(
        self, 
        execution: WorkflowExecution, 
        final_state
    ) -> None:
        """Complete workflow execution record."""
        if not self.db_session:
            return
        
        # Handle both dict and WorkflowState objects
        if isinstance(final_state, dict):
            execution.status = final_state.get("status", "completed")
            execution.output_data = final_state.get("data", {})
            # Can't get duration from dict, set to None
            execution.duration_ms = None
        else:
            execution.status = final_state.status
            execution.output_data = final_state.data
            execution.duration_ms = final_state.get_duration_ms()
        
        execution.completed_at = datetime.utcnow()
        await self.db_session.commit()
    
    async def _fail_execution_record(
        self, 
        execution: WorkflowExecution, 
        error_message: str
    ) -> None:
        """Mark workflow execution as failed."""
        if not self.db_session:
            return
        
        execution.status = "failed"
        execution.completed_at = datetime.utcnow()
        execution.error_message = error_message
        
        await self.db_session.commit()
    
    def create_simple_workflow(self) -> str:
        """
        Create a simple example workflow for testing.
        
        Returns:
            Name of the created workflow
        """
        workflow_name = "simple_example"
        
        # Clear existing registration
        self.node_registry.clear()
        self.edge_registry.clear()
        
        # Register nodes
        self.register_node("start", StartNode())
        self.register_node("end", EndNode())
        
        # Add edges
        self.add_edge("start", "end")
        
        # Build workflow
        self.build_workflow(workflow_name)
        
        return workflow_name
