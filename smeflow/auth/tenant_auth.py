"""
Tenant Authentication Manager for SMEFlow

Manages tenant-specific authentication, realm creation, and multi-tenant isolation
for African SME automation platform.
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Tenant
from ..database.connection import get_db_session
from .keycloak_client import KeycloakClient, TenantRealm

logger = logging.getLogger(__name__)


class TenantRegistration(BaseModel):
    """Tenant registration request model."""
    
    name: str = Field(..., min_length=2, max_length=100, description="Tenant business name")
    region: str = Field(..., description="African region (NG, KE, ZA, etc.)")
    business_type: str = Field(..., description="Type of business (retail, logistics, etc.)")
    admin_email: str = Field(..., description="Admin user email")
    admin_username: str = Field(..., min_length=3, max_length=50, description="Admin username")
    admin_password: str = Field(..., min_length=8, description="Admin password")
    subscription_tier: str = Field(default="free", description="Subscription tier")
    
    # African market specific fields
    local_language: str = Field(default="en", description="Primary local language (en, sw, ha)")
    currency: str = Field(default="USD", description="Local currency (NGN, KES, ZAR, etc.)")
    timezone: str = Field(default="UTC", description="Local timezone")


class TenantAuthManager:
    """
    Manages tenant authentication and realm setup for SMEFlow.
    
    Handles:
    - Tenant registration and realm creation
    - Multi-tenant authentication flows
    - African market localization
    - Subscription tier management
    """
    
    def __init__(self, keycloak_client: Optional[KeycloakClient] = None):
        """Initialize tenant auth manager."""
        self.keycloak_client = keycloak_client or KeycloakClient()
    
    async def register_tenant(
        self, 
        registration: TenantRegistration,
        db_session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Register a new tenant with Keycloak realm and database entry.
        
        Args:
            registration: Tenant registration data
            db_session: Optional database session
            
        Returns:
            Dict containing tenant information and authentication details
        """
        # Generate tenant ID and realm name
        tenant_id = str(uuid4())
        realm_name = f"tenant-{tenant_id[:8]}"
        
        logger.info(f"Registering tenant: {registration.name} with realm: {realm_name}")
        
        try:
            # Create database entry first
            if not db_session:
                async with get_db_session() as db_session:
                    tenant = await self._create_tenant_db_entry(
                        tenant_id, registration, realm_name, db_session
                    )
            else:
                tenant = await self._create_tenant_db_entry(
                    tenant_id, registration, realm_name, db_session
                )
            
            # Create Keycloak realm
            tenant_realm = TenantRealm(
                tenant_id=tenant_id,
                realm_name=realm_name,
                display_name=f"{registration.name} - SMEFlow",
                enabled=True
            )
            
            realm_created = await self.keycloak_client.create_tenant_realm(tenant_realm)
            if not realm_created:
                raise Exception("Failed to create Keycloak realm")
            
            # Create admin user in the realm
            admin_user = await self._create_admin_user(
                realm_name, 
                registration.admin_username,
                registration.admin_email,
                registration.admin_password
            )
            
            # Get OpenID Connect configuration
            oidc_config = await self.keycloak_client.get_realm_openid_config(realm_name)
            
            logger.info(f"Successfully registered tenant {tenant_id}")
            
            return {
                "tenant_id": tenant_id,
                "realm_name": realm_name,
                "tenant_name": registration.name,
                "region": registration.region,
                "subscription_tier": registration.subscription_tier,
                "admin_user": admin_user,
                "auth_endpoints": {
                    "authorization_endpoint": oidc_config.get("authorization_endpoint"),
                    "token_endpoint": oidc_config.get("token_endpoint"),
                    "userinfo_endpoint": oidc_config.get("userinfo_endpoint"),
                    "end_session_endpoint": oidc_config.get("end_session_endpoint")
                },
                "localization": {
                    "language": registration.local_language,
                    "currency": registration.currency,
                    "timezone": registration.timezone
                }
            }
            
        except Exception as e:
            logger.error(f"Tenant registration failed: {e}")
            # Cleanup on failure
            await self._cleanup_failed_registration(tenant_id, realm_name)
            raise Exception(f"Tenant registration failed: {e}")
    
    async def _create_tenant_db_entry(
        self, 
        tenant_id: str, 
        registration: TenantRegistration,
        realm_name: str,
        db_session: AsyncSession
    ) -> Tenant:
        """Create tenant entry in database."""
        tenant = Tenant(
            tenant_id=UUID(tenant_id),
            name=registration.name,
            region=registration.region,
            subscription_tier=registration.subscription_tier,
            realm_name=realm_name,
            business_type=registration.business_type,
            local_language=registration.local_language,
            currency=registration.currency,
            timezone=registration.timezone,
            enabled=True
        )
        
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)
        
        return tenant
    
    async def _create_admin_user(
        self,
        realm_name: str,
        username: str,
        email: str,
        password: str
    ) -> Dict[str, Any]:
        """Create admin user in Keycloak realm."""
        # This would typically use Keycloak Admin API to create user
        # For now, return placeholder data
        logger.info(f"Creating admin user {username} in realm {realm_name}")
        
        return {
            "username": username,
            "email": email,
            "roles": ["tenant-admin"],
            "created": True
        }
    
    async def _cleanup_failed_registration(self, tenant_id: str, realm_name: str):
        """Clean up resources after failed registration."""
        logger.warning(f"Cleaning up failed registration for tenant {tenant_id}")
        
        # TODO: Implement cleanup logic
        # - Delete Keycloak realm
        # - Delete database entry
        # - Clean up any created resources
        pass
    
    async def authenticate_tenant_user(
        self,
        username: str,
        password: str,
        tenant_id: Optional[str] = None,
        realm_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authenticate user against tenant realm.
        
        Args:
            username: User's username or email
            password: User's password
            tenant_id: Optional tenant ID
            realm_name: Optional realm name
            
        Returns:
            Dict containing authentication result and tokens
        """
        if not realm_name and tenant_id:
            # Resolve realm name from tenant ID
            async with get_db_session() as db_session:
                tenant = await self._get_tenant_by_id(tenant_id, db_session)
                if not tenant:
                    raise Exception("Tenant not found")
                realm_name = tenant.realm_name
        
        if not realm_name:
            raise Exception("Realm name or tenant ID required")
        
        # TODO: Implement OAuth 2.0 password grant flow
        # This would typically exchange username/password for tokens
        logger.info(f"Authenticating user {username} in realm {realm_name}")
        
        return {
            "access_token": "placeholder_token",
            "refresh_token": "placeholder_refresh",
            "token_type": "Bearer",
            "expires_in": 3600,
            "realm": realm_name,
            "tenant_id": tenant_id
        }
    
    async def _get_tenant_by_id(self, tenant_id: str, db_session: AsyncSession) -> Optional[Tenant]:
        """Get tenant by ID from database."""
        # TODO: Implement database query
        return None
    
    async def get_tenant_auth_config(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get authentication configuration for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Dict containing auth configuration
        """
        async with get_db_session() as db_session:
            tenant = await self._get_tenant_by_id(tenant_id, db_session)
            if not tenant:
                raise Exception("Tenant not found")
        
        # Get OpenID Connect configuration
        oidc_config = await self.keycloak_client.get_realm_openid_config(tenant.realm_name)
        
        return {
            "tenant_id": tenant_id,
            "realm_name": tenant.realm_name,
            "client_id": f"smeflow-{tenant.realm_name}",
            "auth_endpoints": oidc_config,
            "localization": {
                "language": tenant.local_language,
                "currency": tenant.currency,
                "timezone": tenant.timezone
            }
        }
    
    async def validate_tenant_access(
        self,
        user_info: Dict[str, Any],
        required_tenant_id: str
    ) -> bool:
        """
        Validate that user has access to specified tenant.
        
        Args:
            user_info: User information from JWT token
            required_tenant_id: Required tenant ID for access
            
        Returns:
            bool: True if user has access to tenant
        """
        user_tenant_id = user_info.get("tenant_id")
        user_roles = user_info.get("roles", [])
        
        # Super admin can access any tenant
        if "smeflow-admin" in user_roles:
            return True
        
        # User must belong to the same tenant
        return user_tenant_id == required_tenant_id
    
    async def close(self):
        """Close connections."""
        await self.keycloak_client.close()
