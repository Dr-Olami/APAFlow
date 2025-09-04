"""
LangGraph Workflow API Routes for SMEFlow.

This module provides REST API endpoints for managing LangGraph workflows
with multi-tenant isolation and stateful execution.
"""

from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.jwt_middleware import get_current_user, UserInfo
from ..workflows.manager import WorkflowManager
from ..workflows.state import WorkflowState
from ..workflows.templates import IndustryType, FormField
from ..workflows.template_versioning import TemplateVersionManager, TemplateVersionCreate, TemplateVersionInfo
from ..core.database import get_db_session

router = APIRouter(prefix="/langgraph", tags=["langgraph-workflows"])


class WorkflowCreateRequest(BaseModel):
    """Request model for creating LangGraph workflow."""
    
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    template_type: Optional[str] = Field(None, description="Template type (booking_funnel, marketing_campaign, etc.)")
    definition: Optional[Dict[str, Any]] = Field(None, description="Custom workflow definition")


class WorkflowUpdateRequest(BaseModel):
    """Request model for updating workflow."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    definition: Optional[Dict[str, Any]] = None


class WorkflowExecuteRequest(BaseModel):
    """Request model for executing workflow."""
    
    input_data: Dict[str, Any] = Field(..., description="Input data for workflow")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context data")


class WorkflowResponse(BaseModel):
    """Response model for workflow operations."""
    
    id: str
    name: str
    description: Optional[str]
    template_type: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str


class WorkflowExecutionResponse(BaseModel):
    """Response model for workflow execution."""
    
    execution_id: str
    workflow_id: str
    status: str
    started_at: str
    completed_at: Optional[str]
    duration_ms: Optional[int]
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]


@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowCreateRequest,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Create a new LangGraph workflow.
    
    Args:
        request: Workflow creation request
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Created workflow data
    """
    try:
        manager = WorkflowManager(user_info.tenant_id, db_session)
        
        workflow = await manager.create_workflow(
            name=request.name,
            description=request.description,
            template_type=request.template_type,
            definition=request.definition
        )
        
        return WorkflowResponse(
            id=str(workflow.id),
            name=workflow.name,
            description=workflow.description,
            template_type=workflow.template_type,
            is_active=workflow.is_active,
            created_at=workflow.created_at.isoformat(),
            updated_at=workflow.updated_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get("/workflows", response_model=List[WorkflowResponse])
async def list_workflows(
    active_only: bool = True,
    template_type: Optional[str] = None,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    List workflows for current tenant.
    
    Args:
        active_only: Only return active workflows
        template_type: Filter by template type
        user_info: Current user information
        db_session: Database session
        
    Returns:
        List of tenant workflows
    """
    try:
        manager = WorkflowManager(user_info.tenant_id, db_session)
        
        workflows = await manager.list_workflows(
            active_only=active_only,
            template_type=template_type
        )
        
        return [
            WorkflowResponse(
                id=str(workflow.id),
                name=workflow.name,
                description=workflow.description,
                template_type=workflow.template_type,
                is_active=workflow.is_active,
                created_at=workflow.created_at.isoformat(),
                updated_at=workflow.updated_at.isoformat()
            )
            for workflow in workflows
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflows: {str(e)}"
        )


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Get workflow by ID.
    
    Args:
        workflow_id: Workflow ID
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Workflow data
    """
    try:
        manager = WorkflowManager(user_info.tenant_id, db_session)
        
        workflow = await manager.get_workflow(uuid.UUID(workflow_id))
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        return WorkflowResponse(
            id=str(workflow.id),
            name=workflow.name,
            description=workflow.description,
            template_type=workflow.template_type,
            is_active=workflow.is_active,
            created_at=workflow.created_at.isoformat(),
            updated_at=workflow.updated_at.isoformat()
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow: {str(e)}"
        )


@router.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    request: WorkflowUpdateRequest,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Update workflow.
    
    Args:
        workflow_id: Workflow ID
        request: Update request
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Updated workflow data
    """
    try:
        manager = WorkflowManager(user_info.tenant_id, db_session)
        
        # Filter out None values
        updates = {k: v for k, v in request.dict().items() if v is not None}
        
        workflow = await manager.update_workflow(uuid.UUID(workflow_id), **updates)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        return WorkflowResponse(
            id=str(workflow.id),
            name=workflow.name,
            description=workflow.description,
            template_type=workflow.template_type,
            is_active=workflow.is_active,
            created_at=workflow.created_at.isoformat(),
            updated_at=workflow.updated_at.isoformat()
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update workflow: {str(e)}"
        )


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Delete workflow.
    
    Args:
        workflow_id: Workflow ID
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Success message
    """
    try:
        manager = WorkflowManager(user_info.tenant_id, db_session)
        
        success = await manager.delete_workflow(uuid.UUID(workflow_id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        return {"message": "Workflow deleted successfully"}
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete workflow: {str(e)}"
        )


@router.post("/workflows/{workflow_id}/execute", response_model=Dict[str, Any])
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Execute a workflow.
    
    Args:
        workflow_id: Workflow ID to execute
        request: Execution request with input data
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Execution result data
    """
    try:
        manager = WorkflowManager(user_info.tenant_id, db_session)
        
        final_state = await manager.execute_workflow(
            workflow_id=uuid.UUID(workflow_id),
            input_data=request.input_data,
            context=request.context
        )
        
        return {
            "execution_id": str(final_state.execution_id),
            "workflow_id": str(final_state.workflow_id),
            "status": final_state.status,
            "started_at": final_state.started_at.isoformat(),
            "completed_at": final_state.completed_at.isoformat() if final_state.completed_at else None,
            "duration_ms": final_state.get_duration_ms(),
            "output_data": final_state.data,
            "errors": final_state.errors,
            "total_cost_usd": final_state.total_cost_usd,
            "tokens_used": final_state.tokens_used
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute workflow: {str(e)}"
        )


@router.get("/workflows/{workflow_id}/executions", response_model=List[WorkflowExecutionResponse])
async def get_workflow_executions(
    workflow_id: str,
    limit: int = 50,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Get execution history for a workflow.
    
    Args:
        workflow_id: Workflow ID
        limit: Maximum number of executions to return
        user_info: Current user information
        db_session: Database session
        
    Returns:
        List of workflow executions
    """
    try:
        manager = WorkflowManager(user_info.tenant_id, db_session)
        
        executions = await manager.get_workflow_executions(
            workflow_id=uuid.UUID(workflow_id),
            limit=limit
        )
        
        return [
            WorkflowExecutionResponse(
                execution_id=str(execution.id),
                workflow_id=str(execution.workflow_id),
                status=execution.status,
                started_at=execution.started_at.isoformat(),
                completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
                duration_ms=execution.duration_ms,
                input_data=execution.input_data,
                output_data=execution.output_data,
                error_message=execution.error_message
            )
            for execution in executions
        ]
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workflow ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow executions: {str(e)}"
        )


# Template endpoints
@router.post("/templates/booking-funnel", response_model=WorkflowResponse)
async def create_booking_funnel_workflow(
    name: str = "Booking Funnel",
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Create a pre-built booking funnel workflow.
    
    Args:
        name: Workflow name
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Created workflow data
    """
    try:
        manager = WorkflowManager(user_info.tenant_id, db_session)
        
        workflow = await manager.create_booking_funnel_workflow(name=name)
        
        return WorkflowResponse(
            id=str(workflow.id),
            name=workflow.name,
            description=workflow.description,
            template_type=workflow.template_type,
            is_active=workflow.is_active,
            created_at=workflow.created_at.isoformat(),
            updated_at=workflow.updated_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create booking funnel workflow: {str(e)}"
        )


@router.post("/templates/marketing-campaign", response_model=WorkflowResponse)
async def create_marketing_campaign_workflow(
    name: str = "Marketing Campaign",
    region: str = "NG",
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Create a pre-built marketing campaign workflow.
    
    Args:
        name: Workflow name
        region: Target region (NG, KE, ZA, etc.)
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Created workflow data
    """
    try:
        manager = WorkflowManager(user_info.tenant_id, db_session)
        
        workflow = await manager.create_marketing_campaign_workflow(
            name=name,
            region=region
        )
        
        return WorkflowResponse(
            id=str(workflow.id),
            name=workflow.name,
            description=workflow.description,
            template_type=workflow.template_type,
            is_active=workflow.is_active,
            created_at=workflow.created_at.isoformat(),
            updated_at=workflow.updated_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create marketing campaign workflow: {str(e)}"
        )


# Industry template endpoints
@router.get("/templates/industries", response_model=List[Dict[str, Any]])
async def get_industry_templates(
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Get all available industry workflow templates.
    
    Args:
        user_info: Current user information
        db_session: Database session
        
    Returns:
        List of available industry templates
    """
    try:
        manager = WorkflowManager(user_info.tenant_id, db_session)
        templates = await manager.get_industry_templates()
        return templates
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get industry templates: {str(e)}"
        )


@router.get("/templates/industries/{industry}/form", response_model=Dict[str, Any])
async def get_industry_template_form(
    industry: str,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Get form configuration for a specific industry template.
    
    Args:
        industry: Industry type (consulting, salon_spa, healthcare, manufacturing)
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Form configuration with fields and validation rules
    """
    try:
        # Validate industry type
        try:
            industry_type = IndustryType(industry)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid industry type: {industry}"
            )
        
        manager = WorkflowManager(user_info.tenant_id, db_session)
        form_config = await manager.get_industry_template_form(industry_type)
        return form_config
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get industry template form: {str(e)}"
        )


class IndustryWorkflowCreateRequest(BaseModel):
    """Request model for creating industry-specific workflow."""
    
    industry: str = Field(..., description="Industry type")
    name: Optional[str] = Field(None, description="Custom workflow name")
    custom_fields: Optional[List[Dict[str, Any]]] = Field(None, description="Additional form fields")
    custom_business_rules: Optional[Dict[str, Any]] = Field(None, description="Custom business rules")


@router.post("/templates/industries/create", response_model=WorkflowResponse)
async def create_industry_workflow(
    request: IndustryWorkflowCreateRequest,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Create a workflow from industry-specific template.
    
    Args:
        request: Industry workflow creation request
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Created workflow data
    """
    try:
        # Validate industry type
        try:
            industry_type = IndustryType(request.industry)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid industry type: {request.industry}"
            )
        
        manager = WorkflowManager(user_info.tenant_id, db_session)
        
        # Convert custom fields if provided
        custom_fields = None
        if request.custom_fields:
            custom_fields = []
            for field_data in request.custom_fields:
                try:
                    field = FormField(**field_data)
                    custom_fields.append(field)
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid custom field: {str(e)}"
                    )
        
        workflow = await manager.create_industry_workflow(
            industry=industry_type,
            name=request.name,
            custom_fields=custom_fields,
            custom_business_rules=request.custom_business_rules
        )
        
        return WorkflowResponse(
            id=str(workflow.id),
            name=workflow.name,
            description=workflow.description,
            template_type=workflow.template_type,
            is_active=workflow.is_active,
            created_at=workflow.created_at.isoformat(),
            updated_at=workflow.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create industry workflow: {str(e)}"
        )


# Specific industry template shortcuts
@router.post("/templates/consulting", response_model=WorkflowResponse)
async def create_consulting_workflow(
    name: str = "Professional Consulting Booking",
    custom_business_rules: Optional[Dict[str, Any]] = None,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Create a consulting industry workflow.
    
    Args:
        name: Workflow name
        custom_business_rules: Custom business rules
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Created workflow data
    """
    try:
        manager = WorkflowManager(user_info.tenant_id, db_session)
        
        workflow = await manager.create_industry_workflow(
            industry=IndustryType.CONSULTING,
            name=name,
            custom_business_rules=custom_business_rules
        )
        
        return WorkflowResponse(
            id=str(workflow.id),
            name=workflow.name,
            description=workflow.description,
            template_type=workflow.template_type,
            is_active=workflow.is_active,
            created_at=workflow.created_at.isoformat(),
            updated_at=workflow.updated_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create consulting workflow: {str(e)}"
        )


@router.post("/templates/salon-spa", response_model=WorkflowResponse)
async def create_salon_spa_workflow(
    name: str = "Salon & Spa Booking",
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Create a salon/spa industry workflow.
    
    Args:
        name: Workflow name
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Created workflow data
    """
    try:
        manager = WorkflowManager(user_info.tenant_id, db_session)
        
        workflow = await manager.create_industry_workflow(
            industry=IndustryType.SALON_SPA,
            name=name
        )
        
        return WorkflowResponse(
            id=str(workflow.id),
            name=workflow.name,
            description=workflow.description,
            template_type=workflow.template_type,
            is_active=workflow.is_active,
            created_at=workflow.created_at.isoformat(),
            updated_at=workflow.updated_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create salon/spa workflow: {str(e)}"
        )


@router.post("/templates/healthcare", response_model=WorkflowResponse)
async def create_healthcare_workflow(
    name: str = "Healthcare Appointment Booking",
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Create a healthcare industry workflow.
    
    Args:
        name: Workflow name
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Created workflow data
    """
    try:
        manager = WorkflowManager(user_info.tenant_id, db_session)
        
        workflow = await manager.create_industry_workflow(
            industry=IndustryType.HEALTHCARE,
            name=name
        )
        
        return WorkflowResponse(
            id=str(workflow.id),
            name=workflow.name,
            description=workflow.description,
            template_type=workflow.template_type,
            is_active=workflow.is_active,
            created_at=workflow.created_at.isoformat(),
            updated_at=workflow.updated_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create healthcare workflow: {str(e)}"
        )


@router.post("/templates/manufacturing", response_model=WorkflowResponse)
async def create_manufacturing_workflow(
    name: str = "Manufacturing Resource Booking",
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Create a manufacturing industry workflow.
    
    Args:
        name: Workflow name
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Created workflow data
    """
    try:
        manager = WorkflowManager(user_info.tenant_id, db_session)
        
        workflow = await manager.create_industry_workflow(
            industry=IndustryType.MANUFACTURING,
            name=name
        )
        
        return WorkflowResponse(
            id=str(workflow.id),
            name=workflow.name,
            description=workflow.description,
            template_type=workflow.template_type,
            is_active=workflow.is_active,
            created_at=workflow.created_at.isoformat(),
            updated_at=workflow.updated_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create manufacturing workflow: {str(e)}"
        )


@router.post("/templates/product-recommender", response_model=WorkflowResponse)
async def create_product_recommender_workflow(
    name: str = "AI Product Recommender System",
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Create a product recommender industry workflow for e-commerce/retail SMEs.
    
    Args:
        name: Workflow name
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Created workflow data
    """
    try:
        manager = WorkflowManager(user_info.tenant_id, db_session)
        
        workflow = await manager.create_industry_workflow(
            industry=IndustryType.PRODUCT_RECOMMENDER,
            name=name
        )
        
        return WorkflowResponse(
            id=str(workflow.id),
            name=workflow.name,
            description=workflow.description,
            template_type=workflow.template_type,
            is_active=workflow.is_active,
            created_at=workflow.created_at.isoformat(),
            updated_at=workflow.updated_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product recommender workflow: {str(e)}"
        )


# Template versioning endpoints
@router.get("/templates/{industry}/versions", response_model=List[TemplateVersionInfo])
async def get_template_versions(
    industry: str,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Get version history for a template.
    
    Args:
        industry: Industry type
        user_info: Current user information
        db_session: Database session
        
    Returns:
        List of template versions
    """
    try:
        # Validate industry type
        try:
            industry_type = IndustryType(industry)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid industry type: {industry}"
            )
        
        version_manager = TemplateVersionManager(db_session)
        versions = await version_manager.get_version_history(industry_type)
        
        return versions
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template versions: {str(e)}"
        )


@router.get("/templates/{industry}/versions/current", response_model=Optional[TemplateVersionInfo])
async def get_current_template_version(
    industry: str,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Get current version of a template.
    
    Args:
        industry: Industry type
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Current template version or None
    """
    try:
        # Validate industry type
        try:
            industry_type = IndustryType(industry)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid industry type: {industry}"
            )
        
        version_manager = TemplateVersionManager(db_session)
        current_version = await version_manager.get_current_version(industry_type)
        
        if not current_version:
            return None
            
        return TemplateVersionInfo(
            id=current_version.id,
            template_id=current_version.template_id,
            version=current_version.version,
            is_current=current_version.is_current,
            is_deprecated=current_version.is_deprecated,
            created_at=current_version.created_at,
            changelog=current_version.changelog,
            breaking_changes=current_version.breaking_changes,
            migration_notes=current_version.migration_notes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current template version: {str(e)}"
        )


@router.post("/templates/{industry}/versions", response_model=TemplateVersionInfo)
async def create_template_version(
    industry: str,
    version_data: TemplateVersionCreate,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Create a new version of a template.
    
    Args:
        industry: Industry type
        version_data: Version creation data
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Created template version
    """
    try:
        # Validate industry type
        try:
            industry_type = IndustryType(industry)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid industry type: {industry}"
            )
        
        version_manager = TemplateVersionManager(db_session)
        new_version = await version_manager.create_new_version(industry_type, version_data)
        
        return TemplateVersionInfo(
            id=new_version.id,
            template_id=new_version.template_id,
            version=new_version.version,
            is_current=new_version.is_current,
            is_deprecated=new_version.is_deprecated,
            created_at=new_version.created_at,
            changelog=new_version.changelog,
            breaking_changes=new_version.breaking_changes,
            migration_notes=new_version.migration_notes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template version: {str(e)}"
        )


@router.put("/templates/{industry}/versions/{version}/deprecate")
async def deprecate_template_version(
    industry: str,
    version: str,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Mark a template version as deprecated.
    
    Args:
        industry: Industry type
        version: Version string to deprecate
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Success message
    """
    try:
        # Validate industry type
        try:
            industry_type = IndustryType(industry)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid industry type: {industry}"
            )
        
        version_manager = TemplateVersionManager(db_session)
        success = await version_manager.deprecate_version(industry_type, version)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version} not found for industry {industry}"
            )
        
        return {"message": f"Version {version} deprecated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deprecate template version: {str(e)}"
        )


@router.get("/templates/{industry}/definition")
async def get_template_definition(
    industry: str,
    version: Optional[str] = None,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Get template definition for specific version or current.
    
    Args:
        industry: Industry type
        version: Specific version, or None for current
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Template definition
    """
    try:
        # Validate industry type
        try:
            industry_type = IndustryType(industry)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid industry type: {industry}"
            )
        
        version_manager = TemplateVersionManager(db_session)
        definition = await version_manager.get_template_definition(industry_type, version)
        
        if not definition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template definition not found for industry {industry}" + 
                       (f" version {version}" if version else "")
            )
        
        return definition
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template definition: {str(e)}"
        )
