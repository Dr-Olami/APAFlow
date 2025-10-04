"""
WhatsApp Business API Integration Template for n8N.

Provides comprehensive WhatsApp Business API integration for African markets including:
- Message sending (text, media, templates)
- Webhook handling for incoming messages
- Message status tracking
- Template management
- Multi-language support for African languages
"""

from typing import Dict, Any, Optional, List
from ..base_template import N8nWorkflowTemplate, N8nNode, SimpleN8nWorkflowTemplate


class WhatsAppWorkflowTemplate(N8nWorkflowTemplate):
    """
    WhatsApp Business API workflow template for African markets.
    
    Supports message sending, webhook handling, template management,
    and multi-language communication with proper compliance features.
    """
    
    def __init__(self, tenant_id: str, phone_number_id: str, environment: str = "production"):
        """
        Initialize WhatsApp workflow template.
        
        Args:
            tenant_id: Unique identifier for the tenant
            phone_number_id: WhatsApp Business phone number ID
            environment: Environment (production/sandbox)
        """
        super().__init__(tenant_id, "WhatsApp Business")
        self.phone_number_id = phone_number_id
        self.environment = environment
        self.base_url = "https://graph.facebook.com/v18.0"
        
    def build_workflow(self) -> Dict[str, Any]:
        """
        Build complete WhatsApp Business API workflow.
        
        Returns:
            Complete n8N workflow definition for WhatsApp integration
        """
        # 1. Webhook trigger for WhatsApp operations
        webhook_trigger = self.create_webhook_trigger("whatsapp/send")
        self.add_node(webhook_trigger)
        
        # 2. Message validation and routing
        validation_node = self._create_message_validation_node()
        self.add_node(validation_node)
        self.add_connection(webhook_trigger.name, validation_node.name)
        
        # 3. Send text message
        text_message_node = self._create_text_message_node()
        self.add_node(text_message_node)
        
        # 4. Send media message
        media_message_node = self._create_media_message_node()
        self.add_node(media_message_node)
        
        # 5. Send template message
        template_message_node = self._create_template_message_node()
        self.add_node(template_message_node)
        
        # 6. Response formatter
        response_node = self._create_response_formatter()
        self.add_node(response_node)
        
        # Connect validation to message types
        self.add_connection(validation_node.name, text_message_node.name)
        self.add_connection(validation_node.name, media_message_node.name)
        self.add_connection(validation_node.name, template_message_node.name)
        
        # Connect all message types to response formatter
        self.add_connection(text_message_node.name, response_node.name)
        self.add_connection(media_message_node.name, response_node.name)
        self.add_connection(template_message_node.name, response_node.name)
        
        # 7. SMEFlow callback
        callback_node = self.create_smeflow_callback(
            f"http://smeflow-api:8000/api/v1/workflows/callback/{self.tenant_id}"
        )
        self.add_node(callback_node)
        self.add_connection(response_node.name, callback_node.name)
        
        # 8. Error handler
        error_node = self.create_error_handler()
        self.add_node(error_node)
        
        workflow_def = {
            **self.get_workflow_metadata(),
            "nodes": [node.model_dump() for node in self.nodes],
            "connections": self.connections,
            "staticData": {
                "whatsapp_config": {
                    "phone_number_id": self.phone_number_id,
                    "environment": self.environment,
                    "base_url": self.base_url,
                    "supported_message_types": [
                        "text", "image", "document", "audio", "video", "template"
                    ],
                    "supported_languages": [
                        "en", "sw", "ha", "yo", "ig", "fr", "ar", "am"  # African languages
                    ]
                }
            }
        }
        
        return workflow_def
    
    def _create_message_validation_node(self) -> N8nNode:
        """Create message validation and routing node."""
        return N8nNode(
            name="Validate WhatsApp Message",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": f"""
// Validate and route WhatsApp message requests
const input = $input.first().json;

// Validate required fields
if (!input.to) {{
    throw new Error('Recipient phone number (to) is required');
}}

if (!input.type) {{
    throw new Error('Message type is required');
}}

// Validate phone number format (international format)
const phoneRegex = /^\\+[1-9]\\d{{1,14}}$/;
if (!phoneRegex.test(input.to)) {{
    throw new Error('Invalid phone number format. Use international format (+234XXXXXXXXXX)');
}}

// Validate message type
const validTypes = ['text', 'image', 'document', 'audio', 'video', 'template'];
if (!validTypes.includes(input.type)) {{
    throw new Error(`Invalid message type. Supported types: ${{validTypes.join(', ')}}`);
}}

// Type-specific validation
let messageData = {{
    to: input.to,
    type: input.type,
    tenant_id: '{self.tenant_id}',
    phone_number_id: '{self.phone_number_id}',
    timestamp: new Date().toISOString()
}};

switch (input.type) {{
    case 'text':
        if (!input.text || !input.text.body) {{
            throw new Error('Text message body is required');
        }}
        messageData.text = {{
            body: input.text.body,
            preview_url: input.text.preview_url || false
        }};
        break;
        
    case 'template':
        if (!input.template || !input.template.name) {{
            throw new Error('Template name is required');
        }}
        messageData.template = {{
            name: input.template.name,
            language: {{
                code: input.template.language || 'en'
            }},
            components: input.template.components || []
        }};
        break;
        
    case 'image':
    case 'document':
    case 'audio':
    case 'video':
        if (!input[input.type] || (!input[input.type].id && !input[input.type].link)) {{
            throw new Error(`${{input.type}} media ID or link is required`);
        }}
        messageData[input.type] = input[input.type];
        break;
}}

return [{{
    json: messageData
}}];
"""
            },
            position=[200, 200]
        )
    
    def _create_text_message_node(self) -> N8nNode:
        """Create text message sending node."""
        return N8nNode(
            name="Send WhatsApp Text Message",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Handle WhatsApp text message sending
const messageData = $node['Validate WhatsApp Message'].json;

if (messageData.type !== 'text') {
    return []; // Skip if not text message
}

// Prepare WhatsApp API request
const whatsappPayload = {
    messaging_product: 'whatsapp',
    to: messageData.to,
    type: 'text',
    text: messageData.text
};

return [{
    json: {
        message_type: 'text',
        whatsapp_payload: whatsappPayload,
        api_url: `${messageData.phone_number_id}/messages`,
        original_request: messageData,
        prepared_at: new Date().toISOString()
    }
}];
"""
            },
            position=[300, 100]
        )
    
    def _create_media_message_node(self) -> N8nNode:
        """Create media message sending node."""
        return N8nNode(
            name="Send WhatsApp Media Message",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Handle WhatsApp media message sending
const messageData = $node['Validate WhatsApp Message'].json;

const mediaTypes = ['image', 'document', 'audio', 'video'];
if (!mediaTypes.includes(messageData.type)) {
    return []; // Skip if not media message
}

// Prepare WhatsApp API request for media
const mediaPayload = {
    messaging_product: 'whatsapp',
    to: messageData.to,
    type: messageData.type,
    [messageData.type]: messageData[messageData.type]
};

// Add caption for image/video if provided
if (['image', 'video'].includes(messageData.type) && messageData[messageData.type].caption) {
    mediaPayload[messageData.type].caption = messageData[messageData.type].caption;
}

// Add filename for document if provided
if (messageData.type === 'document' && messageData.document.filename) {
    mediaPayload.document.filename = messageData.document.filename;
}

return [{
    json: {
        message_type: 'media',
        media_type: messageData.type,
        whatsapp_payload: mediaPayload,
        api_url: `${messageData.phone_number_id}/messages`,
        original_request: messageData,
        prepared_at: new Date().toISOString()
    }
}];
"""
            },
            position=[300, 200]
        )
    
    def _create_template_message_node(self) -> N8nNode:
        """Create template message sending node."""
        return N8nNode(
            name="Send WhatsApp Template Message",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Handle WhatsApp template message sending
const messageData = $node['Validate WhatsApp Message'].json;

if (messageData.type !== 'template') {
    return []; // Skip if not template message
}

// Prepare WhatsApp API request for template
const templatePayload = {
    messaging_product: 'whatsapp',
    to: messageData.to,
    type: 'template',
    template: messageData.template
};

// Validate template components if present
if (templatePayload.template.components && templatePayload.template.components.length > 0) {
    for (const component of templatePayload.template.components) {
        if (!component.type) {
            throw new Error('Template component type is required');
        }
        
        // Validate component parameters
        if (component.type === 'body' && component.parameters) {
            for (let i = 0; i < component.parameters.length; i++) {
                if (!component.parameters[i].type || !component.parameters[i].text) {
                    throw new Error(`Template body parameter ${i + 1} is invalid`);
                }
            }
        }
    }
}

return [{
    json: {
        message_type: 'template',
        template_name: messageData.template.name,
        template_language: messageData.template.language.code,
        whatsapp_payload: templatePayload,
        api_url: `${messageData.phone_number_id}/messages`,
        original_request: messageData,
        prepared_at: new Date().toISOString()
    }
}];
"""
            },
            position=[300, 300]
        )
    
    def _create_response_formatter(self) -> N8nNode:
        """Create response formatting node for WhatsApp operations."""
        return N8nNode(
            name="Format WhatsApp Response",
            type="n8n-nodes-base.httpRequest",
            parameters={
                "url": f"{self.base_url}/{{{{ $node['Validate WhatsApp Message'].json.phone_number_id }}}}/messages",
                "method": "POST",
                "authentication": "genericCredentialType",
                "genericAuthType": "httpHeaderAuth",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "Content-Type",
                            "value": "application/json"
                        }
                    ]
                },
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {
                            "name": "whatsapp_payload",
                            "value": "={{ $input.first().json.whatsapp_payload }}"
                        }
                    ]
                }
            },
            credentials={
                "httpHeaderAuth": f"whatsapp_credentials_{self.tenant_id}"
            },
            position=[500, 200]
        )
    
    def create_webhook_handler(self) -> Dict[str, Any]:
        """
        Create a webhook handler workflow for WhatsApp incoming messages.
        
        Returns:
            n8N workflow definition for handling WhatsApp webhooks
        """
        webhook_workflow = SimpleN8nWorkflowTemplate(self.tenant_id, "WhatsApp Webhook Handler")
        
        # 1. Webhook trigger for WhatsApp events
        webhook_trigger = webhook_workflow.create_webhook_trigger("whatsapp/webhook")
        webhook_workflow.add_node(webhook_trigger)
        
        # 2. Webhook verification (required by WhatsApp)
        verification_node = N8nNode(
            name="Verify WhatsApp Webhook",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": f"""
// Verify WhatsApp webhook signature and handle verification
const headers = $input.first().headers;
const body = $input.first().json;
const query = $input.first().query;

// Handle webhook verification challenge
if (query && query['hub.mode'] === 'subscribe') {{
    const verifyToken = '{self.tenant_id}_whatsapp_verify_token';
    if (query['hub.verify_token'] === verifyToken) {{
        return [{{
            json: {{
                challenge: query['hub.challenge'],
                verified: true,
                action: 'verification'
            }}
        }}];
    }} else {{
        throw new Error('Invalid verify token');
    }}
}}

// Handle incoming messages/status updates
if (body && body.entry) {{
    const processedEvents = [];
    
    for (const entry of body.entry) {{
        if (entry.changes) {{
            for (const change of entry.changes) {{
                if (change.field === 'messages' && change.value) {{
                    const value = change.value;
                    
                    // Process incoming messages
                    if (value.messages) {{
                        for (const message of value.messages) {{
                            processedEvents.push({{
                                type: 'message',
                                message_id: message.id,
                                from: message.from,
                                timestamp: message.timestamp,
                                message_type: message.type,
                                content: message[message.type] || {{}},
                                context: message.context || null
                            }});
                        }}
                    }}
                    
                    // Process message statuses
                    if (value.statuses) {{
                        for (const status of value.statuses) {{
                            processedEvents.push({{
                                type: 'status',
                                message_id: status.id,
                                recipient_id: status.recipient_id,
                                status: status.status,
                                timestamp: status.timestamp,
                                errors: status.errors || null
                            }});
                        }}
                    }}
                }}
            }}
        }}
    }}
    
    return [{{
        json: {{
            events: processedEvents,
            processed_at: new Date().toISOString(),
            action: 'process_events'
        }}
    }}];
}}

return [{{
    json: {{
        message: 'No events to process',
        action: 'no_action'
    }}
}}];
"""
            },
            position=[200, 200]
        )
        webhook_workflow.add_node(verification_node)
        webhook_workflow.add_connection(webhook_trigger.name, verification_node.name)
        
        # 3. Process incoming messages
        process_node = N8nNode(
            name="Process WhatsApp Events",
            type="n8n-nodes-base.httpRequest",
            parameters={
                "url": f"http://smeflow-api:8000/api/v1/communication/whatsapp/webhook/{self.tenant_id}",
                "method": "POST",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "Content-Type",
                            "value": "application/json"
                        },
                        {
                            "name": "X-Tenant-ID",
                            "value": self.tenant_id
                        }
                    ]
                },
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {
                            "name": "webhook_data",
                            "value": "={{ $node['Verify WhatsApp Webhook'].json }}"
                        }
                    ]
                }
            },
            position=[300, 200]
        )
        webhook_workflow.add_node(process_node)
        webhook_workflow.add_connection(verification_node.name, process_node.name)
        
        return webhook_workflow.build_workflow()
    
    def create_template_management_workflow(self) -> Dict[str, Any]:
        """
        Create a workflow for managing WhatsApp message templates.
        
        Returns:
            n8N workflow definition for template management
        """
        template_workflow = SimpleN8nWorkflowTemplate(self.tenant_id, "WhatsApp Template Management")
        
        # 1. Webhook trigger for template operations
        template_trigger = template_workflow.create_webhook_trigger("whatsapp/templates")
        template_workflow.add_node(template_trigger)
        
        # 2. Template operation router
        router_node = N8nNode(
            name="Route Template Operation",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Route WhatsApp template operations
const input = $input.first().json;
const operation = input.operation;

if (!operation) {
    throw new Error('Template operation is required');
}

const validOperations = ['create', 'get', 'list', 'delete'];
if (!validOperations.includes(operation)) {
    throw new Error(`Invalid operation. Supported: ${validOperations.join(', ')}`);
}

let templateData = {
    operation: operation,
    tenant_id: input.tenant_id,
    timestamp: new Date().toISOString()
};

switch (operation) {
    case 'create':
        if (!input.template || !input.template.name) {
            throw new Error('Template name is required for creation');
        }
        templateData.template = input.template;
        break;
        
    case 'get':
    case 'delete':
        if (!input.template_name) {
            throw new Error('Template name is required');
        }
        templateData.template_name = input.template_name;
        break;
        
    case 'list':
        templateData.filters = input.filters || {};
        break;
}

return [{
    json: templateData
}];
"""
            },
            position=[200, 200]
        )
        template_workflow.add_node(router_node)
        template_workflow.add_connection(template_trigger.name, router_node.name)
        
        # 3. Execute template operation
        execute_node = N8nNode(
            name="Execute Template Operation",
            type="n8n-nodes-base.httpRequest",
            parameters={
                "url": f"{self.base_url}/{{{{ $node['Route Template Operation'].json.waba_id || 'WABA_ID' }}}}/message_templates",
                "method": "={{ $node['Route Template Operation'].json.operation === 'create' ? 'POST' : 'GET' }}",
                "authentication": "genericCredentialType",
                "genericAuthType": "httpHeaderAuth",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "Content-Type",
                            "value": "application/json"
                        }
                    ]
                },
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {
                            "name": "template_data",
                            "value": "={{ $node['Route Template Operation'].json }}"
                        }
                    ]
                }
            },
            credentials={
                "httpHeaderAuth": f"whatsapp_credentials_{self.tenant_id}"
            },
            position=[300, 200]
        )
        template_workflow.add_node(execute_node)
        template_workflow.add_connection(router_node.name, execute_node.name)
        
        return template_workflow.build_workflow()
