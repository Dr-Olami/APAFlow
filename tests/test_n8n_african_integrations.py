"""
Tests for n8N African Market Integration Templates.

Tests the modular n8N workflow templates for African payment providers,
e-commerce platforms, and communication services.
"""

import pytest
import json
from uuid import uuid4
from unittest.mock import MagicMock, patch

from smeflow.integrations.n8n_templates import (
    N8nWorkflowTemplate,
    MpesaWorkflowTemplate,
    PaystackWorkflowTemplate,
    JumiaWorkflowTemplate
)
from smeflow.integrations.n8n_templates.base_template import N8nNode


class TestConcreteTemplate(N8nWorkflowTemplate):
    """Concrete implementation of N8nWorkflowTemplate for testing."""
    
    def build_workflow(self):
        """Simple test workflow implementation."""
        return {
            **self.get_workflow_metadata(),
            "nodes": [node.model_dump() for node in self.nodes],
            "connections": self.connections
        }


class TestN8nBaseTemplate:
    """Test the base n8N workflow template functionality."""
    
    def test_base_template_initialization(self):
        """Test base template initialization."""
        tenant_id = str(uuid4())
        template = TestConcreteTemplate(tenant_id, "Test Template")
        
        assert template.tenant_id == tenant_id
        assert template.template_name == "Test Template"
        assert len(template.nodes) == 0
        assert len(template.connections) == 0
    
    def test_add_node_and_connection(self):
        """Test adding nodes and connections."""
        tenant_id = str(uuid4())
        template = TestConcreteTemplate(tenant_id, "Test Template")
        
        # Create test nodes
        node1 = N8nNode(name="Node 1", type="test.node")
        node2 = N8nNode(name="Node 2", type="test.node")
        
        # Add nodes
        template.add_node(node1)
        template.add_node(node2)
        
        assert len(template.nodes) == 2
        
        # Add connection
        template.add_connection(node1.name, node2.name)
        
        assert node1.name in template.connections
        assert len(template.connections[node1.name][0]) == 1
        assert template.connections[node1.name][0][0].node == node2.name
    
    def test_webhook_trigger_creation(self):
        """Test webhook trigger node creation."""
        tenant_id = str(uuid4())
        template = TestConcreteTemplate(tenant_id, "Test Template")
        
        webhook_node = template.create_webhook_trigger("test/webhook")
        
        assert webhook_node.name == "SMEFlow Webhook Trigger"
        assert webhook_node.type == "n8n-nodes-base.webhook"
        assert f"smeflow/{tenant_id}/test/webhook" in webhook_node.parameters["path"]
    
    def test_african_market_compliance_validation(self):
        """Test African market compliance validation."""
        tenant_id = str(uuid4())
        template = TestConcreteTemplate(tenant_id, "Test Template")
        
        # Add non-compliant node (European URL)
        bad_node = N8nNode(
            name="Bad Node",
            type="n8n-nodes-base.httpRequest",
            parameters={"url": "https://api.europe.example.com"}
        )
        template.add_node(bad_node)
        
        # Add webhook without tenant isolation
        bad_webhook = N8nNode(
            name="Bad Webhook",
            type="n8n-nodes-base.webhook",
            parameters={"path": "generic/webhook"}
        )
        template.add_node(bad_webhook)
        
        issues = template.validate_african_market_compliance()
        
        assert len(issues) >= 2
        assert any("data residency" in issue for issue in issues)
        assert any("tenant isolation" in issue for issue in issues)


class TestMpesaWorkflowTemplate:
    """Test M-Pesa payment workflow template."""
    
    def test_mpesa_template_initialization(self):
        """Test M-Pesa template initialization."""
        tenant_id = str(uuid4())
        template = MpesaWorkflowTemplate(tenant_id, "sandbox")
        
        assert template.tenant_id == tenant_id
        assert template.template_name == "M-Pesa Payment"
        assert template.environment == "sandbox"
        assert "sandbox.safaricom.co.ke" in template.base_url
    
    def test_mpesa_production_environment(self):
        """Test M-Pesa production environment configuration."""
        tenant_id = str(uuid4())
        template = MpesaWorkflowTemplate(tenant_id, "production")
        
        assert template.environment == "production"
        assert "api.safaricom.co.ke" in template.base_url
    
    def test_mpesa_workflow_build(self):
        """Test M-Pesa workflow building."""
        tenant_id = str(uuid4())
        template = MpesaWorkflowTemplate(tenant_id, "sandbox")
        
        workflow_def = template.build_workflow()
        
        # Verify workflow structure
        assert "nodes" in workflow_def
        assert "connections" in workflow_def
        assert "staticData" in workflow_def
        
        # Verify M-Pesa specific configuration
        mpesa_config = workflow_def["staticData"]["mpesa_config"]
        assert mpesa_config["environment"] == "sandbox"
        assert "sandbox.safaricom.co.ke" in mpesa_config["base_url"]
        assert tenant_id in mpesa_config["callback_url"]
        
        # Verify required nodes are present
        node_names = [node["name"] for node in workflow_def["nodes"]]
        expected_nodes = [
            "SMEFlow Webhook Trigger",
            "Validate M-Pesa Request",
            "Get M-Pesa OAuth Token",
            "Initiate STK Push",
            "Check Payment Status",
            "Format M-Pesa Response"
        ]
        
        for expected_node in expected_nodes:
            assert expected_node in node_names
    
    def test_mpesa_callback_webhook_creation(self):
        """Test M-Pesa callback webhook creation."""
        tenant_id = str(uuid4())
        template = MpesaWorkflowTemplate(tenant_id, "sandbox")
        
        callback_workflow = template.create_callback_webhook()
        
        # Verify callback workflow structure
        assert "nodes" in callback_workflow
        assert "connections" in callback_workflow
        
        # Verify callback-specific nodes
        node_names = [node["name"] for node in callback_workflow["nodes"]]
        assert "SMEFlow Webhook Trigger" in node_names
        assert "Validate M-Pesa Callback" in node_names
        assert "Update Payment Status" in node_names


class TestPaystackWorkflowTemplate:
    """Test Paystack payment workflow template."""
    
    def test_paystack_template_initialization(self):
        """Test Paystack template initialization."""
        tenant_id = str(uuid4())
        template = PaystackWorkflowTemplate(tenant_id, "test")
        
        assert template.tenant_id == tenant_id
        assert template.template_name == "Paystack Payment"
        assert template.environment == "test"
        assert template.base_url == "https://api.paystack.co"
    
    def test_paystack_workflow_build(self):
        """Test Paystack workflow building."""
        tenant_id = str(uuid4())
        template = PaystackWorkflowTemplate(tenant_id, "test")
        
        workflow_def = template.build_workflow()
        
        # Verify workflow structure
        assert "nodes" in workflow_def
        assert "connections" in workflow_def
        assert "staticData" in workflow_def
        
        # Verify Paystack specific configuration
        paystack_config = workflow_def["staticData"]["paystack_config"]
        assert paystack_config["environment"] == "test"
        assert paystack_config["base_url"] == "https://api.paystack.co"
        assert tenant_id in paystack_config["webhook_url"]
        
        # Verify required nodes are present
        node_names = [node["name"] for node in workflow_def["nodes"]]
        expected_nodes = [
            "SMEFlow Webhook Trigger",
            "Validate Paystack Request",
            "Initialize Paystack Transaction",
            "Format Initialization Response"
        ]
        
        for expected_node in expected_nodes:
            assert expected_node in node_names
    
    def test_paystack_verification_workflow(self):
        """Test Paystack verification workflow creation."""
        tenant_id = str(uuid4())
        template = PaystackWorkflowTemplate(tenant_id, "test")
        
        verify_workflow = template.create_verification_workflow()
        
        # Verify verification workflow structure
        assert "nodes" in verify_workflow
        assert "connections" in verify_workflow
        
        # Verify verification-specific nodes
        node_names = [node["name"] for node in verify_workflow["nodes"]]
        assert "Extract Reference" in node_names
        assert "Verify Payment" in node_names
        assert "Format Verification Response" in node_names
        assert "Update Payment Status" in node_names
    
    def test_paystack_webhook_handler(self):
        """Test Paystack webhook handler creation."""
        tenant_id = str(uuid4())
        template = PaystackWorkflowTemplate(tenant_id, "test")
        
        webhook_workflow = template.create_webhook_handler()
        
        # Verify webhook workflow structure
        assert "nodes" in webhook_workflow
        assert "connections" in webhook_workflow
        
        # Verify webhook-specific nodes
        node_names = [node["name"] for node in webhook_workflow["nodes"]]
        assert "Validate Webhook Signature" in node_names
        assert "Process Webhook Event" in node_names
        assert "Update SMEFlow" in node_names


class TestJumiaWorkflowTemplate:
    """Test Jumia e-commerce workflow template."""
    
    def test_jumia_template_initialization(self):
        """Test Jumia template initialization."""
        tenant_id = str(uuid4())
        template = JumiaWorkflowTemplate(tenant_id, "NG", "sandbox")
        
        assert template.tenant_id == tenant_id
        assert template.template_name == "Jumia E-commerce"
        assert template.country_code == "NG"
        assert template.environment == "sandbox"
    
    def test_jumia_country_specific_urls(self):
        """Test Jumia country-specific API URLs."""
        tenant_id = str(uuid4())
        
        # Test different countries
        countries = ["NG", "KE", "EG", "GH", "UG"]
        
        for country in countries:
            template = JumiaWorkflowTemplate(tenant_id, country, "production")
            assert country.lower() in template.base_url.lower()
    
    def test_jumia_workflow_build(self):
        """Test Jumia workflow building."""
        tenant_id = str(uuid4())
        template = JumiaWorkflowTemplate(tenant_id, "NG", "sandbox")
        
        workflow_def = template.build_workflow()
        
        # Verify workflow structure
        assert "nodes" in workflow_def
        assert "connections" in workflow_def
        assert "staticData" in workflow_def
        
        # Verify Jumia specific configuration
        jumia_config = workflow_def["staticData"]["jumia_config"]
        assert jumia_config["country_code"] == "NG"
        assert jumia_config["environment"] == "sandbox"
        assert "supported_operations" in jumia_config
        
        # Verify required nodes are present
        node_names = [node["name"] for node in workflow_def["nodes"]]
        expected_nodes = [
            "SMEFlow Webhook Trigger",
            "Route Jumia Operation",
            "Manage Jumia Products",
            "Process Jumia Orders",
            "Sync Jumia Inventory",
            "Generate Jumia Analytics"
        ]
        
        for expected_node in expected_nodes:
            assert expected_node in node_names
    
    def test_jumia_webhook_listener(self):
        """Test Jumia webhook listener creation."""
        tenant_id = str(uuid4())
        template = JumiaWorkflowTemplate(tenant_id, "NG", "sandbox")
        
        webhook_workflow = template.create_webhook_listener()
        
        # Verify webhook workflow structure
        assert "nodes" in webhook_workflow
        assert "connections" in webhook_workflow
        
        # Verify webhook-specific nodes
        node_names = [node["name"] for node in webhook_workflow["nodes"]]
        assert "Parse Jumia Webhook" in node_names
        assert "Process Webhook Event" in node_names
    
    def test_jumia_default_currency_mapping(self):
        """Test Jumia default currency mapping for different countries."""
        tenant_id = str(uuid4())
        
        currency_tests = [
            ("NG", "NGN"),
            ("KE", "KES"),
            ("EG", "EGP"),
            ("GH", "GHS"),
            ("ZA", "ZAR")
        ]
        
        for country, expected_currency in currency_tests:
            template = JumiaWorkflowTemplate(tenant_id, country, "sandbox")
            assert template._get_default_currency() == expected_currency


class TestAfricanMarketIntegrations:
    """Test African market specific features across all templates."""
    
    def test_multi_tenant_isolation(self):
        """Test multi-tenant isolation across all templates."""
        tenant_id_1 = str(uuid4())
        tenant_id_2 = str(uuid4())
        
        # Test M-Pesa
        mpesa_1 = MpesaWorkflowTemplate(tenant_id_1)
        mpesa_2 = MpesaWorkflowTemplate(tenant_id_2)
        
        workflow_1 = mpesa_1.build_workflow()
        workflow_2 = mpesa_2.build_workflow()
        
        # Verify tenant isolation in webhook paths
        webhook_1 = next(n for n in workflow_1["nodes"] if n["type"] == "n8n-nodes-base.webhook")
        webhook_2 = next(n for n in workflow_2["nodes"] if n["type"] == "n8n-nodes-base.webhook")
        
        assert tenant_id_1 in webhook_1["parameters"]["path"]
        assert tenant_id_2 in webhook_2["parameters"]["path"]
        assert webhook_1["parameters"]["path"] != webhook_2["parameters"]["path"]
    
    def test_african_currency_support(self):
        """Test African currency support across templates."""
        tenant_id = str(uuid4())
        
        # Test Jumia currency mapping
        jumia_ng = JumiaWorkflowTemplate(tenant_id, "NG")
        jumia_ke = JumiaWorkflowTemplate(tenant_id, "KE")
        jumia_za = JumiaWorkflowTemplate(tenant_id, "ZA")
        
        assert jumia_ng._get_default_currency() == "NGN"
        assert jumia_ke._get_default_currency() == "KES"
        assert jumia_za._get_default_currency() == "ZAR"
    
    def test_compliance_validation_across_templates(self):
        """Test compliance validation across all template types."""
        tenant_id = str(uuid4())
        
        templates = [
            MpesaWorkflowTemplate(tenant_id),
            PaystackWorkflowTemplate(tenant_id),
            JumiaWorkflowTemplate(tenant_id, "NG")
        ]
        
        for template in templates:
            workflow_def = template.build_workflow()
            
            # Verify tenant isolation in all webhook nodes
            webhook_nodes = [n for n in workflow_def["nodes"] if n["type"] == "n8n-nodes-base.webhook"]
            for webhook_node in webhook_nodes:
                assert tenant_id in webhook_node["parameters"]["path"]
            
            # Verify no European/US URLs in HTTP request nodes
            http_nodes = [n for n in workflow_def["nodes"] if n["type"] == "n8n-nodes-base.httpRequest"]
            for http_node in http_nodes:
                url = http_node["parameters"].get("url", "")
                assert "europe" not in url.lower()
                assert "us-" not in url.lower()
    
    def test_error_handling_consistency(self):
        """Test consistent error handling across all templates."""
        tenant_id = str(uuid4())
        
        templates = [
            MpesaWorkflowTemplate(tenant_id),
            PaystackWorkflowTemplate(tenant_id),
            JumiaWorkflowTemplate(tenant_id, "NG")
        ]
        
        for template in templates:
            workflow_def = template.build_workflow()
            
            # Verify error handler nodes are present
            node_names = [n["name"] for n in workflow_def["nodes"]]
            error_nodes = [name for name in node_names if "error" in name.lower()]
            assert len(error_nodes) > 0, f"No error handling nodes found in {template.template_name}"
    
    @pytest.mark.parametrize("country_code,expected_currency", [
        ("NG", "NGN"),
        ("KE", "KES"),
        ("EG", "EGP"),
        ("GH", "GHS"),
        ("UG", "UGX"),
        ("TZ", "TZS"),
        ("ZA", "ZAR"),
        ("MA", "MAD"),
        ("DZ", "DZD")
    ])
    def test_african_country_currency_mapping(self, country_code, expected_currency):
        """Test currency mapping for all supported African countries."""
        tenant_id = str(uuid4())
        template = JumiaWorkflowTemplate(tenant_id, country_code)
        
        assert template._get_default_currency() == expected_currency


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
