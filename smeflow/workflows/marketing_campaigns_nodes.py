"""
Marketing Campaigns Workflow Nodes for SMEFlow.

This module provides specialized workflow nodes for marketing campaigns
with hyperlocal trend analysis and performance optimization capabilities.
"""

from typing import Dict, Any, List, Optional
import asyncio
import json
from datetime import datetime, timedelta
import uuid

from ..workflows.state import WorkflowState
from ..workflows.nodes import BaseNode, NodeConfig


class MarketResearchNode(BaseNode):
    """
    Conducts hyperlocal market research for campaign planning.
    
    This node analyzes local market conditions, competitor landscape,
    and regional opportunities for the target campaign.
    """
    
    def __init__(self, config: Optional[NodeConfig] = None):
        """Initialize MarketResearchNode with configuration."""
        if config is None:
            config = NodeConfig(
                name="market_research",
                description="Conducts hyperlocal market research for campaign planning",
                region_specific=True,
                supported_regions=["NG", "KE", "ZA", "GH", "UG", "TZ"],
                supported_languages=["en", "ha", "yo", "ig", "sw", "af", "zu"]
            )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Execute hyperlocal market research.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state with market research results
        """
        # Reason: Mock implementation for Phase 1 - will be replaced with ProAgent integration
        target_regions = state.data.get("target_regions", [])
        campaign_type = state.data.get("campaign_type", "Brand Awareness")
        
        # Mock market research data
        market_insights = {
            "regional_analysis": {
                region: {
                    "market_size": f"₦{1000000 + hash(region) % 5000000:,}",
                    "competition_level": ["Low", "Medium", "High"][hash(region) % 3],
                    "growth_potential": ["Moderate", "High", "Very High"][hash(region) % 3],
                    "key_demographics": {
                        "age_groups": ["18-25", "26-35", "36-45"],
                        "income_levels": ["Lower-middle", "Middle", "Upper-middle"],
                        "digital_adoption": ["Medium", "High"][hash(region) % 2]
                    }
                }
                for region in target_regions
            },
            "market_opportunities": [
                "Growing mobile commerce adoption",
                "Increased social media engagement",
                "Rising disposable income in urban areas",
                "Expanding internet penetration"
            ],
            "competitive_landscape": {
                "direct_competitors": 3 + (hash(campaign_type) % 5),
                "market_leaders": ["Brand A", "Brand B", "Brand C"],
                "competitive_gaps": [
                    "Limited local language content",
                    "Weak mobile optimization",
                    "Poor customer service"
                ]
            },
            "recommended_positioning": f"Focus on {campaign_type.lower()} with local cultural relevance"
        }
        
        # Update state with research data
        state.data["market_research"] = market_insights
        state.context["last_research_update"] = datetime.now().isoformat()
        
        return state


class TrendAnalysisNode(BaseNode):
    """
    Analyzes hyperlocal trends and patterns for campaign optimization.
    
    This node processes social media trends, local events, and seasonal
    patterns to inform campaign timing and messaging.
    """
    
    def __init__(self, config: Optional[NodeConfig] = None):
        """Initialize TrendAnalysisNode with configuration."""
        if config is None:
            config = NodeConfig(
                name="trend_analysis",
                description="Analyzes hyperlocal trends and patterns for campaign optimization",
                region_specific=True,
                supported_regions=["NG", "KE", "ZA", "GH", "UG", "TZ"],
                supported_languages=["en", "ha", "yo", "ig", "sw", "af", "zu"]
            )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Execute hyperlocal trend analysis.
        
        Args:
            state: Current workflow state
            
        Returns:
            Trend analysis results and recommendations
        """
        # Reason: Mock implementation for Phase 1 - will be replaced with ML-powered trend analysis
        target_regions = state.data.get("target_regions", [])
        campaign_objectives = state.data.get("campaign_objectives", [])
        
        # Mock trend analysis
        trend_insights = {
            "trending_topics": {
                region: [
                    f"Local {region.split(',')[0]} culture",
                    "Mobile payments",
                    "Small business support",
                    "Digital transformation"
                ]
                for region in target_regions
            },
            "seasonal_patterns": {
                "current_season": "High engagement period",
                "optimal_timing": {
                    "best_days": ["Monday", "Wednesday", "Friday"],
                    "best_hours": ["9:00-11:00", "14:00-16:00", "19:00-21:00"],
                    "peak_engagement": "Wednesday 15:00 - 16:00"
                }
            },
            "content_preferences": {
                "formats": ["Video", "Images", "Stories", "Carousel"],
                "languages": ["English", "Local language"],
                "tone": "Friendly and professional"
            },
            "hashtag_recommendations": [
                "#SMESuccess", "#LocalBusiness", "#DigitalTransformation",
                "#AfricanEntrepreneurs", "#BusinessGrowth"
            ]
        }
        
        # Update state with trend analysis
        state.data["trend_analysis"] = trend_insights
        state.context["trend_analysis_timestamp"] = datetime.now().isoformat()
        
        return state


class AudienceSegmentationNode(BaseNode):
    """
    Segments target audience based on demographics, behavior, and preferences.
    
    This node creates detailed audience segments for personalized
    campaign targeting and messaging.
    """
    
    def __init__(self, config: Optional[NodeConfig] = None):
        """Initialize AudienceSegmentationNode with configuration."""
        if config is None:
            config = NodeConfig(
                name="audience_segmentation",
                description="Segments target audience based on demographics and behavior",
                region_specific=True,
                supported_regions=["NG", "KE", "ZA", "GH", "UG", "TZ"]
            )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Execute audience segmentation analysis.
        
        Args:
            state: Current workflow state
            
        Returns:
            Audience segmentation results and targeting recommendations
        """
        # Reason: Mock implementation for Phase 1 - will be replaced with ML-powered segmentation
        target_audience = state.data.get("target_audience", "")
        campaign_objectives = state.data.get("campaign_objectives", [])
        
        # Mock audience segmentation
        audience_segments = {
            "primary_segments": [
                {
                    "segment_id": "young_professionals",
                    "name": "Young Urban Professionals",
                    "size": "35% of target audience",
                    "characteristics": {
                        "age_range": "25-35",
                        "income": "₦150,000 - ₦500,000/month",
                        "interests": ["Technology", "Career growth", "Lifestyle"],
                        "digital_behavior": "High social media usage, mobile-first"
                    },
                    "messaging_strategy": "Focus on career advancement and efficiency"
                },
                {
                    "segment_id": "small_business_owners",
                    "name": "SME Owners & Entrepreneurs",
                    "size": "40% of target audience", 
                    "characteristics": {
                        "age_range": "30-50",
                        "income": "₦200,000 - ₦1,000,000/month",
                        "interests": ["Business growth", "Innovation", "Networking"],
                        "digital_behavior": "Professional networks, business content"
                    },
                    "messaging_strategy": "Emphasize business growth and ROI"
                },
                {
                    "segment_id": "tech_early_adopters",
                    "name": "Technology Early Adopters",
                    "size": "25% of target audience",
                    "characteristics": {
                        "age_range": "20-40",
                        "income": "₦100,000 - ₦800,000/month",
                        "interests": ["Technology", "Innovation", "Digital tools"],
                        "digital_behavior": "Heavy app usage, online communities"
                    },
                    "messaging_strategy": "Highlight innovation and cutting-edge features"
                }
            ],
            "targeting_recommendations": {
                "primary_channels": ["Facebook", "Instagram", "LinkedIn", "WhatsApp Business"],
                "content_mix": {
                    "educational": "40%",
                    "promotional": "30%",
                    "engaging": "30%"
                },
                "budget_allocation": {
                    "young_professionals": "35%",
                    "small_business_owners": "45%",
                    "tech_early_adopters": "20%"
                }
            }
        }
        
        # Update state with segmentation results
        state.data["audience_segmentation"] = audience_segments
        state.context["segmentation_timestamp"] = datetime.now().isoformat()
        
        return state


class CampaignStrategyNode(BaseNode):
    """
    Develops comprehensive campaign strategy based on research and analysis.
    
    This node creates detailed campaign plans, messaging frameworks,
    and execution roadmaps.
    """
    
    def __init__(self, config: Optional[NodeConfig] = None):
        """Initialize CampaignStrategyNode with configuration."""
        if config is None:
            config = NodeConfig(
                name="campaign_strategy",
                description="Develops comprehensive campaign strategy based on research and analysis"
            )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Develop campaign strategy and execution plan.
        
        Args:
            state: Current workflow state
            
        Returns:
            Campaign strategy and execution roadmap
        """
        # Reason: Combines insights from previous nodes to create actionable strategy
        market_research = state.data.get("market_research", {})
        trend_analysis = state.data.get("trend_analysis", {})
        audience_segments = state.data.get("audience_segmentation", {})
        campaign_budget = state.data.get("campaign_budget", "₦1,000,000")
        
        # Develop comprehensive strategy
        campaign_strategy = {
            "strategy_overview": {
                "campaign_theme": "Empowering African SMEs through Digital Innovation",
                "key_messaging": [
                    "Transform your business with cutting-edge solutions",
                    "Join thousands of successful African entrepreneurs",
                    "Grow faster with local expertise and global standards"
                ],
                "unique_value_proposition": "The only platform built specifically for African SME needs"
            },
            "execution_phases": [
                {
                    "phase": "Awareness Building",
                    "duration": "Weeks 1-2",
                    "objectives": ["Brand awareness", "Audience education"],
                    "tactics": ["Social media content", "Influencer partnerships", "PR outreach"]
                },
                {
                    "phase": "Engagement & Interest",
                    "duration": "Weeks 3-4", 
                    "objectives": ["Lead generation", "Community building"],
                    "tactics": ["Interactive content", "Webinars", "Free trials"]
                },
                {
                    "phase": "Conversion & Retention",
                    "duration": "Weeks 5-8",
                    "objectives": ["Sales conversion", "Customer retention"],
                    "tactics": ["Targeted offers", "Success stories", "Referral programs"]
                }
            ],
            "channel_strategy": {
                "facebook": {
                    "budget_allocation": "30%",
                    "content_focus": "Community building and engagement",
                    "posting_frequency": "2-3 times daily"
                },
                "instagram": {
                    "budget_allocation": "25%",
                    "content_focus": "Visual storytelling and behind-the-scenes",
                    "posting_frequency": "1-2 times daily"
                },
                "linkedin": {
                    "budget_allocation": "20%",
                    "content_focus": "Professional insights and thought leadership",
                    "posting_frequency": "1 time daily"
                },
                "whatsapp_business": {
                    "budget_allocation": "15%",
                    "content_focus": "Direct customer support and updates",
                    "posting_frequency": "As needed"
                },
                "google_ads": {
                    "budget_allocation": "10%",
                    "content_focus": "Search and display advertising",
                    "posting_frequency": "Continuous"
                }
            },
            "success_metrics": {
                "awareness": ["Reach", "Impressions", "Brand mentions"],
                "engagement": ["Likes", "Comments", "Shares", "Click-through rate"],
                "conversion": ["Leads generated", "Sign-ups", "Sales", "ROI"]
            }
        }
        
        # Update state with strategy
        state.data["campaign_strategy"] = campaign_strategy
        state.context["strategy_created"] = datetime.now().isoformat()
        
        return state


class ContentPlanningNode(BaseNode):
    """
    Creates detailed content calendar and creative briefs.
    
    This node generates content schedules, creative guidelines,
    and asset requirements for campaign execution.
    """
    
    def __init__(self, config: Optional[NodeConfig] = None):
        """Initialize ContentPlanningNode with configuration."""
        if config is None:
            config = NodeConfig(
                name="content_planning",
                description="Creates detailed content calendar and creative briefs"
            )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Create comprehensive content plan and calendar.
        
        Args:
            state: Current workflow state
            
        Returns:
            Content calendar and creative guidelines
        """
        # Reason: Translates strategy into actionable content plans
        campaign_strategy = state.data.get("campaign_strategy", {})
        campaign_duration = state.data.get("campaign_duration", "1 month")
        preferred_channels = state.data.get("preferred_channels", [])
        
        # Create content calendar
        content_plan = {
            "content_calendar": {
                "week_1": {
                    "theme": "Introduction & Awareness",
                    "content_pieces": [
                        {
                            "day": "Monday",
                            "platform": "Facebook",
                            "content_type": "Video",
                            "title": "Meet the SMEFlow Team",
                            "description": "Behind-the-scenes introduction video"
                        },
                        {
                            "day": "Wednesday", 
                            "platform": "Instagram",
                            "content_type": "Carousel",
                            "title": "5 Ways SMEFlow Transforms Businesses",
                            "description": "Educational carousel post"
                        },
                        {
                            "day": "Friday",
                            "platform": "LinkedIn",
                            "content_type": "Article",
                            "title": "The Future of African SMEs",
                            "description": "Thought leadership article"
                        }
                    ]
                },
                "week_2": {
                    "theme": "Features & Benefits",
                    "content_pieces": [
                        {
                            "day": "Monday",
                            "platform": "Facebook",
                            "content_type": "Live Video",
                            "title": "Product Demo Session",
                            "description": "Live demonstration of key features"
                        },
                        {
                            "day": "Wednesday",
                            "platform": "Instagram",
                            "content_type": "Stories",
                            "title": "Customer Success Highlights",
                            "description": "Success story series"
                        }
                    ]
                }
            },
            "creative_guidelines": {
                "brand_colors": ["#1E40AF", "#10B981", "#F59E0B"],
                "typography": "Modern, clean, professional",
                "imagery_style": "Authentic African business scenes",
                "tone_of_voice": "Friendly, professional, empowering",
                "key_messages": [
                    "Empowering African entrepreneurs",
                    "Built for local needs",
                    "Proven results"
                ]
            },
            "asset_requirements": {
                "videos": ["Product demos", "Customer testimonials", "Behind-the-scenes"],
                "images": ["Product screenshots", "Team photos", "Customer success"],
                "graphics": ["Infographics", "Quote cards", "Statistics"]
            }
        }
        
        # Update state with content plan
        state.data["content_plan"] = content_plan
        state.context["content_plan_created"] = datetime.now().isoformat()
        
        return state


class BudgetAllocationNode(BaseNode):
    """
    Optimizes budget allocation across channels and campaign phases.
    
    This node distributes campaign budget for maximum ROI based on
    audience segments and channel performance predictions.
    """
    
    def __init__(self, config: Optional[NodeConfig] = None):
        """Initialize BudgetAllocationNode with configuration."""
        if config is None:
            config = NodeConfig(
                name="budget_allocation",
                description="Optimizes budget allocation across channels and campaign phases"
            )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Optimize budget allocation across channels and phases.
        
        Args:
            state: Current workflow state
            
        Returns:
            Optimized budget allocation plan
        """
        # Reason: Mock optimization for Phase 1 - will be replaced with ML-powered optimization
        campaign_budget_str = state.data.get("campaign_budget", "₦1,000,000")
        # Extract numeric value from budget string
        budget_amount = 1000000  # Default fallback
        
        audience_segments = state.data.get("audience_segmentation", {})
        preferred_channels = state.data.get("preferred_channels", [])
        
        # Mock budget optimization
        budget_allocation = {
            "total_budget": budget_amount,
            "allocation_strategy": "Performance-based with equal testing",
            "channel_allocation": {
                "facebook": {
                    "amount": budget_amount * 0.30,
                    "percentage": "30%",
                    "rationale": "Largest audience reach and engagement"
                },
                "instagram": {
                    "amount": budget_amount * 0.25,
                    "percentage": "25%", 
                    "rationale": "High visual engagement for younger demographics"
                },
                "linkedin": {
                    "amount": budget_amount * 0.20,
                    "percentage": "20%",
                    "rationale": "Professional audience with higher conversion rates"
                },
                "google_ads": {
                    "amount": budget_amount * 0.15,
                    "percentage": "15%",
                    "rationale": "Intent-based targeting for qualified leads"
                },
                "whatsapp_business": {
                    "amount": budget_amount * 0.10,
                    "percentage": "10%",
                    "rationale": "Direct communication and customer support"
                }
            },
            "phase_allocation": {
                "awareness": {
                    "amount": budget_amount * 0.40,
                    "percentage": "40%",
                    "focus": "Reach and brand awareness"
                },
                "engagement": {
                    "amount": budget_amount * 0.35,
                    "percentage": "35%",
                    "focus": "Lead generation and nurturing"
                },
                "conversion": {
                    "amount": budget_amount * 0.25,
                    "percentage": "25%",
                    "focus": "Sales and retention"
                }
            },
            "contingency_fund": {
                "amount": budget_amount * 0.10,
                "percentage": "10%",
                "purpose": "Performance optimization and unexpected opportunities"
            }
        }
        
        # Update state with budget allocation
        state.data["budget_allocation"] = budget_allocation
        state.context["budget_optimized"] = datetime.now().isoformat()
        
        return state


class CampaignSetupNode(BaseNode):
    """
    Sets up campaign channels and tracking infrastructure.
    
    This node configures social media campaigns, tracking pixels,
    and analytics dashboards for campaign execution.
    """
    
    def __init__(self, config: Optional[NodeConfig] = None):
        """Initialize CampaignSetupNode with configuration."""
        if config is None:
            config = NodeConfig(
                name="campaign_setup",
                description="Sets up campaign channels and tracking infrastructure"
            )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Setup campaign channels and tracking infrastructure.
        
        Args:
            state: Current workflow state
            
        Returns:
            Campaign setup status and tracking configuration
        """
        # Reason: Mock setup for Phase 1 - will integrate with actual social media APIs
        preferred_channels = state.data.get("preferred_channels", [])
        budget_allocation = state.data.get("budget_allocation", {})
        
        # Mock campaign setup
        setup_results = {
            "campaign_ids": {
                channel: f"camp_{uuid.uuid4().hex[:8]}"
                for channel in preferred_channels
            },
            "tracking_setup": {
                "google_analytics": {
                    "property_id": "GA4-XXXXXXXXX",
                    "conversion_goals": ["Sign-up", "Demo Request", "Purchase"],
                    "status": "configured"
                },
                "facebook_pixel": {
                    "pixel_id": "FB_PIXEL_123456789",
                    "events": ["PageView", "Lead", "Purchase"],
                    "status": "active"
                },
                "utm_parameters": {
                    "source": "smeflow_campaign",
                    "medium": "social",
                    "campaign": "marketing_campaigns_2024"
                }
            },
            "channel_configurations": {
                channel: {
                    "campaign_id": f"camp_{uuid.uuid4().hex[:8]}",
                    "budget_daily": budget_allocation.get("channel_allocation", {}).get(channel.lower(), {}).get("amount", 0) / 30,
                    "targeting": "Configured based on audience segments",
                    "status": "ready_to_launch"
                }
                for channel in preferred_channels
            },
            "dashboard_links": {
                "campaign_dashboard": "https://dashboard.smeflow.com/campaigns/marketing",
                "analytics_dashboard": "https://analytics.smeflow.com/marketing-campaigns",
                "reporting_dashboard": "https://reports.smeflow.com/campaign-performance"
            }
        }
        
        # Update state with setup results
        state.data["campaign_setup"] = setup_results
        state.context["setup_completed"] = datetime.now().isoformat()
        
        return state


class PerformanceTrackingNode(BaseNode):
    """
    Monitors campaign performance and generates real-time insights.
    
    This node tracks KPIs, identifies optimization opportunities,
    and provides performance alerts.
    """
    
    def __init__(self, config: Optional[NodeConfig] = None):
        """Initialize PerformanceTrackingNode with configuration."""
        if config is None:
            config = NodeConfig(
                name="performance_tracking",
                description="Monitors campaign performance and generates real-time insights"
            )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Monitor campaign performance and generate insights.
        
        Args:
            state: Current workflow state
            
        Returns:
            Performance metrics and optimization recommendations
        """
        # Reason: Mock tracking for Phase 1 - will integrate with real analytics APIs
        campaign_setup = state.data.get("campaign_setup", {})
        
        # Mock performance data
        performance_metrics = {
            "overall_performance": {
                "impressions": 125000,
                "reach": 85000,
                "clicks": 3200,
                "ctr": "2.56%",
                "cost_per_click": "₦45.50",
                "conversions": 156,
                "conversion_rate": "4.88%",
                "cost_per_conversion": "₦298.00"
            },
            "channel_performance": {
                "facebook": {
                    "impressions": 45000,
                    "clicks": 1200,
                    "ctr": "2.67%",
                    "conversions": 58,
                    "roas": "3.2x"
                },
                "instagram": {
                    "impressions": 38000,
                    "clicks": 980,
                    "ctr": "2.58%",
                    "conversions": 42,
                    "roas": "2.8x"
                },
                "linkedin": {
                    "impressions": 22000,
                    "clicks": 650,
                    "ctr": "2.95%",
                    "conversions": 35,
                    "roas": "4.1x"
                }
            },
            "audience_insights": {
                "top_performing_segments": ["Small business owners", "Young professionals"],
                "engagement_patterns": {
                    "peak_hours": ["9:00-11:00", "15:00-17:00", "19:00-21:00"],
                    "best_days": ["Tuesday", "Wednesday", "Thursday"]
                }
            },
            "optimization_alerts": [
                {
                    "type": "opportunity",
                    "message": "LinkedIn showing 40% higher conversion rate - consider budget reallocation",
                    "priority": "high"
                },
                {
                    "type": "warning",
                    "message": "Instagram CTR below target - review creative assets",
                    "priority": "medium"
                }
            ]
        }
        
        # Update state with performance data
        state.data["performance_metrics"] = performance_metrics
        state.context["last_performance_update"] = datetime.now().isoformat()
        
        return state


class OptimizationNode(BaseNode):
    """
    Optimizes campaign performance based on real-time data.
    
    This node implements A/B tests, adjusts targeting, and
    reallocates budget for improved performance.
    """
    
    def __init__(self, config: Optional[NodeConfig] = None):
        """Initialize OptimizationNode with configuration."""
        if config is None:
            config = NodeConfig(
                name="optimization",
                description="Optimizes campaign performance based on real-time data"
            )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Optimize campaign performance based on data insights.
        
        Args:
            state: Current workflow state
            
        Returns:
            Optimization actions and performance improvements
        """
        # Reason: Mock optimization for Phase 1 - will use ML for real-time optimization
        performance_metrics = state.data.get("performance_metrics", {})
        
        # Mock optimization actions
        optimization_actions = {
            "budget_reallocation": {
                "action": "Increase LinkedIn budget by 25%, decrease Instagram by 15%",
                "rationale": "LinkedIn showing 40% higher conversion rate",
                "expected_impact": "15-20% improvement in overall ROAS"
            },
            "creative_optimization": {
                "action": "Test new video creative for Instagram",
                "rationale": "Current Instagram CTR below target",
                "test_duration": "7 days",
                "success_criteria": "CTR > 2.8%"
            },
            "audience_refinement": {
                "action": "Expand 'Small business owners' segment targeting",
                "rationale": "Highest performing audience segment",
                "expected_impact": "10-15% increase in qualified leads"
            },
            "timing_optimization": {
                "action": "Increase ad frequency during peak hours (15:00-17:00)",
                "rationale": "40% higher engagement during these hours",
                "implementation": "Dayparting adjustment"
            }
        }
        
        # Performance improvements
        optimization_results = {
            "implemented_changes": [
                "Budget reallocation completed",
                "New creative assets uploaded",
                "Audience targeting expanded",
                "Dayparting schedule updated"
            ],
            "performance_impact": {
                "ctr_improvement": "+0.3%",
                "conversion_rate_improvement": "+1.2%",
                "cost_per_conversion_reduction": "-12%",
                "overall_roas_improvement": "+18%"
            },
            "next_optimization_cycle": (datetime.now() + timedelta(days=3)).isoformat()
        }
        
        # Update state with optimization results
        state.data["optimization_actions"] = optimization_actions
        state.data["optimization_results"] = optimization_results
        state.context["last_optimization"] = datetime.now().isoformat()
        
        return state


class ReportingNode(BaseNode):
    """
    Generates comprehensive campaign performance reports.
    
    This node creates detailed analytics reports, insights summaries,
    and actionable recommendations for stakeholders.
    """
    
    def __init__(self, config: Optional[NodeConfig] = None):
        """Initialize ReportingNode with configuration."""
        if config is None:
            config = NodeConfig(
                name="reporting",
                description="Generates comprehensive campaign performance reports"
            )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Generate comprehensive campaign performance report.
        
        Args:
            state: Current workflow state
            
        Returns:
            Detailed performance report and recommendations
        """
        # Reason: Consolidates all campaign data into actionable business intelligence
        performance_metrics = state.data.get("performance_metrics", {})
        optimization_results = state.data.get("optimization_results", {})
        campaign_strategy = state.data.get("campaign_strategy", {})
        
        # Generate comprehensive report
        campaign_report = {
            "executive_summary": {
                "campaign_performance": "Exceeding expectations with 18% ROAS improvement",
                "key_achievements": [
                    "156 conversions generated (25% above target)",
                    "₦298 cost per conversion (15% below target)",
                    "3.2x average ROAS across all channels"
                ],
                "total_investment": state.data.get("campaign_budget", "₦1,000,000"),
                "total_return": "₦3,200,000",
                "net_roi": "220%"
            },
            "detailed_metrics": {
                "reach_and_awareness": {
                    "total_reach": "85,000 unique users",
                    "impressions": "125,000",
                    "brand_awareness_lift": "+35%"
                },
                "engagement_metrics": {
                    "total_clicks": "3,200",
                    "average_ctr": "2.56%",
                    "engagement_rate": "4.2%",
                    "social_shares": "450"
                },
                "conversion_metrics": {
                    "total_conversions": "156",
                    "conversion_rate": "4.88%",
                    "qualified_leads": "89",
                    "sales_generated": "₦2,100,000"
                }
            },
            "channel_analysis": performance_metrics.get("channel_performance", {}),
            "audience_insights": {
                "best_performing_segments": ["Small business owners (45% of conversions)", "Young professionals (32% of conversions)"],
                "geographic_performance": "Lagos and Nairobi showing highest engagement",
                "demographic_breakdown": "25-35 age group driving 60% of conversions"
            },
            "optimization_impact": optimization_results.get("performance_impact", {}),
            "recommendations": {
                "immediate_actions": [
                    "Continue increased investment in LinkedIn advertising",
                    "Expand successful creative formats to other channels",
                    "Increase targeting of small business owner segment"
                ],
                "strategic_recommendations": [
                    "Develop dedicated landing pages for top-performing segments",
                    "Create region-specific content for Lagos and Nairobi markets",
                    "Implement retargeting campaigns for engaged users"
                ],
                "budget_recommendations": {
                    "next_period_budget": "₦1,500,000 (50% increase based on performance)",
                    "allocation_changes": "Increase LinkedIn to 35%, maintain Facebook at 30%"
                }
            },
            "next_steps": {
                "short_term": ["Implement A/B tests for new creative concepts", "Set up retargeting campaigns"],
                "medium_term": ["Expand to additional African markets", "Develop video content strategy"],
                "long_term": ["Build comprehensive customer journey mapping", "Implement advanced attribution modeling"]
            }
        }
        
        # Update state with final report
        state.data["campaign_report"] = campaign_report
        state.context["report_generated"] = datetime.now().isoformat()
        state.status = "completed"
        
        return state
