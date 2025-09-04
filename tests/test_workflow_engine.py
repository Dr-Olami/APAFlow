"""
Unit tests for LangGraph Workflow Engine.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from smeflow.workflows.engine import WorkflowEngine
from smeflow.workflows.state import WorkflowState
from smeflow.workflows.nodes import StartNode, EndNode, AgentNode, ConditionalNode, NodeConfig
from smeflow.database.models import Workflow, WorkflowExecution


class TestWorkflowEngine:
    """Test cases for WorkflowEngine."""
    
    @pytest.fixture
    def tenant_id(self):
        """Test tenant ID."""
        return "test_tenant"
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = Mock(spec=AsyncSession)
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
        """Create sample workflow state."""
        return WorkflowState(
            workflow_id=uuid.uuid4(),
            execution_id=uuid.uuid4(),
            tenant_id=tenant_id,
            data={"test_input": "value"},
            context={"region": "NG", "currency": "NGN"}
        )
    
    def test_engine_initialization(self, workflow_engine, tenant_id):
        """Test workflow engine initialization."""
        assert workflow_engine.tenant_id == tenant_id
        assert workflow_engine.workflows == {}
        assert workflow_engine.node_registry == {}
        assert workflow_engine.edge_registry == {}
    
    def test_register_node(self, workflow_engine):
        """Test node registration."""
        node = StartNode()
        workflow_engine.register_node("start", node)
        
        assert "start" in workflow_engine.node_registry
        assert workflow_engine.node_registry["start"] == node
    
    def test_add_edge(self, workflow_engine):
        """Test edge addition."""
        workflow_engine.add_edge("start", "end")
        
        assert "start" in workflow_engine.edge_registry
        assert "end" in workflow_engine.edge_registry["start"]
    
    def test_add_conditional_edge(self, workflow_engine):
        """Test conditional edge addition."""
        def condition_func(state):
            return "success" if state.data.get("success") else "failure"
        
        edge_mapping = {"success": "end", "failure": "retry"}
        workflow_engine.add_conditional_edge("process", condition_func, edge_mapping)
        
        assert hasattr(workflow_engine, 'conditional_edges')
        assert "process" in workflow_engine.conditional_edges
        assert workflow_engine.conditional_edges["process"]["condition_func"] == condition_func
        assert workflow_engine.conditional_edges["process"]["edge_mapping"] == edge_mapping
    
    def test_create_simple_workflow(self, workflow_engine):
        """Test simple workflow creation."""
        workflow_name = workflow_engine.create_simple_workflow()
        
        assert workflow_name == "simple_example"
        assert "start" in workflow_engine.node_registry
        assert "end" in workflow_engine.node_registry
        assert "start" in workflow_engine.edge_registry
        assert "end" in workflow_engine.edge_registry["start"]
        assert workflow_name in workflow_engine.workflows
    
    @pytest.mark.asyncio
    async def test_create_execution_record_without_db(self, workflow_engine):
        """Test execution record creation without database."""
        workflow_engine.db_session = None
        
        workflow_id = uuid.uuid4()
        trigger = "manual"
        input_data = {"test": "data"}
        
        execution = await workflow_engine._create_execution_record(
            workflow_id, trigger, input_data
        )
        
        assert execution.workflow_id == workflow_id
        assert execution.trigger == trigger
        assert execution.status == "running"
        assert execution.input_data == input_data
    
    @pytest.mark.asyncio
    async def test_create_execution_record_with_db(self, workflow_engine, mock_db_session):
        """Test execution record creation with database."""
        workflow_id = uuid.uuid4()
        trigger = "manual"
        input_data = {"test": "data"}
        
        # Mock the execution record
        mock_execution = Mock(spec=WorkflowExecution)
        mock_execution.id = uuid.uuid4()
        mock_execution.workflow_id = workflow_id
        mock_execution.trigger = trigger
        mock_execution.status = "running"
        mock_execution.input_data = input_data
        
        with patch('smeflow.workflows.engine.WorkflowExecution', return_value=mock_execution):
            execution = await workflow_engine._create_execution_record(
                workflow_id, trigger, input_data
            )
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self, workflow_engine, sample_workflow_state):
        """Test simple workflow execution."""
        # Create simple workflow
        workflow_name = workflow_engine.create_simple_workflow()
        
        # Execute workflow
        final_state = await workflow_engine.execute_workflow(
            workflow_name, sample_workflow_state
        )
        
        assert final_state.status == "completed"
        assert final_state.data["initialized"] == True
        assert "start_time" in final_state.data
        assert "end_time" in final_state.data
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_workflow(self, workflow_engine, sample_workflow_state):
        """Test execution of non-existent workflow."""
        with pytest.raises(ValueError, match="Workflow 'nonexistent' not found"):
            await workflow_engine.execute_workflow(
                "nonexistent", sample_workflow_state
            )


class TestWorkflowState:
    """Test cases for WorkflowState."""
    
    @pytest.fixture
    def workflow_state(self):
        """Create sample workflow state."""
        return WorkflowState(
            workflow_id=uuid.uuid4(),
            execution_id=uuid.uuid4(),
            tenant_id="test_tenant",
            data={"input": "test"},
            region="NG",
            currency="NGN"
        )
    
    def test_state_initialization(self, workflow_state):
        """Test workflow state initialization."""
        assert workflow_state.status == "running"
        assert workflow_state.retry_count == 0
        assert workflow_state.max_retries == 3
        assert workflow_state.total_cost_usd == 0.0
        assert workflow_state.tokens_used == 0
        assert workflow_state.region == "NG"
        assert workflow_state.currency == "NGN"
    
    def test_add_error(self, workflow_state):
        """Test error addition."""
        error_msg = "Test error"
        node = "test_node"
        
        workflow_state.add_error(error_msg, node)
        
        assert len(workflow_state.errors) == 1
        assert workflow_state.errors[0]["error"] == error_msg
        assert workflow_state.errors[0]["node"] == node
    
    def test_set_current_node(self, workflow_state):
        """Test current node setting."""
        node = "test_node"
        workflow_state.set_current_node(node)
        
        assert workflow_state.current_node == node
    
    def test_complete(self, workflow_state):
        """Test workflow completion."""
        workflow_state.complete()
        
        assert workflow_state.status == "completed"
        assert workflow_state.completed_at is not None
    
    def test_fail(self, workflow_state):
        """Test workflow failure."""
        error_msg = "Test failure"
        workflow_state.fail(error_msg)
        
        assert workflow_state.status == "failed"
        assert workflow_state.completed_at is not None
        assert len(workflow_state.errors) == 1
        assert workflow_state.errors[0]["error"] == error_msg
    
    def test_pause_resume(self, workflow_state):
        """Test workflow pause and resume."""
        workflow_state.pause()
        assert workflow_state.status == "paused"
        
        workflow_state.resume()
        assert workflow_state.status == "running"
    
    def test_should_retry(self, workflow_state):
        """Test retry logic."""
        assert workflow_state.should_retry() == True
        
        workflow_state.retry_count = 3
        assert workflow_state.should_retry() == False
    
    def test_increment_retry(self, workflow_state):
        """Test retry increment."""
        initial_count = workflow_state.retry_count
        workflow_state.increment_retry()
        
        assert workflow_state.retry_count == initial_count + 1
    
    def test_add_cost(self, workflow_state):
        """Test cost tracking."""
        cost = 0.05
        tokens = 100
        
        workflow_state.add_cost(cost, tokens)
        
        assert workflow_state.total_cost_usd == cost
        assert workflow_state.tokens_used == tokens
    
    def test_get_duration_ms(self, workflow_state):
        """Test duration calculation."""
        # Before completion
        assert workflow_state.get_duration_ms() is None
        
        # After completion
        workflow_state.complete()
        duration = workflow_state.get_duration_ms()
        assert duration is not None
        assert duration >= 0


class TestWorkflowNodes:
    """Test cases for workflow nodes."""
    
    @pytest.fixture
    def sample_state(self):
        """Create sample workflow state."""
        return WorkflowState(
            workflow_id=uuid.uuid4(),
            execution_id=uuid.uuid4(),
            tenant_id="test_tenant",
            data={"agent_input": {"query": "test query"}},
            region="NG"
        )
    
    @pytest.mark.asyncio
    async def test_start_node(self, sample_state):
        """Test start node execution."""
        node = StartNode()
        result_state = await node.execute(sample_state)
        
        assert result_state.data["initialized"] == True
        assert "start_time" in result_state.data
    
    @pytest.mark.asyncio
    async def test_end_node(self, sample_state):
        """Test end node execution."""
        node = EndNode()
        result_state = await node.execute(sample_state)
        
        assert result_state.status == "completed"
        assert "end_time" in result_state.data
    
    @pytest.mark.asyncio
    async def test_agent_node(self, sample_state):
        """Test agent node execution."""
        agent_id = uuid.uuid4()
        agent_config = {"type": "automator"}
        
        node = AgentNode(agent_id, agent_config)
        result_state = await node.execute(sample_state)
        
        assert "agent_output" in result_state.data
        assert str(agent_id) in result_state.agent_results
        assert result_state.total_cost_usd > 0
        assert result_state.tokens_used > 0
    
    @pytest.mark.asyncio
    async def test_conditional_node(self, sample_state):
        """Test conditional node execution."""
        def condition_func(state):
            return "success" if state.data.get("success") else "failure"
        
        sample_state.data["condition_data"] = True
        sample_state.data["success"] = True
        
        node = ConditionalNode(condition_func)
        result_state = await node.execute(sample_state)
        
        assert result_state.data["route"] == "success"
    
    @pytest.mark.asyncio
    async def test_conditional_node_error(self, sample_state):
        """Test conditional node with error."""
        def failing_condition(state):
            raise ValueError("Condition evaluation failed")
        
        sample_state.data["condition_data"] = True
        
        node = ConditionalNode(failing_condition)
        result_state = await node.execute(sample_state)
        
        assert result_state.data["route"] == "error"
        assert len(result_state.errors) > 0
    
    def test_node_config_validation(self):
        """Test node configuration validation."""
        config = NodeConfig(
            name="test_node",
            description="Test node",
            required_inputs=["input1", "input2"],
            outputs=["output1"],
            region_specific=True,
            supported_regions=["NG", "KE"]
        )
        
        assert config.name == "test_node"
        assert config.required_inputs == ["input1", "input2"]
        assert config.region_specific == True
        assert "NG" in config.supported_regions
    
    @pytest.mark.asyncio
    async def test_node_input_validation(self, sample_state):
        """Test node input validation."""
        config = NodeConfig(
            name="test_node",
            required_inputs=["missing_input"]
        )
        
        from smeflow.workflows.nodes import BaseNode
        node = BaseNode(config)
        
        # Should fail validation due to missing input
        result = await node.pre_execute(sample_state)
        assert result == False
        assert len(sample_state.errors) > 0
    
    @pytest.mark.asyncio
    async def test_node_region_validation(self, sample_state):
        """Test node region validation."""
        config = NodeConfig(
            name="test_node",
            region_specific=True,
            supported_regions=["KE", "ZA"]  # NG not supported
        )
        
        from smeflow.workflows.nodes import BaseNode
        node = BaseNode(config)
        
        # Should fail validation due to unsupported region
        result = await node.pre_execute(sample_state)
        assert result == False
        assert len(sample_state.errors) > 0
