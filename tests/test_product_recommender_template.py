"""
Unit tests for Product Recommender workflow template.

Tests the Product Recommender template functionality including form fields,
workflow nodes, business rules, and integration requirements.
"""

import pytest
from smeflow.workflows.templates import IndustryTemplateFactory, IndustryType, FormFieldType


class TestProductRecommenderTemplate:
    """Test suite for Product Recommender workflow template."""

    def test_product_recommender_template_creation(self):
        """Test that Product Recommender template can be created successfully."""
        template = IndustryTemplateFactory.get_template(IndustryType.PRODUCT_RECOMMENDER)
        
        assert template is not None
        assert template.industry == IndustryType.PRODUCT_RECOMMENDER
        assert template.name == "AI Product Recommender System"
        assert "Intelligent product discovery and recommendation workflow" in template.description

    def test_product_recommender_booking_form_fields(self):
        """Test that Product Recommender template has correct booking form fields."""
        template = IndustryTemplateFactory.get_template(IndustryType.PRODUCT_RECOMMENDER)
        
        # Check required customer information fields
        field_names = [field.name for field in template.booking_form_fields]
        
        # Customer basic info
        assert "customer_name" in field_names
        assert "customer_email" in field_names
        assert "customer_phone" in field_names
        
        # Product preferences
        assert "product_category" in field_names
        assert "budget_range" in field_names
        assert "purchase_urgency" in field_names
        
        # Personalization
        assert "preferred_brands" in field_names
        assert "shopping_preferences" in field_names

    def test_product_recommender_field_types(self):
        """Test that Product Recommender fields have correct types and validation."""
        template = IndustryTemplateFactory.get_template(IndustryType.PRODUCT_RECOMMENDER)
        
        field_map = {field.name: field for field in template.booking_form_fields}
        
        # Test email field
        email_field = field_map["customer_email"]
        assert email_field.field_type == FormFieldType.EMAIL
        assert email_field.required is True
        assert email_field.validation_rules["format"] == "email"
        
        # Test phone field
        phone_field = field_map["customer_phone"]
        assert phone_field.field_type == FormFieldType.PHONE
        assert phone_field.required is False  # Phone is optional in the actual implementation
        
        # Test select field for budget
        budget_field = field_map["budget_range"]
        assert budget_field.field_type == FormFieldType.SELECT
        assert budget_field.required is True
        
        # Test select field
        category_field = field_map["product_category"]
        assert category_field.field_type == FormFieldType.SELECT
        assert len(category_field.options) > 0
        assert "Electronics & Gadgets" in category_field.options

    def test_product_recommender_confirmation_fields(self):
        """Test that Product Recommender template has correct confirmation fields."""
        template = IndustryTemplateFactory.get_template(IndustryType.PRODUCT_RECOMMENDER)
        
        confirmation_names = [field.name for field in template.confirmation_fields]
        
        assert "recommendation_delivery" in confirmation_names
        assert "follow_up_preference" in confirmation_names  # Note: singular, not plural
        assert "price_alerts" in confirmation_names
        assert "newsletter_subscription" in confirmation_names

    def test_product_recommender_workflow_nodes(self):
        """Test that Product Recommender template has correct workflow nodes."""
        template = IndustryTemplateFactory.get_template(IndustryType.PRODUCT_RECOMMENDER)
        
        node_names = [node["name"] for node in template.workflow_nodes]
        
        # Check essential workflow nodes
        assert "start" in node_names
        assert "customer_profiling" in node_names
        assert "product_discovery" in node_names
        assert "ai_recommendation" in node_names
        assert "price_comparison" in node_names
        assert "availability_check" in node_names
        assert "recommendation_ranking" in node_names
        assert "customer_notification" in node_names
        assert "feedback_collection" in node_names
        assert "end" in node_names

    def test_product_recommender_workflow_edges(self):
        """Test that Product Recommender template has correct workflow edges."""
        template = IndustryTemplateFactory.get_template(IndustryType.PRODUCT_RECOMMENDER)
        
        # Convert edges to a set of (from, to) tuples for easier testing
        edges = {(edge["from"], edge["to"]) for edge in template.workflow_edges}
        
        # Test key workflow paths
        assert ("start", "customer_profiling") in edges
        assert ("customer_profiling", "product_discovery") in edges
        assert ("product_discovery", "ai_recommendation") in edges
        assert ("ai_recommendation", "price_comparison") in edges
        assert ("price_comparison", "availability_check") in edges
        assert ("availability_check", "recommendation_ranking") in edges
        assert ("feedback_collection", "end") in edges

    def test_product_recommender_business_rules(self):
        """Test that Product Recommender template has appropriate business rules."""
        template = IndustryTemplateFactory.get_template(IndustryType.PRODUCT_RECOMMENDER)
        
        # Should have 24/7 availability for AI recommendations
        assert template.business_hours["monday"]["start"] == "08:00"
        assert template.business_hours["monday"]["end"] == "20:00"
        
        # No advance booking needed for AI recommendations
        assert template.advance_booking_days == 0
        
        # Should have appropriate cancellation policy
        assert "updated anytime" in template.cancellation_policy.lower()

    def test_product_recommender_integrations(self):
        """Test that Product Recommender template has correct integration requirements."""
        template = IndustryTemplateFactory.get_template(IndustryType.PRODUCT_RECOMMENDER)
        
        # Required integrations
        required = template.required_integrations
        assert "ai_engine" in required
        assert "product_catalog" in required
        assert "email" in required
        assert "sms" in required
        
        # Optional integrations
        optional = template.optional_integrations
        assert "whatsapp" in optional
        assert "payment_gateway" in optional
        assert "inventory_management" in optional
        assert "analytics" in optional
        assert "crm" in optional

    def test_product_recommender_regional_support(self):
        """Test that Product Recommender template supports African markets."""
        template = IndustryTemplateFactory.get_template(IndustryType.PRODUCT_RECOMMENDER)
        
        # Should support major African markets
        assert "NG" in template.supported_regions
        assert "KE" in template.supported_regions
        assert "ZA" in template.supported_regions
        assert "GH" in template.supported_regions
        
        # Should support local currencies
        assert "NGN" in template.supported_currencies
        assert "KES" in template.supported_currencies
        assert "ZAR" in template.supported_currencies
        
        # Should support local languages
        assert "en" in template.supported_languages
        assert "ha" in template.supported_languages  # Hausa
        assert "sw" in template.supported_languages  # Swahili

    def test_product_recommender_in_factory_list(self):
        """Test that Product Recommender is available in factory template list."""
        # Test that the factory can create the template
        template = IndustryTemplateFactory.get_template(IndustryType.PRODUCT_RECOMMENDER)
        assert template is not None
        
        # Test that it's in the available industries list
        available_industries = IndustryTemplateFactory.list_available_industries()
        # Check that PRODUCT_RECOMMENDER is now included
        industry_values = [industry.value for industry in available_industries]
        assert "product_recommender" in industry_values

    def test_product_recommender_field_validation_rules(self):
        """Test specific validation rules for Product Recommender fields."""
        template = IndustryTemplateFactory.get_template(IndustryType.PRODUCT_RECOMMENDER)
        
        field_map = {field.name: field for field in template.booking_form_fields}
        
        # Test phone field has African format
        phone_field = field_map["customer_phone"]
        assert phone_field.phone_format == "+234-XXX-XXX-XXXX"
        
        # Test budget range has appropriate options
        budget_field = field_map["budget_range"]
        assert "Under ₦10,000" in budget_field.options
        assert "₦50,000 - ₦100,000" in budget_field.options

    def test_product_recommender_workflow_node_configs(self):
        """Test that workflow nodes have appropriate configurations."""
        template = IndustryTemplateFactory.get_template(IndustryType.PRODUCT_RECOMMENDER)
        
        # Find specific nodes and test their configs
        nodes = {node["name"]: node for node in template.workflow_nodes}
        
        # Customer profiling node should be an agent type
        profiling_node = nodes["customer_profiling"]
        assert profiling_node["type"] == "agent"
        assert profiling_node["config"]["task"] == "analyze_customer_preferences"
        
        # AI recommendation should be an agent type
        recommendation_node = nodes["ai_recommendation"]
        assert recommendation_node["type"] == "agent"
        assert recommendation_node["config"]["task"] == "generate_ai_recommendations"

    def test_product_recommender_error_cases(self):
        """Test error handling for Product Recommender template."""
        # Test that invalid industry type raises appropriate error
        with pytest.raises(ValueError):
            IndustryTemplateFactory.get_template("invalid_industry")
        
        # Test that the template is properly structured
        template = IndustryTemplateFactory.get_template(IndustryType.PRODUCT_RECOMMENDER)
        
        # All required fields should be present
        assert hasattr(template, 'industry')
        assert hasattr(template, 'name')
        assert hasattr(template, 'description')
        assert hasattr(template, 'booking_form_fields')
        assert hasattr(template, 'workflow_nodes')
        assert hasattr(template, 'workflow_edges')

    def test_product_recommender_template_serialization(self):
        """Test that Product Recommender template can be serialized properly."""
        template = IndustryTemplateFactory.get_template(IndustryType.PRODUCT_RECOMMENDER)
        
        # Test that template can be converted to dict
        template_dict = template.model_dump()  # Use model_dump instead of deprecated dict()
        
        assert template_dict["industry"] == "product_recommender"
        assert template_dict["name"] == "AI Product Recommender System"
        assert len(template_dict["booking_form_fields"]) > 0
        assert len(template_dict["workflow_nodes"]) > 0
        assert len(template_dict["workflow_edges"]) > 0
