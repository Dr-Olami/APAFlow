"""
Cerbos authorization client for SMEFlow multi-tenant RBAC.

This module provides integration with Cerbos policy engine for role-based
access control with tenant isolation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

import httpx
from pydantic import BaseModel, Field

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class Principal(BaseModel):
    """Principal (user) for authorization checks."""
    
    id: str = Field(..., description="User ID from Keycloak")
    tenant_id: str = Field(..., description="Tenant identifier")
    roles: List[str] = Field(default_factory=list, description="User roles")
    subscription_tier: str = Field(default="free", description="Tenant subscription level")
    region: Optional[str] = Field(None, description="African region")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "user_123",
                "tenant_id": "lagos_retail_001",
                "roles": ["user", "agent_manager"],
                "subscription_tier": "premium",
                "region": "nigeria"
            }
        }


class Resource(BaseModel):
    """Resource for authorization checks."""
    
    id: str = Field(..., description="Resource identifier")
    tenant_id: str = Field(..., description="Tenant that owns resource")
    owner_id: Optional[str] = Field(None, description="Resource owner")
    resource_type: str = Field(..., description="Type of resource")
    visibility: str = Field(default="tenant", description="Resource visibility")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "agent_product_recommender",
                "tenant_id": "lagos_retail_001",
                "owner_id": "user_123",
                "resource_type": "agent",
                "visibility": "tenant"
            }
        }


class AuthorizationRequest(BaseModel):
    """Authorization check request."""
    
    principal: Principal
    resource: Resource
    actions: List[str]
    
    class Config:
        schema_extra = {
            "example": {
                "principal": {
                    "id": "user_123",
                    "tenant_id": "lagos_retail_001",
                    "roles": ["user"]
                },
                "resource": {
                    "id": "agent_001",
                    "tenant_id": "lagos_retail_001",
                    "resource_type": "agent"
                },
                "actions": ["execute", "view"]
            }
        }


class AuthorizationResponse(BaseModel):
    """Authorization check response."""
    
    allowed: bool
    actions: Dict[str, bool]
    validation_errors: List[str] = Field(default_factory=list)
    
    class Config:
        schema_extra = {
            "example": {
                "allowed": True,
                "actions": {
                    "execute": True,
                    "view": True,
                    "delete": False
                }
            }
        }


class CerbosClient:
    """
    Cerbos authorization client for SMEFlow.
    
    Handles authorization checks with tenant isolation and African market
    optimizations for SME workflows.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = f"http://{self.settings.cerbos_host}:{self.settings.cerbos_port}"
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
    
    async def check_permission(
        self,
        principal: Principal,
        resource: Resource,
        actions: List[str]
    ) -> AuthorizationResponse:
        """
        Check if principal has permission to perform actions on resource.
        
        Args:
            principal: User requesting access
            resource: Resource being accessed
            actions: List of actions to check
            
        Returns:
            Authorization response with allowed actions
            
        Raises:
            httpx.HTTPError: If Cerbos API call fails
        """
        try:
            # Prepare Cerbos check request
            request_data = {
                "requestId": f"req_{principal.id}_{resource.id}_{datetime.utcnow().isoformat()}",
                "principal": {
                    "id": principal.id,
                    "roles": principal.roles,
                    "attr": {
                        "tenant_id": principal.tenant_id,
                        "subscription_tier": principal.subscription_tier,
                        "region": principal.region or "africa"
                    }
                },
                "resource": {
                    "kind": resource.resource_type,
                    "id": resource.id,
                    "attr": {
                        "tenant_id": resource.tenant_id,
                        "owner_id": resource.owner_id,
                        "resource_type": resource.resource_type,
                        "visibility": resource.visibility,
                        "created_at": resource.created_at.isoformat() if resource.created_at else None,
                        "updated_at": resource.updated_at.isoformat() if resource.updated_at else None
                    }
                },
                "actions": actions
            }
            
            # Make authorization request to Cerbos
            response = await self.client.post(
                f"{self.base_url}/api/check",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Parse response
            actions_result = {}
            overall_allowed = True
            
            for action_result in result.get("results", []):
                action = action_result.get("action")
                allowed = action_result.get("effect") == "EFFECT_ALLOW"
                actions_result[action] = allowed
                if not allowed:
                    overall_allowed = False
            
            return AuthorizationResponse(
                allowed=overall_allowed,
                actions=actions_result
            )
            
        except httpx.HTTPError as e:
            logger.error(f"Cerbos authorization check failed: {e}")
            # Fail secure - deny access on error
            return AuthorizationResponse(
                allowed=False,
                actions={action: False for action in actions},
                validation_errors=[f"Authorization service error: {str(e)}"]
            )
        except Exception as e:
            logger.error(f"Unexpected error in authorization check: {e}")
            return AuthorizationResponse(
                allowed=False,
                actions={action: False for action in actions},
                validation_errors=[f"Internal authorization error: {str(e)}"]
            )
    
    async def check_single_permission(
        self,
        principal: Principal,
        resource: Resource,
        action: str
    ) -> bool:
        """
        Check if principal has permission for a single action.
        
        Args:
            principal: User requesting access
            resource: Resource being accessed
            action: Single action to check
            
        Returns:
            True if action is allowed, False otherwise
        """
        result = await self.check_permission(principal, resource, [action])
        return result.actions.get(action, False)
    
    async def get_allowed_actions(
        self,
        principal: Principal,
        resource: Resource,
        actions: List[str]
    ) -> List[str]:
        """
        Get list of allowed actions for principal on resource.
        
        Args:
            principal: User requesting access
            resource: Resource being accessed
            actions: Actions to check
            
        Returns:
            List of allowed actions
        """
        result = await self.check_permission(principal, resource, actions)
        return [action for action, allowed in result.actions.items() if allowed]
    
    async def health_check(self) -> bool:
        """
        Check if Cerbos service is healthy.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self.client.get(f"{self.base_url}/healthz")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Cerbos health check failed: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Global Cerbos client instance
_cerbos_client: Optional[CerbosClient] = None


async def get_cerbos_client() -> CerbosClient:
    """
    Get or create global Cerbos client instance.
    
    Returns:
        CerbosClient instance
    """
    global _cerbos_client
    if _cerbos_client is None:
        _cerbos_client = CerbosClient()
    return _cerbos_client


async def check_permission(
    user_id: str,
    tenant_id: str,
    user_roles: List[str],
    resource_id: str,
    resource_type: str,
    resource_tenant_id: str,
    actions: List[str],
    resource_owner_id: Optional[str] = None,
    subscription_tier: str = "free",
    region: Optional[str] = None
) -> AuthorizationResponse:
    """
    Convenience function for authorization checks.
    
    Args:
        user_id: User identifier
        tenant_id: User's tenant
        user_roles: User's roles
        resource_id: Resource identifier
        resource_type: Type of resource
        resource_tenant_id: Resource's tenant
        actions: Actions to check
        resource_owner_id: Resource owner (optional)
        subscription_tier: Tenant subscription level
        region: African region
        
    Returns:
        Authorization response
    """
    client = await get_cerbos_client()
    
    principal = Principal(
        id=user_id,
        tenant_id=tenant_id,
        roles=user_roles,
        subscription_tier=subscription_tier,
        region=region
    )
    
    resource = Resource(
        id=resource_id,
        tenant_id=resource_tenant_id,
        owner_id=resource_owner_id,
        resource_type=resource_type
    )
    
    return await client.check_permission(principal, resource, actions)
