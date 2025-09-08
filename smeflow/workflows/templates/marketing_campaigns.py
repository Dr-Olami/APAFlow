"""
Marketing campaigns workflow templates.

This module contains workflow templates for marketing campaign management and automation.
"""

from .base import IndustryType, FormFieldType, FormField, IndustryTemplate


def create_marketing_campaigns_template() -> IndustryTemplate:
    """Create marketing campaigns template for hyperlocal marketing automation."""
    return IndustryTemplate(
        industry=IndustryType.MARKETING_CAMPAIGNS,
        name="Marketing Campaign Automation",
        description="Comprehensive marketing campaign workflow with hyperlocal targeting and African market optimizations",
        
        booking_form_fields=[
            FormField(
                name="business_name",
                label="Business Name",
                field_type=FormFieldType.TEXT,
                required=True,
                placeholder="Enter your business name"
            ),
            FormField(
                name="industry_sector",
                label="Industry Sector",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "Retail/E-commerce", "Food & Beverage", "Fashion & Beauty",
                    "Health & Wellness", "Technology", "Education", "Real Estate",
                    "Financial Services", "Entertainment", "Professional Services"
                ]
            ),
            FormField(
                name="target_audience",
                label="Target Audience",
                field_type=FormFieldType.MULTISELECT,
                required=True,
                options=[
                    "Young Adults (18-25)", "Professionals (26-40)", "Middle-aged (41-55)",
                    "Seniors (55+)", "Students", "Parents", "Business Owners", "Tech-savvy Users"
                ]
            ),
            FormField(
                name="campaign_objectives",
                label="Campaign Objectives",
                field_type=FormFieldType.MULTISELECT,
                required=True,
                options=[
                    "Brand Awareness", "Lead Generation", "Sales Conversion",
                    "Customer Retention", "Product Launch", "Event Promotion",
                    "Website Traffic", "Social Media Engagement"
                ]
            ),
            FormField(
                name="target_locations",
                label="Target Locations",
                field_type=FormFieldType.MULTISELECT,
                required=True,
                options=[
                    "Lagos, Nigeria", "Abuja, Nigeria", "Kano, Nigeria", "Port Harcourt, Nigeria",
                    "Cape Town, South Africa", "Johannesburg, South Africa", "Durban, South Africa",
                    "Nairobi, Kenya", "Mombasa, Kenya", "Accra, Ghana", "Kumasi, Ghana"
                ]
            ),
            FormField(
                name="campaign_channels",
                label="Marketing Channels",
                field_type=FormFieldType.MULTISELECT,
                required=True,
                options=[
                    "Social Media (Facebook, Instagram)", "WhatsApp Business",
                    "Google Ads", "Email Marketing", "SMS Marketing",
                    "Radio Advertising", "Local Print Media", "Influencer Marketing"
                ]
            ),
            FormField(
                name="campaign_budget",
                label="Monthly Campaign Budget",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "₦50,000 - ₦100,000", "₦100,000 - ₦250,000",
                    "₦250,000 - ₦500,000", "₦500,000 - ₦1,000,000", "₦1,000,000+"
                ]
            ),
            FormField(
                name="campaign_duration",
                label="Campaign Duration",
                field_type=FormFieldType.SELECT,
                required=True,
                options=["1 month", "3 months", "6 months", "12 months", "Ongoing"]
            ),
            FormField(
                name="preferred_languages",
                label="Preferred Languages",
                field_type=FormFieldType.MULTISELECT,
                required=True,
                options=["English", "Hausa", "Yoruba", "Igbo", "Swahili", "Afrikaans", "French"]
            ),
            FormField(
                name="success_metrics",
                label="Success Metrics",
                field_type=FormFieldType.MULTISELECT,
                required=True,
                options=[
                    "Click-through Rate", "Conversion Rate", "Cost per Acquisition",
                    "Return on Ad Spend", "Brand Mentions", "Social Media Followers",
                    "Website Visitors", "Lead Quality Score"
                ]
            )
        ],
        
        confirmation_fields=[
            FormField(
                name="marketing_contact",
                label="Marketing Contact Email",
                field_type=FormFieldType.EMAIL,
                required=True,
                placeholder="Enter marketing team contact email"
            ),
            FormField(
                name="campaign_start_date",
                label="Preferred Campaign Start Date",
                field_type=FormFieldType.DATE,
                required=True
            ),
            FormField(
                name="reporting_frequency",
                label="Reporting Frequency",
                field_type=FormFieldType.SELECT,
                required=True,
                options=["Daily", "Weekly", "Bi-weekly", "Monthly"]
            )
        ],
        
        workflow_nodes=[
            {"name": "start", "type": "start"},
            {"name": "market_research", "type": "agent", "config": {"task": "conduct_hyperlocal_market_research"}},
            {"name": "audience_segmentation", "type": "agent", "config": {"task": "segment_target_audience"}},
            {"name": "campaign_strategy", "type": "agent", "config": {"task": "develop_campaign_strategy"}},
            {"name": "content_creation", "type": "agent", "config": {"task": "create_marketing_content"}},
            {"name": "channel_setup", "type": "agent", "config": {"task": "setup_marketing_channels"}},
            {"name": "campaign_launch", "type": "agent", "config": {"task": "launch_marketing_campaign"}},
            {"name": "performance_monitoring", "type": "agent", "config": {"task": "monitor_campaign_performance"}},
            {"name": "optimization", "type": "agent", "config": {"task": "optimize_campaign_performance"}},
            {"name": "reporting", "type": "agent", "config": {"task": "generate_campaign_reports"}},
            {"name": "roi_analysis", "type": "agent", "config": {"task": "analyze_campaign_roi"}},
            {"name": "end", "type": "end"}
        ],
        
        workflow_edges=[
            {"from": "start", "to": "market_research"},
            {"from": "market_research", "to": "audience_segmentation"},
            {"from": "audience_segmentation", "to": "campaign_strategy"},
            {"from": "campaign_strategy", "to": "content_creation"},
            {"from": "content_creation", "to": "channel_setup"},
            {"from": "channel_setup", "to": "campaign_launch"},
            {"from": "campaign_launch", "to": "performance_monitoring"},
            {"from": "performance_monitoring", "to": "optimization"},
            {"from": "optimization", "to": "reporting"},
            {"from": "reporting", "to": "roi_analysis"},
            {"from": "roi_analysis", "to": "end"}
        ],
        
        business_hours={
            "timezone": "Africa/Lagos",
            "monday": {"start": "08:00", "end": "18:00"},
            "tuesday": {"start": "08:00", "end": "18:00"},
            "wednesday": {"start": "08:00", "end": "18:00"},
            "thursday": {"start": "08:00", "end": "18:00"},
            "friday": {"start": "08:00", "end": "18:00"},
            "saturday": {"start": "09:00", "end": "14:00"},
            "sunday": {"closed": True}
        },
        
        advance_booking_days=7,
        cancellation_policy="Marketing campaign changes require 48 hours advance notice. Campaign optimization can be done in real-time.",
        
        notification_settings={
            "email_notifications": True,
            "sms_notifications": True,
            "whatsapp_notifications": True,
            "campaign_alerts": True,
            "performance_reports": True,
            "optimization_suggestions": True
        },
        
        required_integrations=["social_media_apis", "analytics_platform", "email", "sms"],
        optional_integrations=[
            "whatsapp_business", "google_ads", "facebook_ads", "influencer_platform",
            "crm_system", "e_commerce_platform", "payment_gateway"
        ],
        
        supported_regions=["NG", "ZA", "KE", "GH", "UG", "TZ", "RW", "ET"],
        supported_currencies=["NGN", "ZAR", "KES", "GHS", "UGX", "TZS", "RWF", "ETB"],
        supported_languages=["en", "ha", "yo", "ig", "sw", "af", "zu", "am", "fr"]
    )
