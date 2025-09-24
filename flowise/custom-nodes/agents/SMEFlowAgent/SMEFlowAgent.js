const { INode, INodeData, INodeParams } = require('flowise-components');
const axios = require('axios');

class SMEFlowAgent {
    constructor() {
        this.label = 'SMEFlow Agent'
        this.name = 'smeflowAgent'
        this.version = 1.0
        this.type = 'SMEFlowAgent'
        this.icon = 'smeflow.svg'
        this.category = 'SMEFlow'
        this.description = 'Execute SMEFlow agent workflows with multi-tenant support'
        this.baseClasses = [this.type]

        this.inputs = [
            {
                label: 'Agent Type',
                name: 'agentType',
                type: 'options',
                options: [
                    {
                        label: 'Automator',
                        name: 'automator'
                    },
                    {
                        label: 'Mentor',
                        name: 'mentor'
                    },
                    {
                        label: 'Supervisor',
                        name: 'supervisor'
                    }
                ],
                default: 'automator'
            },
            {
                label: 'Tenant ID',
                name: 'tenantId',
                type: 'string',
                placeholder: 'Enter tenant UUID',
                description: 'Multi-tenant isolation identifier'
            },
            {
                label: 'Agent Configuration',
                name: 'agentConfig',
                type: 'json',
                placeholder: '{"name": "MyAgent", "description": "Agent description"}',
                description: 'JSON configuration for the agent'
            },
            {
                label: 'Input Message',
                name: 'inputMessage',
                type: 'string',
                placeholder: 'Enter message for agent processing'
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
        const agentType = nodeData.inputs?.agentType || 'automator'
        const tenantId = nodeData.inputs?.tenantId
        const agentConfig = nodeData.inputs?.agentConfig
        const inputMessage = nodeData.inputs?.inputMessage
        const apiUrl = nodeData.inputs?.apiUrl || 'http://smeflow:8000'
        const apiKey = nodeData.inputs?.apiKey

        if (!tenantId) {
            throw new Error('Tenant ID is required for multi-tenant isolation')
        }

        try {
            // Parse agent configuration
            const config = JSON.parse(agentConfig || '{}')
            
            // Prepare headers with tenant isolation
            const headers = {
                'Content-Type': 'application/json',
                'X-Tenant-ID': tenantId
            }
            
            if (apiKey) {
                headers['Authorization'] = `Bearer ${apiKey}`
            }

            // Create agent execution request
            const agentRequest = {
                type: agentType,
                config: {
                    ...config,
                    tenant_id: tenantId,
                    region: config.region || 'africa-west',
                    currency: config.currency || 'NGN',
                    timezone: config.timezone || 'Africa/Lagos',
                    languages: config.languages || ['en', 'ha', 'yo', 'ig']
                },
                input: inputMessage,
                context: {
                    source: 'flowise',
                    timestamp: new Date().toISOString(),
                    workflow_id: nodeData.instance?.id
                }
            }

            // Execute agent via SMEFlow API
            const response = await axios.post(
                `${apiUrl}/api/v1/agents/execute`,
                agentRequest,
                { headers, timeout: 30000 }
            )

            return {
                success: true,
                agent_id: response.data.agent_id,
                execution_id: response.data.execution_id,
                result: response.data.result,
                cost_usd: response.data.cost_usd,
                tokens_used: response.data.tokens_used,
                execution_time: response.data.execution_time,
                tenant_id: tenantId
            }

        } catch (error) {
            console.error('SMEFlow Agent execution error:', error)
            
            return {
                success: false,
                error: error.message,
                tenant_id: tenantId,
                timestamp: new Date().toISOString()
            }
        }
    }
}

module.exports = { nodeClass: SMEFlowAgent }
