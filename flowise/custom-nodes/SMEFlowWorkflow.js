const { INode, INodeData, INodeParams } = require('flowise-components');
const axios = require('axios');

class SMEFlowWorkflow {
    constructor() {
        this.label = 'SMEFlow Workflow'
        this.name = 'smeflowWorkflow'
        this.version = 1.0
        this.type = 'SMEFlowWorkflow'
        this.icon = 'smeflow.svg'
        this.category = 'SMEFlow'
        this.description = 'Execute SMEFlow LangGraph workflows with industry templates'
        this.baseClasses = [this.type]

        this.inputs = [
            {
                label: 'Workflow Template',
                name: 'workflowTemplate',
                type: 'options',
                options: [
                    {
                        label: 'Consulting - Lead Qualification',
                        name: 'consulting_lead_qualification'
                    },
                    {
                        label: 'Salon/Spa - Service Booking',
                        name: 'salon_service_booking'
                    },
                    {
                        label: 'Healthcare - Patient Verification',
                        name: 'healthcare_patient_verification'
                    },
                    {
                        label: 'Manufacturing - Resource Planning',
                        name: 'manufacturing_resource_planning'
                    },
                    {
                        label: 'Marketing Campaign',
                        name: 'marketing_campaign'
                    },
                    {
                        label: 'ERP Integration',
                        name: 'erp_integration'
                    },
                    {
                        label: 'Compliance Audit',
                        name: 'compliance_audit'
                    }
                ],
                default: 'consulting_lead_qualification'
            },
            {
                label: 'Tenant ID',
                name: 'tenantId',
                type: 'string',
                placeholder: 'Enter tenant UUID',
                description: 'Multi-tenant isolation identifier'
            },
            {
                label: 'Workflow Input Data',
                name: 'workflowData',
                type: 'json',
                placeholder: '{"customer_name": "John Doe", "service_type": "consultation"}',
                description: 'JSON input data for workflow execution'
            },
            {
                label: 'African Market Config',
                name: 'marketConfig',
                type: 'json',
                placeholder: '{"region": "nigeria", "currency": "NGN", "language": "en"}',
                description: 'African market-specific configuration',
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
        const workflowTemplate = nodeData.inputs?.workflowTemplate || 'consulting_lead_qualification'
        const tenantId = nodeData.inputs?.tenantId
        const workflowData = nodeData.inputs?.workflowData
        const marketConfig = nodeData.inputs?.marketConfig
        const apiUrl = nodeData.inputs?.apiUrl || 'http://smeflow:8000'
        const apiKey = nodeData.inputs?.apiKey

        if (!tenantId) {
            throw new Error('Tenant ID is required for multi-tenant isolation')
        }

        try {
            // Parse input data and market configuration
            const inputData = JSON.parse(workflowData || '{}')
            const africanMarketConfig = JSON.parse(marketConfig || '{}')
            
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
            }

            const finalMarketConfig = { ...defaultMarketConfig, ...africanMarketConfig }
            
            // Prepare headers with tenant isolation
            const headers = {
                'Content-Type': 'application/json',
                'X-Tenant-ID': tenantId
            }
            
            if (apiKey) {
                headers['Authorization'] = `Bearer ${apiKey}`
            }

            // Create workflow execution request
            const workflowRequest = {
                template: workflowTemplate,
                tenant_id: tenantId,
                input_data: inputData,
                config: {
                    ...finalMarketConfig,
                    source: 'flowise',
                    workflow_id: nodeData.instance?.id,
                    created_at: new Date().toISOString()
                },
                execution_options: {
                    async: false,
                    timeout: 300,
                    retry_on_failure: true,
                    max_retries: 3
                }
            }

            // Execute workflow via SMEFlow API
            const response = await axios.post(
                `${apiUrl}/api/v1/workflows/execute`,
                workflowRequest,
                { headers, timeout: 300000 }
            )

            return {
                success: true,
                workflow_id: response.data.workflow_id,
                execution_id: response.data.execution_id,
                status: response.data.status,
                result: response.data.result,
                steps_completed: response.data.steps_completed,
                cost_usd: response.data.cost_usd,
                execution_time: response.data.execution_time,
                tenant_id: tenantId,
                template: workflowTemplate,
                market_config: finalMarketConfig
            }

        } catch (error) {
            console.error('SMEFlow Workflow execution error:', error)
            
            return {
                success: false,
                error: error.message,
                tenant_id: tenantId,
                template: workflowTemplate,
                timestamp: new Date().toISOString()
            }
        }
    }
}

module.exports = { nodeClass: SMEFlowWorkflow }
