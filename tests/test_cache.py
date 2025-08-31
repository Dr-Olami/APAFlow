"""
Tests for Redis cache functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import timedelta

from smeflow.core.cache import CacheManager, CacheConfig


class TestCacheManager:
    """Test cases for CacheManager."""

    @pytest.fixture
    async def cache_manager(self):
        """Create a test cache manager instance."""
        config = CacheConfig(
            host="localhost",
            port=6379,
            db=1,  # Use different DB for tests
        )
        manager = CacheManager(config)
        return manager

    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache_manager):
        """Test basic cache set and get operations."""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.ping.return_value = True
            mock_client.get.return_value = b'"test_value"'
            mock_client.set.return_value = True
            
            cache_manager._client = mock_client
            
            # Test set
            result = await cache_manager.set("tenant1", "test_key", "test_value")
            assert result is True
            
            # Test get
            value = await cache_manager.get("tenant1", "test_key")
            assert value == "test_value"

    @pytest.mark.asyncio
    async def test_cache_tenant_isolation(self, cache_manager):
        """Test that cache keys are tenant-isolated."""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.set.return_value = True
            
            cache_manager._client = mock_client
            
            await cache_manager.set("tenant1", "key", "value1")
            await cache_manager.set("tenant2", "key", "value2")
            
            # Verify tenant-specific keys were used
            calls = mock_client.set.call_args_list
            assert calls[0][0][0] == "tenant:tenant1:key"
            assert calls[1][0][0] == "tenant:tenant2:key"

    @pytest.mark.asyncio
    async def test_cache_ttl(self, cache_manager):
        """Test cache TTL functionality."""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.set.return_value = True
            
            cache_manager._client = mock_client
            
            # Test with integer TTL
            await cache_manager.set("tenant1", "key", "value", ttl=300)
            mock_client.set.assert_called_with("tenant:tenant1:key", "value", ex=300)
            
            # Test with timedelta TTL
            await cache_manager.set("tenant1", "key2", "value", ttl=timedelta(minutes=5))
            mock_client.set.assert_called_with("tenant:tenant1:key2", "value", ex=300)

    @pytest.mark.asyncio
    async def test_cache_health_check(self, cache_manager):
        """Test cache health check functionality."""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.set.return_value = True
            mock_client.get.return_value = b"ok"
            mock_client.delete.return_value = 1
            
            cache_manager._client = mock_client
            
            health = await cache_manager.health_check()
            assert health["status"] == "healthy"
            assert "Cache operational" in health["message"]

    @pytest.mark.asyncio
    async def test_cache_clear_tenant(self, cache_manager):
        """Test clearing all cache entries for a tenant."""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.keys.return_value = [b"tenant:tenant1:key1", b"tenant:tenant1:key2"]
            mock_client.delete.return_value = 2
            
            cache_manager._client = mock_client
            
            result = await cache_manager.clear_tenant("tenant1")
            assert result == 2
            mock_client.keys.assert_called_with("tenant:tenant1:*")

    @pytest.mark.asyncio
    async def test_cache_not_initialized(self, cache_manager):
        """Test cache operations when not initialized."""
        # Don't initialize the client
        cache_manager._client = None
        
        # Operations should return defaults/False without errors
        result = await cache_manager.get("tenant1", "key", "default")
        assert result == "default"
        
        result = await cache_manager.set("tenant1", "key", "value")
        assert result is False
        
        result = await cache_manager.exists("tenant1", "key")
        assert result is False
