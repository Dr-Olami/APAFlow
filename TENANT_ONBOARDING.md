# SMEFlow Tenant Onboarding System

## Overview

The SMEFlow Tenant Onboarding System provides a streamlined, automated process for SME businesses to register, configure, and start using the platform within 15 minutes. This system supports multi-tenant isolation, African market optimizations, and white-label branding.

## Onboarding Flow Architecture

### Phase 1: Business Registration (3-5 minutes)

#### 1.1 Initial Registration Form
```
Business Information:
├── Company Name (required)
├── Industry Selection (dropdown with SME categories)
├── Business Size (1-10, 11-50, 51-200 employees)
├── Primary Location (African countries + cities)
├── Business Registration Number (optional)
└── Website URL (optional)

Owner/Admin Details:
├── Full Name (required)
├── Email Address (required, becomes admin login)
├── Phone Number (with country code selector)
├── Preferred Language (50+ languages including African)
├── Role/Title in Business
└── Password (with strength requirements)

Regional Preferences:
├── Primary Currency (NGN, KES, ZAR, USD, EUR)
├── Timezone (African timezones)
├── Business Hours (local time)
├── Preferred Communication Channels
└── Compliance Requirements (GDPR, POPIA, CBN)
```

#### 1.2 Plan Selection
```
Freemium Tiers:
├── Starter (Free)
│   ├── 1 admin user
│   ├── 3 basic workflows
│   ├── 100 monthly executions
│   └── Community support
├── Professional ($15/month)
│   ├── 5 team members
│   ├── Unlimited workflows
│   ├── 1,000 monthly executions
│   ├── African market integrations
│   └── Email support
└── Enterprise ($50/month)
    ├── Unlimited users
    ├── Custom branding
    ├── 10,000+ executions
    ├── Priority support
    └── Compliance features
```

### Phase 2: Automated Provisioning (1-2 minutes)

#### 2.1 Infrastructure Setup
```python
# Tenant Provisioning Service
class TenantProvisioningService:
    def provision_tenant(self, registration_data):
        # 1. Create tenant database schema
        tenant_id = self.create_tenant_schema(registration_data)
        
        # 2. Setup Keycloak realm for authentication
        realm_config = {
            'realm': f'smeflow-{tenant_id}',
            'enabled': True,
            'sslRequired': 'external',
            'registrationAllowed': False,
            'loginWithEmailAllowed': True,
            'duplicateEmailsAllowed': False
        }
        realm_id = self.keycloak_admin.create_realm(realm_config)
        
        # 3. Create Flowise workspace
        workspace_config = {
            'name': registration_data.company_name,
            'tenant_id': tenant_id,
            'isolation_level': 'strict',
            'region': registration_data.location
        }
        workspace_id = self.flowise_api.create_workspace(workspace_config)
        
        # 4. Initialize Cerbos policies
        self.setup_tenant_policies(tenant_id, registration_data.plan)
        
        # 5. Create default branding configuration
        self.initialize_branding(tenant_id, registration_data)
        
        return {
            'tenant_id': tenant_id,
            'workspace_id': workspace_id,
            'realm_id': realm_id,
            'dashboard_url': f'https://{tenant_id}.smeflow.com'
        }
```

#### 2.2 Database Schema Creation
```sql
-- Tenant-specific schema creation
CREATE SCHEMA IF NOT EXISTS tenant_{tenant_id};

-- Core tenant configuration
CREATE TABLE tenant_{tenant_id}.tenant_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    location VARCHAR(100),
    currency_code VARCHAR(3) DEFAULT 'USD',
    timezone VARCHAR(50),
    language_code VARCHAR(5) DEFAULT 'en',
    plan_type VARCHAR(20) DEFAULT 'starter',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Branding configuration
CREATE TABLE tenant_{tenant_id}.branding_config (
    tenant_id UUID REFERENCES tenant_{tenant_id}.tenant_config(id),
    logo_url TEXT,
    primary_color VARCHAR(7) DEFAULT '#1976d2',
    secondary_color VARCHAR(7) DEFAULT '#dc004e',
    accent_color VARCHAR(7) DEFAULT '#ff9800',
    font_family VARCHAR(100) DEFAULT 'Roboto',
    custom_domain VARCHAR(255),
    favicon_url TEXT,
    welcome_message TEXT,
    footer_text TEXT,
    custom_css TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User management
CREATE TABLE tenant_{tenant_id}.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'member',
    status VARCHAR(20) DEFAULT 'active',
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Phase 3: Branding Customization (5-10 minutes)

#### 3.1 Brand Configuration Wizard
```
Step 1: Visual Identity
├── Logo Upload (SVG, PNG, JPG - max 2MB)
├── Favicon Upload (ICO, PNG - 32x32px)
├── Color Palette Selection
│   ├── Primary Color (brand main color)
│   ├── Secondary Color (accent/CTA color)
│   ├── Background Colors (light/dark themes)
│   └── Text Colors (headings, body, links)
└── Typography Selection
    ├── Heading Font (Google Fonts integration)
    ├── Body Font (optimized for African languages)
    └── Font Sizes (responsive scaling)

Step 2: Domain Configuration
├── Subdomain Selection (company-name.smeflow.com)
├── Custom Domain Setup (optional - Enterprise)
├── SSL Certificate Provisioning
└── DNS Configuration Guide

Step 3: Localization
├── Primary Language Selection
├── Currency Display Format
├── Date/Time Format
├── Number Format (thousands separator)
├── Address Format (country-specific)
└── Phone Number Format
```

#### 3.2 Dashboard Layout Customization
```
Navigation Customization:
├── Menu Structure (drag-and-drop reordering)
├── Feature Visibility (show/hide modules)
├── Quick Actions (customizable shortcuts)
└── Widget Selection (dashboard cards)

Welcome Experience:
├── Onboarding Checklist (customizable steps)
├── Welcome Message (personalized greeting)
├── Getting Started Videos (localized)
├── Template Recommendations (industry-specific)
└── Integration Suggestions (African market focus)
```

### Phase 4: Team Setup & Collaboration (5-10 minutes)

#### 4.1 Team Member Invitation System
```python
# Team Invitation Service
class TeamInvitationService:
    def invite_team_member(self, tenant_id, inviter_id, invitation_data):
        # Create invitation record
        invitation = {
            'id': str(uuid.uuid4()),
            'tenant_id': tenant_id,
            'inviter_id': inviter_id,
            'email': invitation_data.email,
            'role': invitation_data.role,
            'permissions': self.get_role_permissions(invitation_data.role),
            'status': 'pending',
            'expires_at': datetime.now() + timedelta(days=7),
            'created_at': datetime.now()
        }
        
        # Send branded invitation email
        email_template = self.get_branded_template(tenant_id, 'team_invitation')
        self.email_service.send_invitation(invitation, email_template)
        
        return invitation
```

#### 4.2 Role-Based Access Control
```
Admin Role:
├── Full tenant configuration access
├── Team management (invite/remove users)
├── Billing and subscription management
├── Branding and customization
├── Integration configuration
└── Compliance and audit access

Manager Role:
├── Workflow creation and editing
├── Team member workflow assignment
├── Performance monitoring
├── Limited integration access
└── Report generation

Member Role:
├── Assigned workflow execution
├── Personal dashboard access
├── Basic reporting
└── Profile management

Viewer Role:
├── Read-only dashboard access
├── Report viewing
└── Basic analytics
```

### Phase 5: Initial Workflow Setup (10-15 minutes)

#### 5.1 Industry-Specific Template Selection
```
Template Categories by Industry:

Retail/E-commerce:
├── Product Recommendation Engine
├── Inventory Management Automation
├── Customer Support Chatbot
├── Order Processing Workflow
└── Marketing Campaign Automation

Service Businesses:
├── Appointment Booking System
├── Customer Onboarding Flow
├── Service Delivery Tracking
├── Feedback Collection Automation
└── Rebooking Campaigns

Logistics/Delivery:
├── Shipment Tracking System
├── Route Optimization
├── Delivery Notification Automation
├── Customer Communication Flow
└── Performance Analytics

Financial Services:
├── KYC Automation
├── Transaction Monitoring
├── Compliance Reporting
├── Customer Onboarding
└── Risk Assessment Workflow
```

#### 5.2 African Market Integration Setup
```
Payment Integration Wizard:
├── M-Pesa Configuration (Kenya, Tanzania)
├── Paystack Setup (Nigeria, Ghana)
├── Flutterwave Integration (Multi-country)
├── Local Bank API Connections
└── Currency Conversion Setup

Communication Channels:
├── WhatsApp Business API
├── SMS Gateway Configuration
├── Email Service Setup (localized templates)
├── Voice Calling Integration (LiveKit)
└── Social Media Connections

Compliance Configuration:
├── GDPR Compliance Setup (if applicable)
├── POPIA Configuration (South Africa)
├── CBN Requirements (Nigeria)
├── Data Residency Settings
└── Audit Trail Configuration
```

## Technical Implementation

### Database Architecture
```
Multi-Tenant Isolation Strategy:
├── Schema-per-tenant (PostgreSQL schemas)
├── Row-Level Security (RLS) policies
├── Encrypted tenant data storage
├── Backup and recovery per tenant
└── Performance monitoring per tenant
```

### API Endpoints
```
POST /api/v1/tenants/register
├── Creates new tenant registration
├── Validates business information
├── Initiates provisioning process
└── Returns tenant credentials

GET /api/v1/tenants/{tenant_id}/onboarding-status
├── Returns current onboarding progress
├── Lists completed/pending steps
├── Provides next action recommendations
└── Tracks completion percentage

PUT /api/v1/tenants/{tenant_id}/branding
├── Updates tenant branding configuration
├── Validates uploaded assets
├── Regenerates branded templates
└── Updates CDN assets

POST /api/v1/tenants/{tenant_id}/team/invite
├── Sends team member invitations
├── Creates pending user records
├── Generates invitation tokens
└── Sends branded email notifications
```

### Security Considerations
```
Data Protection:
├── Tenant data encryption at rest
├── API rate limiting per tenant
├── Audit logging for all actions
├── GDPR/POPIA compliance features
└── Secure credential storage

Access Control:
├── Multi-factor authentication (MFA)
├── Role-based permissions
├── Session management
├── API key management
└── OAuth 2.0 integration
```

## Success Metrics

### Onboarding KPIs
- **Time to First Workflow**: < 15 minutes
- **Completion Rate**: > 85% of registrations complete onboarding
- **User Activation**: > 70% create first workflow within 24 hours
- **Team Adoption**: > 60% of invited team members join within 48 hours

### Business Impact
- **Setup Efficiency**: 90% reduction in manual setup time
- **User Satisfaction**: > 4.5/5 rating for onboarding experience
- **Support Reduction**: 50% fewer onboarding-related support tickets
- **Conversion Rate**: > 25% of free users upgrade within 30 days

## African Market Optimizations

### Localization Features
```
Language Support:
├── English (primary)
├── Swahili (Kenya, Tanzania, Uganda)
├── Hausa (Nigeria, Niger, Ghana)
├── Yoruba (Nigeria, Benin)
├── Igbo (Nigeria)
├── Amharic (Ethiopia)
├── Arabic (North Africa)
├── French (West/Central Africa)
├── Portuguese (Angola, Mozambique)
└── Afrikaans (South Africa)

Cultural Adaptations:
├── Business naming conventions
├── Address formats per country
├── Phone number formats
├── Business registration requirements
├── Tax identification formats
└── Banking information formats
```

### Network Optimization
```
Low-Bandwidth Considerations:
├── Progressive image loading
├── Compressed asset delivery
├── Offline-capable onboarding steps
├── Mobile-first responsive design
└── Reduced data usage tracking
```

## Integration with Existing Systems

### Flowise Integration
- Automatic workspace creation with tenant branding
- Custom node availability based on plan tier
- Template library filtered by industry and region
- Multi-language workflow builder interface

### Keycloak Authentication
- Tenant-specific realms for complete isolation
- SSO integration with popular African business tools
- MFA enforcement based on compliance requirements
- User federation with existing business directories

### Observability Integration
- Tenant-specific dashboards in SigNoz
- Cost tracking per tenant in Langfuse
- Performance monitoring with tenant context
- Compliance audit trails in centralized logging

This onboarding system ensures SME businesses can quickly start benefiting from SMEFlow's automation capabilities while maintaining the security, compliance, and customization requirements of a multi-tenant platform.
