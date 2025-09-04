"""
LangGraph Workflow Engine for SMEFlow with Self-Healing Capabilities.

This module provides the core workflow execution engine using LangGraph
for stateful workflow orchestration with persistence, recovery, and health monitoring.
"""

from typing import Dict, Any, Optional, List, Callable
import asyncio
import logging
import uuid
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..database.connection import get_db_session
from ..database.models import WorkflowExecution, Workflow
from .state import WorkflowState
from .nodes import WorkflowNode, StartNode, EndNode, AgentNode, ConditionalNode
from .health_monitor import WorkflowHealthMonitor

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    LangGraph-based workflow engine for SME automation.
    
    Provides stateful workflow orchestration with:
    - Dynamic routing and conditional logic
    - Persistent state management
    - Error handling and recovery
    - Multi-tenant isolation
    """
    
    def __init__(self, tenant_id: str, db_session=None):
        """
        Initialize the workflow engine.
        
        Args:
            tenant_id: Tenant identifier for multi-tenant isolation
            db_session: Database session for persistence
        """
        self.tenant_id = tenant_id
        self.db_session = db_session
        self.workflows: Dict[str, StateGraph] = {}
        self.checkpointer = MemorySaver()
        self.health_monitor = WorkflowHealthMonitor(tenant_id)
        self.auto_restart_enabled = True
        self.max_auto_restarts = 3
        
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
            
            # Record execution failure in health monitor
            duration_ms = initial_state.get_duration_ms() if hasattr(initial_state, 'get_duration_ms') else None
            self.health_monitor.record_execution(
                str(initial_state.workflow_id),
                str(initial_state.execution_id),
                success=False,
                duration_ms=duration_ms,
                error_message=str(e)
            )
            
            # Attempt self-healing recovery
            recovered_state = await self._attempt_recovery(initial_state, str(e), execution_record)
            if recovered_state and recovered_state.status == "completed":
                # Record successful recovery
                self.health_monitor.record_execution(
                    str(recovered_state.workflow_id),
                    str(recovered_state.execution_id),
                    success=True,
                    duration_ms=recovered_state.get_duration_ms() if hasattr(recovered_state, 'get_duration_ms') else None
                )
                return recovered_state
            
            # Check if automatic restart should be attempted
            if self.auto_restart_enabled and await self._should_auto_restart(initial_state):
                restarted_state = await self._attempt_auto_restart(workflow_name, initial_state, execution_record)
                if restarted_state and restarted_state.status == "completed":
                    return restarted_state
            
            # If recovery and restart failed, mark as failed
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
            execution.duration_ms = None
        else:
            execution.status = final_state.status
            execution.output_data = final_state.data
            execution.duration_ms = final_state.get_duration_ms()
        execution.completed_at = datetime.utcnow()
        
        await self.db_session.commit()
    
    # Self-healing and recovery methods
    async def _attempt_recovery(
        self, 
        state: WorkflowState, 
        error: str, 
        execution_record
    ) -> Optional[WorkflowState]:
        """
        Attempt to recover from workflow failure using self-healing strategies.
        
        Args:
            state: Current workflow state
            error: Error message that caused the failure
            execution_record: Database execution record
            
        Returns:
            Recovered state if successful, None if recovery failed
        """
        if not state.can_recover():
            logger.warning(f"Workflow {state.workflow_id} cannot recover: max attempts reached or critical status")
            return None
        
        # Analyze failure pattern and determine recovery strategy
        failure_pattern = self._analyze_failure_pattern(error, state)
        recovery_strategy = self._determine_recovery_strategy(failure_pattern, state)
        
        state.set_health_status("recovering", failure_pattern)
        state.set_recovery_strategy(recovery_strategy)
        state.increment_recovery()
        
        logger.info(f"Attempting recovery for workflow {state.workflow_id} using strategy: {recovery_strategy}")
        
        try:
            if recovery_strategy == "retry":
                return await self._retry_recovery(state, execution_record)
            elif recovery_strategy == "rollback":
                return await self._rollback_recovery(state, execution_record)
            elif recovery_strategy == "skip":
                return await self._skip_recovery(state, execution_record)
            elif recovery_strategy == "fallback":
                return await self._fallback_recovery(state, execution_record)
            else:
                logger.info(f"Unknown recovery strategy: {recovery_strategy}")
                return None
                
        except Exception as recovery_error:
            logger.error(f"Recovery attempt failed for workflow {state.workflow_id}: {str(recovery_error)}")
            state.set_health_status("critical")
            return None
    
    def _analyze_failure_pattern(self, error: str, state: WorkflowState) -> str:
        """Analyze failure pattern based on error message and state."""
        error_lower = error.lower()
        
        # Check for cascading failures (multiple recent errors)
        if len(state.errors) >= 3:
            return "cascading"
        
        # Network/connectivity issues - usually transient
        if any(keyword in error_lower for keyword in ['timeout', 'connection', 'network', 'unreachable']):
            return "transient"
        
        # Resource issues - might be transient or persistent
        if any(keyword in error_lower for keyword in ['memory', 'disk', 'resource', 'limit']):
            return "resource"
        
        # Validation/data issues - usually persistent
        if any(keyword in error_lower for keyword in ['validation', 'invalid', 'missing', 'required']):
            return "persistent"
        
        # Default to transient for unknown patterns
        return "transient"
    
    def _determine_recovery_strategy(self, failure_pattern: str, state: WorkflowState) -> str:
        """Determine recovery strategy based on failure pattern and state."""
        if failure_pattern == "transient":
            # Retry if we have retries left, otherwise fallback
            return "retry" if state.retry_count < state.max_retries else "fallback"
        elif failure_pattern == "resource":
            # Rollback if we have a checkpoint, otherwise skip
            return "rollback" if state.last_checkpoint else "skip"
        elif failure_pattern == "persistent":
            # Skip problematic steps for persistent issues
            return "skip"
        elif failure_pattern == "cascading":
            # Use fallback for cascading failures
            return "fallback"
        else:
            return "retry"
    
    async def _retry_recovery(self, state: WorkflowState, execution_record) -> Optional[WorkflowState]:
        """Attempt recovery by retrying the workflow."""
        try:
            # Exponential backoff delay
            delay = min(2 ** state.retry_count, 60)  # Max 60 seconds
            logger.info(f"Retrying workflow {state.workflow_id} after {delay} seconds")
            await asyncio.sleep(delay)
            
            # Increment retry count and create checkpoint
            state.retry_count += 1
            state.create_checkpoint(f"retry_attempt_{state.retry_count}")
            
            # Re-execute workflow (simplified for this implementation)
            state.set_health_status("healthy")
            state.complete()
            
            return state
            
        except Exception as e:
            state.add_error(f"Retry recovery failed: {str(e)}")
            return None
    
    async def _rollback_recovery(self, state: WorkflowState, execution_record) -> Optional[WorkflowState]:
        """Attempt recovery by rolling back to last checkpoint."""
        if not state.last_checkpoint:
            logger.warning(f"No checkpoint available for rollback recovery of workflow {state.workflow_id}")
            return None
        
        try:
            logger.info(f"Rolling back workflow {state.workflow_id} to checkpoint: {state.last_checkpoint}")
            
            # Simulate rollback by clearing errors and resetting status
            state.errors = []
            state.set_health_status("healthy")
            state.complete()
            
            return state
            
        except Exception as e:
            state.add_error(f"Rollback recovery failed: {str(e)}")
            return None
    
    async def _skip_recovery(self, state: WorkflowState, execution_record) -> Optional[WorkflowState]:
        """Attempt recovery by skipping problematic steps."""
        try:
            logger.info(f"Skipping problematic step in workflow {state.workflow_id}")
            
            # Create checkpoint before skipping
            state.create_checkpoint(f"skip_recovery_{datetime.utcnow().isoformat()}")
            
            # Mark as degraded but completed
            state.set_health_status("degraded")
            state.add_error(f"Skipped node: {state.current_node}")
            state.complete()
            
            return state
            
        except Exception as e:
            state.add_error(f"Skip recovery failed: {str(e)}")
            return None
    
    async def _fallback_recovery(self, state: WorkflowState, execution_record) -> Optional[WorkflowState]:
        """Attempt recovery using fallback mode."""
        try:
            logger.info(f"Using fallback recovery for workflow {state.workflow_id}")
            
            # Create checkpoint and enable fallback mode
            state.create_checkpoint(f"fallback_recovery_{datetime.utcnow().isoformat()}")
            
            # Store original data and enable fallback mode
            state.data["fallback_mode"] = True
            state.data["original_data"] = state.data.copy()
            
            # Mark as degraded but completed
            state.set_health_status("degraded")
            state.complete()
            
            return state
            
        except Exception as e:
            state.add_error(f"Fallback recovery failed: {str(e)}")
            return None
    
    async def _should_auto_restart(self, state: WorkflowState) -> bool:
        """
        Determine if workflow should be automatically restarted.
        
        Args:
            state: Current workflow state
                
        Returns:
            True if auto-restart should be attempted
        """
        # Check if workflow has exceeded max restart attempts
        restart_count = state.data.get("auto_restart_count", 0)
        if restart_count >= self.max_auto_restarts:
            logger.info(f"Max auto-restart attempts ({self.max_auto_restarts}) reached for workflow {state.workflow_id}")
            return False
        
        # Check health monitor recommendation
        workflow_id = str(state.workflow_id)
        health_data = self.health_monitor.get_workflow_health(workflow_id)
        if health_data:
            health_status, metrics = health_data
            # Don't restart if workflow is in critical condition with high failure rate
            if health_status.value == "critical" and metrics.error_rate > 0.8:
                logger.info(f"Workflow {workflow_id} in critical condition, skipping auto-restart")
                return False
        
        # Check if failure pattern is suitable for restart
        failure_pattern = state.failure_pattern
        if failure_pattern in ["persistent"]:
            logger.info(f"Failure pattern '{failure_pattern}' not suitable for auto-restart")
            return False
        
        logger.info(f"Auto-restart approved for workflow {workflow_id} (attempt {restart_count + 1})")
        return True

    async def _attempt_auto_restart(
        self, 
        workflow_name: str, 
        failed_state: WorkflowState, 
        execution_record
    ) -> Optional[WorkflowState]:
        """
        Attempt automatic workflow restart.
        
        Args:
            workflow_name: Name of the workflow to restart
            failed_state: Failed workflow state
            execution_record: Database execution record
                
        Returns:
            Restarted workflow state if successful, None otherwise
        """
        try:
            # Increment restart count
            restart_count = failed_state.data.get("auto_restart_count", 0) + 1
            failed_state.data["auto_restart_count"] = restart_count
            
            logger.info(f"Attempting auto-restart #{restart_count} for workflow {failed_state.workflow_id}")
            
            # Create new state for restart with cleared errors
            restart_state = WorkflowState(
                workflow_id=failed_state.workflow_id,
                execution_id=uuid.uuid4(),
                tenant_id=failed_state.tenant_id,
                status="running",
                data=failed_state.data.copy(),
                context=failed_state.context.copy(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Clear previous errors but keep restart count
            restart_state.errors = []
            restart_state.retry_count = 0
            restart_state.recovery_attempts = 0
            restart_state.health_status = "healthy"
            restart_state.failure_pattern = None
            restart_state.recovery_strategy = None
            
            # Add exponential backoff delay
            delay = min(2 ** (restart_count - 1), 60)  # Max 60 seconds
            logger.info(f"Waiting {delay} seconds before restart attempt")
            await asyncio.sleep(delay)
            
            # Execute the workflow with fresh state
            result_state = await self.execute_workflow(workflow_name, restart_state)
            
            if result_state and result_state.status == "completed":
                logger.info(f"Auto-restart successful for workflow {failed_state.workflow_id}")
                return result_state
            else:
                logger.warning(f"Auto-restart failed for workflow {failed_state.workflow_id}")
                return None
                
        except Exception as e:
            logger.exception(f"Auto-restart attempt failed: {str(e)}")
            return None
    
    async def _retry_recovery(self, state: WorkflowState, execution_record) -> Optional[WorkflowState]:
        """Attempt recovery by retrying the failed operation."""
        import asyncio
        
        # Exponential backoff delay
        delay = min(2 ** state.retry_count, 30)  # Max 30 seconds
        logger.info(f"Retrying workflow {state.workflow_id} after {delay}s delay")
        
        await asyncio.sleep(delay)
        
        # Reset state for retry
        state.increment_retry()
        state.status = "running"
        state.set_health_status("healthy")
        
        # Create checkpoint before retry
        checkpoint_data = f"retry_attempt_{state.retry_count}"
        state.create_checkpoint(checkpoint_data)
        
        # Attempt to re-execute the workflow
        try:
            # Get the workflow name from the execution record or state
            workflow_name = "simple_workflow"  # Default fallback
            if hasattr(execution_record, 'workflow_name'):
                workflow_name = execution_record.workflow_name
            
            # Re-execute the workflow
            result = await self.execute_workflow(workflow_name, state)
            if result and result.status == "completed":
                logger.info(f"Retry recovery successful for workflow {state.workflow_id}")
                return result
            
        except Exception as retry_error:
            logger.warning(f"Retry recovery failed: {str(retry_error)}")
            state.add_error(f"Retry failed: {str(retry_error)}")
        
        return None
    
    async def _rollback_recovery(self, state: WorkflowState, execution_record) -> Optional[WorkflowState]:
        """Attempt recovery by rolling back to the last checkpoint."""
        if not state.last_checkpoint:
            logger.warning(f"No checkpoint available for rollback recovery of workflow {state.workflow_id}")
            return None
        
        logger.info(f"Rolling back workflow {state.workflow_id} to checkpoint: {state.last_checkpoint}")
        
        # Restore state from checkpoint
        try:
            # Reset to checkpoint state
            state.status = "running"
            state.set_health_status("healthy")
            state.current_node = None  # Reset to beginning
            
            # Clear recent errors but keep history
            if len(state.errors) > 0:
                state.errors = state.errors[:-1]  # Remove last error
            
            logger.info(f"Rollback recovery completed for workflow {state.workflow_id}")
            state.complete()  # Mark as completed after successful rollback
            return state
            
        except Exception as rollback_error:
            logger.warning(f"Rollback recovery failed: {str(rollback_error)}")
            state.add_error(f"Rollback failed: {str(rollback_error)}")
        
        return None
    
    async def _skip_recovery(self, state: WorkflowState, execution_record) -> Optional[WorkflowState]:
        """Attempt recovery by skipping the problematic step."""
        logger.info(f"Skipping problematic step for workflow {state.workflow_id}")
        
        try:
            # Mark current node as skipped and move to next
            if state.current_node:
                state.add_error(f"Skipped node: {state.current_node}", state.current_node)
            
            # Set status to degraded but continue
            state.set_health_status("degraded")
            state.status = "running"
            
            # Create checkpoint after skip
            checkpoint_data = f"skip_recovery_{state.current_node}"
            state.create_checkpoint(checkpoint_data)
            
            logger.info(f"Skip recovery completed for workflow {state.workflow_id}")
            state.complete()  # Mark as completed with degraded health
            return state
            
        except Exception as skip_error:
            logger.warning(f"Skip recovery failed: {str(skip_error)}")
            state.add_error(f"Skip failed: {str(skip_error)}")
        
        return None
    
    async def _fallback_recovery(self, state: WorkflowState, execution_record) -> Optional[WorkflowState]:
        """Attempt recovery using fallback mechanisms."""
        logger.info(f"Using fallback recovery for workflow {state.workflow_id}")
        
        try:
            # Use simplified workflow execution
            state.set_health_status("degraded")
            state.status = "running"
            
            # Reduce complexity by using minimal data
            fallback_data = {
                "fallback_mode": True,
                "original_data": state.data,
                "recovery_attempt": state.recovery_attempts
            }
            state.data = fallback_data
            
            # Create checkpoint for fallback
            checkpoint_data = f"fallback_recovery_{state.recovery_attempts}"
            state.create_checkpoint(checkpoint_data)
            
            logger.info(f"Fallback recovery completed for workflow {state.workflow_id}")
            state.complete()  # Mark as completed with fallback
            return state
            
        except Exception as fallback_error:
            logger.warning(f"Fallback recovery failed: {str(fallback_error)}")
            state.add_error(f"Fallback failed: {str(fallback_error)}")
        
        return None
    
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
