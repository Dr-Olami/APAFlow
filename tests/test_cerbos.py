"""
Unit tests for Cerbos RBAC integration in SMEFlow.

Tests cover authorization checks, tenant isolation, role-based access control,
and African market scenarios for SME workflows.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from smeflow.auth.cerbos_client import (
    CerbosClient,
    Principal,
    Resource,
    AuthorizationRequest,
    AuthorizationResponse,
    get_cerbos_client,
    check_permission
)
from smeflow.auth.authorization_middleware import (
    require_permission,
    require_tenant_access,
    require_roles,
    require_subscription_tier,
    check_resource_access,
    AuthorizationError
)
from smeflow.auth.jwt_middleware import UserInfo


class TestCerbosClient:
    """Test Cerbos client functionality."""
    
    @pytest.fixture
    def cerbos_client(self):
        """Create Cerbos client for testing."""
        return CerbosClient()
    
    @pytest.fixture
    def sample_principal(self):
        """Sample principal for testing."""
        return Principal(
            id="user_123",
            tenant_id="lagos_retail_001",
            roles=["user", "agent_manager"],
            subscription_tier="premium",
            region="nigeria"
        )
    
    @pytest.fixture
    def sample_resource(self):
        """Sample resource for testing."""
        return Resource(
            id="agent_product_recommender",
            tenant_id="lagos_retail_001",
            owner_id="user_123",
            resource_type="agent",
            visibility="tenant",
            created_at=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_check_permission_allowed(self, cerbos_client, sample_principal, sample_resource):
        """Test successful permission check."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"action": "execute", "effect": "EFFECT_ALLOW"},
                {"action": "view", "effect": "EFFECT_ALLOW"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(cerbos_client.client, 'post', return_value=mock_response):
            result = await cerbos_client.check_permission(
                sample_principal, 
                sample_resource, 
                ["execute", "view"]
            )
        
        assert result.allowed is True
        assert result.actions["execute"] is True
        assert result.actions["view"] is True
        assert len(result.validation_errors) == 0
    
    @pytest.mark.asyncio
    async def test_check_permission_denied(self, cerbos_client, sample_principal, sample_resource):
        """Test denied permission check."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"action": "delete", "effect": "EFFECT_DENY"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(cerbos_client.client, 'post', return_value=mock_response):
            result = await cerbos_client.check_permission(
                sample_principal, 
                sample_resource, 
                ["delete"]
            )
        
        assert result.allowed is False
        assert result.actions["delete"] is False
    
    @pytest.mark.asyncio
    async def test_check_permission_http_error(self, cerbos_client, sample_principal, sample_resource):
        """Test permission check with HTTP error."""
        with patch.object(cerbos_client.client, 'post', side_effect=Exception("Connection error")):
            result = await cerbos_client.check_permission(
                sample_principal, 
                sample_resource, 
                ["execute"]
            )
        
        # Should fail secure - deny access on error
        assert result.allowed is False
        assert result.actions["execute"] is False
        assert len(result.validation_errors) > 0
    
    @pytest.mark.asyncio
    async def test_check_single_permission(self, cerbos_client, sample_principal, sample_resource):
        """Test single permission check."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"action": "view", "effect": "EFFECT_ALLOW"}]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(cerbos_client.client, 'post', return_value=mock_response):
            result = await cerbos_client.check_single_permission(
                sample_principal, 
                sample_resource, 
                "view"
            )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_allowed_actions(self, cerbos_client, sample_principal, sample_resource):
        """Test getting allowed actions."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"action": "view", "effect": "EFFECT_ALLOW"},
                {"action": "execute", "effect": "EFFECT_ALLOW"},
                {"action": "delete", "effect": "EFFECT_DENY"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(cerbos_client.client, 'post', return_value=mock_response):
            allowed_actions = await cerbos_client.get_allowed_actions(
                sample_principal, 
                sample_resource, 
                ["view", "execute", "delete"]
            )
        
        assert "view" in allowed_actions
        assert "execute" in allowed_actions
        assert "delete" not in allowed_actions
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, cerbos_client):
        """Test successful health check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch.object(cerbos_client.client, 'get', return_value=mock_response):
            result = await cerbos_client.health_check()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, cerbos_client):
        """Test failed health check."""
        with patch.object(cerbos_client.client, 'get', side_effect=Exception("Connection error")):
            result = await cerbos_client.health_check()
        
        assert result is False


class TestTenantIsolation:
    """Test tenant isolation scenarios."""
    
    @pytest.mark.asyncio
    async def test_cross_tenant_access_denied(self):
        """Test that cross-tenant access is denied."""
        # User from one tenant trying to access another tenant's resource
        principal = Principal(
            id="user_123",
            tenant_id="lagos_retail_001",
            roles=["user"]
        )
        
        resource = Resource(
            id="agent_001",
            tenant_id="nairobi_logistics_002",  # Different tenant
            resource_type="agent"
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"action": "view", "effect": "EFFECT_DENY"}]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await check_permission(
                user_id=principal.id,
                tenant_id=principal.tenant_id,
                user_roles=principal.roles,
                resource_id=resource.id,
                resource_type=resource.resource_type,
                resource_tenant_id=resource.tenant_id,
                actions=["view"]
            )
        
        assert result.allowed is False
        assert result.actions["view"] is False
    
    @pytest.mark.asyncio
    async def test_same_tenant_access_allowed(self):
        """Test that same-tenant access is allowed."""
        principal = Principal(
            id="user_123",
            tenant_id="lagos_retail_001",
            roles=["user"]
        )
        
        resource = Resource(
            id="agent_001",
            tenant_id="lagos_retail_001",  # Same tenant
            resource_type="agent"
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"action": "view", "effect": "EFFECT_ALLOW"}]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await check_permission(
                user_id=principal.id,
                tenant_id=principal.tenant_id,
                user_roles=principal.roles,
                resource_id=resource.id,
                resource_type=resource.resource_type,
                resource_tenant_id=resource.tenant_id,
                actions=["view"]
            )
        
        assert result.allowed is True
        assert result.actions["view"] is True


class TestRoleBasedAccess:
    """Test role-based access control scenarios."""
    
    @pytest.mark.asyncio
    async def test_admin_full_access(self):
        """Test that tenant admins have full access."""
        principal = Principal(
            id="admin_123",
            tenant_id="lagos_retail_001",
            roles=["admin"]
        )
        
        resource = Resource(
            id="agent_001",
            tenant_id="lagos_retail_001",
            resource_type="agent"
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"action": "view", "effect": "EFFECT_ALLOW"},
                {"action": "edit", "effect": "EFFECT_ALLOW"},
                {"action": "delete", "effect": "EFFECT_ALLOW"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await check_permission(
                user_id=principal.id,
                tenant_id=principal.tenant_id,
                user_roles=principal.roles,
                resource_id=resource.id,
                resource_type=resource.resource_type,
                resource_tenant_id=resource.tenant_id,
                actions=["view", "edit", "delete"]
            )
        
        assert result.allowed is True
        assert all(result.actions.values())
    
    @pytest.mark.asyncio
    async def test_user_limited_access(self):
        """Test that regular users have limited access."""
        principal = Principal(
            id="user_123",
            tenant_id="lagos_retail_001",
            roles=["user"]
        )
        
        resource = Resource(
            id="agent_001",
            tenant_id="lagos_retail_001",
            resource_type="agent"
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"action": "view", "effect": "EFFECT_ALLOW"},
                {"action": "execute", "effect": "EFFECT_ALLOW"},
                {"action": "delete", "effect": "EFFECT_DENY"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await check_permission(
                user_id=principal.id,
                tenant_id=principal.tenant_id,
                user_roles=principal.roles,
                resource_id=resource.id,
                resource_type=resource.resource_type,
                resource_tenant_id=resource.tenant_id,
                actions=["view", "execute", "delete"]
            )
        
        assert result.actions["view"] is True
        assert result.actions["execute"] is True
        assert result.actions["delete"] is False


class TestSubscriptionTiers:
    """Test subscription tier restrictions."""
    
    @pytest.mark.asyncio
    async def test_premium_features_allowed(self):
        """Test that premium features are allowed for premium users."""
        principal = Principal(
            id="user_123",
            tenant_id="lagos_retail_001",
            roles=["user"],
            subscription_tier="premium"
        )
        
        resource = Resource(
            id="agent_001",
            tenant_id="lagos_retail_001",
            resource_type="agent"
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"action": "advanced_analytics", "effect": "EFFECT_ALLOW"}]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await check_permission(
                user_id=principal.id,
                tenant_id=principal.tenant_id,
                user_roles=principal.roles,
                resource_id=resource.id,
                resource_type=resource.resource_type,
                resource_tenant_id=resource.tenant_id,
                actions=["advanced_analytics"],
                subscription_tier=principal.subscription_tier
            )
        
        assert result.actions["advanced_analytics"] is True
    
    @pytest.mark.asyncio
    async def test_premium_features_denied_for_free_tier(self):
        """Test that premium features are denied for free tier users."""
        principal = Principal(
            id="user_123",
            tenant_id="lagos_retail_001",
            roles=["user"],
            subscription_tier="free"
        )
        
        resource = Resource(
            id="agent_001",
            tenant_id="lagos_retail_001",
            resource_type="agent"
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"action": "advanced_analytics", "effect": "EFFECT_DENY"}]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await check_permission(
                user_id=principal.id,
                tenant_id=principal.tenant_id,
                user_roles=principal.roles,
                resource_id=resource.id,
                resource_type=resource.resource_type,
                resource_tenant_id=resource.tenant_id,
                actions=["advanced_analytics"],
                subscription_tier=principal.subscription_tier
            )
        
        assert result.actions["advanced_analytics"] is False


class TestAuthorizationMiddleware:
    """Test authorization middleware decorators."""
    
    def test_require_roles_decorator(self):
        """Test role requirement decorator."""
        @require_roles(["admin", "manager"])
        async def protected_endpoint(user: UserInfo):
            return {"message": "Access granted"}
        
        # Test with authorized user
        user_with_role = UserInfo(
            user_id="user_123",
            tenant_id="tenant_001",
            roles=["admin"],
            email="admin@example.com"
        )
        
        # This would normally be tested with FastAPI test client
        # For unit test, we verify the decorator exists and can be applied
        assert hasattr(protected_endpoint, '__wrapped__')
    
    def test_require_subscription_tier_decorator(self):
        """Test subscription tier requirement decorator."""
        @require_subscription_tier("premium")
        async def premium_endpoint(user: UserInfo):
            return {"message": "Premium feature"}
        
        # Verify decorator is applied
        assert hasattr(premium_endpoint, '__wrapped__')
    
    @pytest.mark.asyncio
    async def test_authorization_error(self):
        """Test authorization error handling."""
        with pytest.raises(AuthorizationError) as exc_info:
            raise AuthorizationError("Access denied for testing")
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in str(exc_info.value.detail)


class TestAfricanMarketScenarios:
    """Test African market-specific authorization scenarios."""
    
    @pytest.mark.asyncio
    async def test_nigerian_sme_agent_access(self):
        """Test Nigerian SME accessing product recommendation agent."""
        principal = Principal(
            id="sme_owner_lagos",
            tenant_id="lagos_retail_boutique",
            roles=["owner", "agent_manager"],
            subscription_tier="basic",
            region="nigeria"
        )
        
        resource = Resource(
            id="product_recommender_agent",
            tenant_id="lagos_retail_boutique",
            owner_id="sme_owner_lagos",
            resource_type="agent",
            visibility="tenant"
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"action": "execute", "effect": "EFFECT_ALLOW"},
                {"action": "configure", "effect": "EFFECT_ALLOW"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await check_permission(
                user_id=principal.id,
                tenant_id=principal.tenant_id,
                user_roles=principal.roles,
                resource_id=resource.id,
                resource_type=resource.resource_type,
                resource_tenant_id=resource.tenant_id,
                actions=["execute", "configure"],
                resource_owner_id=resource.owner_id,
                subscription_tier=principal.subscription_tier,
                region=principal.region
            )
        
        assert result.allowed is True
        assert result.actions["execute"] is True
        assert result.actions["configure"] is True
    
    @pytest.mark.asyncio
    async def test_kenyan_logistics_workflow_access(self):
        """Test Kenyan logistics company accessing shipment tracking workflow."""
        principal = Principal(
            id="logistics_manager_nairobi",
            tenant_id="nairobi_logistics_express",
            roles=["manager", "workflow_manager"],
            subscription_tier="premium",
            region="kenya"
        )
        
        resource = Resource(
            id="shipment_tracker_workflow",
            tenant_id="nairobi_logistics_express",
            resource_type="workflow",
            visibility="tenant"
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"action": "execute", "effect": "EFFECT_ALLOW"},
                {"action": "monitor", "effect": "EFFECT_ALLOW"},
                {"action": "pause", "effect": "EFFECT_ALLOW"}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await check_permission(
                user_id=principal.id,
                tenant_id=principal.tenant_id,
                user_roles=principal.roles,
                resource_id=resource.id,
                resource_type=resource.resource_type,
                resource_tenant_id=resource.tenant_id,
                actions=["execute", "monitor", "pause"],
                subscription_tier=principal.subscription_tier,
                region=principal.region
            )
        
        assert result.allowed is True
        assert all(result.actions.values())


if __name__ == "__main__":
    pytest.main([__file__])
