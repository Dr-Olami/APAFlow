"""
Unit tests for Marketing Campaigns workflow template.

Tests the Marketing Campaigns industry template including form fields,
workflow nodes, business rules, and African market optimizations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import uuid

from smeflow.workflows.templates import (
    IndustryTemplateFactory, 
    IndustryType, 
    FormFieldType,
    IndustryTemplate
)
from smeflow.workflows.marketing_campaigns_nodes import (
    MarketResearchNode, TrendAnalysisNode, AudienceSegmentationNode,
    CampaignStrategyNode, ContentPlanningNode, BudgetAllocationNode,
    CampaignSetupNode, PerformanceTrackingNode, OptimizationNode, ReportingNode
)
from smeflow.workflows.nodes import BaseNode
from smeflow.workflows.state import WorkflowState


class TestMarketingCampaignsTemplate:
    """Test suite for Marketing Campaigns industry template."""

    def test_create_marketing_campaigns_template(self):
        """Test creating Marketing Campaigns template."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        assert isinstance(template, IndustryTemplate)
        assert template.industry == IndustryType.MARKETING_CAMPAIGNS
        assert template.name == "Marketing Campaigns Management"
        assert "hyperlocal trend analysis" in template.description.lower()
        
    def test_marketing_campaigns_booking_form_fields(self):
        """Test Marketing Campaigns booking form fields."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        # Check required fields
        field_names = [field.name for field in template.booking_form_fields]
        required_fields = [
            "campaign_name", "client_name", "client_email", "client_phone",
            "campaign_type", "target_regions", "target_audience", "campaign_budget",
            "campaign_duration", "campaign_objectives", "preferred_channels",
            "campaign_start_date"
        ]
        
        for required_field in required_fields:
            assert required_field in field_names, f"Missing required field: {required_field}"
        
    def test_campaign_type_field_options(self):
        """Test campaign type field has correct options."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        campaign_type_field = next(
            field for field in template.booking_form_fields 
            if field.name == "campaign_type"
        )
        
        expected_options = [
            "Brand Awareness", "Lead Generation", "Product Launch",
            "Social Media Campaign", "Email Marketing", "Influencer Marketing",
            "Content Marketing", "Performance Marketing"
        ]
        
        assert campaign_type_field.field_type == FormFieldType.SELECT
        assert campaign_type_field.required is True
        for option in expected_options:
            assert option in campaign_type_field.options
            
    def test_target_regions_field(self):
        """Test target regions field configuration."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        target_regions_field = next(
            field for field in template.booking_form_fields 
            if field.name == "target_regions"
        )
        
        assert target_regions_field.field_type == FormFieldType.MULTISELECT
        assert target_regions_field.required is True
        
        # Check African cities are included
        african_cities = ["Lagos, Nigeria", "Nairobi, Kenya", "Cape Town, South Africa", "Accra, Ghana"]
        for city in african_cities:
            assert city in target_regions_field.options
            
    def test_campaign_budget_field(self):
        """Test campaign budget field with Nigerian Naira options."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        budget_field = next(
            field for field in template.booking_form_fields 
            if field.name == "campaign_budget"
        )
        
        assert budget_field.field_type == FormFieldType.SELECT
        assert budget_field.required is True
        
        # Check NGN currency options
        ngn_options = [opt for opt in budget_field.options if "₦" in opt]
        assert len(ngn_options) > 0, "Should have Nigerian Naira budget options"
        
    def test_campaign_objectives_multiselect(self):
        """Test campaign objectives as multiselect field."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        objectives_field = next(
            field for field in template.booking_form_fields 
            if field.name == "campaign_objectives"
        )
        
        assert objectives_field.field_type == FormFieldType.MULTISELECT
        assert objectives_field.required is True
        
        expected_objectives = [
            "Increase brand awareness", "Generate leads", "Drive website traffic",
            "Boost sales", "Improve engagement", "Build community"
        ]
        
        for objective in expected_objectives:
            assert objective in objectives_field.options
            
    def test_preferred_channels_field(self):
        """Test preferred marketing channels field."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        channels_field = next(
            field for field in template.booking_form_fields 
            if field.name == "preferred_channels"
        )
        
        assert channels_field.field_type == FormFieldType.MULTISELECT
        assert channels_field.required is True
        
        # Check major platforms are included
        major_platforms = ["Facebook", "Instagram", "LinkedIn", "WhatsApp Business", "Google Ads"]
        for platform in major_platforms:
            assert platform in channels_field.options
            
    def test_confirmation_fields(self):
        """Test Marketing Campaigns confirmation fields."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        confirmation_field_names = [field.name for field in template.confirmation_fields]
        expected_fields = ["analytics_access", "reporting_frequency", "approval_process"]
        
        for field_name in expected_fields:
            assert field_name in confirmation_field_names
            
    def test_workflow_nodes_structure(self):
        """Test Marketing Campaigns workflow nodes."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        node_names = [node["name"] for node in template.workflow_nodes]
        expected_nodes = [
            "start", "market_research", "trend_analysis", "audience_segmentation",
            "campaign_strategy", "content_planning", "budget_allocation",
            "campaign_setup", "performance_tracking", "optimization", "reporting", "end"
        ]
        
        for node_name in expected_nodes:
            assert node_name in node_names, f"Missing workflow node: {node_name}"
            
    def test_workflow_edges_connectivity(self):
        """Test workflow edges form proper sequence."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        # Check start and end connections
        start_edge = next(edge for edge in template.workflow_edges if edge["from"] == "start")
        assert start_edge["to"] == "market_research"
        
        end_edge = next(edge for edge in template.workflow_edges if edge["to"] == "end")
        assert end_edge["from"] == "reporting"
        
        # Check sequential flow
        expected_sequence = [
            ("start", "market_research"),
            ("market_research", "trend_analysis"),
            ("trend_analysis", "audience_segmentation"),
            ("audience_segmentation", "campaign_strategy"),
            ("campaign_strategy", "content_planning"),
            ("content_planning", "budget_allocation"),
            ("budget_allocation", "campaign_setup"),
            ("campaign_setup", "performance_tracking"),
            ("performance_tracking", "optimization"),
            ("optimization", "reporting"),
            ("reporting", "end")
        ]
        
        for from_node, to_node in expected_sequence:
            edge_exists = any(
                edge["from"] == from_node and edge["to"] == to_node 
                for edge in template.workflow_edges
            )
            assert edge_exists, f"Missing edge: {from_node} -> {to_node}"
            
    def test_business_hours_configuration(self):
        """Test business hours for marketing campaigns."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        # Marketing campaigns typically have extended hours
        assert template.business_hours["monday"]["start"] == "08:00"
        assert template.business_hours["monday"]["end"] == "18:00"
        assert template.business_hours["saturday"]["start"] == "09:00"
        assert template.business_hours["sunday"]["closed"] is True
        
    def test_advance_booking_days(self):
        """Test advance booking requirements."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        # Marketing campaigns need planning time
        assert template.advance_booking_days == 7
        
    def test_cancellation_policy(self):
        """Test cancellation policy for marketing campaigns."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        assert "3 days advance notice" in template.cancellation_policy
        assert "campaign modifications" in template.cancellation_policy
        
    def test_required_integrations(self):
        """Test required integrations for marketing campaigns."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        expected_integrations = ["social_media_apis", "analytics_platforms", "email_marketing"]
        
        for integration in expected_integrations:
            assert integration in template.required_integrations
            
    def test_optional_integrations(self):
        """Test optional integrations including ML components."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        expected_optional = ["crm_system", "payment_gateway", "mixpost", "mlflow"]
        
        for integration in expected_optional:
            assert integration in template.optional_integrations
            
    def test_african_market_support(self):
        """Test African market optimizations."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        # Check supported regions
        expected_regions = ["NG", "KE", "ZA", "GH", "UG", "TZ"]
        for region in expected_regions:
            assert region in template.supported_regions
            
        # Check supported currencies
        expected_currencies = ["NGN", "KES", "ZAR", "GHS", "UGX", "TZS"]
        for currency in expected_currencies:
            assert currency in template.supported_currencies
            
        # Check supported languages
        expected_languages = ["en", "ha", "yo", "ig", "sw", "af", "zu"]
        for language in expected_languages:
            assert language in template.supported_languages
            
    def test_phone_field_african_format(self):
        """Test phone field uses African format."""
        template = IndustryTemplateFactory.create_marketing_campaigns_template()
        
        phone_field = next(
            field for field in template.booking_form_fields 
            if field.name == "client_phone"
        )
        
        assert phone_field.field_type == FormFieldType.PHONE
        assert phone_field.phone_format == "+234-XXX-XXX-XXXX"  # Nigerian format
        assert "+234-801-234-5678" in phone_field.placeholder
        
    def test_template_factory_integration(self):
        """Test Marketing Campaigns template is available in factory."""
        # Test get_template method
        template = IndustryTemplateFactory.get_template(IndustryType.MARKETING_CAMPAIGNS)
        assert template.industry == IndustryType.MARKETING_CAMPAIGNS
        
        # Test list_available_industries includes marketing campaigns
        available_industries = IndustryTemplateFactory.list_available_industries()
        assert IndustryType.MARKETING_CAMPAIGNS in available_industries


class TestMarketingCampaignsWorkflowNodes:
    """Test suite for Marketing Campaigns workflow nodes."""

    @pytest.fixture
    def sample_workflow_state(self):
        """Create sample workflow state for testing."""
        return WorkflowState(
            workflow_id=uuid.uuid4(),
            execution_id=uuid.uuid4(),
            tenant_id="test_tenant",
            current_node="market_research",
            status="running",
            data={
                "campaign_name": "Test Campaign",
                "client_name": "Test Client",
                "client_email": "test@example.com",
                "target_regions": ["Lagos, Nigeria", "Nairobi, Kenya"],
                "campaign_type": "Brand Awareness",
                "campaign_budget": "₦1,000,000 - ₦2,500,000",
                "campaign_objectives": ["Increase brand awareness", "Generate leads"],
                "preferred_channels": ["Facebook", "Instagram", "LinkedIn"]
            },
            metadata={}
        )

    @pytest.mark.asyncio
    async def test_market_research_node(self, sample_workflow_state):
        """Test MarketResearchNode execution."""
        node = MarketResearchNode()

        result = await node.execute(sample_workflow_state)

        assert isinstance(result, WorkflowState)
        assert "market_research" in result.data
        assert "competitive_landscape" in result.data["market_research"]
        assert "recommended_positioning" in result.data["market_research"]
        assert "last_research_update" in result.context

        # Test node inheritance
        assert isinstance(node, BaseNode)
        assert hasattr(node, "config")

        # Check market insights structure
        market_insights = sample_workflow_state.data["market_research"]
        assert "regional_analysis" in market_insights
        assert "market_opportunities" in market_insights
        assert "competitive_landscape" in market_insights

    @pytest.mark.asyncio
    async def test_trend_analysis_node(self, sample_workflow_state):
        """Test TrendAnalysisNode execution."""
        node = TrendAnalysisNode()

        result = await node.execute(sample_workflow_state)

        assert isinstance(result, WorkflowState)
        assert "trend_analysis" in result.data
        assert "trending_topics" in result.data["trend_analysis"]
        assert "seasonal_patterns" in result.data["trend_analysis"]
        assert "content_preferences" in result.data["trend_analysis"]
        assert "trend_analysis_timestamp" in result.context

        # Test node inheritance
        assert isinstance(node, BaseNode)
        assert hasattr(node, "config")

        # Check trend insights structure
        trend_insights = sample_workflow_state.data["trend_analysis"]
        assert "trending_topics" in trend_insights
        assert "seasonal_patterns" in trend_insights
        assert "hashtag_recommendations" in trend_insights

    @pytest.mark.asyncio
    async def test_audience_segmentation_node(self, sample_workflow_state):
        """Test AudienceSegmentationNode execution."""
        node = AudienceSegmentationNode()

        result = await node.execute(sample_workflow_state)

        assert isinstance(result, WorkflowState)
        assert "audience_segmentation" in result.data
        assert "primary_segments" in result.data["audience_segmentation"]
        assert "targeting_recommendations" in result.data["audience_segmentation"]
        assert "segmentation_timestamp" in result.context

        # Test node inheritance
        assert isinstance(node, BaseNode)
        assert hasattr(node, "config")

        # Check segmentation structure
        segments = sample_workflow_state.data["audience_segmentation"]
        assert "primary_segments" in segments
        assert "targeting_recommendations" in segments

    @pytest.mark.asyncio
    async def test_campaign_strategy_node(self, sample_workflow_state):
        """Test CampaignStrategyNode execution."""
        sample_workflow_state.data.update({
            "market_research": {"competitive_landscape": {}},
            "trend_analysis": {"trending_topics": {}},
            "audience_segmentation": {"primary_segments": []}
        })

        node = CampaignStrategyNode()

        result = await node.execute(sample_workflow_state)

        assert isinstance(result, WorkflowState)
        assert "campaign_strategy" in result.data
        assert "strategy_overview" in result.data["campaign_strategy"]
        assert "channel_strategy" in result.data["campaign_strategy"]
        assert "execution_phases" in result.data["campaign_strategy"]
        assert "strategy_created" in result.context

        # Test node inheritance
        assert isinstance(node, BaseNode)
        assert hasattr(node, "config")

        # Check strategy structure
        strategy = sample_workflow_state.data["campaign_strategy"]
        assert "strategy_overview" in strategy
        assert "execution_phases" in strategy
        assert "channel_strategy" in strategy
        assert "success_metrics" in strategy

    @pytest.mark.asyncio
    async def test_content_planning_node(self, sample_workflow_state):
        """Test ContentPlanningNode execution."""
        node = ContentPlanningNode()

        result = await node.execute(sample_workflow_state)

        assert isinstance(result, WorkflowState)
        assert "content_plan" in result.data
        assert "content_calendar" in result.data["content_plan"]
        assert "creative_guidelines" in result.data["content_plan"]
        assert "asset_requirements" in result.data["content_plan"]
        assert "content_plan_created" in result.context

        # Test node inheritance
        assert isinstance(node, BaseNode)
        assert hasattr(node, "config")

        # Check content plan structure
        content_plan = sample_workflow_state.data["content_plan"]
        assert "content_calendar" in content_plan
        assert "creative_guidelines" in content_plan
        assert "asset_requirements" in content_plan

    @pytest.mark.asyncio
    async def test_budget_allocation_node(self, sample_workflow_state):
        """Test BudgetAllocationNode execution."""
        node = BudgetAllocationNode()

        result = await node.execute(sample_workflow_state)

        assert isinstance(result, WorkflowState)
        assert "budget_allocation" in result.data
        assert "channel_allocation" in result.data["budget_allocation"]
        assert "phase_allocation" in result.data["budget_allocation"]
        assert "contingency_fund" in result.data["budget_allocation"]
        assert "budget_optimized" in result.context

        # Test node inheritance
        assert isinstance(node, BaseNode)
        assert hasattr(node, "config")

        # Check budget allocation structure
        budget_plan = sample_workflow_state.data["budget_allocation"]
        assert "total_budget" in budget_plan
        assert "channel_allocation" in budget_plan
        assert "phase_allocation" in budget_plan

        # Verify budget percentages add up correctly
        channel_percentages = [
            float(channel["percentage"].rstrip('%')) 
            for channel in budget_plan["channel_allocation"].values()
        ]
        # Allow for small rounding differences
        assert abs(sum(channel_percentages) - 100) < 1

    @pytest.mark.asyncio
    async def test_campaign_setup_node(self, sample_workflow_state):
        """Test CampaignSetupNode execution."""
        node = CampaignSetupNode()

        result = await node.execute(sample_workflow_state)

        assert isinstance(result, WorkflowState)
        assert "campaign_setup" in result.data
        assert "campaign_ids" in result.data["campaign_setup"]
        assert "tracking_setup" in result.data["campaign_setup"]
        assert "dashboard_links" in result.data["campaign_setup"]
        assert "setup_completed" in result.context

        # Test node inheritance
        assert isinstance(node, BaseNode)
        assert hasattr(node, "config")

        # Check setup results structure
        setup_results = sample_workflow_state.data["campaign_setup"]
        assert "campaign_ids" in setup_results
        assert "tracking_setup" in setup_results
        assert "channel_configurations" in setup_results
        assert "dashboard_links" in setup_results

    @pytest.mark.asyncio
    async def test_performance_tracking_node(self, sample_workflow_state):
        """Test PerformanceTrackingNode execution."""
        node = PerformanceTrackingNode()

        result = await node.execute(sample_workflow_state)

        assert isinstance(result, WorkflowState)
        assert "performance_metrics" in result.data
        assert "overall_performance" in result.data["performance_metrics"]
        assert "channel_performance" in result.data["performance_metrics"]
        assert "optimization_alerts" in result.data["performance_metrics"]
        assert "last_performance_update" in result.context

        # Test node inheritance
        assert isinstance(node, BaseNode)
        assert hasattr(node, "config")

        # Check performance metrics structure
        metrics = sample_workflow_state.data["performance_metrics"]
        assert "overall_performance" in metrics
        assert "channel_performance" in metrics
        assert "optimization_alerts" in metrics

    @pytest.mark.asyncio
    async def test_optimization_node(self, sample_workflow_state):
        """Test OptimizationNode execution."""
        sample_workflow_state.data["performance_metrics"] = {
            "overall_performance": {"ctr": "2.56%"},
            "channel_performance": {"linkedin": {"roas": "4.1x"}}
        }

        node = OptimizationNode()

        result = await node.execute(sample_workflow_state)

        assert isinstance(result, WorkflowState)
        assert "optimization_actions" in result.data
        assert "optimization_results" in result.data
        assert "performance_impact" in result.data["optimization_results"]
        assert "last_optimization" in result.context

        # Test node inheritance
        assert isinstance(node, BaseNode)
        assert hasattr(node, "config")

        # Check optimization structure
        assert "optimization_actions" in sample_workflow_state.data
        assert "optimization_results" in sample_workflow_state.data

    @pytest.mark.asyncio
    async def test_reporting_node(self, sample_workflow_state):
        """Test ReportingNode execution."""
        sample_workflow_state.data.update({
            "performance_metrics": {"overall_performance": {}},
            "optimization_results": {"performance_impact": {}},
            "campaign_strategy": {"strategy_overview": {}}
        })

        node = ReportingNode()

        result = await node.execute(sample_workflow_state)

        assert isinstance(result, WorkflowState)
        assert result.status == "completed"
        assert "campaign_report" in result.data
        assert "executive_summary" in result.data["campaign_report"]
        assert "detailed_metrics" in result.data["campaign_report"]
        assert "recommendations" in result.data["campaign_report"]
        assert "report_generated" in result.context

        # Test node inheritance
        assert isinstance(node, BaseNode)
        assert hasattr(node, "config")

        # Check report structure
        report = sample_workflow_state.data["campaign_report"]
        assert "executive_summary" in report
        assert "detailed_metrics" in report
        assert "recommendations" in report
        assert "next_steps" in report

    @pytest.mark.asyncio
    async def test_node_error_handling(self, sample_workflow_state):
        """Test node error handling."""
        node = MarketResearchNode()

        invalid_state = WorkflowState(
            workflow_id=uuid.uuid4(),
            execution_id=uuid.uuid4(),
            tenant_id="test_tenant",
            current_node="market_research",
            status="running",
            data={},  
            context={}  
        )

        result = await node.execute(invalid_state)
        assert isinstance(result, WorkflowState)
        assert "market_research" in result.data

    def test_node_inheritance(self):
        """Test all nodes inherit from BaseNode."""
        from smeflow.workflows.nodes import BaseNode
        
        node_classes = [
            MarketResearchNode, TrendAnalysisNode, AudienceSegmentationNode,
            CampaignStrategyNode, ContentPlanningNode, BudgetAllocationNode,
            CampaignSetupNode, PerformanceTrackingNode, OptimizationNode, ReportingNode
        ]
        
        for node_class in node_classes:
            assert issubclass(node_class, BaseNode)
            
        # Test node instantiation
        for node_class in node_classes:
            node = node_class()
            assert hasattr(node, 'execute')
            assert callable(getattr(node, 'execute'))


if __name__ == "__main__":
    pytest.main([__file__])
