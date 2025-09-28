"""
API routes for SMEFlow.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from smeflow.core.logging import get_logger
from smeflow.database.connection import db_manager
from .workflow_routes import router as workflow_router
from .agent_routes import router as agent_router
from .langgraph_workflow_routes import router as langgraph_router
from .flowise_integration_routes import router as flowise_router

logger = get_logger(__name__)
security = HTTPBearer()

# Create API router
api_router = APIRouter(prefix="/api/v1")


@api_router.get("/health")
async def health_check():
    """
    Health check endpoint for the API.
    
    Returns:
        dict: Health status and database connectivity.
    """
    db_healthy = await db_manager.health_check()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "version": "0.1.0",
        "database": "connected" if db_healthy else "disconnected"
    }


@api_router.get("/tenants")
async def list_tenants():
    """
    List all tenants (admin endpoint).
    
    Returns:
        dict: List of tenants.
    """
    # TODO: Add authentication and authorization
    # TODO: Implement tenant listing logic
    return {"tenants": [], "message": "Tenant management not yet implemented"}


@api_router.post("/tenants")
async def create_tenant():
    """
    Create a new tenant.
    
    Returns:
        dict: Created tenant information.
    """
    # TODO: Add authentication and authorization
    # TODO: Implement tenant creation logic
    return {"message": "Tenant creation not yet implemented"}


@api_router.get("/agents")
async def list_agents():
    """
    List agents for the current tenant.
    
    Returns:
        dict: List of agents.
    """
    # TODO: Add authentication and tenant context
    # TODO: Implement agent listing logic
    return {"agents": [], "message": "Agent management not yet implemented"}


@api_router.post("/agents")
async def create_agent():
    """
    Create a new agent.
    
    Returns:
        dict: Created agent information.
    """
    # TODO: Add authentication and tenant context
    # TODO: Implement agent creation logic
    return {"message": "Agent creation not yet implemented"}


@api_router.get("/workflows")
async def list_workflows():
    """
    List workflows for the current tenant.
    
    Returns:
        dict: List of workflows.
    """
    # TODO: Add authentication and tenant context
    # TODO: Implement workflow listing logic
    return {"workflows": [], "message": "Workflow management not yet implemented"}


@api_router.post("/workflows")
async def create_workflow():
    """
    Create a new workflow.
    
    Returns:
        dict: Created workflow information.
    """
    # TODO: Add authentication and tenant context
    # TODO: Implement workflow creation logic
    return {"message": "Workflow creation not yet implemented"}


# Include all API route modules
api_router.include_router(workflow_router)
api_router.include_router(agent_router)
api_router.include_router(langgraph_router)
api_router.include_router(flowise_router)
