"""
Healthcare workflow templates.

This module contains workflow templates for healthcare and medical services.
"""

from .base import IndustryType, FormFieldType, FormField, IndustryTemplate


def create_healthcare_template() -> IndustryTemplate:
    """Create healthcare industry template."""
    return IndustryTemplate(
        industry=IndustryType.HEALTHCARE,
        name="Healthcare Appointment Booking",
        description="Medical appointment booking for clinics, hospitals, and healthcare providers",
        
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
                required=True
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
                    "Emergency"
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
                name="symptoms",
                label="Symptoms/Reason for Visit",
                field_type=FormFieldType.TEXTAREA,
                required=True,
                placeholder="Please describe your symptoms or reason for the visit..."
            ),
            FormField(
                name="insurance_provider",
                label="Insurance Provider",
                field_type=FormFieldType.TEXT,
                required=False
            )
        ],
        
        workflow_nodes=[
            {"name": "start", "type": "start"},
            {"name": "patient_registration", "type": "agent", "config": {"task": "register_patient"}},
            {"name": "appointment_scheduling", "type": "agent", "config": {"task": "schedule_appointment"}},
            {"name": "insurance_verification", "type": "agent", "config": {"task": "verify_insurance"}},
            {"name": "confirmation", "type": "agent", "config": {"task": "send_appointment_confirmation"}},
            {"name": "reminder_setup", "type": "agent", "config": {"task": "setup_appointment_reminders"}},
            {"name": "end", "type": "end"}
        ],
        
        workflow_edges=[
            {"from": "start", "to": "patient_registration"},
            {"from": "patient_registration", "to": "appointment_scheduling"},
            {"from": "appointment_scheduling", "to": "insurance_verification"},
            {"from": "insurance_verification", "to": "confirmation"},
            {"from": "confirmation", "to": "reminder_setup"},
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
        
        advance_booking_days=30,
        cancellation_policy="24 hours advance notice required for cancellation",
        
        required_integrations=["calendar", "sms", "patient_records"],
        optional_integrations=["insurance_system", "payment_gateway", "telemedicine"],
        
        supported_regions=["NG", "KE", "ZA", "GH"],
        supported_currencies=["NGN", "KES", "ZAR", "GHS"],
        supported_languages=["en", "ha", "yo", "ig", "sw"]
    )


def create_education_template() -> IndustryTemplate:
    """Create education industry template."""
    return IndustryTemplate(
        industry=IndustryType.EDUCATION,
        name="Educational Services Booking",
        description="Booking system for tutoring, training, and educational services",
        
        booking_form_fields=[
            FormField(
                name="student_name",
                label="Student Name",
                field_type=FormFieldType.TEXT,
                required=True
            ),
            FormField(
                name="parent_name",
                label="Parent/Guardian Name",
                field_type=FormFieldType.TEXT,
                required=False
            ),
            FormField(
                name="phone",
                label="Contact Phone",
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
                name="subject",
                label="Subject/Course",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "Mathematics",
                    "English Language",
                    "Science",
                    "Computer Programming",
                    "Business Studies",
                    "Languages",
                    "Test Preparation",
                    "Other"
                ]
            ),
            FormField(
                name="student_level",
                label="Student Level",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "Primary School",
                    "Secondary School",
                    "University",
                    "Professional",
                    "Adult Learning"
                ]
            ),
            FormField(
                name="session_type",
                label="Session Type",
                field_type=FormFieldType.SELECT,
                required=True,
                options=["Individual Tutoring", "Group Session", "Online Class", "Workshop"]
            ),
            FormField(
                name="preferred_schedule",
                label="Preferred Schedule",
                field_type=FormFieldType.MULTISELECT,
                required=True,
                options=[
                    "Weekday Mornings",
                    "Weekday Afternoons",
                    "Weekday Evenings",
                    "Weekend Mornings",
                    "Weekend Afternoons"
                ]
            )
        ],
        
        workflow_nodes=[
            {"name": "start", "type": "start"},
            {"name": "student_assessment", "type": "agent", "config": {"task": "assess_student_needs"}},
            {"name": "tutor_matching", "type": "agent", "config": {"task": "match_with_tutor"}},
            {"name": "schedule_coordination", "type": "agent", "config": {"task": "coordinate_schedule"}},
            {"name": "session_setup", "type": "agent", "config": {"task": "setup_learning_session"}},
            {"name": "confirmation", "type": "agent", "config": {"task": "send_session_confirmation"}},
            {"name": "end", "type": "end"}
        ],
        
        workflow_edges=[
            {"from": "start", "to": "student_assessment"},
            {"from": "student_assessment", "to": "tutor_matching"},
            {"from": "tutor_matching", "to": "schedule_coordination"},
            {"from": "schedule_coordination", "to": "session_setup"},
            {"from": "session_setup", "to": "confirmation"},
            {"from": "confirmation", "to": "end"}
        ],
        
        business_hours={
            "monday": {"start": "08:00", "end": "20:00"},
            "tuesday": {"start": "08:00", "end": "20:00"},
            "wednesday": {"start": "08:00", "end": "20:00"},
            "thursday": {"start": "08:00", "end": "20:00"},
            "friday": {"start": "08:00", "end": "20:00"},
            "saturday": {"start": "09:00", "end": "17:00"},
            "sunday": {"start": "10:00", "end": "16:00"}
        },
        
        advance_booking_days=14,
        cancellation_policy="12 hours advance notice required for cancellation",
        
        required_integrations=["calendar", "video_conferencing", "email"],
        optional_integrations=["payment_gateway", "learning_management_system", "progress_tracking"],
        
        supported_regions=["NG", "KE", "ZA", "GH"],
        supported_currencies=["NGN", "KES", "ZAR", "GHS"],
        supported_languages=["en", "ha", "yo", "ig", "sw"]
    )
