"""
Database connection management for SMEFlow.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from smeflow.core.config import settings
from smeflow.core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class DatabaseManager:
    """
    Manages database connections and sessions with multi-tenant support.
    """
    
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
    
    async def initialize(self) -> None:
        """
        Initialize database connection and session factory.
        """
        if self._engine is not None:
            return
        
        logger.info("Initializing database connection", url=settings.DATABASE_URL.split("@")[-1])
        
        self._engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            echo=settings.DEBUG,
            future=True,
        )
        
        # Add connection event listeners
        @event.listens_for(self._engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas if using SQLite."""
            if "sqlite" in settings.DATABASE_URL:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        logger.info("Database connection initialized successfully")
    
    async def close(self) -> None:
        """
        Close database connections.
        """
        if self._engine:
            logger.info("Closing database connections")
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
    
    @asynccontextmanager
    async def get_session(self, tenant_id: Optional[str] = None) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session with optional tenant context.
        
        Args:
            tenant_id: Tenant ID for multi-tenant operations.
            
        Yields:
            AsyncSession: Database session.
        """
        if not self._session_factory:
            await self.initialize()
        
        async with self._session_factory() as session:
            try:
                # Set tenant context if provided
                if tenant_id:
                    await session.execute(
                        text("SET search_path TO :tenant_schema, public"),
                        {"tenant_schema": f"tenant_{tenant_id}"}
                    )
                
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def create_tenant_schema(self, tenant_id: str) -> None:
        """
        Create a new tenant schema.
        
        Args:
            tenant_id: Unique tenant identifier.
        """
        schema_name = f"tenant_{tenant_id}"
        
        async with self.get_session() as session:
            # Create schema
            await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            
            # Set search path and create tables
            await session.execute(text(f"SET search_path TO {schema_name}, public"))
            
            # Create tables in tenant schema
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Created tenant schema", tenant_id=tenant_id, schema=schema_name)
    
    async def drop_tenant_schema(self, tenant_id: str) -> None:
        """
        Drop a tenant schema and all its data.
        
        Args:
            tenant_id: Tenant identifier.
        """
        schema_name = f"tenant_{tenant_id}"
        
        async with self.get_session() as session:
            await session.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
        
        logger.info("Dropped tenant schema", tenant_id=tenant_id, schema=schema_name)
    
    async def health_check(self) -> bool:
        """
        Check database connectivity.
        
        Returns:
            bool: True if database is accessible.
        """
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False


# Global database manager instance
db_manager = DatabaseManager()
