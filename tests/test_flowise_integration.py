"""
Unit tests for Flowise Integration components.

Tests the Flowise-to-LangGraph bridge, workflow execution,
and export/import functionality with multi-tenant isolation.
"""

import pytest
import uuid
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from smeflow.workflows.flowise_bridge import (
    FlowiseBridge, 
    FlowiseWorkflowExecutor,
    FlowiseWorkflowData,
    FlowiseNodeData,
    FlowiseEdgeData,
    WorkflowTranslationResult
)
from smeflow.workflows.export_import import (
    WorkflowExportImportService,
    WorkflowExportRequest,
    WorkflowImportRequest,
    WorkflowExportFormat
)
from smeflow.workflows.state import WorkflowState


class TestFlowiseBridge:
    """Test cases for FlowiseBridge functionality."""
    
    @pytest.fixture
    def tenant_id(self):
        """Test tenant ID."""
        return "550e8400-e29b-41d4-a716-446655440000"
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def flowise_bridge(self, tenant_id, mock_db_session):
        """FlowiseBridge instance for testing."""
        return FlowiseBridge(tenant_id, mock_db_session)
    
    @pytest.fixture
    def sample_flowise_workflow(self, tenant_id):
        """Sample Flowise workflow data."""
        return FlowiseWorkflowData(
            id="workflow-123",
            name="Test Workflow",
            description="Test workflow for unit testing",
            tenant_id=tenant_id,
            nodes=[
                FlowiseNodeData(
                    id="start-1",
                    type="startNode",
                    data={"label": "Start"},
                    position={"x": 0, "y": 0}
                ),
                FlowiseNodeData(
                    id="automator-1",
                    type="smeflowAutomator",
                    data={
                        "label": "Automator",
                        "taskType": "api_integration",
                        "taskConfig": '{"priority": "high"}',
                        "inputData": '{"test": "data"}',
                        "marketConfig": '{"region": "nigeria", "currency": "NGN"}'
                    },
                    position={"x": 200, "y": 0}
                ),
                FlowiseNodeData(
                    id="end-1",
                    type="endNode",
                    data={"label": "End"},
                    position={"x": 400, "y": 0}
                )
            ],
            edges=[
                FlowiseEdgeData(
                    id="edge-1",
                    source="start-1",
                    target="automator-1"
                ),
                FlowiseEdgeData(
                    id="edge-2",
                    source="automator-1",
                    target="end-1"
                )
            ]
        )
    
    @pytest.mark.asyncio
    async def test_translate_workflow_success(self, flowise_bridge, sample_flowise_workflow):
        """Test successful workflow translation."""
        result = await flowise_bridge.translate_workflow(sample_flowise_workflow)
        
        assert result.success is True
        assert result.workflow_name == "Test Workflow"
        assert result.langgraph_definition is not None
        assert len(result.errors) == 0
        
        # Check LangGraph definition structure
        definition = result.langgraph_definition
        assert definition['name'] == "Test Workflow"
        assert definition['tenant_id'] == flowise_bridge.tenant_id
        assert len(definition['nodes']) == 3
        assert len(definition['edges']) == 2
        
        # Check node mappings
        assert len(result.node_mappings) == 3
        assert "start-1" in result.node_mappings
        assert "automator-1" in result.node_mappings
        assert "end-1" in result.node_mappings
    
    @pytest.mark.asyncio
    async def test_translate_workflow_tenant_mismatch(self, flowise_bridge, sample_flowise_workflow):
        """Test workflow translation with tenant mismatch."""
        # Change tenant ID to cause mismatch
        sample_flowise_workflow.tenant_id = "different-tenant-id"
        
        result = await flowise_bridge.translate_workflow(sample_flowise_workflow)
        
        assert result.success is False
        assert len(result.errors) > 0
        assert "Tenant mismatch" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_translate_agent_node(self, flowise_bridge):
        """Test translation of SMEFlow agent nodes."""
        automator_node = FlowiseNodeData(
            id="automator-test",
            type="smeflowAutomator",
            data={
                "taskType": "payment_mpesa",
                "taskConfig": '{"business_short_code": "174379"}',
                "inputData": '{"amount": 1000, "phone": "+254700000000"}',
                "marketConfig": '{"region": "kenya", "currency": "KES"}'
            },
            position={"x": 100, "y": 100}
        )
        
        base_node = {
            'name': 'node_automator_test',
            'type': 'automator_agent',
            'flowise_id': 'automator-test',
            'position': {"x": 100, "y": 100},
            'config': automator_node.data.copy()
        }
        
        result = await flowise_bridge._translate_agent_node(automator_node, base_node)
        
        assert result['requires_agent'] is True
        assert 'agent_config' in result
        
        agent_config = result['agent_config']
        assert agent_config['task_type'] == 'payment_mpesa'
        assert agent_config['tenant_id'] == flowise_bridge.tenant_id
        assert 'market_config' in agent_config
        assert agent_config['market_config']['region'] == 'kenya'
        assert agent_config['market_config']['currency'] == 'KES'
    
    @pytest.mark.asyncio
    async def test_execute_flowise_workflow(self, flowise_bridge, sample_flowise_workflow):
        """Test execution of Flowise workflow through LangGraph."""
        input_data = {"customer_name": "John Doe", "service": "consultation"}
        context = {"priority": "high", "source": "test"}
        
        # Mock the workflow engine execution
        with patch.object(flowise_bridge, '_build_langgraph_workflow', new_callable=AsyncMock) as mock_build:
            with patch('smeflow.workflows.flowise_bridge.WorkflowEngine') as mock_engine_class:
                mock_engine = Mock()
                mock_engine_class.return_value = mock_engine
                
                # Mock successful execution
                mock_final_state = WorkflowState(
                    workflow_id=uuid.uuid4(),
                    execution_id=uuid.uuid4(),
                    tenant_id=flowise_bridge.tenant_id,
                    data=input_data,
                    context=context,
                    status="completed"
                )
                mock_engine.execute_workflow = AsyncMock(return_value=mock_final_state)
                
                result = await flowise_bridge.execute_flowise_workflow(
                    sample_flowise_workflow,
                    input_data,
                    context
                )
                
                assert result.status == "completed"
                assert result.tenant_id == flowise_bridge.tenant_id
                assert result.data == input_data
                
                # Verify workflow was built and executed
                mock_build.assert_called_once()
                mock_engine.execute_workflow.assert_called_once()


class TestFlowiseWorkflowExecutor:
    """Test cases for FlowiseWorkflowExecutor."""
    
    @pytest.fixture
    def tenant_id(self):
        """Test tenant ID."""
        return "550e8400-e29b-41d4-a716-446655440000"
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def workflow_executor(self, tenant_id, mock_db_session):
        """FlowiseWorkflowExecutor instance for testing."""
        return FlowiseWorkflowExecutor(tenant_id, mock_db_session)
    
    @pytest.mark.asyncio
    async def test_execute_workflow_with_cache(self, workflow_executor):
        """Test workflow execution with caching."""
        workflow_data = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "tenant_id": workflow_executor.tenant_id,
            "nodes": [],
            "edges": []
        }
        input_data = {"test": "data"}
        
        # Mock the bridge execution
        with patch.object(workflow_executor.bridge, 'execute_flowise_workflow', new_callable=AsyncMock) as mock_execute:
            mock_final_state = WorkflowState(
                workflow_id=uuid.uuid4(),
                execution_id=uuid.uuid4(),
                tenant_id=workflow_executor.tenant_id,
                data=input_data,
                status="completed"
            )
            mock_execute.return_value = mock_final_state
            
            result = await workflow_executor.execute_workflow(
                workflow_data,
                input_data,
                use_cache=True
            )
            
            assert result.status == "completed"
            assert result.tenant_id == workflow_executor.tenant_id
            
            # Check cache was populated
            cache_key = f"test-workflow_{workflow_executor.tenant_id}"
            assert cache_key in workflow_executor._workflow_cache
    
    def test_clear_cache(self, workflow_executor):
        """Test cache clearing functionality."""
        # Add some cache entries
        workflow_executor._workflow_cache["test-1"] = {"timestamp": datetime.utcnow()}
        workflow_executor._workflow_cache["test-2"] = {"timestamp": datetime.utcnow()}
        
        assert len(workflow_executor._workflow_cache) == 2
        
        workflow_executor.clear_cache()
        
        assert len(workflow_executor._workflow_cache) == 0


class TestWorkflowExportImport:
    """Test cases for workflow export/import functionality."""
    
    @pytest.fixture
    def tenant_id(self):
        """Test tenant ID."""
        return "550e8400-e29b-41d4-a716-446655440000"
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def export_import_service(self, tenant_id, mock_db_session):
        """WorkflowExportImportService instance for testing."""
        return WorkflowExportImportService(tenant_id, mock_db_session)
    
    @pytest.fixture
    def sample_workflow(self, tenant_id):
        """Sample workflow for testing."""
        workflow = Mock()
        workflow.id = uuid.uuid4()
        workflow.name = "Test Workflow"
        workflow.description = "Test workflow description"
        workflow.template_type = "consulting"
        workflow.tenant_id = tenant_id
        workflow.is_active = True
        workflow.version = 1
        workflow.created_at = datetime.utcnow()
        workflow.updated_at = datetime.utcnow()
        workflow.definition = {
            "nodes": [
                {"name": "start", "type": "start"},
                {"name": "end", "type": "end"}
            ],
            "edges": [
                {"from": "start", "to": "end"}
            ]
        }
        return workflow
    
    @pytest.mark.asyncio
    async def test_export_workflow_json(self, export_import_service, sample_workflow):
        """Test workflow export to JSON format."""
        request = WorkflowExportRequest(
            workflow_id=str(sample_workflow.id),
            format=WorkflowExportFormat.JSON,
            include_metadata=True,
            african_market_config=True
        )
        
        # Mock the _get_workflow method
        with patch.object(export_import_service, '_get_workflow', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_workflow
            
            result = await export_import_service.export_workflow(request)
            
            assert result.success is True
            assert result.workflow_id == str(sample_workflow.id)
            assert result.format == WorkflowExportFormat.JSON
            assert result.exported_data is not None
            
            # Check exported data structure
            exported_data = result.exported_data
            assert exported_data['name'] == sample_workflow.name
            assert exported_data['tenant_id'] == sample_workflow.tenant_id
            assert 'metadata' in exported_data
            assert 'african_market_config' in exported_data
    
    @pytest.mark.asyncio
    async def test_export_workflow_flowise_format(self, export_import_service, sample_workflow):
        """Test workflow export to Flowise format."""
        request = WorkflowExportRequest(
            workflow_id=str(sample_workflow.id),
            format=WorkflowExportFormat.FLOWISE
        )
        
        with patch.object(export_import_service, '_get_workflow', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_workflow
            
            result = await export_import_service.export_workflow(request)
            
            assert result.success is True
            assert result.exported_data is not None
            
            # Check Flowise format structure
            flowise_data = result.exported_data
            assert 'nodes' in flowise_data
            assert 'edges' in flowise_data
            assert 'viewport' in flowise_data
            assert flowise_data['tenant_id'] == sample_workflow.tenant_id
    
    @pytest.mark.asyncio
    async def test_import_workflow_json(self, export_import_service):
        """Test workflow import from JSON format."""
        workflow_data = {
            "name": "Imported Workflow",
            "description": "Imported from JSON",
            "definition": {
                "nodes": [
                    {"name": "start", "type": "start"},
                    {"name": "end", "type": "end"}
                ],
                "edges": [
                    {"from": "start", "to": "end"}
                ]
            }
        }
        
        request = WorkflowImportRequest(
            workflow_data=workflow_data,
            source_format=WorkflowExportFormat.JSON,
            tenant_id=export_import_service.tenant_id,
            validate_before_import=True
        )
        
        # Mock the workflow manager
        with patch('smeflow.workflows.manager.WorkflowManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            
            mock_workflow = Mock()
            mock_workflow.id = uuid.uuid4()
            mock_manager.create_workflow = AsyncMock(return_value=mock_workflow)
            
            result = await export_import_service.import_workflow(request)
            
            assert result.success is True
            assert result.imported_workflow_id == str(mock_workflow.id)
            assert result.source_format == WorkflowExportFormat.JSON
            
            # Verify workflow was created
            mock_manager.create_workflow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_import_workflow_flowise_format(self, export_import_service):
        """Test workflow import from Flowise format."""
        flowise_data = {
            "id": "flowise-workflow-123",
            "name": "Flowise Workflow",
            "description": "Imported from Flowise",
            "tenant_id": export_import_service.tenant_id,
            "nodes": [
                {
                    "id": "start-1",
                    "type": "startNode",
                    "data": {"label": "Start"},
                    "position": {"x": 0, "y": 0}
                }
            ],
            "edges": []
        }
        
        request = WorkflowImportRequest(
            workflow_data=flowise_data,
            source_format=WorkflowExportFormat.FLOWISE,
            tenant_id=export_import_service.tenant_id
        )
        
        # Mock the Flowise bridge translation
        with patch.object(export_import_service.flowise_bridge, 'translate_workflow', new_callable=AsyncMock) as mock_translate:
            mock_translation_result = Mock()
            mock_translation_result.success = True
            mock_translation_result.langgraph_definition = {
                "name": "Flowise Workflow",
                "description": "Imported from Flowise",
                "nodes": [],
                "edges": []
            }
            mock_translate.return_value = mock_translation_result
            
            # Mock the workflow manager
            with patch('smeflow.workflows.manager.WorkflowManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                mock_workflow = Mock()
                mock_workflow.id = uuid.uuid4()
                mock_manager.create_workflow = AsyncMock(return_value=mock_workflow)
                
                result = await export_import_service.import_workflow(request)
                
                assert result.success is True
                assert result.source_format == WorkflowExportFormat.FLOWISE
                
                # Verify translation and creation were called
                mock_translate.assert_called_once()
                mock_manager.create_workflow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_import_data_flowise(self, export_import_service):
        """Test validation of Flowise import data."""
        # Valid Flowise data
        valid_data = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "nodes": [],
            "edges": [],
            "tenant_id": export_import_service.tenant_id
        }
        
        result = await export_import_service._validate_import_data(
            valid_data, 
            WorkflowExportFormat.FLOWISE
        )
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
        
        # Invalid Flowise data (missing required fields)
        invalid_data = {
            "name": "Test Workflow"
            # Missing id, nodes, edges
        }
        
        result = await export_import_service._validate_import_data(
            invalid_data,
            WorkflowExportFormat.FLOWISE
        )
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert any("Missing required field" in error for error in result['errors'])
    
    @pytest.mark.asyncio
    async def test_export_workflow_not_found(self, export_import_service):
        """Test export of non-existent workflow."""
        request = WorkflowExportRequest(
            workflow_id="non-existent-workflow",
            format=WorkflowExportFormat.JSON
        )
        
        # Mock _get_workflow to return None
        with patch.object(export_import_service, '_get_workflow', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            result = await export_import_service.export_workflow(request)
            
            assert result.success is False
            assert len(result.errors) > 0
            assert "Workflow not found" in result.errors[0]


class TestAfricanMarketOptimizations:
    """Test cases for African market-specific optimizations."""
    
    def test_african_market_config_detection(self):
        """Test detection of African market configuration in nodes."""
        from smeflow.api.flowise_integration_routes import _check_african_market_config
        
        # Node with African market config
        node_with_config = {
            "marketConfig": {
                "region": "nigeria",
                "currency": "NGN",
                "timezone": "Africa/Lagos",
                "languages": ["en", "ha", "yo"]
            }
        }
        
        assert _check_african_market_config(node_with_config) is True
        
        # Node without African market config
        node_without_config = {
            "taskType": "api_integration",
            "inputData": {"test": "data"}
        }
        
        assert _check_african_market_config(node_without_config) is False
        
        # Node with JSON string config
        node_with_json_config = {
            "marketConfig": '{"region": "kenya", "currency": "KES"}'
        }
        
        assert _check_african_market_config(node_with_json_config) is True
    
    def test_multi_language_support_check(self):
        """Test multi-language support validation."""
        from smeflow.api.flowise_integration_routes import _check_multi_language_support
        from smeflow.workflows.flowise_bridge import FlowiseWorkflowData, FlowiseNodeData
        
        # Workflow with African languages
        workflow_with_languages = FlowiseWorkflowData(
            id="test-workflow",
            name="Test Workflow",
            tenant_id="test-tenant",
            nodes=[
                FlowiseNodeData(
                    id="node-1",
                    type="smeflowAutomator",
                    data={
                        "marketConfig": {
                            "languages": ["en", "ha", "yo", "ig"]
                        }
                    },
                    position={"x": 0, "y": 0}
                )
            ],
            edges=[]
        )
        
        result = _check_multi_language_support(workflow_with_languages)
        
        assert result['supported'] is True
        assert result['african_languages_supported'] is True
        assert 'ha' in result['languages_found']
        assert 'yo' in result['languages_found']
    
    def test_currency_handling_check(self):
        """Test currency handling validation."""
        from smeflow.api.flowise_integration_routes import _check_currency_handling
        from smeflow.workflows.flowise_bridge import FlowiseWorkflowData, FlowiseNodeData
        
        # Workflow with African currencies
        workflow_with_currencies = FlowiseWorkflowData(
            id="test-workflow",
            name="Test Workflow", 
            tenant_id="test-tenant",
            nodes=[
                FlowiseNodeData(
                    id="node-1",
                    type="smeflowAutomator",
                    data={
                        "marketConfig": {
                            "currency": "NGN"
                        }
                    },
                    position={"x": 0, "y": 0}
                ),
                FlowiseNodeData(
                    id="node-2",
                    type="smeflowMentor",
                    data={
                        "marketConfig": {
                            "currency": "KES"
                        }
                    },
                    position={"x": 200, "y": 0}
                )
            ],
            edges=[]
        )
        
        result = _check_currency_handling(workflow_with_currencies)
        
        assert result['supported'] is True
        assert result['african_currencies_supported'] is True
        assert 'NGN' in result['currencies_found']
        assert 'KES' in result['currencies_found']


if __name__ == "__main__":
    pytest.main([__file__])
