const { INode, INodeData, INodeParams } = require('flowise-components');
const axios = require('axios');

class SMEFlowSupervisor {
    constructor() {
        this.label = 'SMEFlow Supervisor Agent'
        this.name = 'smeflowSupervisor'
        this.version = 1.0
        this.type = 'SMEFlowSupervisor'
        this.icon = 'supervisor.svg'
        this.category = 'SMEFlow Agents'
        this.description = 'Orchestrate multi-agent workflows with escalation handling and quality assurance'
        this.baseClasses = [this.type]

        this.inputs = [
            {
                label: 'Supervision Type',
                name: 'supervisionType',
                type: 'options',
                options: [
                    {
                        label: 'Workflow Orchestration',
                        name: 'workflow_orchestration'
                    },
                    {
                        label: 'Quality Assurance',
                        name: 'quality_assurance'
                    },
                    {
                        label: 'Escalation Handling',
                        name: 'escalation_handling'
                    },
                    {
                        label: 'Performance Monitoring',
                        name: 'performance_monitoring'
                    },
                    {
                        label: 'Resource Coordination',
                        name: 'resource_coordination'
                    },
                    {
                        label: 'Compliance Oversight',
                        name: 'compliance_oversight'
                    },
                    {
                        label: 'Multi-Agent Coordination',
                        name: 'multi_agent_coordination'
                    },
                    {
                        label: 'Decision Making',
                        name: 'decision_making'
                    }
                ],
                default: 'workflow_orchestration'
            },
            {
                label: 'Tenant ID',
                name: 'tenantId',
                type: 'string',
                placeholder: 'Enter tenant UUID',
                description: 'Multi-tenant isolation identifier'
            },
            {
                label: 'Workflow Configuration',
                name: 'workflowConfig',
                type: 'json',
                placeholder: '{"workflow_id": "wf-123", "steps": [], "dependencies": {}}',
                description: 'Workflow structure and configuration'
            },
            {
                label: 'Agent Coordination',
                name: 'agentCoordination',
                type: 'json',
                placeholder: '{"agents": [{"type": "automator", "id": "agent-1"}, {"type": "mentor", "id": "agent-2"}]}',
                description: 'Agents to coordinate and supervise'
            },
            {
                label: 'Escalation Rules',
                name: 'escalationRules',
                type: 'json',
                placeholder: '{"error_threshold": 3, "timeout_minutes": 30, "escalation_contacts": []}',
                description: 'Rules for escalation and intervention',
                optional: true
            },
            {
                label: 'Quality Criteria',
                name: 'qualityCriteria',
                type: 'json',
                placeholder: '{"accuracy_threshold": 0.95, "response_time_max": 30, "compliance_required": true}',
                description: 'Quality assurance criteria and thresholds',
                optional: true
            },
            {
                label: 'Decision Context',
                name: 'decisionContext',
                type: 'json',
                placeholder: '{"business_impact": "high", "urgency": "medium", "stakeholders": []}',
                description: 'Context for decision making and prioritization'
            },
            {
                label: 'African Market Compliance',
                name: 'marketCompliance',
                type: 'json',
                placeholder: '{"regions": ["nigeria", "kenya"], "regulations": ["cbn", "popia"], "local_requirements": true}',
                description: 'African market compliance requirements',
                optional: true
            },
            {
                label: 'Monitoring Configuration',
                name: 'monitoringConfig',
                type: 'json',
                placeholder: '{"metrics": ["performance", "cost", "quality"], "alerts": true, "reporting": "real_time"}',
                description: 'Performance monitoring and alerting setup',
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
        const supervisionType = nodeData.inputs?.supervisionType || 'workflow_orchestration'
        const tenantId = nodeData.inputs?.tenantId
        const workflowConfig = nodeData.inputs?.workflowConfig
        const agentCoordination = nodeData.inputs?.agentCoordination
        const escalationRules = nodeData.inputs?.escalationRules
        const qualityCriteria = nodeData.inputs?.qualityCriteria
        const decisionContext = nodeData.inputs?.decisionContext
        const marketCompliance = nodeData.inputs?.marketCompliance
        const monitoringConfig = nodeData.inputs?.monitoringConfig
        const apiUrl = nodeData.inputs?.apiUrl || 'http://smeflow:8000'
        const apiKey = nodeData.inputs?.apiKey

        if (!tenantId) {
            throw new Error('Tenant ID is required for multi-tenant isolation')
        }

        if (!workflowConfig && !agentCoordination) {
            throw new Error('Either workflow configuration or agent coordination is required')
        }

        try {
            // Parse configurations
            const workflow = JSON.parse(workflowConfig || '{}')
            const agents = JSON.parse(agentCoordination || '{}')
            const escalation = JSON.parse(escalationRules || '{}')
            const quality = JSON.parse(qualityCriteria || '{}')
            const decision = JSON.parse(decisionContext || '{}')
            const compliance = JSON.parse(marketCompliance || '{}')
            const monitoring = JSON.parse(monitoringConfig || '{}')
            
            // Default escalation rules
            const defaultEscalation = {
                error_threshold: 3,
                timeout_minutes: 30,
                retry_attempts: 2,
                escalation_levels: [
                    {
                        level: 1,
                        trigger: 'error_threshold_reached',
                        action: 'retry_with_different_agent'
                    },
                    {
                        level: 2,
                        trigger: 'timeout_exceeded',
                        action: 'human_intervention_required'
                    },
                    {
                        level: 3,
                        trigger: 'quality_failure',
                        action: 'workflow_suspension'
                    }
                ],
                notification_channels: ['email', 'sms', 'whatsapp', 'dashboard'],
                escalation_contacts: []
            }

            const finalEscalation = { ...defaultEscalation, ...escalation }
            
            // Default quality criteria
            const defaultQuality = {
                accuracy_threshold: 0.95,
                response_time_max: 30,
                compliance_required: true,
                cost_efficiency: true,
                user_satisfaction_min: 4.0,
                quality_checks: [
                    'data_validation',
                    'output_verification',
                    'compliance_check',
                    'performance_assessment',
                    'cost_analysis'
                ],
                automated_qa: true,
                human_review_required: false
            }

            const finalQuality = { ...defaultQuality, ...quality }
            
            // Default African market compliance
            const defaultCompliance = {
                regions: ['nigeria', 'kenya', 'south_africa', 'ghana'],
                regulations: ['cbn', 'popia', 'gdpr', 'local_data_protection'],
                local_requirements: true,
                data_residency: true,
                audit_trails: true,
                compliance_checks: {
                    data_protection: true,
                    financial_regulations: true,
                    business_licensing: true,
                    tax_compliance: true,
                    employment_law: true
                },
                reporting_requirements: {
                    frequency: 'monthly',
                    format: 'standardized',
                    recipients: ['compliance_officer', 'management']
                }
            }

            const finalCompliance = { ...defaultCompliance, ...compliance }
            
            // Default monitoring configuration
            const defaultMonitoring = {
                metrics: [
                    'performance',
                    'cost',
                    'quality',
                    'compliance',
                    'user_satisfaction',
                    'agent_utilization',
                    'workflow_efficiency'
                ],
                alerts: true,
                reporting: 'real_time',
                dashboards: ['executive', 'operational', 'technical'],
                alert_thresholds: {
                    performance_degradation: 20,
                    cost_overrun: 15,
                    quality_drop: 10,
                    compliance_violation: 0
                },
                notification_preferences: {
                    critical: 'immediate',
                    warning: 'hourly_digest',
                    info: 'daily_report'
                }
            }

            const finalMonitoring = { ...defaultMonitoring, ...monitoring }
            
            // Prepare headers with tenant isolation
            const headers = {
                'Content-Type': 'application/json',
                'X-Tenant-ID': tenantId,
                'X-Agent-Type': 'supervisor'
            }
            
            if (apiKey) {
                headers['Authorization'] = `Bearer ${apiKey}`
            }

            // Create supervisor agent execution request
            const supervisorRequest = {
                type: 'supervisor',
                supervision_type: supervisionType,
                config: {
                    tenant_id: tenantId,
                    workflow_config: workflow,
                    agent_coordination: agents,
                    escalation_rules: finalEscalation,
                    quality_criteria: finalQuality,
                    decision_context: decision,
                    african_market_compliance: finalCompliance,
                    monitoring_config: finalMonitoring,
                    supervision_capabilities: [
                        'workflow_orchestration',
                        'quality_assurance',
                        'escalation_handling',
                        'performance_monitoring',
                        'compliance_oversight',
                        'resource_optimization',
                        'decision_support',
                        'risk_management'
                    ],
                    execution_context: {
                        source: 'flowise',
                        node_id: nodeData.instance?.id,
                        workflow_id: nodeData.instance?.chatflowId,
                        timestamp: new Date().toISOString()
                    }
                },
                input: {
                    supervision_type: supervisionType,
                    workflow: workflow,
                    agents: agents,
                    decision_context: decision
                },
                context: {
                    supervision_type: supervisionType,
                    multi_agent_coordination: true,
                    african_market: true,
                    multi_tenant: true,
                    source: 'flowise_supervisor_node'
                }
            }

            // Execute supervisor agent via SMEFlow API
            const response = await axios.post(
                `${apiUrl}/api/v1/agents/supervisor/execute`,
                supervisorRequest,
                { headers, timeout: 120000 }
            )

            return {
                success: true,
                agent_type: 'supervisor',
                supervision_type: supervisionType,
                agent_id: response.data.agent_id,
                execution_id: response.data.execution_id,
                supervision_result: response.data.result,
                orchestration_plan: response.data.orchestration_plan,
                quality_assessment: response.data.quality_assessment,
                escalations_triggered: response.data.escalations_triggered,
                decisions_made: response.data.decisions_made,
                performance_metrics: response.data.performance_metrics,
                compliance_status: response.data.compliance_status,
                agent_coordination_status: response.data.agent_coordination_status,
                recommendations: response.data.recommendations,
                next_actions: response.data.next_actions,
                cost_usd: response.data.cost_usd,
                tokens_used: response.data.tokens_used,
                execution_time: response.data.execution_time,
                supervised_agents: response.data.supervised_agents,
                workflow_status: response.data.workflow_status,
                tenant_id: tenantId,
                escalation_rules: finalEscalation,
                quality_criteria: finalQuality,
                compliance_config: finalCompliance,
                monitoring_config: finalMonitoring,
                timestamp: new Date().toISOString()
            }

        } catch (error) {
            console.error('SMEFlow Supervisor Agent execution error:', error)
            
            return {
                success: false,
                agent_type: 'supervisor',
                supervision_type: supervisionType,
                error: error.message,
                error_code: error.response?.status,
                tenant_id: tenantId,
                timestamp: new Date().toISOString(),
                escalation_required: true,
                suggested_action: 'Review workflow configuration and agent coordination setup'
            }
        }
    }
}

module.exports = { nodeClass: SMEFlowSupervisor }
