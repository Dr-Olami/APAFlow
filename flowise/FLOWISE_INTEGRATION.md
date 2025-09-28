# SMEFlow Flowise Integration

## Overview

This document describes the complete integration between SMEFlow's LangGraph workflow engine and Flowise's visual workflow builder, enabling African SMEs to create sophisticated automation workflows through a no-code interface.

## Architecture

### Core Components

1. **Flowise-to-LangGraph Bridge** (`smeflow/workflows/flowise_bridge.py`)
   - Translates Flowise workflow definitions to LangGraph format
   - Handles node type mapping and data flow conversion
   - Maintains multi-tenant isolation and African market optimizations

2. **Workflow Export/Import Service** (`smeflow/workflows/export_import.py`)
   - Supports multiple formats: JSON, YAML, Flowise, LangGraph
   - Bidirectional workflow conversion
   - Validation and compatibility checking

3. **Enhanced Custom Nodes** (`flowise/custom-nodes/`)
   - Real SMEFlow API integration (replaces mock data)
   - Multi-tenant aware execution
   - African market optimizations built-in

4. **API Integration** (`smeflow/api/flowise_integration_routes.py`)
   - REST endpoints for workflow execution and translation
   - WebSocket support for real-time monitoring
   - Comprehensive validation and error handling

## Features Implemented

### ✅ **Workflow Translation & Execution**
- **Flowise → LangGraph**: Complete workflow definition translation
- **Node Mapping**: SMEFlow agent nodes (Automator, Mentor, Supervisor)
- **Edge Translation**: Workflow routing and conditional logic
- **State Management**: Persistent workflow state with checkpointing
- **Multi-tenant Isolation**: Complete tenant separation at all levels

### ✅ **Enhanced Custom Nodes**
- **SMEFlowAutomator**: Real API integration for task execution
- **SMEFlowMentor**: Business guidance with African market context
- **SMEFlowSupervisor**: Workflow orchestration and quality assurance
- **SMEFlowWorkflowExecutor**: Complete workflow execution with industry templates
- **SMEFlowTenantManager**: Multi-tenant configuration management

### ✅ **Export/Import Functionality**
- **Multiple Formats**: JSON, YAML, Flowise, LangGraph native
- **Validation**: Pre-import workflow validation and compatibility checking
- **Metadata Preservation**: African market configurations and tenant data
- **Batch Operations**: Export all tenant workflows at once

### ✅ **African Market Optimizations**
- **Multi-language Support**: 50+ languages including Swahili, Hausa, Yoruba
- **Currency Handling**: NGN, KES, ZAR, GHS, UGX, TZS, RWF, ETB
- **Regional Compliance**: GDPR, POPIA, CBN data residency
- **Local Integrations**: M-Pesa, Paystack, Flutterwave, WhatsApp Business
- **Timezone Optimization**: African business hours and scheduling

### ✅ **API Endpoints**

#### Workflow Execution
```http
POST /api/v1/flowise/execute
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "workflow_data": {
    "id": "workflow-123",
    "name": "Customer Onboarding",
    "nodes": [...],
    "edges": [...],
    "tenant_id": "tenant-uuid"
  },
  "input_data": {
    "customer_name": "John Doe",
    "service_type": "consultation"
  },
  "context": {
    "priority": "high",
    "source": "flowise"
  }
}
```

#### Workflow Translation
```http
POST /api/v1/flowise/translate
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "workflow_data": {
    "id": "workflow-123",
    "name": "Test Workflow",
    "nodes": [...],
    "edges": [...],
    "tenant_id": "tenant-uuid"
  }
}
```

#### Workflow Export
```http
POST /api/v1/flowise/export
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "workflow_id": "workflow-uuid",
  "format": "flowise",
  "include_executions": true,
  "african_market_config": true
}
```

#### Workflow Import
```http
POST /api/v1/flowise/import
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "workflow_data": {...},
  "source_format": "flowise",
  "validate_before_import": true
}
```

#### Validation
```http
POST /api/v1/flowise/validate
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "workflow_data": {...}
}
```

### ✅ **Real-time Monitoring**
```http
WebSocket: /api/v1/flowise/execute/stream/{workflow_id}
```

## Usage Examples

### 1. Creating a Consulting Workflow in Flowise

```javascript
// Flowise workflow definition
const consultingWorkflow = {
  id: "consulting-workflow-001",
  name: "Professional Consulting Booking",
  description: "Automated lead qualification and booking for consulting services",
  tenant_id: "tenant-uuid",
  nodes: [
    {
      id: "start-1",
      type: "startNode",
      data: { label: "Start" },
      position: { x: 0, y: 0 }
    },
    {
      id: "mentor-1", 
      type: "smeflowMentor",
      data: {
        guidanceType: "lead_qualification",
        industrySector: "consulting",
        marketConfig: JSON.stringify({
          region: "nigeria",
          currency: "NGN",
          timezone: "Africa/Lagos",
          languages: ["en", "ha", "yo"]
        })
      },
      position: { x: 200, y: 0 }
    },
    {
      id: "automator-1",
      type: "smeflowAutomator", 
      data: {
        taskType: "email_automation",
        taskConfig: JSON.stringify({
          template: "consultation_booking",
          priority: "high"
        })
      },
      position: { x: 400, y: 0 }
    },
    {
      id: "end-1",
      type: "endNode",
      data: { label: "End" },
      position: { x: 600, y: 0 }
    }
  ],
  edges: [
    { id: "edge-1", source: "start-1", target: "mentor-1" },
    { id: "edge-2", source: "mentor-1", target: "automator-1" },
    { id: "edge-3", source: "automator-1", target: "end-1" }
  ]
};
```

### 2. Executing the Workflow

```python
# Python client example
import requests

# Execute workflow
response = requests.post(
    "http://localhost:8000/api/v1/flowise/execute",
    headers={
        "Authorization": "Bearer <jwt_token>",
        "Content-Type": "application/json"
    },
    json={
        "workflow_data": consultingWorkflow,
        "input_data": {
            "customer_name": "Adebayo Ogundimu",
            "company": "Lagos Tech Solutions",
            "service_interest": "Digital Transformation Consulting",
            "budget_range": "₦500,000 - ₦2,000,000",
            "timeline": "Q1 2025"
        },
        "context": {
            "priority": "high",
            "source": "website_form",
            "region": "lagos"
        }
    }
)

result = response.json()
print(f"Workflow Status: {result['status']}")
print(f"Execution ID: {result['execution_id']}")
```

### 3. African Market Optimization Example

```javascript
// Marketing campaign workflow for Nigerian SME
const marketingWorkflow = {
  id: "marketing-nigeria-001",
  name: "Lagos Restaurant Social Media Campaign",
  nodes: [
    {
      id: "content-generator",
      type: "smeflowAutomator",
      data: {
        taskType: "ai_content_generation",
        marketConfig: JSON.stringify({
          region: "nigeria",
          currency: "NGN", 
          languages: ["en", "yo", "ig"],
          cultural_context: {
            cuisine_type: "nigerian",
            target_audience: "young_professionals",
            local_events: ["independence_day", "new_yam_festival"]
          },
          business_hours: {
            start: "10:00",
            end: "22:00", 
            timezone: "Africa/Lagos"
          }
        })
      }
    }
  ]
};
```

## Testing

### Unit Tests
```bash
# Run Flowise integration tests
pytest tests/test_flowise_integration.py -v

# Test coverage
pytest tests/test_flowise_integration.py --cov=smeflow.workflows.flowise_bridge --cov-report=html
```

### Integration Tests
```bash
# Test complete workflow execution
python -m pytest tests/test_flowise_integration.py::TestFlowiseBridge::test_execute_flowise_workflow

# Test African market optimizations
python -m pytest tests/test_flowise_integration.py::TestAfricanMarketOptimizations
```

## Deployment

### 1. Flowise Custom Nodes
```bash
# Copy custom nodes to Flowise installation
cp -r flowise/custom-nodes/* /path/to/flowise/packages/components/nodes/

# Install dependencies
cd /path/to/flowise/packages/components/nodes/
npm install

# Restart Flowise
docker-compose restart flowise
```

### 2. SMEFlow API
```bash
# Start SMEFlow with Flowise integration
python -m smeflow.main

# Verify integration
curl http://localhost:8000/api/v1/flowise/health
```

### 3. Environment Variables
```bash
# .env configuration
FLOWISE_API_URL=http://localhost:3000
SMEFLOW_API_URL=http://localhost:8000
ENABLE_FLOWISE_INTEGRATION=true
AFRICAN_MARKET_OPTIMIZATIONS=true
```

## Troubleshooting

### Common Issues

1. **Node Not Appearing in Flowise**
   - Check custom node installation path
   - Verify package.json includes new nodes
   - Restart Flowise container

2. **API Connection Failures**
   - Verify SMEFlow API is running on correct port
   - Check JWT token validity
   - Confirm tenant ID format (UUID)

3. **Workflow Translation Errors**
   - Validate Flowise workflow structure
   - Check required fields (id, name, nodes, edges)
   - Verify tenant ID matches current user

4. **African Market Config Issues**
   - Ensure marketConfig is valid JSON string
   - Check supported currencies and languages
   - Verify timezone format (Africa/Lagos, Africa/Nairobi, etc.)

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger('smeflow.workflows.flowise_bridge').setLevel(logging.DEBUG)
```

## Performance Considerations

### Caching
- Workflow translation results are cached per tenant
- Cache TTL: 1 hour (configurable)
- Clear cache: `POST /api/v1/flowise/cache/clear`

### Optimization
- Use `use_cache=true` for repeated workflow executions
- Batch export operations for multiple workflows
- Enable compression for large workflow definitions

### Monitoring
- WebSocket connections for real-time execution monitoring
- Metrics available via `/api/v1/flowise/health`
- Integration with SigNoz for observability

## Security

### Multi-tenant Isolation
- All operations enforce tenant boundaries
- Database-level separation
- API-level validation

### Authentication
- JWT token required for all endpoints
- Keycloak integration for user management
- Role-based access control via Cerbos

### Data Protection
- Encrypted credential storage
- GDPR/POPIA compliance
- Regional data residency enforcement

## Future Enhancements

### Planned Features
- [ ] Real-time collaborative editing
- [ ] Workflow versioning and rollback
- [ ] Advanced analytics dashboard
- [ ] Mobile app integration
- [ ] Voice-activated workflow creation

### African Market Expansion
- [ ] Additional local language support
- [ ] More regional payment integrations
- [ ] Government API connections
- [ ] Cultural calendar integration

## Support

For technical support and questions:
- GitHub Issues: https://github.com/smeflow/smeflow-platform/issues
- Documentation: https://docs.smeflow.com/flowise-integration
- Community: https://community.smeflow.com

---

**SMEFlow Team** - Empowering African SMEs through intelligent automation
