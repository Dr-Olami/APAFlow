"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const axios = require("axios");

class SMEFlowAgent_Agents {
    constructor() {
        this.label = 'SMEFlow Agent';
        this.name = 'smeflowAgent';
        this.version = 1.0;
        this.type = 'SMEFlowAgent';
        this.icon = 'agent.svg';
        this.category = 'SMEFlow';
        this.description = 'Execute SMEFlow agent workflows with multi-tenant support and African market optimization';
        this.baseClasses = [this.type, 'Agent'];
        this.inputs = [
            {
                label: 'Agent Type',
                name: 'agentType',
                type: 'options',
                options: [
                    {
                        label: 'Automator',
                        name: 'automator',
                        description: 'Execute automated tasks and processes'
                    },
                    {
                        label: 'Mentor',
                        name: 'mentor',
                        description: 'Provide business guidance and recommendations'
                    },
                    {
                        label: 'Supervisor',
                        name: 'supervisor',
                        description: 'Orchestrate workflows and handle escalations'
                    }
                ],
                default: 'automator'
            },
            {
                label: 'Tenant ID',
                name: 'tenantId',
                type: 'string',
                placeholder: 'Enter tenant UUID (e.g., 550e8400-e29b-41d4-a716-446655440000)',
                description: 'Multi-tenant isolation identifier for secure data separation'
            },
            {
                label: 'Agent Configuration',
                name: 'agentConfig',
                type: 'json',
                placeholder: '{"name": "MyAgent", "description": "Agent description", "expertise": "business_strategy"}',
                description: 'JSON configuration for the agent behavior and capabilities'
            },
            {
                label: 'Input Message',
                name: 'inputMessage',
                type: 'string',
                placeholder: 'Enter message or task for agent processing',
                description: 'The input message or task for the agent to process'
            },
            {
                label: 'Context Data',
                name: 'contextData',
                type: 'json',
                placeholder: '{"customer_info": {}, "business_context": {}, "previous_interactions": []}',
                description: 'Additional context data for agent decision making',
                optional: true
            },
            {
                label: 'African Market Config',
                name: 'marketConfig',
                type: 'json',
                placeholder: '{"region": "nigeria", "currency": "NGN", "language": "en", "business_type": "consulting"}',
                description: 'African market-specific configuration and optimizations',
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
        const agentType = nodeData.inputs?.agentType || 'automator';
        const tenantId = nodeData.inputs?.tenantId;
        const agentConfig = nodeData.inputs?.agentConfig;
        const inputMessage = nodeData.inputs?.inputMessage;
        const contextData = nodeData.inputs?.contextData;
        const marketConfig = nodeData.inputs?.marketConfig;
        const apiUrl = nodeData.inputs?.apiUrl || 'http://smeflow:8000';
        const apiKey = nodeData.inputs?.apiKey;

        if (!tenantId) {
            throw new Error('Tenant ID is required for multi-tenant isolation');
        }

        if (!inputMessage) {
            throw new Error('Input Message is required for agent processing');
        }

        // Validate UUID format
        const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
        if (!uuidRegex.test(tenantId)) {
            throw new Error('Tenant ID must be a valid UUID format');
        }

        try {
            // Parse configurations
            const config = JSON.parse(agentConfig || '{}');
            const context = JSON.parse(contextData || '{}');
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
                },
                cultural_context: {
                    greeting_style: 'formal',
                    business_etiquette: 'respectful',
                    communication_preference: 'direct'
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

            // Create agent execution request
            const agentRequest = {
                type: agentType,
                tenant_id: tenantId,
                config: {
                    ...config,
                    ...finalMarketConfig,
                    source: 'flowise',
                    workflow_id: nodeData.instance?.id,
                    created_at: new Date().toISOString()
                },
                input: inputMessage,
                context: {
                    ...context,
                    source: 'flowise',
                    timestamp: new Date().toISOString(),
                    workflow_id: nodeData.instance?.id
                },
                execution_options: {
                    async: false,
                    timeout: 300,
                    retry_on_failure: true,
                    max_retries: 3
                }
            };

            // Execute agent via SMEFlow API
            const response = await axios.post(
                `${apiUrl}/api/v1/agents/execute`,
                agentRequest,
                { headers, timeout: 300000 }
            );

            return {
                success: true,
                agent_type: agentType,
                agent_id: response.data.agent_id,
                execution_id: response.data.execution_id,
                result: response.data.result,
                confidence_score: response.data.confidence_score,
                reasoning: response.data.reasoning,
                recommendations: response.data.recommendations,
                cost_usd: response.data.cost_usd,
                tokens_used: response.data.tokens_used,
                execution_time: response.data.execution_time,
                tenant_id: tenantId,
                market_config: finalMarketConfig,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            console.error('SMEFlow Agent execution error:', error);
            
            return {
                success: false,
                agent_type: agentType,
                error: error.message,
                error_code: error.response?.status || 'UNKNOWN',
                tenant_id: tenantId,
                timestamp: new Date().toISOString()
            };
        }
    }
}

module.exports = { nodeClass: SMEFlowAgent_Agents };
