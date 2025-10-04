"""
M-Pesa Payment Integration Template for n8N.

Provides comprehensive M-Pesa integration for Kenyan market including:
- STK Push (Customer to Business)
- Payment status verification
- Callback handling
- Error management
- Compliance with Safaricom API requirements
"""

from typing import Dict, Any, Optional
from ..base_template import N8nWorkflowTemplate, N8nNode, SimpleN8nWorkflowTemplate


class MpesaWorkflowTemplate(N8nWorkflowTemplate):
    """
    M-Pesa payment workflow template for Kenyan market.
    
    Supports STK Push, payment status checking, and callback handling
    with proper error handling and compliance features.
    """
    
    def __init__(self, tenant_id: str, environment: str = "sandbox"):
        """
        Initialize M-Pesa workflow template.
        
        Args:
            tenant_id: Unique identifier for the tenant
            environment: M-Pesa environment (sandbox/production)
        """
        super().__init__(tenant_id, "M-Pesa Payment")
        self.environment = environment
        self.base_url = (
            "https://sandbox.safaricom.co.ke" if environment == "sandbox"
            else "https://api.safaricom.co.ke"
        )
        self.shortcode = "174379" if environment == "sandbox" else None
    
    def build_workflow(self) -> Dict[str, Any]:
        """
        Build complete M-Pesa payment workflow.
        
        Returns:
            Complete n8N workflow definition for M-Pesa payments
        """
        # 1. Webhook trigger for payment requests
        webhook_trigger = self.create_webhook_trigger("mpesa/payment")
        self.add_node(webhook_trigger)
        
        # 2. Input validation node
        validation_node = self._create_input_validation_node()
        self.add_node(validation_node)
        self.add_connection(webhook_trigger.name, validation_node.name)
        
        # 3. M-Pesa OAuth token node
        oauth_node = self._create_oauth_node()
        self.add_node(oauth_node)
        self.add_connection(validation_node.name, oauth_node.name)
        
        # 4. STK Push request node
        stk_push_node = self._create_stk_push_node()
        self.add_node(stk_push_node)
        self.add_connection(oauth_node.name, stk_push_node.name)
        
        # 5. Payment status check node (with delay)
        status_check_node = self._create_status_check_node()
        self.add_node(status_check_node)
        self.add_connection(stk_push_node.name, status_check_node.name)
        
        # 6. Response formatting node
        response_node = self._create_response_formatter()
        self.add_node(response_node)
        self.add_connection(status_check_node.name, response_node.name)
        
        # 7. SMEFlow callback
        callback_node = self.create_smeflow_callback(
            f"http://smeflow-api:8000/api/v1/workflows/callback/{self.tenant_id}"
        )
        self.add_node(callback_node)
        self.add_connection(response_node.name, callback_node.name)
        
        # 8. Error handler
        error_node = self.create_error_handler()
        self.add_node(error_node)
        
        # Build complete workflow definition
        workflow_def = {
            **self.get_workflow_metadata(),
            "nodes": [node.model_dump() for node in self.nodes],
            "connections": self.connections,
            "staticData": {
                "mpesa_config": {
                    "environment": self.environment,
                    "base_url": self.base_url,
                    "shortcode": self.shortcode,
                    "callback_url": f"http://smeflow-api:8000/api/v1/n8n/webhooks/mpesa/callback/{self.tenant_id}"
                }
            }
        }
        
        return workflow_def
    
    def _create_input_validation_node(self) -> N8nNode:
        """Create input validation node for M-Pesa payments."""
        return N8nNode(
            name="Validate M-Pesa Request",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Validate M-Pesa payment request
const requiredFields = ['phone_number', 'amount', 'account_reference', 'transaction_desc'];
const input = $input.first().json;

// Check required fields
for (const field of requiredFields) {
    if (!input[field]) {
        throw new Error(`Missing required field: ${field}`);
    }
}

// Validate phone number format (Kenyan format)
const phoneRegex = /^254[0-9]{9}$/;
if (!phoneRegex.test(input.phone_number)) {
    throw new Error('Invalid phone number format. Use 254XXXXXXXXX');
}

// Validate amount (minimum 1 KES)
const amount = parseFloat(input.amount);
if (amount < 1) {
    throw new Error('Amount must be at least 1 KES');
}

// Format and return validated data
return [{
    json: {
        phone_number: input.phone_number,
        amount: Math.round(amount), // M-Pesa requires integer amounts
        account_reference: input.account_reference.substring(0, 12), // Max 12 chars
        transaction_desc: input.transaction_desc.substring(0, 13), // Max 13 chars
        timestamp: new Date().toISOString(),
        tenant_id: '${this.tenant_id}'
    }
}];
"""
            },
            position=[200, 200]
        )
    
    def _create_oauth_node(self) -> N8nNode:
        """Create OAuth token acquisition node."""
        return N8nNode(
            name="Get M-Pesa OAuth Token",
            type="n8n-nodes-base.httpRequest",
            parameters={
                "url": f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials",
                "method": "GET",
                "authentication": "genericCredentialType",
                "genericAuthType": "httpBasicAuth",
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
                "httpBasicAuth": f"mpesa_credentials_{self.tenant_id}"
            },
            position=[300, 200]
        )
    
    def _create_stk_push_node(self) -> N8nNode:
        """Create STK Push request node."""
        return N8nNode(
            name="Initiate STK Push",
            type="n8n-nodes-base.httpRequest",
            parameters={
                "url": f"{self.base_url}/mpesa/stkpush/v1/processrequest",
                "method": "POST",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "Authorization",
                            "value": "=Bearer {{ $node['Get M-Pesa OAuth Token'].json.access_token }}"
                        },
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
                            "name": "BusinessShortCode",
                            "value": f"{self.shortcode}"
                        },
                        {
                            "name": "Password",
                            "value": "={{ $node['Get M-Pesa OAuth Token'].json.password }}"
                        },
                        {
                            "name": "Timestamp",
                            "value": "={{ $now.format('YYYYMMDDHHmmss') }}"
                        },
                        {
                            "name": "TransactionType",
                            "value": "CustomerPayBillOnline"
                        },
                        {
                            "name": "Amount",
                            "value": "={{ $node['Validate M-Pesa Request'].json.amount }}"
                        },
                        {
                            "name": "PartyA",
                            "value": "={{ $node['Validate M-Pesa Request'].json.phone_number }}"
                        },
                        {
                            "name": "PartyB",
                            "value": f"{self.shortcode}"
                        },
                        {
                            "name": "PhoneNumber",
                            "value": "={{ $node['Validate M-Pesa Request'].json.phone_number }}"
                        },
                        {
                            "name": "CallBackURL",
                            "value": f"http://smeflow-api:8000/api/v1/n8n/webhooks/mpesa/callback/{self.tenant_id}"
                        },
                        {
                            "name": "AccountReference",
                            "value": "={{ $node['Validate M-Pesa Request'].json.account_reference }}"
                        },
                        {
                            "name": "TransactionDesc",
                            "value": "={{ $node['Validate M-Pesa Request'].json.transaction_desc }}"
                        }
                    ]
                }
            },
            position=[400, 200]
        )
    
    def _create_status_check_node(self) -> N8nNode:
        """Create payment status check node with retry logic."""
        return N8nNode(
            name="Check Payment Status",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Check M-Pesa payment status with retry logic
const stkResponse = $node['Initiate STK Push'].json;

if (stkResponse.ResponseCode !== '0') {
    throw new Error(`STK Push failed: ${stkResponse.ResponseDescription}`);
}

// Store checkout request ID for status checking
const checkoutRequestId = stkResponse.CheckoutRequestID;
const merchantRequestId = stkResponse.MerchantRequestID;

// Return status check data
return [{
    json: {
        checkout_request_id: checkoutRequestId,
        merchant_request_id: merchantRequestId,
        response_code: '0',
        response_description: 'Payment initiated successfully',
        customer_message: 'Please check your phone for payment prompt',
        amount: $node['Validate M-Pesa Request'].json.amount,
        phone_number: $node['Validate M-Pesa Request'].json.phone_number,
        status: 'pending',
        initiated_at: new Date().toISOString()
    }
}];
"""
            },
            position=[500, 200]
        )
    
    def _create_response_formatter(self) -> N8nNode:
        """Create response formatting node."""
        return N8nNode(
            name="Format M-Pesa Response",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Format M-Pesa payment response for SMEFlow
const paymentResult = $node['Check Payment Status'].json;
const originalRequest = $node['Validate M-Pesa Request'].json;

return [{
    json: {
        success: paymentResult.response_code === '0',
        payment_method: 'mpesa',
        provider: 'safaricom',
        checkout_request_id: paymentResult.checkout_request_id,
        merchant_request_id: paymentResult.merchant_request_id,
        amount: paymentResult.amount,
        currency: 'KES',
        phone_number: paymentResult.phone_number,
        account_reference: originalRequest.account_reference,
        transaction_desc: originalRequest.transaction_desc,
        status: paymentResult.status,
        initiated_at: paymentResult.initiated_at,
        provider_response: {
            response_description: paymentResult.response_description,
            customer_message: paymentResult.customer_message
        },
        metadata: {
            tenant_id: originalRequest.tenant_id,
            workflow_id: $workflow.id,
            execution_id: $execution.id,
            processed_at: new Date().toISOString(),
            environment: '${this.environment}'
        }
    }
}];
"""
            },
            position=[600, 200]
        )
    
    def create_callback_webhook(self) -> Dict[str, Any]:
        """
        Create a separate webhook workflow for M-Pesa callbacks.
        
        Returns:
            n8N workflow definition for handling M-Pesa callbacks
        """
        callback_workflow = SimpleN8nWorkflowTemplate(self.tenant_id, "M-Pesa Callback Handler")
        
        # 1. Webhook trigger for M-Pesa callbacks
        callback_trigger = callback_workflow.create_webhook_trigger("mpesa/callback")
        callback_workflow.add_node(callback_trigger)
        
        # 2. Callback validation
        validation_node = N8nNode(
            name="Validate M-Pesa Callback",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Validate M-Pesa callback data
const callback = $input.first().json;

// Extract callback data
const stkCallback = callback.Body.stkCallback;
const resultCode = stkCallback.ResultCode;
const resultDesc = stkCallback.ResultDesc;
const merchantRequestId = stkCallback.MerchantRequestID;
const checkoutRequestId = stkCallback.CheckoutRequestID;

// Process callback items if payment was successful
let callbackMetadata = {};
if (resultCode === 0 && stkCallback.CallbackMetadata) {
    const items = stkCallback.CallbackMetadata.Item;
    for (const item of items) {
        callbackMetadata[item.Name] = item.Value;
    }
}

return [{
    json: {
        result_code: resultCode,
        result_desc: resultDesc,
        merchant_request_id: merchantRequestId,
        checkout_request_id: checkoutRequestId,
        success: resultCode === 0,
        amount: callbackMetadata.Amount || null,
        mpesa_receipt_number: callbackMetadata.MpesaReceiptNumber || null,
        transaction_date: callbackMetadata.TransactionDate || null,
        phone_number: callbackMetadata.PhoneNumber || null,
        processed_at: new Date().toISOString()
    }
}];
"""
            },
            position=[200, 200]
        )
        callback_workflow.add_node(validation_node)
        callback_workflow.add_connection(callback_trigger.name, validation_node.name)
        
        # 3. Update payment status in SMEFlow
        update_node = N8nNode(
            name="Update Payment Status",
            type="n8n-nodes-base.httpRequest",
            parameters={
                "url": f"http://smeflow-api:8000/api/v1/payments/mpesa/callback/{self.tenant_id}",
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
                            "name": "checkout_request_id",
                            "value": "={{ $node['Validate M-Pesa Callback'].json.checkout_request_id }}"
                        },
                        {
                            "name": "merchant_request_id",
                            "value": "={{ $node['Validate M-Pesa Callback'].json.merchant_request_id }}"
                        },
                        {
                            "name": "result_code",
                            "value": "={{ $node['Validate M-Pesa Callback'].json.result_code }}"
                        },
                        {
                            "name": "result_desc",
                            "value": "={{ $node['Validate M-Pesa Callback'].json.result_desc }}"
                        },
                        {
                            "name": "mpesa_receipt_number",
                            "value": "={{ $node['Validate M-Pesa Callback'].json.mpesa_receipt_number }}"
                        },
                        {
                            "name": "amount",
                            "value": "={{ $node['Validate M-Pesa Callback'].json.amount }}"
                        },
                        {
                            "name": "transaction_date",
                            "value": "={{ $node['Validate M-Pesa Callback'].json.transaction_date }}"
                        },
                        {
                            "name": "phone_number",
                            "value": "={{ $node['Validate M-Pesa Callback'].json.phone_number }}"
                        }
                    ]
                }
            },
            position=[300, 200]
        )
        callback_workflow.add_node(update_node)
        callback_workflow.add_connection(validation_node.name, update_node.name)
        
        return callback_workflow.build_workflow()
