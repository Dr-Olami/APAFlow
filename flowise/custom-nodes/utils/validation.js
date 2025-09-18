/**
 * Validation utilities for SMEFlow custom nodes
 * Provides tenant isolation, configuration validation, and security checks
 */

const { v4: uuidv4, validate: uuidValidate } = require('uuid');

class SMEFlowValidation {
    /**
     * Validate tenant ID format and isolation
     * @param {string} tenantId - Tenant UUID
     * @returns {object} Validation result
     */
    static validateTenantId(tenantId) {
        if (!tenantId) {
            return {
                valid: false,
                error: 'Tenant ID is required for multi-tenant isolation'
            };
        }

        if (typeof tenantId !== 'string') {
            return {
                valid: false,
                error: 'Tenant ID must be a string'
            };
        }

        if (!uuidValidate(tenantId)) {
            return {
                valid: false,
                error: 'Tenant ID must be a valid UUID format'
            };
        }

        return {
            valid: true,
            tenantId: tenantId.toLowerCase()
        };
    }

    /**
     * Validate JSON configuration input
     * @param {string} jsonString - JSON string to validate
     * @param {string} fieldName - Name of the field for error messages
     * @param {boolean} required - Whether the field is required
     * @returns {object} Validation result
     */
    static validateJsonConfig(jsonString, fieldName, required = true) {
        if (!jsonString || jsonString.trim() === '') {
            if (required) {
                return {
                    valid: false,
                    error: `${fieldName} is required`
                };
            }
            return {
                valid: true,
                data: {}
            };
        }

        try {
            const parsed = JSON.parse(jsonString);
            return {
                valid: true,
                data: parsed
            };
        } catch (error) {
            return {
                valid: false,
                error: `Invalid JSON format in ${fieldName}: ${error.message}`
            };
        }
    }

    /**
     * Validate African market configuration
     * @param {object} marketConfig - Market configuration object
     * @returns {object} Validation result
     */
    static validateAfricanMarketConfig(marketConfig) {
        const supportedRegions = [
            'nigeria', 'kenya', 'south_africa', 'ghana', 'uganda', 
            'tanzania', 'rwanda', 'ethiopia', 'zambia', 'malawi'
        ];

        const supportedCurrencies = [
            'NGN', 'KES', 'ZAR', 'GHS', 'UGX', 'TZS', 'RWF', 'ETB', 'ZMW', 'MWK'
        ];

        const errors = [];

        if (marketConfig.region && !supportedRegions.includes(marketConfig.region)) {
            errors.push(`Unsupported region: ${marketConfig.region}. Supported regions: ${supportedRegions.join(', ')}`);
        }

        if (marketConfig.currency && !supportedCurrencies.includes(marketConfig.currency)) {
            errors.push(`Unsupported currency: ${marketConfig.currency}. Supported currencies: ${supportedCurrencies.join(', ')}`);
        }

        if (marketConfig.phone_format && !marketConfig.phone_format.startsWith('+')) {
            errors.push('Phone format must start with country code (e.g., +234)');
        }

        if (marketConfig.languages && !Array.isArray(marketConfig.languages)) {
            errors.push('Languages must be an array');
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Validate agent configuration
     * @param {object} agentConfig - Agent configuration object
     * @param {string} agentType - Type of agent (automator, mentor, supervisor)
     * @returns {object} Validation result
     */
    static validateAgentConfig(agentConfig, agentType) {
        const errors = [];

        // Common validations
        if (agentConfig.name && agentConfig.name.length > 255) {
            errors.push('Agent name must be 255 characters or less');
        }

        if (agentConfig.description && agentConfig.description.length > 1000) {
            errors.push('Agent description must be 1000 characters or less');
        }

        // Agent-specific validations
        switch (agentType) {
            case 'automator':
                if (agentConfig.tools && !Array.isArray(agentConfig.tools)) {
                    errors.push('Tools configuration must be an array');
                }
                break;

            case 'mentor':
                if (agentConfig.expertise_level && 
                    !['beginner', 'intermediate', 'advanced', 'expert'].includes(agentConfig.expertise_level)) {
                    errors.push('Invalid expertise level. Must be: beginner, intermediate, advanced, or expert');
                }
                break;

            case 'supervisor':
                if (agentConfig.escalation_rules && typeof agentConfig.escalation_rules !== 'object') {
                    errors.push('Escalation rules must be an object');
                }
                break;
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Validate API configuration and security
     * @param {object} apiConfig - API configuration object
     * @returns {object} Validation result
     */
    static validateApiConfig(apiConfig) {
        const errors = [];

        if (!apiConfig.apiUrl) {
            errors.push('API URL is required');
        } else {
            try {
                new URL(apiConfig.apiUrl);
            } catch (error) {
                errors.push('Invalid API URL format');
            }
        }

        if (apiConfig.apiKey && apiConfig.apiKey.length < 10) {
            errors.push('API key appears to be too short (minimum 10 characters)');
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Validate compliance configuration
     * @param {object} complianceConfig - Compliance configuration object
     * @returns {object} Validation result
     */
    static validateComplianceConfig(complianceConfig) {
        const supportedRegulations = [
            'cbn', 'popia', 'gdpr', 'cbk', 'sarb', 'sars', 'kra', 'bog', 'gra'
        ];

        const errors = [];

        if (complianceConfig.regulatory_compliance && Array.isArray(complianceConfig.regulatory_compliance)) {
            const unsupported = complianceConfig.regulatory_compliance.filter(
                reg => !supportedRegulations.includes(reg)
            );
            if (unsupported.length > 0) {
                errors.push(`Unsupported regulations: ${unsupported.join(', ')}`);
            }
        }

        if (complianceConfig.data_residency !== undefined && typeof complianceConfig.data_residency !== 'boolean') {
            errors.push('Data residency must be a boolean value');
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Sanitize input data to prevent injection attacks
     * @param {any} input - Input data to sanitize
     * @returns {any} Sanitized input
     */
    static sanitizeInput(input) {
        if (typeof input === 'string') {
            // Remove potentially dangerous characters
            return input.replace(/[<>\"'%;()&+]/g, '');
        }

        if (typeof input === 'object' && input !== null) {
            const sanitized = {};
            for (const [key, value] of Object.entries(input)) {
                sanitized[this.sanitizeInput(key)] = this.sanitizeInput(value);
            }
            return sanitized;
        }

        return input;
    }

    /**
     * Generate execution context for audit trails
     * @param {object} nodeData - Flowise node data
     * @param {string} tenantId - Tenant ID
     * @param {string} agentType - Agent type
     * @returns {object} Execution context
     */
    static generateExecutionContext(nodeData, tenantId, agentType) {
        return {
            execution_id: uuidv4(),
            tenant_id: tenantId,
            agent_type: agentType,
            source: 'flowise',
            node_id: nodeData.instance?.id || 'unknown',
            workflow_id: nodeData.instance?.chatflowId || 'unknown',
            timestamp: new Date().toISOString(),
            user_agent: 'SMEFlow-Flowise-Node/1.0',
            session_id: nodeData.instance?.sessionId || null
        };
    }

    /**
     * Validate complete node input
     * @param {object} inputs - All node inputs
     * @param {string} nodeType - Type of node
     * @returns {object} Complete validation result
     */
    static validateNodeInputs(inputs, nodeType) {
        const validationResults = {
            valid: true,
            errors: [],
            warnings: [],
            sanitizedInputs: {}
        };

        // Validate tenant ID
        const tenantValidation = this.validateTenantId(inputs.tenantId);
        if (!tenantValidation.valid) {
            validationResults.valid = false;
            validationResults.errors.push(tenantValidation.error);
        } else {
            validationResults.sanitizedInputs.tenantId = tenantValidation.tenantId;
        }

        // Validate API configuration
        const apiValidation = this.validateApiConfig({
            apiUrl: inputs.apiUrl,
            apiKey: inputs.apiKey
        });
        if (!apiValidation.valid) {
            validationResults.valid = false;
            validationResults.errors.push(...apiValidation.errors);
        }

        // Node-specific validations
        switch (nodeType) {
            case 'automator':
                this.validateAutomatorInputs(inputs, validationResults);
                break;
            case 'mentor':
                this.validateMentorInputs(inputs, validationResults);
                break;
            case 'supervisor':
                this.validateSupervisorInputs(inputs, validationResults);
                break;
            case 'african_integrations':
                this.validateAfricanIntegrationsInputs(inputs, validationResults);
                break;
        }

        return validationResults;
    }

    /**
     * Validate automator-specific inputs
     */
    static validateAutomatorInputs(inputs, validationResults) {
        // Validate task configuration
        const taskConfigValidation = this.validateJsonConfig(inputs.taskConfig, 'Task Configuration');
        if (!taskConfigValidation.valid) {
            validationResults.valid = false;
            validationResults.errors.push(taskConfigValidation.error);
        }

        // Validate input data
        const inputDataValidation = this.validateJsonConfig(inputs.inputData, 'Input Data', false);
        if (!inputDataValidation.valid) {
            validationResults.valid = false;
            validationResults.errors.push(inputDataValidation.error);
        }
    }

    /**
     * Validate mentor-specific inputs
     */
    static validateMentorInputs(inputs, validationResults) {
        if (!inputs.question || inputs.question.trim() === '') {
            validationResults.valid = false;
            validationResults.errors.push('Question or challenge is required for mentor guidance');
        }

        // Validate business context
        const contextValidation = this.validateJsonConfig(inputs.businessContext, 'Business Context', false);
        if (!contextValidation.valid) {
            validationResults.valid = false;
            validationResults.errors.push(contextValidation.error);
        }
    }

    /**
     * Validate supervisor-specific inputs
     */
    static validateSupervisorInputs(inputs, validationResults) {
        if (!inputs.workflowConfig && !inputs.agentCoordination) {
            validationResults.valid = false;
            validationResults.errors.push('Either workflow configuration or agent coordination is required');
        }
    }

    /**
     * Validate African integrations-specific inputs
     */
    static validateAfricanIntegrationsInputs(inputs, validationResults) {
        // Validate integration configuration
        const configValidation = this.validateJsonConfig(inputs.integrationConfig, 'Integration Configuration');
        if (!configValidation.valid) {
            validationResults.valid = false;
            validationResults.errors.push(configValidation.error);
        }
    }
}

module.exports = SMEFlowValidation;
