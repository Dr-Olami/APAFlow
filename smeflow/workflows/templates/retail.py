"""
Retail and business workflow templates.

This module contains workflow templates for retail, manufacturing, and general business services.
"""

from .base import IndustryType, FormFieldType, FormField, IndustryTemplate


def create_retail_template() -> IndustryTemplate:
    """Create retail industry template."""
    return IndustryTemplate(
        industry=IndustryType.RETAIL,
        name="Retail Service Booking",
        description="Booking system for retail services and appointments",
        
        booking_form_fields=[
            FormField(
                name="customer_name",
                label="Customer Name",
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
                name="service_type",
                label="Service Type",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "Personal Shopping",
                    "Product Consultation",
                    "Fitting Session",
                    "Custom Order",
                    "Delivery Scheduling",
                    "Returns/Exchange"
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
            )
        ],
        
        workflow_nodes=[
            {"name": "start", "type": "start"},
            {"name": "service_booking", "type": "agent", "config": {"task": "book_retail_service"}},
            {"name": "inventory_check", "type": "agent", "config": {"task": "check_product_availability"}},
            {"name": "confirmation", "type": "agent", "config": {"task": "confirm_retail_booking"}},
            {"name": "end", "type": "end"}
        ],
        
        workflow_edges=[
            {"from": "start", "to": "service_booking"},
            {"from": "service_booking", "to": "inventory_check"},
            {"from": "inventory_check", "to": "confirmation"},
            {"from": "confirmation", "to": "end"}
        ],
        
        business_hours={
            "monday": {"start": "09:00", "end": "18:00"},
            "tuesday": {"start": "09:00", "end": "18:00"},
            "wednesday": {"start": "09:00", "end": "18:00"},
            "thursday": {"start": "09:00", "end": "18:00"},
            "friday": {"start": "09:00", "end": "19:00"},
            "saturday": {"start": "09:00", "end": "19:00"},
            "sunday": {"start": "11:00", "end": "17:00"}
        },
        
        advance_booking_days=7,
        cancellation_policy="2 hours advance notice required for cancellation",
        
        required_integrations=["inventory", "calendar"],
        optional_integrations=["payment_gateway", "loyalty_program", "crm"],
        
        supported_regions=["NG", "KE", "ZA", "GH"],
        supported_currencies=["NGN", "KES", "ZAR", "GHS"],
        supported_languages=["en", "ha", "yo", "ig", "sw"]
    )


def create_manufacturing_template() -> IndustryTemplate:
    """Create manufacturing industry template."""
    return IndustryTemplate(
        industry=IndustryType.MANUFACTURING,
        name="Manufacturing Service Booking",
        description="Booking system for manufacturing services and consultations",
        
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
                name="service_type",
                label="Service Type",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "Custom Manufacturing",
                    "Quality Inspection",
                    "Equipment Maintenance",
                    "Process Consultation",
                    "Supply Chain Review"
                ]
            ),
            FormField(
                name="project_scope",
                label="Project Scope",
                field_type=FormFieldType.TEXTAREA,
                required=True,
                placeholder="Describe your manufacturing requirements..."
            )
        ],
        
        workflow_nodes=[
            {"name": "start", "type": "start"},
            {"name": "requirements_analysis", "type": "agent", "config": {"task": "analyze_manufacturing_requirements"}},
            {"name": "capacity_check", "type": "agent", "config": {"task": "check_production_capacity"}},
            {"name": "quote_generation", "type": "agent", "config": {"task": "generate_manufacturing_quote"}},
            {"name": "booking_confirmation", "type": "agent", "config": {"task": "confirm_manufacturing_booking"}},
            {"name": "end", "type": "end"}
        ],
        
        workflow_edges=[
            {"from": "start", "to": "requirements_analysis"},
            {"from": "requirements_analysis", "to": "capacity_check"},
            {"from": "capacity_check", "to": "quote_generation"},
            {"from": "quote_generation", "to": "booking_confirmation"},
            {"from": "booking_confirmation", "to": "end"}
        ],
        
        business_hours={
            "monday": {"start": "07:00", "end": "17:00"},
            "tuesday": {"start": "07:00", "end": "17:00"},
            "wednesday": {"start": "07:00", "end": "17:00"},
            "thursday": {"start": "07:00", "end": "17:00"},
            "friday": {"start": "07:00", "end": "17:00"},
            "saturday": {"closed": True},
            "sunday": {"closed": True}
        },
        
        advance_booking_days=14,
        cancellation_policy="48 hours advance notice required for cancellation",
        
        required_integrations=["production_system", "calendar", "email"],
        optional_integrations=["erp_system", "quality_management", "supply_chain"],
        
        supported_regions=["NG", "KE", "ZA", "GH"],
        supported_currencies=["NGN", "KES", "ZAR", "GHS"],
        supported_languages=["en", "ha", "yo", "ig", "sw"]
    )


def create_product_recommender_template() -> IndustryTemplate:
    """Create product recommender template."""
    return IndustryTemplate(
        industry=IndustryType.PRODUCT_RECOMMENDER,
        name="Product Recommendation Service",
        description="AI-powered product recommendation and consultation service",
        
        booking_form_fields=[
            FormField(
                name="customer_name",
                label="Customer Name",
                field_type=FormFieldType.TEXT,
                required=True
            ),
            FormField(
                name="email",
                label="Email Address",
                field_type=FormFieldType.EMAIL,
                required=True
            ),
            FormField(
                name="product_category",
                label="Product Category",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "Electronics",
                    "Fashion & Clothing",
                    "Home & Garden",
                    "Health & Beauty",
                    "Sports & Outdoors",
                    "Books & Media"
                ]
            ),
            FormField(
                name="budget_range",
                label="Budget Range",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "Under ₦50,000",
                    "₦50,000 - ₦100,000",
                    "₦100,000 - ₦250,000",
                    "Over ₦250,000"
                ]
            ),
            FormField(
                name="preferences",
                label="Preferences & Requirements",
                field_type=FormFieldType.TEXTAREA,
                required=True,
                placeholder="Describe what you're looking for..."
            )
        ],
        
        workflow_nodes=[
            {"name": "start", "type": "start"},
            {"name": "preference_analysis", "type": "agent", "config": {"task": "analyze_customer_preferences"}},
            {"name": "product_matching", "type": "agent", "config": {"task": "match_products"}},
            {"name": "recommendation_generation", "type": "agent", "config": {"task": "generate_recommendations"}},
            {"name": "presentation", "type": "agent", "config": {"task": "present_recommendations"}},
            {"name": "end", "type": "end"}
        ],
        
        workflow_edges=[
            {"from": "start", "to": "preference_analysis"},
            {"from": "preference_analysis", "to": "product_matching"},
            {"from": "product_matching", "to": "recommendation_generation"},
            {"from": "recommendation_generation", "to": "presentation"},
            {"from": "presentation", "to": "end"}
        ],
        
        business_hours={
            "monday": {"start": "09:00", "end": "18:00"},
            "tuesday": {"start": "09:00", "end": "18:00"},
            "wednesday": {"start": "09:00", "end": "18:00"},
            "thursday": {"start": "09:00", "end": "18:00"},
            "friday": {"start": "09:00", "end": "18:00"},
            "saturday": {"start": "10:00", "end": "16:00"},
            "sunday": {"closed": True}
        },
        
        advance_booking_days=3,
        cancellation_policy="1 hour advance notice required for cancellation",
        
        required_integrations=["product_catalog", "ai_engine"],
        optional_integrations=["payment_gateway", "inventory_system", "crm"],
        
        supported_regions=["NG", "KE", "ZA", "GH"],
        supported_currencies=["NGN", "KES", "ZAR", "GHS"],
        supported_languages=["en", "ha", "yo", "ig", "sw"]
    )


def create_restaurant_template() -> IndustryTemplate:
    """Create restaurant industry template."""
    return IndustryTemplate(
        industry=IndustryType.RESTAURANT,
        name="Restaurant Reservation System",
        description="Table booking and reservation system for restaurants",
        
        booking_form_fields=[
            FormField(
                name="customer_name",
                label="Customer Name",
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
                name="party_size",
                label="Party Size",
                field_type=FormFieldType.SELECT,
                required=True,
                options=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10+"]
            ),
            FormField(
                name="reservation_date",
                label="Reservation Date",
                field_type=FormFieldType.DATE,
                required=True
            ),
            FormField(
                name="reservation_time",
                label="Reservation Time",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "12:00 PM", "12:30 PM", "1:00 PM", "1:30 PM",
                    "6:00 PM", "6:30 PM", "7:00 PM", "7:30 PM", "8:00 PM"
                ]
            ),
            FormField(
                name="special_requests",
                label="Special Requests",
                field_type=FormFieldType.TEXTAREA,
                required=False,
                placeholder="Dietary restrictions, celebrations, etc."
            )
        ],
        
        workflow_nodes=[
            {"name": "start", "type": "start"},
            {"name": "table_availability", "type": "agent", "config": {"task": "check_table_availability"}},
            {"name": "reservation_booking", "type": "agent", "config": {"task": "book_table_reservation"}},
            {"name": "confirmation", "type": "agent", "config": {"task": "send_reservation_confirmation"}},
            {"name": "reminder_setup", "type": "agent", "config": {"task": "setup_reservation_reminders"}},
            {"name": "end", "type": "end"}
        ],
        
        workflow_edges=[
            {"from": "start", "to": "table_availability"},
            {"from": "table_availability", "to": "reservation_booking"},
            {"from": "reservation_booking", "to": "confirmation"},
            {"from": "confirmation", "to": "reminder_setup"},
            {"from": "reminder_setup", "to": "end"}
        ],
        
        business_hours={
            "monday": {"start": "11:00", "end": "22:00"},
            "tuesday": {"start": "11:00", "end": "22:00"},
            "wednesday": {"start": "11:00", "end": "22:00"},
            "thursday": {"start": "11:00", "end": "22:00"},
            "friday": {"start": "11:00", "end": "23:00"},
            "saturday": {"start": "11:00", "end": "23:00"},
            "sunday": {"start": "12:00", "end": "21:00"}
        },
        
        advance_booking_days=30,
        cancellation_policy="2 hours advance notice required for cancellation",
        
        required_integrations=["reservation_system", "sms"],
        optional_integrations=["payment_gateway", "loyalty_program", "pos_system"],
        
        supported_regions=["NG", "KE", "ZA", "GH"],
        supported_currencies=["NGN", "KES", "ZAR", "GHS"],
        supported_languages=["en", "ha", "yo", "ig", "sw"]
    )


def create_logistics_template() -> IndustryTemplate:
    """Create logistics industry template."""
    return IndustryTemplate(
        industry=IndustryType.LOGISTICS,
        name="Logistics Service Booking",
        description="Booking system for logistics and delivery services",
        
        booking_form_fields=[
            FormField(
                name="sender_name",
                label="Sender Name",
                field_type=FormFieldType.TEXT,
                required=True
            ),
            FormField(
                name="sender_phone",
                label="Sender Phone",
                field_type=FormFieldType.PHONE,
                required=True
            ),
            FormField(
                name="pickup_address",
                label="Pickup Address",
                field_type=FormFieldType.TEXTAREA,
                required=True
            ),
            FormField(
                name="delivery_address",
                label="Delivery Address",
                field_type=FormFieldType.TEXTAREA,
                required=True
            ),
            FormField(
                name="package_type",
                label="Package Type",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "Documents",
                    "Small Package",
                    "Medium Package",
                    "Large Package",
                    "Fragile Items",
                    "Bulk Delivery"
                ]
            ),
            FormField(
                name="delivery_urgency",
                label="Delivery Urgency",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "Same Day",
                    "Next Day",
                    "2-3 Days",
                    "Standard (5-7 Days)"
                ]
            )
        ],
        
        workflow_nodes=[
            {"name": "start", "type": "start"},
            {"name": "route_planning", "type": "agent", "config": {"task": "plan_delivery_route"}},
            {"name": "driver_assignment", "type": "agent", "config": {"task": "assign_delivery_driver"}},
            {"name": "pickup_scheduling", "type": "agent", "config": {"task": "schedule_package_pickup"}},
            {"name": "tracking_setup", "type": "agent", "config": {"task": "setup_package_tracking"}},
            {"name": "confirmation", "type": "agent", "config": {"task": "send_booking_confirmation"}},
            {"name": "end", "type": "end"}
        ],
        
        workflow_edges=[
            {"from": "start", "to": "route_planning"},
            {"from": "route_planning", "to": "driver_assignment"},
            {"from": "driver_assignment", "to": "pickup_scheduling"},
            {"from": "pickup_scheduling", "to": "tracking_setup"},
            {"from": "tracking_setup", "to": "confirmation"},
            {"from": "confirmation", "to": "end"}
        ],
        
        business_hours={
            "monday": {"start": "06:00", "end": "20:00"},
            "tuesday": {"start": "06:00", "end": "20:00"},
            "wednesday": {"start": "06:00", "end": "20:00"},
            "thursday": {"start": "06:00", "end": "20:00"},
            "friday": {"start": "06:00", "end": "20:00"},
            "saturday": {"start": "08:00", "end": "18:00"},
            "sunday": {"start": "10:00", "end": "16:00"}
        },
        
        advance_booking_days=1,
        cancellation_policy="1 hour advance notice required for cancellation",
        
        required_integrations=["gps_tracking", "sms", "driver_app"],
        optional_integrations=["payment_gateway", "insurance", "fleet_management"],
        
        supported_regions=["NG", "KE", "ZA", "GH"],
        supported_currencies=["NGN", "KES", "ZAR", "GHS"],
        supported_languages=["en", "ha", "yo", "ig", "sw"]
    )


def create_fintech_template() -> IndustryTemplate:
    """Create fintech industry template."""
    return IndustryTemplate(
        industry=IndustryType.FINTECH,
        name="Financial Services Booking",
        description="Booking system for financial consultations and services",
        
        booking_form_fields=[
            FormField(
                name="client_name",
                label="Client Name",
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
                name="service_type",
                label="Service Type",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "Investment Consultation",
                    "Loan Application",
                    "Insurance Planning",
                    "Financial Planning",
                    "Tax Advisory",
                    "Business Banking"
                ]
            ),
            FormField(
                name="consultation_purpose",
                label="Consultation Purpose",
                field_type=FormFieldType.TEXTAREA,
                required=True,
                placeholder="Describe your financial needs..."
            )
        ],
        
        workflow_nodes=[
            {"name": "start", "type": "start"},
            {"name": "kyc_verification", "type": "agent", "config": {"task": "verify_client_identity"}},
            {"name": "risk_assessment", "type": "agent", "config": {"task": "assess_financial_risk"}},
            {"name": "advisor_matching", "type": "agent", "config": {"task": "match_financial_advisor"}},
            {"name": "consultation_booking", "type": "agent", "config": {"task": "book_financial_consultation"}},
            {"name": "confirmation", "type": "agent", "config": {"task": "send_consultation_confirmation"}},
            {"name": "end", "type": "end"}
        ],
        
        workflow_edges=[
            {"from": "start", "to": "kyc_verification"},
            {"from": "kyc_verification", "to": "risk_assessment"},
            {"from": "risk_assessment", "to": "advisor_matching"},
            {"from": "advisor_matching", "to": "consultation_booking"},
            {"from": "consultation_booking", "to": "confirmation"},
            {"from": "confirmation", "to": "end"}
        ],
        
        business_hours={
            "monday": {"start": "08:00", "end": "17:00"},
            "tuesday": {"start": "08:00", "end": "17:00"},
            "wednesday": {"start": "08:00", "end": "17:00"},
            "thursday": {"start": "08:00", "end": "17:00"},
            "friday": {"start": "08:00", "end": "17:00"},
            "saturday": {"closed": True},
            "sunday": {"closed": True}
        },
        
        advance_booking_days=7,
        cancellation_policy="24 hours advance notice required for cancellation",
        
        required_integrations=["kyc_system", "calendar", "secure_messaging"],
        optional_integrations=["payment_gateway", "document_management", "crm"],
        
        supported_regions=["NG", "KE", "ZA", "GH"],
        supported_currencies=["NGN", "KES", "ZAR", "GHS"],
        supported_languages=["en", "ha", "yo", "ig", "sw"]
    )


def create_agriculture_template() -> IndustryTemplate:
    """Create agriculture industry template."""
    return IndustryTemplate(
        industry=IndustryType.AGRICULTURE,
        name="Agricultural Services Booking",
        description="Booking system for agricultural consultations and services",
        
        booking_form_fields=[
            FormField(
                name="farmer_name",
                label="Farmer Name",
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
                name="farm_location",
                label="Farm Location",
                field_type=FormFieldType.TEXT,
                required=True
            ),
            FormField(
                name="farm_size",
                label="Farm Size (Hectares)",
                field_type=FormFieldType.NUMBER,
                required=True
            ),
            FormField(
                name="crop_type",
                label="Crop Type",
                field_type=FormFieldType.MULTISELECT,
                required=True,
                options=[
                    "Rice",
                    "Maize",
                    "Cassava",
                    "Yam",
                    "Cocoa",
                    "Palm Oil",
                    "Vegetables",
                    "Fruits",
                    "Livestock"
                ]
            ),
            FormField(
                name="service_needed",
                label="Service Needed",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "Soil Testing",
                    "Crop Consultation",
                    "Pest Control",
                    "Irrigation Planning",
                    "Harvest Planning",
                    "Market Linkage"
                ]
            )
        ],
        
        workflow_nodes=[
            {"name": "start", "type": "start"},
            {"name": "farm_assessment", "type": "agent", "config": {"task": "assess_farm_conditions"}},
            {"name": "expert_matching", "type": "agent", "config": {"task": "match_agricultural_expert"}},
            {"name": "service_planning", "type": "agent", "config": {"task": "plan_agricultural_service"}},
            {"name": "visit_scheduling", "type": "agent", "config": {"task": "schedule_farm_visit"}},
            {"name": "confirmation", "type": "agent", "config": {"task": "send_service_confirmation"}},
            {"name": "end", "type": "end"}
        ],
        
        workflow_edges=[
            {"from": "start", "to": "farm_assessment"},
            {"from": "farm_assessment", "to": "expert_matching"},
            {"from": "expert_matching", "to": "service_planning"},
            {"from": "service_planning", "to": "visit_scheduling"},
            {"from": "visit_scheduling", "to": "confirmation"},
            {"from": "confirmation", "to": "end"}
        ],
        
        business_hours={
            "monday": {"start": "06:00", "end": "18:00"},
            "tuesday": {"start": "06:00", "end": "18:00"},
            "wednesday": {"start": "06:00", "end": "18:00"},
            "thursday": {"start": "06:00", "end": "18:00"},
            "friday": {"start": "06:00", "end": "18:00"},
            "saturday": {"start": "06:00", "end": "16:00"},
            "sunday": {"start": "08:00", "end": "14:00"}
        },
        
        advance_booking_days=3,
        cancellation_policy="12 hours advance notice required for cancellation",
        
        required_integrations=["weather_api", "sms", "gps"],
        optional_integrations=["payment_gateway", "market_prices", "soil_database"],
        
        supported_regions=["NG", "KE", "ZA", "GH"],
        supported_currencies=["NGN", "KES", "ZAR", "GHS"],
        supported_languages=["en", "ha", "yo", "ig", "sw"]
    )
