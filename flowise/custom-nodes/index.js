// SMEFlow Custom Flowise Nodes
// Main entry point for all custom nodes

const agents = require('./agents');
const chains = require('./chains');
const tools = require('./tools');
const utilities = require('./utilities');
const workflows = require('./workflows');
const themes = require('./themes')

module.exports = {
    ...agents,
    ...workflows,
    ...themes,
    nodes: [
        ...agents.nodes,
        ...chains.nodes,
        ...tools.nodes,
        ...utilities.nodes,
        ...workflows.nodes,
        ...themes.nodes
    ]
};
