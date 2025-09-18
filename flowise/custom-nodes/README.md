# SMEFlow Custom Flowise Nodes

This package contains custom Flowise nodes for SMEFlow platform integration, providing multi-tenant African market automation capabilities.

## Overview

SMEFlow custom nodes enable seamless integration between Flowise workflows and the SMEFlow agent system, with specialized support for African market operations including M-Pesa payments, local APIs, and regional compliance.

## Available Nodes

### Core Agent Nodes

#### 1. SMEFlow Automator Agent
- **Purpose**: Execute automated tasks with African market integrations
- **Features**: 
  - API integrations and data processing
  - M-Pesa and Paystack payment processing
  - SMS/WhatsApp notifications via Africa's Talking
  - File processing and database operations
  - Web scraping and automation tasks
- **Category**: SMEFlow Agents

#### 2. SMEFlow Mentor Agent
- **Purpose**: Provide business guidance and recommendations
- **Features**:
  - Industry-specific expertise (Consulting, Healthcare, Manufacturing, etc.)
  - African market business strategy guidance
  - Financial planning and compliance advisory
  - Risk assessment and growth planning
  - Multi-level expertise (Beginner to Expert)
- **Category**: SMEFlow Agents

#### 3. SMEFlow Supervisor Agent
- **Purpose**: Orchestrate multi-agent workflows with quality assurance
- **Features**:
  - Workflow orchestration and coordination
  - Quality assurance and performance monitoring
  - Escalation handling and decision making
  - Compliance oversight for African regulations
  - Multi-agent resource coordination
- **Category**: SMEFlow Agents

### Integration Nodes

#### 4. SMEFlow African Market Integrations
- **Purpose**: Connect with African market services and APIs
- **Features**:
  - M-Pesa payment processing (Kenya)
  - Paystack and Flutterwave payments (Nigeria, Ghana, South Africa)
  - Africa's Talking SMS and voice services
  - WhatsApp Business API integration
  - Local banking and tax system APIs
  - Country-specific compliance and regulations
- **Category**: SMEFlow Integrations

### Management Nodes

#### 5. SMEFlow Workflow (Enhanced)
- **Purpose**: Execute LangGraph workflows with industry templates
- **Features**:
  - Industry-specific workflow templates
  - African market optimizations
  - Multi-tenant execution
  - Real-time monitoring and cost tracking
- **Category**: SMEFlow

#### 6. SMEFlow Tenant Manager
- **Purpose**: Manage multi-tenant workspace isolation
- **Features**:
  - Tenant information and validation
  - Usage statistics and monitoring
  - Agent and workflow listing
  - Access control and security
- **Category**: SMEFlow

#### 7. SMEFlow Agent (Generic)
- **Purpose**: Generic agent execution with basic functionality
- **Features**:
  - Basic agent execution
  - Multi-tenant support
  - African market configurations
- **Category**: SMEFlow

## Installation

1. Copy the custom nodes to your Flowise custom nodes directory:
```bash
cp -r flowise/custom-nodes/* /path/to/flowise/packages/components/nodes/
```

2. Install dependencies:
```bash
cd /path/to/flowise/packages/components/nodes/
npm install
```

3. Restart Flowise to load the new nodes.

## Configuration

### Multi-Tenant Setup

All nodes require a **Tenant ID** (UUID format) for proper multi-tenant isolation:
```json
{
  "tenantId": "550e8400-e29b-41d4-a716-446655440000"
}
```

### African Market Configuration

Configure regional settings for optimal African market support:
```json
{
  "region": "nigeria",
  "currency": "NGN",
  "timezone": "Africa/Lagos",
  "languages": ["en", "ha", "yo", "ig"],
  "phone_format": "+234"
}
```

### API Configuration

Connect to SMEFlow backend services:
```json
{
  "apiUrl": "http://smeflow:8000",
  "apiKey": "your_smeflow_api_key"
}
```

## Usage Examples

### 1. Automator Agent - M-Pesa Payment Processing

```json
{
  "taskType": "payment_mpesa",
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "taskConfig": {
    "business_short_code": "174379",
    "passkey": "your_mpesa_passkey",
    "callback_url": "https://your-app.com/mpesa/callback"
  },
  "inputData": {
    "amount": 1000,
    "phone": "+254700000000",
    "account_reference": "ORDER123",
    "transaction_desc": "Payment for services"
  }
}
```

### 2. Mentor Agent - Business Strategy Guidance

```json
{
  "guidanceType": "business_strategy",
  "industrySector": "fintech",
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "businessContext": {
    "company_size": "small",
    "revenue": 50000,
    "employees": 5,
    "location": "Lagos"
  },
  "question": "How can we expand our fintech services to rural areas in Nigeria?"
}
```

### 3. Supervisor Agent - Workflow Orchestration

```json
{
  "supervisionType": "workflow_orchestration",
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "workflowConfig": {
    "workflow_id": "customer_onboarding",
    "steps": ["verification", "kyc", "account_creation"],
    "dependencies": {"kyc": ["verification"]}
  },
  "agentCoordination": {
    "agents": [
      {"type": "automator", "id": "verifier"},
      {"type": "mentor", "id": "advisor"}
    ]
  }
}
```

## Supported African Markets

### Countries
- Nigeria (NGN) - Paystack, Flutterwave, CBN compliance
- Kenya (KES) - M-Pesa, Airtel Money, KRA integration
- South Africa (ZAR) - EFT, SARB compliance, POPIA
- Ghana (GHS) - MTN MoMo, Vodafone Cash, GRA integration
- Uganda (UGX) - Mobile Money, Bank of Uganda
- Tanzania (TZS) - M-Pesa, Airtel Money
- Rwanda (RWF) - Mobile Money, BNR compliance
- Ethiopia (ETB) - CBE Birr, National Bank integration

### Payment Methods
- Mobile Money: M-Pesa, Airtel Money, MTN MoMo, Vodafone Cash
- Payment Gateways: Paystack, Flutterwave, Pesapal
- Banking: Local bank APIs, SWIFT integration
- Digital Wallets: Various local providers

### Compliance & Regulations
- Nigeria: CBN (Central Bank of Nigeria), CAC, FIRS
- Kenya: CBK (Central Bank of Kenya), KRA
- South Africa: SARB, SARS, POPIA compliance
- Ghana: BOG (Bank of Ghana), GRA

## Error Handling

All nodes implement comprehensive error handling with:
- Retry mechanisms with exponential backoff
- Detailed error reporting and logging
- Tenant-specific error isolation
- Compliance audit trails
- Graceful degradation for network issues

## Security Features

- Multi-tenant data isolation
- Encrypted credential storage
- API key validation and rotation
- Audit logging for all operations
- Regional data residency compliance
- Input sanitization and validation

## Development

### Adding New Nodes

1. Create a new node class extending the base structure
2. Implement required methods: `constructor()` and `init()`
3. Add validation using the SMEFlowValidation utility
4. Update `index.js` to export the new node
5. Add tests and documentation

### Testing

Run the validation script to test node configurations:
```bash
npm run validate
```

### Linting

Check code quality:
```bash
npm run lint
```

## Support

For issues and support:
- GitHub Issues: https://github.com/smeflow/smeflow-platform/issues
- Documentation: https://docs.smeflow.com
- Community: https://community.smeflow.com

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

---

**SMEFlow Team** - Empowering African SMEs through intelligent automation
