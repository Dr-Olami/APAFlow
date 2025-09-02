"""
SMEFlow Authentication Module

This module provides authentication and authorization services for the SMEFlow platform,
including Keycloak integration, JWT middleware, Cerbos RBAC, and tenant authentication management.
"""

from .keycloak_client import KeycloakClient
from .jwt_middleware import JWTMiddleware, get_current_user, UserInfo
from .tenant_auth import TenantAuthManager, TenantRegistration, TenantRealm
from .cerbos_client import CerbosClient, Principal, Resource, get_cerbos_client, check_permission
from .authorization_middleware import (
    require_permission, 
    require_tenant_access, 
    require_roles, 
    require_subscription_tier,
    check_resource_access,
    AuthorizationError
)

__all__ = [
    "KeycloakClient",
    "JWTMiddleware", 
    "get_current_user",
    "UserInfo",
    "TenantAuthManager",
    "TenantRegistration", 
    "TenantRealm",
    "CerbosClient",
    "Principal",
    "Resource", 
    "get_cerbos_client",
    "check_permission",
    "require_permission",
    "require_tenant_access",
    "require_roles",
    "require_subscription_tier", 
    "check_resource_access",
    "AuthorizationError"
]
