"""
ERP integration workflow templates.

This module contains workflow templates for ERP integration and financial automation.
"""

from .base import IndustryType, FormFieldType, FormField, IndustryTemplate


def create_erp_integration_template() -> IndustryTemplate:
    """Create ERP integration template for invoice processing and vendor management."""
    return IndustryTemplate(
        industry=IndustryType.ERP_INTEGRATION,
        name="ERP Integration & Financial Automation",
        description="Comprehensive ERP integration workflow for invoice processing, vendor management, and financial reconciliation with African market optimizations",
        
        booking_form_fields=[
            FormField(
                name="company_name",
                label="Company Name",
                field_type=FormFieldType.TEXT,
                required=True,
                placeholder="Enter your company name"
            ),
            FormField(
                name="business_type",
                label="Business Type",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "Manufacturing", "Retail/E-commerce", "Services", "Distribution",
                    "Construction", "Healthcare", "Education", "Agriculture",
                    "Technology", "Financial Services", "Real Estate"
                ]
            ),
            FormField(
                name="current_erp_system",
                label="Current ERP System",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "SAP", "Oracle ERP", "Microsoft Dynamics", "HubSpot",
                    "Salesforce", "QuickBooks", "Sage", "Odoo", "Local ERP",
                    "Custom System", "Spreadsheets", "No ERP System"
                ]
            ),
            FormField(
                name="integration_modules",
                label="Integration Modules Required",
                field_type=FormFieldType.MULTISELECT,
                required=True,
                options=[
                    "Invoice Processing", "Vendor Management", "Purchase Orders",
                    "Financial Reconciliation", "Inventory Management", "HR Payroll",
                    "Customer Management", "Reporting & Analytics", "Tax Compliance"
                ]
            ),
            FormField(
                name="monthly_invoice_volume",
                label="Monthly Invoice Volume",
                field_type=FormFieldType.SELECT,
                required=True,
                options=["1-50", "51-200", "201-500", "501-1000", "1000+"]
            ),
            FormField(
                name="vendor_count",
                label="Number of Active Vendors",
                field_type=FormFieldType.SELECT,
                required=True,
                options=["1-10", "11-50", "51-100", "101-500", "500+"]
            ),
            FormField(
                name="primary_currency",
                label="Primary Business Currency",
                field_type=FormFieldType.SELECT,
                required=True,
                options=["NGN", "ZAR", "KES", "GHS", "UGX", "TZS", "RWF", "ETB", "USD", "EUR"]
            ),
            FormField(
                name="compliance_requirements",
                label="Financial Compliance Requirements",
                field_type=FormFieldType.MULTISELECT,
                required=True,
                options=[
                    "CBN Guidelines (Nigeria)", "SARS Compliance (South Africa)",
                    "KRA Requirements (Kenya)", "IFRS Standards", "Local Tax Laws",
                    "VAT/GST Compliance", "Audit Trail Requirements", "Multi-currency Reporting"
                ]
            ),
            FormField(
                name="automation_priority",
                label="Automation Priority Areas",
                field_type=FormFieldType.MULTISELECT,
                required=True,
                options=[
                    "Invoice Approval Workflow", "Vendor Payment Processing",
                    "Purchase Order Automation", "Expense Management",
                    "Financial Reporting", "Tax Calculation", "Audit Trail Generation",
                    "Multi-currency Reconciliation"
                ]
            ),
            FormField(
                name="integration_budget",
                label="Integration Budget Range (Annual)",
                field_type=FormFieldType.SELECT,
                required=True,
                options=[
                    "Under $5,000", "$5,000 - $15,000", "$15,000 - $50,000",
                    "$50,000 - $100,000", "Over $100,000"
                ]
            )
        ],
        
        confirmation_fields=[
            FormField(
                name="technical_contact",
                label="Technical Contact Email",
                field_type=FormFieldType.EMAIL,
                required=True,
                placeholder="Enter technical contact email"
            ),
            FormField(
                name="implementation_timeline",
                label="Preferred Implementation Timeline",
                field_type=FormFieldType.SELECT,
                required=True,
                options=["Immediate (1-2 weeks)", "Standard (3-4 weeks)", "Extended (6-8 weeks)", "Phased Approach"]
            ),
            FormField(
                name="data_migration_scope",
                label="Data Migration Scope",
                field_type=FormFieldType.SELECT,
                required=True,
                options=["Historical Data (1 year)", "Historical Data (3 years)", "Full Historical Data", "New Data Only"]
            )
        ],
        
        workflow_nodes=[
            {"name": "start", "type": "start"},
            {"name": "erp_assessment", "type": "agent", "config": {"task": "assess_current_erp_system"}},
            {"name": "integration_planning", "type": "agent", "config": {"task": "plan_erp_integration_strategy"}},
            {"name": "connector_setup", "type": "agent", "config": {"task": "configure_erp_connectors"}},
            {"name": "invoice_automation", "type": "agent", "config": {"task": "setup_invoice_processing"}},
            {"name": "vendor_management", "type": "agent", "config": {"task": "configure_vendor_workflows"}},
            {"name": "financial_reconciliation", "type": "agent", "config": {"task": "setup_financial_reconciliation"}},
            {"name": "compliance_monitoring", "type": "agent", "config": {"task": "configure_compliance_tracking"}},
            {"name": "reporting_setup", "type": "agent", "config": {"task": "setup_automated_reporting"}},
            {"name": "data_migration", "type": "agent", "config": {"task": "migrate_historical_data"}},
            {"name": "testing_validation", "type": "agent", "config": {"task": "test_erp_integration"}},
            {"name": "go_live", "type": "agent", "config": {"task": "activate_erp_integration"}},
            {"name": "end", "type": "end"}
        ],
        
        workflow_edges=[
            {"from": "start", "to": "erp_assessment"},
            {"from": "erp_assessment", "to": "integration_planning"},
            {"from": "integration_planning", "to": "connector_setup"},
            {"from": "connector_setup", "to": "invoice_automation"},
            {"from": "invoice_automation", "to": "vendor_management"},
            {"from": "vendor_management", "to": "financial_reconciliation"},
            {"from": "financial_reconciliation", "to": "compliance_monitoring"},
            {"from": "compliance_monitoring", "to": "reporting_setup"},
            {"from": "reporting_setup", "to": "data_migration"},
            {"from": "data_migration", "to": "testing_validation"},
            {"from": "testing_validation", "to": "go_live"},
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
        
        advance_booking_days=30,
        cancellation_policy="ERP integration changes require 72 hours advance notice. Critical financial processes can be addressed immediately with proper authorization.",
        
        notification_settings={
            "email_notifications": True,
            "sms_notifications": True,
            "whatsapp_notifications": True,
            "invoice_alerts": True,
            "vendor_notifications": True,
            "compliance_reminders": True,
            "financial_reports": True
        },
        
        required_integrations=["erp_system", "financial_system", "email", "sms"],
        optional_integrations=[
            "whatsapp", "banking_apis", "tax_systems", "audit_tools",
            "reporting_platform", "document_management", "workflow_automation"
        ],
        
        supported_regions=["NG", "ZA", "KE", "GH", "UG", "TZ", "RW", "ET"],
        supported_currencies=["NGN", "ZAR", "KES", "GHS", "UGX", "TZS", "RWF", "ETB"],
        supported_languages=["en", "ha", "yo", "ig", "sw", "af", "zu", "am", "fr"]
    )
