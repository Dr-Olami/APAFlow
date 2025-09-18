const { INode, INodeData, INodeParams } = require('flowise-components');
const axios = require('axios');

class SMEFlowAfricanIntegrations {
    constructor() {
        this.label = 'SMEFlow African Market Integrations'
        this.name = 'smeflowAfricanIntegrations'
        this.version = 1.0
        this.type = 'SMEFlowAfricanIntegrations'
        this.icon = 'africa.svg'
        this.category = 'SMEFlow Integrations'
        this.description = 'Connect with African market services (M-Pesa, Paystack, Africa\'s Talking, local APIs)'
        this.baseClasses = [this.type]

        this.inputs = [
            {
                label: 'Integration Type',
                name: 'integrationType',
                type: 'options',
                options: [
                    {
                        label: 'M-Pesa Payment',
                        name: 'mpesa_payment'
                    },
                    {
                        label: 'Paystack Payment',
                        name: 'paystack_payment'
                    },
                    {
                        label: 'Flutterwave Payment',
                        name: 'flutterwave_payment'
                    },
                    {
                        label: 'Africa\'s Talking SMS',
                        name: 'africas_talking_sms'
                    },
                    {
                        label: 'WhatsApp Business API',
                        name: 'whatsapp_business'
                    },
                    {
                        label: 'Jumia API',
                        name: 'jumia_api'
                    },
                    {
                        label: 'Nigerian Bank Verification',
                        name: 'nigeria_bvn'
                    },
                    {
                        label: 'Kenya KRA Tax API',
                        name: 'kenya_kra'
                    },
                    {
                        label: 'South Africa SARS',
                        name: 'south_africa_sars'
                    },
                    {
                        label: 'Local Banking APIs',
                        name: 'local_banking'
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
                placeholder: 'Enter tenant UUID',
                description: 'Multi-tenant isolation identifier'
            },
            {
                label: 'Integration Configuration',
                name: 'integrationConfig',
                type: 'json',
                placeholder: '{"api_key": "your_api_key", "environment": "sandbox", "callback_url": "https://your-app.com/callback"}',
                description: 'Integration-specific configuration and credentials'
            },
            {
                label: 'Transaction Data',
                name: 'transactionData',
                type: 'json',
                placeholder: '{"amount": 1000, "currency": "KES", "phone": "+254700000000", "reference": "TXN123"}',
                description: 'Transaction or operation data'
            },
            {
                label: 'Local Settings',
                name: 'localSettings',
                type: 'json',
                placeholder: '{"language": "sw", "timezone": "Africa/Nairobi", "currency_format": "KES"}',
                description: 'Local market settings and preferences',
                optional: true
            },
            {
                label: 'Compliance Configuration',
                name: 'complianceConfig',
                type: 'json',
                placeholder: '{"data_residency": true, "audit_logging": true, "regulatory_compliance": ["cbn", "popia"]}',
                description: 'Compliance and regulatory settings',
                optional: true
            },
            {
                label: 'SMEFlow API URL',
                name: 'apiUrl',
                type: 'string',
                default: 'http://smeflow:8000',
                description: 'SMEFlow API endpoint'
            },
            {
                label: 'API Key',
                name: 'apiKey',
                type: 'password',
                placeholder: 'Enter SMEFlow API key',
                optional: true
            }
        ]
    }

    async init(nodeData) {
        const integrationType = nodeData.inputs?.integrationType || 'mpesa_payment'
        const country = nodeData.inputs?.country || 'nigeria'
        const tenantId = nodeData.inputs?.tenantId
        const integrationConfig = nodeData.inputs?.integrationConfig
        const transactionData = nodeData.inputs?.transactionData
        const localSettings = nodeData.inputs?.localSettings
        const complianceConfig = nodeData.inputs?.complianceConfig
        const apiUrl = nodeData.inputs?.apiUrl || 'http://smeflow:8000'
        const apiKey = nodeData.inputs?.apiKey

        if (!tenantId) {
            throw new Error('Tenant ID is required for multi-tenant isolation')
        }

        if (!integrationConfig) {
            throw new Error('Integration configuration is required')
        }

        try {
            // Parse configurations
            const config = JSON.parse(integrationConfig || '{}')
            const transaction = JSON.parse(transactionData || '{}')
            const local = JSON.parse(localSettings || '{}')
            const compliance = JSON.parse(complianceConfig || '{}')
            
            // Default local settings by country
            const countryDefaults = {
                nigeria: {
                    currency: 'NGN',
                    timezone: 'Africa/Lagos',
                    languages: ['en', 'ha', 'yo', 'ig'],
                    phone_format: '+234',
                    business_hours: '08:00-18:00',
                    payment_methods: ['paystack', 'flutterwave', 'bank_transfer'],
                    regulatory_bodies: ['cbn', 'cac'],
                    tax_system: 'firs'
                },
                kenya: {
                    currency: 'KES',
                    timezone: 'Africa/Nairobi',
                    languages: ['en', 'sw'],
                    phone_format: '+254',
                    business_hours: '08:00-17:00',
                    payment_methods: ['mpesa', 'airtel_money', 'bank_transfer'],
                    regulatory_bodies: ['cbk', 'kra'],
                    tax_system: 'kra'
                },
                south_africa: {
                    currency: 'ZAR',
                    timezone: 'Africa/Johannesburg',
                    languages: ['en', 'af', 'zu', 'xh'],
                    phone_format: '+27',
                    business_hours: '08:00-17:00',
                    payment_methods: ['eft', 'card_payment', 'instant_eft'],
                    regulatory_bodies: ['sarb', 'sars'],
                    tax_system: 'sars'
                },
                ghana: {
                    currency: 'GHS',
                    timezone: 'Africa/Accra',
                    languages: ['en', 'tw', 'ak'],
                    phone_format: '+233',
                    business_hours: '08:00-17:00',
                    payment_methods: ['mtn_momo', 'vodafone_cash', 'bank_transfer'],
                    regulatory_bodies: ['bog', 'gra'],
                    tax_system: 'gra'
                }
            }

            const defaultLocal = countryDefaults[country] || countryDefaults.nigeria
            const finalLocal = { ...defaultLocal, ...local }
            
            // Default compliance configuration
            const defaultCompliance = {
                data_residency: true,
                audit_logging: true,
                encryption_required: true,
                regulatory_compliance: finalLocal.regulatory_bodies,
                pci_dss_required: integrationType.includes('payment'),
                gdpr_compliance: true,
                local_data_protection: true,
                transaction_monitoring: true,
                fraud_detection: true,
                aml_compliance: integrationType.includes('payment')
            }

            const finalCompliance = { ...defaultCompliance, ...compliance }
            
            // Integration-specific configurations
            const integrationDefaults = {
                mpesa_payment: {
                    environment: 'sandbox',
                    business_short_code: '',
                    passkey: '',
                    callback_url: '',
                    timeout: 30,
                    supported_currencies: ['KES'],
                    min_amount: 1,
                    max_amount: 300000
                },
                paystack_payment: {
                    environment: 'test',
                    callback_url: '',
                    webhook_url: '',
                    supported_currencies: ['NGN', 'GHS', 'ZAR', 'USD'],
                    channels: ['card', 'bank', 'ussd', 'qr', 'mobile_money']
                },
                africas_talking_sms: {
                    environment: 'sandbox',
                    username: '',
                    sender_id: '',
                    supported_countries: ['KE', 'UG', 'TZ', 'RW', 'MW', 'ZM']
                },
                whatsapp_business: {
                    phone_number_id: '',
                    business_account_id: '',
                    webhook_verify_token: '',
                    supported_message_types: ['text', 'media', 'template', 'interactive']
                }
            }

            const integrationDefault = integrationDefaults[integrationType] || {}
            const finalConfig = { ...integrationDefault, ...config }
            
            // Prepare headers with tenant isolation
            const headers = {
                'Content-Type': 'application/json',
                'X-Tenant-ID': tenantId,
                'X-Integration-Type': integrationType,
                'X-Country': country
            }
            
            if (apiKey) {
                headers['Authorization'] = `Bearer ${apiKey}`
            }

            // Create African integration request
            const integrationRequest = {
                integration_type: integrationType,
                country: country,
                tenant_id: tenantId,
                config: {
                    ...finalConfig,
                    local_settings: finalLocal,
                    compliance_config: finalCompliance,
                    integration_metadata: {
                        source: 'flowise',
                        node_id: nodeData.instance?.id,
                        workflow_id: nodeData.instance?.chatflowId,
                        timestamp: new Date().toISOString()
                    }
                },
                transaction_data: transaction,
                context: {
                    integration_type: integrationType,
                    country: country,
                    african_market: true,
                    multi_tenant: true,
                    source: 'flowise_african_integrations_node'
                }
            }

            // Execute African integration via SMEFlow API
            const response = await axios.post(
                `${apiUrl}/api/v1/integrations/african-market/execute`,
                integrationRequest,
                { headers, timeout: 60000 }
            )

            return {
                success: true,
                integration_type: integrationType,
                country: country,
                integration_id: response.data.integration_id,
                transaction_id: response.data.transaction_id,
                result: response.data.result,
                transaction_status: response.data.transaction_status,
                payment_reference: response.data.payment_reference,
                confirmation_code: response.data.confirmation_code,
                fees_charged: response.data.fees_charged,
                exchange_rate: response.data.exchange_rate,
                local_amount: response.data.local_amount,
                processing_time: response.data.processing_time,
                compliance_status: response.data.compliance_status,
                audit_trail: response.data.audit_trail,
                next_steps: response.data.next_steps,
                webhook_data: response.data.webhook_data,
                tenant_id: tenantId,
                local_settings: finalLocal,
                compliance_config: finalCompliance,
                timestamp: new Date().toISOString()
            }

        } catch (error) {
            console.error('SMEFlow African Integrations execution error:', error)
            
            return {
                success: false,
                integration_type: integrationType,
                country: country,
                error: error.message,
                error_code: error.response?.status,
                error_details: error.response?.data,
                tenant_id: tenantId,
                timestamp: new Date().toISOString(),
                retry_recommended: error.response?.status >= 500,
                suggested_action: 'Check integration configuration and credentials'
            }
        }
    }
}

module.exports = { nodeClass: SMEFlowAfricanIntegrations }
