"""
Unit tests for workflow self-healing capabilities.
"""

import pytest
import uuid
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from smeflow.workflows.engine import WorkflowEngine
from smeflow.workflows.state import WorkflowState
from smeflow.database.models import WorkflowExecution


class TestWorkflowSelfHealing:
    """Test workflow self-healing and recovery capabilities."""
    
    @pytest.fixture
    def tenant_id(self):
        """Test tenant ID."""
        return "test_tenant"
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = Mock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = AsyncMock()
        return session
    
    @pytest.fixture
    def workflow_engine(self, tenant_id, mock_db_session):
        """Create workflow engine for testing."""
        return WorkflowEngine(tenant_id, mock_db_session)
    
    @pytest.fixture
    def sample_workflow_state(self, tenant_id):
        """Create sample workflow state for testing."""
        return WorkflowState(
            workflow_id=uuid.uuid4(),
            execution_id=uuid.uuid4(),
            tenant_id=tenant_id,
            data={"test_input": "value"},
            context={"region": "NG", "currency": "NGN"}
        )
    
    @pytest.fixture
    def mock_execution_record(self):
        """Create mock execution record."""
        execution = Mock(spec=WorkflowExecution)
        execution.id = uuid.uuid4()
        execution.workflow_id = uuid.uuid4()
        execution.status = "running"
        execution.trigger = "manual"
        execution.input_data = {"test": "data"}
        return execution

    # Test WorkflowState self-healing methods
    def test_can_recover_healthy_state(self, sample_workflow_state):
        """Test can_recover returns True for healthy state."""
        assert sample_workflow_state.can_recover() is True
    
    def test_can_recover_max_attempts_reached(self, sample_workflow_state):
        """Test can_recover returns False when max recovery attempts reached."""
        sample_workflow_state.recovery_attempts = 5
        assert sample_workflow_state.can_recover() is False
    
    def test_can_recover_critical_status(self, sample_workflow_state):
        """Test can_recover returns False for critical health status."""
        sample_workflow_state.health_status = "critical"
        assert sample_workflow_state.can_recover() is False
    
    def test_set_health_status(self, sample_workflow_state):
        """Test setting health status and failure pattern."""
        sample_workflow_state.set_health_status("degraded", "transient")
        assert sample_workflow_state.health_status == "degraded"
        assert sample_workflow_state.failure_pattern == "transient"
    
    def test_set_recovery_strategy(self, sample_workflow_state):
        """Test setting recovery strategy."""
        sample_workflow_state.set_recovery_strategy("retry")
        assert sample_workflow_state.recovery_strategy == "retry"
    
    def test_increment_recovery(self, sample_workflow_state):
        """Test incrementing recovery attempts."""
        initial_attempts = sample_workflow_state.recovery_attempts
        sample_workflow_state.increment_recovery()
        assert sample_workflow_state.recovery_attempts == initial_attempts + 1
        assert sample_workflow_state.health_status == "recovering"
    
    def test_create_checkpoint(self, sample_workflow_state):
        """Test creating checkpoint."""
        checkpoint_data = "test_checkpoint_data"
        sample_workflow_state.create_checkpoint(checkpoint_data)
        assert sample_workflow_state.last_checkpoint == checkpoint_data
    
    def test_is_healthy(self, sample_workflow_state):
        """Test health status check."""
        assert sample_workflow_state.is_healthy() is True
        sample_workflow_state.health_status = "degraded"
        assert sample_workflow_state.is_healthy() is False
    
    def test_needs_intervention(self, sample_workflow_state):
        """Test intervention requirement check."""
        assert sample_workflow_state.needs_intervention() is False
        
        sample_workflow_state.health_status = "critical"
        assert sample_workflow_state.needs_intervention() is True
        
        sample_workflow_state.health_status = "healthy"
        sample_workflow_state.recovery_attempts = 5
        assert sample_workflow_state.needs_intervention() is True

    # Test failure pattern analysis
    def test_analyze_failure_pattern_transient(self, workflow_engine, sample_workflow_state):
        """Test analysis of transient failure patterns."""
        error = "Connection timeout occurred"
        pattern = workflow_engine._analyze_failure_pattern(error, sample_workflow_state)
        assert pattern == "transient"
    
    def test_analyze_failure_pattern_resource(self, workflow_engine, sample_workflow_state):
        """Test analysis of resource failure patterns."""
        error = "Memory limit exceeded"
        pattern = workflow_engine._analyze_failure_pattern(error, sample_workflow_state)
        assert pattern == "resource"
    
    def test_analyze_failure_pattern_persistent(self, workflow_engine, sample_workflow_state):
        """Test analysis of persistent failure patterns."""
        error = "Validation error: required field missing"
        pattern = workflow_engine._analyze_failure_pattern(error, sample_workflow_state)
        assert pattern == "persistent"
    
    def test_analyze_failure_pattern_cascading(self, workflow_engine, sample_workflow_state):
        """Test analysis of cascading failure patterns."""
        # Add multiple errors to trigger cascading pattern
        sample_workflow_state.add_error("Error 1")
        sample_workflow_state.add_error("Error 2")
        sample_workflow_state.add_error("Error 3")
        
        error = "Another error occurred"
        pattern = workflow_engine._analyze_failure_pattern(error, sample_workflow_state)
        assert pattern == "cascading"

    # Test recovery strategy determination
    def test_determine_recovery_strategy_transient_retry(self, workflow_engine, sample_workflow_state):
        """Test recovery strategy for transient failures with retries available."""
        strategy = workflow_engine._determine_recovery_strategy("transient", sample_workflow_state)
        assert strategy == "retry"
    
    def test_determine_recovery_strategy_transient_fallback(self, workflow_engine, sample_workflow_state):
        """Test recovery strategy for transient failures with no retries left."""
        sample_workflow_state.retry_count = 3  # max_retries
        strategy = workflow_engine._determine_recovery_strategy("transient", sample_workflow_state)
        assert strategy == "fallback"
    
    def test_determine_recovery_strategy_resource_rollback(self, workflow_engine, sample_workflow_state):
        """Test recovery strategy for resource failures with checkpoint."""
        sample_workflow_state.last_checkpoint = "checkpoint_data"
        strategy = workflow_engine._determine_recovery_strategy("resource", sample_workflow_state)
        assert strategy == "rollback"
    
    def test_determine_recovery_strategy_resource_skip(self, workflow_engine, sample_workflow_state):
        """Test recovery strategy for resource failures without checkpoint."""
        strategy = workflow_engine._determine_recovery_strategy("resource", sample_workflow_state)
        assert strategy == "skip"
    
    def test_determine_recovery_strategy_persistent(self, workflow_engine, sample_workflow_state):
        """Test recovery strategy for persistent failures."""
        strategy = workflow_engine._determine_recovery_strategy("persistent", sample_workflow_state)
        assert strategy == "skip"
    
    def test_determine_recovery_strategy_cascading(self, workflow_engine, sample_workflow_state):
        """Test recovery strategy for cascading failures."""
        strategy = workflow_engine._determine_recovery_strategy("cascading", sample_workflow_state)
        assert strategy == "fallback"

    # Test recovery methods
    @pytest.mark.asyncio
    async def test_retry_recovery_success(self, workflow_engine, sample_workflow_state, mock_execution_record):
        """Test successful retry recovery."""
        with patch.object(workflow_engine, 'execute_workflow') as mock_execute:
            # Mock successful execution
            successful_state = WorkflowState(
                workflow_id=sample_workflow_state.workflow_id,
                tenant_id=sample_workflow_state.tenant_id,
                status="completed"
            )
            mock_execute.return_value = successful_state
            
            result = await workflow_engine._retry_recovery(sample_workflow_state, mock_execution_record)
            
            assert result is not None
            assert result.status == "completed"
            assert sample_workflow_state.retry_count == 1
            assert sample_workflow_state.last_checkpoint is not None
    
    @pytest.mark.asyncio
    async def test_retry_recovery_failure(self, workflow_engine, sample_workflow_state, mock_execution_record):
        """Test failed retry recovery."""
        with patch.object(workflow_engine, 'execute_workflow') as mock_execute:
            # Mock failed execution
            mock_execute.side_effect = Exception("Retry failed")
            
            result = await workflow_engine._retry_recovery(sample_workflow_state, mock_execution_record)
            
            assert result is None
            assert len(sample_workflow_state.errors) > 0
            assert "Retry failed" in sample_workflow_state.errors[-1]["error"]
    
    @pytest.mark.asyncio
    async def test_rollback_recovery_success(self, workflow_engine, sample_workflow_state, mock_execution_record):
        """Test successful rollback recovery."""
        sample_workflow_state.create_checkpoint("test_checkpoint")
        sample_workflow_state.add_error("Test error")
        
        result = await workflow_engine._rollback_recovery(sample_workflow_state, mock_execution_record)
        
        assert result is not None
        assert result.status == "completed"
        assert result.health_status == "healthy"
        assert len(result.errors) == 0  # Error should be removed
    
    @pytest.mark.asyncio
    async def test_rollback_recovery_no_checkpoint(self, workflow_engine, sample_workflow_state, mock_execution_record):
        """Test rollback recovery without checkpoint."""
        result = await workflow_engine._rollback_recovery(sample_workflow_state, mock_execution_record)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_skip_recovery_success(self, workflow_engine, sample_workflow_state, mock_execution_record):
        """Test successful skip recovery."""
        sample_workflow_state.current_node = "problematic_node"
        
        result = await workflow_engine._skip_recovery(sample_workflow_state, mock_execution_record)
        
        assert result is not None
        assert result.status == "completed"
        assert result.health_status == "degraded"
        assert result.last_checkpoint is not None
        assert len(result.errors) > 0
        assert "Skipped node: problematic_node" in result.errors[-1]["error"]
    
    @pytest.mark.asyncio
    async def test_fallback_recovery_success(self, workflow_engine, sample_workflow_state, mock_execution_record):
        """Test successful fallback recovery."""
        original_data = sample_workflow_state.data.copy()
        
        result = await workflow_engine._fallback_recovery(sample_workflow_state, mock_execution_record)
        
        assert result is not None
        assert result.status == "completed"
        assert result.health_status == "degraded"
        assert result.data["fallback_mode"] is True
        assert result.data["original_data"] == original_data
        assert result.last_checkpoint is not None

    # Test complete recovery flow
    @pytest.mark.asyncio
    async def test_attempt_recovery_cannot_recover(self, workflow_engine, sample_workflow_state, mock_execution_record):
        """Test recovery attempt when workflow cannot recover."""
        sample_workflow_state.recovery_attempts = 5  # Max attempts reached
        
        result = await workflow_engine._attempt_recovery(
            sample_workflow_state, "Test error", mock_execution_record
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_attempt_recovery_retry_strategy(self, workflow_engine, sample_workflow_state, mock_execution_record):
        """Test recovery attempt with retry strategy."""
        with patch.object(workflow_engine, '_retry_recovery') as mock_retry:
            mock_retry.return_value = sample_workflow_state
            sample_workflow_state.status = "completed"
            
            result = await workflow_engine._attempt_recovery(
                sample_workflow_state, "Connection timeout", mock_execution_record
            )
            
            assert result is not None
            assert sample_workflow_state.failure_pattern == "transient"
            assert sample_workflow_state.recovery_strategy == "retry"
            assert sample_workflow_state.health_status == "recovering"
            mock_retry.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_attempt_recovery_unknown_strategy(self, workflow_engine, sample_workflow_state, mock_execution_record):
        """Test recovery attempt with unknown strategy."""
        with patch.object(workflow_engine, '_determine_recovery_strategy') as mock_strategy:
            mock_strategy.return_value = "unknown_strategy"
            
            result = await workflow_engine._attempt_recovery(
                sample_workflow_state, "Test error", mock_execution_record
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_attempt_recovery_exception(self, workflow_engine, sample_workflow_state, mock_execution_record):
        """Test recovery attempt with exception during recovery."""
        with patch.object(workflow_engine, '_retry_recovery') as mock_retry:
            mock_retry.side_effect = Exception("Recovery failed")
            
            result = await workflow_engine._attempt_recovery(
                sample_workflow_state, "Connection timeout", mock_execution_record
            )
            
            assert result is None
            assert sample_workflow_state.health_status == "critical"

    # Test integration with workflow execution
    @pytest.mark.asyncio
    async def test_execute_workflow_with_recovery(self, workflow_engine, sample_workflow_state):
        """Test workflow execution with self-healing recovery."""
        workflow_name = workflow_engine.create_simple_workflow()
        
        with patch.object(workflow_engine, '_attempt_recovery') as mock_recovery:
            # Mock successful recovery
            recovered_state = WorkflowState(
                workflow_id=sample_workflow_state.workflow_id,
                tenant_id=sample_workflow_state.tenant_id,
                status="completed"
            )
            mock_recovery.return_value = recovered_state
            
            # Mock workflow execution to fail first, then recover
            with patch.object(workflow_engine.workflows[workflow_name], 'astream') as mock_stream:
                mock_stream.side_effect = Exception("Simulated failure")
                
                result = await workflow_engine.execute_workflow(workflow_name, sample_workflow_state)
                
                assert result.status == "completed"
                mock_recovery.assert_called_once()

    # Test edge cases and error conditions
    def test_workflow_state_defaults(self):
        """Test WorkflowState default values for self-healing fields."""
        state = WorkflowState(
            workflow_id=uuid.uuid4(),
            tenant_id="test"
        )
        
        assert state.recovery_attempts == 0
        assert state.max_recovery_attempts == 5
        assert state.last_checkpoint is None
        assert state.health_status == "healthy"
        assert state.failure_pattern is None
        assert state.recovery_strategy is None
    
    def test_multiple_recovery_attempts(self, sample_workflow_state):
        """Test multiple recovery attempts tracking."""
        for i in range(3):
            sample_workflow_state.increment_recovery()
        
        assert sample_workflow_state.recovery_attempts == 3
        assert sample_workflow_state.health_status == "recovering"
        
        # Should still be able to recover
        assert sample_workflow_state.can_recover() is True
        
        # Reach max attempts
        sample_workflow_state.recovery_attempts = 5
        assert sample_workflow_state.can_recover() is False
        assert sample_workflow_state.needs_intervention() is True
