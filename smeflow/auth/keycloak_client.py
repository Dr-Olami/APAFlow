"""
Keycloak Client for SMEFlow Authentication

Handles Keycloak integration, realm management, and OAuth 2.0/OpenID Connect flows
for multi-tenant African SME authentication.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, Field

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class KeycloakConfig(BaseModel):
    """Keycloak configuration model."""
    
    server_url: str = Field(..., description="Keycloak server URL")
    realm: str = Field(default="smeflow", description="Default realm name")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    admin_username: str = Field(..., description="Admin username")
    admin_password: str = Field(..., description="Admin password")


class TenantRealm(BaseModel):
    """Tenant realm configuration."""
    
    tenant_id: str
    realm_name: str
    display_name: str
    enabled: bool = True
    themes: Dict[str, str] = Field(default_factory=lambda: {
        "login": "smeflow",
        "account": "smeflow"
    })


class KeycloakClient:
    """
    Keycloak client for managing authentication and multi-tenant realms.
    
    Handles:
    - Realm creation and management for tenants
    - OAuth 2.0/OpenID Connect configuration
    - User authentication and token validation
    - African market localization (Swahili, Hausa, English)
    """
    
    def __init__(self, config: Optional[KeycloakConfig] = None):
        """Initialize Keycloak client with configuration."""
        self.settings = get_settings()
        self.config = config or self._load_config()
        self.admin_token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)
        
    def _load_config(self) -> KeycloakConfig:
        """Load Keycloak configuration from settings."""
        return KeycloakConfig(
            server_url=self.settings.keycloak_url,
            client_id=self.settings.keycloak_client_id,
            client_secret=self.settings.keycloak_client_secret,
            admin_username=self.settings.keycloak_admin_username,
            admin_password=self.settings.keycloak_admin_password
        )
    
    async def get_admin_token(self) -> str:
        """Get admin access token for Keycloak management operations."""
        if self.admin_token:
            return self.admin_token
            
        token_url = urljoin(
            self.config.server_url,
            f"/realms/master/protocol/openid-connect/token"
        )
        
        data = {
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": self.config.admin_username,
            "password": self.config.admin_password
        }
        
        try:
            response = await self.client.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            self.admin_token = token_data["access_token"]
            
            logger.info("Successfully obtained Keycloak admin token")
            return self.admin_token
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get admin token: {e}")
            raise Exception(f"Keycloak admin authentication failed: {e}")
    
    async def create_tenant_realm(self, tenant_realm: TenantRealm) -> bool:
        """
        Create a new realm for a tenant.
        
        Args:
            tenant_realm: Tenant realm configuration
            
        Returns:
            bool: True if realm created successfully
        """
        admin_token = await self.get_admin_token()
        realms_url = urljoin(self.config.server_url, "/admin/realms")
        
        realm_config = {
            "realm": tenant_realm.realm_name,
            "displayName": tenant_realm.display_name,
            "enabled": tenant_realm.enabled,
            "registrationAllowed": True,
            "loginWithEmailAllowed": True,
            "duplicateEmailsAllowed": False,
            "resetPasswordAllowed": True,
            "editUsernameAllowed": False,
            "bruteForceProtected": True,
            "loginTheme": tenant_realm.themes.get("login", "smeflow"),
            "accountTheme": tenant_realm.themes.get("account", "smeflow"),
            "internationalizationEnabled": True,
            "supportedLocales": ["en", "sw", "ha"],  # English, Swahili, Hausa
            "defaultLocale": "en",
            "attributes": {
                "tenant_id": tenant_realm.tenant_id,
                "african_market": "true"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.client.post(
                realms_url, 
                json=realm_config, 
                headers=headers
            )
            
            if response.status_code == 201:
                logger.info(f"Created realm {tenant_realm.realm_name} for tenant {tenant_realm.tenant_id}")
                await self._configure_realm_client(tenant_realm.realm_name, admin_token)
                return True
            elif response.status_code == 409:
                logger.warning(f"Realm {tenant_realm.realm_name} already exists")
                return True
            else:
                logger.error(f"Failed to create realm: {response.status_code} - {response.text}")
                return False
                
        except httpx.HTTPError as e:
            logger.error(f"Error creating realm: {e}")
            return False
    
    async def _configure_realm_client(self, realm_name: str, admin_token: str) -> bool:
        """Configure OAuth client for the realm."""
        clients_url = urljoin(
            self.config.server_url,
            f"/admin/realms/{realm_name}/clients"
        )
        
        client_config = {
            "clientId": f"smeflow-{realm_name}",
            "name": f"SMEFlow Client for {realm_name}",
            "description": "SMEFlow application client for African SME automation",
            "enabled": True,
            "clientAuthenticatorType": "client-secret",
            "secret": self.config.client_secret,
            "standardFlowEnabled": True,
            "implicitFlowEnabled": False,
            "directAccessGrantsEnabled": True,
            "serviceAccountsEnabled": True,
            "publicClient": False,
            "protocol": "openid-connect",
            "attributes": {
                "saml.assertion.signature": "false",
                "saml.force.post.binding": "false",
                "saml.multivalued.roles": "false",
                "saml.encrypt": "false",
                "saml.server.signature": "false",
                "saml.server.signature.keyinfo.ext": "false",
                "exclude.session.state.from.auth.response": "false",
                "saml_force_name_id_format": "false",
                "saml.client.signature": "false",
                "tls.client.certificate.bound.access.tokens": "false",
                "saml.authnstatement": "false",
                "display.on.consent.screen": "false",
                "saml.onetimeuse.condition": "false"
            },
            "redirectUris": [
                "http://localhost:3000/*",
                "http://localhost:8000/*",
                f"https://{self.settings.domain}/*"
            ],
            "webOrigins": [
                "http://localhost:3000",
                "http://localhost:8000",
                f"https://{self.settings.domain}"
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.client.post(
                clients_url,
                json=client_config,
                headers=headers
            )
            
            if response.status_code in [201, 409]:  # Created or already exists
                logger.info(f"Configured OAuth client for realm {realm_name}")
                return True
            else:
                logger.error(f"Failed to configure client: {response.status_code} - {response.text}")
                return False
                
        except httpx.HTTPError as e:
            logger.error(f"Error configuring realm client: {e}")
            return False
    
    async def get_realm_openid_config(self, realm_name: str) -> Dict[str, Any]:
        """Get OpenID Connect configuration for a realm."""
        config_url = urljoin(
            self.config.server_url,
            f"/realms/{realm_name}/.well-known/openid_configuration"
        )
        
        try:
            response = await self.client.get(config_url)
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get OpenID config for realm {realm_name}: {e}")
            raise
    
    async def validate_token(self, token: str, realm_name: str) -> Dict[str, Any]:
        """
        Validate JWT token against Keycloak.
        
        Args:
            token: JWT access token
            realm_name: Realm to validate against
            
        Returns:
            Dict containing token validation result
        """
        userinfo_url = urljoin(
            self.config.server_url,
            f"/realms/{realm_name}/protocol/openid-connect/userinfo"
        )
        
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = await self.client.get(userinfo_url, headers=headers)
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Token validation failed: {e}")
            raise Exception(f"Invalid token: {e}")
    
    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
