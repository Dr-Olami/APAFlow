"""
Simple Workflow Example - Demonstrates basic LangGraph workflow functionality.

This example shows how to create, configure, and execute a simple workflow
using the SMEFlow LangGraph workflow engine.
"""

import asyncio
import uuid
from datetime import datetime

from smeflow.workflows.engine import WorkflowEngine
from smeflow.workflows.manager import WorkflowManager
from smeflow.workflows.state import WorkflowState
from smeflow.workflows.nodes import StartNode, EndNode, AgentNode, ConditionalNode, NodeConfig, BaseNode


async def simple_workflow_example():
    """
    Demonstrate a simple workflow with start and end nodes.
    """
    print("=== Simple Workflow Example ===")
    
    # Initialize workflow engine
    tenant_id = "demo_tenant"
    engine = WorkflowEngine(tenant_id)
    
    # Create and register nodes
    start_node = StartNode()
    end_node = EndNode()
    
    engine.register_node("start", start_node)
    engine.register_node("end", end_node)
    
    # Add edge
    engine.add_edge("start", "end")
    
    # Build workflow
    workflow_name = "simple_demo"
    workflow = engine.build_workflow(workflow_name)
    
    # Create initial state
    initial_state = WorkflowState(
        workflow_id=uuid.uuid4(),
        execution_id=uuid.uuid4(),
        tenant_id=tenant_id,
        data={"message": "Hello from SMEFlow!"},
        context={"region": "NG", "currency": "NGN"}
    )
    
    print(f"Starting workflow execution...")
    print(f"Initial state: {initial_state.status}")
    print(f"Initial data: {initial_state.data}")
    
    # Execute workflow
    final_state = await engine.execute_workflow(workflow_name, initial_state)
    
    print(f"\nWorkflow completed!")
    print(f"Final status: {final_state.status}")
    print(f"Final data: {final_state.data}")
    print(f"Duration: {final_state.get_duration_ms()}ms")


async def agent_workflow_example():
    """
    Demonstrate a workflow with agent nodes.
    """
    print("\n=== Agent Workflow Example ===")
    
    # Initialize workflow engine
    tenant_id = "demo_tenant"
    engine = WorkflowEngine(tenant_id)
    
    # Create nodes
    start_node = StartNode()
    agent_node = AgentNode(
        agent_id=uuid.uuid4(),
        agent_config={"type": "automator", "task": "process_data"}
    )
    end_node = EndNode()
    
    # Register nodes
    engine.register_node("start", start_node)
    engine.register_node("process", agent_node)
    engine.register_node("end", end_node)
    
    # Add edges
    engine.add_edge("start", "process")
    engine.add_edge("process", "end")
    
    # Build workflow
    workflow_name = "agent_demo"
    workflow = engine.build_workflow(workflow_name)
    
    # Create initial state with agent input
    initial_state = WorkflowState(
        workflow_id=uuid.uuid4(),
        execution_id=uuid.uuid4(),
        tenant_id=tenant_id,
        data={
            "agent_input": {
                "task": "Analyze customer data for Nigerian SME",
                "data": {"customers": 150, "revenue": "₦2,500,000"}
            }
        },
        context={"region": "NG", "currency": "NGN", "language": "en"}
    )
    
    print(f"Starting agent workflow...")
    print(f"Agent input: {initial_state.data['agent_input']}")
    
    # Execute workflow
    final_state = await engine.execute_workflow(workflow_name, initial_state)
    
    print(f"\nAgent workflow completed!")
    print(f"Final status: {final_state.status}")
    print(f"Agent output: {final_state.data.get('agent_output', {})}")
    print(f"Total cost: ${final_state.total_cost_usd:.4f}")
    print(f"Tokens used: {final_state.tokens_used}")


async def conditional_workflow_example():
    """
    Demonstrate a workflow with conditional routing.
    """
    print("\n=== Conditional Workflow Example ===")
    
    # Initialize workflow engine
    tenant_id = "demo_tenant"
    engine = WorkflowEngine(tenant_id)
    
    # Create custom processing node
    async def process_business_data(state: WorkflowState) -> WorkflowState:
        """Custom node that processes business data."""
        business_data = state.data.get("business_data", {})
        revenue = business_data.get("monthly_revenue", 0)
        
        # Simulate processing
        if revenue > 1000000:  # > ₦1M
            state.data["business_category"] = "high_value"
            state.data["recommendation"] = "Premium automation package"
        elif revenue > 500000:  # > ₦500K
            state.data["business_category"] = "medium_value"
            state.data["recommendation"] = "Standard automation package"
        else:
            state.data["business_category"] = "startup"
            state.data["recommendation"] = "Basic automation package"
        
        state.data["processed"] = True
        return state
    
    # Create nodes
    start_node = StartNode()
    
    process_config = NodeConfig(
        name="process_business",
        description="Process business data and categorize",
        required_inputs=["business_data"],
        outputs=["business_category", "recommendation"]
    )
    process_node = BaseNode(process_config, process_business_data)
    
    # Conditional routing function
    def route_by_category(state: WorkflowState) -> str:
        """Route based on business category."""
        category = state.data.get("business_category", "startup")
        if category == "high_value":
            return "premium_flow"
        elif category == "medium_value":
            return "standard_flow"
        else:
            return "basic_flow"
    
    conditional_node = ConditionalNode(route_by_category)
    
    # Different end nodes for different paths
    premium_end = EndNode()
    standard_end = EndNode()
    basic_end = EndNode()
    
    # Register nodes
    engine.register_node("start", start_node)
    engine.register_node("process_business", process_node)
    engine.register_node("conditional", conditional_node)
    engine.register_node("premium_end", premium_end)
    engine.register_node("standard_end", standard_end)
    engine.register_node("basic_end", basic_end)
    
    # Add edges
    engine.add_edge("start", "process_business")
    engine.add_edge("process_business", "conditional")
    
    # Add conditional edges
    engine.add_conditional_edge(
        "conditional",
        route_by_category,
        {
            "premium_flow": "premium_end",
            "standard_flow": "standard_end", 
            "basic_flow": "basic_end"
        }
    )
    
    # Build workflow
    workflow_name = "conditional_demo"
    workflow = engine.build_workflow(workflow_name)
    
    # Test different business scenarios
    test_cases = [
        {
            "name": "High-value SME",
            "data": {
                "business_data": {
                    "name": "Lagos Tech Solutions",
                    "monthly_revenue": 2500000,  # ₦2.5M
                    "employees": 25,
                    "region": "NG"
                },
                "condition_data": True
            }
        },
        {
            "name": "Medium SME", 
            "data": {
                "business_data": {
                    "name": "Abuja Consulting",
                    "monthly_revenue": 750000,  # ₦750K
                    "employees": 8,
                    "region": "NG"
                },
                "condition_data": True
            }
        },
        {
            "name": "Startup",
            "data": {
                "business_data": {
                    "name": "Port Harcourt Startup",
                    "monthly_revenue": 200000,  # ₦200K
                    "employees": 3,
                    "region": "NG"
                },
                "condition_data": True
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        
        # Create initial state
        initial_state = WorkflowState(
            workflow_id=uuid.uuid4(),
            execution_id=uuid.uuid4(),
            tenant_id=tenant_id,
            data=test_case["data"],
            context={"region": "NG", "currency": "NGN"}
        )
        
        # Execute workflow
        final_state = await engine.execute_workflow(workflow_name, initial_state)
        
        print(f"  Category: {final_state.data.get('business_category')}")
        print(f"  Recommendation: {final_state.data.get('recommendation')}")
        print(f"  Route taken: {final_state.data.get('route')}")
        print(f"  Status: {final_state.status}")


async def booking_funnel_workflow_example():
    """
    Demonstrate a booking funnel workflow using WorkflowManager.
    """
    print("\n=== Booking Funnel Workflow Example ===")
    
    # Initialize workflow manager (without database for demo)
    tenant_id = "demo_tenant"
    manager = WorkflowManager(tenant_id, None)
    
    # Create booking funnel workflow definition
    definition = {
        "nodes": [
            {"name": "start", "type": "start"},
            {"name": "discovery", "type": "agent", "agent_id": str(uuid.uuid4())},
            {"name": "booking", "type": "agent", "agent_id": str(uuid.uuid4())},
            {"name": "confirmation", "type": "agent", "agent_id": str(uuid.uuid4())},
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
            "max_retries": 2
        }
    }
    
    # Build workflow from definition
    workflow_name = "booking_funnel_demo"
    await manager._build_workflow_from_definition(workflow_name, definition)
    
    # Create initial state for booking scenario
    initial_state = WorkflowState(
        workflow_id=uuid.uuid4(),
        execution_id=uuid.uuid4(),
        tenant_id=tenant_id,
        data={
            "customer": {
                "name": "Adebayo Ogundimu",
                "phone": "+234-801-234-5678",
                "location": "Lagos, Nigeria",
                "service_interest": "Digital marketing consultation"
            },
            "agent_input": {
                "service_type": "consultation",
                "duration": "1 hour",
                "preferred_time": "afternoon"
            }
        },
        context={
            "region": "NG",
            "currency": "NGN",
            "language": "en",
            "timezone": "Africa/Lagos"
        }
    )
    
    print(f"Customer: {initial_state.data['customer']['name']}")
    print(f"Service: {initial_state.data['customer']['service_interest']}")
    print(f"Location: {initial_state.data['customer']['location']}")
    
    # Execute booking funnel
    final_state = await manager.engine.execute_workflow(workflow_name, initial_state)
    
    print(f"\nBooking funnel completed!")
    print(f"Final status: {final_state.status}")
    print(f"Total cost: ${final_state.total_cost_usd:.4f}")
    print(f"Processing time: {final_state.get_duration_ms()}ms")
    
    # Show agent results
    if final_state.agent_results:
        print(f"\nAgent Results:")
        for agent_id, result in final_state.agent_results.items():
            print(f"  Agent {agent_id[:8]}...: {result.get('output', 'No output')}")


async def main():
    """
    Run all workflow examples.
    """
    print("SMEFlow LangGraph Workflow Examples")
    print("=" * 50)
    
    try:
        # Run examples
        await simple_workflow_example()
        await agent_workflow_example()
        await conditional_workflow_example()
        await booking_funnel_workflow_example()
        
        print("\n" + "=" * 50)
        print("All workflow examples completed successfully!")
        
    except Exception as e:
        print(f"\nError running examples: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
