const { INode, INodeData, INodeParams } = require('flowise-components');
const axios = require('axios');

class SMEFlowTenantManager {
    constructor() {
        this.label = 'SMEFlow Tenant Manager'
        this.name = 'smeflowTenantManager'
        this.version = 1.0
        this.type = 'SMEFlowTenantManager'
        this.icon = 'smeflow.svg'
        this.category = 'SMEFlow'
        this.description = 'Manage multi-tenant workspace isolation and tenant-specific configurations'
        this.baseClasses = [this.type]

        this.inputs = [
            {
                label: 'Operation',
                name: 'operation',
                type: 'options',
                options: [
                    {
                        label: 'Get Tenant Info',
                        name: 'get_tenant'
                    },
                    {
                        label: 'List Tenant Agents',
                        name: 'list_agents'
                    },
                    {
                        label: 'List Tenant Workflows',
                        name: 'list_workflows'
                    },
                    {
                        label: 'Get Usage Statistics',
                        name: 'get_usage'
                    },
                    {
                        label: 'Validate Tenant Access',
                        name: 'validate_access'
                    }
                ],
                default: 'get_tenant'
            },
            {
                label: 'Tenant ID',
                name: 'tenantId',
                type: 'string',
                placeholder: 'Enter tenant UUID',
                description: 'Multi-tenant isolation identifier'
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
        const operation = nodeData.inputs?.operation || 'get_tenant'
        const tenantId = nodeData.inputs?.tenantId
        const apiUrl = nodeData.inputs?.apiUrl || 'http://smeflow:8000'
        const apiKey = nodeData.inputs?.apiKey

        if (!tenantId) {
            throw new Error('Tenant ID is required for multi-tenant operations')
        }

        try {
            // Prepare headers with tenant isolation
            const headers = {
                'Content-Type': 'application/json',
                'X-Tenant-ID': tenantId
            }
            
            if (apiKey) {
                headers['Authorization'] = `Bearer ${apiKey}`
            }

            let endpoint = ''
            let method = 'GET'

            switch (operation) {
                case 'get_tenant':
                    endpoint = `/api/v1/tenants/${tenantId}`
                    break
                case 'list_agents':
                    endpoint = `/api/v1/agents`
                    break
                case 'list_workflows':
                    endpoint = `/api/v1/workflows`
                    break
                case 'get_usage':
                    endpoint = `/api/v1/tenants/${tenantId}/usage`
                    break
                case 'validate_access':
                    endpoint = `/api/v1/tenants/${tenantId}/validate`
                    break
                default:
                    throw new Error(`Unknown operation: ${operation}`)
            }

            // Execute API request
            const response = await axios({
                method,
                url: `${apiUrl}${endpoint}`,
                headers,
                timeout: 10000
            })

            return {
                success: true,
                operation: operation,
                tenant_id: tenantId,
                data: response.data,
                timestamp: new Date().toISOString()
            }

        } catch (error) {
            console.error('SMEFlow Tenant Manager error:', error)
            
            return {
                success: false,
                operation: operation,
                tenant_id: tenantId,
                error: error.message,
                timestamp: new Date().toISOString()
            }
        }
    }
}

module.exports = { nodeClass: SMEFlowTenantManager }
