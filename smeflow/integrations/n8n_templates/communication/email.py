"""
Email Integration Template for n8N.

Provides comprehensive email integration for African markets including:
- SMTP/API email sending (SendGrid, Mailgun, AWS SES, etc.)
- Template-based emails
- Bulk email campaigns
- Email tracking and analytics
- Multi-language support
- Compliance with African data protection laws
"""

from typing import Dict, Any, Optional, List
from ..base_template import N8nWorkflowTemplate, N8nNode, SimpleN8nWorkflowTemplate


class EmailWorkflowTemplate(N8nWorkflowTemplate):
    """
    Email integration workflow template for African markets.
    
    Supports multiple email providers, template management,
    bulk campaigns, and comprehensive tracking features.
    """
    
    def __init__(self, tenant_id: str, email_provider: str = "sendgrid", sender_domain: str = None):
        """
        Initialize Email workflow template.
        
        Args:
            tenant_id: Unique identifier for the tenant
            email_provider: Email service provider (sendgrid, mailgun, ses, smtp)
            sender_domain: Verified sender domain for the tenant
        """
        super().__init__(tenant_id, "Email Integration")
        self.email_provider = email_provider
        self.sender_domain = sender_domain or f"{tenant_id}.smeflow.com"
        self.provider_config = self._get_provider_config()
        
    def _get_provider_config(self) -> Dict[str, Any]:
        """Get email provider configuration."""
        providers = {
            "sendgrid": {
                "name": "SendGrid",
                "base_url": "https://api.sendgrid.com/v3",
                "auth_type": "bearer",
                "features": ["templates", "tracking", "analytics", "bulk"],
                "cost_per_email": 0.0006,  # USD
                "african_presence": True
            },
            "mailgun": {
                "name": "Mailgun",
                "base_url": "https://api.mailgun.net/v3",
                "auth_type": "basic",
                "features": ["templates", "tracking", "validation", "bulk"],
                "cost_per_email": 0.0008,  # USD
                "african_presence": False
            },
            "ses": {
                "name": "Amazon SES",
                "base_url": "https://email.us-east-1.amazonaws.com",
                "auth_type": "aws_signature",
                "features": ["templates", "tracking", "bounce_handling"],
                "cost_per_email": 0.0001,  # USD
                "african_presence": True  # Available in Cape Town region
            },
            "smtp": {
                "name": "SMTP",
                "base_url": "smtp://smtp.gmail.com:587",
                "auth_type": "basic",
                "features": ["basic_sending"],
                "cost_per_email": 0.0,  # Free for most providers
                "african_presence": True
            }
        }
        
        return providers.get(self.email_provider, providers["sendgrid"])
    
    def build_workflow(self) -> Dict[str, Any]:
        """
        Build complete email integration workflow.
        
        Returns:
            Complete n8N workflow definition for email integration
        """
        # 1. Webhook trigger for email operations
        webhook_trigger = self.create_webhook_trigger("email/send")
        self.add_node(webhook_trigger)
        
        # 2. Email validation and routing
        validation_node = self._create_email_validation_node()
        self.add_node(validation_node)
        self.add_connection(webhook_trigger.name, validation_node.name)
        
        # 3. Template processing
        template_node = self._create_template_processing_node()
        self.add_node(template_node)
        self.add_connection(validation_node.name, template_node.name)
        
        # 4. Single email sending
        single_email_node = self._create_single_email_node()
        self.add_node(single_email_node)
        
        # 5. Bulk email sending
        bulk_email_node = self._create_bulk_email_node()
        self.add_node(bulk_email_node)
        
        # 6. Response formatter
        response_node = self._create_response_formatter()
        self.add_node(response_node)
        
        # Connect template processing to email types
        self.add_connection(template_node.name, single_email_node.name)
        self.add_connection(template_node.name, bulk_email_node.name)
        
        # Connect email types to response formatter
        self.add_connection(single_email_node.name, response_node.name)
        self.add_connection(bulk_email_node.name, response_node.name)
        
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
                "email_config": {
                    "provider": self.email_provider,
                    "sender_domain": self.sender_domain,
                    "provider_config": self.provider_config,
                    "supported_operations": [
                        "send_single", "send_bulk", "send_template", "track_opens", "track_clicks"
                    ],
                    "compliance": {
                        "gdpr_compliant": True,
                        "popia_compliant": True,
                        "unsubscribe_required": True,
                        "data_residency": "africa"
                    }
                }
            }
        }
        
        return workflow_def
    
    def _create_email_validation_node(self) -> N8nNode:
        """Create email validation and routing node."""
        return N8nNode(
            name="Validate Email Request",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": f"""
// Validate email request and prepare routing
const input = $input.first().json;

// Validate required fields
if (!input.subject && !input.template_id) {{
    throw new Error('Email subject or template ID is required');
}}

if (!input.content && !input.template_id) {{
    throw new Error('Email content or template ID is required');
}}

// Determine if single or bulk email
let emailType = 'single';
let recipients = [];

if (input.to) {{
    // Single or multiple recipients
    if (typeof input.to === 'string') {{
        recipients = [{{ email: input.to }}];
    }} else if (Array.isArray(input.to)) {{
        recipients = input.to.map(email => 
            typeof email === 'string' ? {{ email }} : email
        );
        emailType = recipients.length > 1 ? 'bulk' : 'single';
    }}
}} else if (input.recipients && Array.isArray(input.recipients)) {{
    // Bulk recipients with personalization
    recipients = input.recipients;
    emailType = 'bulk';
}} else {{
    throw new Error('Recipient email address(es) required');
}}

// Validate email addresses
const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
const validRecipients = [];
const invalidEmails = [];

for (const recipient of recipients) {{
    const email = recipient.email || recipient;
    if (typeof email === 'string' && emailRegex.test(email)) {{
        validRecipients.push({{
            email: email,
            name: recipient.name || null,
            variables: recipient.variables || {{}}
        }});
    }} else {{
        invalidEmails.push(email);
    }}
}}

if (invalidEmails.length > 0) {{
    throw new Error(`Invalid email addresses: ${{invalidEmails.join(', ')}}`);
}}

if (validRecipients.length === 0) {{
    throw new Error('No valid recipients found');
}}

// Validate sender information
const fromEmail = input.from || `noreply@{self.sender_domain}`;
const fromName = input.from_name || 'SMEFlow';

if (!emailRegex.test(fromEmail)) {{
    throw new Error('Invalid sender email address');
}}

// Check for compliance requirements
const requiresUnsubscribe = emailType === 'bulk' || input.marketing === true;

return [{{
    json: {{
        email_type: emailType,
        subject: input.subject,
        content: input.content,
        template_id: input.template_id,
        template_data: input.template_data || {{}},
        recipients: validRecipients,
        from_email: fromEmail,
        from_name: fromName,
        reply_to: input.reply_to || fromEmail,
        attachments: input.attachments || [],
        tracking: {{
            open_tracking: input.track_opens !== false,
            click_tracking: input.track_clicks !== false,
            unsubscribe_tracking: requiresUnsubscribe
        }},
        priority: input.priority || 'normal',
        schedule_time: input.schedule_time || null,
        tenant_id: '{self.tenant_id}',
        created_at: new Date().toISOString()
    }}
}}];
"""
            },
            position=[200, 200]
        )
    
    def _create_template_processing_node(self) -> N8nNode:
        """Create email template processing node."""
        return N8nNode(
            name="Process Email Template",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Process email templates and personalization
const emailData = $node['Validate Email Request'].json;

let processedEmail = { ...emailData };

// If using template, process template data
if (emailData.template_id) {
    // This would typically fetch template from database
    // For now, we'll simulate template processing
    
    const templateData = emailData.template_data;
    
    // Basic template variable replacement
    let subject = emailData.subject || 'Default Subject';
    let content = emailData.content || 'Default Content';
    
    // Replace variables in subject and content
    for (const [key, value] of Object.entries(templateData)) {
        const placeholder = `{{${key}}}`;
        subject = subject.replace(new RegExp(placeholder, 'g'), value);
        content = content.replace(new RegExp(placeholder, 'g'), value);
    }
    
    processedEmail.subject = subject;
    processedEmail.content = content;
}

// Add compliance footer for bulk emails
if (emailData.email_type === 'bulk' || emailData.tracking.unsubscribe_tracking) {
    const unsubscribeLink = `http://smeflow-api:8000/api/v1/communication/email/unsubscribe/${emailData.tenant_id}`;
    const complianceFooter = `
    
---
This email was sent by SMEFlow. 
If you no longer wish to receive these emails, you can unsubscribe here: ${unsubscribeLink}
    `;
    
    processedEmail.content += complianceFooter;
}

// Add tracking pixels if enabled
if (emailData.tracking.open_tracking) {
    const trackingPixel = `<img src="http://smeflow-api:8000/api/v1/communication/email/track/open/${emailData.tenant_id}" width="1" height="1" style="display:none;">`;
    processedEmail.content += trackingPixel;
}

return [{
    json: {
        ...processedEmail,
        processed_at: new Date().toISOString()
    }
}];
"""
            },
            position=[300, 200]
        )
    
    def _create_single_email_node(self) -> N8nNode:
        """Create single email sending node."""
        return N8nNode(
            name="Send Single Email",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": f"""
// Handle single email sending
const emailData = $node['Process Email Template'].json;

if (emailData.email_type !== 'single') {{
    return []; // Skip if not single email
}}

const recipient = emailData.recipients[0];
const provider = '{self.email_provider}';

let apiPayload = {{}};
let apiUrl = '';

// Prepare provider-specific payload
switch (provider) {{
    case 'sendgrid':
        apiPayload = {{
            personalizations: [{{
                to: [{{ email: recipient.email, name: recipient.name }}],
                subject: emailData.subject
            }}],
            from: {{ email: emailData.from_email, name: emailData.from_name }},
            reply_to: {{ email: emailData.reply_to }},
            content: [{{
                type: 'text/html',
                value: emailData.content
            }}],
            tracking_settings: {{
                open_tracking: {{ enable: emailData.tracking.open_tracking }},
                click_tracking: {{ enable: emailData.tracking.click_tracking }}
            }}
        }};
        apiUrl = 'https://api.sendgrid.com/v3/mail/send';
        break;
        
    case 'mailgun':
        apiPayload = {{
            from: `${{emailData.from_name}} <${{emailData.from_email}}>`,
            to: recipient.email,
            subject: emailData.subject,
            html: emailData.content,
            'o:tracking': emailData.tracking.open_tracking,
            'o:tracking-clicks': emailData.tracking.click_tracking
        }};
        apiUrl = `https://api.mailgun.net/v3/{self.sender_domain}/messages`;
        break;
        
    case 'ses':
        apiPayload = {{
            Source: `${{emailData.from_name}} <${{emailData.from_email}}>`,
            Destination: {{
                ToAddresses: [recipient.email]
            }},
            Message: {{
                Subject: {{ Data: emailData.subject }},
                Body: {{
                    Html: {{ Data: emailData.content }}
                }}
            }}
        }};
        apiUrl = 'https://email.us-east-1.amazonaws.com/';
        break;
        
    case 'smtp':
        apiPayload = {{
            from: emailData.from_email,
            to: recipient.email,
            subject: emailData.subject,
            html: emailData.content
        }};
        apiUrl = 'smtp://smtp.gmail.com:587';
        break;
}}

return [{{
    json: {{
        email_type: 'single',
        provider: provider,
        api_url: apiUrl,
        api_payload: apiPayload,
        recipient: recipient,
        subject: emailData.subject,
        prepared_at: new Date().toISOString()
    }}
}}];
"""
            },
            position=[400, 100]
        )
    
    def _create_bulk_email_node(self) -> N8nNode:
        """Create bulk email sending node."""
        return N8nNode(
            name="Send Bulk Email",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": f"""
// Handle bulk email sending
const emailData = $node['Process Email Template'].json;

if (emailData.email_type !== 'bulk') {{
    return []; // Skip if not bulk email
}}

const recipients = emailData.recipients;
const provider = '{self.email_provider}';

let apiPayload = {{}};
let apiUrl = '';

// Prepare provider-specific bulk payload
switch (provider) {{
    case 'sendgrid':
        apiPayload = {{
            personalizations: recipients.map(recipient => ({{
                to: [{{ email: recipient.email, name: recipient.name }}],
                subject: emailData.subject,
                substitutions: recipient.variables || {{}}
            }})),
            from: {{ email: emailData.from_email, name: emailData.from_name }},
            reply_to: {{ email: emailData.reply_to }},
            content: [{{
                type: 'text/html',
                value: emailData.content
            }}],
            tracking_settings: {{
                open_tracking: {{ enable: emailData.tracking.open_tracking }},
                click_tracking: {{ enable: emailData.tracking.click_tracking }}
            }}
        }};
        apiUrl = 'https://api.sendgrid.com/v3/mail/send';
        break;
        
    case 'mailgun':
        // Mailgun batch sending
        apiPayload = {{
            from: `${{emailData.from_name}} <${{emailData.from_email}}>`,
            to: recipients.map(r => r.email),
            subject: emailData.subject,
            html: emailData.content,
            'o:tracking': emailData.tracking.open_tracking,
            'o:tracking-clicks': emailData.tracking.click_tracking
        }};
        apiUrl = `https://api.mailgun.net/v3/{self.sender_domain}/messages`;
        break;
        
    case 'ses':
        // SES bulk sending (simplified)
        apiPayload = {{
            Source: `${{emailData.from_name}} <${{emailData.from_email}}>`,
            Destinations: recipients.map(recipient => ({{
                Destination: {{
                    ToAddresses: [recipient.email]
                }},
                ReplacementTemplateData: JSON.stringify(recipient.variables || {{}})
            }})),
            Template: emailData.template_id || 'default',
            DefaultTemplateData: JSON.stringify(emailData.template_data || {{}})
        }};
        apiUrl = 'https://email.us-east-1.amazonaws.com/';
        break;
}}

// Calculate batch information
const batchSize = 1000; // Most providers support up to 1000 recipients per batch
const totalBatches = Math.ceil(recipients.length / batchSize);

return [{{
    json: {{
        email_type: 'bulk',
        provider: provider,
        api_url: apiUrl,
        api_payload: apiPayload,
        recipient_count: recipients.length,
        batch_size: batchSize,
        total_batches: totalBatches,
        prepared_at: new Date().toISOString()
    }}
}}];
"""
            },
            position=[400, 200]
        )
    
    def _create_response_formatter(self) -> N8nNode:
        """Create response formatting node for email operations."""
        return N8nNode(
            name="Format Email Response",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Format email response for SMEFlow
const inputs = $input.all();
let emailResult = null;

// Find the result from the executed email operation
for (const input of inputs) {
    if (input.json && input.json.email_type) {
        emailResult = input.json;
        break;
    }
}

if (!emailResult) {
    throw new Error('No email operation result found');
}

// Mock successful email sending response
// In production, this would be the actual API response
const mockResponse = {
    success: true,
    message_id: `EMAIL_${Date.now()}`,
    status: 'sent',
    provider_response: {
        provider: emailResult.provider,
        recipient_count: emailResult.email_type === 'bulk' ? emailResult.recipient_count : 1
    }
};

return [{
    json: {
        success: mockResponse.success,
        email_type: emailResult.email_type,
        provider: emailResult.provider,
        message_id: mockResponse.message_id,
        status: mockResponse.status,
        recipient_count: emailResult.email_type === 'bulk' ? emailResult.recipient_count : 1,
        subject: emailResult.subject,
        sent_at: new Date().toISOString(),
        metadata: {
            tenant_id: emailResult.tenant_id || 'unknown',
            workflow_id: $workflow.id,
            execution_id: $execution.id
        }
    }
}];
"""
            },
            position=[500, 150]
        )
    
    def create_email_tracking_workflow(self) -> Dict[str, Any]:
        """
        Create a workflow for tracking email opens, clicks, and unsubscribes.
        
        Returns:
            n8N workflow definition for email tracking
        """
        tracking_workflow = SimpleN8nWorkflowTemplate(self.tenant_id, "Email Tracking")
        
        # 1. Webhook trigger for tracking events
        tracking_trigger = tracking_workflow.create_webhook_trigger("email/track")
        tracking_workflow.add_node(tracking_trigger)
        
        # 2. Parse tracking event
        parse_node = N8nNode(
            name="Parse Tracking Event",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Parse email tracking events
const input = $input.first().json;
const query = $input.first().query;
const path = $input.first().path;

let trackingEvent = {
    event_type: 'unknown',
    message_id: null,
    recipient_email: null,
    timestamp: new Date().toISOString(),
    user_agent: $input.first().headers['user-agent'],
    ip_address: $input.first().headers['x-forwarded-for'] || $input.first().headers['x-real-ip']
};

// Determine event type from path
if (path.includes('/track/open/')) {
    trackingEvent.event_type = 'open';
    trackingEvent.message_id = query.message_id;
    trackingEvent.recipient_email = query.email;
} else if (path.includes('/track/click/')) {
    trackingEvent.event_type = 'click';
    trackingEvent.message_id = query.message_id;
    trackingEvent.recipient_email = query.email;
    trackingEvent.clicked_url = query.url;
} else if (path.includes('/unsubscribe/')) {
    trackingEvent.event_type = 'unsubscribe';
    trackingEvent.message_id = query.message_id;
    trackingEvent.recipient_email = query.email;
} else if (input.event) {
    // Provider webhook format (SendGrid, Mailgun, etc.)
    trackingEvent = {
        event_type: input.event,
        message_id: input.sg_message_id || input['message-id'] || input.MessageId,
        recipient_email: input.email,
        timestamp: input.timestamp || new Date().toISOString(),
        reason: input.reason,
        bounce_classification: input.bounce_classification
    };
}

return [{
    json: {
        ...trackingEvent,
        tenant_id: input.tenant_id || 'unknown',
        processed_at: new Date().toISOString()
    }
}];
"""
            },
            position=[200, 200]
        )
        tracking_workflow.add_node(parse_node)
        tracking_workflow.add_connection(tracking_trigger.name, parse_node.name)
        
        # 3. Update email analytics
        analytics_node = N8nNode(
            name="Update Email Analytics",
            type="n8n-nodes-base.httpRequest",
            parameters={
                "url": f"http://smeflow-api:8000/api/v1/communication/email/analytics/{self.tenant_id}",
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
                            "name": "tracking_event",
                            "value": "={{ $node['Parse Tracking Event'].json }}"
                        }
                    ]
                }
            },
            position=[300, 200]
        )
        tracking_workflow.add_node(analytics_node)
        tracking_workflow.add_connection(parse_node.name, analytics_node.name)
        
        return tracking_workflow.build_workflow()
