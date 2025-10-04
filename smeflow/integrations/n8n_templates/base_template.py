"""
Base n8N Workflow Template for SMEFlow Platform.

Provides the foundation for creating n8N workflow templates with SMEFlow integration,
multi-tenant support, and African market optimizations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import json
import uuid


class N8nNode(BaseModel):
    """Represents an n8N workflow node."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str
    typeVersion: int = 1
    position: List[int] = Field(default_factory=lambda: [0, 0])
    parameters: Dict[str, Any] = Field(default_factory=dict)
    credentials: Optional[Dict[str, str]] = None
    
    class Config:
        """Pydantic configuration."""
        extra = "allow"


class N8nConnection(BaseModel):
    """Represents a connection between n8N nodes."""
    
    node: str
    type: str = "main"
    index: int = 0


class N8nWorkflowTemplate(ABC):
    """
    Base class for n8N workflow templates.
    
    Provides common functionality for creating n8N workflows with SMEFlow integration,
    including tenant isolation, credential management, and African market optimizations.
    """
    
    def __init__(self, tenant_id: str, template_name: str):
        """
        Initialize workflow template.
        
        Args:
            tenant_id: Unique identifier for the tenant
            template_name: Name of the workflow template
        """
        self.tenant_id = tenant_id
        self.template_name = template_name
        self.workflow_id = str(uuid.uuid4())
        self.nodes: List[N8nNode] = []
        self.connections: Dict[str, List[List[N8nConnection]]] = {}
        
    @abstractmethod
    def build_workflow(self) -> Dict[str, Any]:
        """
        Build the complete n8N workflow definition.
        
        Returns:
            Complete n8N workflow JSON definition
        """
        pass
    
    def add_node(self, node: N8nNode) -> str:
        """
        Add a node to the workflow.
        
        Args:
            node: The n8N node to add
            
        Returns:
            The node ID
        """
        self.nodes.append(node)
        return node.id
    
    def add_connection(self, from_node: str, to_node: str, 
                      connection_type: str = "main", index: int = 0):
        """
        Add a connection between two nodes.
        
        Args:
            from_node: Source node name
            to_node: Target node name
            connection_type: Type of connection (default: "main")
            index: Connection index (default: 0)
        """
        if from_node not in self.connections:
            self.connections[from_node] = [[]]
            
        connection = N8nConnection(
            node=to_node,
            type=connection_type,
            index=index
        )
        self.connections[from_node][0].append(connection)
    
    def create_webhook_trigger(self, webhook_path: str) -> N8nNode:
        """
        Create a webhook trigger node for SMEFlow integration.
        
        Args:
            webhook_path: Path for the webhook endpoint
            
        Returns:
            Configured webhook trigger node
        """
        return N8nNode(
            name="SMEFlow Webhook Trigger",
            type="n8n-nodes-base.webhook",
            parameters={
                "path": f"smeflow/{self.tenant_id}/{webhook_path}",
                "httpMethod": "POST",
                "responseMode": "responseNode",
                "options": {
                    "noResponseBody": False
                }
            },
            position=[100, 100]
        )
    
    def create_smeflow_callback(self, callback_url: str) -> N8nNode:
        """
        Create a callback node to notify SMEFlow of completion.
        
        Args:
            callback_url: SMEFlow callback endpoint
            
        Returns:
            Configured HTTP request node for callback
        """
        return N8nNode(
            name="SMEFlow Callback",
            type="n8n-nodes-base.httpRequest",
            parameters={
                "url": callback_url,
                "method": "POST",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "Content-Type",
                            "value": "application/json"
                        },
                        {
                            "name": "X-Tenant-ID", 
                            "value": self.tenant_id
                        }
                    ]
                },
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {
                            "name": "workflow_id",
                            "value": "={{ $workflow.id }}"
                        },
                        {
                            "name": "execution_id", 
                            "value": "={{ $execution.id }}"
                        },
                        {
                            "name": "status",
                            "value": "completed"
                        },
                        {
                            "name": "result",
                            "value": "={{ $json }}"
                        },
                        {
                            "name": "timestamp",
                            "value": "={{ $now }}"
                        }
                    ]
                }
            },
            position=[800, 300]
        )
    
    def create_error_handler(self) -> N8nNode:
        """
        Create an error handling node for workflow failures.
        
        Returns:
            Configured error handler node
        """
        return N8nNode(
            name="Error Handler",
            type="n8n-nodes-base.httpRequest",
            parameters={
                "url": f"http://smeflow-api:8000/api/v1/n8n/webhooks/error",
                "method": "POST",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "Content-Type",
                            "value": "application/json"
                        },
                        {
                            "name": "X-Tenant-ID",
                            "value": self.tenant_id
                        }
                    ]
                },
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {
                            "name": "workflow_id",
                            "value": "={{ $workflow.id }}"
                        },
                        {
                            "name": "execution_id",
                            "value": "={{ $execution.id }}"
                        },
                        {
                            "name": "error",
                            "value": "={{ $json.error }}"
                        },
                        {
                            "name": "timestamp",
                            "value": "={{ $now }}"
                        }
                    ]
                }
            },
            position=[800, 500]
        )
    
    def get_workflow_metadata(self) -> Dict[str, Any]:
        """
        Get workflow metadata for SMEFlow integration.
        
        Returns:
            Workflow metadata dictionary
        """
        return {
            "id": self.workflow_id,
            "name": f"{self.template_name} - {self.tenant_id}",
            "tenant_id": self.tenant_id,
            "template_name": self.template_name,
            "created_at": datetime.utcnow().isoformat(),
            "tags": ["smeflow", "african-market", self.template_name.lower()],
            "settings": {
                "executionOrder": "v1",
                "saveManualExecutions": True,
                "callerPolicy": "workflowsFromSameOwner",
                "errorWorkflow": f"error-handler-{self.tenant_id}"
            }
        }
    
    def to_n8n_json(self) -> str:
        """
        Convert workflow to n8N JSON format.
        
        Returns:
            JSON string representation of the workflow
        """
        workflow_def = self.build_workflow()
        return json.dumps(workflow_def, indent=2)
    
    def validate_african_market_compliance(self) -> List[str]:
        """
        Validate workflow for African market compliance requirements.
        
        Returns:
            List of compliance issues (empty if compliant)
        """
        issues = []
        
        # Check for data residency compliance
        for node in self.nodes:
            if node.type == "n8n-nodes-base.httpRequest":
                url = node.parameters.get("url", "")
                if "europe" in url.lower() or "us-" in url.lower():
                    issues.append(f"Node {node.name} may violate data residency requirements")
        
        # Check for required error handling
        error_nodes = [n for n in self.nodes if "error" in n.name.lower()]
        if not error_nodes:
            issues.append("Workflow missing error handling nodes")
        
        # Check for tenant isolation
        webhook_nodes = [n for n in self.nodes if n.type == "n8n-nodes-base.webhook"]
        for node in webhook_nodes:
            path = node.parameters.get("path", "")
            if self.tenant_id not in path:
                issues.append(f"Webhook node {node.name} missing tenant isolation")
        
        return issues


class SimpleN8nWorkflowTemplate(N8nWorkflowTemplate):
    """
    Simple concrete implementation of N8nWorkflowTemplate for creating sub-workflows.
    
    Used by other templates when they need to create additional workflows
    (like callback handlers, verification workflows, etc.)
    """
    
    def build_workflow(self) -> Dict[str, Any]:
        """
        Build a simple workflow with just the added nodes.
        
        Returns:
            Complete n8N workflow JSON definition
        """
        workflow_def = {
            **self.get_workflow_metadata(),
            "nodes": [node.model_dump() for node in self.nodes],
            "connections": self.connections
        }
        
        return workflow_def
