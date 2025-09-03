"""
SMEFlow main application entry point.
"""

import asyncio
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database.connection import database_manager
from .core.config import settings
from .core.cache import cache_manager
from smeflow.core.logging import setup_logging
from smeflow.api.routes import api_router
from .auth.security_middleware import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RateLimiter,
    create_security_config,
    setup_cors_middleware
)
from .auth.jwt_middleware import JWTMiddleware
from .auth.keycloak_client import KeycloakClient


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured application instance.
    """
    app = FastAPI(
        title="SMEFlow API",
        description="Agentic Process Automation Platform for African SMEs",
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )
    
    # Create security configuration
    security_config = create_security_config()
    
    # Setup CORS middleware with African market optimizations
    setup_cors_middleware(app, security_config)
    
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware, config=security_config)
    
    # Add rate limiting middleware
    rate_limiter = RateLimiter(cache_manager, security_config)
    app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)
    
    # Add JWT authentication middleware
    keycloak_client = KeycloakClient()
    app.add_middleware(JWTMiddleware, keycloak_client=keycloak_client)
    
    # Include API routes
    app.include_router(api_router)
    
    # Startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup."""
        await database_manager.initialize()
        await cache_manager.initialize()
        # Initialize Keycloak client
        await keycloak_client.initialize()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup services on shutdown."""
        await database_manager.close()
        await cache_manager.close()
        await keycloak_client.close()
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}
    
    # Cache health check endpoint
    @app.get("/health/cache")
    async def cache_health_check():
        """Cache health check endpoint."""
        health_status = await cache_manager.health_check()
        return health_status
    
    return app


def main():
    """Main entry point for the SMEFlow application."""
    setup_logging()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print("SMEFlow v0.1.0")
        return
    
    app = create_app()
    
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=None,  # We handle logging ourselves
    )


if __name__ == "__main__":
    main()
