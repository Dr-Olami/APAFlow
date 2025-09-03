"""
API Security Integration Tests for SMEFlow.

Tests the comprehensive API security framework including JWT validation,
rate limiting, CORS, and security headers for African SME environments.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from smeflow.auth.security_middleware import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RateLimiter,
    SecurityConfig,
    RateLimitConfig,
    create_security_config
)
from smeflow.auth.jwt_middleware import JWTMiddleware, UserInfo
from smeflow.core.cache import CacheManager


class TestSecurityConfig:
    """Test security configuration."""
    
    def test_default_security_config(self):
        """Test default security configuration creation."""
        config = SecurityConfig()
        
        assert config.default_rate_limit.requests_per_minute == 60
        assert config.default_rate_limit.requests_per_hour == 1000
        assert config.default_rate_limit.burst_limit == 10
        assert config.enable_security_headers is True
        assert "https://*.sme-flow.org" in config.allowed_origins
    
    def test_rate_limit_config(self):
        """Test rate limit configuration."""
        config = RateLimitConfig(
            requests_per_minute=120,
            requests_per_hour=2000,
            burst_limit=20,
            block_duration_minutes=30
        )
        
        assert config.requests_per_minute == 120
        assert config.requests_per_hour == 2000
        assert config.burst_limit == 20
        assert config.block_duration_minutes == 30


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    @pytest.fixture
    def mock_cache(self):
        """Mock cache manager."""
        cache = AsyncMock(spec=CacheManager)
        cache.get.return_value = None
        cache.set.return_value = None
        return cache
    
    @pytest.fixture
    def security_config(self):
        """Security configuration for testing."""
        return SecurityConfig(
            default_rate_limit=RateLimitConfig(
                requests_per_minute=5,
                requests_per_hour=20,
                burst_limit=3,
                block_duration_minutes=1
            )
        )
    
    @pytest.fixture
    def rate_limiter(self, mock_cache, security_config):
        """Rate limiter instance."""
        return RateLimiter(mock_cache, security_config)
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_first_request(self, rate_limiter):
        """Test that first request is allowed."""
        is_allowed, info = await rate_limiter.is_allowed("192.168.1.1", "tenant1")
        
        assert is_allowed is True
        assert info["requests_remaining_minute"] == 4  # 5 - 1
        assert info["requests_remaining_hour"] == 19   # 20 - 1
    
    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_after_limit(self, rate_limiter, mock_cache):
        """Test that requests are blocked after limit is reached."""
        # Mock cache to return timestamps indicating limit reached
        current_time = time.time()
        timestamps = [str(current_time - i) for i in range(5)]  # 5 requests in last minute
        mock_cache.get.return_value = ",".join(timestamps)
        
        is_allowed, info = await rate_limiter.is_allowed("192.168.1.1", "tenant1")
        
        assert is_allowed is False
        assert info["requests_remaining_minute"] == 0
    
    @pytest.mark.asyncio
    async def test_burst_protection(self, rate_limiter, mock_cache):
        """Test burst protection functionality."""
        # Mock recent requests within 10 seconds
        current_time = time.time()
        recent_requests = [str(current_time - i) for i in range(3)]  # 3 requests in last 10 seconds
        
        async def mock_get(key):
            if "burst:" in key:
                return ",".join(recent_requests)
            return None
        
        mock_cache.get.side_effect = mock_get
        
        is_allowed, info = await rate_limiter.is_allowed("192.168.1.1", "tenant1")
        
        # Should be blocked due to burst limit
        assert is_allowed is False
    
    @pytest.mark.asyncio
    async def test_ip_blocking_after_violations(self, rate_limiter, mock_cache):
        """Test IP blocking after multiple violations."""
        # Mock violation count
        mock_cache.get.return_value = "5"  # 5 violations
        
        # This should trigger IP blocking
        await rate_limiter._record_violation("192.168.1.1", "tenant1")
        
        # Verify that set was called to block the IP
        mock_cache.set.assert_called()
        
        # Check if the call was for blocking
        calls = mock_cache.set.call_args_list
        block_call = next((call for call in calls if "blocked_ip:" in call[0][0]), None)
        assert block_call is not None
    
    @pytest.mark.asyncio
    async def test_tenant_specific_rate_limits(self, mock_cache):
        """Test tenant-specific rate limits."""
        config = SecurityConfig(
            tenant_rate_limits={
                "premium_tenant": RateLimitConfig(
                    requests_per_minute=120,
                    requests_per_hour=5000,
                    burst_limit=20
                )
            }
        )
        
        rate_limiter = RateLimiter(mock_cache, config)
        
        # Test premium tenant gets higher limits
        is_allowed, info = await rate_limiter.is_allowed("192.168.1.1", "premium_tenant")
        
        assert is_allowed is True
        assert info["requests_remaining_minute"] == 119  # 120 - 1
        assert info["requests_remaining_hour"] == 4999   # 5000 - 1


class TestSecurityMiddleware:
    """Test security middleware integration."""
    
    def test_security_headers_middleware(self):
        """Test security headers are added to responses."""
        app = FastAPI()
        config = SecurityConfig()
        
        app.add_middleware(SecurityHeadersMiddleware, config=config)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Check security headers
        assert "Strict-Transport-Security" in response.headers
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers
        
        # Check header values
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    
    def test_rate_limit_middleware_blocks_requests(self):
        """Test rate limit middleware blocks excessive requests."""
        app = FastAPI()
        
        # Mock cache and rate limiter
        mock_cache = AsyncMock(spec=CacheManager)
        config = SecurityConfig(
            default_rate_limit=RateLimitConfig(requests_per_minute=1)
        )
        rate_limiter = RateLimiter(mock_cache, config)
        
        # Mock rate limiter to deny requests
        async def mock_is_allowed(*args, **kwargs):
            return False, {
                "error": "Rate limit exceeded",
                "retry_after": 60,
                "requests_remaining_minute": 0,
                "requests_remaining_hour": 0
            }
        
        rate_limiter.is_allowed = mock_is_allowed
        
        app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["error"]
        assert "Retry-After" in response.headers
    
    def test_rate_limit_middleware_adds_headers(self):
        """Test rate limit middleware adds rate limit headers."""
        app = FastAPI()
        
        # Mock cache and rate limiter
        mock_cache = AsyncMock(spec=CacheManager)
        config = SecurityConfig()
        rate_limiter = RateLimiter(mock_cache, config)
        
        # Mock rate limiter to allow requests
        async def mock_is_allowed(*args, **kwargs):
            return True, {
                "requests_remaining_minute": 59,
                "requests_remaining_hour": 999,
                "reset_time_minute": int(time.time() + 60),
                "reset_time_hour": int(time.time() + 3600)
            }
        
        rate_limiter.is_allowed = mock_is_allowed
        
        app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-RateLimit-Remaining-Minute" in response.headers
        assert "X-RateLimit-Remaining-Hour" in response.headers
        assert response.headers["X-RateLimit-Remaining-Minute"] == "59"
        assert response.headers["X-RateLimit-Remaining-Hour"] == "999"


class TestJWTMiddleware:
    """Test JWT middleware functionality."""
    
    @pytest.fixture
    def mock_keycloak_client(self):
        """Mock Keycloak client."""
        client = AsyncMock()
        client.validate_token.return_value = {
            "sub": "user123",
            "preferred_username": "testuser",
            "email": "test@example.com",
            "tenant_id": "tenant123"
        }
        return client
    
    def test_jwt_middleware_allows_public_paths(self, mock_keycloak_client):
        """Test JWT middleware allows access to public paths."""
        app = FastAPI()
        app.add_middleware(JWTMiddleware, keycloak_client=mock_keycloak_client)
        
        @app.get("/health")
        async def health_endpoint():
            return {"status": "healthy"}
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_jwt_middleware_requires_auth_for_protected_paths(self, mock_keycloak_client):
        """Test JWT middleware requires authentication for protected paths."""
        app = FastAPI()
        app.add_middleware(JWTMiddleware, keycloak_client=mock_keycloak_client)
        
        @app.get("/api/protected")
        async def protected_endpoint():
            return {"message": "protected"}
        
        client = TestClient(app)
        
        # Test without authorization header
        with pytest.raises(Exception) as exc_info:
            response = client.get("/api/protected")
        
        # The middleware should raise HTTPException which gets converted by FastAPI
        assert "401" in str(exc_info.value) or "Authentication required" in str(exc_info.value)
    
    def test_jwt_middleware_validates_valid_token(self, mock_keycloak_client):
        """Test JWT middleware validates valid tokens."""
        app = FastAPI()
        app.add_middleware(JWTMiddleware, keycloak_client=mock_keycloak_client)
        
        @app.get("/api/protected")
        async def protected_endpoint(request: Request):
            return {
                "message": "protected",
                "user": getattr(request.state, "user", None),
                "tenant_id": getattr(request.state, "tenant_id", None)
            }
        
        # Mock JWT token
        with patch('jwt.decode') as mock_decode:
            mock_decode.return_value = {
                "sub": "user123",
                "iss": "http://keycloak:8080/auth/realms/tenant123",
                "tenant_id": "tenant123",
                "realm_access": {"roles": ["user"]}
            }
            
            client = TestClient(app)
            response = client.get(
                "/api/protected",
                headers={"Authorization": "Bearer valid_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "protected"
            assert data["tenant_id"] == "tenant123"


class TestCORSConfiguration:
    """Test CORS configuration for African markets."""
    
    def test_cors_allows_african_domains(self):
        """Test CORS allows African market domains."""
        config = create_security_config()
        
        # Check that African market domains are included
        assert any("sme-flow.org" in origin for origin in config.allowed_origins)
        assert any("smeflow.africa" in origin for origin in config.allowed_origins)
    
    def test_cors_headers_in_response(self):
        """Test CORS headers are properly set."""
        from fastapi.middleware.cors import CORSMiddleware
        
        app = FastAPI()
        
        # Add CORS middleware with specific allowed origins including localhost:3000
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://localhost:3000", "https://app.sme-flow.org"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        
        # Test actual request with origin that's in allowed list
        response = client.get(
            "/test",
            headers={"Origin": "https://localhost:3000"}
        )
        
        assert response.status_code == 200
        # CORS headers should be present for cross-origin requests
        assert "access-control-allow-origin" in response.headers or "Access-Control-Allow-Origin" in response.headers


class TestAfricanMarketOptimizations:
    """Test African market specific optimizations."""
    
    def test_client_ip_extraction_with_african_proxies(self):
        """Test client IP extraction works with African cloud proxies."""
        from smeflow.auth.security_middleware import RateLimitMiddleware
        
        app = FastAPI()
        mock_cache = AsyncMock()
        config = SecurityConfig()
        rate_limiter = RateLimiter(mock_cache, config)
        middleware = RateLimitMiddleware(app, rate_limiter)
        
        # Mock request with African proxy headers
        mock_request = MagicMock()
        mock_request.headers = {
            "X-Forwarded-For": "41.191.226.1, 10.0.0.1",  # Nigerian IP
            "X-Real-IP": "41.191.226.1"
        }
        mock_request.client = None
        
        client_ip = middleware._get_client_ip(mock_request)
        assert client_ip == "41.191.226.1"
    
    def test_tenant_specific_rate_limits_for_african_regions(self):
        """Test tenant-specific rate limits for African regions."""
        config = SecurityConfig(
            tenant_rate_limits={
                "nigeria_tenant": RateLimitConfig(requests_per_minute=100),
                "kenya_tenant": RateLimitConfig(requests_per_minute=80),
                "south_africa_tenant": RateLimitConfig(requests_per_minute=120)
            }
        )
        
        mock_cache = AsyncMock()
        rate_limiter = RateLimiter(mock_cache, config)
        
        # Test different limits for different regions
        nigeria_config = rate_limiter._get_rate_config("nigeria_tenant")
        kenya_config = rate_limiter._get_rate_config("kenya_tenant")
        sa_config = rate_limiter._get_rate_config("south_africa_tenant")
        
        assert nigeria_config.requests_per_minute == 100
        assert kenya_config.requests_per_minute == 80
        assert sa_config.requests_per_minute == 120


class TestSecurityIntegration:
    """Test full security framework integration."""
    
    def test_complete_security_stack(self):
        """Test complete security middleware stack."""
        app = FastAPI()
        
        # Mock dependencies
        mock_cache = AsyncMock()
        mock_keycloak = AsyncMock()
        mock_keycloak.validate_token.return_value = {
            "sub": "user123",
            "preferred_username": "testuser",
            "email": "test@smeflow.africa",
            "tenant_id": "african_sme_tenant"
        }
        
        # Setup security stack
        config = SecurityConfig()
        rate_limiter = RateLimiter(mock_cache, config)
        
        # Add middleware in correct order (reverse of execution order)
        app.add_middleware(SecurityHeadersMiddleware, config=config)
        app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)
        
        # Use a non-exempted endpoint to test rate limiting
        @app.get("/api/test")
        async def test_endpoint():
            return {"message": "test"}
        
        # Mock rate limiter to allow requests
        async def mock_is_allowed(*args, **kwargs):
            return True, {
                "requests_remaining_minute": 59,
                "requests_remaining_hour": 999,
                "reset_time_minute": int(time.time() + 60),
                "reset_time_hour": int(time.time() + 3600)
            }
        
        rate_limiter.is_allowed = mock_is_allowed
        
        client = TestClient(app)
        response = client.get("/api/test")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "test"
        
        # Verify security headers
        assert "Strict-Transport-Security" in response.headers
        assert "X-Frame-Options" in response.headers
        
        # Verify rate limit headers
        assert "X-RateLimit-Remaining-Minute" in response.headers


if __name__ == "__main__":
    pytest.main([__file__])
