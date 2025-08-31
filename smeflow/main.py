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
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router)
    
    # Startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup."""
        await database_manager.initialize()
        await cache_manager.initialize()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup services on shutdown."""
        await database_manager.close()
        await cache_manager.close()
    
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
