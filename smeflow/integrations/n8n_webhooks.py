"""
SMEFlow n8N Webhook Integration.

This module provides webhook endpoints for triggering and managing n8N workflows
with multi-tenant isolation, authentication, and African market optimizations.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from smeflow.auth.jwt_middleware import get_current_user, UserInfo
from smeflow.database.connection import get_db_session
from smeflow.integrations.n8n_wrapper import SMEFlowN8nClient, N8nConfig
from smeflow.core.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/webhooks/n8n", tags=["n8n-webhooks"])

# Pydantic models for request/response
class WorkflowTriggerRequest(BaseModel):
    """Request model for triggering n8N workflows."""
    workflow_id: str = Field(..., description="n8N workflow ID to trigger")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for workflow")
    tenant_context: Optional[Dict[str, Any]] = Field(default=None, description="Tenant-specific context")
    priority: str = Field(default="normal", description="Execution priority (low, normal, high)")
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if v not in ['low', 'normal', 'high']:
            raise ValueError('Priority must be low, normal, or high')
        return v

class WorkflowTriggerResponse(BaseModel):
    """Response model for workflow trigger."""
    execution_id: str = Field(..., description="n8N execution ID")
    workflow_id: str = Field(..., description="n8N workflow ID")
    status: str = Field(..., description="Initial execution status")
    tenant_id: str = Field(..., description="Tenant ID for isolation")
    triggered_at: datetime = Field(..., description="Trigger timestamp")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")

class ExecutionStatusResponse(BaseModel):
    """Response model for execution status."""
    execution_id: str = Field(..., description="n8N execution ID")
    workflow_id: str = Field(..., description="n8N workflow ID")
    status: str = Field(..., description="Current execution status")
    progress: Optional[float] = Field(None, description="Execution progress (0-100)")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: Optional[datetime] = Field(None, description="Execution completion time")
    tenant_id: str = Field(..., description="Tenant ID for isolation")

class TenantWorkflowsResponse(BaseModel):
    """Response model for tenant workflows."""
    tenant_id: str = Field(..., description="Tenant ID")
    workflows: List[Dict[str, Any]] = Field(..., description="List of available workflows")
    total_count: int = Field(..., description="Total number of workflows")
    active_count: int = Field(..., description="Number of active workflows")

# Helper functions
async def get_n8n_client() -> SMEFlowN8nClient:
    """Get configured n8N client."""
    settings = get_settings()
    config = N8nConfig(
        base_url=settings.N8N_BASE_URL or "http://localhost:5678",
        api_key=settings.N8N_API_KEY or "default-api-key",
        timeout=30
    )
    return SMEFlowN8nClient(config=config)

async def validate_tenant_workflow_access(
    tenant_id: str, 
    workflow_id: str, 
    client: SMEFlowN8nClient
) -> bool:
    """Validate that tenant has access to the specified workflow."""
    try:
        # Get workflow details
        workflow = await client.get_workflow(workflow_id)
        
        # Check if workflow belongs to tenant or is public
        workflow_tags = workflow.get('tags', [])
        
        # Allow access if:
        # 1. Workflow has tenant-specific tag
        # 2. Workflow is marked as public/shared
        # 3. Workflow is a system template
        tenant_tag = f"tenant:{tenant_id}"
        public_tags = ["public", "shared", "template", "system"]
        
        has_access = (
            tenant_tag in workflow_tags or
            any(tag in workflow_tags for tag in public_tags) or
            workflow.get('active', False)  # Active workflows are accessible
        )
        
        return has_access
        
    except Exception as e:
        logger.error(f"Error validating workflow access: {str(e)}")
        return False

# Webhook endpoints
@router.post("/workflow/{workflow_id}/trigger", response_model=WorkflowTriggerResponse)
async def trigger_workflow(
    workflow_id: str,
    request: WorkflowTriggerRequest,
    background_tasks: BackgroundTasks,
    user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Trigger n8N workflow with tenant isolation.
    
    This endpoint allows authenticated users to trigger n8N workflows
    with proper tenant isolation and security validation.
    """
    try:
        client = await get_n8n_client()
        tenant_id = user.tenant_id
        
        # Validate tenant access to workflow
        has_access = await validate_tenant_workflow_access(tenant_id, workflow_id, client)
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail=f"Tenant {tenant_id} does not have access to workflow {workflow_id}"
            )
        
        # Prepare execution data with tenant context
        execution_data = {
            **request.input_data,
            "tenant_id": tenant_id,
            "user_id": user.user_id,
            "triggered_by": user.email,
            "tenant_context": request.tenant_context or {},
            "priority": request.priority,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Trigger workflow execution
        execution = await client.trigger_workflow(workflow_id, execution_data)
        execution_id = execution.get('id') or str(uuid4())
        
        # Log the trigger event
        logger.info(
            f"Workflow triggered - Tenant: {tenant_id}, Workflow: {workflow_id}, "
            f"Execution: {execution_id}, User: {user.email}"
        )
        
        # Schedule background monitoring (optional)
        background_tasks.add_task(
            monitor_execution_progress,
            execution_id,
            workflow_id,
            tenant_id
        )
        
        return WorkflowTriggerResponse(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=execution.get('status', 'running'),
            tenant_id=tenant_id,
            triggered_at=datetime.utcnow(),
            estimated_completion=None  # Could be calculated based on workflow complexity
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering workflow {workflow_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger workflow: {str(e)}"
        )

@router.get("/execution/{execution_id}/status", response_model=ExecutionStatusResponse)
async def get_execution_status(
    execution_id: str,
    user: UserInfo = Depends(get_current_user)
):
    """
    Get n8N workflow execution status with tenant validation.
    
    Returns the current status and results of a workflow execution,
    ensuring the user has access to the execution data.
    """
    try:
        client = await get_n8n_client()
        tenant_id = user.tenant_id
        
        # Get execution details
        execution = await client.get_execution(execution_id)
        
        # Validate tenant access to execution
        execution_tenant = execution.get('data', {}).get('tenant_id')
        if execution_tenant != tenant_id:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to execution {execution_id}"
            )
        
        # Extract execution information
        status = execution.get('status', 'unknown')
        started_at = execution.get('startedAt')
        finished_at = execution.get('finishedAt')
        
        # Parse timestamps
        started_at_dt = datetime.fromisoformat(started_at.replace('Z', '+00:00')) if started_at else datetime.utcnow()
        completed_at_dt = datetime.fromisoformat(finished_at.replace('Z', '+00:00')) if finished_at else None
        
        # Calculate progress (simplified)
        progress = None
        if status == 'success':
            progress = 100.0
        elif status == 'running':
            # Estimate progress based on elapsed time (simplified)
            elapsed = (datetime.utcnow() - started_at_dt).total_seconds()
            progress = min(elapsed / 60.0 * 10, 90.0)  # Rough estimate
        elif status == 'error':
            progress = 0.0
        
        return ExecutionStatusResponse(
            execution_id=execution_id,
            workflow_id=execution.get('workflowId', ''),
            status=status,
            progress=progress,
            result=execution.get('data', {}).get('resultData') if status == 'success' else None,
            error=execution.get('data', {}).get('error') if status == 'error' else None,
            started_at=started_at_dt,
            completed_at=completed_at_dt,
            tenant_id=tenant_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution status {execution_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get execution status: {str(e)}"
        )

@router.get("/tenant/{tenant_id}/workflows", response_model=TenantWorkflowsResponse)
async def list_tenant_workflows(
    tenant_id: str,
    user: UserInfo = Depends(get_current_user),
    active_only: bool = False
):
    """
    List workflows available to a specific tenant.
    
    Returns all workflows that the tenant has access to,
    including tenant-specific and public workflows.
    """
    try:
        # Validate tenant access
        if user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to tenant {tenant_id} workflows"
            )
        
        client = await get_n8n_client()
        
        # Get all workflows
        all_workflows = await client.get_workflows()
        
        # Filter workflows for tenant
        tenant_workflows = []
        tenant_tag = f"tenant:{tenant_id}"
        public_tags = ["public", "shared", "template", "system"]
        
        for workflow in all_workflows:
            workflow_tags = workflow.get('tags', [])
            is_active = workflow.get('active', False)
            
            # Check access criteria
            has_access = (
                tenant_tag in workflow_tags or
                any(tag in workflow_tags for tag in public_tags)
            )
            
            # Apply active filter if requested
            if active_only and not is_active:
                has_access = False
            
            if has_access:
                # Add tenant-specific metadata
                workflow_info = {
                    "id": workflow.get('id'),
                    "name": workflow.get('name'),
                    "active": is_active,
                    "tags": workflow_tags,
                    "created_at": workflow.get('createdAt'),
                    "updated_at": workflow.get('updatedAt'),
                    "description": workflow.get('description', ''),
                    "is_tenant_specific": tenant_tag in workflow_tags,
                    "is_public": any(tag in workflow_tags for tag in public_tags)
                }
                tenant_workflows.append(workflow_info)
        
        # Count active workflows
        active_count = sum(1 for w in tenant_workflows if w['active'])
        
        return TenantWorkflowsResponse(
            tenant_id=tenant_id,
            workflows=tenant_workflows,
            total_count=len(tenant_workflows),
            active_count=active_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing workflows for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list tenant workflows: {str(e)}"
        )

@router.get("/health")
async def webhook_health_check():
    """
    Health check endpoint for n8N webhook system.
    
    Returns the health status of the n8N integration and webhook system.
    """
    try:
        client = await get_n8n_client()
        health_status = await client.health_check()
        
        return {
            "status": "healthy",
            "n8n_status": health_status.get('status', 'unknown'),
            "webhook_system": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Webhook health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "webhook_system": "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }

# Background task functions
async def monitor_execution_progress(
    execution_id: str,
    workflow_id: str,
    tenant_id: str
):
    """
    Background task to monitor workflow execution progress.
    
    This function runs in the background to track execution progress
    and can send notifications or updates as needed.
    """
    try:
        client = await get_n8n_client()
        
        # Monitor execution for up to 10 minutes
        max_wait_time = 600  # 10 minutes
        check_interval = 30   # 30 seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            try:
                execution = await client.get_execution(execution_id)
                status = execution.get('status', 'unknown')
                
                # Log progress
                logger.info(
                    f"Execution progress - ID: {execution_id}, Status: {status}, "
                    f"Tenant: {tenant_id}, Elapsed: {elapsed_time}s"
                )
                
                # Check if execution is complete
                if status in ['success', 'error', 'canceled']:
                    logger.info(f"Execution {execution_id} completed with status: {status}")
                    break
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                elapsed_time += check_interval
                
            except Exception as e:
                logger.error(f"Error monitoring execution {execution_id}: {str(e)}")
                break
        
        if elapsed_time >= max_wait_time:
            logger.warning(f"Execution {execution_id} monitoring timeout after {max_wait_time}s")
            
    except Exception as e:
        logger.error(f"Background monitoring failed for execution {execution_id}: {str(e)}")
