"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const axios = require("axios");

class SMEFlowWorkflow_Chains {
    constructor() {
        this.label = 'SMEFlow Workflow';
        this.name = 'smeflowWorkflow';
        this.version = 1.0;
        this.type = 'SMEFlowWorkflow';
        this.icon = 'workflow.svg';
        this.category = 'SMEFlow';
        this.description = 'Execute SMEFlow LangGraph workflows with industry templates and African market optimization';
        this.baseClasses = [this.type];
        this.inputs = [
            {
                label: 'Workflow Template',
                name: 'workflowTemplate',
                type: 'options',
                options: [
                    {
                        label: 'Consulting - Lead Qualification',
                        name: 'consulting_lead_qualification',
                        description: 'Qualify leads for consulting services'
                    },
                    {
                        label: 'Salon/Spa - Service Booking',
                        name: 'salon_service_booking',
                        description: 'Handle salon and spa service bookings'
                    },
                    {
                        label: 'Healthcare - Patient Verification',
                        name: 'healthcare_patient_verification',
                        description: 'Verify patient information and insurance'
                    },
                    {
                        label: 'Manufacturing - Resource Planning',
                        name: 'manufacturing_resource_planning',
                        description: 'Plan manufacturing resources and capacity'
                    },
                    {
                        label: 'Marketing Campaign',
                        name: 'marketing_campaign',
                        description: 'Execute marketing campaigns with analytics'
                    },
                    {
                        label: 'ERP Integration',
                        name: 'erp_integration',
                        description: 'Integrate with ERP systems and processes'
                    },
                    {
                        label: 'Compliance Audit',
                        name: 'compliance_audit',
                        description: 'Automated compliance auditing workflows'
                    },
                    {
                        label: 'Customer Support',
                        name: 'customer_support',
                        description: '360-degree customer support workflows'
                    }
                ],
                default: 'consulting_lead_qualification'
            },
            {
                label: 'Tenant ID',
                name: 'tenantId',
                type: 'string',
                placeholder: 'Enter tenant UUID (e.g., 550e8400-e29b-41d4-a716-446655440000)',
                description: 'Multi-tenant isolation identifier'
            },
            {
                label: 'Workflow Input Data',
                name: 'workflowData',
                type: 'json',
                placeholder: '{"customer_name": "John Doe", "service_type": "consultation", "budget": 50000}',
                description: 'JSON input data for workflow execution'
            },
            {
                label: 'Workflow Configuration',
                name: 'workflowConfig',
                type: 'json',
                placeholder: '{"async": false, "timeout": 300, "retry_on_failure": true, "max_retries": 3}',
                description: 'Workflow execution configuration options',
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
                label: 'Industry Context',
                name: 'industryContext',
                type: 'json',
                placeholder: '{"industry": "consulting", "company_size": "small", "target_market": "african_smes"}',
                description: 'Industry-specific context for workflow customization',
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
        const workflowTemplate = nodeData.inputs?.workflowTemplate || 'consulting_lead_qualification';
        const tenantId = nodeData.inputs?.tenantId;
        const workflowData = nodeData.inputs?.workflowData;
        const workflowConfig = nodeData.inputs?.workflowConfig;
        const marketConfig = nodeData.inputs?.marketConfig;
        const industryContext = nodeData.inputs?.industryContext;
        const apiUrl = nodeData.inputs?.apiUrl || 'http://smeflow:8000';
        const apiKey = nodeData.inputs?.apiKey;

        if (!tenantId) {
            throw new Error('Tenant ID is required for multi-tenant isolation');
        }

        if (!workflowData) {
            throw new Error('Workflow Input Data is required for workflow execution');
        }

        // Validate UUID format
        const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
        if (!uuidRegex.test(tenantId)) {
            throw new Error('Tenant ID must be a valid UUID format');
        }

        try {
            // Parse configurations
            const inputData = JSON.parse(workflowData || '{}');
            const config = JSON.parse(workflowConfig || '{}');
            const africanMarketConfig = JSON.parse(marketConfig || '{}');
            const industry = JSON.parse(industryContext || '{}');
            
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
                payment_methods: ['paystack', 'flutterwave', 'bank_transfer'],
                cultural_context: {
                    greeting_style: 'formal',
                    business_etiquette: 'respectful',
                    communication_preference: 'direct'
                }
            };

            const finalMarketConfig = { ...defaultMarketConfig, ...africanMarketConfig };
            
            // Default workflow configuration
            const defaultWorkflowConfig = {
                async: false,
                timeout: 300,
                retry_on_failure: true,
                max_retries: 3,
                self_healing: true,
                checkpoint_enabled: true
            };

            const finalWorkflowConfig = { ...defaultWorkflowConfig, ...config };
            
            // Prepare headers with tenant isolation
            const headers = {
                'Content-Type': 'application/json',
                'X-Tenant-ID': tenantId
            };
            
            if (apiKey) {
                headers['Authorization'] = `Bearer ${apiKey}`;
            }

            // Create workflow execution request
            const workflowRequest = {
                template: workflowTemplate,
                tenant_id: tenantId,
                input_data: inputData,
                config: {
                    ...finalMarketConfig,
                    ...industry,
                    source: 'flowise',
                    workflow_id: nodeData.instance?.id,
                    created_at: new Date().toISOString()
                },
                execution_options: finalWorkflowConfig
            };

            // Execute workflow via SMEFlow API
            const response = await axios.post(
                `${apiUrl}/api/v1/workflows/execute`,
                workflowRequest,
                { headers, timeout: (finalWorkflowConfig.timeout + 60) * 1000 }
            );

            return {
                success: true,
                workflow_template: workflowTemplate,
                workflow_id: response.data.workflow_id,
                execution_id: response.data.execution_id,
                status: response.data.status,
                result: response.data.result,
                steps_completed: response.data.steps_completed,
                steps_total: response.data.steps_total,
                checkpoints: response.data.checkpoints,
                performance_metrics: response.data.performance_metrics,
                cost_usd: response.data.cost_usd,
                tokens_used: response.data.tokens_used,
                execution_time: response.data.execution_time,
                tenant_id: tenantId,
                market_config: finalMarketConfig,
                industry_context: industry,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            console.error('SMEFlow Workflow execution error:', error);
            
            return {
                success: false,
                workflow_template: workflowTemplate,
                error: error.message,
                error_code: error.response?.status || 'UNKNOWN',
                tenant_id: tenantId,
                timestamp: new Date().toISOString()
            };
        }
    }
}

module.exports = { nodeClass: SMEFlowWorkflow_Chains };
