"""
Test for n8N wrapper health check fix.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from smeflow.integrations.n8n_wrapper import SMEFlowN8nClient, N8nConfig


@pytest.fixture
def n8n_config():
    """Create test n8N configuration."""
    return N8nConfig(
        base_url="http://localhost:5678",
        api_key="test-api-key",
        timeout=30,
        max_retries=3,
        tenant_prefix="test"
    )


@pytest.fixture
def n8n_client(n8n_config):
    """Create test n8N client."""
    return SMEFlowN8nClient(config=n8n_config)


@pytest.mark.asyncio
async def test_health_check_with_tenant_id(n8n_client):
    """Test health check with explicit tenant ID."""
    # Mock the get_client method
    mock_client = AsyncMock()
    mock_workflows = MagicMock()
    mock_workflows.data = []
    mock_client.list_workflows.return_value = mock_workflows
    
    n8n_client.get_client = AsyncMock(return_value=mock_client)
    
    # Test with explicit tenant ID
    result = await n8n_client.health_check(tenant_id="test-tenant")
    
    # Verify the call was made with correct tenant ID
    n8n_client.get_client.assert_called_once_with("test-tenant")
    mock_client.list_workflows.assert_called_once_with(limit=1)
    
    # Verify response structure
    assert result["status"] == "healthy"
    assert result["n8n_url"] == "http://localhost:5678"
    assert result["connection"] == "ok"
    assert result["workflows_accessible"] is True
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_health_check_without_tenant_id(n8n_client):
    """Test health check without tenant ID (uses default)."""
    # Mock the get_client method
    mock_client = AsyncMock()
    mock_workflows = MagicMock()
    mock_workflows.data = []
    mock_client.list_workflows.return_value = mock_workflows
    
    n8n_client.get_client = AsyncMock(return_value=mock_client)
    
    # Test without tenant ID (should use default)
    result = await n8n_client.health_check()
    
    # Verify the call was made with default tenant ID
    n8n_client.get_client.assert_called_once_with("health-check")
    mock_client.list_workflows.assert_called_once_with(limit=1)
    
    # Verify response structure
    assert result["status"] == "healthy"
    assert result["connection"] == "ok"


@pytest.mark.asyncio
async def test_health_check_connection_failure(n8n_client):
    """Test health check when connection fails."""
    # Mock the get_client method to raise an exception
    n8n_client.get_client = AsyncMock(side_effect=Exception("Connection failed"))
    
    # Test health check failure
    result = await n8n_client.health_check()
    
    # Verify error response
    assert result["status"] == "unhealthy"
    assert result["connection"] == "failed"
    assert "Connection failed" in result["error"]
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_health_check_workflow_list_failure(n8n_client):
    """Test health check when workflow listing fails."""
    # Mock the get_client method
    mock_client = AsyncMock()
    mock_client.list_workflows.side_effect = Exception("Workflow listing failed")
    
    n8n_client.get_client = AsyncMock(return_value=mock_client)
    
    # Test health check failure
    result = await n8n_client.health_check(tenant_id="test-tenant")
    
    # Verify error response
    assert result["status"] == "unhealthy"
    assert result["connection"] == "failed"
    assert "Workflow listing failed" in result["error"]
