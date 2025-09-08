"""
Consulting workflow templates.

This module contains workflow templates for consulting and professional services.
"""

from .base import IndustryType, FormFieldType, FormField, IndustryTemplate


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
                required=True
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
            ),
            FormField(
                name="special_requests",
                label="Special Requests",
                field_type=FormFieldType.TEXTAREA,
                required=False,
                placeholder="Any allergies, preferences, or special requests..."
            )
        ],
        
        workflow_nodes=[
            {"name": "start", "type": "start"},
            {"name": "service_selection", "type": "agent", "config": {"task": "select_spa_services"}},
            {"name": "availability_check", "type": "agent", "config": {"task": "check_stylist_availability"}},
            {"name": "booking_confirmation", "type": "agent", "config": {"task": "confirm_spa_booking"}},
            {"name": "reminder_setup", "type": "agent", "config": {"task": "setup_appointment_reminders"}},
            {"name": "end", "type": "end"}
        ],
        
        workflow_edges=[
            {"from": "start", "to": "service_selection"},
            {"from": "service_selection", "to": "availability_check"},
            {"from": "availability_check", "to": "booking_confirmation"},
            {"from": "booking_confirmation", "to": "reminder_setup"},
            {"from": "reminder_setup", "to": "end"}
        ],
        
        business_hours={
            "monday": {"start": "09:00", "end": "19:00"},
            "tuesday": {"start": "09:00", "end": "19:00"},
            "wednesday": {"start": "09:00", "end": "19:00"},
            "thursday": {"start": "09:00", "end": "19:00"},
            "friday": {"start": "09:00", "end": "20:00"},
            "saturday": {"start": "08:00", "end": "20:00"},
            "sunday": {"start": "10:00", "end": "18:00"}
        },
        
        advance_booking_days=14,
        cancellation_policy="4 hours advance notice required for cancellation",
        
        required_integrations=["calendar", "sms"],
        optional_integrations=["payment_gateway", "loyalty_program"],
        
        supported_regions=["NG", "KE", "ZA", "GH"],
        supported_currencies=["NGN", "KES", "ZAR", "GHS"],
        supported_languages=["en", "ha", "yo", "ig", "sw"]
    )
