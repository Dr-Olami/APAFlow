"""
Tenant-Specific Social Media Configuration for SMEFlow Multi-Tenancy.

This module demonstrates how different businesses can configure their own
social media preferences while maintaining complete tenant isolation.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, Field

from ..workflows.state import WorkflowState
from ..workflows.nodes import BaseNode, NodeConfig


class TenantSocialMediaConfig(BaseModel):
    """
    Tenant-specific social media configuration model.
    
    Each tenant can customize their social media strategy, brand guidelines,
    and platform preferences independently.
    """
    tenant_id: str = Field(..., description="Unique tenant identifier")
    business_name: str = Field(..., description="Business name for branding")
    industry: str = Field(..., description="Business industry category")
    target_regions: List[str] = Field(default=["NG"], description="Target African regions")
    
    # Brand Guidelines (Tenant-Specific)
    brand_colors: Dict[str, str] = Field(
        default={
            "primary": "#1E40AF",
            "secondary": "#10B981", 
            "accent": "#F59E0B"
        },
        description="Tenant's brand color palette"
    )
    
    brand_voice: Dict[str, Any] = Field(
        default={
            "tone": "professional_friendly",
            "personality": ["innovative", "trustworthy", "empowering"],
            "avoid_terms": [],
            "preferred_terms": []
        },
        description="Tenant's brand voice and messaging"
    )
    
    # Platform Preferences (Tenant-Specific)
    active_platforms: List[str] = Field(
        default=["facebook", "instagram", "linkedin"],
        description="Social media platforms tenant wants to use"
    )
    
    platform_priorities: Dict[str, int] = Field(
        default={
            "facebook": 1,
            "instagram": 2, 
            "linkedin": 3,
            "twitter": 4,
            "tiktok": 5
        },
        description="Platform priority ranking (1=highest)"
    )
    
    posting_frequency: Dict[str, str] = Field(
        default={
            "facebook": "daily",
            "instagram": "daily",
            "linkedin": "3x_weekly",
            "twitter": "2x_daily",
            "tiktok": "3x_weekly"
        },
        description="Desired posting frequency per platform"
    )
    
    # Content Preferences (Tenant-Specific)
    content_mix: Dict[str, int] = Field(
        default={
            "educational": 40,
            "promotional": 30,
            "engaging": 20,
            "brand_story": 10
        },
        description="Content type distribution percentages"
    )
    
    languages: List[str] = Field(
        default=["en"],
        description="Preferred languages for content"
    )
    
    cultural_context: Dict[str, Any] = Field(
        default={
            "local_references": True,
            "cultural_sensitivity": True,
            "regional_holidays": True
        },
        description="Cultural adaptation preferences"
    )
    
    # AI Generation Preferences (Tenant-Specific)
    ai_preferences: Dict[str, Any] = Field(
        default={
            "image_style": "professional_authentic",
            "video_style": "engaging_educational",
            "budget_limit": 200,  # USD per month
            "quality_level": "high"
        },
        description="AI content generation preferences"
    )
    
    # Analytics & Reporting (Tenant-Specific)
    kpi_priorities: List[str] = Field(
        default=["engagement_rate", "reach", "conversions", "follower_growth"],
        description="Key performance indicators to track"
    )
    
    reporting_frequency: str = Field(
        default="weekly",
        description="Analytics reporting frequency"
    )
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class TenantConfigurationNode(BaseNode):
    """
    Manages tenant-specific social media configurations.
    
    This node handles loading, validating, and applying tenant-specific
    preferences to social media workflows while ensuring complete isolation.
    """
    
    def __init__(self, config: Optional[NodeConfig] = None):
        """Initialize TenantConfigurationNode with multi-tenant support."""
        if config is None:
            config = NodeConfig(
                name="tenant_social_config",
                description="Manages tenant-specific social media configurations",
                tenant_isolated=True  # Ensures tenant isolation
            )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Load and apply tenant-specific social media configuration.
        
        Args:
            state: Current workflow state with tenant context
            
        Returns:
            Updated state with tenant-specific configurations applied
        """
        # Extract tenant context from workflow state
        tenant_id = state.tenant_id  # Tenant isolation enforced at state level
        
        # Load tenant-specific configuration
        # In production, this would query the database with tenant isolation
        try:
            tenant_config = await self._load_tenant_config(tenant_id)
        except Exception as e:
            # Handle validation errors or database issues
            return self._apply_default_configuration(state)
        
        # Handle case where no tenant config is found or validation fails
        if tenant_config is None:
            # Return default configuration
            return self._apply_default_configuration(state)
        
        # Apply tenant-specific brand guidelines
        tenant_brand_guidelines = {
            "visual_identity": {
                "primary_colors": tenant_config.brand_colors,
                "typography": self._get_tenant_typography(tenant_config),
                "logo_usage": self._get_tenant_logo_specs(tenant_config),
                "imagery_style": self._get_tenant_imagery_style(tenant_config)
            },
            "voice_and_tone": {
                "brand_personality": tenant_config.brand_voice["personality"],
                "tone_attributes": self._get_tone_attributes(tenant_config),
                "language_guidelines": {
                    "preferred_terms": tenant_config.brand_voice["preferred_terms"],
                    "avoid_terms": tenant_config.brand_voice["avoid_terms"],
                    "cultural_sensitivity": tenant_config.cultural_context
                }
            },
            "platform_adaptations": self._get_platform_adaptations(tenant_config)
        }
        
        # Apply tenant-specific platform preferences
        platform_preferences = {
            "active_platforms": tenant_config.active_platforms,
            "platform_priorities": tenant_config.platform_priorities,
            "posting_schedule": self._generate_posting_schedule(tenant_config),
            "content_distribution": tenant_config.content_mix
        }
        
        # Apply tenant-specific AI generation settings
        ai_generation_config = {
            "style_preferences": tenant_config.ai_preferences,
            "budget_constraints": {
                "monthly_limit": tenant_config.ai_preferences["budget_limit"],
                "cost_per_asset_limits": self._get_cost_limits(tenant_config)
            },
            "quality_settings": {
                "image_resolution": self._get_image_resolution(tenant_config),
                "video_quality": self._get_video_quality(tenant_config)
            }
        }
        
        # Return updated workflow state with tenant configurations
        state.data.update({
            "tenant_brand_guidelines": tenant_brand_guidelines,
            "tenant_platform_preferences": platform_preferences,
            "tenant_ai_config": ai_generation_config,
            "tenant_languages": tenant_config.languages,
            "tenant_regions": tenant_config.target_regions
        })
        
        # Add tenant context for all subsequent nodes
        state.context["tenant_configured"] = True
        state.context["tenant_industry"] = tenant_config.industry
        state.context["configuration_timestamp"] = datetime.now().isoformat()
        
        return state
    
    def _apply_default_configuration(self, state: WorkflowState) -> WorkflowState:
        """Apply default configuration when tenant config is not available."""
        default_ai_config = {
            "budget_constraints": {
                "monthly_limit": 100,
                "cost_per_asset_limits": {
                    "image_generation": 5.0,
                    "video_generation": 15.0,
                    "graphic_design": 10.0
                }
            },
            "quality_settings": {
                "image_resolution": "1024x1024",
                "video_quality": "720p"
            }
        }
        
        state.data.update({
            "tenant_ai_config": default_ai_config,
            "tenant_brand_guidelines": {},
            "tenant_platform_preferences": {},
            "tenant_languages": ["en"],
            "tenant_regions": ["US"]
        })
        
        return state
    
    async def _load_tenant_config(self, tenant_id: str) -> TenantSocialMediaConfig:
        """
        Load tenant configuration with database isolation.
        
        In production, this would use tenant-scoped database queries.
        """
        # Mock tenant configurations for demonstration
        tenant_configs = {
            "tenant_lagos_restaurant": TenantSocialMediaConfig(
                tenant_id="tenant_lagos_restaurant",
                business_name="Mama's Kitchen Lagos",
                industry="Restaurant",
                target_regions=["NG"],
                brand_colors={
                    "primary": "#FF6B35",  # Warm orange
                    "secondary": "#F7931E", # Golden yellow
                    "accent": "#2E8B57"     # Sea green
                },
                brand_voice={
                    "tone": "warm_family_friendly",
                    "personality": ["welcoming", "authentic", "community-focused"],
                    "preferred_terms": ["family", "home-cooked", "traditional", "fresh"],
                    "avoid_terms": ["fast food", "processed", "artificial"]
                },
                active_platforms=["facebook", "instagram", "whatsapp"],
                languages=["en", "yo", "ig"],  # English, Yoruba, Igbo
                content_mix={
                    "food_photos": 50,
                    "behind_scenes": 20,
                    "customer_stories": 20,
                    "promotions": 10
                }
            ),
            "tenant_nairobi_fintech": TenantSocialMediaConfig(
                tenant_id="tenant_nairobi_fintech",
                business_name="KenyaPay Solutions",
                industry="FinTech",
                target_regions=["KE", "UG", "TZ"],
                brand_colors={
                    "primary": "#1E3A8A",   # Professional blue
                    "secondary": "#059669", # Trust green
                    "accent": "#DC2626"     # Alert red
                },
                brand_voice={
                    "tone": "professional_trustworthy",
                    "personality": ["secure", "innovative", "reliable"],
                    "preferred_terms": ["secure", "trusted", "innovative", "empowering"],
                    "avoid_terms": ["risky", "experimental", "untested"]
                },
                active_platforms=["linkedin", "twitter", "facebook"],
                languages=["en", "sw"],  # English, Swahili
                content_mix={
                    "educational": 60,
                    "product_updates": 25,
                    "industry_news": 10,
                    "company_culture": 5
                }
            ),
            "tenant_capetown_fashion": TenantSocialMediaConfig(
                tenant_id="tenant_capetown_fashion",
                business_name="Ubuntu Fashion House",
                industry="Fashion",
                target_regions=["ZA"],
                brand_colors={
                    "primary": "#8B5CF6",   # Creative purple
                    "secondary": "#EC4899", # Vibrant pink
                    "accent": "#F59E0B"     # Golden accent
                },
                brand_voice={
                    "tone": "creative_inspiring",
                    "personality": ["artistic", "bold", "culturally-proud"],
                    "preferred_terms": ["authentic", "heritage", "artistic", "unique"],
                    "avoid_terms": ["mass-produced", "generic", "copied"]
                },
                active_platforms=["instagram", "tiktok", "facebook", "pinterest"],
                languages=["en", "af", "zu"],  # English, Afrikaans, Zulu
                content_mix={
                    "product_showcase": 40,
                    "styling_tips": 30,
                    "behind_scenes": 20,
                    "cultural_stories": 10
                }
            )
        }
        
        # Return tenant-specific config or default
        return tenant_configs.get(tenant_id, TenantSocialMediaConfig(tenant_id=tenant_id))
    
    def _get_tenant_typography(self, config: TenantSocialMediaConfig) -> Dict[str, str]:
        """Get typography settings based on tenant industry."""
        typography_by_industry = {
            "Restaurant": {
                "primary_font": "Playfair Display, serif",
                "secondary_font": "Open Sans, sans-serif",
                "style": "elegant, readable"
            },
            "FinTech": {
                "primary_font": "Inter, system-ui, sans-serif", 
                "secondary_font": "Roboto, Arial, sans-serif",
                "style": "clean, professional"
            },
            "Fashion": {
                "primary_font": "Montserrat, sans-serif",
                "secondary_font": "Lato, sans-serif", 
                "style": "modern, stylish"
            }
        }
        return typography_by_industry.get(config.industry, typography_by_industry["FinTech"])
    
    def _get_tenant_logo_specs(self, config: TenantSocialMediaConfig) -> Dict[str, Any]:
        """Get logo specifications for tenant."""
        return {
            "minimum_size": "32px",
            "clear_space": "1x logo height",
            "backgrounds": ["white", "dark", config.brand_colors["primary"]],
            "formats": ["PNG", "SVG", "JPG"]
        }
    
    def _get_tenant_imagery_style(self, config: TenantSocialMediaConfig) -> Dict[str, str]:
        """Get imagery style based on tenant preferences."""
        styles_by_industry = {
            "Restaurant": {
                "photography": "Warm, appetizing food photography",
                "illustration": "Hand-drawn, artisanal style",
                "color_treatment": "Warm, inviting tones"
            },
            "FinTech": {
                "photography": "Professional, diverse business scenes",
                "illustration": "Clean, modern infographics",
                "color_treatment": "Professional, trustworthy"
            },
            "Fashion": {
                "photography": "Artistic, culturally-rich fashion photography",
                "illustration": "Bold, creative graphics",
                "color_treatment": "Vibrant, artistic"
            }
        }
        return styles_by_industry.get(config.industry, styles_by_industry["FinTech"])
    
    def _get_tone_attributes(self, config: TenantSocialMediaConfig) -> Dict[str, str]:
        """Get tone attributes based on tenant voice preferences."""
        return {
            "formal_level": config.brand_voice["tone"],
            "energy_level": "Confident and optimistic",
            "emotional_tone": "Supportive and encouraging"
        }
    
    def _get_platform_adaptations(self, config: TenantSocialMediaConfig) -> Dict[str, Dict[str, str]]:
        """Get platform-specific adaptations for tenant."""
        base_adaptations = {}
        
        for platform in config.active_platforms:
            base_adaptations[platform] = {
                "tone_adjustment": self._get_platform_tone(platform, config),
                "content_focus": self._get_platform_focus(platform, config),
                "posting_frequency": config.posting_frequency.get(platform, "daily")
            }
        
        return base_adaptations
    
    def _get_platform_tone(self, platform: str, config: TenantSocialMediaConfig) -> str:
        """Get platform-specific tone adjustment."""
        industry_tones = {
            "Restaurant": {
                "facebook": "Community-focused, family-friendly",
                "instagram": "Visual storytelling, appetizing",
                "whatsapp": "Personal, direct communication"
            },
            "FinTech": {
                "linkedin": "Professional insights, thought leadership",
                "twitter": "Industry news, quick updates",
                "facebook": "Educational, community-building"
            },
            "Fashion": {
                "instagram": "Artistic, trend-setting",
                "tiktok": "Creative, trend-aware",
                "facebook": "Community, style inspiration"
            }
        }
        
        return industry_tones.get(config.industry, {}).get(platform, "Professional and engaging")
    
    def _get_platform_focus(self, platform: str, config: TenantSocialMediaConfig) -> str:
        """Get platform-specific content focus."""
        return f"{config.industry}-specific content optimized for {platform}"
    
    def _generate_posting_schedule(self, config: TenantSocialMediaConfig) -> Dict[str, Any]:
        """Generate tenant-specific posting schedule."""
        return {
            "timezone": "Local business timezone",
            "frequency": config.posting_frequency,
            "optimal_times": self._get_optimal_times_for_industry(config.industry),
            "content_rotation": config.content_mix
        }
    
    def _get_optimal_times_for_industry(self, industry: str) -> List[str]:
        """Get optimal posting times based on industry."""
        industry_times = {
            "Restaurant": ["11:00", "17:00", "19:00"],  # Meal times
            "FinTech": ["9:00", "12:00", "17:00"],      # Business hours
            "Fashion": ["10:00", "15:00", "20:00"]      # Lifestyle times
        }
        return industry_times.get(industry, ["9:00", "15:00", "19:00"])
    
    def _get_cost_limits(self, config: TenantSocialMediaConfig) -> Dict[str, float]:
        """Get cost limits based on tenant budget."""
        monthly_budget = config.ai_preferences["budget_limit"]
        return {
            "image_generation": monthly_budget * 0.4,  # 40% for images
            "video_generation": monthly_budget * 0.5,  # 50% for videos
            "graphic_design": monthly_budget * 0.1     # 10% for graphics
        }
    
    def _get_image_resolution(self, config: TenantSocialMediaConfig) -> str:
        """Get image resolution based on quality preferences."""
        quality_map = {
            "high": "1024x1024",
            "medium": "512x512", 
            "low": "256x256"
        }
        return quality_map.get(config.ai_preferences["quality_level"], "1024x1024")
    
    def _get_video_quality(self, config: TenantSocialMediaConfig) -> str:
        """Get video quality based on preferences."""
        quality_map = {
            "high": "1080p",
            "medium": "720p",
            "low": "480p"
        }
        return quality_map.get(config.ai_preferences["quality_level"], "1080p")


# Example usage demonstrating tenant isolation
async def demonstrate_tenant_isolation():
    """
    Demonstrate how different tenants get isolated configurations.
    """
    
    # Tenant 1: Lagos Restaurant
    restaurant_state = WorkflowState(
        workflow_id=str(uuid.uuid4()),
        tenant_id="tenant_lagos_restaurant",
        data={},
        context={}
    )
    
    # Tenant 2: Nairobi FinTech  
    fintech_state = WorkflowState(
        workflow_id=str(uuid.uuid4()),
        tenant_id="tenant_nairobi_fintech", 
        data={},
        context={}
    )
    
    # Tenant 3: Cape Town Fashion
    fashion_state = WorkflowState(
        workflow_id=str(uuid.uuid4()),
        tenant_id="tenant_capetown_fashion",
        data={},
        context={}
    )
    
    # Each tenant gets completely isolated configuration
    config_node = TenantConfigurationNode()
    
    # Process each tenant independently
    restaurant_configured = await config_node._execute_logic(restaurant_state)
    fintech_configured = await config_node._execute_logic(fintech_state)
    fashion_configured = await config_node._execute_logic(fashion_state)
    
    # Results are completely isolated per tenant
    print("Restaurant brand colors:", restaurant_configured.data["tenant_brand_guidelines"]["visual_identity"]["primary_colors"])
    print("FinTech brand colors:", fintech_configured.data["tenant_brand_guidelines"]["visual_identity"]["primary_colors"])
    print("Fashion brand colors:", fashion_configured.data["tenant_brand_guidelines"]["visual_identity"]["primary_colors"])
    
    return {
        "restaurant": restaurant_configured,
        "fintech": fintech_configured,
        "fashion": fashion_configured
    }
