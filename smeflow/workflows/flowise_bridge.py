"""
Flowise-to-LangGraph Workflow Bridge for SMEFlow.

This module provides translation between Flowise workflow definitions
and SMEFlow LangGraph execution engine with multi-tenant isolation.
"""

from typing import Dict, Any, List, Optional, Union
import uuid
import json
import logging
from datetime import datetime
from pydantic import BaseModel, Field

from .engine import WorkflowEngine
from .state import WorkflowState
from .nodes import StartNode, EndNode, AgentNode, ConditionalNode
from ..agents.manager import AgentManager
from ..database.connection import get_db_session

logger = logging.getLogger(__name__)


class FlowiseNodeData(BaseModel):
    """Flowise node data structure."""
    
    id: str
    type: str
    data: Dict[str, Any]
    position: Dict[str, float]
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None


class FlowiseEdgeData(BaseModel):
    """Flowise edge data structure."""
    
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None


class FlowiseWorkflowData(BaseModel):
    """Complete Flowise workflow data structure."""
    
    id: str
    name: str
    description: Optional[str] = None
    nodes: List[FlowiseNodeData]
    edges: List[FlowiseEdgeData]
    viewport: Optional[Dict[str, Any]] = None
    tenant_id: str = Field(..., description="Multi-tenant isolation identifier")


class WorkflowTranslationResult(BaseModel):
    """Result of workflow translation."""
    
    success: bool
    workflow_name: str
    langgraph_definition: Optional[Dict[str, Any]] = None
    errors: List[str] = []
    warnings: List[str] = []
    node_mappings: Dict[str, str] = {}  # Flowise node ID -> LangGraph node name


class FlowiseBridge:
    """
    Bridge service for translating Flowise workflows to LangGraph execution.
    
    Provides:
    - Workflow definition translation
    - Node type mapping
    - Multi-tenant execution
    - African market optimizations
    """
    
    def __init__(self, tenant_id: str, db_session=None):
        """
        Initialize the Flowise bridge.
        
        Args:
            tenant_id: Tenant identifier for multi-tenant isolation
            db_session: Optional database session
        """
        self.tenant_id = tenant_id
        self.db_session = db_session
        self.agent_manager = AgentManager(tenant_id, db_session)
        
        # Node type mappings from Flowise to SMEFlow
        self.node_type_mappings = {
            'smeflowAutomator': 'automator_agent',
            'smeflowMentor': 'mentor_agent', 
            'smeflowSupervisor': 'supervisor_agent',
            'smeflowTenantManager': 'tenant_manager',
            'startNode': 'start',
            'endNode': 'end',
            'conditionalNode': 'conditional',
            'agentNode': 'agent'
        }
        
        logger.info(f"Initialized FlowiseBridge for tenant: {tenant_id}")
    
    async def translate_workflow(
        self, 
        flowise_data: FlowiseWorkflowData
    ) -> WorkflowTranslationResult:
        """
        Translate Flowise workflow to LangGraph format.
        
        Args:
            flowise_data: Complete Flowise workflow data
            
        Returns:
            Translation result with LangGraph definition
        """
        result = WorkflowTranslationResult(
            success=False,
            workflow_name=flowise_data.name,
            node_mappings={}
        )
        
        try:
            # Validate tenant isolation
            if flowise_data.tenant_id != self.tenant_id:
                result.errors.append(f"Tenant mismatch: expected {self.tenant_id}, got {flowise_data.tenant_id}")
                return result
            
            # Translate nodes
            langgraph_nodes = []
            node_mappings = {}
            
            for flowise_node in flowise_data.nodes:
                translated_node = await self._translate_node(flowise_node)
                if translated_node:
                    langgraph_nodes.append(translated_node)
                    node_mappings[flowise_node.id] = translated_node['name']
                else:
                    result.warnings.append(f"Skipped unsupported node type: {flowise_node.type}")
            
            # Translate edges
            langgraph_edges = []
            for flowise_edge in flowise_data.edges:
                translated_edge = self._translate_edge(flowise_edge, node_mappings)
                if translated_edge:
                    langgraph_edges.append(translated_edge)
            
            # Create LangGraph definition
            langgraph_definition = {
                'name': flowise_data.name,
                'description': flowise_data.description,
                'tenant_id': self.tenant_id,
                'nodes': langgraph_nodes,
                'edges': langgraph_edges,
                'config': {
                    'timeout_seconds': 600,
                    'max_retries': 3,
                    'source': 'flowise',
                    'flowise_workflow_id': flowise_data.id,
                    'african_market_optimizations': True
                },
                'metadata': {
                    'created_from': 'flowise',
                    'original_id': flowise_data.id,
                    'translation_timestamp': datetime.utcnow().isoformat(),
                    'node_count': len(langgraph_nodes),
                    'edge_count': len(langgraph_edges)
                }
            }
            
            result.success = True
            result.langgraph_definition = langgraph_definition
            result.node_mappings = node_mappings
            
            logger.info(f"Successfully translated Flowise workflow: {flowise_data.name}")
            
        except Exception as e:
            logger.exception(f"Failed to translate Flowise workflow: {str(e)}")
            result.errors.append(f"Translation failed: {str(e)}")
        
        return result
    
    async def _translate_node(self, flowise_node: FlowiseNodeData) -> Optional[Dict[str, Any]]:
        """
        Translate a single Flowise node to LangGraph format.
        
        Args:
            flowise_node: Flowise node data
            
        Returns:
            LangGraph node definition or None if unsupported
        """
        node_type = self.node_type_mappings.get(flowise_node.type)
        if not node_type:
            logger.warning(f"Unsupported Flowise node type: {flowise_node.type}")
            return None
        
        # Generate clean node name from Flowise ID
        node_name = f"node_{flowise_node.id.replace('-', '_')}"
        
        base_node = {
            'name': node_name,
            'type': node_type,
            'flowise_id': flowise_node.id,
            'position': flowise_node.position,
            'config': flowise_node.data.copy()
        }
        
        # Handle specific node types
        if node_type in ['automator_agent', 'mentor_agent', 'supervisor_agent']:
            return await self._translate_agent_node(flowise_node, base_node)
        elif node_type == 'start':
            return self._translate_start_node(flowise_node, base_node)
        elif node_type == 'end':
            return self._translate_end_node(flowise_node, base_node)
        elif node_type == 'conditional':
            return self._translate_conditional_node(flowise_node, base_node)
        else:
            return base_node
    
    async def _translate_agent_node(
        self, 
        flowise_node: FlowiseNodeData, 
        base_node: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Translate SMEFlow agent node with proper configuration.
        
        Args:
            flowise_node: Original Flowise node
            base_node: Base translated node
            
        Returns:
            Enhanced agent node definition
        """
        node_data = flowise_node.data
        
        # Extract agent configuration from Flowise node
        # Parse JSON strings if needed
        task_config = node_data.get('taskConfig', {})
        if isinstance(task_config, str):
            try:
                task_config = json.loads(task_config)
            except (json.JSONDecodeError, TypeError):
                task_config = {}
        
        input_data = node_data.get('inputData', {})
        if isinstance(input_data, str):
            try:
                input_data = json.loads(input_data)
            except (json.JSONDecodeError, TypeError):
                input_data = {}
        
        market_config = node_data.get('marketConfig', {})
        if isinstance(market_config, str):
            try:
                market_config = json.loads(market_config)
            except (json.JSONDecodeError, TypeError):
                market_config = {}
        
        agent_config = {
            'task_type': node_data.get('taskType', 'api_integration'),
            'tenant_id': self.tenant_id,
            'task_config': task_config,
            'input_data': input_data,
            'market_config': market_config,
            'api_url': node_data.get('apiUrl', 'http://smeflow:8000'),
            'api_key': node_data.get('apiKey')
        }
        
        # Add African market optimizations
        if not agent_config['market_config']:
            agent_config['market_config'] = {
                'region': 'africa-west',
                'currency': 'NGN',
                'timezone': 'Africa/Lagos',
                'languages': ['en', 'ha', 'yo', 'ig'],
                'phone_format': '+234'
            }
        
        base_node['agent_config'] = agent_config
        base_node['requires_agent'] = True
        
        return base_node
    
    def _translate_start_node(
        self, 
        flowise_node: FlowiseNodeData, 
        base_node: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Translate start node."""
        base_node['is_entry_point'] = True
        return base_node
    
    def _translate_end_node(
        self, 
        flowise_node: FlowiseNodeData, 
        base_node: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Translate end node."""
        base_node['is_exit_point'] = True
        return base_node
    
    def _translate_conditional_node(
        self, 
        flowise_node: FlowiseNodeData, 
        base_node: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Translate conditional routing node."""
        node_data = flowise_node.data
        
        base_node['condition_config'] = {
            'condition_type': node_data.get('conditionType', 'simple'),
            'condition_expression': node_data.get('conditionExpression', 'true'),
            'true_path': node_data.get('truePath'),
            'false_path': node_data.get('falsePath')
        }
        
        return base_node
    
    def _translate_edge(
        self, 
        flowise_edge: FlowiseEdgeData, 
        node_mappings: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """
        Translate Flowise edge to LangGraph format.
        
        Args:
            flowise_edge: Flowise edge data
            node_mappings: Mapping of Flowise IDs to LangGraph names
            
        Returns:
            LangGraph edge definition or None if invalid
        """
        source_name = node_mappings.get(flowise_edge.source)
        target_name = node_mappings.get(flowise_edge.target)
        
        if not source_name or not target_name:
            logger.warning(f"Invalid edge: source={flowise_edge.source}, target={flowise_edge.target}")
            return None
        
        return {
            'from': source_name,
            'to': target_name,
            'flowise_id': flowise_edge.id,
            'source_handle': flowise_edge.sourceHandle,
            'target_handle': flowise_edge.targetHandle
        }
    
    async def execute_flowise_workflow(
        self,
        flowise_data: FlowiseWorkflowData,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """
        Execute a Flowise workflow through LangGraph engine.
        
        Args:
            flowise_data: Complete Flowise workflow data
            input_data: Input data for workflow execution
            context: Optional context data
            
        Returns:
            Final workflow execution state
        """
        # Translate workflow
        translation_result = await self.translate_workflow(flowise_data)
        
        if not translation_result.success:
            raise ValueError(f"Workflow translation failed: {translation_result.errors}")
        
        # Create workflow engine
        engine = WorkflowEngine(self.tenant_id, self.db_session)
        
        # Build workflow from translated definition
        workflow_name = f"flowise_{flowise_data.id}"
        await self._build_langgraph_workflow(
            engine, 
            workflow_name, 
            translation_result.langgraph_definition
        )
        
        # Create initial state
        initial_state = WorkflowState(
            workflow_id=uuid.uuid4(),
            execution_id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            data=input_data,
            context=context or {},
            metadata={
                'source': 'flowise',
                'flowise_workflow_id': flowise_data.id,
                'flowise_workflow_name': flowise_data.name
            }
        )
        
        # Execute workflow
        logger.info(f"Executing Flowise workflow: {flowise_data.name}")
        return await engine.execute_workflow(workflow_name, initial_state)
    
    async def _build_langgraph_workflow(
        self,
        engine: WorkflowEngine,
        workflow_name: str,
        definition: Dict[str, Any]
    ) -> None:
        """
        Build LangGraph workflow from translated definition.
        
        Args:
            engine: Workflow engine instance
            workflow_name: Name for the workflow
            definition: Translated workflow definition
        """
        # Clear existing registration
        engine.node_registry.clear()
        engine.edge_registry.clear()
        
        # Register nodes
        for node_def in definition['nodes']:
            node = await self._create_langgraph_node(node_def)
            engine.register_node(node_def['name'], node)
        
        # Add edges
        for edge_def in definition['edges']:
            engine.add_edge(edge_def['from'], edge_def['to'])
        
        # Build the workflow
        engine.build_workflow(workflow_name)
        
        logger.info(f"Built LangGraph workflow: {workflow_name} with {len(definition['nodes'])} nodes")
    
    async def _create_langgraph_node(self, node_def: Dict[str, Any]):
        """
        Create LangGraph node from definition.
        
        Args:
            node_def: Node definition
            
        Returns:
            WorkflowNode instance
        """
        node_type = node_def['type']
        
        if node_type == 'start':
            return StartNode()
        elif node_type == 'end':
            return EndNode()
        elif node_type in ['automator_agent', 'mentor_agent', 'supervisor_agent']:
            # Create agent node with configuration
            agent_config = node_def.get('agent_config', {})
            return AgentNode(
                agent_id=uuid.uuid4(),  # Will be resolved during execution
                config=agent_config
            )
        elif node_type == 'conditional':
            condition_config = node_def.get('condition_config', {})
            return ConditionalNode(condition_config)
        else:
            # Default to start node for unknown types
            logger.warning(f"Unknown node type: {node_type}, using StartNode")
            return StartNode()


class FlowiseWorkflowExecutor:
    """
    High-level executor for Flowise workflows with caching and optimization.
    """
    
    def __init__(self, tenant_id: str, db_session=None):
        """Initialize the executor."""
        self.tenant_id = tenant_id
        self.db_session = db_session
        self.bridge = FlowiseBridge(tenant_id, db_session)
        self._workflow_cache = {}  # Cache translated workflows
    
    async def execute_workflow(
        self,
        workflow_data: Union[FlowiseWorkflowData, Dict[str, Any]],
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> WorkflowState:
        """
        Execute Flowise workflow with caching optimization.
        
        Args:
            workflow_data: Flowise workflow data or dict
            input_data: Input data for execution
            context: Optional context data
            use_cache: Whether to use workflow translation cache
            
        Returns:
            Final workflow execution state
        """
        # Convert dict to FlowiseWorkflowData if needed
        if isinstance(workflow_data, dict):
            workflow_data = FlowiseWorkflowData(**workflow_data)
        
        # Check cache for translated workflow
        cache_key = f"{workflow_data.id}_{workflow_data.tenant_id}"
        
        if use_cache and cache_key in self._workflow_cache:
            logger.info(f"Using cached workflow translation: {workflow_data.name}")
            # Execute with cached translation
            # Implementation would use cached LangGraph definition
        
        # Execute workflow through bridge
        result = await self.bridge.execute_flowise_workflow(
            workflow_data, 
            input_data, 
            context
        )
        
        # Cache successful translations
        if use_cache and result.status == "completed":
            self._workflow_cache[cache_key] = {
                'timestamp': datetime.utcnow(),
                'workflow_name': workflow_data.name
            }
        
        return result
    
    def clear_cache(self) -> None:
        """Clear workflow translation cache."""
        self._workflow_cache.clear()
        logger.info("Cleared workflow translation cache")
