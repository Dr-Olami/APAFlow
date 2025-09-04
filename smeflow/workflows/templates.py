"""
Industry-Specific Workflow Templates for SMEFlow.

This module provides pre-built workflow templates tailored for different
African SME industries with customizable forms and business processes.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import uuid
from pydantic import BaseModel, Field

from .nodes import NodeConfig


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


class FormFieldType(str, Enum):
    """Form field types for dynamic form generation."""
    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    SELECT = "select"
    MULTISELECT = "multiselect"
    TEXTAREA = "textarea"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    FILE = "file"
    NUMBER = "number"
    CURRENCY = "currency"


class FormField(BaseModel):
    """Dynamic form field definition."""
    name: str
    label: str
    field_type: FormFieldType
    required: bool = False
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    options: Optional[List[str]] = None  # For select/radio fields
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    default_value: Optional[Any] = None
    
    # African market specific
    local_label: Optional[Dict[str, str]] = None  # Translations
    currency_code: Optional[str] = None  # For currency fields
    phone_format: Optional[str] = None  # For phone fields


class IndustryTemplate(BaseModel):
    """Industry-specific workflow template."""
    industry: IndustryType
    name: str
    description: str
    
    # Booking/appointment specific
    booking_form_fields: List[FormField]
    confirmation_fields: List[FormField]
    
    # Workflow configuration
    workflow_nodes: List[Dict[str, Any]]
    workflow_edges: List[Dict[str, str]]
    
    # Business rules
    business_hours: Dict[str, Any]
    advance_booking_days: int = 30
    cancellation_policy: str
    
    # Integration requirements
    required_integrations: List[str] = Field(default_factory=list)
    optional_integrations: List[str] = Field(default_factory=list)
    
    # African market specific
    supported_regions: List[str] = Field(default_factory=list)
    supported_currencies: List[str] = Field(default_factory=list)
    supported_languages: List[str] = Field(default_factory=list)


class IndustryTemplateFactory:
    """Factory for creating industry-specific workflow templates."""
    
    @staticmethod
    def create_consulting_template() -> IndustryTemplate:
        """Create consulting industry template."""
        return IndustryTemplate(
            industry=IndustryType.CONSULTING,
            name="Professional Consulting Booking",
            description="Booking workflow for consultants, advisors, and professional services",
            
            booking_form_fields=[
                FormField(
                    name="client_name",
                    label="Full Name",
                    field_type=FormFieldType.TEXT,
                    required=True,
                    placeholder="Enter your full name"
                ),
                FormField(
                    name="company_name",
                    label="Company/Organization",
                    field_type=FormFieldType.TEXT,
                    required=False,
                    placeholder="Your company name"
                ),
                FormField(
                    name="email",
                    label="Email Address",
                    field_type=FormFieldType.EMAIL,
                    required=True,
                    validation_rules={"format": "email"}
                ),
                FormField(
                    name="phone",
                    label="Phone Number",
                    field_type=FormFieldType.PHONE,
                    required=True,
                    phone_format="+234-XXX-XXX-XXXX",
                    placeholder="+234-801-234-5678"
                ),
                FormField(
                    name="consultation_type",
                    label="Type of Consultation",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=[
                        "Business Strategy",
                        "Financial Planning",
                        "Marketing Strategy",
                        "Operations Optimization",
                        "Digital Transformation",
                        "Other"
                    ]
                ),
                FormField(
                    name="preferred_date",
                    label="Preferred Date",
                    field_type=FormFieldType.DATE,
                    required=True,
                    validation_rules={"min_days_ahead": 1}
                ),
                FormField(
                    name="preferred_time",
                    label="Preferred Time",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=["Morning (9AM-12PM)", "Afternoon (1PM-4PM)", "Evening (5PM-7PM)"]
                ),
                FormField(
                    name="session_duration",
                    label="Session Duration",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=["30 minutes", "1 hour", "2 hours", "Half day", "Full day"]
                ),
                FormField(
                    name="consultation_details",
                    label="Brief Description of Your Needs",
                    field_type=FormFieldType.TEXTAREA,
                    required=True,
                    placeholder="Please describe what you'd like to discuss..."
                ),
                FormField(
                    name="budget_range",
                    label="Budget Range",
                    field_type=FormFieldType.SELECT,
                    required=False,
                    options=[
                        "₦50,000 - ₦100,000",
                        "₦100,000 - ₦250,000", 
                        "₦250,000 - ₦500,000",
                        "₦500,000+"
                    ]
                )
            ],
            
            confirmation_fields=[
                FormField(
                    name="payment_method",
                    label="Payment Method",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=["Bank Transfer", "Card Payment", "Mobile Money", "Cash"]
                ),
                FormField(
                    name="meeting_location",
                    label="Meeting Location",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=["Client Office", "Consultant Office", "Virtual Meeting", "Neutral Location"]
                )
            ],
            
            workflow_nodes=[
                {"name": "start", "type": "start"},
                {"name": "lead_qualification", "type": "agent", "config": {"task": "qualify_consulting_lead"}},
                {"name": "availability_check", "type": "agent", "config": {"task": "check_consultant_availability"}},
                {"name": "proposal_generation", "type": "agent", "config": {"task": "generate_consultation_proposal"}},
                {"name": "booking_confirmation", "type": "agent", "config": {"task": "confirm_consultation_booking"}},
                {"name": "calendar_integration", "type": "agent", "config": {"task": "add_to_calendar"}},
                {"name": "client_notification", "type": "agent", "config": {"task": "send_confirmation_email"}},
                {"name": "end", "type": "end"}
            ],
            
            workflow_edges=[
                {"from": "start", "to": "lead_qualification"},
                {"from": "lead_qualification", "to": "availability_check"},
                {"from": "availability_check", "to": "proposal_generation"},
                {"from": "proposal_generation", "to": "booking_confirmation"},
                {"from": "booking_confirmation", "to": "calendar_integration"},
                {"from": "calendar_integration", "to": "client_notification"},
                {"from": "client_notification", "to": "end"}
            ],
            
            business_hours={
                "monday": {"start": "09:00", "end": "17:00"},
                "tuesday": {"start": "09:00", "end": "17:00"},
                "wednesday": {"start": "09:00", "end": "17:00"},
                "thursday": {"start": "09:00", "end": "17:00"},
                "friday": {"start": "09:00", "end": "17:00"},
                "saturday": {"start": "10:00", "end": "14:00"},
                "sunday": {"closed": True}
            },
            
            advance_booking_days=30,
            cancellation_policy="24 hours advance notice required for cancellation",
            
            required_integrations=["calendar", "email"],
            optional_integrations=["payment_gateway", "video_conferencing", "crm"],
            
            supported_regions=["NG", "KE", "ZA", "GH"],
            supported_currencies=["NGN", "KES", "ZAR", "GHS"],
            supported_languages=["en", "ha", "yo", "ig", "sw"]
        )
    
    @staticmethod
    def create_salon_spa_template() -> IndustryTemplate:
        """Create salon/spa industry template."""
        return IndustryTemplate(
            industry=IndustryType.SALON_SPA,
            name="Salon & Spa Booking",
            description="Appointment booking for salons, spas, and beauty services",
            
            booking_form_fields=[
                FormField(
                    name="client_name",
                    label="Full Name",
                    field_type=FormFieldType.TEXT,
                    required=True
                ),
                FormField(
                    name="phone",
                    label="Phone Number",
                    field_type=FormFieldType.PHONE,
                    required=True,
                    phone_format="+234-XXX-XXX-XXXX"
                ),
                FormField(
                    name="email",
                    label="Email Address",
                    field_type=FormFieldType.EMAIL,
                    required=False
                ),
                FormField(
                    name="services",
                    label="Services Needed",
                    field_type=FormFieldType.MULTISELECT,
                    required=True,
                    options=[
                        "Haircut & Styling",
                        "Hair Coloring",
                        "Manicure",
                        "Pedicure", 
                        "Facial Treatment",
                        "Massage Therapy",
                        "Eyebrow Threading",
                        "Makeup Application",
                        "Hair Treatment",
                        "Waxing"
                    ]
                ),
                FormField(
                    name="preferred_stylist",
                    label="Preferred Stylist/Therapist",
                    field_type=FormFieldType.SELECT,
                    required=False,
                    options=["Any Available", "Adunni", "Kemi", "Fatima", "Grace"]
                ),
                FormField(
                    name="appointment_date",
                    label="Preferred Date",
                    field_type=FormFieldType.DATE,
                    required=True
                ),
                FormField(
                    name="appointment_time",
                    label="Preferred Time",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=[
                        "9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM",
                        "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM"
                    ]
                ),
                FormField(
                    name="special_requests",
                    label="Special Requests or Allergies",
                    field_type=FormFieldType.TEXTAREA,
                    required=False,
                    placeholder="Any allergies, preferences, or special requests..."
                ),
                FormField(
                    name="first_visit",
                    label="Is this your first visit?",
                    field_type=FormFieldType.RADIO,
                    required=True,
                    options=["Yes", "No"]
                )
            ],
            
            confirmation_fields=[
                FormField(
                    name="payment_preference",
                    label="Payment Method",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=["Cash", "Card", "Mobile Transfer", "Bank Transfer"]
                ),
                FormField(
                    name="reminder_preference",
                    label="Reminder Preference",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=["SMS", "WhatsApp", "Phone Call", "Email"]
                )
            ],
            
            workflow_nodes=[
                {"name": "start", "type": "start"},
                {"name": "service_validation", "type": "agent", "config": {"task": "validate_service_availability"}},
                {"name": "stylist_assignment", "type": "agent", "config": {"task": "assign_stylist"}},
                {"name": "time_slot_booking", "type": "agent", "config": {"task": "book_time_slot"}},
                {"name": "appointment_confirmation", "type": "agent", "config": {"task": "confirm_appointment"}},
                {"name": "reminder_setup", "type": "agent", "config": {"task": "setup_appointment_reminders"}},
                {"name": "end", "type": "end"}
            ],
            
            workflow_edges=[
                {"from": "start", "to": "service_validation"},
                {"from": "service_validation", "to": "stylist_assignment"},
                {"from": "stylist_assignment", "to": "time_slot_booking"},
                {"from": "time_slot_booking", "to": "appointment_confirmation"},
                {"from": "appointment_confirmation", "to": "reminder_setup"},
                {"from": "reminder_setup", "to": "end"}
            ],
            
            business_hours={
                "monday": {"closed": True},
                "tuesday": {"start": "09:00", "end": "18:00"},
                "wednesday": {"start": "09:00", "end": "18:00"},
                "thursday": {"start": "09:00", "end": "18:00"},
                "friday": {"start": "09:00", "end": "19:00"},
                "saturday": {"start": "08:00", "end": "19:00"},
                "sunday": {"start": "12:00", "end": "17:00"}
            },
            
            advance_booking_days=14,
            cancellation_policy="4 hours advance notice required",
            
            required_integrations=["sms", "calendar"],
            optional_integrations=["whatsapp", "payment_gateway", "pos_system"],
            
            supported_regions=["NG", "KE", "ZA", "GH"],
            supported_currencies=["NGN", "KES", "ZAR", "GHS"],
            supported_languages=["en", "ha", "yo", "ig", "sw"]
        )
    
    @staticmethod
    def create_healthcare_template() -> IndustryTemplate:
        """Create healthcare industry template."""
        return IndustryTemplate(
            industry=IndustryType.HEALTHCARE,
            name="Healthcare Appointment Booking",
            description="Medical appointment booking for clinics and healthcare providers",
            
            booking_form_fields=[
                FormField(
                    name="patient_name",
                    label="Patient Full Name",
                    field_type=FormFieldType.TEXT,
                    required=True
                ),
                FormField(
                    name="date_of_birth",
                    label="Date of Birth",
                    field_type=FormFieldType.DATE,
                    required=True
                ),
                FormField(
                    name="phone",
                    label="Phone Number",
                    field_type=FormFieldType.PHONE,
                    required=True,
                    phone_format="+234-XXX-XXX-XXXX"
                ),
                FormField(
                    name="email",
                    label="Email Address",
                    field_type=FormFieldType.EMAIL,
                    required=False
                ),
                FormField(
                    name="appointment_type",
                    label="Type of Appointment",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=[
                        "General Consultation",
                        "Follow-up Visit",
                        "Specialist Consultation",
                        "Diagnostic Test",
                        "Vaccination",
                        "Health Screening",
                        "Emergency"
                    ]
                ),
                FormField(
                    name="preferred_doctor",
                    label="Preferred Doctor",
                    field_type=FormFieldType.SELECT,
                    required=False,
                    options=["Any Available", "Dr. Adebayo", "Dr. Okafor", "Dr. Hassan"]
                ),
                FormField(
                    name="symptoms",
                    label="Symptoms or Reason for Visit",
                    field_type=FormFieldType.TEXTAREA,
                    required=True,
                    placeholder="Please describe your symptoms or reason for the visit..."
                ),
                FormField(
                    name="insurance_provider",
                    label="Insurance Provider",
                    field_type=FormFieldType.SELECT,
                    required=False,
                    options=["None", "NHIS", "Private Insurance", "Corporate Plan"]
                ),
                FormField(
                    name="emergency_contact",
                    label="Emergency Contact",
                    field_type=FormFieldType.PHONE,
                    required=True
                ),
                FormField(
                    name="preferred_date",
                    label="Preferred Date",
                    field_type=FormFieldType.DATE,
                    required=True
                ),
                FormField(
                    name="preferred_time",
                    label="Preferred Time",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=["Morning", "Afternoon", "Evening"]
                )
            ],
            
            confirmation_fields=[
                FormField(
                    name="payment_method",
                    label="Payment Method",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=["Cash", "Card", "Insurance", "Bank Transfer"]
                ),
                FormField(
                    name="consent_forms",
                    label="Consent Forms Completed",
                    field_type=FormFieldType.CHECKBOX,
                    required=True
                )
            ],
            
            workflow_nodes=[
                {"name": "start", "type": "start"},
                {"name": "patient_verification", "type": "agent", "config": {"task": "verify_patient_details"}},
                {"name": "doctor_availability", "type": "agent", "config": {"task": "check_doctor_availability"}},
                {"name": "appointment_scheduling", "type": "agent", "config": {"task": "schedule_appointment"}},
                {"name": "insurance_verification", "type": "agent", "config": {"task": "verify_insurance"}},
                {"name": "confirmation_notification", "type": "agent", "config": {"task": "send_appointment_confirmation"}},
                {"name": "reminder_setup", "type": "agent", "config": {"task": "setup_appointment_reminders"}},
                {"name": "end", "type": "end"}
            ],
            
            workflow_edges=[
                {"from": "start", "to": "patient_verification"},
                {"from": "patient_verification", "to": "doctor_availability"},
                {"from": "doctor_availability", "to": "appointment_scheduling"},
                {"from": "appointment_scheduling", "to": "insurance_verification"},
                {"from": "insurance_verification", "to": "confirmation_notification"},
                {"from": "confirmation_notification", "to": "reminder_setup"},
                {"from": "reminder_setup", "to": "end"}
            ],
            
            business_hours={
                "monday": {"start": "08:00", "end": "17:00"},
                "tuesday": {"start": "08:00", "end": "17:00"},
                "wednesday": {"start": "08:00", "end": "17:00"},
                "thursday": {"start": "08:00", "end": "17:00"},
                "friday": {"start": "08:00", "end": "17:00"},
                "saturday": {"start": "09:00", "end": "13:00"},
                "sunday": {"closed": True}
            },
            
            advance_booking_days=60,
            cancellation_policy="24 hours advance notice required",
            
            required_integrations=["sms", "email", "calendar"],
            optional_integrations=["insurance_api", "emr_system", "payment_gateway"],
            
            supported_regions=["NG", "KE", "ZA", "GH"],
            supported_currencies=["NGN", "KES", "ZAR", "GHS"],
            supported_languages=["en", "ha", "yo", "ig", "sw"]
        )
    
    @staticmethod
    def create_manufacturing_template() -> IndustryTemplate:
        """Create manufacturing industry template for equipment/facility booking."""
        return IndustryTemplate(
            industry=IndustryType.MANUFACTURING,
            name="Manufacturing Resource Booking",
            description="Equipment and facility booking for manufacturing SMEs",
            
            booking_form_fields=[
                FormField(
                    name="company_name",
                    label="Company Name",
                    field_type=FormFieldType.TEXT,
                    required=True
                ),
                FormField(
                    name="contact_person",
                    label="Contact Person",
                    field_type=FormFieldType.TEXT,
                    required=True
                ),
                FormField(
                    name="phone",
                    label="Phone Number",
                    field_type=FormFieldType.PHONE,
                    required=True
                ),
                FormField(
                    name="email",
                    label="Email Address",
                    field_type=FormFieldType.EMAIL,
                    required=True
                ),
                FormField(
                    name="resource_type",
                    label="Resource Needed",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=[
                        "Production Line",
                        "CNC Machine",
                        "3D Printer",
                        "Assembly Area",
                        "Testing Equipment",
                        "Packaging Line",
                        "Storage Space",
                        "Meeting Room"
                    ]
                ),
                FormField(
                    name="booking_duration",
                    label="Booking Duration",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=["2 hours", "4 hours", "8 hours", "1 day", "2 days", "1 week", "Custom"]
                ),
                FormField(
                    name="start_date",
                    label="Start Date",
                    field_type=FormFieldType.DATE,
                    required=True
                ),
                FormField(
                    name="end_date",
                    label="End Date",
                    field_type=FormFieldType.DATE,
                    required=True
                ),
                FormField(
                    name="project_description",
                    label="Project Description",
                    field_type=FormFieldType.TEXTAREA,
                    required=True,
                    placeholder="Describe what you'll be manufacturing..."
                ),
                FormField(
                    name="safety_requirements",
                    label="Special Safety Requirements",
                    field_type=FormFieldType.TEXTAREA,
                    required=False
                ),
                FormField(
                    name="estimated_budget",
                    label="Estimated Budget",
                    field_type=FormFieldType.CURRENCY,
                    required=True,
                    currency_code="NGN"
                )
            ],
            
            confirmation_fields=[
                FormField(
                    name="payment_terms",
                    label="Payment Terms",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=["50% Upfront", "Full Payment", "Net 30", "Custom Terms"]
                ),
                FormField(
                    name="insurance_coverage",
                    label="Insurance Coverage",
                    field_type=FormFieldType.CHECKBOX,
                    required=True
                )
            ],
            
            workflow_nodes=[
                {"name": "start", "type": "start"},
                {"name": "resource_availability", "type": "agent", "config": {"task": "check_resource_availability"}},
                {"name": "capacity_planning", "type": "agent", "config": {"task": "plan_production_capacity"}},
                {"name": "safety_assessment", "type": "agent", "config": {"task": "assess_safety_requirements"}},
                {"name": "cost_calculation", "type": "agent", "config": {"task": "calculate_booking_cost"}},
                {"name": "booking_confirmation", "type": "agent", "config": {"task": "confirm_resource_booking"}},
                {"name": "schedule_integration", "type": "agent", "config": {"task": "integrate_production_schedule"}},
                {"name": "end", "type": "end"}
            ],
            
            workflow_edges=[
                {"from": "start", "to": "resource_availability"},
                {"from": "resource_availability", "to": "capacity_planning"},
                {"from": "capacity_planning", "to": "safety_assessment"},
                {"from": "safety_assessment", "to": "cost_calculation"},
                {"from": "cost_calculation", "to": "booking_confirmation"},
                {"from": "booking_confirmation", "to": "schedule_integration"},
                {"from": "schedule_integration", "to": "end"}
            ],
            
            business_hours={
                "monday": {"start": "06:00", "end": "18:00"},
                "tuesday": {"start": "06:00", "end": "18:00"},
                "wednesday": {"start": "06:00", "end": "18:00"},
                "thursday": {"start": "06:00", "end": "18:00"},
                "friday": {"start": "06:00", "end": "18:00"},
                "saturday": {"start": "08:00", "end": "16:00"},
                "sunday": {"closed": True}
            },
            
            advance_booking_days=90,
            cancellation_policy="7 days advance notice required for full refund",
            
            required_integrations=["calendar", "email", "erp_system"],
            optional_integrations=["payment_gateway", "inventory_management", "quality_control"],
            
            supported_regions=["NG", "KE", "ZA", "GH"],
            supported_currencies=["NGN", "KES", "ZAR", "GHS"],
            supported_languages=["en", "ha", "yo", "ig", "sw"]
        )
    
    @staticmethod
    def get_template(industry: IndustryType) -> IndustryTemplate:
        """Get template for specific industry."""
        templates = {
            IndustryType.CONSULTING: IndustryTemplateFactory.create_consulting_template,
            IndustryType.SALON_SPA: IndustryTemplateFactory.create_salon_spa_template,
            IndustryType.HEALTHCARE: IndustryTemplateFactory.create_healthcare_template,
            IndustryType.MANUFACTURING: IndustryTemplateFactory.create_manufacturing_template,
            IndustryType.PRODUCT_RECOMMENDER: IndustryTemplateFactory.create_product_recommender_template,
        }
        
        if industry not in templates:
            raise ValueError(f"Template not available for industry: {industry}")
        
        return templates[industry]()
    
    @staticmethod
    def list_available_industries() -> List[IndustryType]:
        """List all available industry templates."""
        return [
            IndustryType.CONSULTING,
            IndustryType.SALON_SPA,
            IndustryType.HEALTHCARE,
            IndustryType.MANUFACTURING,
            IndustryType.PRODUCT_RECOMMENDER,
        ]
    
    @staticmethod
    def customize_template(
        base_template: IndustryTemplate,
        custom_fields: List[FormField],
        custom_workflow_steps: Optional[List[Dict[str, Any]]] = None,
        custom_business_rules: Optional[Dict[str, Any]] = None
    ) -> IndustryTemplate:
        """
        Customize an industry template with specific business requirements.
        
        Args:
            base_template: Base industry template
            custom_fields: Additional form fields
            custom_workflow_steps: Custom workflow nodes
            custom_business_rules: Custom business rules
            
        Returns:
            Customized template
        """
        # Create a copy of the base template
        customized = base_template.copy(deep=True)
        
        # Add custom fields
        customized.booking_form_fields.extend(custom_fields)
        
        # Add custom workflow steps if provided
        if custom_workflow_steps:
            customized.workflow_nodes.extend(custom_workflow_steps)
        
        # Apply custom business rules
        if custom_business_rules:
            if "business_hours" in custom_business_rules:
                customized.business_hours.update(custom_business_rules["business_hours"])
            if "advance_booking_days" in custom_business_rules:
                customized.advance_booking_days = custom_business_rules["advance_booking_days"]
            if "cancellation_policy" in custom_business_rules:
                customized.cancellation_policy = custom_business_rules["cancellation_policy"]
        
        return customized
    
    @staticmethod
    def create_product_recommender_template() -> IndustryTemplate:
        """Create product recommender template for e-commerce/retail."""
        return IndustryTemplate(
            industry=IndustryType.PRODUCT_RECOMMENDER,
            name="AI Product Recommender System",
            description="Intelligent product discovery and recommendation workflow for e-commerce and retail SMEs",
            
            booking_form_fields=[
                FormField(
                    name="customer_name",
                    label="Customer Name",
                    field_type=FormFieldType.TEXT,
                    required=True,
                    placeholder="Enter customer name"
                ),
                FormField(
                    name="customer_email",
                    label="Email Address",
                    field_type=FormFieldType.EMAIL,
                    required=True,
                    validation_rules={"format": "email"},
                    placeholder="customer@example.com"
                ),
                FormField(
                    name="customer_phone",
                    label="Phone Number",
                    field_type=FormFieldType.PHONE,
                    required=False,
                    phone_format="+234-XXX-XXX-XXXX",
                    placeholder="+234-801-234-5678"
                ),
                FormField(
                    name="product_category",
                    label="Product Category of Interest",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=[
                        "Electronics & Gadgets",
                        "Fashion & Clothing",
                        "Home & Living",
                        "Beauty & Personal Care",
                        "Sports & Fitness",
                        "Books & Education",
                        "Food & Beverages",
                        "Health & Wellness",
                        "Automotive",
                        "Arts & Crafts"
                    ]
                ),
                FormField(
                    name="budget_range",
                    label="Budget Range",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=[
                        "Under ₦10,000",
                        "₦10,000 - ₦25,000",
                        "₦25,000 - ₦50,000",
                        "₦50,000 - ₦100,000",
                        "₦100,000 - ₦250,000",
                        "₦250,000 - ₦500,000",
                        "Above ₦500,000"
                    ]
                ),
                FormField(
                    name="purchase_urgency",
                    label="When do you need this?",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=[
                        "Immediately",
                        "Within 1 week",
                        "Within 1 month",
                        "Within 3 months",
                        "Just browsing"
                    ]
                ),
                FormField(
                    name="preferred_brands",
                    label="Preferred Brands (if any)",
                    field_type=FormFieldType.MULTISELECT,
                    required=False,
                    options=[
                        "Samsung", "Apple", "Nike", "Adidas", "HP", "Dell",
                        "Tecno", "Infinix", "Oraimo", "Xiaomi", "Huawei",
                        "Local Brands", "No Preference"
                    ]
                ),
                FormField(
                    name="shopping_preferences",
                    label="Shopping Preferences",
                    field_type=FormFieldType.MULTISELECT,
                    required=False,
                    options=[
                        "Latest Technology",
                        "Best Value for Money",
                        "Premium Quality",
                        "Eco-Friendly",
                        "Local Products",
                        "Fast Delivery",
                        "Warranty Coverage",
                        "After-Sales Support"
                    ]
                ),
                FormField(
                    name="previous_purchases",
                    label="Tell us about your recent purchases",
                    field_type=FormFieldType.TEXTAREA,
                    required=False,
                    placeholder="Describe products you've bought recently to help us understand your preferences..."
                ),
                FormField(
                    name="specific_requirements",
                    label="Specific Requirements or Features",
                    field_type=FormFieldType.TEXTAREA,
                    required=False,
                    placeholder="Any specific features, colors, sizes, or requirements you're looking for..."
                ),
                FormField(
                    name="delivery_location",
                    label="Delivery Location",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=[
                        "Lagos, Nigeria",
                        "Abuja, Nigeria", 
                        "Kano, Nigeria",
                        "Port Harcourt, Nigeria",
                        "Ibadan, Nigeria",
                        "Nairobi, Kenya",
                        "Mombasa, Kenya",
                        "Cape Town, South Africa",
                        "Johannesburg, South Africa",
                        "Accra, Ghana",
                        "Other (specify in comments)"
                    ]
                )
            ],
            
            confirmation_fields=[
                FormField(
                    name="recommendation_delivery",
                    label="How would you like to receive recommendations?",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=["Email", "SMS", "WhatsApp", "Phone Call", "In-App Notification"]
                ),
                FormField(
                    name="follow_up_preference",
                    label="Follow-up Preference",
                    field_type=FormFieldType.SELECT,
                    required=True,
                    options=["Daily Updates", "Weekly Summary", "Only Best Matches", "No Follow-up"]
                ),
                FormField(
                    name="price_alerts",
                    label="Enable Price Drop Alerts?",
                    field_type=FormFieldType.CHECKBOX,
                    required=False
                ),
                FormField(
                    name="newsletter_subscription",
                    label="Subscribe to Product Newsletter?",
                    field_type=FormFieldType.CHECKBOX,
                    required=False
                )
            ],
            
            workflow_nodes=[
                {"name": "start", "type": "start"},
                {"name": "customer_profiling", "type": "agent", "config": {"task": "analyze_customer_preferences"}},
                {"name": "product_discovery", "type": "agent", "config": {"task": "discover_relevant_products"}},
                {"name": "ai_recommendation", "type": "agent", "config": {"task": "generate_ai_recommendations"}},
                {"name": "price_comparison", "type": "agent", "config": {"task": "compare_prices_across_vendors"}},
                {"name": "availability_check", "type": "agent", "config": {"task": "check_product_availability"}},
                {"name": "recommendation_ranking", "type": "agent", "config": {"task": "rank_recommendations_by_relevance"}},
                {"name": "personalization", "type": "agent", "config": {"task": "personalize_recommendations"}},
                {"name": "delivery_estimation", "type": "agent", "config": {"task": "estimate_delivery_times"}},
                {"name": "recommendation_packaging", "type": "agent", "config": {"task": "package_final_recommendations"}},
                {"name": "customer_notification", "type": "agent", "config": {"task": "send_recommendations_to_customer"}},
                {"name": "feedback_collection", "type": "agent", "config": {"task": "collect_customer_feedback"}},
                {"name": "end", "type": "end"}
            ],
            
            workflow_edges=[
                {"from": "start", "to": "customer_profiling"},
                {"from": "customer_profiling", "to": "product_discovery"},
                {"from": "product_discovery", "to": "ai_recommendation"},
                {"from": "ai_recommendation", "to": "price_comparison"},
                {"from": "price_comparison", "to": "availability_check"},
                {"from": "availability_check", "to": "recommendation_ranking"},
                {"from": "recommendation_ranking", "to": "personalization"},
                {"from": "personalization", "to": "delivery_estimation"},
                {"from": "delivery_estimation", "to": "recommendation_packaging"},
                {"from": "recommendation_packaging", "to": "customer_notification"},
                {"from": "customer_notification", "to": "feedback_collection"},
                {"from": "feedback_collection", "to": "end"}
            ],
            
            business_hours={
                "monday": {"start": "08:00", "end": "20:00"},
                "tuesday": {"start": "08:00", "end": "20:00"},
                "wednesday": {"start": "08:00", "end": "20:00"},
                "thursday": {"start": "08:00", "end": "20:00"},
                "friday": {"start": "08:00", "end": "20:00"},
                "saturday": {"start": "09:00", "end": "18:00"},
                "sunday": {"start": "10:00", "end": "16:00"}
            },
            
            advance_booking_days=0,  # Immediate processing
            cancellation_policy="Recommendations can be updated anytime based on feedback",
            
            required_integrations=["ai_engine", "product_catalog", "email", "sms"],
            optional_integrations=[
                "whatsapp", "payment_gateway", "inventory_management", 
                "price_monitoring", "analytics", "crm", "social_media"
            ],
            
            supported_regions=["NG", "KE", "ZA", "GH", "UG", "TZ"],
            supported_currencies=["NGN", "KES", "ZAR", "GHS", "UGX", "TZS"],
            supported_languages=["en", "ha", "yo", "ig", "sw", "zu", "af"]
        )
