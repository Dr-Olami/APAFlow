/**
 * SMEFlow Custom Nodes for Flowise Integration
 * 
 * This module exports all custom SMEFlow nodes for Flowise integration,
 * providing multi-tenant African market automation capabilities.
 */

const SMEFlowAgent = require('./SMEFlowAgent');
const SMEFlowWorkflow = require('./SMEFlowWorkflow');
const SMEFlowTenantManager = require('./SMEFlowTenantManager');

module.exports = {
    nodes: [
        SMEFlowAgent,
        SMEFlowWorkflow,
        SMEFlowTenantManager
    ]
};
