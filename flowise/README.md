# SMEFlow Flowise Integration

This directory contains the Flowise integration configuration for SMEFlow's multi-tenant African market automation platform.

## Overview

Flowise provides a no-code visual workflow builder that integrates with SMEFlow's agent system, allowing users to create complex automation workflows without coding.

## Features

### Multi-tenant Support
- Tenant-aware workspace isolation
- Per-tenant configuration and data separation
- Regional compliance (CBN Nigeria, POPIA South Africa)

### African Market Optimizations
- Multi-currency support (NGN, KES, ZAR, GHS, UGX, TZS, RWF, ETB)
- Multi-language UI (50+ languages including Swahili, Hausa, Yoruba)
- Local phone format validation (+234, +254, +27)
- Regional business hours and timezone awareness

### Custom SMEFlow Nodes

#### 1. SMEFlow Agent Node
- Execute Automator, Mentor, and Supervisor agents
- Multi-tenant isolation with tenant ID validation
- African market configuration support
- Real-time cost and token tracking

#### 2. SMEFlow Workflow Node
- Industry-specific workflow templates:
  - Consulting: Lead qualification and proposal generation
  - Salon/Spa: Service booking and stylist assignment
  - Healthcare: Patient verification and compliance
  - Manufacturing: Resource planning and safety assessment
  - Marketing: Campaign execution and trend analysis
  - ERP: Invoice processing and vendor management
  - Compliance: Automated audit trails and reporting
- LangGraph stateful workflow execution
- Self-healing capabilities with automatic recovery

#### 3. SMEFlow Tenant Manager Node
- Tenant information and validation
- Agent and workflow listing per tenant
- Usage statistics and cost tracking
- Access control and permissions

## Configuration

### Environment Variables
- `FLOWISE_USERNAME`: Admin username (default: admin)
- `FLOWISE_PASSWORD`: Admin password (default: admin123)
- `DATABASE_TYPE`: postgres
- `DATABASE_HOST`: db
- `DATABASE_NAME`: smeflow
- `CORS_ORIGINS`: * (for development)

### Custom Node Installation
Custom SMEFlow nodes are automatically mounted at:
```
/opt/flowise/packages/components/nodes/smeflow
```

## Usage

### 1. Access Flowise UI
Navigate to `http://localhost:3000` (or your Codespaces URL)

### 2. Create Multi-tenant Workflows
1. Add SMEFlow nodes to your workflow
2. Configure tenant ID for isolation
3. Set African market parameters (region, currency, language)
4. Connect with other Flowise nodes for complete automation

### 3. Example Workflow: Nigerian Salon Booking
```
Customer Input → SMEFlow Tenant Manager (validate) → 
SMEFlow Workflow (salon_service_booking) → 
SMS Notification (WhatsApp Business API) → 
Calendar Integration (Google Calendar)
```

## Security

### Multi-tenant Isolation
- Database-level tenant separation
- API-level tenant validation
- Encrypted credential storage per tenant

### African Market Compliance
- CBN data residency for Nigerian tenants
- POPIA compliance for South African tenants
- Audit trails for all tenant operations

## Development

### Adding New Custom Nodes
1. Create new node file in `custom-nodes/`
2. Implement INode interface with multi-tenant support
3. Add to `index.js` exports
4. Restart Flowise container

### Testing
- Use Postman or curl to test SMEFlow API endpoints
- Validate tenant isolation with different tenant IDs
- Test African market configurations

## Troubleshooting

### Common Issues
1. **Tenant ID Missing**: Ensure all SMEFlow nodes have valid tenant UUID
2. **API Connection**: Verify SMEFlow API URL (default: http://smeflow:8000)
3. **Database Connection**: Check PostgreSQL connection in docker-compose
4. **Custom Nodes**: Restart Flowise container after node changes

### Logs
- Flowise logs: `docker-compose logs flowise`
- SMEFlow API logs: `docker-compose logs smeflow`
- Database logs: `docker-compose logs db`

## Integration with SMEFlow Components

### Agent System
- Direct integration with BaseAgent, AutomatorAgent, MentorAgent, SupervisorAgent
- LLM cost tracking via Langfuse
- Performance metrics via SigNoz

### Workflow Engine
- LangGraph stateful workflows
- Industry-specific templates
- Self-healing and recovery mechanisms

### Security Framework
- Keycloak authentication integration
- Cerbos policy-based authorization
- Multi-factor authentication support

## Deployment

### Development (Docker Compose)
```bash
docker-compose up flowise
```

### Production (Kubernetes)
- Use Helm charts for scalable deployment
- Configure persistent volumes for workflow data
- Set up load balancing for high availability

## Support

For issues and feature requests, please refer to the main SMEFlow documentation or create an issue in the repository.
