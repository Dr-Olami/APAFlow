"""
JWT Middleware for SMEFlow Authentication

Provides JWT token validation middleware for FastAPI endpoints with multi-tenant
support and African market optimizations.
"""

import logging
from typing import Optional, Dict, Any, List
from functools import wraps

import jwt
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..core.config import get_settings
from ..database.models import Tenant
from .keycloak_client import KeycloakClient

logger = logging.getLogger(__name__)

# Security scheme for FastAPI
security = HTTPBearer()


class JWTMiddleware(BaseHTTPMiddleware):
    """
    JWT authentication middleware for SMEFlow.
    
    Validates JWT tokens from Keycloak and extracts tenant information
    for multi-tenant isolation in African SME contexts.
    """
    
    def __init__(self, app, keycloak_client: KeycloakClient):
        """Initialize JWT middleware with Keycloak client."""
        super().__init__(app)
        self.keycloak_client = keycloak_client
        self.settings = get_settings()
        self.public_paths = {
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/auth/login",
            "/auth/register",
            "/auth/callback"
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with JWT validation."""
        # Skip authentication for public paths
        if any(request.url.path.startswith(path) for path in self.public_paths):
            return await call_next(request)
        
        # Extract and validate JWT token
        try:
            token = await self._extract_token(request)
            if token:
                user_info = await self._validate_token(token, request)
                request.state.user = user_info
                request.state.tenant_id = user_info.get("tenant_id")
                request.state.token = token
            else:
                # No token provided for protected endpoint
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"JWT middleware error: {e}")
            raise HTTPException(
                status_code=401,
                detail="Authentication failed"
            )
        
        return await call_next(request)
    
    async def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request headers."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        if not auth_header.startswith("Bearer "):
            return None
        
        return auth_header.split(" ", 1)[1]
    
    async def _validate_token(self, token: str, request: Request) -> Dict[str, Any]:
        """
        Validate JWT token and extract user information.
        
        Args:
            token: JWT access token
            request: FastAPI request object
            
        Returns:
            Dict containing user and tenant information
        """
        try:
            # Decode token without verification first to get realm info
            unverified_payload = jwt.decode(
                token, 
                options={"verify_signature": False}
            )
            
            # Extract realm from issuer
            issuer = unverified_payload.get("iss", "")
            realm_name = issuer.split("/")[-1] if "/" in issuer else "smeflow"
            
            # Validate token with Keycloak
            user_info = await self.keycloak_client.validate_token(token, realm_name)
            
            # Extract tenant information from token claims
            tenant_id = unverified_payload.get("tenant_id") or user_info.get("tenant_id")
            if not tenant_id:
                # Try to extract from realm name or user attributes
                tenant_id = await self._resolve_tenant_id(realm_name, user_info)
            
            return {
                "user_id": user_info.get("sub"),
                "username": user_info.get("preferred_username"),
                "email": user_info.get("email"),
                "tenant_id": tenant_id,
                "realm": realm_name,
                "roles": unverified_payload.get("realm_access", {}).get("roles", []),
                "token_type": unverified_payload.get("typ", "Bearer")
            }
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise HTTPException(
                status_code=401,
                detail="Authentication validation failed"
            )
    
    async def _resolve_tenant_id(self, realm_name: str, user_info: Dict[str, Any]) -> Optional[str]:
        """Resolve tenant ID from realm name or user information."""
        # If realm follows pattern: tenant-{tenant_id}
        if realm_name.startswith("tenant-"):
            return realm_name.replace("tenant-", "")
        
        # Check user attributes for tenant information
        if "tenant_id" in user_info:
            return user_info["tenant_id"]
        
        # Default to realm name as tenant identifier
        return realm_name


class TenantAuthDependency:
    """FastAPI dependency for tenant-aware authentication."""
    
    def __init__(self, required_roles: Optional[List[str]] = None):
        """Initialize with optional required roles."""
        self.required_roles = required_roles or []
    
    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """
        Validate authentication and return user information.
        
        Args:
            request: FastAPI request object
            credentials: HTTP authorization credentials
            
        Returns:
            Dict containing authenticated user information
        """
        # Check if user info is already in request state (from middleware)
        if hasattr(request.state, "user"):
            user_info = request.state.user
        else:
            # Fallback: validate token directly
            keycloak_client = KeycloakClient()
            try:
                # Extract realm from token
                unverified_payload = jwt.decode(
                    credentials.credentials,
                    options={"verify_signature": False}
                )
                issuer = unverified_payload.get("iss", "")
                realm_name = issuer.split("/")[-1] if "/" in issuer else "smeflow"
                
                # Validate with Keycloak
                user_info = await keycloak_client.validate_token(
                    credentials.credentials, 
                    realm_name
                )
                
                # Add tenant information
                tenant_id = unverified_payload.get("tenant_id", realm_name)
                user_info.update({
                    "tenant_id": tenant_id,
                    "realm": realm_name,
                    "roles": unverified_payload.get("realm_access", {}).get("roles", [])
                })
                
            except Exception as e:
                logger.error(f"Authentication dependency error: {e}")
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            finally:
                await keycloak_client.close()
        
        # Check required roles
        if self.required_roles:
            user_roles = user_info.get("roles", [])
            if not any(role in user_roles for role in self.required_roles):
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions"
                )
        
        return user_info


# Convenience functions for common authentication patterns
def require_auth(required_roles: Optional[List[str]] = None):
    """Decorator for requiring authentication with optional roles."""
    return Depends(TenantAuthDependency(required_roles))


def require_admin():
    """Dependency for requiring admin role."""
    return require_auth(["admin", "smeflow-admin"])


def require_tenant_access():
    """Dependency for requiring tenant access."""
    return require_auth(["tenant-user", "tenant-admin", "admin"])


async def get_current_user(request: Request) -> Dict[str, Any]:
    """Get current authenticated user from request state."""
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    return request.state.user


async def get_current_tenant_id(request: Request) -> str:
    """Get current tenant ID from request state."""
    if not hasattr(request.state, "tenant_id") or not request.state.tenant_id:
        raise HTTPException(
            status_code=401,
            detail="Tenant context required"
        )
    return request.state.tenant_id
