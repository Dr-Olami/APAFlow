"""
Tests for n8N Communication Integration Templates.

Tests the communication workflow templates for WhatsApp Business API,
SMS gateways, and email automation optimized for African markets.
"""

import pytest
import json
from uuid import uuid4
from unittest.mock import MagicMock, patch

from smeflow.integrations.n8n_templates import (
    WhatsAppWorkflowTemplate,
    SMSWorkflowTemplate,
    EmailWorkflowTemplate
)
from smeflow.integrations.n8n_templates.base_template import N8nNode


class TestWhatsAppWorkflowTemplate:
    """Test WhatsApp Business API workflow template."""
    
    def test_whatsapp_template_initialization(self):
        """Test WhatsApp template initialization."""
        tenant_id = str(uuid4())
        phone_number_id = "1234567890"
        template = WhatsAppWorkflowTemplate(tenant_id, phone_number_id, "production")
        
        assert template.tenant_id == tenant_id
        assert template.template_name == "WhatsApp Business"
        assert template.phone_number_id == phone_number_id
        assert template.environment == "production"
        assert "graph.facebook.com" in template.base_url
    
    def test_whatsapp_workflow_build(self):
        """Test WhatsApp workflow building."""
        tenant_id = str(uuid4())
        phone_number_id = "1234567890"
        template = WhatsAppWorkflowTemplate(tenant_id, phone_number_id)
        
        workflow_def = template.build_workflow()
        
        # Verify workflow structure
        assert "nodes" in workflow_def
        assert "connections" in workflow_def
        assert "staticData" in workflow_def
        
        # Verify WhatsApp specific configuration
        whatsapp_config = workflow_def["staticData"]["whatsapp_config"]
        assert whatsapp_config["phone_number_id"] == phone_number_id
        assert whatsapp_config["environment"] == "production"
        assert "graph.facebook.com" in whatsapp_config["base_url"]
        
        # Verify supported message types
        supported_types = whatsapp_config["supported_message_types"]
        expected_types = ["text", "image", "document", "audio", "video", "template"]
        for msg_type in expected_types:
            assert msg_type in supported_types
        
        # Verify African language support
        supported_languages = whatsapp_config["supported_languages"]
        african_languages = ["sw", "ha", "yo", "ig", "am"]  # Swahili, Hausa, Yoruba, Igbo, Amharic
        for lang in african_languages:
            assert lang in supported_languages
        
        # Verify required nodes are present
        node_names = [node["name"] for node in workflow_def["nodes"]]
        expected_nodes = [
            "SMEFlow Webhook Trigger",
            "Validate WhatsApp Message",
            "Send WhatsApp Text Message",
            "Send WhatsApp Media Message",
            "Send WhatsApp Template Message"
        ]
        
        for expected_node in expected_nodes:
            assert expected_node in node_names
    
    def test_whatsapp_webhook_handler_creation(self):
        """Test WhatsApp webhook handler creation."""
        tenant_id = str(uuid4())
        phone_number_id = "1234567890"
        template = WhatsAppWorkflowTemplate(tenant_id, phone_number_id)
        
        webhook_workflow = template.create_webhook_handler()
        
        # Verify webhook workflow structure
        assert "nodes" in webhook_workflow
        assert "connections" in webhook_workflow
        
        # Verify webhook-specific nodes
        node_names = [node["name"] for node in webhook_workflow["nodes"]]
        assert "Verify WhatsApp Webhook" in node_names
        assert "Process WhatsApp Events" in node_names
    
    def test_whatsapp_template_management_workflow(self):
        """Test WhatsApp template management workflow creation."""
        tenant_id = str(uuid4())
        phone_number_id = "1234567890"
        template = WhatsAppWorkflowTemplate(tenant_id, phone_number_id)
        
        template_workflow = template.create_template_management_workflow()
        
        # Verify template workflow structure
        assert "nodes" in template_workflow
        assert "connections" in template_workflow
        
        # Verify template-specific nodes
        node_names = [node["name"] for node in template_workflow["nodes"]]
        assert "Route Template Operation" in node_names
        assert "Execute Template Operation" in node_names


class TestSMSWorkflowTemplate:
    """Test SMS gateway workflow template."""
    
    def test_sms_template_initialization(self):
        """Test SMS template initialization."""
        tenant_id = str(uuid4())
        template = SMSWorkflowTemplate(tenant_id, "africas_talking", "KE")
        
        assert template.tenant_id == tenant_id
        assert template.template_name == "SMS Gateway"
        assert template.primary_provider == "africas_talking"
        assert template.country_code == "KE"
    
    def test_sms_provider_configuration(self):
        """Test SMS provider configuration for different countries."""
        tenant_id = str(uuid4())
        
        # Test different providers
        providers = ["africas_talking", "twilio", "termii", "clickatell"]
        
        for provider in providers:
            template = SMSWorkflowTemplate(tenant_id, provider, "NG")
            config = template.provider_config
            
            assert "name" in config
            assert "base_url" in config
            assert "supported_countries" in config
            assert "cost_per_sms" in config
            assert "features" in config
    
    def test_sms_workflow_build(self):
        """Test SMS workflow building."""
        tenant_id = str(uuid4())
        template = SMSWorkflowTemplate(tenant_id, "termii", "NG")
        
        workflow_def = template.build_workflow()
        
        # Verify workflow structure
        assert "nodes" in workflow_def
        assert "connections" in workflow_def
        assert "staticData" in workflow_def
        
        # Verify SMS specific configuration
        sms_config = workflow_def["staticData"]["sms_config"]
        assert sms_config["primary_provider"] == "termii"
        assert sms_config["country_code"] == "NG"
        assert "provider_config" in sms_config
        assert "failover_providers" in sms_config
        
        # Verify supported operations
        supported_ops = sms_config["supported_operations"]
        expected_ops = ["send_single", "send_bulk", "check_status", "get_balance"]
        for op in expected_ops:
            assert op in supported_ops
        
        # Verify required nodes are present
        node_names = [node["name"] for node in workflow_def["nodes"]]
        expected_nodes = [
            "SMEFlow Webhook Trigger",
            "Validate SMS Request",
            "Select SMS Provider",
            "Send Single SMS",
            "Send Bulk SMS"
        ]
        
        for expected_node in expected_nodes:
            assert expected_node in node_names
    
    def test_sms_failover_providers(self):
        """Test SMS failover provider selection for different countries."""
        tenant_id = str(uuid4())
        
        country_tests = [
            ("NG", "termii", ["twilio", "clickatell"]),
            ("KE", "africas_talking", ["twilio", "clickatell"]),
            ("ZA", "clickatell", ["twilio", "africas_talking"])
        ]
        
        for country, primary, expected_failovers in country_tests:
            template = SMSWorkflowTemplate(tenant_id, primary, country)
            failover_providers = template._get_failover_providers()
            
            # Primary provider should not be in failover list
            assert primary not in failover_providers
            
            # Should have at least one failover provider
            assert len(failover_providers) > 0
    
    def test_sms_delivery_tracking_workflow(self):
        """Test SMS delivery tracking workflow creation."""
        tenant_id = str(uuid4())
        template = SMSWorkflowTemplate(tenant_id, "twilio", "NG")
        
        tracking_workflow = template.create_delivery_tracking_workflow()
        
        # Verify tracking workflow structure
        assert "nodes" in tracking_workflow
        assert "connections" in tracking_workflow
        
        # Verify tracking-specific nodes
        node_names = [node["name"] for node in tracking_workflow["nodes"]]
        assert "Parse Delivery Status" in node_names
        assert "Update SMS Status" in node_names


class TestEmailWorkflowTemplate:
    """Test email integration workflow template."""
    
    def test_email_template_initialization(self):
        """Test email template initialization."""
        tenant_id = str(uuid4())
        template = EmailWorkflowTemplate(tenant_id, "sendgrid", "example.com")
        
        assert template.tenant_id == tenant_id
        assert template.template_name == "Email Integration"
        assert template.email_provider == "sendgrid"
        assert template.sender_domain == "example.com"
    
    def test_email_provider_configuration(self):
        """Test email provider configuration."""
        tenant_id = str(uuid4())
        
        providers = ["sendgrid", "mailgun", "ses", "smtp"]
        
        for provider in providers:
            template = EmailWorkflowTemplate(tenant_id, provider)
            config = template.provider_config
            
            assert "name" in config
            assert "base_url" in config
            assert "auth_type" in config
            assert "features" in config
            assert "cost_per_email" in config
            assert "african_presence" in config
    
    def test_email_workflow_build(self):
        """Test email workflow building."""
        tenant_id = str(uuid4())
        template = EmailWorkflowTemplate(tenant_id, "sendgrid", "smeflow.com")
        
        workflow_def = template.build_workflow()
        
        # Verify workflow structure
        assert "nodes" in workflow_def
        assert "connections" in workflow_def
        assert "staticData" in workflow_def
        
        # Verify email specific configuration
        email_config = workflow_def["staticData"]["email_config"]
        assert email_config["provider"] == "sendgrid"
        assert email_config["sender_domain"] == "smeflow.com"
        assert "provider_config" in email_config
        
        # Verify compliance settings
        compliance = email_config["compliance"]
        assert compliance["gdpr_compliant"] is True
        assert compliance["popia_compliant"] is True
        assert compliance["unsubscribe_required"] is True
        assert compliance["data_residency"] == "africa"
        
        # Verify supported operations
        supported_ops = email_config["supported_operations"]
        expected_ops = ["send_single", "send_bulk", "send_template", "track_opens", "track_clicks"]
        for op in expected_ops:
            assert op in supported_ops
        
        # Verify required nodes are present
        node_names = [node["name"] for node in workflow_def["nodes"]]
        expected_nodes = [
            "SMEFlow Webhook Trigger",
            "Validate Email Request",
            "Process Email Template",
            "Send Single Email",
            "Send Bulk Email"
        ]
        
        for expected_node in expected_nodes:
            assert expected_node in node_names
    
    def test_email_tracking_workflow(self):
        """Test email tracking workflow creation."""
        tenant_id = str(uuid4())
        template = EmailWorkflowTemplate(tenant_id, "mailgun")
        
        tracking_workflow = template.create_email_tracking_workflow()
        
        # Verify tracking workflow structure
        assert "nodes" in tracking_workflow
        assert "connections" in tracking_workflow
        
        # Verify tracking-specific nodes
        node_names = [node["name"] for node in tracking_workflow["nodes"]]
        assert "Parse Tracking Event" in node_names
        assert "Update Email Analytics" in node_names


class TestCommunicationIntegrationsCompliance:
    """Test compliance features across all communication integrations."""
    
    def test_african_market_compliance(self):
        """Test African market compliance across all communication templates."""
        tenant_id = str(uuid4())
        
        templates = [
            WhatsAppWorkflowTemplate(tenant_id, "1234567890"),
            SMSWorkflowTemplate(tenant_id, "africas_talking", "NG"),
            EmailWorkflowTemplate(tenant_id, "sendgrid")
        ]
        
        for template in templates:
            workflow_def = template.build_workflow()
            
            # Verify tenant isolation in webhook nodes
            webhook_nodes = [n for n in workflow_def["nodes"] if n["type"] == "n8n-nodes-base.webhook"]
            for webhook_node in webhook_nodes:
                assert tenant_id in webhook_node["parameters"]["path"]
            
            # Verify no European/US-only URLs in HTTP request nodes
            http_nodes = [n for n in workflow_def["nodes"] if n["type"] == "n8n-nodes-base.httpRequest"]
            for http_node in http_nodes:
                url = http_node["parameters"].get("url", "")
                # Allow Facebook Graph API for WhatsApp as it's the official API
                if "graph.facebook.com" not in url:
                    assert "europe-only" not in url.lower()
                    assert "us-only" not in url.lower()
    
    def test_multi_language_support(self):
        """Test multi-language support for African markets."""
        tenant_id = str(uuid4())
        
        # Test WhatsApp language support
        whatsapp_template = WhatsAppWorkflowTemplate(tenant_id, "1234567890")
        whatsapp_workflow = whatsapp_template.build_workflow()
        
        supported_languages = whatsapp_workflow["staticData"]["whatsapp_config"]["supported_languages"]
        african_languages = ["sw", "ha", "yo", "ig", "am"]  # Major African languages
        
        for lang in african_languages:
            assert lang in supported_languages
    
    def test_cost_optimization_features(self):
        """Test cost optimization features across communication templates."""
        tenant_id = str(uuid4())
        
        # Test SMS cost optimization
        sms_template = SMSWorkflowTemplate(tenant_id, "termii", "NG")
        sms_workflow = sms_template.build_workflow()
        
        sms_config = sms_workflow["staticData"]["sms_config"]
        assert sms_config["cost_optimization"] is True
        assert len(sms_config["failover_providers"]) > 0
        
        # Test email provider cost comparison
        email_template = EmailWorkflowTemplate(tenant_id, "ses")  # Cheapest provider
        email_config = email_template.provider_config
        assert email_config["cost_per_email"] <= 0.001  # Very low cost
    
    def test_data_residency_compliance(self):
        """Test data residency compliance for African markets."""
        tenant_id = str(uuid4())
        
        # Test email data residency
        email_template = EmailWorkflowTemplate(tenant_id, "sendgrid")
        email_workflow = email_template.build_workflow()
        
        compliance = email_workflow["staticData"]["email_config"]["compliance"]
        assert compliance["data_residency"] == "africa"
        assert compliance["gdpr_compliant"] is True
        assert compliance["popia_compliant"] is True
    
    @pytest.mark.parametrize("provider,country,expected_support", [
        ("africas_talking", "KE", True),
        ("africas_talking", "NG", False),
        ("termii", "NG", True),
        ("termii", "ZA", False),
        ("twilio", "NG", True),
        ("twilio", "KE", True)
    ])
    def test_provider_country_support(self, provider, country, expected_support):
        """Test SMS provider country support mapping."""
        tenant_id = str(uuid4())
        template = SMSWorkflowTemplate(tenant_id, provider, country)
        
        supported_countries = template.provider_config["supported_countries"]
        
        if expected_support:
            assert country in supported_countries
        else:
            # Should fallback to a supported provider
            failover_providers = template._get_failover_providers()
            assert len(failover_providers) > 0


class TestCommunicationIntegrationsPerformance:
    """Test performance and scalability features."""
    
    def test_bulk_messaging_support(self):
        """Test bulk messaging capabilities."""
        tenant_id = str(uuid4())
        
        # Test SMS bulk support
        sms_template = SMSWorkflowTemplate(tenant_id, "africas_talking", "KE")
        sms_workflow = sms_template.build_workflow()
        
        node_names = [node["name"] for node in sms_workflow["nodes"]]
        assert "Send Bulk SMS" in node_names
        
        # Test email bulk support
        email_template = EmailWorkflowTemplate(tenant_id, "sendgrid")
        email_workflow = email_template.build_workflow()
        
        node_names = [node["name"] for node in email_workflow["nodes"]]
        assert "Send Bulk Email" in node_names
    
    def test_error_handling_consistency(self):
        """Test consistent error handling across all communication templates."""
        tenant_id = str(uuid4())
        
        templates = [
            WhatsAppWorkflowTemplate(tenant_id, "1234567890"),
            SMSWorkflowTemplate(tenant_id, "twilio", "NG"),
            EmailWorkflowTemplate(tenant_id, "mailgun")
        ]
        
        for template in templates:
            workflow_def = template.build_workflow()
            
            # Verify error handler nodes are present
            node_names = [n["name"] for n in workflow_def["nodes"]]
            error_nodes = [name for name in node_names if "error" in name.lower()]
            assert len(error_nodes) > 0, f"No error handling nodes found in {template.template_name}"
    
    def test_webhook_security_features(self):
        """Test webhook security features across communication templates."""
        tenant_id = str(uuid4())
        
        # Test WhatsApp webhook security
        whatsapp_template = WhatsAppWorkflowTemplate(tenant_id, "1234567890")
        webhook_workflow = whatsapp_template.create_webhook_handler()
        
        node_names = [node["name"] for node in webhook_workflow["nodes"]]
        assert "Verify WhatsApp Webhook" in node_names
        
        # Verify webhook verification includes signature checking
        verify_node = next(n for n in webhook_workflow["nodes"] if n["name"] == "Verify WhatsApp Webhook")
        function_code = verify_node["parameters"]["functionCode"]
        assert "hub.verify_token" in function_code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
