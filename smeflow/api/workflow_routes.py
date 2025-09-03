"""
N8n Workflow Management API Routes for SMEFlow.

This module provides REST API endpoints for managing n8n workflows with
multi-tenant isolation and SME-specific templates.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..auth.jwt_middleware import get_current_user, UserInfo
from ..integrations.n8n_wrapper import SMEFlowN8nClient
from ..core.config import get_settings

router = APIRouter(prefix="/workflows", tags=["workflows"])


class WorkflowCreateRequest(BaseModel):
    """Request model for creating workflow from template."""
    
    template_id: str = Field(..., description="Template ID to use")
    custom_settings: Optional[Dict[str, Any]] = Field(default=None, description="Custom workflow settings")


class WorkflowExecuteRequest(BaseModel):
    """Request model for executing workflow."""
    
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="Input data for workflow")


class WorkflowResponse(BaseModel):
    """Response model for workflow operations."""
    
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


# Initialize N8n client
n8n_client = SMEFlowN8nClient()


@router.get("/templates", response_model=List[Dict[str, Any]])
async def get_workflow_templates():
    """
    Get available SME workflow templates.
    
    Returns:
        List of available workflow templates
    """
    return n8n_client.get_available_templates()


@router.post("/create", response_model=WorkflowResponse)
async def create_workflow_from_template(
    request: WorkflowCreateRequest,
    user_info: UserInfo = Depends(get_current_user)
):
    """
    Create a new workflow from SME template.
    
    Args:
        request: Workflow creation request
        user_info: Current user information
        
    Returns:
        Created workflow data
    """
    try:
        workflow_data = await n8n_client.create_workflow_from_template(
            template_id=request.template_id,
            tenant_id=user_info.tenant_id,
            user_info=user_info,
            custom_settings=request.custom_settings
        )
        
        return WorkflowResponse(
            success=True,
            data=workflow_data,
            message=f"Workflow created from template '{request.template_id}'"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get("/list", response_model=List[Dict[str, Any]])
async def list_tenant_workflows(
    active_only: bool = False,
    user_info: UserInfo = Depends(get_current_user)
):
    """
    List workflows for current tenant.
    
    Args:
        active_only: Only return active workflows
        user_info: Current user information
        
    Returns:
        List of tenant workflows
    """
    try:
        workflows = await n8n_client.list_tenant_workflows(
            tenant_id=user_info.tenant_id,
            user_info=user_info,
            active_only=active_only
        )
        
        return workflows
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflows: {str(e)}"
        )


@router.post("/{workflow_id}/execute", response_model=WorkflowResponse)
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    user_info: UserInfo = Depends(get_current_user)
):
    """
    Execute a workflow.
    
    Args:
        workflow_id: Workflow ID to execute
        request: Execution request with input data
        user_info: Current user information
        
    Returns:
        Execution result data
    """
    try:
        execution_data = await n8n_client.execute_workflow(
            workflow_id=workflow_id,
            tenant_id=user_info.tenant_id,
            user_info=user_info,
            input_data=request.input_data
        )
        
        return WorkflowResponse(
            success=True,
            data=execution_data,
            message=f"Workflow {workflow_id} executed successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute workflow: {str(e)}"
        )


@router.post("/{workflow_id}/activate", response_model=WorkflowResponse)
async def activate_workflow(
    workflow_id: str,
    user_info: UserInfo = Depends(get_current_user)
):
    """
    Activate a workflow for production use.
    
    Args:
        workflow_id: Workflow ID to activate
        user_info: Current user information
        
    Returns:
        Updated workflow data
    """
    try:
        workflow_data = await n8n_client.activate_workflow(
            workflow_id=workflow_id,
            tenant_id=user_info.tenant_id,
            user_info=user_info
        )
        
        return WorkflowResponse(
            success=True,
            data=workflow_data,
            message=f"Workflow {workflow_id} activated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate workflow: {str(e)}"
        )


@router.get("/{workflow_id}/executions", response_model=List[Dict[str, Any]])
async def get_workflow_executions(
    workflow_id: str,
    limit: int = 50,
    user_info: UserInfo = Depends(get_current_user)
):
    """
    Get execution history for a workflow.
    
    Args:
        workflow_id: Workflow ID
        limit: Maximum number of executions to return
        user_info: Current user information
        
    Returns:
        List of workflow executions
    """
    try:
        executions = await n8n_client.get_workflow_executions(
            workflow_id=workflow_id,
            tenant_id=user_info.tenant_id,
            user_info=user_info,
            limit=limit
        )
        
        return executions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow executions: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, Any])
async def n8n_health_check():
    """
    Perform health check on N8n integration.
    
    Returns:
        Health status information
    """
    return await n8n_client.health_check()
