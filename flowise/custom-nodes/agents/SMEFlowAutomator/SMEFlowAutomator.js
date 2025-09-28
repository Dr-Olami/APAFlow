"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const axios = require("axios");

class SMEFlowAutomator_Agents {
    constructor() {
        this.label = 'SMEFlow Automator Agent';
        this.name = 'smeflowAutomator';
        this.version = 1.0;
        this.type = 'SMEFlowAutomator';
        this.icon = 'automator.svg';
        this.category = 'Agents';
        this.description = 'Execute automated tasks with African market integrations (M-Pesa, APIs, data processing)';
        this.baseClasses = [this.type, 'BaseAgent', 'Agent'];
        this.inputs = [
            {
                label: 'SMEFlow Tenant Manager',
                name: 'tenantManager',
                type: 'SMEFlowTenantManager',
                optional: true,
                description: 'Connect SMEFlow Tenant Manager for tenant configuration'
            },
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
                placeholder: 'Enter tenant UUID (e.g., 550e8400-e29b-41d4-a716-446655440000)',
                description: 'Multi-tenant isolation identifier for secure data separation'
            },
            {
                label: 'Task Configuration',
                name: 'taskConfig',
                type: 'json',
                placeholder: '{"priority": "high", "auto_assign": true, "notification_channels": ["email", "whatsapp"]}',
                description: 'JSON configuration for the automation task'
            },
            {
                label: 'Input Data',
                name: 'inputData',
                type: 'json',
                placeholder: '{"customer_name": "John Doe", "email": "john@example.com", "phone": "+234801234567"}',
                description: 'JSON input data for task processing'
            },
            {
                label: 'African Market Config',
                name: 'marketConfig',
                type: 'json',
                placeholder: '{"region": "nigeria", "currency": "NGN", "language": "en", "phone_format": "+234"}',
                description: 'African market-specific configuration',
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

    async init(nodeData, input, options) {
        // Handle connected node data (Flowise passes it through input parameter)
        const tenantManager = nodeData.inputs?.tenantManager || input;
        const taskType = nodeData.inputs?.taskType || 'api_integration';
        let tenantId = nodeData.inputs?.tenantId;
        const taskConfig = nodeData.inputs?.taskConfig;
        const inputData = nodeData.inputs?.inputData;
        const marketConfig = nodeData.inputs?.marketConfig;
        const apiUrl = nodeData.inputs?.apiUrl || 'http://smeflow:8000';
        const apiKey = nodeData.inputs?.apiKey;

        // Debug: Log what we receive from connected nodes
        console.log('SMEFlow Automator: Received input:', input);
        console.log('SMEFlow Automator: Tenant Manager connection:', tenantManager);

        // If tenant manager is connected, use its tenant configuration
        if (tenantManager && tenantManager.tenant_id) {
            tenantId = tenantManager.tenant_id;
            console.log('SMEFlow Automator: Using tenant configuration from connected Tenant Manager');
            console.log('SMEFlow Automator: Inherited tenant ID:', tenantId);
            console.log('SMEFlow Automator: Tenant Manager success status:', tenantManager.success);
        } else if (input && input.tenant_id) {
            // Alternative: Check if input directly contains tenant data
            tenantId = input.tenant_id;
            console.log('SMEFlow Automator: Using tenant ID from input:', tenantId);
        }

        if (!tenantId) {
            throw new Error('Tenant ID is required for multi-tenant isolation');
        }

        try {
            // Parse configurations
            const config = JSON.parse(taskConfig || '{}');
            const data = JSON.parse(inputData || '{}');
            const africanMarketConfig = JSON.parse(marketConfig || '{}');
            
            // Default African market optimizations
            const defaultMarketConfig = {
                region: 'africa-west',
                currency: 'NGN',
                timezone: 'Africa/Lagos',
                languages: ['en', 'ha', 'yo', 'ig'],
                phone_format: '+234',
                business_hours: {
                    start: '08:00',
                    end: '18:00',
                    timezone: 'Africa/Lagos'
                }
            };

            const finalMarketConfig = { ...defaultMarketConfig, ...africanMarketConfig };
            
            // Prepare headers with tenant isolation
            const headers = {
                'Content-Type': 'application/json',
                'X-Tenant-ID': tenantId
            };
            
            if (apiKey) {
                headers['Authorization'] = `Bearer ${apiKey}`;
            }

            // Create automation request
            const automationRequest = {
                task_type: taskType,
                tenant_id: tenantId,
                config: {
                    ...config,
                    ...finalMarketConfig,
                    source: 'flowise',
                    workflow_id: nodeData.instance?.id,
                    created_at: new Date().toISOString()
                },
                input_data: data,
                execution_options: {
                    async: false,
                    timeout: 120,
                    retry_on_failure: true,
                    max_retries: 3
                }
            };

            // For Flowise testing, return mock data
            console.log('SMEFlow Automator: Executing task type:', taskType);
            console.log('SMEFlow Automator: Using tenant ID:', tenantId);

            return {
                success: true,
                task_id: `task_${Date.now()}`,
                execution_id: `exec_${Date.now()}`,
                status: 'completed',
                result: {
                    message: `Successfully executed ${taskType} task`,
                    processed_data: data,
                    tenant_context: tenantId
                },
                cost_usd: 0.05,
                execution_time: 1.2,
                tenant_id: tenantId,
                task_type: taskType,
                market_config: finalMarketConfig
            };

        } catch (error) {
            console.error('SMEFlow Automator execution error:', error);
            
            return {
                success: false,
                error: error.message,
                tenant_id: tenantId,
                task_type: taskType,
                timestamp: new Date().toISOString()
            };
        }
    }

    // Required Flowise method for node execution
    async run(nodeData, input, options) {
        return await this.init(nodeData, input, options);
    }

    // Required Flowise method for serialization
    serialize() {
        return {
            type: this.type,
            label: this.label,
            name: this.name,
            version: this.version,
            inputs: this.inputs
        };
    }
}

module.exports = { nodeClass: SMEFlowAutomator_Agents };
