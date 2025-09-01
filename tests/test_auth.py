"""
Unit tests for SMEFlow Authentication Module

Tests Keycloak integration, JWT middleware, and tenant authentication
for the African SME automation platform.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from smeflow.auth.keycloak_client import KeycloakClient, KeycloakConfig, TenantRealm
from smeflow.auth.jwt_middleware import JWTMiddleware, TenantAuthDependency
from smeflow.auth.tenant_auth import TenantAuthManager, TenantRegistration


class TestKeycloakClient:
    """Test Keycloak client functionality."""
    
    @pytest.fixture
    def keycloak_config(self):
        """Keycloak configuration for testing."""
        return KeycloakConfig(
            server_url="http://localhost:8080",
            client_id="test-client",
            client_secret="test-secret",
            admin_username="admin",
            admin_password="admin"
        )
    
    @pytest.fixture
    def keycloak_client(self, keycloak_config):
        """Keycloak client instance for testing."""
        return KeycloakClient(keycloak_config)
    
    @pytest.mark.asyncio
    async def test_get_admin_token_success(self, keycloak_client):
        """Test successful admin token retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test-token"}
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(keycloak_client.client, 'post', return_value=mock_response):
            token = await keycloak_client.get_admin_token()
            assert token == "test-token"
            assert keycloak_client.admin_token == "test-token"
    
    @pytest.mark.asyncio
    async def test_create_tenant_realm_success(self, keycloak_client):
        """Test successful tenant realm creation."""
        tenant_realm = TenantRealm(
            tenant_id="test-tenant",
            realm_name="test-realm",
            display_name="Test Realm"
        )
        
        # Mock admin token
        keycloak_client.admin_token = "admin-token"
        
        # Mock successful realm creation
        mock_response = MagicMock()
        mock_response.status_code = 201
        
        with patch.object(keycloak_client.client, 'post', return_value=mock_response):
            with patch.object(keycloak_client, '_configure_realm_client', return_value=True):
                result = await keycloak_client.create_tenant_realm(tenant_realm)
                assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_token_success(self, keycloak_client):
        """Test successful token validation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sub": "user-123",
            "preferred_username": "testuser",
            "email": "test@example.com"
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(keycloak_client.client, 'get', return_value=mock_response):
            result = await keycloak_client.validate_token("test-token", "test-realm")
            assert result["sub"] == "user-123"
            assert result["preferred_username"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_get_realm_openid_config(self, keycloak_client):
        """Test OpenID configuration retrieval."""
        mock_config = {
            "authorization_endpoint": "http://localhost:8080/realms/test/auth",
            "token_endpoint": "http://localhost:8080/realms/test/token"
        }
        
        mock_response = MagicMock()
        mock_response.json.return_value = mock_config
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(keycloak_client.client, 'get', return_value=mock_response):
            config = await keycloak_client.get_realm_openid_config("test-realm")
            assert config["authorization_endpoint"] == mock_config["authorization_endpoint"]


class TestJWTMiddleware:
    """Test JWT middleware functionality."""
    
    @pytest.fixture
    def mock_keycloak_client(self):
        """Mock Keycloak client for testing."""
        client = AsyncMock()
        client.validate_token.return_value = {
            "sub": "user-123",
            "preferred_username": "testuser",
            "email": "test@example.com",
            "tenant_id": "tenant-123"
        }
        return client
    
    @pytest.fixture
    def jwt_middleware(self, mock_keycloak_client):
        """JWT middleware instance for testing."""
        app = MagicMock()
        return JWTMiddleware(app, mock_keycloak_client)
    
    @pytest.mark.asyncio
    async def test_extract_token_success(self, jwt_middleware):
        """Test successful token extraction from headers."""
        request = MagicMock()
        request.headers.get.return_value = "Bearer test-token"
        
        token = await jwt_middleware._extract_token(request)
        assert token == "test-token"
    
    @pytest.mark.asyncio
    async def test_extract_token_no_header(self, jwt_middleware):
        """Test token extraction with no authorization header."""
        request = MagicMock()
        request.headers.get.return_value = None
        
        token = await jwt_middleware._extract_token(request)
        assert token is None
    
    @pytest.mark.asyncio
    async def test_public_path_bypass(self, jwt_middleware):
        """Test that public paths bypass authentication."""
        request = MagicMock()
        request.url.path = "/health"
        
        call_next = AsyncMock()
        call_next.return_value = "response"
        
        result = await jwt_middleware.dispatch(request, call_next)
        assert result == "response"
        call_next.assert_called_once_with(request)


class TestTenantAuthManager:
    """Test tenant authentication manager."""
    
    @pytest.fixture
    def mock_keycloak_client(self):
        """Mock Keycloak client for testing."""
        client = AsyncMock()
        client.create_tenant_realm.return_value = True
        client.get_realm_openid_config.return_value = {
            "authorization_endpoint": "http://localhost:8080/realms/test/auth",
            "token_endpoint": "http://localhost:8080/realms/test/token"
        }
        return client
    
    @pytest.fixture
    def tenant_auth_manager(self, mock_keycloak_client):
        """Tenant auth manager instance for testing."""
        return TenantAuthManager(mock_keycloak_client)
    
    @pytest.fixture
    def tenant_registration(self):
        """Sample tenant registration data."""
        return TenantRegistration(
            name="Test SME Business",
            region="NG",
            business_type="retail",
            admin_email="admin@testsme.com",
            admin_username="admin",
            admin_password="secure123",
            local_language="en",
            currency="NGN",
            timezone="Africa/Lagos"
        )
    
    @pytest.mark.asyncio
    async def test_register_tenant_success(self, tenant_auth_manager, tenant_registration):
        """Test successful tenant registration."""
        # Mock database operations
        with patch.object(tenant_auth_manager, '_create_tenant_db_entry') as mock_db:
            with patch.object(tenant_auth_manager, '_create_admin_user') as mock_admin:
                mock_db.return_value = MagicMock()
                mock_admin.return_value = {
                    "username": "admin",
                    "email": "admin@testsme.com",
                    "roles": ["tenant-admin"],
                    "created": True
                }
                
                result = await tenant_auth_manager.register_tenant(tenant_registration)
                
                assert "tenant_id" in result
                assert result["tenant_name"] == "Test SME Business"
                assert result["region"] == "NG"
                assert result["localization"]["currency"] == "NGN"
    
    @pytest.mark.asyncio
    async def test_validate_tenant_access_success(self, tenant_auth_manager):
        """Test successful tenant access validation."""
        user_info = {
            "tenant_id": "tenant-123",
            "roles": ["tenant-user"]
        }
        
        result = await tenant_auth_manager.validate_tenant_access(
            user_info, "tenant-123"
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_tenant_access_admin_override(self, tenant_auth_manager):
        """Test admin can access any tenant."""
        user_info = {
            "tenant_id": "tenant-456",
            "roles": ["smeflow-admin"]
        }
        
        result = await tenant_auth_manager.validate_tenant_access(
            user_info, "tenant-123"
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_tenant_access_denied(self, tenant_auth_manager):
        """Test tenant access denied for wrong tenant."""
        user_info = {
            "tenant_id": "tenant-456",
            "roles": ["tenant-user"]
        }
        
        result = await tenant_auth_manager.validate_tenant_access(
            user_info, "tenant-123"
        )
        assert result is False


class TestTenantAuthDependency:
    """Test FastAPI authentication dependency."""
    
    @pytest.fixture
    def auth_dependency(self):
        """Authentication dependency for testing."""
        return TenantAuthDependency(required_roles=["tenant-user"])
    
    @pytest.mark.asyncio
    async def test_auth_dependency_success(self, auth_dependency):
        """Test successful authentication dependency."""
        request = MagicMock()
        request.state.user = {
            "user_id": "user-123",
            "tenant_id": "tenant-123",
            "roles": ["tenant-user"]
        }
        
        credentials = MagicMock()
        credentials.credentials = "test-token"
        
        result = await auth_dependency(request, credentials)
        assert result["user_id"] == "user-123"
        assert result["tenant_id"] == "tenant-123"


# Integration test for African market scenarios
class TestAfricanMarketIntegration:
    """Test African market specific authentication scenarios."""
    
    @pytest.mark.asyncio
    async def test_nigerian_sme_registration(self):
        """Test Nigerian SME registration flow."""
        registration = TenantRegistration(
            name="Lagos Fashion Store",
            region="NG",
            business_type="retail",
            admin_email="owner@lagosfashion.ng",
            admin_username="owner",
            admin_password="secure123",
            local_language="en",
            currency="NGN",
            timezone="Africa/Lagos"
        )
        
        # Mock Keycloak client
        mock_client = AsyncMock()
        mock_client.create_tenant_realm.return_value = True
        mock_client.get_realm_openid_config.return_value = {
            "authorization_endpoint": "http://localhost:8080/realms/tenant-123/auth"
        }
        
        manager = TenantAuthManager(mock_client)
        
        with patch.object(manager, '_create_tenant_db_entry') as mock_db:
            with patch.object(manager, '_create_admin_user') as mock_admin:
                mock_db.return_value = MagicMock()
                mock_admin.return_value = {"username": "owner", "created": True}
                
                result = await manager.register_tenant(registration)
                
                assert result["region"] == "NG"
                assert result["localization"]["currency"] == "NGN"
                assert result["localization"]["timezone"] == "Africa/Lagos"
    
    @pytest.mark.asyncio
    async def test_kenyan_sme_swahili_support(self):
        """Test Kenyan SME with Swahili language support."""
        registration = TenantRegistration(
            name="Nairobi Tech Hub",
            region="KE",
            business_type="technology",
            admin_email="admin@nairobihub.ke",
            admin_username="admin",
            admin_password="secure123",
            local_language="sw",  # Swahili
            currency="KES",
            timezone="Africa/Nairobi"
        )
        
        mock_client = AsyncMock()
        mock_client.create_tenant_realm.return_value = True
        mock_client.get_realm_openid_config.return_value = {}
        
        manager = TenantAuthManager(mock_client)
        
        with patch.object(manager, '_create_tenant_db_entry') as mock_db:
            with patch.object(manager, '_create_admin_user') as mock_admin:
                mock_db.return_value = MagicMock()
                mock_admin.return_value = {"username": "admin", "created": True}
                
                result = await manager.register_tenant(registration)
                
                assert result["localization"]["language"] == "sw"
                assert result["localization"]["currency"] == "KES"


if __name__ == "__main__":
    pytest.main([__file__])
