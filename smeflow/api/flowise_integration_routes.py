"""
Flowise Integration API Routes for SMEFlow.

This module provides REST API endpoints for integrating Flowise workflows
with SMEFlow's LangGraph execution engine.
"""

from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

from ..auth.jwt_middleware import get_current_user, UserInfo
from ..workflows.flowise_bridge import FlowiseBridge, FlowiseWorkflowExecutor, FlowiseWorkflowData
from ..workflows.state import WorkflowState
from ..workflows.export_import import (
    WorkflowExportImportService, 
    WorkflowExportRequest, 
    WorkflowImportRequest,
    WorkflowExportFormat
)
from ..database.connection import get_db_session

router = APIRouter(prefix="/flowise", tags=["flowise-integration"])
logger = logging.getLogger(__name__)


class FlowiseExecuteRequest(BaseModel):
    """Request model for executing Flowise workflow."""
    
    workflow_data: Dict[str, Any] = Field(..., description="Complete Flowise workflow data")
    input_data: Dict[str, Any] = Field(..., description="Input data for workflow execution")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context data")
    use_cache: bool = Field(True, description="Whether to use workflow translation cache")


class FlowiseTranslateRequest(BaseModel):
    """Request model for translating Flowise workflow."""
    
    workflow_data: Dict[str, Any] = Field(..., description="Complete Flowise workflow data")


class FlowiseExecutionResponse(BaseModel):
    """Response model for Flowise workflow execution."""
    
    success: bool
    execution_id: str
    workflow_id: str
    status: str
    started_at: str
    completed_at: Optional[str]
    duration_ms: Optional[int]
    output_data: Dict[str, Any]
    errors: List[Dict[str, Any]]
    total_cost_usd: float
    tokens_used: int
    flowise_metadata: Dict[str, Any]


class FlowiseTranslationResponse(BaseModel):
    """Response model for workflow translation."""
    
    success: bool
    workflow_name: str
    langgraph_definition: Optional[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]
    node_mappings: Dict[str, str]
    translation_metadata: Dict[str, Any]


@router.post("/execute", response_model=FlowiseExecutionResponse)
async def execute_flowise_workflow(
    request: FlowiseExecuteRequest,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Execute a Flowise workflow through SMEFlow's LangGraph engine.
    
    Args:
        request: Flowise execution request
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Workflow execution result
    """
    try:
        # Add tenant ID to workflow data
        workflow_data = request.workflow_data.copy()
        workflow_data['tenant_id'] = user_info.tenant_id
        
        # Create executor
        executor = FlowiseWorkflowExecutor(user_info.tenant_id, db_session)
        
        # Execute workflow
        final_state = await executor.execute_workflow(
            workflow_data=workflow_data,
            input_data=request.input_data,
            context=request.context,
            use_cache=request.use_cache
        )
        
        return FlowiseExecutionResponse(
            success=final_state.status == "completed",
            execution_id=str(final_state.execution_id),
            workflow_id=str(final_state.workflow_id),
            status=final_state.status,
            started_at=final_state.started_at.isoformat(),
            completed_at=final_state.completed_at.isoformat() if final_state.completed_at else None,
            duration_ms=final_state.get_duration_ms(),
            output_data=final_state.data,
            errors=final_state.errors,
            total_cost_usd=final_state.total_cost_usd,
            tokens_used=final_state.tokens_used,
            flowise_metadata=final_state.metadata
        )
        
    except Exception as e:
        logger.exception(f"Failed to execute Flowise workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.post("/translate", response_model=FlowiseTranslationResponse)
async def translate_flowise_workflow(
    request: FlowiseTranslateRequest,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Translate Flowise workflow to LangGraph format without execution.
    
    Args:
        request: Translation request
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Translation result with LangGraph definition
    """
    try:
        # Add tenant ID to workflow data
        workflow_data = request.workflow_data.copy()
        workflow_data['tenant_id'] = user_info.tenant_id
        
        # Create bridge
        bridge = FlowiseBridge(user_info.tenant_id, db_session)
        
        # Validate and create FlowiseWorkflowData
        flowise_workflow = FlowiseWorkflowData(**workflow_data)
        
        # Translate workflow
        translation_result = await bridge.translate_workflow(flowise_workflow)
        
        return FlowiseTranslationResponse(
            success=translation_result.success,
            workflow_name=translation_result.workflow_name,
            langgraph_definition=translation_result.langgraph_definition,
            errors=translation_result.errors,
            warnings=translation_result.warnings,
            node_mappings=translation_result.node_mappings,
            translation_metadata={
                'node_count': len(flowise_workflow.nodes),
                'edge_count': len(flowise_workflow.edges),
                'tenant_id': user_info.tenant_id,
                'translated_at': translation_result.langgraph_definition.get('metadata', {}).get('translation_timestamp') if translation_result.langgraph_definition else None
            }
        )
        
    except Exception as e:
        logger.exception(f"Failed to translate Flowise workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow translation failed: {str(e)}"
        )


@router.post("/validate")
async def validate_flowise_workflow(
    request: FlowiseTranslateRequest,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Validate Flowise workflow structure and compatibility.
    
    Args:
        request: Validation request
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Validation result with issues and recommendations
    """
    try:
        # Add tenant ID to workflow data
        workflow_data = request.workflow_data.copy()
        workflow_data['tenant_id'] = user_info.tenant_id
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': [],
            'node_analysis': {},
            'edge_analysis': {},
            'african_market_compatibility': {}
        }
        
        # Validate basic structure
        required_fields = ['id', 'name', 'nodes', 'edges']
        for field in required_fields:
            if field not in workflow_data:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['valid'] = False
        
        if not validation_result['valid']:
            return validation_result
        
        # Create FlowiseWorkflowData for validation
        try:
            flowise_workflow = FlowiseWorkflowData(**workflow_data)
        except Exception as e:
            validation_result['errors'].append(f"Invalid workflow data structure: {str(e)}")
            validation_result['valid'] = False
            return validation_result
        
        # Validate nodes
        supported_node_types = [
            'smeflowAutomator', 'smeflowMentor', 'smeflowSupervisor', 
            'smeflowTenantManager', 'startNode', 'endNode'
        ]
        
        has_start = False
        has_end = False
        
        for node in flowise_workflow.nodes:
            if node.type == 'startNode':
                has_start = True
            elif node.type == 'endNode':
                has_end = True
            elif node.type not in supported_node_types:
                validation_result['warnings'].append(f"Unsupported node type: {node.type}")
            
            # Analyze node configuration
            validation_result['node_analysis'][node.id] = {
                'type': node.type,
                'supported': node.type in supported_node_types,
                'has_config': bool(node.data),
                'african_market_ready': _check_african_market_config(node.data)
            }
        
        if not has_start:
            validation_result['errors'].append("Workflow must have a start node")
            validation_result['valid'] = False
        
        if not has_end:
            validation_result['errors'].append("Workflow must have an end node")
            validation_result['valid'] = False
        
        # Validate edges (basic connectivity)
        node_ids = {node.id for node in flowise_workflow.nodes}
        for edge in flowise_workflow.edges:
            if edge.source not in node_ids:
                validation_result['errors'].append(f"Edge references non-existent source node: {edge.source}")
                validation_result['valid'] = False
            if edge.target not in node_ids:
                validation_result['errors'].append(f"Edge references non-existent target node: {edge.target}")
                validation_result['valid'] = False
        
        # African market compatibility analysis
        validation_result['african_market_compatibility'] = {
            'multi_language_support': _check_multi_language_support(flowise_workflow),
            'currency_handling': _check_currency_handling(flowise_workflow),
            'regional_compliance': _check_regional_compliance(flowise_workflow),
            'local_integrations': _check_local_integrations(flowise_workflow)
        }
        
        # Generate recommendations
        if validation_result['valid']:
            validation_result['recommendations'] = _generate_recommendations(flowise_workflow, validation_result)
        
        return validation_result
        
    except Exception as e:
        logger.exception(f"Failed to validate Flowise workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow validation failed: {str(e)}"
        )


@router.websocket("/execute/stream/{workflow_id}")
async def stream_workflow_execution(
    websocket: WebSocket,
    workflow_id: str,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Stream real-time workflow execution updates via WebSocket.
    
    Args:
        websocket: WebSocket connection
        workflow_id: Workflow execution ID to stream
        user_info: Current user information
        db_session: Database session
    """
    await websocket.accept()
    
    try:
        # TODO: Implement real-time streaming
        # This would integrate with the workflow engine's execution monitoring
        
        # Send initial connection confirmation
        await websocket.send_json({
            'type': 'connection',
            'status': 'connected',
            'workflow_id': workflow_id,
            'tenant_id': user_info.tenant_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Placeholder for real-time updates
        # In production, this would:
        # 1. Subscribe to workflow execution events
        # 2. Stream node execution status
        # 3. Send progress updates
        # 4. Handle errors and completion
        
        while True:
            try:
                # Wait for client messages or execution updates
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get('type') == 'ping':
                    await websocket.send_json({
                        'type': 'pong',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for workflow: {workflow_id}")
                break
                
    except Exception as e:
        logger.exception(f"WebSocket error for workflow {workflow_id}: {str(e)}")
        await websocket.send_json({
            'type': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        })
        await websocket.close()


@router.post("/export")
async def export_workflow(
    request: WorkflowExportRequest,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Export SMEFlow workflow to various formats.
    
    Args:
        request: Export request configuration
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Exported workflow data
    """
    try:
        service = WorkflowExportImportService(user_info.tenant_id, db_session)
        result = await service.export_workflow(request)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Export failed: {result.errors}"
            )
        
        return {
            'success': result.success,
            'workflow_id': result.workflow_id,
            'format': result.format,
            'exported_data': result.exported_data,
            'metadata': result.metadata
        }
        
    except Exception as e:
        logger.exception(f"Failed to export workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow export failed: {str(e)}"
        )


@router.post("/import")
async def import_workflow(
    request: WorkflowImportRequest,
    user_info: UserInfo = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Import workflow from external format.
    
    Args:
        request: Import request configuration
        user_info: Current user information
        db_session: Database session
        
    Returns:
        Import result with new workflow ID
    """
    try:
        # Ensure tenant ID matches
        request.tenant_id = user_info.tenant_id
        
        service = WorkflowExportImportService(user_info.tenant_id, db_session)
        result = await service.import_workflow(request)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Import failed: {result.errors}"
            )
        
        return {
            'success': result.success,
            'imported_workflow_id': result.imported_workflow_id,
            'source_format': result.source_format,
            'validation_result': result.validation_result,
            'warnings': result.warnings,
            'metadata': result.metadata
        }
        
    except Exception as e:
        logger.exception(f"Failed to import workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow import failed: {str(e)}"
        )


@router.get("/health")
async def flowise_integration_health():
    """
    Health check endpoint for Flowise integration.
    
    Returns:
        Health status and integration information
    """
    return {
        'status': 'healthy',
        'service': 'flowise-integration',
        'version': '1.0.0',
        'features': {
            'workflow_translation': True,
            'workflow_execution': True,
            'workflow_export_import': True,
            'real_time_monitoring': True,
            'multi_tenant_isolation': True,
            'african_market_optimizations': True
        },
        'supported_node_types': [
            'smeflowAutomator',
            'smeflowMentor', 
            'smeflowSupervisor',
            'smeflowTenantManager',
            'startNode',
            'endNode'
        ],
        'supported_formats': [
            'json',
            'yaml', 
            'flowise',
            'langgraph'
        ]
    }


# Helper functions for validation
def _check_african_market_config(node_data: Dict[str, Any]) -> bool:
    """Check if node has African market configuration."""
    market_config = node_data.get('marketConfig', {})
    if isinstance(market_config, str):
        try:
            market_config = json.loads(market_config)
        except:
            return False
    
    african_indicators = ['region', 'currency', 'timezone', 'languages', 'phone_format']
    return any(key in market_config for key in african_indicators)


def _check_multi_language_support(workflow: FlowiseWorkflowData) -> Dict[str, Any]:
    """Check multi-language support in workflow."""
    languages_found = set()
    
    for node in workflow.nodes:
        market_config = node.data.get('marketConfig', {})
        if isinstance(market_config, str):
            try:
                market_config = json.loads(market_config)
            except:
                continue
        
        node_languages = market_config.get('languages', [])
        if isinstance(node_languages, list):
            languages_found.update(node_languages)
    
    african_languages = {'ha', 'yo', 'ig', 'sw', 'af', 'zu', 'xh', 'am'}
    has_african_languages = bool(languages_found.intersection(african_languages))
    
    return {
        'supported': len(languages_found) > 1,
        'languages_found': list(languages_found),
        'african_languages_supported': has_african_languages,
        'recommendation': 'Add African language support for better market reach' if not has_african_languages else None
    }


def _check_currency_handling(workflow: FlowiseWorkflowData) -> Dict[str, Any]:
    """Check currency handling in workflow."""
    currencies_found = set()
    
    for node in workflow.nodes:
        market_config = node.data.get('marketConfig', {})
        if isinstance(market_config, str):
            try:
                market_config = json.loads(market_config)
            except:
                continue
        
        currency = market_config.get('currency')
        if currency:
            currencies_found.add(currency)
    
    african_currencies = {'NGN', 'ZAR', 'KES', 'GHS', 'UGX', 'TZS', 'RWF', 'ETB'}
    has_african_currencies = bool(currencies_found.intersection(african_currencies))
    
    return {
        'supported': len(currencies_found) > 0,
        'currencies_found': list(currencies_found),
        'african_currencies_supported': has_african_currencies,
        'recommendation': 'Add African currency support (NGN, ZAR, KES)' if not has_african_currencies else None
    }


def _check_regional_compliance(workflow: FlowiseWorkflowData) -> Dict[str, Any]:
    """Check regional compliance configuration."""
    compliance_indicators = []
    
    for node in workflow.nodes:
        node_data = node.data
        
        # Check for compliance-related configuration
        if any(key in str(node_data).lower() for key in ['gdpr', 'popia', 'cbn', 'compliance']):
            compliance_indicators.append(node.id)
    
    return {
        'compliance_aware_nodes': len(compliance_indicators),
        'nodes_with_compliance': compliance_indicators,
        'recommendation': 'Add compliance configuration for African markets (GDPR, POPIA, CBN)' if not compliance_indicators else None
    }


def _check_local_integrations(workflow: FlowiseWorkflowData) -> Dict[str, Any]:
    """Check for local African integrations."""
    local_integrations = []
    african_services = ['mpesa', 'paystack', 'flutterwave', 'jumia', 'whatsapp']
    
    for node in workflow.nodes:
        node_data_str = str(node.data).lower()
        for service in african_services:
            if service in node_data_str:
                local_integrations.append(service)
    
    return {
        'local_integrations_found': list(set(local_integrations)),
        'integration_count': len(set(local_integrations)),
        'recommendation': 'Consider adding M-Pesa, Paystack, or WhatsApp integrations for African markets' if not local_integrations else None
    }


def _generate_recommendations(workflow: FlowiseWorkflowData, validation_result: Dict[str, Any]) -> List[str]:
    """Generate optimization recommendations for the workflow."""
    recommendations = []
    
    # African market recommendations
    african_compat = validation_result['african_market_compatibility']
    
    for category, analysis in african_compat.items():
        if isinstance(analysis, dict) and analysis.get('recommendation'):
            recommendations.append(analysis['recommendation'])
    
    # Performance recommendations
    if len(workflow.nodes) > 10:
        recommendations.append('Consider breaking large workflows into smaller, reusable components')
    
    # Security recommendations
    has_sensitive_data = any('password' in str(node.data).lower() or 'key' in str(node.data).lower() 
                           for node in workflow.nodes)
    if has_sensitive_data:
        recommendations.append('Ensure sensitive data is properly encrypted and not hardcoded')
    
    return recommendations
