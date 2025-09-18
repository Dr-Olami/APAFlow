# SMEFlow - Agentic Process Automation Platform

## Project Overview

**SMEFlow** is a robust, scalable Agentic Process Automation (APA) platform tailored for Small and Medium Enterprises (SMEs) in emerging markets, with a strong focus on Africa. It's a multi-tenant, cloud-native solution that evolves from a monolithic architecture for rapid development to microservices for enterprise scalability.

### Core Identity
- **Target Market**: African SMEs (Nigeria, Kenya, South Africa, Ghana, Uganda, Tanzania, Rwanda, Ethiopia, Egypt, Morocco)
- **Business Model**: Freemium ($15-$50/month), targeting 20-40% cost reduction for SMEs
- **Languages**: 50+ languages including English, Swahili, Hausa, Yoruba, Igbo, Amharic, Arabic, French, Portuguese, Afrikaans, Zulu, Xhosa
- **Compliance**: GDPR, POPIA (South Africa), CBN (Nigeria Central Bank)

## Architecture

### Evolution Path
- **v0.1 Monolith MVP** (August 2025): Single codebase for rapid development
- **v1.0 Microservices** (Q1 2026): Strangler fig pattern migration for enterprise scalability

### Core Components
1. **Agent Layer**: Automator, Mentor, Supervisor agents using LangChain SDKs
2. **Workflow Engine**: LangGraph orchestration with self-healing and dynamic routing
3. **Integration Layer**: n8N with 400+ connectors for local systems and ERPs/CRMs
4. **Data Processing**: ProAgent-inspired structured/unstructured data analysis
5. **Compliance Logging**: Audit AI, Privacy Meter, Giskard risk scans
6. **Observability**: Langfuse/SigNoz with cost tracking
7. **Security**: Keycloak/Cerbos with governance hooks

### Multi-Tenancy
- **Isolation**: Separate databases/schemas (PostgreSQL)
- **Authentication**: Keycloak realms for RBAC
- **Scaling**: Support for 10K+ tenants in microservices phase

## Core Tools

### AI & Automation Stack
- **LangChain**: LLM agents and tool orchestration
- **LangGraph**: Workflow orchestration with self-healing
- **AutoGen**: Multi-agent conversations and coordination
- **ProAgent**: Process-centric automation framework
- **PyAutoGen**: Python-based agent development

### Integration & Workflow
- **Flowise**: No-code workflow builder (drag-and-drop UI)
- **n8N**: 400+ pre-built connectors and integrations
- **browser-use**: Web automation and RPA capabilities

### African Market Integrations
- **Payment**: M-Pesa, Paystack, Flutterwave
- **E-commerce**: Jumia API integration
- **Communication**: WhatsApp Business API
- **Social Media**: Multi-platform consistency system with AI content generation
- **Booking**: Cal.com integration
- **Voice**: LiveKit for real-time voice communication and calling
- **HITL**: Human-in-the-Loop framework for agent supervision

### Observability & Compliance
- **Monitoring**: Langfuse, SigNoz, Prometheus, Sentry
- **Logging**: Loki, Graylog, structured logging
- **Compliance**: Audit AI (bias detection), Privacy Meter, Giskard (risk scanning)
- **Security**: Keycloak (identity), Cerbos (authorization)

### Development & Deployment
- **Containerization**: Docker, Kubernetes
- **API Gateway**: Kong, Envoy
- **Database**: PostgreSQL (multi-tenant), Redis (caching/workflows)
- **Package Management**: uv (fast Python package installer)

## Features

### Ready-Made Templates
1. **Product Recommender** (Retail)
   - Impact: 20-30% admin time reduction
   - AI-powered recommendations with local market focus
   - WooCommerce integration
   - Shopify integration, 
   - Jumia integration, cultural relevance

2. **Local Discovery** (Services)
   - Impact: 45% booking increase
   - Hyperlocal trend analysis and social media automation
   - Location-aware for African cities

3. **360 Support Agent** (Customer Service)
   - Impact: 85% wait time reduction
   - Full customer context with voice handling
   - Multilingual support with cultural sensitivity

4. **Shipment Tracker** (Logistics)
   - Impact: 25% delay reduction
   - Real-time tracking with SMS notifications

5. **Invoice Auditor** (ERP/Finance)
   - Automated delay detection and vendor escalation
   - Compliance with local financial regulations

6. **Social Media Manager** (Marketing)
   - Impact: 60% content creation time reduction
   - Multi-platform brand consistency (Meta, TikTok, LinkedIn, Twitter, Instagram)
   - AI-powered content generation with African market optimization
   - Automated scheduling with timezone optimization
   - Keyword research and hashtag optimization in local languages

### Core Capabilities
- **No-Code Workflow Builder**: Drag-and-drop interface via Flowise
- **Multilingual AI Agents**: Support for African languages
- **Hyperlocal Intelligence**: Neighborhood trend analysis
- **Self-Healing Workflows**: Adaptive routing for system changes
- **Voice Automation**: Calls, reminders, and real-time communication
- **Compliance Suite**: Automated audits and regulatory adherence
- **Social Media Consistency**: Multi-platform brand management with AI content generation
- **Multi-Tenant Isolation**: Complete tenant separation for brand guidelines and preferences

### User Experience
- **Dashboard**: Flowise-based with Agent Builder
- **Onboarding**: Sign up at sme-flow.org or AWS Marketplace
- **Pricing Tiers**: Free tier and premium ($10-$50/month)
- **Monitoring**: Insights tab with Langfuse analytics

## Target Use Cases

### By Industry
- **Retail/E-commerce**: Inventory management, product recommendations (Lagos, Nairobi shops)
- **Logistics**: Delivery tracking, route optimization (Johannesburg, Accra services)
- **Marketing Agencies**: Campaign management, engagement automation (Addis Ababa, Dar es Salaam)
- **Service Businesses**: Booking automation, customer retention (Cape Town spas, Kampala clinics)
- **Fintech**: Compliance automation, transaction monitoring (Senegal startups)

### By Function
- **Discovery → Booking → Rebooking**: Complete customer funnel automation
- **ERP/CRM Integration**: Finance, HR, procurement automation
- **Customer Support**: 360-degree customer view with voice handling
- **Compliance Management**: Automated audits and regulatory reporting

## Extensibility

### Third-Party Development
- **Agent SDK + APIs**: Python-based SDKs for custom agent creation
- **MCP Schemas**: Model Context Protocol for standardized LLM-API communications
- **Integration Adapters**: Plugin system for external systems
- **Governance Hooks**: Custom policy engines for regulatory compliance

### Ecosystem
- **Open Source**: GitHub-hosted with community contributions
- **Marketplace**: AWS, Shopify deployment options
- **Partnerships**: Safaricom and other African telecom/fintech partnerships

## Success Metrics

### Quantified Outcomes
- **Admin Time Savings**: 20-30% (retail automation)
- **Booking Increase**: 45% (hyperlocal marketing)
- **Wait Time Reduction**: 85% (customer support)
- **Delay Reduction**: 25% (logistics tracking)
- **ROI Improvement**: 20% (marketing campaigns)
- **Cost Reduction**: 20-40% overall for SMEs

### Scaling Targets
- **v0.1**: 1-10 tenants per instance (monolith)
- **v1.0**: 10K+ tenants (microservices)
- **Enterprise**: 1M+ interactions, elastic scaling

## Development Context

When working with SMEFlow:
1. **Focus on African SME needs**: Local languages, currencies, cultural context
2. **Prioritize compliance**: GDPR, POPIA, CBN requirements
3. **Emphasize measurable outcomes**: Quantified business impact
4. **Consider extensibility**: Third-party integration capabilities
5. **Plan for scale**: Monolith-to-microservices evolution
6. **Maintain cost-effectiveness**: Freemium model sustainability

## Quick Start Commands

```bash
# Install dependencies with uv
uv pip install -r requirements.txt

# Start development environment
docker-compose up -d

# Run SMEFlow application
python -m smeflow.main

# Access services
# SMEFlow API: http://localhost:8000
# Flowise UI: http://localhost:3000
# n8n Workflows: http://localhost:5678
# SigNoz Observability: http://localhost:3301
# Keycloak Auth: http://localhost:8080
```

This template provides comprehensive context for AI assistants and developers working on SMEFlow, ensuring alignment with the platform's African SME focus, technical architecture, and business objectives.
