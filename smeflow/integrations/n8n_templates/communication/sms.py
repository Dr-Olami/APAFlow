"""
SMS Gateway Integration Template for n8N.

Provides comprehensive SMS integration for African markets including:
- Multiple SMS providers (Twilio, Africa's Talking, Termii, etc.)
- Bulk SMS sending
- Delivery status tracking
- Multi-language support
- Cost optimization and provider failover
"""

from typing import Dict, Any, Optional, List
from ..base_template import N8nWorkflowTemplate, N8nNode, SimpleN8nWorkflowTemplate


class SMSWorkflowTemplate(N8nWorkflowTemplate):
    """
    SMS gateway workflow template for African markets.
    
    Supports multiple SMS providers with failover, bulk messaging,
    delivery tracking, and cost optimization features.
    """
    
    def __init__(self, tenant_id: str, primary_provider: str = "africas_talking", country_code: str = "NG"):
        """
        Initialize SMS workflow template.
        
        Args:
            tenant_id: Unique identifier for the tenant
            primary_provider: Primary SMS provider (africas_talking, twilio, termii, etc.)
            country_code: Country code for local provider optimization
        """
        super().__init__(tenant_id, "SMS Gateway")
        self.primary_provider = primary_provider
        self.country_code = country_code.upper()
        self.provider_config = self._get_provider_config()
        
    def _get_provider_config(self) -> Dict[str, Any]:
        """Get SMS provider configuration based on country and provider."""
        providers = {
            "africas_talking": {
                "name": "Africa's Talking",
                "base_url": "https://api.africastalking.com/version1",
                "supported_countries": ["KE", "UG", "TZ", "RW", "MW", "ZM"],
                "cost_per_sms": 0.02,  # USD
                "features": ["bulk_sms", "delivery_reports", "sender_id"]
            },
            "twilio": {
                "name": "Twilio",
                "base_url": "https://api.twilio.com/2010-04-01",
                "supported_countries": ["NG", "KE", "ZA", "GH", "EG", "MA"],
                "cost_per_sms": 0.05,  # USD
                "features": ["global_coverage", "delivery_reports", "two_way_sms"]
            },
            "termii": {
                "name": "Termii",
                "base_url": "https://api.ng.termii.com/api",
                "supported_countries": ["NG", "GH", "KE", "UG"],
                "cost_per_sms": 0.015,  # USD
                "features": ["bulk_sms", "otp", "sender_id", "local_routes"]
            },
            "clickatell": {
                "name": "Clickatell",
                "base_url": "https://platform.clickatell.com",
                "supported_countries": ["ZA", "NG", "KE", "GH", "EG"],
                "cost_per_sms": 0.04,  # USD
                "features": ["global_coverage", "delivery_reports", "rich_messaging"]
            }
        }
        
        return providers.get(self.primary_provider, providers["twilio"])
    
    def build_workflow(self) -> Dict[str, Any]:
        """
        Build complete SMS gateway workflow.
        
        Returns:
            Complete n8N workflow definition for SMS integration
        """
        # 1. Webhook trigger for SMS operations
        webhook_trigger = self.create_webhook_trigger("sms/send")
        self.add_node(webhook_trigger)
        
        # 2. SMS validation and routing
        validation_node = self._create_sms_validation_node()
        self.add_node(validation_node)
        self.add_connection(webhook_trigger.name, validation_node.name)
        
        # 3. Provider selection and failover
        provider_node = self._create_provider_selection_node()
        self.add_node(provider_node)
        self.add_connection(validation_node.name, provider_node.name)
        
        # 4. Single SMS sending
        single_sms_node = self._create_single_sms_node()
        self.add_node(single_sms_node)
        
        # 5. Bulk SMS sending
        bulk_sms_node = self._create_bulk_sms_node()
        self.add_node(bulk_sms_node)
        
        # 6. Response formatter
        response_node = self._create_response_formatter()
        self.add_node(response_node)
        
        # Connect provider selection to SMS types
        self.add_connection(provider_node.name, single_sms_node.name)
        self.add_connection(provider_node.name, bulk_sms_node.name)
        
        # Connect SMS types to response formatter
        self.add_connection(single_sms_node.name, response_node.name)
        self.add_connection(bulk_sms_node.name, response_node.name)
        
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
            "connections": self._serialize_connections(),
            "staticData": {
                "sms_config": {
                    "primary_provider": self.primary_provider,
                    "country_code": self.country_code,
                    "provider_config": self.provider_config,
                    "supported_operations": [
                        "send_single", "send_bulk", "check_status", "get_balance"
                    ],
                    "failover_providers": self._get_failover_providers(),
                    "cost_optimization": True
                }
            }
        }
        
        return workflow_def
    
    def _get_failover_providers(self) -> List[str]:
        """Get list of failover providers for the country."""
        country_providers = {
            "NG": ["termii", "twilio", "clickatell"],
            "KE": ["africas_talking", "twilio", "clickatell"],
            "ZA": ["clickatell", "twilio", "africas_talking"],
            "GH": ["termii", "twilio", "clickatell"],
            "UG": ["africas_talking", "termii", "twilio"],
            "TZ": ["africas_talking", "twilio", "clickatell"]
        }
        
        providers = country_providers.get(self.country_code, ["twilio", "clickatell"])
        # Remove primary provider from failover list
        return [p for p in providers if p != self.primary_provider]
    
    def _create_sms_validation_node(self) -> N8nNode:
        """Create SMS validation and routing node."""
        return N8nNode(
            name="Validate SMS Request",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": f"""
// Validate SMS request and prepare routing
const input = $input.first().json;

// Validate required fields
if (!input.message) {{
    throw new Error('SMS message content is required');
}}

// Determine if single or bulk SMS
let smsType = 'single';
let recipients = [];

if (input.to) {{
    // Single recipient
    if (typeof input.to === 'string') {{
        recipients = [input.to];
    }} else if (Array.isArray(input.to)) {{
        recipients = input.to;
        smsType = recipients.length > 1 ? 'bulk' : 'single';
    }}
}} else if (input.recipients && Array.isArray(input.recipients)) {{
    // Bulk recipients
    recipients = input.recipients;
    smsType = 'bulk';
}} else {{
    throw new Error('Recipient phone number(s) required');
}}

// Validate phone numbers
const phoneRegex = /^\\+[1-9]\\d{{7,14}}$/;
const validRecipients = [];
const invalidNumbers = [];

for (const recipient of recipients) {{
    const phone = typeof recipient === 'string' ? recipient : recipient.phone;
    if (phoneRegex.test(phone)) {{
        validRecipients.push({{
            phone: phone,
            name: typeof recipient === 'object' ? recipient.name : null
        }});
    }} else {{
        invalidNumbers.push(phone);
    }}
}}

if (invalidNumbers.length > 0) {{
    throw new Error(`Invalid phone numbers: ${{invalidNumbers.join(', ')}}`);
}}

if (validRecipients.length === 0) {{
    throw new Error('No valid recipients found');
}}

// Validate message length
const message = input.message;
const maxLength = 1600; // SMS character limit
if (message.length > maxLength) {{
    throw new Error(`Message too long. Maximum ${{maxLength}} characters allowed.`);
}}

// Calculate SMS parts (160 chars per SMS for GSM, 70 for Unicode)
const isUnicode = /[^\\x00-\\x7F]/.test(message);
const charsPerSms = isUnicode ? 70 : 160;
const smsParts = Math.ceil(message.length / charsPerSms);

return [{{
    json: {{
        sms_type: smsType,
        message: message,
        recipients: validRecipients,
        sender_id: input.sender_id || 'SMEFlow',
        priority: input.priority || 'normal',
        schedule_time: input.schedule_time || null,
        sms_parts: smsParts,
        estimated_cost: smsParts * validRecipients.length * 0.02, // Rough estimate
        country_code: '{self.country_code}',
        tenant_id: '{self.tenant_id}',
        created_at: new Date().toISOString()
    }}
}}];
"""
            },
            position=[200, 200]
        )
    
    def _create_provider_selection_node(self) -> N8nNode:
        """Create SMS provider selection and failover node."""
        return N8nNode(
            name="Select SMS Provider",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": f"""
// Select optimal SMS provider based on country, cost, and availability
const smsData = $node['Validate SMS Request'].json;

// Provider configurations
const providers = {{
    'africas_talking': {{
        name: 'Africa\\'s Talking',
        base_url: 'https://api.africastalking.com/version1',
        supported_countries: ['KE', 'UG', 'TZ', 'RW', 'MW', 'ZM'],
        cost_per_sms: 0.02,
        auth_type: 'api_key'
    }},
    'twilio': {{
        name: 'Twilio',
        base_url: 'https://api.twilio.com/2010-04-01',
        supported_countries: ['NG', 'KE', 'ZA', 'GH', 'EG', 'MA'],
        cost_per_sms: 0.05,
        auth_type: 'basic'
    }},
    'termii': {{
        name: 'Termii',
        base_url: 'https://api.ng.termii.com/api',
        supported_countries: ['NG', 'GH', 'KE', 'UG'],
        cost_per_sms: 0.015,
        auth_type: 'api_key'
    }},
    'clickatell': {{
        name: 'Clickatell',
        base_url: 'https://platform.clickatell.com',
        supported_countries: ['ZA', 'NG', 'KE', 'GH', 'EG'],
        cost_per_sms: 0.04,
        auth_type: 'bearer'
    }}
}};

// Primary provider selection
let selectedProvider = '{self.primary_provider}';
let providerConfig = providers[selectedProvider];

// Check if primary provider supports the country
if (!providerConfig.supported_countries.includes(smsData.country_code)) {{
    // Find best alternative provider
    const alternatives = Object.keys(providers).filter(p => 
        providers[p].supported_countries.includes(smsData.country_code)
    );
    
    if (alternatives.length > 0) {{
        // Select cheapest alternative
        selectedProvider = alternatives.reduce((best, current) => 
            providers[current].cost_per_sms < providers[best].cost_per_sms ? current : best
        );
        providerConfig = providers[selectedProvider];
    }} else {{
        // Fallback to Twilio for global coverage
        selectedProvider = 'twilio';
        providerConfig = providers['twilio'];
    }}
}}

// Calculate actual cost
const actualCost = smsData.sms_parts * smsData.recipients.length * providerConfig.cost_per_sms;

return [{{
    json: {{
        ...smsData,
        selected_provider: selectedProvider,
        provider_config: providerConfig,
        actual_cost: actualCost,
        provider_selected_at: new Date().toISOString()
    }}
}}];
"""
            },
            position=[300, 200]
        )
    
    def _create_single_sms_node(self) -> N8nNode:
        """Create single SMS sending node."""
        return N8nNode(
            name="Send Single SMS",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Handle single SMS sending
const smsData = $node['Select SMS Provider'].json;

if (smsData.sms_type !== 'single') {
    return []; // Skip if not single SMS
}

const recipient = smsData.recipients[0];
const provider = smsData.selected_provider;

let apiPayload = {};
let apiUrl = '';

// Prepare provider-specific payload
switch (provider) {
    case 'africas_talking':
        apiPayload = {
            username: 'AFRICAS_TALKING_USERNAME',
            to: recipient.phone,
            message: smsData.message,
            from: smsData.sender_id
        };
        apiUrl = `${smsData.provider_config.base_url}/messaging`;
        break;
        
    case 'twilio':
        apiPayload = {
            To: recipient.phone,
            From: smsData.sender_id,
            Body: smsData.message
        };
        apiUrl = `${smsData.provider_config.base_url}/Accounts/TWILIO_ACCOUNT_SID/Messages.json`;
        break;
        
    case 'termii':
        apiPayload = {
            to: recipient.phone,
            from: smsData.sender_id,
            sms: smsData.message,
            type: 'plain',
            channel: 'generic',
            api_key: 'TERMII_API_KEY'
        };
        apiUrl = `${smsData.provider_config.base_url}/sms/send`;
        break;
        
    case 'clickatell':
        apiPayload = {
            messages: [{
                to: [recipient.phone],
                content: smsData.message,
                from: smsData.sender_id
            }]
        };
        apiUrl = `${smsData.provider_config.base_url}/v1/message`;
        break;
}

return [{
    json: {
        sms_type: 'single',
        provider: provider,
        api_url: apiUrl,
        api_payload: apiPayload,
        recipient: recipient,
        message: smsData.message,
        estimated_cost: smsData.actual_cost,
        prepared_at: new Date().toISOString()
    }
}];
"""
            },
            position=[400, 100]
        )
    
    def _create_bulk_sms_node(self) -> N8nNode:
        """Create bulk SMS sending node."""
        return N8nNode(
            name="Send Bulk SMS",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Handle bulk SMS sending
const smsData = $node['Select SMS Provider'].json;

if (smsData.sms_type !== 'bulk') {
    return []; // Skip if not bulk SMS
}

const recipients = smsData.recipients;
const provider = smsData.selected_provider;

let apiPayload = {};
let apiUrl = '';

// Prepare provider-specific bulk payload
switch (provider) {
    case 'africas_talking':
        apiPayload = {
            username: 'AFRICAS_TALKING_USERNAME',
            to: recipients.map(r => r.phone).join(','),
            message: smsData.message,
            from: smsData.sender_id,
            bulkSMSMode: 1
        };
        apiUrl = `${smsData.provider_config.base_url}/messaging`;
        break;
        
    case 'twilio':
        // Twilio doesn't have native bulk SMS, so we'll batch them
        apiPayload = {
            messages: recipients.map(recipient => ({
                To: recipient.phone,
                From: smsData.sender_id,
                Body: smsData.message
            }))
        };
        apiUrl = `${smsData.provider_config.base_url}/Accounts/TWILIO_ACCOUNT_SID/Messages.json`;
        break;
        
    case 'termii':
        apiPayload = {
            to: recipients.map(r => r.phone),
            from: smsData.sender_id,
            sms: smsData.message,
            type: 'plain',
            channel: 'generic',
            api_key: 'TERMII_API_KEY'
        };
        apiUrl = `${smsData.provider_config.base_url}/sms/send/bulk`;
        break;
        
    case 'clickatell':
        apiPayload = {
            messages: [{
                to: recipients.map(r => r.phone),
                content: smsData.message,
                from: smsData.sender_id
            }]
        };
        apiUrl = `${smsData.provider_config.base_url}/v1/message`;
        break;
}

// Calculate batch information
const batchSize = 1000; // Most providers support up to 1000 recipients per batch
const totalBatches = Math.ceil(recipients.length / batchSize);

return [{
    json: {
        sms_type: 'bulk',
        provider: provider,
        api_url: apiUrl,
        api_payload: apiPayload,
        recipient_count: recipients.length,
        batch_size: batchSize,
        total_batches: totalBatches,
        estimated_cost: smsData.actual_cost,
        prepared_at: new Date().toISOString()
    }
}];
"""
            },
            position=[400, 200]
        )
    
    def _create_response_formatter(self) -> N8nNode:
        """Create response formatting node for SMS operations."""
        return N8nNode(
            name="Format SMS Response",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Format SMS response for SMEFlow
const inputs = $input.all();
let smsResult = null;

// Find the result from the executed SMS operation
for (const input of inputs) {
    if (input.json && input.json.sms_type) {
        smsResult = input.json;
        break;
    }
}

if (!smsResult) {
    throw new Error('No SMS operation result found');
}

// Make actual API call to SMS provider
// This would be replaced with actual HTTP request node in production
const mockResponse = {
    success: true,
    message_id: `SMS_${Date.now()}`,
    status: 'sent',
    provider_response: {
        provider: smsResult.provider,
        cost: smsResult.estimated_cost,
        message_count: smsResult.sms_type === 'bulk' ? smsResult.recipient_count : 1
    }
};

return [{
    json: {
        success: mockResponse.success,
        sms_type: smsResult.sms_type,
        provider: smsResult.provider,
        message_id: mockResponse.message_id,
        status: mockResponse.status,
        recipient_count: smsResult.sms_type === 'bulk' ? smsResult.recipient_count : 1,
        cost: smsResult.estimated_cost,
        sent_at: new Date().toISOString(),
        metadata: {
            tenant_id: smsResult.tenant_id || 'unknown',
            workflow_id: $workflow.id,
            execution_id: $execution.id
        }
    }
}];
"""
            },
            position=[500, 150]
        )
    
    def create_delivery_tracking_workflow(self) -> Dict[str, Any]:
        """
        Create a workflow for tracking SMS delivery status.
        
        Returns:
            n8N workflow definition for SMS delivery tracking
        """
        tracking_workflow = SimpleN8nWorkflowTemplate(self.tenant_id, "SMS Delivery Tracking")
        
        # 1. Webhook trigger for delivery status updates
        status_trigger = tracking_workflow.create_webhook_trigger("sms/status")
        tracking_workflow.add_node(status_trigger)
        
        # 2. Parse delivery status
        parse_node = N8nNode(
            name="Parse Delivery Status",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Parse SMS delivery status from provider webhook
const input = $input.first().json;

let parsedStatus = {
    message_id: null,
    status: 'unknown',
    recipient: null,
    delivered_at: null,
    error_code: null,
    error_message: null,
    provider: 'unknown'
};

// Parse based on provider format
if (input.MessageSid) {
    // Twilio format
    parsedStatus = {
        message_id: input.MessageSid,
        status: input.MessageStatus,
        recipient: input.To,
        delivered_at: input.DateSent,
        error_code: input.ErrorCode,
        error_message: input.ErrorMessage,
        provider: 'twilio'
    };
} else if (input.id && input.status) {
    // Africa's Talking format
    parsedStatus = {
        message_id: input.id,
        status: input.status,
        recipient: input.phoneNumber,
        delivered_at: input.sentAt,
        error_code: input.failureReason ? 'DELIVERY_FAILED' : null,
        error_message: input.failureReason,
        provider: 'africas_talking'
    };
} else if (input.message_id) {
    // Termii format
    parsedStatus = {
        message_id: input.message_id,
        status: input.status,
        recipient: input.phone_number,
        delivered_at: input.sent_at,
        error_code: input.error_code,
        error_message: input.error_message,
        provider: 'termii'
    };
}

return [{
    json: {
        ...parsedStatus,
        received_at: new Date().toISOString(),
        tenant_id: input.tenant_id || 'unknown'
    }
}];
"""
            },
            position=[200, 200]
        )
        tracking_workflow.add_node(parse_node)
        tracking_workflow.add_connection(status_trigger.name, parse_node.name)
        
        # 3. Update SMS status in SMEFlow
        update_node = N8nNode(
            name="Update SMS Status",
            type="n8n-nodes-base.httpRequest",
            parameters={
                "url": f"http://smeflow-api:8000/api/v1/communication/sms/status/{self.tenant_id}",
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
                            "name": "status_update",
                            "value": "={{ $node['Parse Delivery Status'].json }}"
                        }
                    ]
                }
            },
            position=[300, 200]
        )
        tracking_workflow.add_node(update_node)
        tracking_workflow.add_connection(parse_node.name, update_node.name)
        
        return tracking_workflow.build_workflow()
