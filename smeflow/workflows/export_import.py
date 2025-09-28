"""
Workflow Export/Import Service for SMEFlow.

This module provides functionality to export SMEFlow workflows to various formats
and import workflows from external sources like Flowise.
"""

from typing import Dict, Any, List, Optional, Union
import uuid
import json
import logging
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
from enum import Enum
import yaml

from .state import WorkflowState
from .flowise_bridge import FlowiseWorkflowData, FlowiseBridge
from ..database.models import Workflow, WorkflowExecution
from ..database.connection import get_db_session

logger = logging.getLogger(__name__)


class WorkflowExportFormat(str, Enum):
    """Supported workflow export formats."""
    JSON = "json"
    YAML = "yaml"
    FLOWISE = "flowise"
    LANGGRAPH = "langgraph"


class WorkflowExportRequest(BaseModel):
    """Request model for workflow export."""
    
    workflow_id: str = Field(..., description="Workflow ID to export")
    format: WorkflowExportFormat = Field(WorkflowExportFormat.JSON, description="Export format")
    include_executions: bool = Field(False, description="Include execution history")
    include_metadata: bool = Field(True, description="Include metadata and timestamps")
    african_market_config: bool = Field(True, description="Include African market optimizations")


class WorkflowImportRequest(BaseModel):
    """Request model for workflow import."""
    
    workflow_data: Dict[str, Any] = Field(..., description="Workflow data to import")
    source_format: WorkflowExportFormat = Field(WorkflowExportFormat.JSON, description="Source format")
    tenant_id: str = Field(..., description="Target tenant ID")
    name_override: Optional[str] = Field(None, description="Override workflow name")
    validate_before_import: bool = Field(True, description="Validate workflow before import")


class WorkflowExportResult(BaseModel):
    """Result of workflow export operation."""
    
    success: bool
    workflow_id: str
    format: WorkflowExportFormat
    exported_data: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    errors: List[str] = []
    metadata: Dict[str, Any] = {}


class WorkflowImportResult(BaseModel):
    """Result of workflow import operation."""
    
    success: bool
    imported_workflow_id: Optional[str] = None
    source_format: WorkflowExportFormat
    validation_result: Optional[Dict[str, Any]] = None
    errors: List[str] = []
    warnings: List[str] = []
    metadata: Dict[str, Any] = {}


class WorkflowExportImportService:
    """
    Service for exporting and importing SMEFlow workflows.
    
    Supports multiple formats and provides validation, transformation,
    and African market optimization features.
    """
    
    def __init__(self, tenant_id: str, db_session=None):
        """
        Initialize the export/import service.
        
        Args:
            tenant_id: Tenant identifier for multi-tenant isolation
            db_session: Optional database session
        """
        self.tenant_id = tenant_id
        self.db_session = db_session
        self.flowise_bridge = FlowiseBridge(tenant_id, db_session)
        
        logger.info(f"Initialized WorkflowExportImportService for tenant: {tenant_id}")
    
    async def export_workflow(
        self, 
        request: WorkflowExportRequest,
        output_file: Optional[str] = None
    ) -> WorkflowExportResult:
        """
        Export workflow to specified format.
        
        Args:
            request: Export request configuration
            output_file: Optional output file path
            
        Returns:
            Export result with data or file path
        """
        result = WorkflowExportResult(
            success=False,
            workflow_id=request.workflow_id,
            format=request.format
        )
        
        try:
            # Get workflow from database
            workflow = await self._get_workflow(request.workflow_id)
            if not workflow:
                result.errors.append(f"Workflow not found: {request.workflow_id}")
                return result
            
            # Build export data based on format
            if request.format == WorkflowExportFormat.JSON:
                exported_data = await self._export_to_json(workflow, request)
            elif request.format == WorkflowExportFormat.YAML:
                exported_data = await self._export_to_yaml(workflow, request)
            elif request.format == WorkflowExportFormat.FLOWISE:
                exported_data = await self._export_to_flowise(workflow, request)
            elif request.format == WorkflowExportFormat.LANGGRAPH:
                exported_data = await self._export_to_langgraph(workflow, request)
            else:
                result.errors.append(f"Unsupported export format: {request.format}")
                return result
            
            # Save to file if requested
            if output_file:
                file_path = await self._save_export_file(exported_data, output_file, request.format)
                result.file_path = file_path
            else:
                result.exported_data = exported_data
            
            result.success = True
            result.metadata = {
                'exported_at': datetime.utcnow().isoformat(),
                'workflow_name': workflow.name,
                'tenant_id': self.tenant_id,
                'format': request.format,
                'size_bytes': len(json.dumps(exported_data)) if exported_data else 0
            }
            
            logger.info(f"Successfully exported workflow: {request.workflow_id} to {request.format}")
            
        except Exception as e:
            logger.exception(f"Failed to export workflow: {str(e)}")
            result.errors.append(f"Export failed: {str(e)}")
        
        return result
    
    async def import_workflow(self, request: WorkflowImportRequest) -> WorkflowImportResult:
        """
        Import workflow from external format.
        
        Args:
            request: Import request configuration
            
        Returns:
            Import result with new workflow ID
        """
        result = WorkflowImportResult(
            success=False,
            source_format=request.source_format
        )
        
        try:
            # Validate workflow data if requested
            if request.validate_before_import:
                validation_result = await self._validate_import_data(
                    request.workflow_data, 
                    request.source_format
                )
                result.validation_result = validation_result
                
                if not validation_result.get('valid', False):
                    result.errors.extend(validation_result.get('errors', []))
                    result.warnings.extend(validation_result.get('warnings', []))
                    return result
            
            # Transform data based on source format
            if request.source_format == WorkflowExportFormat.FLOWISE:
                workflow_definition = await self._import_from_flowise(request.workflow_data)
            elif request.source_format == WorkflowExportFormat.JSON:
                workflow_definition = await self._import_from_json(request.workflow_data)
            elif request.source_format == WorkflowExportFormat.YAML:
                workflow_definition = await self._import_from_yaml(request.workflow_data)
            elif request.source_format == WorkflowExportFormat.LANGGRAPH:
                workflow_definition = await self._import_from_langgraph(request.workflow_data)
            else:
                result.errors.append(f"Unsupported import format: {request.source_format}")
                return result
            
            # Create workflow in database
            workflow_name = request.name_override or workflow_definition.get('name', 'Imported Workflow')
            
            if not self.db_session:
                result.errors.append("Database session required for workflow import")
                return result
            
            from .manager import WorkflowManager
            manager = WorkflowManager(self.tenant_id, self.db_session)
            
            created_workflow = await manager.create_workflow(
                name=workflow_name,
                description=workflow_definition.get('description', 'Imported workflow'),
                template_type=workflow_definition.get('template_type'),
                definition=workflow_definition
            )
            
            result.success = True
            result.imported_workflow_id = str(created_workflow.id)
            result.metadata = {
                'imported_at': datetime.utcnow().isoformat(),
                'source_format': request.source_format,
                'workflow_name': workflow_name,
                'tenant_id': self.tenant_id,
                'original_id': workflow_definition.get('original_id')
            }
            
            logger.info(f"Successfully imported workflow: {workflow_name} from {request.source_format}")
            
        except Exception as e:
            logger.exception(f"Failed to import workflow: {str(e)}")
            result.errors.append(f"Import failed: {str(e)}")
        
        return result
    
    async def _get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow from database with tenant isolation."""
        if not self.db_session:
            return None
        
        from sqlalchemy import select
        
        stmt = select(Workflow).where(
            Workflow.id == uuid.UUID(workflow_id),
            Workflow.tenant_id == self.tenant_id
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _export_to_json(self, workflow: Workflow, request: WorkflowExportRequest) -> Dict[str, Any]:
        """Export workflow to JSON format."""
        export_data = {
            'id': str(workflow.id),
            'name': workflow.name,
            'description': workflow.description,
            'template_type': workflow.template_type,
            'definition': workflow.definition,
            'is_active': workflow.is_active,
            'version': workflow.version,
            'created_at': workflow.created_at.isoformat(),
            'updated_at': workflow.updated_at.isoformat(),
            'tenant_id': workflow.tenant_id
        }
        
        if request.include_metadata:
            export_data['metadata'] = {
                'export_format': 'json',
                'exported_at': datetime.utcnow().isoformat(),
                'smeflow_version': '1.0.0',
                'tenant_id': self.tenant_id
            }
        
        if request.african_market_config:
            export_data['african_market_config'] = {
                'supported_regions': ['NG', 'KE', 'ZA', 'GH', 'UG', 'TZ', 'RW', 'ET'],
                'supported_currencies': ['NGN', 'KES', 'ZAR', 'GHS', 'UGX', 'TZS', 'RWF', 'ETB'],
                'supported_languages': ['en', 'ha', 'yo', 'ig', 'sw', 'af', 'zu', 'xh', 'am'],
                'compliance_frameworks': ['GDPR', 'POPIA', 'CBN'],
                'local_integrations': ['M-Pesa', 'Paystack', 'Flutterwave', 'WhatsApp Business']
            }
        
        if request.include_executions:
            executions = await self._get_workflow_executions(workflow.id)
            export_data['executions'] = [
                {
                    'id': str(exec.id),
                    'status': exec.status,
                    'started_at': exec.started_at.isoformat(),
                    'completed_at': exec.completed_at.isoformat() if exec.completed_at else None,
                    'duration_ms': exec.duration_ms,
                    'input_data': exec.input_data,
                    'output_data': exec.output_data,
                    'error_message': exec.error_message
                }
                for exec in executions
            ]
        
        return export_data
    
    async def _export_to_yaml(self, workflow: Workflow, request: WorkflowExportRequest) -> Dict[str, Any]:
        """Export workflow to YAML-compatible format."""
        json_data = await self._export_to_json(workflow, request)
        # YAML export uses same structure as JSON but will be serialized differently
        return json_data
    
    async def _export_to_flowise(self, workflow: Workflow, request: WorkflowExportRequest) -> Dict[str, Any]:
        """Export workflow to Flowise format."""
        # Convert SMEFlow workflow to Flowise format
        flowise_data = {
            'id': str(workflow.id),
            'name': workflow.name,
            'description': workflow.description,
            'nodes': [],
            'edges': [],
            'viewport': {'x': 0, 'y': 0, 'zoom': 1},
            'tenant_id': workflow.tenant_id
        }
        
        # Convert workflow definition to Flowise nodes and edges
        definition = workflow.definition or {}
        nodes = definition.get('nodes', [])
        edges = definition.get('edges', [])
        
        # Transform nodes to Flowise format
        for i, node in enumerate(nodes):
            flowise_node = {
                'id': node.get('flowise_id', f"node-{i}"),
                'type': self._smeflow_to_flowise_node_type(node.get('type', 'start')),
                'position': node.get('position', {'x': i * 200, 'y': 100}),
                'data': {
                    'label': node.get('name', f"Node {i}"),
                    **node.get('config', {}),
                    **node.get('agent_config', {})
                }
            }
            flowise_data['nodes'].append(flowise_node)
        
        # Transform edges to Flowise format
        for edge in edges:
            flowise_edge = {
                'id': edge.get('flowise_id', f"edge-{len(flowise_data['edges'])}"),
                'source': edge.get('from'),
                'target': edge.get('to'),
                'sourceHandle': edge.get('source_handle'),
                'targetHandle': edge.get('target_handle')
            }
            flowise_data['edges'].append(flowise_edge)
        
        return flowise_data
    
    async def _export_to_langgraph(self, workflow: Workflow, request: WorkflowExportRequest) -> Dict[str, Any]:
        """Export workflow to LangGraph native format."""
        return {
            'workflow_id': str(workflow.id),
            'name': workflow.name,
            'description': workflow.description,
            'definition': workflow.definition,
            'langgraph_config': {
                'checkpointer': 'memory',
                'state_schema': 'WorkflowState',
                'node_types': ['start', 'end', 'agent', 'conditional'],
                'african_market_optimizations': True
            },
            'metadata': {
                'export_format': 'langgraph',
                'smeflow_version': '1.0.0',
                'tenant_id': self.tenant_id
            }
        }
    
    def _smeflow_to_flowise_node_type(self, smeflow_type: str) -> str:
        """Convert SMEFlow node type to Flowise node type."""
        type_mapping = {
            'start': 'startNode',
            'end': 'endNode',
            'automator_agent': 'smeflowAutomator',
            'mentor_agent': 'smeflowMentor',
            'supervisor_agent': 'smeflowSupervisor',
            'conditional': 'conditionalNode',
            'agent': 'smeflowAutomator'  # Default agent type
        }
        return type_mapping.get(smeflow_type, 'smeflowAutomator')
    
    async def _import_from_flowise(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import workflow from Flowise format."""
        # Use FlowiseBridge to translate
        flowise_workflow = FlowiseWorkflowData(**workflow_data)
        translation_result = await self.flowise_bridge.translate_workflow(flowise_workflow)
        
        if not translation_result.success:
            raise ValueError(f"Flowise translation failed: {translation_result.errors}")
        
        return translation_result.langgraph_definition
    
    async def _import_from_json(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import workflow from JSON format."""
        # JSON format is native SMEFlow format
        return workflow_data.get('definition', workflow_data)
    
    async def _import_from_yaml(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import workflow from YAML format."""
        # YAML format uses same structure as JSON
        return workflow_data.get('definition', workflow_data)
    
    async def _import_from_langgraph(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import workflow from LangGraph format."""
        return workflow_data.get('definition', workflow_data)
    
    async def _validate_import_data(
        self, 
        workflow_data: Dict[str, Any], 
        source_format: WorkflowExportFormat
    ) -> Dict[str, Any]:
        """Validate workflow data before import."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Basic structure validation
        if source_format == WorkflowExportFormat.FLOWISE:
            required_fields = ['id', 'name', 'nodes', 'edges']
            for field in required_fields:
                if field not in workflow_data:
                    validation_result['errors'].append(f"Missing required field: {field}")
                    validation_result['valid'] = False
        
        # Tenant ID validation
        if 'tenant_id' in workflow_data and workflow_data['tenant_id'] != self.tenant_id:
            validation_result['warnings'].append(
                f"Workflow tenant ID ({workflow_data['tenant_id']}) differs from current tenant ({self.tenant_id})"
            )
        
        return validation_result
    
    async def _get_workflow_executions(self, workflow_id: uuid.UUID) -> List[WorkflowExecution]:
        """Get workflow execution history."""
        if not self.db_session:
            return []
        
        from sqlalchemy import select
        
        stmt = select(WorkflowExecution).where(
            WorkflowExecution.workflow_id == workflow_id
        ).order_by(WorkflowExecution.started_at.desc()).limit(10)
        
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())
    
    async def _save_export_file(
        self, 
        data: Dict[str, Any], 
        file_path: str, 
        format: WorkflowExportFormat
    ) -> str:
        """Save exported data to file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == WorkflowExportFormat.YAML:
            with open(path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
        else:
            # JSON format (default)
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Saved exported workflow to: {file_path}")
        return str(path.absolute())


# Utility functions for batch operations
async def export_all_tenant_workflows(
    tenant_id: str,
    output_dir: str,
    format: WorkflowExportFormat = WorkflowExportFormat.JSON,
    db_session=None
) -> Dict[str, Any]:
    """
    Export all workflows for a tenant.
    
    Args:
        tenant_id: Tenant identifier
        output_dir: Output directory for exported files
        format: Export format
        db_session: Database session
        
    Returns:
        Export summary with results
    """
    service = WorkflowExportImportService(tenant_id, db_session)
    
    # Get all workflows for tenant
    from sqlalchemy import select
    from ..database.models import Workflow
    
    if not db_session:
        raise ValueError("Database session required")
    
    stmt = select(Workflow).where(Workflow.tenant_id == tenant_id)
    result = await db_session.execute(stmt)
    workflows = list(result.scalars().all())
    
    export_results = []
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for workflow in workflows:
        request = WorkflowExportRequest(
            workflow_id=str(workflow.id),
            format=format,
            include_executions=True,
            include_metadata=True,
            african_market_config=True
        )
        
        file_name = f"{workflow.name.replace(' ', '_')}_{workflow.id}.{format}"
        file_path = output_path / file_name
        
        export_result = await service.export_workflow(request, str(file_path))
        export_results.append({
            'workflow_id': str(workflow.id),
            'workflow_name': workflow.name,
            'success': export_result.success,
            'file_path': export_result.file_path,
            'errors': export_result.errors
        })
    
    return {
        'tenant_id': tenant_id,
        'total_workflows': len(workflows),
        'successful_exports': sum(1 for r in export_results if r['success']),
        'failed_exports': sum(1 for r in export_results if not r['success']),
        'output_directory': str(output_path.absolute()),
        'results': export_results
    }
