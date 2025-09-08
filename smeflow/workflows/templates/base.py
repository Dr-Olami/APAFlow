"""
Base models and enums for workflow templates.

This module contains the core data structures used across all workflow templates.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import uuid
from pydantic import BaseModel, Field

from ..nodes import NodeConfig


class IndustryType(str, Enum):
    """Supported industry types for workflow templates."""
    CONSULTING = "consulting"
    SALON_SPA = "salon_spa"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    PRODUCT_RECOMMENDER = "product_recommender"
    RESTAURANT = "restaurant"
    EDUCATION = "education"
    LOGISTICS = "logistics"
    FINTECH = "fintech"
    AGRICULTURE = "agriculture"
    MARKETING_CAMPAIGNS = "marketing_campaigns"
    COMPLIANCE_WORKFLOWS = "compliance_workflows"
    ERP_INTEGRATION = "erp_integration"


class FormFieldType(str, Enum):
    """Form field types for dynamic form generation."""
    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    NUMBER = "number"
    TEXTAREA = "textarea"
    SELECT = "select"
    MULTISELECT = "multiselect"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    FILE = "file"
    URL = "url"
    PASSWORD = "password"
    HIDDEN = "hidden"


class FormField(BaseModel):
    """Dynamic form field configuration."""
    name: str = Field(..., description="Field name/identifier")
    label: str = Field(..., description="Display label")
    field_type: FormFieldType = Field(..., description="Field input type")
    required: bool = Field(default=False, description="Whether field is required")
    placeholder: Optional[str] = Field(None, description="Placeholder text")
    default_value: Optional[str] = Field(None, description="Default value")
    options: Optional[List[str]] = Field(None, description="Options for select/radio fields")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")
    help_text: Optional[str] = Field(None, description="Help text for the field")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class IndustryTemplate(BaseModel):
    """Industry-specific workflow template."""
    industry: IndustryType = Field(..., description="Industry type")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    
    # Form configuration
    booking_form_fields: List[FormField] = Field(default_factory=list, description="Booking form fields")
    confirmation_fields: List[FormField] = Field(default_factory=list, description="Confirmation form fields")
    
    # Workflow configuration
    workflow_nodes: List[Dict[str, Any]] = Field(default_factory=list, description="Workflow nodes")
    workflow_edges: List[Dict[str, str]] = Field(default_factory=list, description="Workflow edges")
    
    # Business configuration
    business_hours: Dict[str, Any] = Field(default_factory=dict, description="Business hours")
    advance_booking_days: int = Field(default=7, description="Advance booking days")
    cancellation_policy: str = Field(default="", description="Cancellation policy")
    
    # Notification settings
    notification_settings: Dict[str, bool] = Field(default_factory=dict, description="Notification preferences")
    
    # Integration settings
    required_integrations: List[str] = Field(default_factory=list, description="Required integrations")
    optional_integrations: List[str] = Field(default_factory=list, description="Optional integrations")
    
    # Localization
    supported_regions: List[str] = Field(default_factory=list, description="Supported regions")
    supported_currencies: List[str] = Field(default_factory=list, description="Supported currencies")
    supported_languages: List[str] = Field(default_factory=list, description="Supported languages")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class IndustryTemplateFactory:
    """Factory class for creating industry-specific workflow templates."""
    
    @staticmethod
    def get_template(industry: IndustryType) -> IndustryTemplate:
        """Get template for specified industry type."""
        # Import here to avoid circular imports
        from . import consulting, healthcare, retail, compliance_workflows, erp_integration, marketing_campaigns
        
        template_map = {
            IndustryType.CONSULTING: consulting.create_consulting_template,
            IndustryType.SALON_SPA: consulting.create_salon_spa_template,
            IndustryType.HEALTHCARE: healthcare.create_healthcare_template,
            IndustryType.MANUFACTURING: retail.create_manufacturing_template,
            IndustryType.RETAIL: retail.create_retail_template,
            IndustryType.PRODUCT_RECOMMENDER: retail.create_product_recommender_template,
            IndustryType.RESTAURANT: retail.create_restaurant_template,
            IndustryType.EDUCATION: healthcare.create_education_template,
            IndustryType.LOGISTICS: retail.create_logistics_template,
            IndustryType.FINTECH: retail.create_fintech_template,
            IndustryType.AGRICULTURE: retail.create_agriculture_template,
            IndustryType.MARKETING_CAMPAIGNS: marketing_campaigns.create_marketing_campaigns_template,
            IndustryType.COMPLIANCE_WORKFLOWS: compliance_workflows.create_compliance_workflows_template,
            IndustryType.ERP_INTEGRATION: erp_integration.create_erp_integration_template,
        }
        
        template_func = template_map.get(industry)
        if not template_func:
            raise ValueError(f"No template found for industry: {industry}")
        
        return template_func()
    
    @staticmethod
    def get_all_templates() -> Dict[IndustryType, IndustryTemplate]:
        """Get all available templates."""
        templates = {}
        for industry in IndustryType:
            try:
                templates[industry] = IndustryTemplateFactory.get_template(industry)
            except ValueError:
                # Skip industries without templates
                continue
        return templates
