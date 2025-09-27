"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const axios = require("axios");

class SMEFlowMentor_Agents {
    constructor() {
        this.label = 'SMEFlow Mentor Agent';
        this.name = 'smeflowMentor';
        this.version = 1.0;
        this.type = 'SMEFlowMentor';
        this.icon = 'mentor.svg';
        this.category = 'SMEFlow Agents';
        this.description = 'Provide business guidance and strategic recommendations for African SMEs';
        this.baseClasses = [this.type, 'Agent'];
        this.inputs = [
            {
                label: 'Guidance Type',
                name: 'guidanceType',
                type: 'options',
                options: [
                    {
                        label: 'Business Strategy',
                        name: 'business_strategy',
                        description: 'Strategic planning and growth advice'
                    },
                    {
                        label: 'Financial Planning',
                        name: 'financial_planning',
                        description: 'Financial management and budgeting'
                    },
                    {
                        label: 'Market Analysis',
                        name: 'market_analysis',
                        description: 'Market research and competitive analysis'
                    },
                    {
                        label: 'Operations Optimization',
                        name: 'operations_optimization',
                        description: 'Process improvement and efficiency'
                    },
                    {
                        label: 'Digital Transformation',
                        name: 'digital_transformation',
                        description: 'Technology adoption and digitization'
                    },
                    {
                        label: 'Compliance Advisory',
                        name: 'compliance_advisory',
                        description: 'Regulatory compliance guidance'
                    }
                ],
                default: 'business_strategy'
            },
            {
                label: 'Industry Sector',
                name: 'industrySector',
                type: 'options',
                options: [
                    {
                        label: 'Retail/E-commerce',
                        name: 'retail'
                    },
                    {
                        label: 'Healthcare',
                        name: 'healthcare'
                    },
                    {
                        label: 'Fintech',
                        name: 'fintech'
                    },
                    {
                        label: 'Manufacturing',
                        name: 'manufacturing'
                    },
                    {
                        label: 'Agriculture',
                        name: 'agriculture'
                    },
                    {
                        label: 'Education',
                        name: 'education'
                    },
                    {
                        label: 'Logistics',
                        name: 'logistics'
                    },
                    {
                        label: 'Consulting',
                        name: 'consulting'
                    },
                    {
                        label: 'Beauty/Salon',
                        name: 'beauty'
                    }
                ],
                default: 'retail'
            },
            {
                label: 'Tenant ID',
                name: 'tenantId',
                type: 'string',
                placeholder: 'Enter tenant UUID (e.g., 550e8400-e29b-41d4-a716-446655440000)',
                description: 'Multi-tenant isolation identifier'
            },
            {
                label: 'Business Context',
                name: 'businessContext',
                type: 'json',
                placeholder: '{"company_size": "small", "revenue": 50000, "employees": 5, "location": "Lagos"}',
                description: 'JSON object with business context information'
            },
            {
                label: 'Question/Challenge',
                name: 'question',
                type: 'string',
                placeholder: 'Describe your business question or challenge',
                description: 'The specific question or challenge you need guidance on'
            },
            {
                label: 'African Market Config',
                name: 'marketConfig',
                type: 'json',
                placeholder: '{"region": "nigeria", "currency": "NGN", "language": "en", "market_focus": "urban"}',
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

    async init(nodeData, _, options) {
        const guidanceType = nodeData.inputs?.guidanceType || 'business_strategy';
        const industrySector = nodeData.inputs?.industrySector || 'retail';
        const tenantId = nodeData.inputs?.tenantId;
        const businessContext = nodeData.inputs?.businessContext;
        const question = nodeData.inputs?.question;
        const marketConfig = nodeData.inputs?.marketConfig;
        const apiUrl = nodeData.inputs?.apiUrl || 'http://smeflow:8000';
        const apiKey = nodeData.inputs?.apiKey;

        if (!tenantId) {
            throw new Error('Tenant ID is required for multi-tenant isolation');
        }

        if (!question) {
            throw new Error('Question/Challenge is required for mentor guidance');
        }

        // Validate UUID format
        const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
        if (!uuidRegex.test(tenantId)) {
            throw new Error('Tenant ID must be a valid UUID format');
        }

        try {
            // Parse configurations
            const context = JSON.parse(businessContext || '{}');
            const africanMarketConfig = JSON.parse(marketConfig || '{}');
            
            // Default African market optimizations
            const defaultMarketConfig = {
                region: 'africa-west',
                currency: 'NGN',
                timezone: 'Africa/Lagos',
                languages: ['en', 'ha', 'yo', 'ig'],
                market_focus: 'urban',
                business_environment: {
                    infrastructure: 'developing',
                    digital_adoption: 'growing',
                    regulatory_complexity: 'moderate'
                },
                cultural_context: {
                    business_relationships: 'relationship_focused',
                    decision_making: 'consensus_driven',
                    communication_style: 'respectful'
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

            // Create mentor guidance request
            const mentorRequest = {
                guidance_type: guidanceType,
                industry_sector: industrySector,
                tenant_id: tenantId,
                business_context: {
                    ...context,
                    ...finalMarketConfig,
                    source: 'flowise',
                    workflow_id: nodeData.instance?.id,
                    created_at: new Date().toISOString()
                },
                question: question,
                preferences: {
                    response_style: 'practical',
                    detail_level: 'comprehensive',
                    include_examples: true,
                    african_context: true
                }
            };

            // Execute mentor guidance via SMEFlow API
            const response = await axios.post(
                `${apiUrl}/api/v1/mentor/guidance`,
                mentorRequest,
                { headers, timeout: 120000 }
            );

            return {
                success: true,
                guidance_type: guidanceType,
                industry_sector: industrySector,
                mentor_id: response.data.mentor_id,
                session_id: response.data.session_id,
                guidance: response.data.guidance,
                recommendations: response.data.recommendations,
                action_items: response.data.action_items,
                resources: response.data.resources,
                follow_up_questions: response.data.follow_up_questions,
                confidence_score: response.data.confidence_score,
                cost_usd: response.data.cost_usd,
                tokens_used: response.data.tokens_used,
                execution_time: response.data.execution_time,
                tenant_id: tenantId,
                market_config: finalMarketConfig,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            console.error('SMEFlow Mentor execution error:', error);
            
            return {
                success: false,
                guidance_type: guidanceType,
                industry_sector: industrySector,
                error: error.message,
                error_code: error.response?.status || 'UNKNOWN',
                tenant_id: tenantId,
                timestamp: new Date().toISOString()
            };
        }
    }
}

module.exports = { nodeClass: SMEFlowMentor_Agents };
