const { INode, INodeData, INodeParams } = require('flowise-components');
const axios = require('axios');

class SMEFlowMentor {
    constructor() {
        this.label = 'SMEFlow Mentor Agent'
        this.name = 'smeflowMentor'
        this.version = 1.0
        this.type = 'SMEFlowMentor'
        this.icon = 'mentor.svg'
        this.category = 'SMEFlow Agents'
        this.description = 'Provide business guidance and recommendations with African market expertise'
        this.baseClasses = [this.type]

        this.inputs = [
            {
                label: 'Guidance Type',
                name: 'guidanceType',
                type: 'options',
                options: [
                    {
                        label: 'Business Strategy',
                        name: 'business_strategy'
                    },
                    {
                        label: 'Financial Planning',
                        name: 'financial_planning'
                    },
                    {
                        label: 'Market Analysis',
                        name: 'market_analysis'
                    },
                    {
                        label: 'Compliance Advisory',
                        name: 'compliance_advisory'
                    },
                    {
                        label: 'Technology Recommendations',
                        name: 'tech_recommendations'
                    },
                    {
                        label: 'Process Optimization',
                        name: 'process_optimization'
                    },
                    {
                        label: 'Risk Assessment',
                        name: 'risk_assessment'
                    },
                    {
                        label: 'Growth Planning',
                        name: 'growth_planning'
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
                        label: 'Consulting Services',
                        name: 'consulting'
                    },
                    {
                        label: 'Salon & Spa',
                        name: 'salon_spa'
                    },
                    {
                        label: 'Healthcare',
                        name: 'healthcare'
                    },
                    {
                        label: 'Manufacturing',
                        name: 'manufacturing'
                    },
                    {
                        label: 'Retail & E-commerce',
                        name: 'retail'
                    },
                    {
                        label: 'Agriculture & Agtech',
                        name: 'agriculture'
                    },
                    {
                        label: 'Fintech & Financial Services',
                        name: 'fintech'
                    },
                    {
                        label: 'Education & Training',
                        name: 'education'
                    },
                    {
                        label: 'Transportation & Logistics',
                        name: 'logistics'
                    },
                    {
                        label: 'General Business',
                        name: 'general'
                    }
                ],
                default: 'general'
            },
            {
                label: 'Tenant ID',
                name: 'tenantId',
                type: 'string',
                placeholder: 'Enter tenant UUID',
                description: 'Multi-tenant isolation identifier'
            },
            {
                label: 'Business Context',
                name: 'businessContext',
                type: 'json',
                placeholder: '{"company_size": "small", "revenue": 50000, "employees": 5, "location": "Lagos"}',
                description: 'Business context and current situation'
            },
            {
                label: 'Question/Challenge',
                name: 'question',
                type: 'string',
                placeholder: 'What business challenge do you need guidance on?',
                description: 'Specific question or challenge to address'
            },
            {
                label: 'African Market Focus',
                name: 'marketFocus',
                type: 'json',
                placeholder: '{"region": "west_africa", "countries": ["nigeria", "ghana"], "local_regulations": true}',
                description: 'African market-specific focus areas',
                optional: true
            },
            {
                label: 'Expertise Level',
                name: 'expertiseLevel',
                type: 'options',
                options: [
                    {
                        label: 'Beginner - New to business',
                        name: 'beginner'
                    },
                    {
                        label: 'Intermediate - Some experience',
                        name: 'intermediate'
                    },
                    {
                        label: 'Advanced - Experienced entrepreneur',
                        name: 'advanced'
                    },
                    {
                        label: 'Expert - Industry veteran',
                        name: 'expert'
                    }
                ],
                default: 'intermediate'
            },
            {
                label: 'Response Format',
                name: 'responseFormat',
                type: 'options',
                options: [
                    {
                        label: 'Detailed Analysis',
                        name: 'detailed'
                    },
                    {
                        label: 'Action Plan',
                        name: 'action_plan'
                    },
                    {
                        label: 'Quick Tips',
                        name: 'quick_tips'
                    },
                    {
                        label: 'Step-by-Step Guide',
                        name: 'step_guide'
                    },
                    {
                        label: 'Risk-Benefit Analysis',
                        name: 'risk_benefit'
                    }
                ],
                default: 'detailed'
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
        const guidanceType = nodeData.inputs?.guidanceType || 'business_strategy'
        const industrySector = nodeData.inputs?.industrySector || 'general'
        const tenantId = nodeData.inputs?.tenantId
        const businessContext = nodeData.inputs?.businessContext
        const question = nodeData.inputs?.question
        const marketFocus = nodeData.inputs?.marketFocus
        const expertiseLevel = nodeData.inputs?.expertiseLevel || 'intermediate'
        const responseFormat = nodeData.inputs?.responseFormat || 'detailed'
        const apiUrl = nodeData.inputs?.apiUrl || 'http://smeflow:8000'
        const apiKey = nodeData.inputs?.apiKey

        if (!tenantId) {
            throw new Error('Tenant ID is required for multi-tenant isolation')
        }

        if (!question) {
            throw new Error('Question or challenge is required for mentor guidance')
        }

        try {
            // Parse configurations
            const context = JSON.parse(businessContext || '{}')
            const africanMarketFocus = JSON.parse(marketFocus || '{}')
            
            // Default African market expertise
            const defaultMarketFocus = {
                region: 'west_africa',
                countries: ['nigeria', 'ghana', 'kenya', 'south_africa'],
                local_regulations: true,
                cultural_considerations: true,
                local_business_practices: {
                    payment_methods: ['cash', 'mobile_money', 'bank_transfer'],
                    business_hours: 'flexible',
                    relationship_building: 'high_importance',
                    community_engagement: 'essential'
                },
                economic_factors: {
                    currency_volatility: true,
                    inflation_considerations: true,
                    access_to_credit: 'limited',
                    informal_economy: 'significant'
                },
                regulatory_landscape: {
                    business_registration: 'varies_by_country',
                    tax_compliance: 'complex',
                    import_export: 'bureaucratic',
                    data_protection: 'emerging'
                }
            }

            const finalMarketFocus = { ...defaultMarketFocus, ...africanMarketFocus }
            
            // Default business context
            const defaultContext = {
                company_size: 'small',
                stage: 'growth',
                funding_status: 'bootstrapped',
                digital_maturity: 'basic',
                market_presence: 'local'
            }

            const finalContext = { ...defaultContext, ...context }
            
            // Prepare headers with tenant isolation
            const headers = {
                'Content-Type': 'application/json',
                'X-Tenant-ID': tenantId,
                'X-Agent-Type': 'mentor'
            }
            
            if (apiKey) {
                headers['Authorization'] = `Bearer ${apiKey}`
            }

            // Create mentor agent execution request
            const mentorRequest = {
                type: 'mentor',
                guidance_type: guidanceType,
                industry_sector: industrySector,
                config: {
                    tenant_id: tenantId,
                    expertise_level: expertiseLevel,
                    response_format: responseFormat,
                    african_market_focus: finalMarketFocus,
                    business_context: finalContext,
                    specializations: [
                        'african_market_dynamics',
                        'sme_growth_strategies',
                        'local_compliance',
                        'cultural_business_practices',
                        'digital_transformation',
                        'financial_inclusion',
                        'supply_chain_optimization',
                        'customer_acquisition'
                    ],
                    knowledge_base: {
                        local_regulations: true,
                        market_data: true,
                        best_practices: true,
                        case_studies: true,
                        industry_benchmarks: true
                    },
                    execution_context: {
                        source: 'flowise',
                        node_id: nodeData.instance?.id,
                        workflow_id: nodeData.instance?.chatflowId,
                        timestamp: new Date().toISOString()
                    }
                },
                input: {
                    question: question,
                    context: finalContext,
                    guidance_type: guidanceType,
                    industry: industrySector
                },
                context: {
                    guidance_type: guidanceType,
                    industry_sector: industrySector,
                    african_market: true,
                    multi_tenant: true,
                    source: 'flowise_mentor_node'
                }
            }

            // Execute mentor agent via SMEFlow API
            const response = await axios.post(
                `${apiUrl}/api/v1/agents/mentor/execute`,
                mentorRequest,
                { headers, timeout: 90000 }
            )

            return {
                success: true,
                agent_type: 'mentor',
                guidance_type: guidanceType,
                industry_sector: industrySector,
                agent_id: response.data.agent_id,
                execution_id: response.data.execution_id,
                guidance: response.data.result,
                recommendations: response.data.recommendations,
                action_items: response.data.action_items,
                resources: response.data.resources,
                risk_factors: response.data.risk_factors,
                success_metrics: response.data.success_metrics,
                follow_up_questions: response.data.follow_up_questions,
                cost_usd: response.data.cost_usd,
                tokens_used: response.data.tokens_used,
                execution_time: response.data.execution_time,
                expertise_level: expertiseLevel,
                response_format: responseFormat,
                tenant_id: tenantId,
                african_market_focus: finalMarketFocus,
                timestamp: new Date().toISOString()
            }

        } catch (error) {
            console.error('SMEFlow Mentor Agent execution error:', error)
            
            return {
                success: false,
                agent_type: 'mentor',
                guidance_type: guidanceType,
                industry_sector: industrySector,
                error: error.message,
                error_code: error.response?.status,
                tenant_id: tenantId,
                timestamp: new Date().toISOString(),
                suggested_action: 'Review question format and business context'
            }
        }
    }
}

module.exports = { nodeClass: SMEFlowMentor }
