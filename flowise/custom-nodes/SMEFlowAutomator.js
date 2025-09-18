const { INode, INodeData, INodeParams } = require('flowise-components');
const axios = require('axios');

class SMEFlowAutomator {
    constructor() {
        this.label = 'SMEFlow Automator Agent'
        this.name = 'smeflowAutomator'
        this.version = 1.0
        this.type = 'SMEFlowAutomator'
        this.icon = 'automator.svg'
        this.category = 'SMEFlow Agents'
        this.description = 'Execute automated tasks with African market integrations (M-Pesa, APIs, data processing)'
        this.baseClasses = [this.type]

        this.inputs = [
            {
                label: 'Task Type',
                name: 'taskType',
                type: 'options',
                options: [
                    {
                        label: 'API Integration',
                        name: 'api_integration'
                    },
                    {
                        label: 'Data Processing',
                        name: 'data_processing'
                    },
                    {
                        label: 'Payment Processing (M-Pesa)',
                        name: 'payment_mpesa'
                    },
                    {
                        label: 'SMS/WhatsApp Notification',
                        name: 'notification_sms'
                    },
                    {
                        label: 'Email Automation',
                        name: 'email_automation'
                    },
                    {
                        label: 'File Processing',
                        name: 'file_processing'
                    },
                    {
                        label: 'Database Operations',
                        name: 'database_ops'
                    },
                    {
                        label: 'Web Scraping',
                        name: 'web_scraping'
                    }
                ],
                default: 'api_integration'
            },
            {
                label: 'Tenant ID',
                name: 'tenantId',
                type: 'string',
                placeholder: 'Enter tenant UUID',
                description: 'Multi-tenant isolation identifier'
            },
            {
                label: 'Task Configuration',
                name: 'taskConfig',
                type: 'json',
                placeholder: '{"endpoint": "https://api.example.com", "method": "POST", "headers": {}}',
                description: 'Task-specific configuration parameters'
            },
            {
                label: 'Input Data',
                name: 'inputData',
                type: 'json',
                placeholder: '{"customer_id": "12345", "amount": 1000, "currency": "NGN"}',
                description: 'Input data for task execution'
            },
            {
                label: 'African Market Settings',
                name: 'marketSettings',
                type: 'json',
                placeholder: '{"region": "nigeria", "currency": "NGN", "phone_format": "+234"}',
                description: 'African market-specific settings',
                optional: true
            },
            {
                label: 'Tools Configuration',
                name: 'toolsConfig',
                type: 'json',
                placeholder: '{"tools": ["api_client", "data_validator", "payment_processor"]}',
                description: 'Available tools for the automator agent',
                optional: true
            },
            {
                label: 'Retry Configuration',
                name: 'retryConfig',
                type: 'json',
                placeholder: '{"max_retries": 3, "retry_delay": 5, "exponential_backoff": true}',
                description: 'Retry settings for failed tasks',
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
        const taskType = nodeData.inputs?.taskType || 'api_integration'
        const tenantId = nodeData.inputs?.tenantId
        const taskConfig = nodeData.inputs?.taskConfig
        const inputData = nodeData.inputs?.inputData
        const marketSettings = nodeData.inputs?.marketSettings
        const toolsConfig = nodeData.inputs?.toolsConfig
        const retryConfig = nodeData.inputs?.retryConfig
        const apiUrl = nodeData.inputs?.apiUrl || 'http://smeflow:8000'
        const apiKey = nodeData.inputs?.apiKey

        if (!tenantId) {
            throw new Error('Tenant ID is required for multi-tenant isolation')
        }

        try {
            // Parse configurations
            const config = JSON.parse(taskConfig || '{}')
            const input = JSON.parse(inputData || '{}')
            const africanMarketSettings = JSON.parse(marketSettings || '{}')
            const tools = JSON.parse(toolsConfig || '{}')
            const retry = JSON.parse(retryConfig || '{}')
            
            // Default African market optimizations
            const defaultMarketSettings = {
                region: 'nigeria',
                currency: 'NGN',
                timezone: 'Africa/Lagos',
                languages: ['en', 'ha', 'yo', 'ig'],
                phone_format: '+234',
                business_hours: {
                    start: '08:00',
                    end: '18:00',
                    timezone: 'Africa/Lagos'
                },
                payment_methods: ['mpesa', 'paystack', 'flutterwave'],
                local_apis: {
                    sms_gateway: 'africas_talking',
                    payment_gateway: 'paystack',
                    bank_verification: 'mono'
                }
            }

            const finalMarketSettings = { ...defaultMarketSettings, ...africanMarketSettings }
            
            // Default tools for automator agents
            const defaultTools = {
                tools: [
                    'api_client',
                    'data_validator', 
                    'payment_processor',
                    'notification_sender',
                    'file_processor',
                    'database_client',
                    'web_scraper'
                ],
                african_integrations: {
                    mpesa: finalMarketSettings.payment_methods.includes('mpesa'),
                    paystack: finalMarketSettings.payment_methods.includes('paystack'),
                    africas_talking: finalMarketSettings.local_apis.sms_gateway === 'africas_talking'
                }
            }

            const finalTools = { ...defaultTools, ...tools }
            
            // Default retry configuration
            const defaultRetry = {
                max_retries: 3,
                retry_delay: 5,
                exponential_backoff: true,
                retry_on_status: [500, 502, 503, 504, 429]
            }

            const finalRetry = { ...defaultRetry, ...retry }
            
            // Prepare headers with tenant isolation
            const headers = {
                'Content-Type': 'application/json',
                'X-Tenant-ID': tenantId,
                'X-Agent-Type': 'automator'
            }
            
            if (apiKey) {
                headers['Authorization'] = `Bearer ${apiKey}`
            }

            // Create automator agent execution request
            const automatorRequest = {
                type: 'automator',
                task_type: taskType,
                config: {
                    ...config,
                    tenant_id: tenantId,
                    market_settings: finalMarketSettings,
                    tools: finalTools,
                    retry_config: finalRetry,
                    execution_context: {
                        source: 'flowise',
                        node_id: nodeData.instance?.id,
                        workflow_id: nodeData.instance?.chatflowId,
                        timestamp: new Date().toISOString()
                    }
                },
                input: input,
                context: {
                    task_type: taskType,
                    african_market: true,
                    multi_tenant: true,
                    source: 'flowise_automator_node'
                }
            }

            // Execute automator agent via SMEFlow API
            const response = await axios.post(
                `${apiUrl}/api/v1/agents/automator/execute`,
                automatorRequest,
                { headers, timeout: 60000 }
            )

            return {
                success: true,
                agent_type: 'automator',
                task_type: taskType,
                agent_id: response.data.agent_id,
                execution_id: response.data.execution_id,
                result: response.data.result,
                processed_data: response.data.processed_data,
                api_calls_made: response.data.api_calls_made,
                tools_used: response.data.tools_used,
                cost_usd: response.data.cost_usd,
                tokens_used: response.data.tokens_used,
                execution_time: response.data.execution_time,
                retry_attempts: response.data.retry_attempts,
                tenant_id: tenantId,
                market_settings: finalMarketSettings,
                timestamp: new Date().toISOString()
            }

        } catch (error) {
            console.error('SMEFlow Automator Agent execution error:', error)
            
            return {
                success: false,
                agent_type: 'automator',
                task_type: taskType,
                error: error.message,
                error_code: error.response?.status,
                tenant_id: tenantId,
                timestamp: new Date().toISOString(),
                retry_recommended: error.response?.status >= 500
            }
        }
    }
}

module.exports = { nodeClass: SMEFlowAutomator }
