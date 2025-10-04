"""
Paystack Payment Integration Template for n8N.

Provides comprehensive Paystack integration for Nigerian market including:
- Transaction initialization
- Payment verification
- Webhook handling
- Multi-channel support (cards, bank transfer, mobile money)
- Compliance with Paystack API requirements
"""

from typing import Dict, Any, Optional
from ..base_template import N8nWorkflowTemplate, N8nNode, SimpleN8nWorkflowTemplate


class PaystackWorkflowTemplate(N8nWorkflowTemplate):
    """
    Paystack payment workflow template for Nigerian market.
    
    Supports card payments, bank transfers, and mobile money
    with proper webhook handling and transaction verification.
    """
    
    def __init__(self, tenant_id: str, environment: str = "test"):
        """
        Initialize Paystack workflow template.
        
        Args:
            tenant_id: Unique identifier for the tenant
            environment: Paystack environment (test/live)
        """
        super().__init__(tenant_id, "Paystack Payment")
        self.environment = environment
        self.base_url = "https://api.paystack.co"
    
    def build_workflow(self) -> Dict[str, Any]:
        """
        Build complete Paystack payment workflow.
        
        Returns:
            Complete n8N workflow definition for Paystack payments
        """
        # 1. Webhook trigger for payment initialization
        webhook_trigger = self.create_webhook_trigger("paystack/initialize")
        self.add_node(webhook_trigger)
        
        # 2. Input validation
        validation_node = self._create_paystack_validation_node()
        self.add_node(validation_node)
        self.add_connection(webhook_trigger.name, validation_node.name)
        
        # 3. Initialize transaction
        init_node = self._create_transaction_init_node()
        self.add_node(init_node)
        self.add_connection(validation_node.name, init_node.name)
        
        # 4. Response formatting for initialization
        init_response_node = self._create_init_response_formatter()
        self.add_node(init_response_node)
        self.add_connection(init_node.name, init_response_node.name)
        
        # 5. SMEFlow callback for initialization
        callback_node = self.create_smeflow_callback(
            f"http://smeflow-api:8000/api/v1/workflows/callback/{self.tenant_id}"
        )
        self.add_node(callback_node)
        self.add_connection(init_response_node.name, callback_node.name)
        
        # 6. Error handler
        error_node = self.create_error_handler()
        self.add_node(error_node)
        
        workflow_def = {
            **self.get_workflow_metadata(),
            "nodes": [node.model_dump() for node in self.nodes],
            "connections": self._serialize_connections(),
            "staticData": {
                "paystack_config": {
                    "environment": self.environment,
                    "base_url": self.base_url,
                    "webhook_url": f"http://smeflow-api:8000/api/v1/n8n/webhooks/paystack/callback/{self.tenant_id}"
                }
            }
        }
        
        return workflow_def
    
    def _create_paystack_validation_node(self) -> N8nNode:
        """Create input validation node for Paystack payments."""
        return N8nNode(
            name="Validate Paystack Request",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Validate Paystack payment request
const requiredFields = ['email', 'amount'];
const input = $input.first().json;

// Check required fields
for (const field of requiredFields) {
    if (!input[field]) {
        throw new Error(`Missing required field: ${field}`);
    }
}

// Validate email format
const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
if (!emailRegex.test(input.email)) {
    throw new Error('Invalid email format');
}

// Validate amount (minimum 50 kobo for NGN)
const amount = parseFloat(input.amount);
if (amount < 0.5) {
    throw new Error('Amount must be at least 0.5 NGN');
}

// Convert amount to kobo (Paystack uses kobo)
const amountInKobo = Math.round(amount * 100);

// Generate reference if not provided
const reference = input.reference || `PS_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

return [{
    json: {
        email: input.email,
        amount: amountInKobo,
        currency: input.currency || 'NGN',
        reference: reference,
        callback_url: input.callback_url || `http://smeflow-api:8000/api/v1/n8n/webhooks/paystack/callback/${this.tenant_id}`,
        channels: input.channels || ['card', 'bank', 'ussd', 'mobile_money'],
        metadata: {
            tenant_id: '${this.tenant_id}',
            custom_fields: input.custom_fields || [],
            customer_id: input.customer_id || null,
            order_id: input.order_id || null
        },
        split_code: input.split_code || null,
        subaccount: input.subaccount || null
    }
}];
"""
            },
            position=[200, 200]
        )
    
    def _create_transaction_init_node(self) -> N8nNode:
        """Create transaction initialization node."""
        return N8nNode(
            name="Initialize Paystack Transaction",
            type="n8n-nodes-base.httpRequest",
            parameters={
                "url": f"{self.base_url}/transaction/initialize",
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
                            "name": "email",
                            "value": "={{ $node['Validate Paystack Request'].json.email }}"
                        },
                        {
                            "name": "amount",
                            "value": "={{ $node['Validate Paystack Request'].json.amount }}"
                        },
                        {
                            "name": "currency",
                            "value": "={{ $node['Validate Paystack Request'].json.currency }}"
                        },
                        {
                            "name": "reference",
                            "value": "={{ $node['Validate Paystack Request'].json.reference }}"
                        },
                        {
                            "name": "callback_url",
                            "value": "={{ $node['Validate Paystack Request'].json.callback_url }}"
                        },
                        {
                            "name": "channels",
                            "value": "={{ $node['Validate Paystack Request'].json.channels }}"
                        },
                        {
                            "name": "metadata",
                            "value": "={{ $node['Validate Paystack Request'].json.metadata }}"
                        }
                    ]
                }
            },
            credentials={
                "httpHeaderAuth": f"paystack_credentials_{self.tenant_id}"
            },
            position=[300, 200]
        )
    
    def _create_init_response_formatter(self) -> N8nNode:
        """Create response formatting node for initialization."""
        return N8nNode(
            name="Format Initialization Response",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Format Paystack initialization response for SMEFlow
const initResult = $node['Initialize Paystack Transaction'].json;
const originalRequest = $node['Validate Paystack Request'].json;

const isSuccess = initResult.status === true;

return [{
    json: {
        success: isSuccess,
        payment_method: 'paystack',
        provider: 'paystack',
        reference: initResult.data?.reference || originalRequest.reference,
        authorization_url: initResult.data?.authorization_url,
        access_code: initResult.data?.access_code,
        amount: originalRequest.amount / 100, // Convert back to naira
        currency: originalRequest.currency,
        email: originalRequest.email,
        channels: originalRequest.channels,
        status: 'initialized',
        message: initResult.message,
        metadata: {
            tenant_id: originalRequest.metadata.tenant_id,
            workflow_id: $workflow.id,
            execution_id: $execution.id,
            processed_at: new Date().toISOString(),
            environment: '${this.environment}'
        },
        next_action: {
            type: 'redirect',
            url: initResult.data?.authorization_url,
            message: 'Redirect customer to authorization URL to complete payment'
        }
    }
}];
"""
            },
            position=[400, 200]
        )
    
    def create_verification_workflow(self) -> Dict[str, Any]:
        """
        Create a separate workflow for payment verification.
        
        Returns:
            n8N workflow definition for verifying Paystack payments
        """
        verify_workflow = SimpleN8nWorkflowTemplate(self.tenant_id, "Paystack Payment Verification")
        
        # 1. Webhook trigger for verification requests
        verify_trigger = verify_workflow.create_webhook_trigger("paystack/verify")
        verify_workflow.add_node(verify_trigger)
        
        # 2. Extract reference from request
        extract_node = N8nNode(
            name="Extract Reference",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Extract payment reference for verification
const input = $input.first().json;
const reference = input.reference || input.trxref;

if (!reference) {
    throw new Error('Payment reference is required for verification');
}

return [{
    json: {
        reference: reference,
        tenant_id: '${self.tenant_id}',
        requested_at: new Date().toISOString()
    }
}];
"""
            },
            position=[200, 200]
        )
        verify_workflow.add_node(extract_node)
        verify_workflow.add_connection(verify_trigger.name, extract_node.name)
        
        # 3. Verify payment with Paystack
        verify_node = N8nNode(
            name="Verify Payment",
            type="n8n-nodes-base.httpRequest",
            parameters={
                "url": f"{self.base_url}/transaction/verify/{{{{ $node['Extract Reference'].json.reference }}}}",
                "method": "GET",
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
                }
            },
            credentials={
                "httpHeaderAuth": f"paystack_credentials_{self.tenant_id}"
            },
            position=[300, 200]
        )
        verify_workflow.add_node(verify_node)
        verify_workflow.add_connection(extract_node.name, verify_node.name)
        
        # 4. Format verification response
        format_node = N8nNode(
            name="Format Verification Response",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Format Paystack verification response
const verificationResult = $node['Verify Payment'].json;
const originalRequest = $node['Extract Reference'].json;

const isSuccess = verificationResult.status && verificationResult.data.status === 'success';

return [{
    json: {
        success: isSuccess,
        payment_method: 'paystack',
        provider: 'paystack',
        transaction_id: verificationResult.data?.id,
        reference: verificationResult.data?.reference,
        amount: verificationResult.data?.amount / 100, // Convert from kobo
        currency: verificationResult.data?.currency,
        email: verificationResult.data?.customer?.email,
        status: verificationResult.data?.status,
        gateway_response: verificationResult.data?.gateway_response,
        paid_at: verificationResult.data?.paid_at,
        created_at: verificationResult.data?.created_at,
        channel: verificationResult.data?.channel,
        fees: verificationResult.data?.fees,
        authorization: {
            authorization_code: verificationResult.data?.authorization?.authorization_code,
            bin: verificationResult.data?.authorization?.bin,
            last4: verificationResult.data?.authorization?.last4,
            exp_month: verificationResult.data?.authorization?.exp_month,
            exp_year: verificationResult.data?.authorization?.exp_year,
            channel: verificationResult.data?.authorization?.channel,
            card_type: verificationResult.data?.authorization?.card_type,
            bank: verificationResult.data?.authorization?.bank,
            country_code: verificationResult.data?.authorization?.country_code,
            brand: verificationResult.data?.authorization?.brand,
            reusable: verificationResult.data?.authorization?.reusable
        },
        customer: {
            id: verificationResult.data?.customer?.id,
            first_name: verificationResult.data?.customer?.first_name,
            last_name: verificationResult.data?.customer?.last_name,
            email: verificationResult.data?.customer?.email,
            customer_code: verificationResult.data?.customer?.customer_code,
            phone: verificationResult.data?.customer?.phone
        },
        metadata: {
            tenant_id: originalRequest.tenant_id,
            workflow_id: $workflow.id,
            execution_id: $execution.id,
            verified_at: new Date().toISOString(),
            environment: '${self.environment}'
        }
    }
}];
"""
            },
            position=[400, 200]
        )
        verify_workflow.add_node(format_node)
        verify_workflow.add_connection(verify_node.name, format_node.name)
        
        # 5. Update payment status in SMEFlow
        update_node = N8nNode(
            name="Update Payment Status",
            type="n8n-nodes-base.httpRequest",
            parameters={
                "url": f"http://smeflow-api:8000/api/v1/payments/paystack/verify/{self.tenant_id}",
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
                            "name": "verification_result",
                            "value": "={{ $node['Format Verification Response'].json }}"
                        }
                    ]
                }
            },
            position=[500, 200]
        )
        verify_workflow.add_node(update_node)
        verify_workflow.add_connection(format_node.name, update_node.name)
        
        return verify_workflow.build_workflow()
    
    def create_webhook_handler(self) -> Dict[str, Any]:
        """
        Create a webhook handler workflow for Paystack events.
        
        Returns:
            n8N workflow definition for handling Paystack webhooks
        """
        webhook_workflow = SimpleN8nWorkflowTemplate(self.tenant_id, "Paystack Webhook Handler")
        
        # 1. Webhook trigger for Paystack events
        webhook_trigger = webhook_workflow.create_webhook_trigger("paystack/webhook")
        webhook_workflow.add_node(webhook_trigger)
        
        # 2. Validate webhook signature
        validate_node = N8nNode(
            name="Validate Webhook Signature",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Validate Paystack webhook signature
const crypto = require('crypto');
const payload = JSON.stringify($input.first().json);
const signature = $input.first().headers['x-paystack-signature'];
const secret = '${self.tenant_id}_webhook_secret'; // Should be stored securely

const hash = crypto.createHmac('sha512', secret).update(payload).digest('hex');

if (hash !== signature) {
    throw new Error('Invalid webhook signature');
}

const event = $input.first().json;

return [{
    json: {
        event: event.event,
        data: event.data,
        validated: true,
        received_at: new Date().toISOString()
    }
}];
"""
            },
            position=[200, 200]
        )
        webhook_workflow.add_node(validate_node)
        webhook_workflow.add_connection(webhook_trigger.name, validate_node.name)
        
        # 3. Process webhook event
        process_node = N8nNode(
            name="Process Webhook Event",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Process different Paystack webhook events
const webhook = $node['Validate Webhook Signature'].json;
const eventType = webhook.event;
const eventData = webhook.data;

let processedEvent = {
    event_type: eventType,
    processed: true,
    processed_at: new Date().toISOString()
};

switch (eventType) {
    case 'charge.success':
        processedEvent = {
            ...processedEvent,
            payment_status: 'completed',
            transaction_id: eventData.id,
            reference: eventData.reference,
            amount: eventData.amount / 100,
            currency: eventData.currency,
            customer_email: eventData.customer.email,
            channel: eventData.channel,
            paid_at: eventData.paid_at
        };
        break;
        
    case 'charge.failed':
        processedEvent = {
            ...processedEvent,
            payment_status: 'failed',
            transaction_id: eventData.id,
            reference: eventData.reference,
            failure_reason: eventData.gateway_response
        };
        break;
        
    case 'transfer.success':
    case 'transfer.failed':
        processedEvent = {
            ...processedEvent,
            transfer_status: eventType.includes('success') ? 'completed' : 'failed',
            transfer_code: eventData.transfer_code,
            amount: eventData.amount / 100,
            recipient: eventData.recipient.name
        };
        break;
        
    default:
        processedEvent.message = `Unhandled event type: ${eventType}`;
}

return [{
    json: processedEvent
}];
"""
            },
            position=[300, 200]
        )
        webhook_workflow.add_node(process_node)
        webhook_workflow.add_connection(validate_node.name, process_node.name)
        
        # 4. Update SMEFlow with event data
        update_node = N8nNode(
            name="Update SMEFlow",
            type="n8n-nodes-base.httpRequest",
            parameters={
                "url": f"http://smeflow-api:8000/api/v1/payments/paystack/webhook/{self.tenant_id}",
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
                            "name": "webhook_event",
                            "value": "={{ $node['Process Webhook Event'].json }}"
                        }
                    ]
                }
            },
            position=[400, 200]
        )
        webhook_workflow.add_node(update_node)
        webhook_workflow.add_connection(process_node.name, update_node.name)
        
        return webhook_workflow.build_workflow()
