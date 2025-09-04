"""
Unit tests for Workflow Manager.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from smeflow.workflows.manager import WorkflowManager
from smeflow.workflows.state import WorkflowState
from smeflow.database.models import Workflow, WorkflowExecution


class TestWorkflowManager:
    """Test cases for WorkflowManager."""
    
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
        session.execute = AsyncMock()
        return session
    
    @pytest.fixture
    def workflow_manager(self, tenant_id, mock_db_session):
        """Create workflow manager for testing."""
        return WorkflowManager(tenant_id, mock_db_session)
    
    @pytest.fixture
    def sample_workflow(self, tenant_id):
        """Create sample workflow."""
        return Workflow(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name="Test Workflow",
            description="Test workflow description",
            template_type="test",
            definition={
                "nodes": [
                    {"name": "start", "type": "start"},
                    {"name": "end", "type": "end"}
                ],
                "edges": [
                    {"from": "start", "to": "end"}
                ]
            },
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    def test_manager_initialization(self, workflow_manager, tenant_id):
        """Test workflow manager initialization."""
        assert workflow_manager.tenant_id == tenant_id
        assert workflow_manager.engine.tenant_id == tenant_id
    
    @pytest.mark.asyncio
    async def test_create_workflow(self, workflow_manager, mock_db_session):
        """Test workflow creation."""
        name = "Test Workflow"
        description = "Test description"
        template_type = "booking_funnel"
        definition = {"nodes": [], "edges": []}
        
        # Mock the workflow creation
        mock_workflow = Mock(spec=Workflow)
        mock_workflow.id = uuid.uuid4()
        mock_workflow.name = name
        mock_workflow.description = description
        mock_workflow.template_type = template_type
        
        with patch('smeflow.workflows.manager.Workflow', return_value=mock_workflow):
            workflow = await workflow_manager.create_workflow(
                name=name,
                description=description,
                template_type=template_type,
                definition=definition
            )
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        assert workflow == mock_workflow
    
    @pytest.mark.asyncio
    async def test_create_workflow_without_db(self, tenant_id):
        """Test workflow creation without database session."""
        manager = WorkflowManager(tenant_id, None)
        
        with pytest.raises(ValueError, match="Database session required"):
            await manager.create_workflow("Test Workflow")
    
    @pytest.mark.asyncio
    async def test_get_workflow(self, workflow_manager, mock_db_session, sample_workflow):
        """Test workflow retrieval."""
        workflow_id = sample_workflow.id
        
        # Mock database query result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_workflow
        mock_db_session.execute.return_value = mock_result
        
        workflow = await workflow_manager.get_workflow(workflow_id)
        
        mock_db_session.execute.assert_called_once()
        assert workflow == sample_workflow
    
    @pytest.mark.asyncio
    async def test_get_workflow_not_found(self, workflow_manager, mock_db_session):
        """Test workflow retrieval when not found."""
        workflow_id = uuid.uuid4()
        
        # Mock database query result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        workflow = await workflow_manager.get_workflow(workflow_id)
        
        assert workflow is None
    
    @pytest.mark.asyncio
    async def test_get_workflow_without_db(self, tenant_id):
        """Test workflow retrieval without database session."""
        manager = WorkflowManager(tenant_id, None)
        
        workflow = await manager.get_workflow(uuid.uuid4())
        assert workflow is None
    
    @pytest.mark.asyncio
    async def test_list_workflows(self, workflow_manager, mock_db_session, sample_workflow):
        """Test workflow listing."""
        # Mock database query result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [sample_workflow]
        mock_db_session.execute.return_value = mock_result
        
        workflows = await workflow_manager.list_workflows()
        
        mock_db_session.execute.assert_called_once()
        assert len(workflows) == 1
        assert workflows[0] == sample_workflow
    
    @pytest.mark.asyncio
    async def test_list_workflows_with_filters(self, workflow_manager, mock_db_session):
        """Test workflow listing with filters."""
        # Mock database query result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result
        
        workflows = await workflow_manager.list_workflows(
            active_only=True,
            template_type="booking_funnel"
        )
        
        mock_db_session.execute.assert_called_once()
        assert workflows == []
    
    @pytest.mark.asyncio
    async def test_update_workflow(self, workflow_manager, mock_db_session, sample_workflow):
        """Test workflow update."""
        workflow_id = sample_workflow.id
        updates = {"name": "Updated Name", "description": "Updated description"}
        
        # Mock get_workflow
        with patch.object(workflow_manager, 'get_workflow', return_value=sample_workflow):
            updated_workflow = await workflow_manager.update_workflow(workflow_id, **updates)
        
        assert updated_workflow.name == "Updated Name"
        assert updated_workflow.description == "Updated description"
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_workflow_not_found(self, workflow_manager, mock_db_session):
        """Test workflow update when workflow not found."""
        workflow_id = uuid.uuid4()
        
        # Mock get_workflow returning None
        with patch.object(workflow_manager, 'get_workflow', return_value=None):
            updated_workflow = await workflow_manager.update_workflow(workflow_id, name="New Name")
        
        assert updated_workflow is None
    
    @pytest.mark.asyncio
    async def test_delete_workflow(self, workflow_manager, mock_db_session, sample_workflow):
        """Test workflow deletion."""
        workflow_id = sample_workflow.id
        
        # Mock get_workflow
        with patch.object(workflow_manager, 'get_workflow', return_value=sample_workflow):
            success = await workflow_manager.delete_workflow(workflow_id)
        
        assert success == True
        mock_db_session.delete.assert_called_once_with(sample_workflow)
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_workflow_not_found(self, workflow_manager, mock_db_session):
        """Test workflow deletion when workflow not found."""
        workflow_id = uuid.uuid4()
        
        # Mock get_workflow returning None
        with patch.object(workflow_manager, 'get_workflow', return_value=None):
            success = await workflow_manager.delete_workflow(workflow_id)
        
        assert success == False
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self, workflow_manager, mock_db_session, sample_workflow):
        """Test workflow execution."""
        workflow_id = sample_workflow.id
        input_data = {"test": "data"}
        context = {"region": "NG"}
        
        # Mock get_workflow
        with patch.object(workflow_manager, 'get_workflow', return_value=sample_workflow):
            # Mock _build_workflow_from_definition
            with patch.object(workflow_manager, '_build_workflow_from_definition', return_value=None):
                # Mock engine execution
                mock_final_state = Mock(spec=WorkflowState)
                mock_final_state.status = "completed"
                with patch.object(workflow_manager.engine, 'execute_workflow', return_value=mock_final_state):
                    final_state = await workflow_manager.execute_workflow(
                        workflow_id, input_data, context
                    )
        
        assert final_state.status == "completed"
    
    @pytest.mark.asyncio
    async def test_execute_workflow_not_found(self, workflow_manager, mock_db_session):
        """Test workflow execution when workflow not found."""
        workflow_id = uuid.uuid4()
        input_data = {"test": "data"}
        
        # Mock get_workflow returning None
        with patch.object(workflow_manager, 'get_workflow', return_value=None):
            with pytest.raises(ValueError, match="Workflow .* not found"):
                await workflow_manager.execute_workflow(workflow_id, input_data)
    
    @pytest.mark.asyncio
    async def test_get_workflow_executions(self, workflow_manager, mock_db_session):
        """Test workflow execution history retrieval."""
        workflow_id = uuid.uuid4()
        
        # Mock execution
        mock_execution = Mock(spec=WorkflowExecution)
        mock_execution.id = uuid.uuid4()
        mock_execution.workflow_id = workflow_id
        mock_execution.status = "completed"
        
        # Mock database query result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_execution]
        mock_db_session.execute.return_value = mock_result
        
        executions = await workflow_manager.get_workflow_executions(workflow_id)
        
        mock_db_session.execute.assert_called_once()
        assert len(executions) == 1
        assert executions[0] == mock_execution
    
    @pytest.mark.asyncio
    async def test_get_workflow_executions_without_db(self, tenant_id):
        """Test workflow execution history without database session."""
        manager = WorkflowManager(tenant_id, None)
        
        executions = await manager.get_workflow_executions(uuid.uuid4())
        assert executions == []
    
    @pytest.mark.asyncio
    async def test_create_booking_funnel_workflow(self, workflow_manager, mock_db_session):
        """Test booking funnel workflow creation."""
        name = "Test Booking Funnel"
        agent_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
        
        # Mock create_workflow
        mock_workflow = Mock(spec=Workflow)
        mock_workflow.id = uuid.uuid4()
        mock_workflow.name = name
        mock_workflow.template_type = "booking_funnel"
        
        with patch.object(workflow_manager, 'create_workflow', return_value=mock_workflow):
            workflow = await workflow_manager.create_booking_funnel_workflow(
                name=name, agent_ids=agent_ids
            )
        
        assert workflow == mock_workflow
    
    @pytest.mark.asyncio
    async def test_create_marketing_campaign_workflow(self, workflow_manager, mock_db_session):
        """Test marketing campaign workflow creation."""
        name = "Test Marketing Campaign"
        region = "KE"
        
        # Mock create_workflow
        mock_workflow = Mock(spec=Workflow)
        mock_workflow.id = uuid.uuid4()
        mock_workflow.name = name
        mock_workflow.template_type = "marketing_campaign"
        
        with patch.object(workflow_manager, 'create_workflow', return_value=mock_workflow):
            workflow = await workflow_manager.create_marketing_campaign_workflow(
                name=name, region=region
            )
        
        assert workflow == mock_workflow
    
    def test_get_default_definition(self, workflow_manager):
        """Test default workflow definition."""
        definition = workflow_manager._get_default_definition()
        
        assert "nodes" in definition
        assert "edges" in definition
        assert "config" in definition
        assert len(definition["nodes"]) == 2
        assert len(definition["edges"]) == 1
    
    @pytest.mark.asyncio
    async def test_build_workflow_from_definition(self, workflow_manager):
        """Test building workflow from definition."""
        workflow_name = "test_workflow"
        definition = {
            "nodes": [
                {"name": "start", "type": "start"},
                {"name": "end", "type": "end"}
            ],
            "edges": [
                {"from": "start", "to": "end"}
            ],
            "conditional_edges": []
        }
        
        await workflow_manager._build_workflow_from_definition(workflow_name, definition)
        
        assert "start" in workflow_manager.engine.node_registry
        assert "end" in workflow_manager.engine.node_registry
        assert "start" in workflow_manager.engine.edge_registry
        assert workflow_name in workflow_manager.engine.workflows
    
    @pytest.mark.asyncio
    async def test_create_node_from_definition_start(self, workflow_manager):
        """Test creating start node from definition."""
        node_def = {"name": "start", "type": "start"}
        
        node = await workflow_manager._create_node_from_definition(node_def)
        
        from smeflow.workflows.nodes import StartNode
        assert isinstance(node, StartNode)
    
    @pytest.mark.asyncio
    async def test_create_node_from_definition_end(self, workflow_manager):
        """Test creating end node from definition."""
        node_def = {"name": "end", "type": "end"}
        
        node = await workflow_manager._create_node_from_definition(node_def)
        
        from smeflow.workflows.nodes import EndNode
        assert isinstance(node, EndNode)
    
    @pytest.mark.asyncio
    async def test_create_node_from_definition_agent(self, workflow_manager):
        """Test creating agent node from definition."""
        agent_id = uuid.uuid4()
        node_def = {
            "name": "agent_node",
            "type": "agent",
            "agent_id": str(agent_id),
            "config": {"type": "automator"}
        }
        
        node = await workflow_manager._create_node_from_definition(node_def)
        
        from smeflow.workflows.nodes import AgentNode
        assert isinstance(node, AgentNode)
        assert node.agent_id == agent_id
    
    @pytest.mark.asyncio
    async def test_create_node_from_definition_unknown(self, workflow_manager):
        """Test creating node from unknown type definition."""
        node_def = {"name": "unknown", "type": "unknown_type"}
        
        node = await workflow_manager._create_node_from_definition(node_def)
        
        # Should default to StartNode for unknown types
        from smeflow.workflows.nodes import StartNode
        assert isinstance(node, StartNode)
