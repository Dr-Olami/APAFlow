"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const axios = require("axios");

class SMEFlowSupervisor_Agents {
    constructor() {
        this.label = 'SMEFlow Supervisor Agent';
        this.name = 'smeflowSupervisor';
        this.version = 1.0;
        this.type = 'SMEFlowSupervisor';
        this.icon = 'supervisor.svg';
        this.category = 'Agents';
        this.description = 'Orchestrate multi-agent workflows with escalation handling and quality assurance';
        this.baseClasses = [this.type, 'Agent'];
        this.inputs = [
            {
                label: 'Supervision Type',
                name: 'supervisionType',
                type: 'options',
                options: [
                    {
                        label: 'Workflow Orchestration',
                        name: 'workflow_orchestration',
                        description: 'Coordinate multiple agents in a workflow'
                    },
                    {
                        label: 'Quality Assurance',
                        name: 'quality_assurance',
                        description: 'Monitor and validate agent outputs'
                    },
                    {
                        label: 'Escalation Handling',
                        name: 'escalation_handling',
                        description: 'Handle complex cases requiring human intervention'
                    },
                    {
                        label: 'Performance Monitoring',
                        name: 'performance_monitoring',
                        description: 'Monitor agent performance and optimization'
                    },
                    {
                        label: 'Conflict Resolution',
                        name: 'conflict_resolution',
                        description: 'Resolve conflicts between agents or processes'
                    }
                ],
                default: 'workflow_orchestration'
            },
            {
                label: 'Tenant ID',
                name: 'tenantId',
                type: 'string',
                placeholder: 'Enter tenant UUID (e.g., 550e8400-e29b-41d4-a716-446655440000)',
                description: 'Multi-tenant isolation identifier'
            },
            {
                label: 'Workflow Configuration',
                name: 'workflowConfig',
                type: 'json',
                placeholder: '{"agents": ["automator", "mentor"], "escalation_rules": {}, "quality_thresholds": {}}',
                description: 'JSON configuration for workflow supervision'
            },
            {
                label: 'Supervision Context',
                name: 'supervisionContext',
                type: 'json',
                placeholder: '{"workflow_id": "wf-123", "current_step": 1, "previous_results": []}',
                description: 'Context information for supervision decisions'
            },
            {
                label: 'Quality Thresholds',
                name: 'qualityThresholds',
                type: 'json',
                placeholder: '{"accuracy": 0.95, "response_time": 30, "customer_satisfaction": 0.9}',
                description: 'Quality thresholds for supervision decisions',
                optional: true
            },
            {
                label: 'Escalation Rules',
                name: 'escalationRules',
                type: 'json',
                placeholder: '{"auto_escalate": true, "escalation_threshold": 0.8, "human_review_required": false}',
                description: 'Rules for escalating issues to human supervisors',
                optional: true
            },
            {
                label: 'African Market Config',
                name: 'marketConfig',
                type: 'json',
                placeholder: '{"region": "nigeria", "currency": "NGN", "business_hours": "08:00-18:00"}',
                description: 'African market-specific supervision configuration',
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
        const supervisionType = nodeData.inputs?.supervisionType || 'workflow_orchestration';
        const tenantId = nodeData.inputs?.tenantId;
        const workflowConfig = nodeData.inputs?.workflowConfig;
        const supervisionContext = nodeData.inputs?.supervisionContext;
        const qualityThresholds = nodeData.inputs?.qualityThresholds;
        const escalationRules = nodeData.inputs?.escalationRules;
        const marketConfig = nodeData.inputs?.marketConfig;
        const apiUrl = nodeData.inputs?.apiUrl || 'http://smeflow:8000';
        const apiKey = nodeData.inputs?.apiKey;

        if (!tenantId) {
            throw new Error('Tenant ID is required for multi-tenant isolation');
        }

        if (!workflowConfig) {
            throw new Error('Workflow Configuration is required for supervision');
        }

        // Validate UUID format
        const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
        if (!uuidRegex.test(tenantId)) {
            throw new Error('Tenant ID must be a valid UUID format');
        }

        try {
            // Parse configurations
            const config = JSON.parse(workflowConfig || '{}');
            const context = JSON.parse(supervisionContext || '{}');
            const thresholds = JSON.parse(qualityThresholds || '{}');
            const escalation = JSON.parse(escalationRules || '{}');
            const africanMarketConfig = JSON.parse(marketConfig || '{}');
            
            // Default African market optimizations
            const defaultMarketConfig = {
                region: 'africa-west',
                currency: 'NGN',
                timezone: 'Africa/Lagos',
                languages: ['en', 'ha', 'yo', 'ig'],
                business_hours: {
                    start: '08:00',
                    end: '18:00',
                    timezone: 'Africa/Lagos'
                },
                escalation_preferences: {
                    human_review_hours: '08:00-17:00',
                    auto_escalate_after_hours: true,
                    cultural_sensitivity: 'high'
                }
            };

            const finalMarketConfig = { ...defaultMarketConfig, ...africanMarketConfig };
            
            // Default quality thresholds
            const defaultThresholds = {
                accuracy: 0.95,
                response_time: 30,
                customer_satisfaction: 0.9,
                cost_efficiency: 0.8
            };

            const finalThresholds = { ...defaultThresholds, ...thresholds };
            
            // Default escalation rules
            const defaultEscalation = {
                auto_escalate: true,
                escalation_threshold: 0.8,
                human_review_required: false,
                max_auto_retries: 3
            };

            const finalEscalation = { ...defaultEscalation, ...escalation };
            
            // Prepare headers with tenant isolation
            const headers = {
                'Content-Type': 'application/json',
                'X-Tenant-ID': tenantId
            };
            
            if (apiKey) {
                headers['Authorization'] = `Bearer ${apiKey}`;
            }

            // Create supervision request
            const supervisionRequest = {
                supervision_type: supervisionType,
                tenant_id: tenantId,
                workflow_config: {
                    ...config,
                    ...finalMarketConfig,
                    source: 'flowise',
                    workflow_id: nodeData.instance?.id,
                    created_at: new Date().toISOString()
                },
                supervision_context: {
                    ...context,
                    source: 'flowise',
                    timestamp: new Date().toISOString()
                },
                quality_thresholds: finalThresholds,
                escalation_rules: finalEscalation,
                execution_options: {
                    async: false,
                    timeout: 300,
                    retry_on_failure: true,
                    max_retries: 3
                }
            };

            // Execute supervision via SMEFlow API
            const response = await axios.post(
                `${apiUrl}/api/v1/supervisor/execute`,
                supervisionRequest,
                { headers, timeout: 300000 }
            );

            return {
                success: true,
                supervision_type: supervisionType,
                supervisor_id: response.data.supervisor_id,
                session_id: response.data.session_id,
                supervision_result: response.data.result,
                quality_score: response.data.quality_score,
                escalation_triggered: response.data.escalation_triggered,
                recommendations: response.data.recommendations,
                next_actions: response.data.next_actions,
                performance_metrics: response.data.performance_metrics,
                cost_usd: response.data.cost_usd,
                execution_time: response.data.execution_time,
                tenant_id: tenantId,
                market_config: finalMarketConfig,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            console.error('SMEFlow Supervisor execution error:', error);
            
            return {
                success: false,
                supervision_type: supervisionType,
                error: error.message,
                error_code: error.response?.status || 'UNKNOWN',
                tenant_id: tenantId,
                escalation_required: true,
                timestamp: new Date().toISOString()
            };
        }
    }
}

module.exports = { nodeClass: SMEFlowSupervisor_Agents };
