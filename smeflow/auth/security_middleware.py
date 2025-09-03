"""
API Security Framework for SMEFlow.

Provides comprehensive API security including rate limiting, CORS, security headers,
and request throttling for African SME multi-tenant environments.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.cache import CacheManager

logger = logging.getLogger(__name__)


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    block_duration_minutes: int = 15


class SecurityConfig(BaseModel):
    """Security configuration for API framework."""
    
    # Rate limiting
    default_rate_limit: RateLimitConfig = RateLimitConfig()
    tenant_rate_limits: Dict[str, RateLimitConfig] = {}
    
    # CORS settings
    allowed_origins: List[str] = ["http://localhost:3000", "https://*.sme-flow.org"]
    allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers: List[str] = ["*"]
    allow_credentials: bool = True
    
    # Security headers
    enable_security_headers: bool = True
    hsts_max_age: int = 31536000  # 1 year
    content_security_policy: str = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https:; "
        "connect-src 'self' https:; "
        "frame-ancestors 'none';"
    )


class RateLimiter:
    """
    Advanced rate limiter with tenant isolation and African market optimizations.
    
    Features:
    - Per-tenant rate limiting
    - Sliding window algorithm
    - Burst protection
    - Automatic IP blocking
    - Redis-backed for distributed environments
    """
    
    def __init__(self, cache_manager: CacheManager, config: SecurityConfig):
        """Initialize rate limiter with cache backend."""
        self.cache = cache_manager
        self.config = config
        self.local_cache: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, datetime] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    async def is_allowed(
        self, 
        client_ip: str, 
        tenant_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is allowed based on rate limits.
        
        Args:
            client_ip: Client IP address
            tenant_id: Tenant identifier for tenant-specific limits
            endpoint: API endpoint for endpoint-specific limits
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        # Check if IP is blocked
        if await self._is_ip_blocked(client_ip):
            return False, {
                "error": "IP temporarily blocked due to rate limit violations",
                "retry_after": self._get_block_remaining_time(client_ip)
            }
        
        # Get rate limit config for tenant
        rate_config = self._get_rate_config(tenant_id)
        
        # Check rate limits
        current_time = time.time()
        
        # Check minute limit
        minute_key = f"rate_limit:{client_ip}:{tenant_id}:minute"
        minute_allowed, minute_info = await self._check_sliding_window(
            minute_key, rate_config.requests_per_minute, 60, current_time
        )
        
        # Check hour limit
        hour_key = f"rate_limit:{client_ip}:{tenant_id}:hour"
        hour_allowed, hour_info = await self._check_sliding_window(
            hour_key, rate_config.requests_per_hour, 3600, current_time
        )
        
        # Check burst limit
        burst_allowed, burst_info = await self._check_burst_limit(
            client_ip, tenant_id, rate_config.burst_limit
        )
        
        is_allowed = minute_allowed and hour_allowed and burst_allowed
        
        # If not allowed, consider blocking IP
        if not is_allowed:
            await self._record_violation(client_ip, tenant_id)
        
        # Cleanup old entries periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            await self._cleanup_old_entries()
            self.last_cleanup = current_time
        
        return is_allowed, {
            "requests_remaining_minute": minute_info["remaining"],
            "requests_remaining_hour": hour_info["remaining"],
            "reset_time_minute": minute_info["reset_time"],
            "reset_time_hour": hour_info["reset_time"],
            "burst_remaining": burst_info.get("remaining", rate_config.burst_limit)
        }
    
    async def _check_sliding_window(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int, 
        current_time: float
    ) -> Tuple[bool, Dict[str, any]]:
        """Check sliding window rate limit."""
        try:
            # Get current request timestamps from cache
            timestamps_str = await self.cache.get(key)
            timestamps = []
            
            if timestamps_str:
                timestamps = [float(ts) for ts in timestamps_str.split(",")]
            
            # Remove old timestamps outside the window
            cutoff_time = current_time - window_seconds
            timestamps = [ts for ts in timestamps if ts > cutoff_time]
            
            # Check if under limit
            if len(timestamps) >= limit:
                return False, {
                    "remaining": 0,
                    "reset_time": int(timestamps[0] + window_seconds)
                }
            
            # Add current timestamp
            timestamps.append(current_time)
            
            # Store updated timestamps
            await self.cache.set(
                key, 
                ",".join(map(str, timestamps)), 
                ttl=window_seconds + 60
            )
            
            return True, {
                "remaining": limit - len(timestamps),
                "reset_time": int(current_time + window_seconds)
            }
            
        except Exception as e:
            logger.error(f"Rate limit check error for {key}: {e}")
            # Fail open - allow request if cache is unavailable
            return True, {"remaining": limit, "reset_time": int(current_time + window_seconds)}
    
    async def _check_burst_limit(
        self, 
        client_ip: str, 
        tenant_id: Optional[str], 
        burst_limit: int
    ) -> Tuple[bool, Dict[str, any]]:
        """Check burst protection (requests in last 10 seconds)."""
        burst_key = f"burst:{client_ip}:{tenant_id}"
        current_time = time.time()
        
        try:
            # Get recent requests
            recent_requests_str = await self.cache.get(burst_key)
            recent_requests = []
            
            if recent_requests_str:
                recent_requests = [float(ts) for ts in recent_requests_str.split(",")]
            
            # Remove requests older than 10 seconds
            cutoff_time = current_time - 10
            recent_requests = [ts for ts in recent_requests if ts > cutoff_time]
            
            if len(recent_requests) >= burst_limit:
                return False, {"remaining": 0}
            
            # Add current request
            recent_requests.append(current_time)
            
            # Store updated requests
            await self.cache.set(
                burst_key,
                ",".join(map(str, recent_requests)),
                ttl=15
            )
            
            return True, {"remaining": burst_limit - len(recent_requests)}
            
        except Exception as e:
            logger.error(f"Burst limit check error: {e}")
            return True, {"remaining": burst_limit}
    
    async def _is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is temporarily blocked."""
        block_key = f"blocked_ip:{client_ip}"
        try:
            blocked_until_str = await self.cache.get(block_key)
            if blocked_until_str:
                blocked_until = datetime.fromisoformat(blocked_until_str)
                return datetime.now() < blocked_until
        except Exception as e:
            logger.error(f"IP block check error: {e}")
        
        return False
    
    def _get_block_remaining_time(self, client_ip: str) -> int:
        """Get remaining block time in seconds."""
        if client_ip in self.blocked_ips:
            remaining = (self.blocked_ips[client_ip] - datetime.now()).total_seconds()
            return max(0, int(remaining))
        return 0
    
    async def _record_violation(self, client_ip: str, tenant_id: Optional[str]):
        """Record rate limit violation and potentially block IP."""
        violation_key = f"violations:{client_ip}"
        
        try:
            # Get current violation count
            violations_str = await self.cache.get(violation_key)
            violations = int(violations_str) if violations_str else 0
            violations += 1
            
            # Store updated violation count
            await self.cache.set(violation_key, str(violations), ttl=3600)  # 1 hour
            
            # Block IP if too many violations
            if violations >= 5:  # Block after 5 violations in an hour
                block_until = datetime.now() + timedelta(
                    minutes=self.config.default_rate_limit.block_duration_minutes
                )
                block_key = f"blocked_ip:{client_ip}"
                await self.cache.set(
                    block_key, 
                    block_until.isoformat(), 
                    ttl=self.config.default_rate_limit.block_duration_minutes * 60
                )
                
                logger.warning(f"Blocked IP {client_ip} due to rate limit violations")
                
        except Exception as e:
            logger.error(f"Error recording violation: {e}")
    
    def _get_rate_config(self, tenant_id: Optional[str]) -> RateLimitConfig:
        """Get rate limit configuration for tenant."""
        if tenant_id and tenant_id in self.config.tenant_rate_limits:
            return self.config.tenant_rate_limits[tenant_id]
        return self.config.default_rate_limit
    
    async def _cleanup_old_entries(self):
        """Cleanup old rate limit entries."""
        try:
            # This would be implemented with Redis SCAN in production
            # For now, we rely on TTL for cleanup
            logger.debug("Rate limiter cleanup completed")
        except Exception as e:
            logger.error(f"Rate limiter cleanup error: {e}")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    def __init__(self, app, config: SecurityConfig):
        """Initialize security headers middleware."""
        super().__init__(app)
        self.config = config
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        if self.config.enable_security_headers:
            # HSTS (HTTP Strict Transport Security)
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.config.hsts_max_age}; includeSubDomains; preload"
            )
            
            # Content Security Policy
            response.headers["Content-Security-Policy"] = self.config.content_security_policy
            
            # X-Frame-Options
            response.headers["X-Frame-Options"] = "DENY"
            
            # X-Content-Type-Options
            response.headers["X-Content-Type-Options"] = "nosniff"
            
            # X-XSS-Protection
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            # Referrer Policy
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # Permissions Policy
            response.headers["Permissions-Policy"] = (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            )
            
        # Remove server information for security
        if "Server" in response.headers:
            del response.headers["Server"]
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for API rate limiting with tenant isolation."""
    
    def __init__(self, app, rate_limiter: RateLimiter):
        """Initialize rate limiting middleware."""
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.exempt_paths = {
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc"
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Apply rate limiting to requests."""
        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Get tenant ID from request state (set by JWT middleware)
        tenant_id = getattr(request.state, "tenant_id", None)
        
        # Check rate limits
        is_allowed, rate_info = await self.rate_limiter.is_allowed(
            client_ip=client_ip,
            tenant_id=tenant_id,
            endpoint=request.url.path
        )
        
        if not is_allowed:
            # Return rate limit exceeded response
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": rate_info.get("error", "Too many requests"),
                    "retry_after": rate_info.get("retry_after", 60)
                },
                headers={
                    "Retry-After": str(rate_info.get("retry_after", 60)),
                    "X-RateLimit-Remaining-Minute": str(rate_info.get("requests_remaining_minute", 0)),
                    "X-RateLimit-Remaining-Hour": str(rate_info.get("requests_remaining_hour", 0))
                }
            )
        
        # Add rate limit headers to successful responses
        response = await call_next(request)
        
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            rate_info.get("requests_remaining_minute", 0)
        )
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            rate_info.get("requests_remaining_hour", 0)
        )
        response.headers["X-RateLimit-Reset-Minute"] = str(
            rate_info.get("reset_time_minute", 0)
        )
        response.headers["X-RateLimit-Reset-Hour"] = str(
            rate_info.get("reset_time_hour", 0)
        )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers (common in African cloud deployments)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"


def setup_cors_middleware(app, config: SecurityConfig):
    """Setup CORS middleware with African market optimizations."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=config.allow_credentials,
        allow_methods=config.allowed_methods,
        allow_headers=config.allowed_headers,
        expose_headers=[
            "X-RateLimit-Remaining-Minute",
            "X-RateLimit-Remaining-Hour",
            "X-RateLimit-Reset-Minute",
            "X-RateLimit-Reset-Hour"
        ]
    )


def create_security_config() -> SecurityConfig:
    """Create security configuration from environment settings."""
    settings = get_settings()
    
    # African market specific origins
    african_origins = [
        "https://*.sme-flow.org",
        "https://*.smeflow.africa",
        "https://localhost:3000",
        "http://localhost:3000",
        "https://localhost:8000",
        "http://localhost:8000"
    ]
    
    # Add environment-specific origins
    if hasattr(settings, 'CORS_ORIGINS') and settings.CORS_ORIGINS:
        african_origins.extend(settings.CORS_ORIGINS.split(","))
    
    return SecurityConfig(
        allowed_origins=african_origins,
        default_rate_limit=RateLimitConfig(
            requests_per_minute=getattr(settings, 'RATE_LIMIT_PER_MINUTE', 60),
            requests_per_hour=getattr(settings, 'RATE_LIMIT_PER_HOUR', 1000),
            burst_limit=getattr(settings, 'RATE_LIMIT_BURST', 10),
            block_duration_minutes=getattr(settings, 'RATE_LIMIT_BLOCK_DURATION', 15)
        )
    )
