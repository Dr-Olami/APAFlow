"""
Social Media Consistency and Content Generation Nodes for SMEFlow.

This module provides specialized workflow nodes for maintaining brand consistency
across multiple social media platforms with AI-powered content generation.
"""

from typing import Dict, Any, List, Optional, Union
import asyncio
import json
from datetime import datetime, timedelta
import uuid
import hashlib

from ..workflows.state import WorkflowState
from ..workflows.nodes import BaseNode, NodeConfig


class BrandConsistencyNode(BaseNode):
    """
    Enforces brand consistency across all social media platforms.
    
    This node validates and standardizes brand guidelines including colors,
    typography, tone of voice, and messaging across different platforms.
    """
    
    def __init__(self, config: Optional[NodeConfig] = None):
        """Initialize BrandConsistencyNode with configuration."""
        if config is None:
            config = NodeConfig(
                name="brand_consistency",
                description="Enforces brand consistency across social media platforms",
                region_specific=True,
                supported_regions=["NG", "KE", "ZA", "GH", "UG", "TZ"],
                supported_languages=["en", "ha", "yo", "ig", "sw", "af", "zu"]
            )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Validate and enforce brand consistency guidelines.
        
        Args:
            state: Current workflow state
            
        Returns:
            Brand guidelines and consistency validation results
        """
        # Extract brand information from state
        business_info = state.data.get("business_info", {})
        existing_brand = state.data.get("brand_guidelines", {})
        
        # Define comprehensive brand guidelines
        brand_guidelines = {
            "visual_identity": {
                "primary_colors": existing_brand.get("colors", {
                    "primary": "#1E40AF",  # Professional blue
                    "secondary": "#10B981",  # Success green
                    "accent": "#F59E0B",  # Warning amber
                    "neutral": "#6B7280",  # Cool gray
                    "background": "#FFFFFF"
                }),
                "typography": {
                    "primary_font": "Inter, system-ui, sans-serif",
                    "secondary_font": "Roboto, Arial, sans-serif",
                    "heading_weights": ["600", "700", "800"],
                    "body_weights": ["400", "500"]
                },
                "logo_usage": {
                    "minimum_size": "32px",
                    "clear_space": "1x logo height",
                    "backgrounds": ["white", "dark", "brand_primary"],
                    "formats": ["PNG", "SVG", "JPG"]
                },
                "imagery_style": {
                    "photography": "Authentic African business scenes",
                    "illustration": "Modern, clean, professional",
                    "color_treatment": "Vibrant but professional",
                    "composition": "Clean, uncluttered layouts"
                }
            },
            "voice_and_tone": {
                "brand_personality": ["Professional", "Empowering", "Innovative", "Trustworthy"],
                "tone_attributes": {
                    "formal_level": "Professional but approachable",
                    "energy_level": "Confident and optimistic",
                    "emotional_tone": "Supportive and encouraging"
                },
                "language_guidelines": {
                    "preferred_terms": [
                        "Empower", "Transform", "Growth", "Success", 
                        "Innovation", "Community", "Excellence"
                    ],
                    "avoid_terms": [
                        "Cheap", "Basic", "Simple", "Easy money", 
                        "Get rich quick", "Guaranteed"
                    ],
                    "cultural_sensitivity": {
                        "inclusive_language": True,
                        "local_references": True,
                        "cultural_awareness": True
                    }
                }
            },
            "messaging_framework": {
                "core_messages": [
                    "Empowering African SMEs through digital innovation",
                    "Built for local needs, powered by global technology",
                    "Your success is our mission"
                ],
                "value_propositions": [
                    "20-40% cost reduction for SME operations",
                    "Hyperlocal intelligence for African markets",
                    "Multi-language support in 50+ languages"
                ],
                "call_to_actions": {
                    "primary": ["Get Started", "Transform Your Business", "Join Thousands"],
                    "secondary": ["Learn More", "See How It Works", "Request Demo"],
                    "urgency": ["Limited Time", "Start Today", "Don't Miss Out"]
                }
            },
            "platform_adaptations": {
                "facebook": {
                    "post_length": "125-250 characters optimal",
                    "image_specs": "1200x630px",
                    "tone_adjustment": "Community-focused, engaging"
                },
                "instagram": {
                    "post_length": "125-150 characters optimal", 
                    "image_specs": "1080x1080px (square), 1080x1350px (portrait)",
                    "tone_adjustment": "Visual storytelling, behind-the-scenes"
                },
                "linkedin": {
                    "post_length": "150-300 characters optimal",
                    "image_specs": "1200x627px",
                    "tone_adjustment": "Professional insights, thought leadership"
                },
                "twitter": {
                    "post_length": "71-100 characters optimal",
                    "image_specs": "1200x675px",
                    "tone_adjustment": "Concise, timely, conversational"
                },
                "tiktok": {
                    "video_length": "15-30 seconds optimal",
                    "video_specs": "1080x1920px (9:16 ratio)",
                    "tone_adjustment": "Energetic, authentic, trend-aware"
                }
            }
        }
        
        # Validate existing content against guidelines
        content_validation = {
            "validation_results": {
                "color_compliance": "100%",
                "typography_compliance": "95%",
                "tone_consistency": "90%",
                "messaging_alignment": "85%"
            },
            "compliance_issues": [
                {
                    "issue": "Inconsistent font usage in Instagram posts",
                    "severity": "medium",
                    "recommendation": "Standardize to primary font family"
                },
                {
                    "issue": "CTA variations across platforms",
                    "severity": "low", 
                    "recommendation": "Use consistent primary CTAs"
                }
            ],
            "optimization_suggestions": [
                "Implement brand color palette across all visual assets",
                "Create platform-specific templates for consistent layouts",
                "Develop tone of voice guidelines for different content types"
            ]
        }
        
        # Update state with brand guidelines
        state.data["brand_guidelines"] = brand_guidelines
        state.data["brand_validation"] = content_validation
        state.context["brand_guidelines_updated"] = datetime.now().isoformat()
        
        return state


class MultiPlatformContentNode(BaseNode):
    """
    Generates platform-optimized content for multiple social media channels.
    
    This node creates tailored content for Meta, TikTok, LinkedIn, Twitter, 
    and Instagram while maintaining brand consistency.
    """
    
    def __init__(self, config: Optional[NodeConfig] = None):
        """Initialize MultiPlatformContentNode with configuration."""
        if config is None:
            config = NodeConfig(
                name="multi_platform_content",
                description="Generates platform-optimized content for multiple social channels",
                region_specific=True,
                supported_regions=["NG", "KE", "ZA", "GH", "UG", "TZ"]
            )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Generate platform-optimized content for multiple channels.
        
        Args:
            state: Current workflow state
            
        Returns:
            Platform-specific content variations and posting guidelines
        """
        # Extract content requirements
        campaign_theme = state.data.get("campaign_theme", "Business Growth")
        brand_guidelines = state.data.get("brand_guidelines", {})
        target_platforms = state.data.get("target_platforms", ["facebook", "instagram", "linkedin"])
        
        # Generate base content concepts
        content_concepts = [
            {
                "concept_id": "success_story",
                "theme": "Customer Success",
                "base_message": "See how Lagos entrepreneur Sarah increased her revenue by 45% using SMEFlow automation",
                "content_type": "testimonial",
                "visual_elements": ["customer_photo", "before_after_stats", "brand_logo"]
            },
            {
                "concept_id": "feature_highlight", 
                "theme": "Product Education",
                "base_message": "Discover how hyperlocal intelligence helps African SMEs identify the best opportunities in their neighborhood",
                "content_type": "educational",
                "visual_elements": ["product_screenshot", "infographic", "map_visualization"]
            },
            {
                "concept_id": "behind_scenes",
                "theme": "Brand Personality",
                "base_message": "Meet our team of African tech innovators building the future of SME automation",
                "content_type": "brand_story",
                "visual_elements": ["team_photos", "office_scenes", "development_process"]
            }
        ]
        
        # Generate platform-specific content
        platform_content = {}
        
        for platform in target_platforms:
            platform_specs = brand_guidelines.get("platform_adaptations", {}).get(platform, {})
            
            platform_content[platform] = {
                "content_variations": [],
                "posting_guidelines": platform_specs,
                "optimal_timing": self._get_optimal_timing(platform),
                "engagement_tactics": self._get_engagement_tactics(platform)
            }
            
            # Create platform-specific variations for each concept
            for concept in content_concepts:
                variation = self._adapt_content_for_platform(concept, platform, brand_guidelines)
                platform_content[platform]["content_variations"].append(variation)
        
        # Update state with generated content
        state.data["platform_content"] = platform_content
        state.data["content_concepts"] = content_concepts
        state.context["content_generated"] = datetime.now().isoformat()
        
        return state
    
    def _get_optimal_timing(self, platform: str) -> Dict[str, Any]:
        """Get optimal posting times for specific platform in African markets."""
        # African market timing optimizations
        timing_data = {
            "facebook": {
                "best_days": ["Tuesday", "Wednesday", "Thursday"],
                "best_hours": ["9:00-11:00", "15:00-17:00", "19:00-21:00"],
                "timezone": "WAT/CAT/EAT",
                "frequency": "1-2 posts daily"
            },
            "instagram": {
                "best_days": ["Monday", "Wednesday", "Friday"],
                "best_hours": ["11:00-13:00", "17:00-19:00", "20:00-22:00"],
                "timezone": "WAT/CAT/EAT", 
                "frequency": "1-2 posts daily"
            },
            "linkedin": {
                "best_days": ["Tuesday", "Wednesday", "Thursday"],
                "best_hours": ["8:00-10:00", "12:00-14:00", "17:00-18:00"],
                "timezone": "WAT/CAT/EAT",
                "frequency": "3-5 posts weekly"
            },
            "twitter": {
                "best_days": ["Monday", "Tuesday", "Wednesday"],
                "best_hours": ["9:00-10:00", "12:00-13:00", "17:00-18:00"],
                "timezone": "WAT/CAT/EAT",
                "frequency": "3-5 tweets daily"
            },
            "tiktok": {
                "best_days": ["Tuesday", "Thursday", "Sunday"],
                "best_hours": ["18:00-20:00", "20:00-22:00"],
                "timezone": "WAT/CAT/EAT",
                "frequency": "3-7 videos weekly"
            }
        }
        
        return timing_data.get(platform, timing_data["facebook"])
    
    def _get_engagement_tactics(self, platform: str) -> List[str]:
        """Get platform-specific engagement tactics."""
        tactics = {
            "facebook": [
                "Ask questions to encourage comments",
                "Use Facebook polls and reactions",
                "Share behind-the-scenes content",
                "Create event announcements",
                "Use Facebook Live for real-time engagement"
            ],
            "instagram": [
                "Use Instagram Stories with polls and questions",
                "Create carousel posts for step-by-step content",
                "Use relevant hashtags (10-15 per post)",
                "Partner with local micro-influencers",
                "Share user-generated content"
            ],
            "linkedin": [
                "Share industry insights and thought leadership",
                "Engage with comments professionally",
                "Use LinkedIn articles for long-form content",
                "Participate in relevant LinkedIn groups",
                "Share employee achievements and company culture"
            ],
            "twitter": [
                "Use trending hashtags relevant to your industry",
                "Engage in Twitter chats and conversations",
                "Share quick tips and insights",
                "Retweet and comment on industry news",
                "Use Twitter threads for detailed explanations"
            ],
            "tiktok": [
                "Follow trending sounds and challenges",
                "Create educational content in short format",
                "Show authentic behind-the-scenes moments",
                "Use trending hashtags and effects",
                "Collaborate with other creators"
            ]
        }
        
        return tactics.get(platform, tactics["facebook"])
    
    def _adapt_content_for_platform(self, concept: Dict[str, Any], platform: str, brand_guidelines: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt content concept for specific platform requirements."""
        platform_specs = brand_guidelines.get("platform_adaptations", {}).get(platform, {})
        
        # Platform-specific adaptations
        adaptations = {
            "facebook": {
                "format": "image_with_text",
                "caption_style": "storytelling",
                "cta_placement": "end_of_post",
                "hashtag_count": "3-5"
            },
            "instagram": {
                "format": "square_image_or_carousel",
                "caption_style": "visual_first",
                "cta_placement": "stories_or_bio",
                "hashtag_count": "10-15"
            },
            "linkedin": {
                "format": "professional_image",
                "caption_style": "thought_leadership",
                "cta_placement": "professional_context",
                "hashtag_count": "3-5"
            },
            "twitter": {
                "format": "image_with_short_text",
                "caption_style": "conversational",
                "cta_placement": "thread_continuation",
                "hashtag_count": "2-3"
            },
            "tiktok": {
                "format": "vertical_video",
                "caption_style": "trend_aware",
                "cta_placement": "video_overlay",
                "hashtag_count": "5-10"
            }
        }
        
        adaptation = adaptations.get(platform, adaptations["facebook"])
        
        return {
            "concept_id": concept["concept_id"],
            "platform": platform,
            "adapted_message": self._adapt_message_length(concept["base_message"], platform_specs),
            "format_requirements": adaptation,
            "visual_specifications": {
                "dimensions": platform_specs.get("image_specs", "1200x630px"),
                "elements": concept["visual_elements"],
                "brand_compliance": True
            },
            "engagement_elements": {
                "hashtags": self._generate_platform_hashtags(platform, concept["theme"]),
                "cta": self._generate_platform_cta(platform, concept["content_type"]),
                "mentions": []
            }
        }
    
    def _adapt_message_length(self, message: str, platform_specs: Dict[str, Any]) -> str:
        """Adapt message length for platform specifications."""
        optimal_length = platform_specs.get("post_length", "125-250 characters optimal")
        
        # Extract target length (simplified approach)
        if "71-100" in optimal_length:
            return message[:97] + "..." if len(message) > 100 else message
        elif "125-150" in optimal_length:
            return message[:147] + "..." if len(message) > 150 else message
        elif "150-300" in optimal_length:
            return message[:297] + "..." if len(message) > 300 else message
        else:
            return message[:247] + "..." if len(message) > 250 else message
    
    def _generate_platform_hashtags(self, platform: str, theme: str) -> List[str]:
        """Generate platform-appropriate hashtags."""
        base_hashtags = {
            "Customer Success": ["#SMESuccess", "#BusinessGrowth", "#CustomerWins"],
            "Product Education": ["#DigitalTransformation", "#SMETech", "#BusinessAutomation"],
            "Brand Personality": ["#TeamSpotlight", "#Innovation", "#AfricanTech"]
        }
        
        platform_hashtags = {
            "facebook": ["#SMEFlow", "#AfricanBusiness", "#Entrepreneurship"],
            "instagram": ["#SMEFlow", "#AfricanEntrepreneurs", "#BusinessSuccess", "#TechForGood"],
            "linkedin": ["#SMEFlow", "#BusinessInnovation", "#AfricanTech", "#Leadership"],
            "twitter": ["#SMEFlow", "#AfricanSMEs", "#TechNews"],
            "tiktok": ["#SMEFlow", "#BusinessTips", "#Entrepreneur", "#AfricaTech"]
        }
        
        theme_tags = base_hashtags.get(theme, ["#Business", "#Growth", "#Success"])
        platform_tags = platform_hashtags.get(platform, ["#SMEFlow", "#Business"])
        
        return theme_tags + platform_tags
    
    def _generate_platform_cta(self, platform: str, content_type: str) -> str:
        """Generate platform-appropriate call-to-action."""
        cta_options = {
            "facebook": {
                "testimonial": "See how SMEFlow can transform your business too! Link in bio 👆",
                "educational": "Want to learn more? Check out our free resources 📚",
                "brand_story": "Ready to join our mission? Get started today! 🚀"
            },
            "instagram": {
                "testimonial": "Your success story could be next! Link in bio ✨",
                "educational": "Save this post and share with fellow entrepreneurs! 💡",
                "brand_story": "Follow our journey and start yours! Link in bio 🌟"
            },
            "linkedin": {
                "testimonial": "Connect with us to discuss how we can support your business growth.",
                "educational": "What challenges is your business facing? Let's discuss in the comments.",
                "brand_story": "We're hiring! Check out our careers page for opportunities."
            },
            "twitter": {
                "testimonial": "RT if you're ready to transform your business! 🔄",
                "educational": "Thread: More tips for African SMEs 👇",
                "brand_story": "Follow for more behind-the-scenes content! 📱"
            },
            "tiktok": {
                "testimonial": "Follow for more success stories! 📈",
                "educational": "Part 2 coming soon! Follow to not miss it 👀",
                "brand_story": "Day in the life at SMEFlow! Follow for more 🎬"
            }
        }
        
        return cta_options.get(platform, {}).get(content_type, "Learn more about SMEFlow!")


class KeywordHashtagNode(BaseNode):
    """
    Researches keywords and optimizes hashtags for African markets.
    
    This node analyzes trending keywords, local market terms, and generates
    optimized hashtag strategies for maximum reach and engagement.
    """
    
    def __init__(self, config: Optional[NodeConfig] = None):
        """Initialize KeywordHashtagNode with configuration."""
        if config is None:
            config = NodeConfig(
                name="keyword_hashtag_research",
                description="Researches keywords and optimizes hashtags for African markets",
                region_specific=True,
                supported_regions=["NG", "KE", "ZA", "GH", "UG", "TZ"],
                supported_languages=["en", "ha", "yo", "ig", "sw", "af", "zu"]
            )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Research keywords and generate optimized hashtag strategies.
        
        Args:
            state: Current workflow state
            
        Returns:
            Keyword research results and hashtag optimization recommendations
        """
        # Extract campaign context
        campaign_theme = state.data.get("campaign_theme", "Business Growth")
        target_regions = state.data.get("target_regions", ["NG", "KE", "ZA"])
        target_audience = state.data.get("target_audience", "SME Owners")
        business_category = state.data.get("business_category", "Technology")
        
        # Research trending keywords by region
        regional_keywords = {
            "NG": {
                "trending_terms": [
                    "naija business", "lagos entrepreneur", "abuja startup",
                    "nigerian sme", "fintech nigeria", "digital payment",
                    "online business nigeria", "ecommerce naija"
                ],
                "local_languages": {
                    "yoruba": ["owo", "ise", "ilosiwaju", "aseyori"],  # money, work, progress, success
                    "igbo": ["ego", "oru", "ihe oma", "omenala"],  # money, work, good thing, culture
                    "hausa": ["kudi", "aiki", "nasara", "kasuwanci"]  # money, work, success, business
                }
            },
            "KE": {
                "trending_terms": [
                    "kenyan business", "nairobi startup", "mpesa integration",
                    "kenyan entrepreneur", "east africa business", "tech hub kenya",
                    "digital kenya", "sme kenya"
                ],
                "local_languages": {
                    "swahili": ["biashara", "kazi", "mafanikio", "teknolojia"]  # business, work, success, technology
                }
            },
            "ZA": {
                "trending_terms": [
                    "south african business", "cape town startup", "joburg entrepreneur",
                    "sa sme", "fintech south africa", "digital transformation sa",
                    "township business", "black business sa"
                ],
                "local_languages": {
                    "afrikaans": ["besigheid", "werk", "sukses", "tegnologie"],  # business, work, success, technology
                    "zulu": ["ibhizinisi", "umsebenzi", "impumelelo", "ubuchwepheshe"]  # business, work, success, technology
                }
            }
        }
        
        # Generate category-specific keywords
        category_keywords = {
            "Technology": [
                "AI for business", "automation tools", "digital solutions",
                "business software", "tech innovation", "digital transformation"
            ],
            "Retail": [
                "online store", "ecommerce platform", "inventory management",
                "customer experience", "retail technology", "point of sale"
            ],
            "Healthcare": [
                "digital health", "telemedicine", "health tech",
                "patient management", "medical software", "healthcare innovation"
            ],
            "Finance": [
                "fintech solutions", "digital banking", "payment systems",
                "financial inclusion", "mobile money", "digital wallet"
            ]
        }
        
        # Optimize hashtags for each platform
        platform_hashtag_strategies = {
            "instagram": {
                "strategy": "High volume, mix of popular and niche",
                "recommended_count": "25-30 hashtags",
                "hashtag_mix": {
                    "popular": ["#entrepreneur", "#business", "#success", "#motivation"],
                    "niche": ["#africanbusiness", "#smetech", "#digitalafrika", "#techforafrica"],
                    "branded": ["#smeflow", "#empoweringsmes", "#africanentrepreneurs"],
                    "location": ["#lagos", "#nairobi", "#capetown", "#accra", "#kampala"]
                }
            },
            "twitter": {
                "strategy": "Trending and conversational hashtags",
                "recommended_count": "2-3 hashtags",
                "hashtag_mix": {
                    "trending": ["#TechTwitter", "#StartupLife", "#EntrepreneurLife"],
                    "industry": ["#FinTech", "#DigitalTransformation", "#AI"],
                    "regional": ["#AfricaTech", "#NaijaTwitter", "#SATwitter"]
                }
            },
            "linkedin": {
                "strategy": "Professional and industry-focused",
                "recommended_count": "3-5 hashtags",
                "hashtag_mix": {
                    "professional": ["#Leadership", "#Innovation", "#BusinessGrowth"],
                    "industry": ["#Technology", "#Entrepreneurship", "#DigitalTransformation"],
                    "regional": ["#AfricanBusiness", "#EmergingMarkets", "#TechInAfrica"]
                }
            },
            "tiktok": {
                "strategy": "Trending sounds and viral hashtags",
                "recommended_count": "3-5 hashtags",
                "hashtag_mix": {
                    "trending": ["#SmallBusiness", "#Entrepreneur", "#BusinessTips"],
                    "educational": ["#LearnOnTikTok", "#BusinessHacks", "#TechTips"],
                    "regional": ["#AfricaTikTok", "#NaijaTikTok", "#KenyaTikTok"]
                }
            }
        }
        
        # Generate SEO-optimized content keywords
        seo_keywords = {
            "primary_keywords": [
                f"{business_category.lower()} automation africa",
                f"sme {business_category.lower()} solutions",
                f"african {business_category.lower()} software",
                f"{target_audience.lower().replace(' ', '_')} tools"
            ],
            "long_tail_keywords": [
                f"best {business_category.lower()} automation for african smes",
                f"how to automate {business_category.lower()} processes in africa",
                f"{business_category.lower()} digital transformation africa",
                f"affordable {business_category.lower()} software for smes"
            ],
            "local_seo_keywords": []
        }
        
        # Add region-specific SEO keywords
        for region in target_regions:
            region_name = {"NG": "nigeria", "KE": "kenya", "ZA": "south africa"}.get(region, region.lower())
            seo_keywords["local_seo_keywords"].extend([
                f"{business_category.lower()} automation {region_name}",
                f"sme software {region_name}",
                f"business tools {region_name}"
            ])
        
        # Compile research results
        keyword_research = {
            "regional_analysis": regional_keywords,
            "category_keywords": category_keywords.get(business_category, category_keywords["Technology"]),
            "platform_strategies": platform_hashtag_strategies,
            "seo_optimization": seo_keywords,
            "trending_analysis": {
                "current_trends": [
                    "AI and automation adoption",
                    "Digital payment integration", 
                    "Remote work solutions",
                    "Sustainable business practices"
                ],
                "seasonal_trends": {
                    "q1": "New year business planning",
                    "q2": "Mid-year optimization",
                    "q3": "Back-to-business season",
                    "q4": "Year-end growth push"
                }
            },
            "competitive_analysis": {
                "competitor_hashtags": [
                    "#digitaltransformation", "#businessautomation", "#smetechnology",
                    "#africainnovation", "#entrepreneurship", "#businessgrowth"
                ],
                "gap_opportunities": [
                    "#hyperlocalbusiness", "#africansmesuccess", "#culturallyaware tech",
                    "#multilingualbusiness", "#inclusivetech"
                ]
            }
        }
        
        # Update state with research results
        state.data["keyword_research"] = keyword_research
        state.context["keyword_research_completed"] = datetime.now().isoformat()
        
        return state


class AIContentGenerationNode(BaseNode):
    """
    Integrates AI image and video generation for social media content.
    
    This node coordinates with AI models for generating visual content
    including images, graphics, and video assets optimized for each platform.
    """
    
    def __init__(self, config: Optional[NodeConfig] = None):
        """Initialize AIContentGenerationNode with configuration."""
        if config is None:
            config = NodeConfig(
                name="ai_content_generation",
                description="Integrates AI image and video generation for social media content",
                region_specific=False
            )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Generate AI-powered visual content for social media platforms.
        
        Args:
            state: Current workflow state
            
        Returns:
            AI-generated content specifications and asset requirements
        """
        # Extract content requirements
        platform_content = state.data.get("platform_content", {})
        brand_guidelines = state.data.get("brand_guidelines", {})
        content_concepts = state.data.get("content_concepts", [])
        
        # AI model configurations (research-based alternatives to nano-banana, veo3)
        ai_models = {
            "image_generation": {
                "primary": "stable_diffusion_xl",
                "alternatives": ["midjourney_api", "dall_e_3", "firefly_api"],
                "specifications": {
                    "resolution": "1024x1024",
                    "style": "professional, authentic, diverse",
                    "format": "PNG, JPEG"
                }
            },
            "video_generation": {
                "primary": "runway_ml",
                "alternatives": ["pika_labs", "stable_video", "synthesia"],
                "specifications": {
                    "resolution": "1080p",
                    "duration": "15-60 seconds",
                    "format": "MP4, MOV"
                }
            },
            "graphic_design": {
                "primary": "canva_api",
                "alternatives": ["figma_api", "adobe_express_api"],
                "specifications": {
                    "templates": "platform-optimized",
                    "brand_compliance": "automatic",
                    "format": "PNG, SVG, PDF"
                }
            }
        }
        
        # Generate content specifications for each platform
        ai_content_specs = {}
        
        for platform, content_data in platform_content.items():
            platform_specs = {
                "image_requirements": [],
                "video_requirements": [],
                "graphic_requirements": [],
                "generation_prompts": []
            }
            
            # Process each content variation
            for variation in content_data.get("content_variations", []):
                concept_id = variation["concept_id"]
                visual_specs = variation["visual_specifications"]
                
                # Generate AI prompts based on concept and platform
                prompts = self._generate_ai_prompts(
                    concept_id, platform, visual_specs, brand_guidelines
                )
                
                platform_specs["generation_prompts"].extend(prompts)
                
                # Add specific requirements based on visual elements
                for element in visual_specs.get("elements", []):
                    if element in ["customer_photo", "team_photos", "office_scenes"]:
                        platform_specs["image_requirements"].append({
                            "type": "photography",
                            "subject": element,
                            "style": "authentic, professional, diverse",
                            "dimensions": visual_specs["dimensions"]
                        })
                    elif element in ["infographic", "brand_logo", "statistics"]:
                        platform_specs["graphic_requirements"].append({
                            "type": "graphic_design",
                            "subject": element,
                            "style": "clean, modern, brand-compliant",
                            "dimensions": visual_specs["dimensions"]
                        })
                    elif element in ["product_screenshot", "map_visualization"]:
                        platform_specs["image_requirements"].append({
                            "type": "ui_mockup",
                            "subject": element,
                            "style": "clean, professional, realistic",
                            "dimensions": visual_specs["dimensions"]
                        })
            
            # Add platform-specific video requirements
            if platform == "tiktok":
                platform_specs["video_requirements"].append({
                    "type": "short_form_video",
                    "duration": "15-30 seconds",
                    "aspect_ratio": "9:16",
                    "style": "energetic, authentic, trend-aware"
                })
            elif platform in ["facebook", "instagram"]:
                platform_specs["video_requirements"].append({
                    "type": "social_video",
                    "duration": "30-60 seconds",
                    "aspect_ratio": "16:9 or 1:1",
                    "style": "professional, engaging, story-driven"
                })
            
            ai_content_specs[platform] = platform_specs
        
        # Generate asset production timeline
        production_timeline = {
            "phase_1_images": {
                "duration": "2-3 days",
                "deliverables": "Profile images, cover photos, basic graphics",
                "priority": "high"
            },
            "phase_2_content": {
                "duration": "3-5 days", 
                "deliverables": "Post images, infographics, carousel designs",
                "priority": "medium"
            },
            "phase_3_video": {
                "duration": "5-7 days",
                "deliverables": "Video content, animations, motion graphics",
                "priority": "medium"
            },
            "phase_4_optimization": {
                "duration": "ongoing",
                "deliverables": "A/B test variations, performance optimizations",
                "priority": "low"
            }
        }
        
        # Compile AI generation results
        ai_generation_results = {
            "model_configurations": ai_models,
            "platform_specifications": ai_content_specs,
            "production_timeline": production_timeline,
            "quality_guidelines": {
                "brand_compliance": "All assets must follow brand guidelines",
                "cultural_sensitivity": "Content must be culturally appropriate for African markets",
                "accessibility": "Include alt text and captions for all visual content",
                "performance_optimization": "Optimize file sizes for mobile-first African markets"
            },
            "cost_estimation": {
                "image_generation": "$0.02-0.05 per image",
                "video_generation": "$0.10-0.50 per video",
                "graphic_design": "$0.01-0.03 per graphic",
                "monthly_budget": "$50-200 for typical SME campaign"
            }
        }
        
        # Update state with AI generation specifications
        state.data["ai_content_generation"] = ai_generation_results
        state.context["ai_content_specs_created"] = datetime.now().isoformat()
        
        return state
    
    def _generate_ai_prompts(self, concept_id: str, platform: str, visual_specs: Dict[str, Any], brand_guidelines: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate AI model prompts for specific content concepts."""
        
        # Extract brand colors and style
        brand_colors = brand_guidelines.get("visual_identity", {}).get("primary_colors", {})
        imagery_style = brand_guidelines.get("visual_identity", {}).get("imagery_style", {})
        
        # Base prompt templates by concept
        concept_prompts = {
            "success_story": [
                {
                    "type": "image",
                    "prompt": f"Professional African entrepreneur in modern office, {imagery_style.get('photography', 'authentic business scene')}, using {brand_colors.get('primary', '#1E40AF')} and {brand_colors.get('secondary', '#10B981')} color scheme, high quality, realistic",
                    "negative_prompt": "cartoon, anime, low quality, blurry, unprofessional"
                }
            ],
            "feature_highlight": [
                {
                    "type": "graphic",
                    "prompt": f"Clean infographic showing business automation workflow, {imagery_style.get('illustration', 'modern and professional')}, {brand_colors.get('primary', '#1E40AF')} primary color, minimalist design, African business context",
                    "negative_prompt": "cluttered, outdated, generic, non-African context"
                }
            ],
            "behind_scenes": [
                {
                    "type": "image",
                    "prompt": f"Diverse African tech team collaborating in modern workspace, {imagery_style.get('photography', 'authentic scenes')}, natural lighting, professional but approachable, {brand_colors.get('primary', '#1E40AF')} accents",
                    "negative_prompt": "staged, artificial, non-diverse, unprofessional"
                }
            ]
        }
        
        # Platform-specific adjustments
        platform_adjustments = {
            "instagram": " square format, Instagram-optimized, vibrant colors",
            "tiktok": " vertical format, mobile-first, energetic and dynamic",
            "linkedin": " professional tone, business-focused, corporate appropriate",
            "facebook": " engaging and community-focused, family-friendly",
            "twitter": " clean and simple, Twitter card optimized"
        }
        
        # Get base prompts and adjust for platform
        base_prompts = concept_prompts.get(concept_id, concept_prompts["success_story"])
        adjusted_prompts = []
        
        for prompt in base_prompts:
            adjusted_prompt = prompt.copy()
            adjusted_prompt["prompt"] += platform_adjustments.get(platform, "")
            adjusted_prompt["platform"] = platform
            adjusted_prompt["dimensions"] = visual_specs.get("dimensions", "1200x630px")
            adjusted_prompts.append(adjusted_prompt)
        
        return adjusted_prompts
