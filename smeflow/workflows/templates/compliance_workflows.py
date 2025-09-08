"""
Compliance workflows templates.

This module contains workflow templates for compliance management and regulatory automation.
"""

from .base import IndustryType, FormFieldType, FormField, IndustryTemplate


def create_compliance_workflows_template() -> IndustryTemplate:
    """Create compliance workflows template for regulatory compliance automation."""
    return IndustryTemplate(
        industry=IndustryType.COMPLIANCE_WORKFLOWS,
        name="Compliance & Regulatory Automation",
        description="Comprehensive compliance workflow for regulatory adherence with African market optimizations",
        
        booking_form_fields=[
            FormField(
                name="organization_name",
                label="Organization Name",
                field_type=FormFieldType.TEXT,
                required=True,
                placeholder="Enter your organization name"
            ),
            FormField(
                name="industry_type",
                label="Industry Type",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "Financial Services", "Healthcare", "Technology", "Manufacturing",
                    "Retail", "Education", "Government", "Non-profit", "Energy",
                    "Telecommunications", "Transportation", "Real Estate"
                ]
            ),
            FormField(
                name="compliance_frameworks",
                label="Required Compliance Frameworks",
                field_type=FormFieldType.MULTISELECT,
                required=True,
                options=[
                    "GDPR (General Data Protection Regulation)",
                    "POPIA (Protection of Personal Information Act - South Africa)",
                    "CBN (Central Bank of Nigeria Guidelines)",
                    "ISO 27001 (Information Security)",
                    "SOC 2 (Service Organization Control)",
                    "HIPAA (Healthcare)",
                    "PCI DSS (Payment Card Industry)"
                ]
            ),
            FormField(
                name="business_sector",
                label="Business Sector",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "Banking & Finance", "Insurance", "Healthcare", "E-commerce",
                    "SaaS/Technology", "Manufacturing", "Government", "Education",
                    "Non-profit", "Consulting"
                ]
            ),
            FormField(
                name="data_processing_activities",
                label="Data Processing Activities",
                field_type=FormFieldType.MULTISELECT,
                required=True,
                options=[
                    "Customer Data Collection", "Payment Processing", "Employee Records",
                    "Marketing Analytics", "Third-party Integrations", "Cloud Storage",
                    "International Data Transfers", "Automated Decision Making"
                ]
            ),
            FormField(
                name="reporting_frequency",
                label="Compliance Reporting Frequency",
                field_type=FormFieldType.SELECT,
                required=True,
                options=["Monthly", "Quarterly", "Semi-annually", "Annually", "As Required"]
            ),
            FormField(
                name="compliance_budget",
                label="Annual Compliance Budget",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "Under $10,000", "$10,000 - $50,000", "$50,000 - $100,000",
                    "$100,000 - $250,000", "Over $250,000"
                ]
            ),
            FormField(
                name="current_compliance_tools",
                label="Current Compliance Tools",
                field_type=FormFieldType.MULTISELECT,
                required=False,
                options=[
                    "Manual Processes", "Spreadsheets", "GRC Platform", "Legal Software",
                    "Audit Management System", "Risk Management Tool", "Custom Solution", "None"
                ]
            ),
            FormField(
                name="priority_areas",
                label="Priority Compliance Areas",
                field_type=FormFieldType.MULTISELECT,
                required=True,
                options=[
                    "Data Privacy", "Financial Regulations", "Operational Risk",
                    "Cybersecurity", "Audit Management", "Policy Management",
                    "Training & Awareness", "Incident Response"
                ]
            )
        ],
        
        confirmation_fields=[
            FormField(
                name="compliance_officer_contact",
                label="Compliance Officer Contact",
                field_type=FormFieldType.EMAIL,
                required=True,
                placeholder="Enter compliance officer email"
            ),
            FormField(
                name="implementation_timeline",
                label="Implementation Timeline",
                field_type=FormFieldType.SELECT,
                required=True,
                options=["Immediate (2-4 weeks)", "Standard (6-8 weeks)", "Extended (3-4 months)", "Phased Approach"]
            ),
            FormField(
                name="data_residency_preference",
                label="Data Residency Preference",
                field_type=FormFieldType.SELECT,
                required=True,
                options=["Local (African) Data Centers", "Global with Local Backup", "No Preference"]
            )
        ],
        
        workflow_nodes=[
            {"name": "start", "type": "start"},
            {"name": "compliance_assessment", "type": "agent", "config": {"task": "assess_current_compliance_posture"}},
            {"name": "regulatory_mapping", "type": "agent", "config": {"task": "map_applicable_regulations"}},
            {"name": "gap_analysis", "type": "agent", "config": {"task": "identify_compliance_gaps"}},
            {"name": "policy_generation", "type": "agent", "config": {"task": "generate_compliance_policies"}},
            {"name": "audit_trail_setup", "type": "agent", "config": {"task": "setup_audit_trail_system"}},
            {"name": "monitoring_implementation", "type": "agent", "config": {"task": "implement_compliance_monitoring"}},
            {"name": "risk_assessment", "type": "agent", "config": {"task": "conduct_compliance_risk_assessment"}},
            {"name": "reporting_setup", "type": "agent", "config": {"task": "setup_compliance_reporting"}},
            {"name": "training_deployment", "type": "agent", "config": {"task": "deploy_compliance_training"}},
            {"name": "integration_testing", "type": "agent", "config": {"task": "test_compliance_integrations"}},
            {"name": "go_live", "type": "agent", "config": {"task": "activate_compliance_system"}},
            {"name": "end", "type": "end"}
        ],
        
        workflow_edges=[
            {"from": "start", "to": "compliance_assessment"},
            {"from": "compliance_assessment", "to": "regulatory_mapping"},
            {"from": "regulatory_mapping", "to": "gap_analysis"},
            {"from": "gap_analysis", "to": "policy_generation"},
            {"from": "policy_generation", "to": "audit_trail_setup"},
            {"from": "audit_trail_setup", "to": "monitoring_implementation"},
            {"from": "monitoring_implementation", "to": "risk_assessment"},
            {"from": "risk_assessment", "to": "reporting_setup"},
            {"from": "reporting_setup", "to": "training_deployment"},
            {"from": "training_deployment", "to": "integration_testing"},
            {"from": "integration_testing", "to": "go_live"},
            {"from": "go_live", "to": "end"}
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
        
        advance_booking_days=14,
        cancellation_policy="Compliance workflow changes require 48 hours advance notice. Emergency compliance issues can be addressed immediately with proper authorization.",
        
        notification_settings={
            "email_notifications": True,
            "sms_notifications": True,
            "whatsapp_notifications": True,
            "compliance_alerts": True,
            "audit_reminders": True,
            "regulatory_updates": True,
            "risk_notifications": True
        },
        
        required_integrations=["audit_system", "compliance_platform", "email", "sms"],
        optional_integrations=[
            "whatsapp", "government_apis", "grc_platform", "training_platform",
            "risk_management", "policy_management", "document_management"
        ],
        
        supported_regions=["NG", "ZA", "KE", "GH", "UG", "TZ", "RW", "ET"],
        supported_currencies=["NGN", "ZAR", "KES", "GHS", "UGX", "TZS", "RWF", "ETB"],
        supported_languages=["en", "ha", "yo", "ig", "sw", "af", "zu", "am", "fr"]
    )
