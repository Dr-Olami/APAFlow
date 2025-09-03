"""
Unit tests for SMEFlow N8n integration.

Tests the n8n wrapper, workflow management, and API routes with proper
mocking and tenant isolation validation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

from smeflow.integrations.n8n_wrapper import SMEFlowN8nClient, N8nConfig, WorkflowTemplate
from smeflow.auth.jwt_middleware import UserInfo


class TestN8nConfig:
    """Test N8n configuration model."""
    
    def test_config_creation(self):
        """Test creating N8n configuration."""
        config = N8nConfig(
            api_key="test-key",
            base_url="http://localhost:5678",
            timeout=30
        )
        
        assert config.api_key == "test-key"
        assert config.base_url == "http://localhost:5678"
        assert config.timeout == 30
        assert config.tenant_prefix == "smeflow"
    
    def test_base_url_validation(self):
        """Test base URL validation removes trailing slash."""
        config = N8nConfig(
            api_key="test-key",
            base_url="http://localhost:5678/"
        )
        
        assert config.base_url == "http://localhost:5678"


class TestWorkflowTemplate:
    """Test workflow template model."""
    
    def test_template_creation(self):
        """Test creating workflow template."""
        template = WorkflowTemplate(
            id="test_template",
            name="Test Template",
            description="Test description",
            category="retail",
            nodes=[{"id": "node1", "type": "webhook"}],
            connections={"node1": {"main": [["node2"]]}},
            tags=["test", "retail"]
        )
        
        assert template.id == "test_template"
        assert template.category == "retail"
        assert template.african_optimized is True
        assert template.compliance_level == "standard"


class TestSMEFlowN8nClient:
    """Test SMEFlow N8n client wrapper."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock N8n configuration."""
        return N8nConfig(
            api_key="test-api-key",
            base_url="http://localhost:5678",
            timeout=30,
            tenant_prefix="test"
        )
    
    @pytest.fixture
    def mock_user_info(self):
        """Mock user information."""
        return UserInfo(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            tenant_id="tenant123",
            roles=["user"]
        )
    
    @pytest.fixture
    def n8n_client(self, mock_config):
        """Create N8n client with mock config."""
        with patch('smeflow.integrations.n8n_wrapper.get_settings') as mock_settings:
            mock_settings.return_value.N8N_API_KEY = "test-key"
            client = SMEFlowN8nClient(config=mock_config)
            return client
    
    def test_client_initialization(self, n8n_client):
        """Test client initialization."""
        assert n8n_client.config.api_key == "test-api-key"
        assert len(n8n_client._templates) == 3  # product_recommender, local_discovery, support_agent
        assert "product_recommender" in n8n_client._templates
        assert "local_discovery" in n8n_client._templates
        assert "support_agent" in n8n_client._templates
    
    def test_get_available_templates(self, n8n_client):
        """Test getting available templates."""
        templates = n8n_client.get_available_templates()
        
        assert len(templates) == 3
        assert all("id" in template for template in templates)
        assert all("name" in template for template in templates)
        assert all("category" in template for template in templates)
        
        # Check specific template
        product_template = next(t for t in templates if t["id"] == "product_recommender")
        assert product_template["category"] == "retail"
        assert product_template["african_optimized"] is True
    
    def test_tenant_workflow_name_generation(self, n8n_client):
        """Test tenant-specific workflow name generation."""
        workflow_name = n8n_client._get_tenant_workflow_name("Test Workflow", "tenant123")
        assert workflow_name == "test_tenant123_Test Workflow"
    
    @pytest.mark.asyncio
    async def test_get_client(self, n8n_client):
        """Test getting N8n client instance."""
        with patch('smeflow.integrations.n8n_wrapper.N8nClient') as mock_n8n_client:
            mock_instance = AsyncMock()
            mock_n8n_client.return_value = mock_instance
            
            client = await n8n_client.get_client("tenant123")
            
            assert client == mock_instance
            mock_n8n_client.assert_called_once_with(
                base_url="http://localhost:5678",
                api_key="test-api-key"
            )
    
    @pytest.mark.asyncio
    async def test_create_workflow_from_template_success(self, n8n_client, mock_user_info):
        """Test successful workflow creation from template."""
        mock_workflow = MagicMock()
        mock_workflow.id = "workflow123"
        mock_workflow.dict.return_value = {"id": "workflow123", "name": "test_workflow"}
        
        with patch.object(n8n_client, 'get_client') as mock_get_client, \
             patch.object(n8n_client, '_log_workflow_action') as mock_log:
            
            mock_client = AsyncMock()
            mock_client.create_workflow.return_value = mock_workflow
            mock_get_client.return_value = mock_client
            
            result = await n8n_client.create_workflow_from_template(
                template_id="product_recommender",
                tenant_id="tenant123",
                user_info=mock_user_info
            )
            
            assert result["id"] == "workflow123"
            mock_client.create_workflow.assert_called_once()
            mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_workflow_invalid_template(self, n8n_client, mock_user_info):
        """Test workflow creation with invalid template."""
        with pytest.raises(ValueError, match="Template 'invalid_template' not found"):
            await n8n_client.create_workflow_from_template(
                template_id="invalid_template",
                tenant_id="tenant123",
                user_info=mock_user_info
            )
    
    @pytest.mark.asyncio
    async def test_execute_workflow_success(self, n8n_client, mock_user_info):
        """Test successful workflow execution."""
        mock_execution = MagicMock()
        mock_execution.id = "execution123"
        mock_execution.dict.return_value = {"id": "execution123", "status": "success"}
        
        with patch.object(n8n_client, 'get_client') as mock_get_client, \
             patch.object(n8n_client, '_log_workflow_action') as mock_log:
            
            mock_client = AsyncMock()
            mock_client.execute_workflow.return_value = mock_execution
            mock_get_client.return_value = mock_client
            
            result = await n8n_client.execute_workflow(
                workflow_id="workflow123",
                tenant_id="tenant123",
                user_info=mock_user_info,
                input_data={"test": "data"}
            )
            
            assert result["id"] == "execution123"
            mock_client.execute_workflow.assert_called_once_with(
                workflow_id="workflow123",
                input_data={"test": "data"}
            )
            mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_tenant_workflows(self, n8n_client, mock_user_info):
        """Test listing tenant workflows."""
        mock_workflow1 = MagicMock()
        mock_workflow1.name = "test_tenant123_Workflow1"
        mock_workflow1.active = True
        mock_workflow1.dict.return_value = {"name": "test_tenant123_Workflow1", "active": True}
        
        mock_workflow2 = MagicMock()
        mock_workflow2.name = "test_tenant123_Workflow2"
        mock_workflow2.active = False
        mock_workflow2.dict.return_value = {"name": "test_tenant123_Workflow2", "active": False}
        
        mock_workflow3 = MagicMock()
        mock_workflow3.name = "other_tenant_Workflow3"
        mock_workflow3.active = True
        mock_workflow3.dict.return_value = {"name": "other_tenant_Workflow3", "active": True}
        
        mock_workflow_list = MagicMock()
        mock_workflow_list.data = [mock_workflow1, mock_workflow2, mock_workflow3]
        
        with patch.object(n8n_client, 'get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.list_workflows.return_value = mock_workflow_list
            mock_get_client.return_value = mock_client
            
            # Test all workflows
            result = await n8n_client.list_tenant_workflows(
                tenant_id="tenant123",
                user_info=mock_user_info,
                active_only=False
            )
            
            assert len(result) == 2  # Only tenant123 workflows
            assert all("test_tenant123_" in w["name"] for w in result)
            
            # Test active only
            result_active = await n8n_client.list_tenant_workflows(
                tenant_id="tenant123",
                user_info=mock_user_info,
                active_only=True
            )
            
            assert len(result_active) == 1
            assert result_active[0]["active"] is True
    
    @pytest.mark.asyncio
    async def test_activate_workflow(self, n8n_client, mock_user_info):
        """Test workflow activation."""
        mock_workflow = MagicMock()
        mock_workflow.dict.return_value = {"id": "workflow123", "active": True}
        
        with patch.object(n8n_client, 'get_client') as mock_get_client, \
             patch.object(n8n_client, '_log_workflow_action') as mock_log:
            
            mock_client = AsyncMock()
            mock_client.update_workflow.return_value = mock_workflow
            mock_get_client.return_value = mock_client
            
            result = await n8n_client.activate_workflow(
                workflow_id="workflow123",
                tenant_id="tenant123",
                user_info=mock_user_info
            )
            
            assert result["active"] is True
            mock_client.update_workflow.assert_called_once_with(
                workflow_id="workflow123",
                workflow_data={"active": True}
            )
            mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_workflow_executions(self, n8n_client, mock_user_info):
        """Test getting workflow executions."""
        mock_execution1 = MagicMock()
        mock_execution1.dict.return_value = {"id": "exec1", "status": "success"}
        
        mock_execution2 = MagicMock()
        mock_execution2.dict.return_value = {"id": "exec2", "status": "running"}
        
        mock_execution_list = MagicMock()
        mock_execution_list.data = [mock_execution1, mock_execution2]
        
        with patch.object(n8n_client, 'get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.list_executions.return_value = mock_execution_list
            mock_get_client.return_value = mock_client
            
            result = await n8n_client.get_workflow_executions(
                workflow_id="workflow123",
                tenant_id="tenant123",
                user_info=mock_user_info,
                limit=50
            )
            
            assert len(result) == 2
            assert result[0]["id"] == "exec1"
            assert result[1]["id"] == "exec2"
            mock_client.list_executions.assert_called_once_with(
                workflow_id="workflow123",
                limit=50
            )
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, n8n_client):
        """Test health check when N8n is healthy."""
        mock_workflow_list = MagicMock()
        
        with patch.object(n8n_client, 'get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.list_workflows.return_value = mock_workflow_list
            mock_get_client.return_value = mock_client
            
            result = await n8n_client.health_check()
            
            assert result["status"] == "healthy"
            assert result["connection"] == "ok"
            assert result["workflows_accessible"] is True
            assert result["templates_loaded"] == 3
            assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, n8n_client):
        """Test health check when N8n is unhealthy."""
        with patch.object(n8n_client, 'get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.list_workflows.side_effect = Exception("Connection failed")
            mock_get_client.return_value = mock_client
            
            result = await n8n_client.health_check()
            
            assert result["status"] == "unhealthy"
            assert result["connection"] == "failed"
            assert "Connection failed" in result["error"]
            assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_log_workflow_action(self, n8n_client, mock_user_info):
        """Test workflow action logging."""
        with patch('smeflow.integrations.n8n_wrapper.get_db_session') as mock_get_session, \
             patch('smeflow.integrations.n8n_wrapper.logger') as mock_logger:
            
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            await n8n_client._log_workflow_action(
                action="create",
                workflow_id="workflow123",
                tenant_id="tenant123",
                user_info=mock_user_info,
                template_id="product_recommender",
                metadata={"test": "data"}
            )
            
            mock_get_session.assert_called_once_with("tenant123")
            mock_logger.info.assert_called_once()
            
            # Verify log entry structure
            log_call = mock_logger.info.call_args[0][0]
            assert "create" in log_call
            assert "workflow123" in log_call
            assert "tenant123" in log_call
            assert "product_recommender" in log_call


class TestWorkflowTemplates:
    """Test SME workflow templates."""
    
    @pytest.fixture
    def n8n_client(self):
        """Create N8n client for template testing."""
        config = N8nConfig(api_key="test-key")
        with patch('smeflow.integrations.n8n_wrapper.get_settings') as mock_settings:
            mock_settings.return_value.N8N_API_KEY = "test-key"
            return SMEFlowN8nClient(config=config)
    
    def test_product_recommender_template(self, n8n_client):
        """Test product recommender template structure."""
        template = n8n_client._templates["product_recommender"]
        
        assert template.id == "product_recommender"
        assert template.category == "retail"
        assert template.compliance_level == "standard"
        assert len(template.nodes) == 3
        assert "webhook" in [node["id"] for node in template.nodes]
        assert "ai_agent" in [node["id"] for node in template.nodes]
        assert "response" in [node["id"] for node in template.nodes]
    
    def test_local_discovery_template(self, n8n_client):
        """Test local discovery template structure."""
        template = n8n_client._templates["local_discovery"]
        
        assert template.id == "local_discovery"
        assert template.category == "services"
        assert template.compliance_level == "standard"
        assert len(template.nodes) == 4
        assert "location_webhook" in [node["id"] for node in template.nodes]
        assert "geocoding" in [node["id"] for node in template.nodes]
        assert "business_search" in [node["id"] for node in template.nodes]
        assert "booking_integration" in [node["id"] for node in template.nodes]
    
    def test_support_agent_template(self, n8n_client):
        """Test 360 support agent template structure."""
        template = n8n_client._templates["support_agent"]
        
        assert template.id == "support_agent"
        assert template.category == "support"
        assert template.compliance_level == "enterprise"
        assert len(template.nodes) == 5
        assert "support_webhook" in [node["id"] for node in template.nodes]
        assert "intent_analysis" in [node["id"] for node in template.nodes]
        assert "knowledge_search" in [node["id"] for node in template.nodes]
        assert "human_escalation" in [node["id"] for node in template.nodes]
        assert "livekit_call" in [node["id"] for node in template.nodes]


if __name__ == "__main__":
    pytest.main([__file__])
