"""
Authorization middleware for SMEFlow FastAPI application.

This module provides RBAC authorization middleware using Cerbos policy engine
with multi-tenant isolation and African market optimizations.
"""

import logging
from typing import Dict, List, Optional, Callable, Any
from functools import wraps

from fastapi import HTTPException, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .cerbos_client import (
    get_cerbos_client, 
    Principal, 
    Resource, 
    AuthorizationResponse,
    check_permission
)
from .jwt_middleware import get_current_user, UserInfo

logger = logging.getLogger(__name__)

security = HTTPBearer()


class AuthorizationError(HTTPException):
    """Custom authorization error."""
    
    def __init__(self, detail: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ResourcePermission:
    """
    Decorator for endpoint authorization checks.
    
    Usage:
        @app.get("/agents/{agent_id}")
        @require_permission("agent", ["view", "read"])
        async def get_agent(agent_id: str, user: UserInfo = Depends(get_current_user)):
            ...
    """
    
    def __init__(
        self,
        resource_type: str,
        actions: List[str],
        resource_id_param: str = "resource_id",
        owner_check: bool = False
    ):
        self.resource_type = resource_type
        self.actions = actions
        self.resource_id_param = resource_id_param
        self.owner_check = owner_check
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user info from dependencies
            user_info = None
            request = None
            
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif hasattr(arg, 'user_id'):  # UserInfo object
                    user_info = arg
            
            # Try to get user from kwargs
            if user_info is None:
                for key, value in kwargs.items():
                    if hasattr(value, 'user_id'):
                        user_info = value
                        break
            
            if user_info is None:
                raise AuthorizationError("User authentication required")
            
            # Extract resource ID from path parameters
            resource_id = kwargs.get(self.resource_id_param)
            if resource_id is None:
                # Try common parameter names
                for param in ["id", "agent_id", "workflow_id", "template_id"]:
                    if param in kwargs:
                        resource_id = kwargs[param]
                        break
            
            if resource_id is None:
                raise AuthorizationError("Resource identifier not found")
            
            # Perform authorization check
            auth_response = await check_permission(
                user_id=user_info.user_id,
                tenant_id=user_info.tenant_id,
                user_roles=user_info.roles,
                resource_id=resource_id,
                resource_type=self.resource_type,
                resource_tenant_id=user_info.tenant_id,  # Assume same tenant for now
                actions=self.actions,
                subscription_tier=getattr(user_info, 'subscription_tier', 'free'),
                region=getattr(user_info, 'region', None)
            )
            
            if not auth_response.allowed:
                denied_actions = [
                    action for action, allowed in auth_response.actions.items() 
                    if not allowed
                ]
                raise AuthorizationError(
                    f"Access denied for actions: {', '.join(denied_actions)} on {self.resource_type} {resource_id}"
                )
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper


def require_permission(
    resource_type: str, 
    actions: List[str], 
    resource_id_param: str = "resource_id"
) -> Callable:
    """
    Decorator factory for resource permission checks.
    
    Args:
        resource_type: Type of resource (agent, workflow, etc.)
        actions: Required actions
        resource_id_param: Parameter name containing resource ID
        
    Returns:
        Decorator function
    """
    return ResourcePermission(resource_type, actions, resource_id_param)


def require_tenant_access(func: Callable) -> Callable:
    """
    Decorator to ensure user can only access their tenant's resources.
    
    Args:
        func: FastAPI endpoint function
        
    Returns:
        Decorated function with tenant isolation
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract user info
        user_info = None
        for arg in args:
            if hasattr(arg, 'user_id'):
                user_info = arg
                break
        
        if user_info is None:
            for key, value in kwargs.items():
                if hasattr(value, 'user_id'):
                    user_info = value
                    break
        
        if user_info is None:
            raise AuthorizationError("User authentication required")
        
        # Check if tenant_id is provided in request
        tenant_id = kwargs.get('tenant_id')
        if tenant_id and tenant_id != user_info.tenant_id:
            raise AuthorizationError("Access denied: Cross-tenant access not allowed")
        
        return await func(*args, **kwargs)
    
    return wrapper


def require_roles(required_roles: List[str]) -> Callable:
    """
    Decorator to require specific roles.
    
    Args:
        required_roles: List of required roles
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user info
            user_info = None
            for arg in args:
                if hasattr(arg, 'user_id'):
                    user_info = arg
                    break
            
            if user_info is None:
                for key, value in kwargs.items():
                    if hasattr(value, 'user_id'):
                        user_info = value
                        break
            
            if user_info is None:
                raise AuthorizationError("User authentication required")
            
            # Check if user has any of the required roles
            user_roles = set(user_info.roles)
            required_roles_set = set(required_roles)
            
            if not user_roles.intersection(required_roles_set):
                raise AuthorizationError(
                    f"Access denied: Requires one of roles: {', '.join(required_roles)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def require_subscription_tier(min_tier: str) -> Callable:
    """
    Decorator to require minimum subscription tier.
    
    Args:
        min_tier: Minimum subscription tier (free, basic, premium, enterprise)
        
    Returns:
        Decorator function
    """
    tier_hierarchy = {"free": 0, "basic": 1, "premium": 2, "enterprise": 3}
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user info
            user_info = None
            for arg in args:
                if hasattr(arg, 'user_id'):
                    user_info = arg
                    break
            
            if user_info is None:
                for key, value in kwargs.items():
                    if hasattr(value, 'user_id'):
                        user_info = value
                        break
            
            if user_info is None:
                raise AuthorizationError("User authentication required")
            
            current_tier = getattr(user_info, 'subscription_tier', 'free')
            current_level = tier_hierarchy.get(current_tier, 0)
            required_level = tier_hierarchy.get(min_tier, 0)
            
            if current_level < required_level:
                raise AuthorizationError(
                    f"Access denied: Requires {min_tier} subscription or higher"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


async def check_resource_access(
    user: UserInfo,
    resource_id: str,
    resource_type: str,
    actions: List[str],
    resource_tenant_id: Optional[str] = None
) -> AuthorizationResponse:
    """
    Check if user has access to perform actions on a resource.
    
    Args:
        user: User information
        resource_id: Resource identifier
        resource_type: Type of resource
        actions: Actions to check
        resource_tenant_id: Resource tenant (defaults to user's tenant)
        
    Returns:
        Authorization response
    """
    return await check_permission(
        user_id=user.user_id,
        tenant_id=user.tenant_id,
        user_roles=user.roles,
        resource_id=resource_id,
        resource_type=resource_type,
        resource_tenant_id=resource_tenant_id or user.tenant_id,
        actions=actions,
        subscription_tier=getattr(user, 'subscription_tier', 'free'),
        region=getattr(user, 'region', None)
    )


async def get_user_permissions(
    user: UserInfo,
    resource_id: str,
    resource_type: str,
    all_actions: List[str]
) -> Dict[str, bool]:
    """
    Get all permissions for a user on a specific resource.
    
    Args:
        user: User information
        resource_id: Resource identifier
        resource_type: Type of resource
        all_actions: All possible actions to check
        
    Returns:
        Dictionary mapping actions to permission status
    """
    auth_response = await check_resource_access(
        user=user,
        resource_id=resource_id,
        resource_type=resource_type,
        actions=all_actions
    )
    
    return auth_response.actions


# FastAPI dependency for authorization checks
async def authorize_resource_access(
    resource_type: str,
    actions: List[str],
    resource_id: str,
    user: UserInfo = Depends(get_current_user)
) -> UserInfo:
    """
    FastAPI dependency for resource authorization.
    
    Args:
        resource_type: Type of resource
        actions: Required actions
        resource_id: Resource identifier
        user: Current user (from JWT)
        
    Returns:
        User info if authorized
        
    Raises:
        AuthorizationError: If access is denied
    """
    auth_response = await check_resource_access(
        user=user,
        resource_id=resource_id,
        resource_type=resource_type,
        actions=actions
    )
    
    if not auth_response.allowed:
        denied_actions = [
            action for action, allowed in auth_response.actions.items() 
            if not allowed
        ]
        raise AuthorizationError(
            f"Access denied for actions: {', '.join(denied_actions)} on {resource_type} {resource_id}"
        )
    
    return user
