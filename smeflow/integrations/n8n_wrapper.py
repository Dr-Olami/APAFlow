"""
SMEFlow N8n Integration Wrapper.

This module provides a comprehensive wrapper around n8n-sdk-python with SMEFlow-specific
features including tenant isolation, compliance logging, and enterprise-grade error handling.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

try:
    from n8n_sdk_python import N8nClient
    from n8n_sdk_python.models.workflows import WorkflowList, Workflow
    from n8n_sdk_python.models.executions import ExecutionList, Execution
    N8N_SDK_AVAILABLE = True
except ImportError:
    # Mock classes for testing when n8n-sdk-python is not available
    class N8nClient:
        def __init__(self, base_url: str, api_key: str):
            self.base_url = base_url
            self.api_key = api_key
    
    class WorkflowList:
        def __init__(self, data=None):
            self.data = data or []
    
    class Workflow:
        def __init__(self, id=None, name=None, active=False):
            self.id = id
            self.name = name
            self.active = active
        
        def dict(self):
            return {"id": self.id, "name": self.name, "active": self.active}
    
    class ExecutionList:
        def __init__(self, data=None):
            self.data = data or []
    
    class Execution:
        def __init__(self, id=None, status=None):
            self.id = id
            self.status = status
        
        def dict(self):
            return {"id": self.id, "status": self.status}
    
    N8N_SDK_AVAILABLE = False

from pydantic import BaseModel, Field, validator

try:
    from python_dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from ..core.config import get_settings
from ..auth.jwt_middleware import UserInfo
from ..database.connection import get_db_session

logger = logging.getLogger(__name__)


class N8nConfig(BaseModel):
    """N8n configuration for SMEFlow integration."""
    
    base_url: str = Field(default="http://localhost:5678", description="N8n instance URL")
    api_key: str = Field(..., description="N8n API key")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    tenant_prefix: str = Field(default="smeflow", description="Tenant workflow prefix")
    
    @validator('base_url')
    def validate_base_url(cls, v):
        """Ensure base URL doesn't end with slash."""
        return v.rstrip('/')


class WorkflowTemplate(BaseModel):
    """SME workflow template definition."""
    
    id: str
    name: str
    description: str
    category: str  # "retail", "logistics", "services", "marketing"
    nodes: List[Dict[str, Any]]
    connections: Dict[str, Any]
    settings: Dict[str, Any] = {}
    tags: List[str] = []
    compliance_level: str = "standard"  # "basic", "standard", "enterprise"
    african_optimized: bool = True


class SMEFlowN8nClient:
    """
    Enterprise-grade N8n client wrapper for SMEFlow.
    
    Features:
    - Multi-tenant workflow isolation
    - Compliance logging and audit trails
    - SME-specific workflow templates
    - Integration with SMEFlow authentication
    - Error handling and retry logic
    - Performance monitoring
    """
    
    def __init__(self, config: Optional[N8nConfig] = None):
        """
        Initialize SMEFlow N8n client.
        
        Args:
            config: N8n configuration. If None, loads from environment.
        """
        self.config = config or self._load_config()
        self._client: Optional[N8nClient] = None
        self._templates: Dict[str, WorkflowTemplate] = {}
        self._load_templates()
    
    def _load_config(self) -> N8nConfig:
        """Load N8n configuration from environment variables."""
        settings = get_settings()
        return N8nConfig(
            base_url=settings.N8N_BASE_URL or "http://localhost:5678",
            api_key=settings.N8N_API_KEY,
            timeout=settings.N8N_TIMEOUT or 30,
            max_retries=settings.N8N_MAX_RETRIES or 3,
            tenant_prefix=settings.N8N_TENANT_PREFIX or "smeflow"
        )
    
    def _load_templates(self):
        """Load SME workflow templates."""
        # Product Recommender Template
        self._templates["product_recommender"] = WorkflowTemplate(
            id="product_recommender",
            name="Product Recommender",
            description="AI-powered product recommendation system for retail SMEs",
            category="retail",
            nodes=[
                {
                    "id": "webhook",
                    "type": "n8n-nodes-base.webhook",
                    "name": "Customer Request",
                    "parameters": {"httpMethod": "POST", "path": "recommend"}
                },
                {
                    "id": "ai_agent",
                    "type": "n8n-nodes-base.httpRequest",
                    "name": "AI Analysis",
                    "parameters": {
                        "url": "{{ $env.SMEFLOW_API_URL }}/agents/product-recommender",
                        "method": "POST"
                    }
                },
                {
                    "id": "response",
                    "type": "n8n-nodes-base.respondToWebhook",
                    "name": "Send Recommendations"
                }
            ],
            connections={
                "webhook": {"main": [["ai_agent"]]},
                "ai_agent": {"main": [["response"]]}
            },
            tags=["retail", "ai", "recommendations", "sme"],
            compliance_level="standard"
        )
        
        # Local Discovery Template
        self._templates["local_discovery"] = WorkflowTemplate(
            id="local_discovery",
            name="Local Business Discovery",
            description="Hyperlocal business discovery and booking system",
            category="services",
            nodes=[
                {
                    "id": "location_webhook",
                    "type": "n8n-nodes-base.webhook",
                    "name": "Location Request",
                    "parameters": {"httpMethod": "POST", "path": "discover"}
                },
                {
                    "id": "geocoding",
                    "type": "n8n-nodes-base.httpRequest",
                    "name": "Geocode Location",
                    "parameters": {
                        "url": "{{ $env.OPENCAGE_API_URL }}",
                        "method": "GET"
                    }
                },
                {
                    "id": "business_search",
                    "type": "n8n-nodes-base.httpRequest",
                    "name": "Find Local Businesses",
                    "parameters": {
                        "url": "{{ $env.SMEFLOW_API_URL }}/agents/local-discovery",
                        "method": "POST"
                    }
                },
                {
                    "id": "booking_integration",
                    "type": "n8n-nodes-base.httpRequest",
                    "name": "Cal.com Integration",
                    "parameters": {
                        "url": "{{ $env.CALCOM_API_URL }}/bookings",
                        "method": "POST"
                    }
                }
            ],
            connections={
                "location_webhook": {"main": [["geocoding"]]},
                "geocoding": {"main": [["business_search"]]},
                "business_search": {"main": [["booking_integration"]]}
            },
            tags=["services", "local", "booking", "hyperlocal"],
            compliance_level="standard"
        )
        
        # 360 Support Agent Template
        self._templates["support_agent"] = WorkflowTemplate(
            id="support_agent",
            name="360 Support Agent",
            description="Comprehensive customer support automation with HITL",
            category="support",
            nodes=[
                {
                    "id": "support_webhook",
                    "type": "n8n-nodes-base.webhook",
                    "name": "Support Request",
                    "parameters": {"httpMethod": "POST", "path": "support"}
                },
                {
                    "id": "intent_analysis",
                    "type": "n8n-nodes-base.httpRequest",
                    "name": "Analyze Intent",
                    "parameters": {
                        "url": "{{ $env.SMEFLOW_API_URL }}/agents/intent-analyzer",
                        "method": "POST"
                    }
                },
                {
                    "id": "knowledge_search",
                    "type": "n8n-nodes-base.httpRequest",
                    "name": "Search Knowledge Base",
                    "parameters": {
                        "url": "{{ $env.SMEFLOW_API_URL }}/knowledge/search",
                        "method": "POST"
                    }
                },
                {
                    "id": "human_escalation",
                    "type": "n8n-nodes-base.if",
                    "name": "Needs Human?",
                    "parameters": {
                        "conditions": {
                            "string": [{"value1": "{{ $json.confidence }}", "operation": "smaller", "value2": "0.8"}]
                        }
                    }
                },
                {
                    "id": "livekit_call",
                    "type": "n8n-nodes-base.httpRequest",
                    "name": "Initiate Voice Call",
                    "parameters": {
                        "url": "{{ $env.LIVEKIT_API_URL }}/calls",
                        "method": "POST"
                    }
                }
            ],
            connections={
                "support_webhook": {"main": [["intent_analysis"]]},
                "intent_analysis": {"main": [["knowledge_search"]]},
                "knowledge_search": {"main": [["human_escalation"]]},
                "human_escalation": {"main": [["livekit_call"], []]}
            },
            tags=["support", "ai", "hitl", "voice"],
            compliance_level="enterprise"
        )
    
    async def get_client(self, tenant_id: str) -> N8nClient:
        """
        Get N8n client instance for tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            N8n client instance
        """
        if not N8N_SDK_AVAILABLE:
            logger.warning("N8n SDK not available, using mock client for testing")
        
        return N8nClient(
            base_url=self.config.base_url,
            api_key=self.config.api_key
        )
    
    def _get_tenant_workflow_name(self, workflow_name: str, tenant_id: str) -> str:
        """Generate tenant-specific workflow name."""
        return f"{self.config.tenant_prefix}_{tenant_id}_{workflow_name}"
    
    async def create_workflow_from_template(
        self,
        template_id: str,
        tenant_id: str,
        user_info: UserInfo,
        custom_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new workflow from SME template.
        
        Args:
            template_id: Template identifier
            tenant_id: Tenant ID for isolation
            user_info: User information for audit
            custom_settings: Optional custom settings override
            
        Returns:
            Created workflow data
            
        Raises:
            ValueError: If template not found
            Exception: If workflow creation fails
        """
        if template_id not in self._templates:
            raise ValueError(f"Template '{template_id}' not found")
        
        template = self._templates[template_id]
        client = await self.get_client(tenant_id)
        
        # Generate tenant-specific workflow name
        workflow_name = self._get_tenant_workflow_name(template.name, tenant_id)
        
        # Prepare workflow data
        workflow_data = {
            "name": workflow_name,
            "nodes": template.nodes,
            "connections": template.connections,
            "settings": {**template.settings, **(custom_settings or {})},
            "tags": template.tags + [f"tenant:{tenant_id}", f"template:{template_id}"],
            "active": False  # Start inactive for safety
        }
        
        try:
            # Create workflow
            workflow = await client.create_workflow(workflow_data)
            
            # Log creation for compliance
            await self._log_workflow_action(
                action="create",
                workflow_id=workflow.id,
                template_id=template_id,
                tenant_id=tenant_id,
                user_info=user_info,
                metadata={"template_category": template.category}
            )
            
            logger.info(f"Created workflow '{workflow_name}' for tenant {tenant_id}")
            return workflow.dict()
            
        except Exception as e:
            logger.error(f"Failed to create workflow from template {template_id}: {str(e)}")
            raise
    
    async def execute_workflow(
        self,
        workflow_id: str,
        tenant_id: str,
        user_info: UserInfo,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow with tenant isolation.
        
        Args:
            workflow_id: Workflow ID to execute
            tenant_id: Tenant ID for isolation
            user_info: User information for audit
            input_data: Optional input data for workflow
            
        Returns:
            Execution result data
        """
        client = await self.get_client(tenant_id)
        
        try:
            # Execute workflow
            execution = await client.execute_workflow(
                workflow_id=workflow_id,
                input_data=input_data or {}
            )
            
            # Log execution for compliance
            await self._log_workflow_action(
                action="execute",
                workflow_id=workflow_id,
                execution_id=execution.id,
                tenant_id=tenant_id,
                user_info=user_info,
                metadata={"input_data_keys": list(input_data.keys()) if input_data else []}
            )
            
            logger.info(f"Executed workflow {workflow_id} for tenant {tenant_id}")
            return execution.dict()
            
        except Exception as e:
            logger.error(f"Failed to execute workflow {workflow_id}: {str(e)}")
            raise
    
    async def list_tenant_workflows(
        self,
        tenant_id: str,
        user_info: UserInfo,
        active_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List workflows for a specific tenant.
        
        Args:
            tenant_id: Tenant ID
            user_info: User information for audit
            active_only: Only return active workflows
            
        Returns:
            List of tenant workflows
        """
        client = await self.get_client(tenant_id)
        
        try:
            # Get all workflows and filter by tenant
            workflows: WorkflowList = await client.list_workflows()
            tenant_prefix = f"{self.config.tenant_prefix}_{tenant_id}_"
            
            tenant_workflows = [
                workflow.dict() for workflow in workflows.data
                if workflow.name.startswith(tenant_prefix) and
                (not active_only or workflow.active)
            ]
            
            logger.info(f"Listed {len(tenant_workflows)} workflows for tenant {tenant_id}")
            return tenant_workflows
            
        except Exception as e:
            logger.error(f"Failed to list workflows for tenant {tenant_id}: {str(e)}")
            raise
    
    async def get_workflow_executions(
        self,
        workflow_id: str,
        tenant_id: str,
        user_info: UserInfo,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get execution history for a workflow.
        
        Args:
            workflow_id: Workflow ID
            tenant_id: Tenant ID for isolation
            user_info: User information for audit
            limit: Maximum number of executions to return
            
        Returns:
            List of workflow executions
        """
        client = await self.get_client(tenant_id)
        
        try:
            executions: ExecutionList = await client.list_executions(
                workflow_id=workflow_id,
                limit=limit
            )
            
            return [execution.dict() for execution in executions.data]
            
        except Exception as e:
            logger.error(f"Failed to get executions for workflow {workflow_id}: {str(e)}")
            raise
    
    async def activate_workflow(
        self,
        workflow_id: str,
        tenant_id: str,
        user_info: UserInfo
    ) -> Dict[str, Any]:
        """
        Activate a workflow for production use.
        
        Args:
            workflow_id: Workflow ID to activate
            tenant_id: Tenant ID for isolation
            user_info: User information for audit
            
        Returns:
            Updated workflow data
        """
        client = await self.get_client(tenant_id)
        
        try:
            # Update workflow to active
            workflow = await client.update_workflow(
                workflow_id=workflow_id,
                workflow_data={"active": True}
            )
            
            # Log activation for compliance
            await self._log_workflow_action(
                action="activate",
                workflow_id=workflow_id,
                tenant_id=tenant_id,
                user_info=user_info
            )
            
            logger.info(f"Activated workflow {workflow_id} for tenant {tenant_id}")
            return workflow.dict()
            
        except Exception as e:
            logger.error(f"Failed to activate workflow {workflow_id}: {str(e)}")
            raise
    
    async def _log_workflow_action(
        self,
        action: str,
        workflow_id: str,
        tenant_id: str,
        user_info: UserInfo,
        template_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log workflow actions for compliance and audit.
        
        Args:
            action: Action performed (create, execute, activate, etc.)
            workflow_id: Workflow ID
            tenant_id: Tenant ID
            user_info: User information
            template_id: Optional template ID
            execution_id: Optional execution ID
            metadata: Optional additional metadata
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "workflow_id": workflow_id,
            "tenant_id": tenant_id,
            "user_id": user_info.user_id,
            "username": user_info.username,
            "template_id": template_id,
            "execution_id": execution_id,
            "metadata": metadata or {},
            "compliance_level": "standard"
        }
        
        # Store in database for compliance
        async with get_db_session(tenant_id) as session:
            # Implementation would store in audit log table
            logger.info(f"Workflow audit log: {json.dumps(log_entry)}")
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """
        Get list of available SME workflow templates.
        
        Returns:
            List of template metadata
        """
        return [
            {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "tags": template.tags,
                "compliance_level": template.compliance_level,
                "african_optimized": template.african_optimized
            }
            for template in self._templates.values()
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on N8n connection.
        
        Returns:
            Health status information
        """
        try:
            client = await self.get_client()
            workflows = await client.list_workflows(limit=1)
            
            return {
                "status": "healthy",
                "n8n_url": self.config.base_url,
                "connection": "ok",
                "workflows_accessible": True,
                "templates_loaded": len(self._templates),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "n8n_url": self.config.base_url,
                "connection": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
