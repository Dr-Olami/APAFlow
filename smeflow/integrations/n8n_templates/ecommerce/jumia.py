"""
Jumia E-commerce Integration Template for n8N.

Provides comprehensive Jumia marketplace integration for African markets including:
- Product listing management
- Order processing and fulfillment
- Inventory synchronization
- Performance analytics
- Multi-country support (Nigeria, Kenya, Egypt, etc.)
"""

from typing import Dict, Any, Optional, List
from ..base_template import N8nWorkflowTemplate, N8nNode, SimpleN8nWorkflowTemplate


class JumiaWorkflowTemplate(N8nWorkflowTemplate):
    """
    Jumia e-commerce workflow template for African markets.
    
    Supports product management, order processing, inventory sync,
    and analytics across multiple African countries.
    """
    
    def __init__(self, tenant_id: str, country_code: str = "NG", environment: str = "sandbox"):
        """
        Initialize Jumia workflow template.
        
        Args:
            tenant_id: Unique identifier for the tenant
            country_code: Country code (NG, KE, EG, etc.)
            environment: Jumia environment (sandbox/production)
        """
        super().__init__(tenant_id, "Jumia E-commerce")
        self.country_code = country_code.upper()
        self.environment = environment
        self.base_url = self._get_api_base_url()
        
    def _get_api_base_url(self) -> str:
        """Get the appropriate Jumia API base URL for the country."""
        country_urls = {
            "NG": "https://api.jumia.com.ng",
            "KE": "https://api.jumia.co.ke", 
            "EG": "https://api.jumia.com.eg",
            "GH": "https://api.jumia.com.gh",
            "UG": "https://api.jumia.co.ug",
            "TZ": "https://api.jumia.co.tz",
            "ZA": "https://api.jumia.co.za",
            "MA": "https://api.jumia.ma",
            "DZ": "https://api.jumia.dz"
        }
        
        if self.environment == "sandbox":
            return f"https://api-sandbox.jumia.{self.country_code.lower()}"
        
        return country_urls.get(self.country_code, "https://api.jumia.com")
    
    def build_workflow(self) -> Dict[str, Any]:
        """
        Build complete Jumia e-commerce workflow.
        
        Returns:
            Complete n8N workflow definition for Jumia integration
        """
        # 1. Webhook trigger for e-commerce operations
        webhook_trigger = self.create_webhook_trigger("jumia/operation")
        self.add_node(webhook_trigger)
        
        # 2. Operation router (determines what action to take)
        router_node = self._create_operation_router()
        self.add_node(router_node)
        self.add_connection(webhook_trigger.name, router_node.name)
        
        # 3. Product management branch
        product_node = self._create_product_management_node()
        self.add_node(product_node)
        
        # 4. Order processing branch  
        order_node = self._create_order_processing_node()
        self.add_node(order_node)
        
        # 5. Inventory sync branch
        inventory_node = self._create_inventory_sync_node()
        self.add_node(inventory_node)
        
        # 6. Analytics branch
        analytics_node = self._create_analytics_node()
        self.add_node(analytics_node)
        
        # 7. Response formatter
        response_node = self._create_response_formatter()
        self.add_node(response_node)
        
        # Connect router to different branches
        self.add_connection(router_node.name, product_node.name)
        self.add_connection(router_node.name, order_node.name)
        self.add_connection(router_node.name, inventory_node.name)
        self.add_connection(router_node.name, analytics_node.name)
        
        # Connect all branches to response formatter
        self.add_connection(product_node.name, response_node.name)
        self.add_connection(order_node.name, response_node.name)
        self.add_connection(inventory_node.name, response_node.name)
        self.add_connection(analytics_node.name, response_node.name)
        
        # 8. SMEFlow callback
        callback_node = self.create_smeflow_callback(
            f"http://smeflow-api:8000/api/v1/workflows/callback/{self.tenant_id}"
        )
        self.add_node(callback_node)
        self.add_connection(response_node.name, callback_node.name)
        
        # 9. Error handler
        error_node = self.create_error_handler()
        self.add_node(error_node)
        
        workflow_def = {
            **self.get_workflow_metadata(),
            "nodes": [node.model_dump() for node in self.nodes],
            "connections": self._serialize_connections(),
            "staticData": {
                "jumia_config": {
                    "country_code": self.country_code,
                    "environment": self.environment,
                    "base_url": self.base_url,
                    "supported_operations": [
                        "create_product", "update_product", "delete_product",
                        "process_order", "update_order_status", "cancel_order",
                        "sync_inventory", "update_stock", "get_stock_levels",
                        "get_analytics", "get_sales_report", "get_performance_metrics"
                    ]
                }
            }
        }
        
        return workflow_def
    
    def _create_operation_router(self) -> N8nNode:
        """Create operation routing node to determine action type."""
        return N8nNode(
            name="Route Jumia Operation",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Route Jumia operations based on operation type
const input = $input.first().json;
const operation = input.operation;

if (!operation) {
    throw new Error('Operation type is required');
}

const supportedOps = [
    'create_product', 'update_product', 'delete_product',
    'process_order', 'update_order_status', 'cancel_order',
    'sync_inventory', 'update_stock', 'get_stock_levels',
    'get_analytics', 'get_sales_report', 'get_performance_metrics'
];

if (!supportedOps.includes(operation)) {
    throw new Error(`Unsupported operation: ${operation}`);
}

// Determine operation category
let category = 'unknown';
if (operation.includes('product')) category = 'product';
else if (operation.includes('order')) category = 'order';
else if (operation.includes('inventory') || operation.includes('stock')) category = 'inventory';
else if (operation.includes('analytics') || operation.includes('report') || operation.includes('metrics')) category = 'analytics';

return [{
    json: {
        operation: operation,
        category: category,
        data: input.data || {},
        tenant_id: '${this.tenant_id}',
        country_code: '${this.country_code}',
        timestamp: new Date().toISOString()
    }
}];
"""
            },
            position=[200, 200]
        )
    
    def _create_product_management_node(self) -> N8nNode:
        """Create product management node for Jumia."""
        return N8nNode(
            name="Manage Jumia Products",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Handle Jumia product management operations
const routedData = $node['Route Jumia Operation'].json;

if (routedData.category !== 'product') {
    return []; // Skip if not product operation
}

const operation = routedData.operation;
const productData = routedData.data;

let result = {
    operation: operation,
    category: 'product',
    success: false,
    message: '',
    data: {}
};

switch (operation) {
    case 'create_product':
        // Validate required product fields
        const requiredFields = ['name', 'description', 'price', 'category', 'brand'];
        for (const field of requiredFields) {
            if (!productData[field]) {
                throw new Error(`Missing required product field: ${field}`);
            }
        }
        
        result = {
            ...result,
            success: true,
            message: 'Product creation prepared',
            data: {
                product_id: `JM_${Date.now()}`,
                name: productData.name,
                description: productData.description,
                price: parseFloat(productData.price),
                currency: productData.currency || 'NGN',
                category: productData.category,
                brand: productData.brand,
                images: productData.images || [],
                attributes: productData.attributes || {},
                inventory: {
                    quantity: productData.quantity || 0,
                    sku: productData.sku || `SKU_${Date.now()}`
                },
                shipping: {
                    weight: productData.weight || 0,
                    dimensions: productData.dimensions || {},
                    shipping_class: productData.shipping_class || 'standard'
                },
                status: 'pending_approval'
            }
        };
        break;
        
    case 'update_product':
        if (!productData.product_id) {
            throw new Error('Product ID is required for update');
        }
        
        result = {
            ...result,
            success: true,
            message: 'Product update prepared',
            data: {
                product_id: productData.product_id,
                updates: productData.updates || {},
                updated_at: new Date().toISOString()
            }
        };
        break;
        
    case 'delete_product':
        if (!productData.product_id) {
            throw new Error('Product ID is required for deletion');
        }
        
        result = {
            ...result,
            success: true,
            message: 'Product deletion prepared',
            data: {
                product_id: productData.product_id,
                reason: productData.reason || 'Merchant request'
            }
        };
        break;
}

return [{
    json: result
}];
"""
            },
            position=[300, 100]
        )
    
    def _create_order_processing_node(self) -> N8nNode:
        """Create order processing node for Jumia."""
        return N8nNode(
            name="Process Jumia Orders",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Handle Jumia order processing operations
const routedData = $node['Route Jumia Operation'].json;

if (routedData.category !== 'order') {
    return []; // Skip if not order operation
}

const operation = routedData.operation;
const orderData = routedData.data;

let result = {
    operation: operation,
    category: 'order',
    success: false,
    message: '',
    data: {}
};

switch (operation) {
    case 'process_order':
        if (!orderData.order_id) {
            throw new Error('Order ID is required');
        }
        
        result = {
            ...result,
            success: true,
            message: 'Order processing initiated',
            data: {
                order_id: orderData.order_id,
                status: 'processing',
                items: orderData.items || [],
                customer: orderData.customer || {},
                shipping_address: orderData.shipping_address || {},
                payment_info: orderData.payment_info || {},
                processing_started_at: new Date().toISOString()
            }
        };
        break;
        
    case 'update_order_status':
        if (!orderData.order_id || !orderData.status) {
            throw new Error('Order ID and status are required');
        }
        
        const validStatuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled', 'returned'];
        if (!validStatuses.includes(orderData.status)) {
            throw new Error(`Invalid order status: ${orderData.status}`);
        }
        
        result = {
            ...result,
            success: true,
            message: 'Order status update prepared',
            data: {
                order_id: orderData.order_id,
                old_status: orderData.old_status,
                new_status: orderData.status,
                tracking_number: orderData.tracking_number,
                notes: orderData.notes || '',
                updated_at: new Date().toISOString()
            }
        };
        break;
        
    case 'cancel_order':
        if (!orderData.order_id) {
            throw new Error('Order ID is required for cancellation');
        }
        
        result = {
            ...result,
            success: true,
            message: 'Order cancellation prepared',
            data: {
                order_id: orderData.order_id,
                reason: orderData.reason || 'Customer request',
                refund_amount: orderData.refund_amount || 0,
                cancelled_at: new Date().toISOString()
            }
        };
        break;
}

return [{
    json: result
}];
"""
            },
            position=[300, 200]
        )
    
    def _create_inventory_sync_node(self) -> N8nNode:
        """Create inventory synchronization node for Jumia."""
        return N8nNode(
            name="Sync Jumia Inventory",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Handle Jumia inventory synchronization operations
const routedData = $node['Route Jumia Operation'].json;

if (routedData.category !== 'inventory') {
    return []; // Skip if not inventory operation
}

const operation = routedData.operation;
const inventoryData = routedData.data;

let result = {
    operation: operation,
    category: 'inventory',
    success: false,
    message: '',
    data: {}
};

switch (operation) {
    case 'sync_inventory':
        if (!inventoryData.products || !Array.isArray(inventoryData.products)) {
            throw new Error('Products array is required for inventory sync');
        }
        
        const syncResults = inventoryData.products.map(product => ({
            product_id: product.product_id || product.sku,
            sku: product.sku,
            current_stock: product.current_stock || 0,
            available_stock: product.available_stock || 0,
            reserved_stock: product.reserved_stock || 0,
            last_updated: new Date().toISOString()
        }));
        
        result = {
            ...result,
            success: true,
            message: `Inventory sync prepared for ${syncResults.length} products`,
            data: {
                sync_id: `SYNC_${Date.now()}`,
                products: syncResults,
                total_products: syncResults.length,
                sync_initiated_at: new Date().toISOString()
            }
        };
        break;
        
    case 'update_stock':
        if (!inventoryData.product_id && !inventoryData.sku) {
            throw new Error('Product ID or SKU is required for stock update');
        }
        
        if (inventoryData.quantity === undefined) {
            throw new Error('Quantity is required for stock update');
        }
        
        result = {
            ...result,
            success: true,
            message: 'Stock update prepared',
            data: {
                product_id: inventoryData.product_id,
                sku: inventoryData.sku,
                old_quantity: inventoryData.old_quantity || 0,
                new_quantity: parseInt(inventoryData.quantity),
                adjustment_reason: inventoryData.reason || 'Manual adjustment',
                updated_at: new Date().toISOString()
            }
        };
        break;
        
    case 'get_stock_levels':
        const productIds = inventoryData.product_ids || [];
        
        result = {
            ...result,
            success: true,
            message: 'Stock level query prepared',
            data: {
                query_id: `QUERY_${Date.now()}`,
                product_ids: productIds,
                include_reserved: inventoryData.include_reserved || false,
                include_history: inventoryData.include_history || false,
                requested_at: new Date().toISOString()
            }
        };
        break;
}

return [{
    json: result
}];
"""
            },
            position=[300, 300]
        )
    
    def _create_analytics_node(self) -> N8nNode:
        """Create analytics and reporting node for Jumia."""
        return N8nNode(
            name="Generate Jumia Analytics",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Handle Jumia analytics and reporting operations
const routedData = $node['Route Jumia Operation'].json;

if (routedData.category !== 'analytics') {
    return []; // Skip if not analytics operation
}

const operation = routedData.operation;
const analyticsData = routedData.data;

let result = {
    operation: operation,
    category: 'analytics',
    success: false,
    message: '',
    data: {}
};

// Set default date range if not provided
const endDate = analyticsData.end_date || new Date().toISOString().split('T')[0];
const startDate = analyticsData.start_date || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

switch (operation) {
    case 'get_analytics':
        result = {
            ...result,
            success: true,
            message: 'Analytics query prepared',
            data: {
                query_id: `ANALYTICS_${Date.now()}`,
                date_range: {
                    start_date: startDate,
                    end_date: endDate
                },
                metrics: analyticsData.metrics || [
                    'total_sales', 'order_count', 'average_order_value',
                    'conversion_rate', 'top_products', 'customer_acquisition'
                ],
                filters: analyticsData.filters || {},
                requested_at: new Date().toISOString()
            }
        };
        break;
        
    case 'get_sales_report':
        result = {
            ...result,
            success: true,
            message: 'Sales report query prepared',
            data: {
                report_id: `SALES_${Date.now()}`,
                date_range: {
                    start_date: startDate,
                    end_date: endDate
                },
                group_by: analyticsData.group_by || 'day',
                include_products: analyticsData.include_products || false,
                include_categories: analyticsData.include_categories || false,
                currency: analyticsData.currency || '${this._get_default_currency()}',
                requested_at: new Date().toISOString()
            }
        };
        break;
        
    case 'get_performance_metrics':
        result = {
            ...result,
            success: true,
            message: 'Performance metrics query prepared',
            data: {
                metrics_id: `PERF_${Date.now()}`,
                date_range: {
                    start_date: startDate,
                    end_date: endDate
                },
                metrics_type: analyticsData.metrics_type || 'all',
                include_benchmarks: analyticsData.include_benchmarks || true,
                compare_previous_period: analyticsData.compare_previous_period || true,
                requested_at: new Date().toISOString()
            }
        };
        break;
}

return [{
    json: result
}];
"""
            },
            position=[300, 400]
        )
    
    def _create_response_formatter(self) -> N8nNode:
        """Create response formatting node for Jumia operations."""
        return N8nNode(
            name="Format Jumia Response",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Format Jumia operation response for SMEFlow
const inputs = $input.all();
let operationResult = null;

// Find the result from the executed operation
for (const input of inputs) {
    if (input.json && input.json.operation) {
        operationResult = input.json;
        break;
    }
}

if (!operationResult) {
    throw new Error('No operation result found');
}

return [{
    json: {
        success: operationResult.success,
        operation: operationResult.operation,
        category: operationResult.category,
        message: operationResult.message,
        platform: 'jumia',
        country_code: '${this.country_code}',
        environment: '${this.environment}',
        data: operationResult.data,
        metadata: {
            tenant_id: '${this.tenant_id}',
            workflow_id: $workflow.id,
            execution_id: $execution.id,
            processed_at: new Date().toISOString()
        }
    }
}];
"""
            },
            position=[500, 250]
        )
    
    def _get_default_currency(self) -> str:
        """Get default currency for the country."""
        currency_map = {
            "NG": "NGN",
            "KE": "KES", 
            "EG": "EGP",
            "GH": "GHS",
            "UG": "UGX",
            "TZ": "TZS",
            "ZA": "ZAR",
            "MA": "MAD",
            "DZ": "DZD"
        }
        return currency_map.get(self.country_code, "USD")
    
    def create_webhook_listener(self) -> Dict[str, Any]:
        """
        Create a webhook listener workflow for Jumia events.
        
        Returns:
            n8N workflow definition for handling Jumia webhooks
        """
        webhook_workflow = SimpleN8nWorkflowTemplate(self.tenant_id, "Jumia Webhook Listener")
        
        # 1. Webhook trigger for Jumia events
        webhook_trigger = webhook_workflow.create_webhook_trigger("jumia/webhook")
        webhook_workflow.add_node(webhook_trigger)
        
        # 2. Validate and parse webhook
        parse_node = N8nNode(
            name="Parse Jumia Webhook",
            type="n8n-nodes-base.function",
            parameters={
                "functionCode": """
// Parse and validate Jumia webhook events
const webhook = $input.first().json;
const eventType = webhook.event_type || webhook.type;

if (!eventType) {
    throw new Error('Event type is required in webhook');
}

let parsedEvent = {
    event_type: eventType,
    event_id: webhook.event_id || `EVENT_${Date.now()}`,
    received_at: new Date().toISOString(),
    data: webhook.data || webhook
};

// Parse different event types
switch (eventType) {
    case 'order.created':
    case 'order.updated':
    case 'order.cancelled':
        parsedEvent.order_data = {
            order_id: webhook.data?.order_id,
            status: webhook.data?.status,
            customer: webhook.data?.customer,
            items: webhook.data?.items || [],
            total_amount: webhook.data?.total_amount
        };
        break;
        
    case 'product.approved':
    case 'product.rejected':
    case 'product.updated':
        parsedEvent.product_data = {
            product_id: webhook.data?.product_id,
            sku: webhook.data?.sku,
            status: webhook.data?.status,
            reason: webhook.data?.reason
        };
        break;
        
    case 'inventory.updated':
        parsedEvent.inventory_data = {
            product_id: webhook.data?.product_id,
            sku: webhook.data?.sku,
            old_quantity: webhook.data?.old_quantity,
            new_quantity: webhook.data?.new_quantity
        };
        break;
        
    case 'payment.completed':
    case 'payment.failed':
        parsedEvent.payment_data = {
            order_id: webhook.data?.order_id,
            payment_id: webhook.data?.payment_id,
            amount: webhook.data?.amount,
            status: webhook.data?.status,
            method: webhook.data?.method
        };
        break;
}

return [{
    json: parsedEvent
}];
"""
            },
            position=[200, 200]
        )
        webhook_workflow.add_node(parse_node)
        webhook_workflow.add_connection(webhook_trigger.name, parse_node.name)
        
        # 3. Process webhook event
        process_node = N8nNode(
            name="Process Webhook Event",
            type="n8n-nodes-base.httpRequest",
            parameters={
                "url": f"http://smeflow-api:8000/api/v1/ecommerce/jumia/webhook/{self.tenant_id}",
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
                        },
                        {
                            "name": "X-Country-Code",
                            "value": self.country_code
                        }
                    ]
                },
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {
                            "name": "webhook_event",
                            "value": "={{ $node['Parse Jumia Webhook'].json }}"
                        }
                    ]
                }
            },
            position=[300, 200]
        )
        webhook_workflow.add_node(process_node)
        webhook_workflow.add_connection(parse_node.name, process_node.name)
        
        return webhook_workflow.build_workflow()
