"""
Redis caching layer for SMEFlow platform.

Provides tenant-aware caching with connection pooling and async support.
"""

import json
import logging
from typing import Any, Optional, Union
from datetime import timedelta

import redis.asyncio as redis
from redis.asyncio import ConnectionPool
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)


class CacheConfig(BaseModel):
    """Configuration for Redis cache."""
    
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 20
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    retry_on_timeout: bool = True
    health_check_interval: int = 30


class CacheManager:
    """
    Async Redis cache manager with tenant isolation.
    
    Provides tenant-aware caching operations with automatic key prefixing
    and connection pooling for optimal performance.
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize cache manager with configuration."""
        self.config = config or CacheConfig(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
        )
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
    
    async def initialize(self) -> None:
        """Initialize Redis connection pool."""
        try:
            self._pool = ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                health_check_interval=self.config.health_check_interval,
            )
            
            self._client = redis.Redis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            logger.info("Redis cache initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            raise
    
    async def close(self) -> None:
        """Close Redis connections."""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        logger.info("Redis cache connections closed")
    
    def _get_tenant_key(self, tenant_id: str, key: str) -> str:
        """Generate tenant-specific cache key."""
        return f"tenant:{tenant_id}:{key}"
    
    async def get(
        self, 
        tenant_id: str, 
        key: str, 
        default: Any = None
    ) -> Any:
        """
        Get value from cache for specific tenant.
        
        Args:
            tenant_id: Tenant identifier
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        if not self._client:
            logger.warning("Cache not initialized, returning default")
            return default
        
        try:
            tenant_key = self._get_tenant_key(tenant_id, key)
            value = await self._client.get(tenant_key)
            
            if value is None:
                return default
            
            # Try to deserialize JSON, fallback to string
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value.decode('utf-8') if isinstance(value, bytes) else value
                
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return default
    
    async def set(
        self,
        tenant_id: str,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        Set value in cache for specific tenant.
        
        Args:
            tenant_id: Tenant identifier
            key: Cache key
            value: Value to cache
            ttl: Time to live (seconds or timedelta)
            
        Returns:
            True if successful, False otherwise
        """
        if not self._client:
            logger.warning("Cache not initialized, skipping set")
            return False
        
        try:
            tenant_key = self._get_tenant_key(tenant_id, key)
            
            # Serialize value
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            # Convert timedelta to seconds
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            await self._client.set(tenant_key, serialized_value, ex=ttl)
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False
    
    async def delete(self, tenant_id: str, key: str) -> bool:
        """
        Delete value from cache for specific tenant.
        
        Args:
            tenant_id: Tenant identifier
            key: Cache key
            
        Returns:
            True if key was deleted, False otherwise
        """
        if not self._client:
            logger.warning("Cache not initialized, skipping delete")
            return False
        
        try:
            tenant_key = self._get_tenant_key(tenant_id, key)
            result = await self._client.delete(tenant_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            return False
    
    async def exists(self, tenant_id: str, key: str) -> bool:
        """
        Check if key exists in cache for specific tenant.
        
        Args:
            tenant_id: Tenant identifier
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        if not self._client:
            return False
        
        try:
            tenant_key = self._get_tenant_key(tenant_id, key)
            result = await self._client.exists(tenant_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache exists error for {key}: {e}")
            return False
    
    async def clear_tenant(self, tenant_id: str) -> int:
        """
        Clear all cache entries for a specific tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Number of keys deleted
        """
        if not self._client:
            logger.warning("Cache not initialized, skipping clear")
            return 0
        
        try:
            pattern = f"tenant:{tenant_id}:*"
            keys = await self._client.keys(pattern)
            
            if not keys:
                return 0
            
            result = await self._client.delete(*keys)
            logger.info(f"Cleared {result} cache entries for tenant {tenant_id}")
            return result
            
        except Exception as e:
            logger.error(f"Cache clear error for tenant {tenant_id}: {e}")
            return 0
    
    async def health_check(self) -> dict:
        """
        Perform health check on Redis connection.
        
        Returns:
            Health status information
        """
        if not self._client:
            return {"status": "error", "message": "Cache not initialized"}
        
        try:
            # Test basic operations
            test_key = "health_check"
            await self._client.set(test_key, "ok", ex=10)
            value = await self._client.get(test_key)
            await self._client.delete(test_key)
            
            if value == b"ok":
                return {"status": "healthy", "message": "Cache operational"}
            else:
                return {"status": "error", "message": "Cache test failed"}
                
        except Exception as e:
            return {"status": "error", "message": f"Cache error: {e}"}


# Global cache manager instance
cache_manager = CacheManager()


async def get_cache() -> CacheManager:
    """Get the global cache manager instance."""
    return cache_manager
