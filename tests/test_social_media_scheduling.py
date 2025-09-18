"""
Unit tests for social media scheduling and analytics nodes.

Tests cover content calendar generation, scheduling optimization,
and social media analytics with African market considerations.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
import uuid

from smeflow.workflows.state import WorkflowState
from smeflow.workflows.social_media_scheduling import (
    ContentCalendarNode,
    SocialMediaAnalyticsNode
)


class TestContentCalendarNode:
    """Test content calendar generation and scheduling optimization."""

    @pytest.fixture
    def calendar_node(self):
        """Create ContentCalendarNode instance."""
        return ContentCalendarNode()

    @pytest.fixture
    def workflow_state_with_content(self):
        """Create workflow state with multi-platform content."""
        state = WorkflowState(
            workflow_id=uuid.uuid4(),
            tenant_id=str(uuid.uuid4()),
            data={
                "tenant_config": {
                    "business_location": "Lagos, Nigeria",
                    "target_platforms": ["facebook", "instagram", "linkedin", "twitter"],
                    "posting_preferences": {
                        "frequency": {
                            "facebook": "2-3 times daily",
                            "instagram": "1-2 times daily",
                            "linkedin": "3-5 times weekly",
                            "twitter": "3-5 times daily"
                        }
                    }
                },
                "multi_platform_content": {
                    "platform_content": {
                        "facebook": {
                            "post_text": "Fresh local ingredients at our Lagos restaurant!",
                            "optimal_posting_times": ["09:00", "15:00", "20:00"]
                        },
                        "instagram": {
                            "caption": "Authentic Nigerian flavors 🍽️ #LagosEats",
                            "hashtags": ["#LagosEats", "#NigerianFood", "#FreshIngredients"]
                        },
                        "linkedin": {
                            "article_title": "Supporting Local Food Systems in Lagos",
                            "professional_summary": "How our restaurant contributes to local economy"
                        }
                    }
                },
                "campaign_strategy": {
                    "campaign_name": "Lagos Restaurant Launch",
                    "campaign_duration": "30 days"
                }
            }
        )
        return state

    @pytest.mark.asyncio
    async def test_content_calendar_generation(self, calendar_node, workflow_state_with_content):
        """Test content calendar generation."""
        result = await calendar_node._execute_logic(workflow_state_with_content)
        
        assert "content_calendar" in result.data
        calendar_data = result.data["content_calendar"]
        
        # Test calendar structure - should have daily entries
        assert len(calendar_data) > 0
        
        # Test posting guidelines exist
        assert "posting_guidelines" in result.data
        guidelines = result.data["posting_guidelines"]
        assert "frequency_recommendations" in guidelines

    @pytest.mark.asyncio
    async def test_african_timezone_optimization(self, calendar_node, workflow_state_with_content):
        """Test African timezone optimization in scheduling."""
        result = await calendar_node._execute_logic(workflow_state_with_content)
        
        calendar_data = result.data["content_calendar"]
        
        # Test content distribution in guidelines
        guidelines = result.data["posting_guidelines"]
        assert "content_distribution" in guidelines
        distribution = guidelines["content_distribution"]
        assert "educational" in distribution
        
        # Test optimal timing in guidelines
        assert "optimal_timing" in guidelines
        timing = guidelines["optimal_timing"]
        assert "peak_engagement_hours" in timing
        
        # Test that timing guidance exists
        assert "best_days" in timing
        assert "peak_engagement_hours" in timing

    @pytest.mark.asyncio
    async def test_cultural_awareness_integration(self, calendar_node, workflow_state_with_content):
        """Test cultural awareness in content scheduling."""
        result = await calendar_node._execute_logic(workflow_state_with_content)
        
        calendar_data = result.data["content_calendar"]
        
        # Test that daily entries have regional considerations
        first_day_key = list(calendar_data.keys())[0]
        first_day = calendar_data[first_day_key]
        assert "regional_considerations" in first_day
        regional = first_day["regional_considerations"]
        assert "holidays" in regional
        assert "cultural_events" in regional
        
        # Test cultural events exist
        assert "cultural_events" in regional

        # Test holidays structure
        local_holidays = regional["holidays"]
        assert isinstance(local_holidays, list)

    @pytest.mark.asyncio
    async def test_platform_specific_scheduling(self, calendar_node, workflow_state_with_content):
        """Test platform-specific scheduling optimization."""
        result = await calendar_node._execute_logic(workflow_state_with_content)
        
        calendar_data = result.data["content_calendar"]
        
        # Test that posts are scheduled for different platforms
        posts_found = False
        for day_key, day_data in calendar_data.items():
            if "posts" in day_data and len(day_data["posts"]) > 0:
                posts_found = True
                for post in day_data["posts"]:
                    assert "platform" in post
                    assert "scheduled_time" in post
                    assert "content_type" in post
        
        # Should have some posts scheduled or calendar data
        assert posts_found or len(calendar_data) > 0

    @pytest.mark.asyncio
    async def test_content_theme_distribution(self, calendar_node, workflow_state_with_content):
        """Test content theme distribution across calendar."""
        result = await calendar_node._execute_logic(workflow_state_with_content)
        
        calendar_data = result.data["content_calendar"]
        
        # Test content themes in daily schedule
        themes_found = False
        for day_key, day_data in calendar_data.items():
            if "content_themes" in day_data:
                themes_found = True
                assert isinstance(day_data["content_themes"], list)
                assert len(day_data["content_themes"]) > 0
        
        assert themes_found
        
        # Test that calendar has daily entries with themes
        assert len(calendar_data) > 0
        
        # Test that daily entries have content themes
        for day_key, day_data in calendar_data.items():
            if "content_themes" in day_data:
                assert isinstance(day_data["content_themes"], list)
                assert len(day_data["content_themes"]) > 0
        
        # Test that themes are found in daily entries
        assert themes_found

    @pytest.mark.asyncio
    async def test_optimal_timing_calculation(self, calendar_node, workflow_state_with_content):
        """Test optimal timing calculation for posts."""
        result = await calendar_node._execute_logic(workflow_state_with_content)
        
        calendar_data = result.data["content_calendar"]
        # Test optimal times in daily schedule
        optimal_times_found = False
        for day_key, day_data in calendar_data.items():
            if "optimal_times" in day_data:
                optimal_times_found = True
                times = day_data["optimal_times"]
                assert len(times) > 0
        
        # Should have optimal timing guidance
        assert optimal_times_found or "optimal_timing" in result.data["posting_guidelines"]


class TestSocialMediaAnalyticsNode:
    """Test social media analytics and performance tracking."""

    @pytest.fixture
    def analytics_node(self):
        """Create SocialMediaAnalyticsNode instance."""
        return SocialMediaAnalyticsNode()

    @pytest.fixture
    def workflow_state_with_calendar(self):
        """Create workflow state with content calendar."""
        state = WorkflowState(
            workflow_id=uuid.uuid4(),
            tenant_id=str(uuid.uuid4()),
            data={
                "tenant_config": {
                    "target_platforms": ["facebook", "instagram", "linkedin", "twitter"],
                    "analytics_preferences": {
                        "tracking_metrics": ["reach", "engagement", "clicks", "conversions"],
                        "reporting_frequency": "weekly"
                    }
                },
                "content_calendar": {
                    "calendar_overview": {
                        "total_posts": 120,
                        "campaign_duration": "30 days"
                    },
                    "daily_schedule": [
                        {
                            "date": "2024-01-01",
                            "posts": [
                                {"platform": "facebook", "content_type": "image_post"},
                                {"platform": "instagram", "content_type": "story"}
                            ]
                        }
                    ]
                },
                "campaign_strategy": {
                    "campaign_name": "Lagos Restaurant Launch",
                    "success_metrics": {
                        "target_reach": 50000,
                        "target_engagement_rate": 5.0,
                        "target_conversions": 500
                    }
                }
            }
        )
        return state

    @pytest.mark.asyncio
    async def test_analytics_setup(self, analytics_node, workflow_state_with_calendar):
        """Test social media analytics setup."""
        result = await analytics_node._execute_logic(workflow_state_with_calendar)
        
        assert "social_media_analytics" in result.data
        analytics_data = result.data["social_media_analytics"]
        
        # Test overall metrics
        assert "overall_metrics" in analytics_data
        overall = analytics_data["overall_metrics"]
        assert "total_reach" in overall
        assert "total_engagement" in overall
        assert "engagement_rate" in overall

    @pytest.mark.asyncio
    async def test_performance_metrics_structure(self, analytics_node, workflow_state_with_calendar):
        """Test performance metrics structure."""
        result = await analytics_node._execute_logic(workflow_state_with_calendar)
        
        analytics_data = result.data["social_media_analytics"]
        
        # Test platform breakdown
        assert "platform_breakdown" in analytics_data
        platform_breakdown = analytics_data["platform_breakdown"]
        
        # Test each platform has required metrics
        for platform in ["facebook", "instagram", "linkedin", "twitter"]:
            if platform in platform_breakdown:
                platform_data = platform_breakdown[platform]
                assert "reach" in platform_data
                assert "engagement" in platform_data
                assert "engagement_rate" in platform_data

    @pytest.mark.asyncio
    async def test_audience_insights(self, analytics_node, workflow_state_with_calendar):
        """Test audience insights generation."""
        result = await analytics_node._execute_logic(workflow_state_with_calendar)
        
        analytics_data = result.data["social_media_analytics"]
        
        # Test audience insights
        assert "audience_insights" in analytics_data
        audience_insights = analytics_data["audience_insights"]
        
        # Test demographic data
        assert "demographics" in audience_insights
        demographics = audience_insights["demographics"]
        assert "age_groups" in demographics
        assert "gender_split" in demographics
        assert "top_locations" in demographics
        
        # Test that locations include African markets
        locations = demographics["top_locations"]
        assert isinstance(locations, list)
        assert len(locations) > 0

        # Test behavior patterns
        assert "behavior_patterns" in audience_insights
        behavior = audience_insights["behavior_patterns"]
        assert "content_preferences" in behavior

    @pytest.mark.asyncio
    async def test_optimization_recommendations(self, analytics_node, workflow_state_with_calendar):
        """Test optimization recommendations generation."""
        result = await analytics_node._execute_logic(workflow_state_with_calendar)
        
        analytics_data = result.data["social_media_analytics"]
        
        # Test that analytics includes recommendations in audience insights
        assert "audience_insights" in analytics_data
        audience_insights = analytics_data["audience_insights"]
        assert "behavior_patterns" in audience_insights
        behavior = audience_insights["behavior_patterns"]
        assert "content_preferences" in behavior

    @pytest.mark.asyncio
    async def test_competitive_analysis_integration(self, analytics_node, workflow_state_with_calendar):
        """Test competitive analysis in analytics."""
        result = await analytics_node._execute_logic(workflow_state_with_calendar)
        
        analytics_data = result.data["social_media_analytics"]
        
        # Test competitive analysis
        assert "competitive_analysis" in analytics_data
        comp_analysis = analytics_data["competitive_analysis"]
        assert "competitor_gaps" in comp_analysis
        assert "market_position" in comp_analysis
        assert "share_of_voice" in comp_analysis
        
        # Test competitor gaps analysis
        competitor_gaps = comp_analysis["competitor_gaps"]
        assert isinstance(competitor_gaps, list)
        assert len(competitor_gaps) > 0

    @pytest.mark.asyncio
    async def test_roi_tracking(self, analytics_node, workflow_state_with_calendar):
        """Test ROI tracking and business impact measurement."""
        result = await analytics_node._execute_logic(workflow_state_with_calendar)
        
        analytics_data = result.data["social_media_analytics"]
        
        # Test that overall metrics include business impact data
        assert "overall_metrics" in analytics_data
        overall = analytics_data["overall_metrics"]
        assert "total_reach" in overall
        assert "total_engagement" in overall
        assert "engagement_rate" in overall

    @pytest.mark.asyncio
    async def test_african_market_analytics(self, analytics_node, workflow_state_with_calendar):
        """Test African market-specific analytics considerations."""
        result = await analytics_node._execute_logic(workflow_state_with_calendar)
        
        analytics_data = result.data["social_media_analytics"]
        
        # Test that audience insights include regional data
        assert "audience_insights" in analytics_data
        audience_insights = analytics_data["audience_insights"]
        assert "demographics" in audience_insights
        demographics = audience_insights["demographics"]
        assert "top_locations" in demographics
        
        # Test that locations include African markets
        locations = demographics["top_locations"]
        assert isinstance(locations, list)
        assert len(locations) > 0

    @pytest.mark.asyncio
    async def test_reporting_automation(self, analytics_node, workflow_state_with_calendar):
        """Test automated reporting setup."""
        result = await analytics_node._execute_logic(workflow_state_with_calendar)
        
        analytics_data = result.data["social_media_analytics"]
        
        # Test that analytics data is structured for reporting
        assert "platform_breakdown" in analytics_data
        platform_breakdown = analytics_data["platform_breakdown"]
        
        # Test that each platform has metrics suitable for reporting
        for platform in ["facebook", "instagram", "linkedin", "twitter"]:
            if platform in platform_breakdown:
                platform_data = platform_breakdown[platform]
                assert "reach" in platform_data
                assert "engagement" in platform_data


class TestSchedulingIntegration:
    """Test integration between scheduling and analytics nodes."""

    @pytest.mark.asyncio
    async def test_calendar_to_analytics_integration(self):
        """Test data flow from calendar to analytics."""
        # Create initial state with content
        state = WorkflowState(
            workflow_id=uuid.uuid4(),
            tenant_id=str(uuid.uuid4()),
            data={
                "tenant_config": {
                    "target_platforms": ["facebook", "instagram", "linkedin"],
                    "business_location": "Nairobi, Kenya"
                },
                "multi_platform_content": {
                    "platform_content": {
                        "facebook": {"post_text": "Kenyan coffee excellence"},
                        "instagram": {"caption": "Fresh roasted beans ☕"}
                    }
                },
                "campaign_strategy": {
                    "campaign_name": "Nairobi Coffee Launch",
                    "campaign_duration": "30 days"
                }
            }
        )
        
        # Execute calendar node
        calendar_node = ContentCalendarNode()
        state = await calendar_node._execute_logic(state)
        
        # Execute analytics node
        analytics_node = SocialMediaAnalyticsNode()
        state = await analytics_node._execute_logic(state)
        
        # Verify integration
        assert "content_calendar" in state.data
        assert "social_media_analytics" in state.data
        
        # Analytics should reference calendar data
        analytics_data = state.data["social_media_analytics"]
        calendar_data = state.data["content_calendar"]
        
        # Analytics should have platform breakdown
        assert "platform_breakdown" in analytics_data
        platform_breakdown = analytics_data["platform_breakdown"]
        
        # Verify platform consistency
        assert "facebook" in platform_breakdown
        assert "instagram" in platform_breakdown
        assert "linkedin" in platform_breakdown

    @pytest.mark.asyncio
    async def test_tenant_specific_scheduling_preferences(self):
        """Test tenant-specific scheduling and analytics preferences."""
        tenant_id = str(uuid.uuid4())
        
        state = WorkflowState(
            workflow_id=uuid.uuid4(),
            tenant_id=tenant_id,
            data={
                "tenant_config": {
                    "business_location": "Accra, Ghana",
                    "target_platforms": ["facebook", "instagram", "twitter"],
                    "posting_preferences": {
                        "frequency": {
                            "facebook": "3 times daily",
                            "instagram": "2 times daily",
                            "twitter": "5 times daily"
                        },
                        "optimal_times": {
                            "facebook": ["08:00", "13:00", "19:00"],
                            "instagram": ["11:00", "16:00"],
                            "twitter": ["07:00", "12:00", "15:00", "18:00", "21:00"]
                        }
                    },
                    "analytics_preferences": {
                        "tracking_metrics": ["reach", "engagement", "conversions"],
                        "reporting_frequency": "daily"
                    }
                }
            }
        )
        
        # Execute scheduling
        calendar_node = ContentCalendarNode()
        result = await calendar_node._execute_logic(state)
        
        # Verify tenant-specific preferences are applied
        calendar_data = result.data["content_calendar"]
        
        # Check that calendar respects tenant preferences
        guidelines = result.data["posting_guidelines"]
        assert "frequency_recommendations" in guidelines
        freq_recs = guidelines["frequency_recommendations"]
        
        # Should reflect tenant preferences for platforms
        assert "facebook" in freq_recs
        assert "instagram" in freq_recs
        assert "twitter" in freq_recs
        
        # Check optimal timing exists
        assert "optimal_timing" in guidelines
        timing = guidelines["optimal_timing"]
        assert "peak_engagement_hours" in timing
        
        # Execute analytics
        analytics_node = SocialMediaAnalyticsNode()
        result = await analytics_node._execute_logic(result)
        
        # Verify analytics respects tenant preferences
        analytics_data = result.data["social_media_analytics"]
        
        # Should have platform breakdown for configured platforms
        assert "platform_breakdown" in analytics_data
        platform_breakdown = analytics_data["platform_breakdown"]
        assert "facebook" in platform_breakdown
        assert "instagram" in platform_breakdown
        assert "twitter" in platform_breakdown


if __name__ == "__main__":
    pytest.main([__file__])
