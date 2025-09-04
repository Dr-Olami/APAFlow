"""
Workflow Manager for SMEFlow - High-level workflow management.

This module provides workflow lifecycle management, template handling,
and integration with the database layer.
"""

from typing import Dict, Any, Optional, List
import uuid
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .engine import WorkflowEngine
from .state import WorkflowState
from .nodes import StartNode, EndNode, AgentNode, ConditionalNode
from .templates import IndustryTemplateFactory, IndustryType, IndustryTemplate, FormField
from ..database.models import Workflow, WorkflowExecution, Tenant
from ..database.connection import get_db_session

logger = logging.getLogger(__name__)


class WorkflowManager:
    """
    High-level workflow management for SMEFlow.
    
    Provides workflow CRUD operations, template management,
    and execution orchestration with multi-tenant isolation.
    """
    
    def __init__(self, tenant_id: str, db_session: Optional[AsyncSession] = None):
        """
        Initialize workflow manager.
        
        Args:
            tenant_id: Tenant identifier for multi-tenant isolation
            db_session: Optional database session
        """
        self.tenant_id = tenant_id
        self.db_session = db_session
        self.engine = WorkflowEngine(tenant_id, db_session)
        
        logger.info(f"Initialized WorkflowManager for tenant: {tenant_id}")
    
    async def create_workflow(
        self, 
        name: str, 
        description: Optional[str] = None,
        template_type: Optional[str] = None,
        definition: Optional[Dict[str, Any]] = None
    ) -> Workflow:
        """
        Create a new workflow.
        
        Args:
            name: Workflow name
            description: Optional description
            template_type: Optional template type
            definition: Workflow definition (nodes, edges, config)
            
        Returns:
            Created Workflow instance
        """
        if not self.db_session:
            raise ValueError("Database session required for workflow creation")
        
        # Create workflow record
        workflow = Workflow(
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            template_type=template_type,
            definition=definition or self._get_default_definition()
        )
        
        self.db_session.add(workflow)
        await self.db_session.commit()
        await self.db_session.refresh(workflow)
        
        logger.info(f"Created workflow: {name} (ID: {workflow.id})")
        return workflow
    
    async def get_workflow(self, workflow_id: uuid.UUID) -> Optional[Workflow]:
        """
        Get workflow by ID with tenant isolation.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Workflow instance or None if not found
        """
        if not self.db_session:
            return None
        
        stmt = select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.tenant_id == self.tenant_id
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_workflows(
        self, 
        active_only: bool = True,
        template_type: Optional[str] = None
    ) -> List[Workflow]:
        """
        List workflows for the tenant.
        
        Args:
            active_only: Only return active workflows
            template_type: Filter by template type
            
        Returns:
            List of Workflow instances
        """
        if not self.db_session:
            return []
        
        stmt = select(Workflow).where(Workflow.tenant_id == self.tenant_id)
        
        if active_only:
            stmt = stmt.where(Workflow.is_active == True)
        
        if template_type:
            stmt = stmt.where(Workflow.template_type == template_type)
        
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())
    
    async def update_workflow(
        self, 
        workflow_id: uuid.UUID, 
        **updates
    ) -> Optional[Workflow]:
        """
        Update workflow with tenant isolation.
        
        Args:
            workflow_id: Workflow identifier
            **updates: Fields to update
            
        Returns:
            Updated Workflow instance or None if not found
        """
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        for key, value in updates.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)
        
        workflow.updated_at = datetime.utcnow()
        await self.db_session.commit()
        await self.db_session.refresh(workflow)
        
        logger.info(f"Updated workflow: {workflow_id}")
        return workflow
    
    async def delete_workflow(self, workflow_id: uuid.UUID) -> bool:
        """
        Delete workflow with tenant isolation.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            True if deleted, False if not found
        """
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return False
        
        await self.db_session.delete(workflow)
        await self.db_session.commit()
        
        logger.info(f"Deleted workflow: {workflow_id}")
        return True
    
    async def execute_workflow(
        self, 
        workflow_id: uuid.UUID,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """
        Execute a workflow by ID.
        
        Args:
            workflow_id: Workflow identifier
            input_data: Input data for workflow
            context: Optional context data
            
        Returns:
            Final workflow state
        """
        # Get workflow definition
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Build workflow from definition
        workflow_name = f"workflow_{workflow_id}"
        await self._build_workflow_from_definition(workflow_name, workflow.definition)
        
        # Create initial state
        initial_state = WorkflowState(
            workflow_id=workflow_id,
            execution_id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            data=input_data,
            context=context or {}
        )
        
        # Execute workflow
        return await self.engine.execute_workflow(workflow_name, initial_state)
    
    async def get_workflow_executions(
        self, 
        workflow_id: uuid.UUID,
        limit: int = 50
    ) -> List[WorkflowExecution]:
        """
        Get execution history for a workflow.
        
        Args:
            workflow_id: Workflow identifier
            limit: Maximum number of executions to return
            
        Returns:
            List of WorkflowExecution instances
        """
        if not self.db_session:
            return []
        
        stmt = select(WorkflowExecution).where(
            WorkflowExecution.workflow_id == workflow_id
        ).order_by(WorkflowExecution.started_at.desc()).limit(limit)
        
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())
    
    async def _build_workflow_from_definition(
        self, 
        workflow_name: str, 
        definition: Dict[str, Any]
    ) -> None:
        """
        Build workflow engine from definition.
        
        Args:
            workflow_name: Name for the workflow
            definition: Workflow definition with nodes and edges
        """
        # Clear existing registration
        self.engine.node_registry.clear()
        self.engine.edge_registry.clear()
        
        # Register nodes from definition
        nodes = definition.get("nodes", [])
        for node_def in nodes:
            node = await self._create_node_from_definition(node_def)
            self.engine.register_node(node_def["name"], node)
        
        # Add edges from definition
        edges = definition.get("edges", [])
        for edge in edges:
            self.engine.add_edge(edge["from"], edge["to"])
        
        # Add conditional edges
        conditional_edges = definition.get("conditional_edges", [])
        for cond_edge in conditional_edges:
            # This would need more sophisticated condition parsing
            # For now, we'll skip conditional edges in definitions
            pass
        
        # Build the workflow
        self.engine.build_workflow(workflow_name)
    
    async def _create_node_from_definition(self, node_def: Dict[str, Any]):
        """
        Create a workflow node from definition.
        
        Args:
            node_def: Node definition dictionary
            
        Returns:
            WorkflowNode instance
        """
        node_type = node_def.get("type", "base")
        
        if node_type == "start":
            return StartNode()
        elif node_type == "end":
            return EndNode()
        elif node_type == "agent":
            agent_id = uuid.UUID(node_def["agent_id"])
            agent_config = node_def.get("config", {})
            return AgentNode(agent_id, agent_config)
        else:
            # Default to start node for unknown types
            return StartNode()
    
    def _get_default_definition(self) -> Dict[str, Any]:
        """
        Get default workflow definition.
        
        Returns:
            Default workflow definition
        """
        return {
            "nodes": [
                {"name": "start", "type": "start"},
                {"name": "end", "type": "end"}
            ],
            "edges": [
                {"from": "start", "to": "end"}
            ],
            "config": {
                "timeout_seconds": 300,
                "max_retries": 3
            }
        }
    
    async def create_booking_funnel_workflow(
        self, 
        name: str = "Booking Funnel",
        agent_ids: Optional[List[uuid.UUID]] = None
    ) -> Workflow:
        """
        Create a pre-built booking funnel workflow.
        
        Args:
            name: Workflow name
            agent_ids: Optional list of agent IDs to use
            
        Returns:
            Created Workflow instance
        """
        definition = {
            "nodes": [
                {"name": "start", "type": "start"},
                {"name": "discovery", "type": "agent", "agent_id": str(agent_ids[0]) if agent_ids else str(uuid.uuid4())},
                {"name": "booking", "type": "agent", "agent_id": str(agent_ids[1]) if len(agent_ids) > 1 else str(uuid.uuid4())},
                {"name": "confirmation", "type": "agent", "agent_id": str(agent_ids[2]) if len(agent_ids) > 2 else str(uuid.uuid4())},
                {"name": "end", "type": "end"}
            ],
            "edges": [
                {"from": "start", "to": "discovery"},
                {"from": "discovery", "to": "booking"},
                {"from": "booking", "to": "confirmation"},
                {"from": "confirmation", "to": "end"}
            ],
            "config": {
                "timeout_seconds": 600,
                "max_retries": 2,
                "template_type": "booking_funnel"
            }
        }
        
        return await self.create_workflow(
            name=name,
            description="Automated booking funnel for SME services",
            template_type="booking_funnel",
            definition=definition
        )
    
    async def create_marketing_campaign_workflow(
        self, 
        name: str = "Marketing Campaign",
        region: str = "NG"
    ) -> Workflow:
        """
        Create a pre-built marketing campaign workflow.
        
        Args:
            name: Workflow name
            region: Target region (NG, KE, ZA, etc.)
            
        Returns:
            Created Workflow instance
        """
        definition = {
            "nodes": [
                {"name": "start", "type": "start"},
                {"name": "trend_analysis", "type": "agent", "agent_id": str(uuid.uuid4())},
                {"name": "content_creation", "type": "agent", "agent_id": str(uuid.uuid4())},
                {"name": "campaign_execution", "type": "agent", "agent_id": str(uuid.uuid4())},
                {"name": "end", "type": "end"}
            ],
            "edges": [
                {"from": "start", "to": "trend_analysis"},
                {"from": "trend_analysis", "to": "content_creation"},
                {"from": "content_creation", "to": "campaign_execution"},
                {"from": "campaign_execution", "to": "end"}
            ],
            "config": {
                "timeout_seconds": 1800,
                "max_retries": 3,
                "template_type": "marketing_campaign",
                "region": region
            }
        }
        
        return await self.create_workflow(
            name=name,
            description=f"Hyperlocal marketing campaign for {region} market",
            template_type="marketing_campaign",
            definition=definition
        )

    async def create_industry_workflow(
        self,
        industry: IndustryType,
        name: Optional[str] = None,
        custom_fields: Optional[List[FormField]] = None,
        custom_business_rules: Optional[Dict[str, Any]] = None
    ) -> Workflow:
        """
        Create a workflow from industry-specific template.
        
        Args:
            industry: Industry type for template selection
            name: Optional custom name (uses template name if not provided)
            custom_fields: Additional form fields for customization
            custom_business_rules: Custom business rules to override defaults
            
        Returns:
            Created Workflow instance
        """
        # Get base template for industry
        base_template = IndustryTemplateFactory.get_template(industry)
        
        # Customize template if needed
        if custom_fields or custom_business_rules:
            template = IndustryTemplateFactory.customize_template(
                base_template,
                custom_fields or [],
                custom_business_rules=custom_business_rules
            )
        else:
            template = base_template
        
        # Create workflow definition from template
        definition = {
            "nodes": template.workflow_nodes,
            "edges": template.workflow_edges,
            "config": {
                "business_hours": template.business_hours,
                "advance_booking_days": template.advance_booking_days,
                "cancellation_policy": template.cancellation_policy,
                "required_integrations": template.required_integrations,
                "optional_integrations": template.optional_integrations,
                "supported_regions": template.supported_regions,
                "supported_currencies": template.supported_currencies,
                "supported_languages": template.supported_languages
            },
            "forms": {
                "booking_form": [field.dict() for field in template.booking_form_fields],
                "confirmation_form": [field.dict() for field in template.confirmation_fields]
            }
        }
        
        workflow_name = name or template.name
        
        return await self.create_workflow(
            name=workflow_name,
            description=template.description,
            template_type=f"industry_{industry.value}",
            definition=definition
        )

    async def get_industry_templates(self) -> List[Dict[str, Any]]:
        """
        Get all available industry templates.
        
        Returns:
            List of industry template information
        """
        templates = []
        
        for industry in IndustryTemplateFactory.list_available_industries():
            template = IndustryTemplateFactory.get_template(industry)
            templates.append({
                "industry": industry.value,
                "name": template.name,
                "description": template.description,
                "supported_regions": template.supported_regions,
                "supported_currencies": template.supported_currencies,
                "required_integrations": template.required_integrations,
                "optional_integrations": template.optional_integrations,
                "advance_booking_days": template.advance_booking_days,
                "sample_fields": len(template.booking_form_fields)
            })
        
        return templates

    async def get_industry_template_form(self, industry: IndustryType) -> Dict[str, Any]:
        """
        Get form fields for a specific industry template.
        
        Args:
            industry: Industry type
            
        Returns:
            Form configuration with fields and validation rules
        """
        template = IndustryTemplateFactory.get_template(industry)
        
        return {
            "industry": industry.value,
            "name": template.name,
            "description": template.description,
            "booking_form": [field.dict() for field in template.booking_form_fields],
            "confirmation_form": [field.dict() for field in template.confirmation_fields],
            "business_rules": {
                "business_hours": template.business_hours,
                "advance_booking_days": template.advance_booking_days,
                "cancellation_policy": template.cancellation_policy
            },
            "integrations": {
                "required": template.required_integrations,
                "optional": template.optional_integrations
            },
            "localization": {
                "supported_regions": template.supported_regions,
                "supported_currencies": template.supported_currencies,
                "supported_languages": template.supported_languages
            }
        }
