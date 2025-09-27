"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const axios = require("axios");

class SMEFlowAfricanIntegrations_Tools {
    constructor() {
        this.label = 'SMEFlow African Market Integrations';
        this.name = 'smeflowAfricanIntegrations';
        this.version = 1.0;
        this.type = 'SMEFlowAfricanIntegrations';
        this.icon = 'africa.svg';
        this.category = 'SMEFlow Integrations';
        this.description = 'Integrate with African market services: M-Pesa, Paystack, WhatsApp Business, local APIs';
        this.baseClasses = [this.type];
        this.inputs = [
            {
                label: 'SMEFlow Agent',
                name: 'smeflowAgent',
                type: 'SMEFlowAutomator',
                optional: true,
                description: 'Connect SMEFlow Automator Agent for task coordination'
            },
            {
                label: 'SMEFlow Tenant Manager',
                name: 'tenantManager',
                type: 'SMEFlowTenantManager',
                optional: true,
                description: 'Connect SMEFlow Tenant Manager for tenant configuration'
            },
            {
                label: 'Integration Type',
                name: 'integrationType',
                type: 'options',
                options: [
                    {
                        label: 'M-Pesa Payment',
                        name: 'mpesa_payment',
                        description: 'Safaricom M-Pesa mobile money integration'
                    },
                    {
                        label: 'Paystack Payment',
                        name: 'paystack_payment',
                        description: 'Paystack payment gateway integration'
                    },
                    {
                        label: 'Flutterwave Payment',
                        name: 'flutterwave_payment',
                        description: 'Flutterwave payment processing'
                    },
                    {
                        label: 'WhatsApp Business',
                        name: 'whatsapp_business',
                        description: 'WhatsApp Business API messaging'
                    },
                    {
                        label: 'Africa\'s Talking SMS',
                        name: 'africastalking_sms',
                        description: 'SMS gateway via Africa\'s Talking'
                    },
                    {
                        label: 'Jumia API',
                        name: 'jumia_api',
                        description: 'Jumia marketplace integration'
                    },
                    {
                        label: 'Local Banking API',
                        name: 'local_banking',
                        description: 'Local bank API integrations'
                    },
                    {
                        label: 'Government Services',
                        name: 'government_services',
                        description: 'Government API integrations (tax, compliance)'
                    }
                ],
                default: 'mpesa_payment'
            },
            {
                label: 'Country/Region',
                name: 'country',
                type: 'options',
                options: [
                    {
                        label: 'Nigeria',
                        name: 'nigeria'
                    },
                    {
                        label: 'Kenya',
                        name: 'kenya'
                    },
                    {
                        label: 'South Africa',
                        name: 'south_africa'
                    },
                    {
                        label: 'Ghana',
                        name: 'ghana'
                    },
                    {
                        label: 'Uganda',
                        name: 'uganda'
                    },
                    {
                        label: 'Tanzania',
                        name: 'tanzania'
                    },
                    {
                        label: 'Rwanda',
                        name: 'rwanda'
                    },
                    {
                        label: 'Ethiopia',
                        name: 'ethiopia'
                    }
                ],
                default: 'nigeria'
            },
            {
                label: 'Tenant ID',
                name: 'tenantId',
                type: 'string',
                placeholder: 'Enter tenant UUID (e.g., 550e8400-e29b-41d4-a716-446655440000)',
                description: 'Multi-tenant isolation identifier'
            },
            {
                label: 'Integration Configuration',
                name: 'integrationConfig',
                type: 'json',
                placeholder: '{"api_key": "your_api_key", "environment": "sandbox", "webhook_url": "https://your-domain.com/webhook"}',
                description: 'JSON configuration for the integration service'
            },
            {
                label: 'Transaction/Request Data',
                name: 'requestData',
                type: 'json',
                placeholder: '{"amount": 1000, "phone": "+254700000000", "account_reference": "ORDER123", "transaction_desc": "Payment for services"}',
                description: 'JSON data for the integration request (payment, message, etc.)'
            },
            {
                label: 'Market Localization',
                name: 'marketLocalization',
                type: 'json',
                placeholder: '{"currency": "KES", "language": "sw", "timezone": "Africa/Nairobi", "phone_format": "+254"}',
                description: 'Market-specific localization settings',
                optional: true
            },
            {
                label: 'Compliance Settings',
                name: 'complianceSettings',
                type: 'json',
                placeholder: '{"data_residency": "local", "audit_logging": true, "encryption": "aes256"}',
                description: 'Compliance and regulatory settings',
                optional: true
            },
            {
                label: 'SMEFlow API URL',
                name: 'apiUrl',
                type: 'string',
                default: 'http://smeflow:8000',
                description: 'SMEFlow API endpoint URL'
            },
            {
                label: 'API Key',
                name: 'apiKey',
                type: 'password',
                placeholder: 'Enter SMEFlow API key',
                description: 'Authentication key for SMEFlow API',
                optional: true
            }
        ];
    }

    async init(nodeData, _, options) {
        const smeflowAgent = nodeData.inputs?.smeflowAgent;
        const tenantManager = nodeData.inputs?.tenantManager;
        const integrationType = nodeData.inputs?.integrationType || 'mpesa_payment';
        const country = nodeData.inputs?.country || 'nigeria';
        let tenantId = nodeData.inputs?.tenantId;
        const integrationConfig = nodeData.inputs?.integrationConfig;
        const requestData = nodeData.inputs?.requestData;
        const marketLocalization = nodeData.inputs?.marketLocalization;
        const complianceSettings = nodeData.inputs?.complianceSettings;
        const apiUrl = nodeData.inputs?.apiUrl || 'http://smeflow:8000';
        const apiKey = nodeData.inputs?.apiKey;

        // If tenant manager is connected, use its tenant configuration
        if (tenantManager && tenantManager.success) {
            tenantId = tenantManager.tenant_id;
            console.log('SMEFlow African Integrations: Using tenant configuration from connected Tenant Manager');
        }

        // If SMEFlow agent is connected, inherit its context
        if (smeflowAgent && smeflowAgent.success) {
            tenantId = tenantId || smeflowAgent.tenant_id;
            console.log('SMEFlow African Integrations: Using context from connected SMEFlow Agent');
        }

        if (!tenantId) {
            throw new Error('Tenant ID is required for multi-tenant isolation');
        }

        if (!integrationConfig) {
            throw new Error('Integration Configuration is required');
        }

        if (!requestData) {
            throw new Error('Transaction/Request Data is required');
        }

        // Validate UUID format
        const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
        if (!uuidRegex.test(tenantId)) {
            throw new Error('Tenant ID must be a valid UUID format');
        }

        try {
            // Parse configurations
            const config = JSON.parse(integrationConfig || '{}');
            const data = JSON.parse(requestData || '{}');
            const localization = JSON.parse(marketLocalization || '{}');
            const compliance = JSON.parse(complianceSettings || '{}');
            
            // Default market localization by country
            const countryDefaults = {
                nigeria: {
                    currency: 'NGN',
                    language: 'en',
                    timezone: 'Africa/Lagos',
                    phone_format: '+234',
                    payment_methods: ['paystack', 'flutterwave', 'bank_transfer']
                },
                kenya: {
                    currency: 'KES',
                    language: 'sw',
                    timezone: 'Africa/Nairobi',
                    phone_format: '+254',
                    payment_methods: ['mpesa', 'paystack', 'bank_transfer']
                },
                south_africa: {
                    currency: 'ZAR',
                    language: 'en',
                    timezone: 'Africa/Johannesburg',
                    phone_format: '+27',
                    payment_methods: ['paystack', 'ozow', 'bank_transfer']
                },
                ghana: {
                    currency: 'GHS',
                    language: 'en',
                    timezone: 'Africa/Accra',
                    phone_format: '+233',
                    payment_methods: ['paystack', 'flutterwave', 'mtn_mobile_money']
                }
            };

            const defaultLocalization = countryDefaults[country] || countryDefaults.nigeria;
            const finalLocalization = { ...defaultLocalization, ...localization };
            
            // Default compliance settings
            const defaultCompliance = {
                data_residency: 'local',
                audit_logging: true,
                encryption: 'aes256',
                gdpr_compliant: true,
                local_regulations: true
            };

            const finalCompliance = { ...defaultCompliance, ...compliance };
            
            // Prepare headers with tenant isolation
            const headers = {
                'Content-Type': 'application/json',
                'X-Tenant-ID': tenantId,
                'X-Country': country,
                'X-Integration-Type': integrationType
            };
            
            if (apiKey) {
                headers['Authorization'] = `Bearer ${apiKey}`;
            }

            // Create integration request
            const integrationRequest = {
                integration_type: integrationType,
                country: country,
                tenant_id: tenantId,
                config: {
                    ...config,
                    ...finalLocalization,
                    source: 'flowise',
                    workflow_id: nodeData.instance?.id,
                    created_at: new Date().toISOString()
                },
                request_data: data,
                compliance_settings: finalCompliance,
                execution_options: {
                    async: false,
                    timeout: 120,
                    retry_on_failure: true,
                    max_retries: 3
                }
            };

            // Execute integration via SMEFlow API
            const response = await axios.post(
                `${apiUrl}/api/v1/integrations/african-markets/execute`,
                integrationRequest,
                { headers, timeout: 120000 }
            );

            return {
                success: true,
                integration_type: integrationType,
                country: country,
                integration_id: response.data.integration_id,
                transaction_id: response.data.transaction_id,
                status: response.data.status,
                result: response.data.result,
                provider_response: response.data.provider_response,
                fees: response.data.fees,
                exchange_rate: response.data.exchange_rate,
                local_amount: response.data.local_amount,
                confirmation_code: response.data.confirmation_code,
                cost_usd: response.data.cost_usd,
                execution_time: response.data.execution_time,
                tenant_id: tenantId,
                market_config: finalLocalization,
                compliance_status: response.data.compliance_status,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            console.error('SMEFlow African Integrations execution error:', error);
            
            return {
                success: false,
                integration_type: integrationType,
                country: country,
                error: error.message,
                error_code: error.response?.status || 'UNKNOWN',
                provider_error: error.response?.data?.provider_error,
                tenant_id: tenantId,
                timestamp: new Date().toISOString()
            };
        }
    }
}

module.exports = { nodeClass: SMEFlowAfricanIntegrations_Tools };
