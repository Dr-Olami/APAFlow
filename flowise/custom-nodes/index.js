/**
 * SMEFlow Custom Nodes for Flowise Integration
 * 
 * This module exports all custom SMEFlow nodes for Flowise integration,
 * providing multi-tenant African market automation capabilities with
 * specialized agent types and African market integrations.
 */

const SMEFlowAgent = require('./SMEFlowAgent');
const SMEFlowWorkflow = require('./SMEFlowWorkflow');
const SMEFlowTenantManager = require('./SMEFlowTenantManager');
const SMEFlowAutomator = require('./SMEFlowAutomator');
const SMEFlowMentor = require('./SMEFlowMentor');
const SMEFlowSupervisor = require('./SMEFlowSupervisor');
const SMEFlowAfricanIntegrations = require('./SMEFlowAfricanIntegrations');

module.exports = {
    nodes: [
        // Original nodes
        SMEFlowAgent,
        SMEFlowWorkflow,
        SMEFlowTenantManager,
        
        // Specialized agent nodes
        SMEFlowAutomator,
        SMEFlowMentor,
        SMEFlowSupervisor,
        
        // African market integrations
        SMEFlowAfricanIntegrations
    ]
};
