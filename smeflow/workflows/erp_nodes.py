"""
ERP Integration Workflow Nodes.

This module contains specialized workflow nodes for ERP integration,
invoice processing, vendor management, and financial reconciliation.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging
from enum import Enum

from .nodes import BaseNode, NodeConfig
from .state import WorkflowState
from ..core.config import get_settings

logger = logging.getLogger(__name__)


class ERPSystemType(str, Enum):
    """Supported ERP system types."""
    SAP = "sap"
    ORACLE = "oracle"
    DYNAMICS = "dynamics"
    HUBSPOT = "hubspot"
    SALESFORCE = "salesforce"
    QUICKBOOKS = "quickbooks"
    SAGE = "sage"
    ODOO = "odoo"
    LOCAL_ERP = "local_erp"
    CUSTOM = "custom"


class InvoiceStatus(str, Enum):
    """Invoice processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    OVERDUE = "overdue"


class ERPAssessmentNode(BaseNode):
    """Node for assessing current ERP system capabilities."""
    
    def __init__(self, config: NodeConfig):
        super().__init__(config)
        self.node_type = "erp_assessment"
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Execute ERP assessment logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with assessment results
        """
        try:
            # Validate required booking data exists
            booking_data = state.data.get("booking_data")
            if not booking_data:
                state.add_error("Missing booking_data in workflow state")
                return state
            
            # Extract ERP system info from booking form
            current_erp = booking_data.get("current_erp_system")
            business_type = booking_data.get("business_type")
            integration_modules = booking_data.get("integration_modules", [])
            
            # Validate required fields
            if not current_erp:
                state.add_error("Missing current_erp_system in booking data")
                return state
            
            # Perform ERP assessment
            assessment_results = {
                "erp_system_type": current_erp,
                "business_type": business_type,
                "required_modules": integration_modules,
                "integration_complexity": self._assess_complexity(current_erp, integration_modules),
                "recommended_approach": self._recommend_approach(current_erp, integration_modules),
                "estimated_timeline": self._estimate_timeline(current_erp, integration_modules),
                "compatibility_score": self._calculate_compatibility(current_erp),
                "assessment_timestamp": datetime.utcnow().isoformat()
            }
            
            # Store assessment results
            state.data["erp_assessment"] = assessment_results
            
            logger.info(f"ERP assessment completed for {current_erp}")
            return state
            
        except Exception as e:
            logger.error(f"ERP assessment failed: {str(e)}")
            state.add_error(f"ERP assessment error: {str(e)}")
            return state
    
    def _assess_complexity(self, erp_system: str, modules: List[str]) -> str:
        """Assess integration complexity based on ERP system and modules."""
        complexity_scores = {
            "SAP": 5, "Oracle ERP": 5, "Microsoft Dynamics": 4,
            "HubSpot": 2, "Salesforce": 3, "QuickBooks": 2,
            "Sage": 3, "Odoo": 3, "Local ERP": 4,
            "Custom System": 5, "Spreadsheets": 1, "No ERP System": 1
        }
        
        base_score = complexity_scores.get(erp_system, 3)
        module_score = len(modules) * 0.5
        total_score = base_score + module_score
        
        if total_score <= 2:
            return "Low"
        elif total_score <= 4:
            return "Medium"
        else:
            return "High"
    
    def _recommend_approach(self, erp_system: str, modules: List[str]) -> str:
        """Recommend integration approach based on system and requirements."""
        if erp_system in ["No ERP System", "Spreadsheets"]:
            return "Fresh Implementation"
        elif erp_system in ["SAP", "Oracle ERP"]:
            return "Enterprise Integration"
        elif len(modules) > 5:
            return "Phased Integration"
        else:
            return "Standard Integration"
    
    def _estimate_timeline(self, erp_system: str, modules: List[str]) -> str:
        """Estimate implementation timeline."""
        base_weeks = {
            "SAP": 8, "Oracle ERP": 8, "Microsoft Dynamics": 6,
            "HubSpot": 2, "Salesforce": 4, "QuickBooks": 2,
            "Sage": 3, "Odoo": 4, "Local ERP": 6,
            "Custom System": 8, "Spreadsheets": 1, "No ERP System": 2
        }
        
        weeks = base_weeks.get(erp_system, 4) + len(modules)
        return f"{weeks} weeks"
    
    def _calculate_compatibility(self, erp_system: str) -> int:
        """Calculate compatibility score (1-10)."""
        scores = {
            "SAP": 9, "Oracle ERP": 9, "Microsoft Dynamics": 8,
            "HubSpot": 10, "Salesforce": 9, "QuickBooks": 8,
            "Sage": 7, "Odoo": 8, "Local ERP": 6,
            "Custom System": 5, "Spreadsheets": 3, "No ERP System": 10
        }
        return scores.get(erp_system, 7)


class InvoiceProcessingNode(BaseNode):
    """Node for automated invoice processing and approval workflows."""
    
    def __init__(self, config: NodeConfig):
        super().__init__(config)
        self.node_type = "invoice_processing"
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Setup automated invoice processing workflows.
        
        Args:
            state: Current workflow state with invoice processing requirements
            
        Returns:
            Updated state with invoice processing configuration
        """
        try:
            # Extract invoice processing requirements
            monthly_volume = state.data.get("booking_data", {}).get("monthly_invoice_volume")
            automation_priorities = state.data.get("booking_data", {}).get("automation_priority", [])
            primary_currency = state.data.get("booking_data", {}).get("primary_currency", "NGN")
            
            # Configure invoice processing workflow
            processing_config = {
                "workflow_rules": self._create_workflow_rules(automation_priorities),
                "approval_matrix": self._create_approval_matrix(monthly_volume),
                "validation_rules": self._create_validation_rules(primary_currency),
                "notification_settings": self._create_notification_settings(),
                "integration_endpoints": self._setup_integration_endpoints(),
                "african_market_optimizations": self._apply_african_optimizations(primary_currency),
                "setup_timestamp": datetime.utcnow().isoformat()
            }
            
            # Store invoice processing configuration
            state.data["invoice_processing"] = processing_config
            
            logger.info(f"Invoice processing configured for {monthly_volume} monthly volume")
            return state
            
        except Exception as e:
            logger.error(f"Invoice processing setup failed: {str(e)}")
            state.add_error(f"Invoice processing error: {str(e)}")
            return state
    
    def _create_workflow_rules(self, priorities: List[str]) -> Dict[str, Any]:
        """Create invoice workflow rules based on priorities."""
        rules = {
            "auto_approval_threshold": 10000,  # Default threshold
            "require_receipt": True,
            "duplicate_detection": True,
            "vendor_validation": True
        }
        
        if "Invoice Approval Workflow" in priorities:
            rules["multi_level_approval"] = True
            rules["approval_routing"] = "dynamic"
        
        if "Tax Calculation" in priorities:
            rules["auto_tax_calculation"] = True
            rules["tax_compliance_check"] = True
        
        return rules
    
    def _create_approval_matrix(self, volume: str) -> Dict[str, Any]:
        """Create approval matrix based on invoice volume."""
        if volume in ["1-50", "51-200"]:
            return {
                "levels": 2,
                "thresholds": [5000, 25000],
                "approvers": ["manager", "finance_head"]
            }
        elif volume in ["100-500", "201-500", "501-1000"]:
            return {
                "levels": 3,
                "thresholds": [10000, 50000, 100000],
                "approvers": ["supervisor", "manager", "finance_head"]
            }
        else:  # 1000+
            return {
                "levels": 4,
                "thresholds": [5000, 25000, 100000, 500000],
                "approvers": ["team_lead", "manager", "finance_head", "cfo"]
            }
    
    def _create_validation_rules(self, currency: str) -> Dict[str, Any]:
        """Create validation rules for invoices."""
        return {
            "required_fields": ["vendor_name", "amount", "date", "description"],
            "currency_validation": currency,
            "amount_limits": self._get_currency_limits(currency),
            "date_validation": {"max_days_old": 90, "future_date_allowed": False},
            "vendor_whitelist_required": True
        }
    
    def _get_currency_limits(self, currency: str) -> Dict[str, float]:
        """Get currency-specific amount limits."""
        limits = {
            "NGN": {"min": 100, "max": 10000000},
            "ZAR": {"min": 10, "max": 1000000},
            "KES": {"min": 100, "max": 5000000},
            "GHS": {"min": 1, "max": 500000},
            "USD": {"min": 1, "max": 100000}
        }
        return limits.get(currency, {"min": 1, "max": 100000})
    
    def _create_notification_settings(self) -> Dict[str, Any]:
        """Create notification settings for invoice processing."""
        return {
            "approval_notifications": True,
            "rejection_notifications": True,
            "overdue_alerts": True,
            "duplicate_warnings": True,
            "channels": ["email", "sms", "whatsapp"]
        }
    
    def _setup_integration_endpoints(self) -> Dict[str, str]:
        """Setup integration endpoints for invoice processing."""
        return {
            "invoice_submission": "/api/v1/invoices/submit",
            "approval_webhook": "/api/v1/invoices/approve",
            "status_update": "/api/v1/invoices/status",
            "payment_confirmation": "/api/v1/invoices/payment"
        }
    
    def _apply_african_optimizations(self, currency: str) -> Dict[str, Any]:
        """Apply African market-specific optimizations."""
        optimizations = {
            "mobile_money_integration": True,
            "local_banking_apis": True,
            "multi_language_support": ["en", "ha", "yo", "ig", "sw"],
            "local_tax_rates": self._get_local_tax_rates(currency),
            "business_hours": "Africa/Lagos",
            "compliance_frameworks": self._get_compliance_frameworks(currency)
        }
        return optimizations
    
    def _get_local_tax_rates(self, currency: str) -> Dict[str, float]:
        """Get local tax rates by currency/region."""
        tax_rates = {
            "NGN": {"vat": 7.5, "withholding": 5.0},
            "ZAR": {"vat": 15.0, "withholding": 20.0},
            "KES": {"vat": 16.0, "withholding": 5.0},
            "GHS": {"vat": 12.5, "withholding": 5.0}
        }
        return tax_rates.get(currency, {"vat": 0.0, "withholding": 0.0})
    
    def _get_compliance_frameworks(self, currency: str) -> List[str]:
        """Get applicable compliance frameworks by currency/region."""
        frameworks = {
            "NGN": ["CBN", "FIRS"],
            "ZAR": ["SARS", "POPIA"],
            "KES": ["KRA", "CBK"],
            "GHS": ["GRA", "BOG"]
        }
        return frameworks.get(currency, [])


class VendorManagementNode(BaseNode):
    """Node for vendor management and payment workflows."""
    
    def __init__(self, config: NodeConfig):
        super().__init__(config)
        self.node_type = "vendor_management"
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Setup vendor management workflows and payment processing.
        
        Args:
            state: Current workflow state with vendor management requirements
            
        Returns:
            Updated state with vendor management configuration
        """
        try:
            # Extract vendor management requirements
            vendor_count = state.data.get("booking_data", {}).get("vendor_count")
            automation_priorities = state.data.get("booking_data", {}).get("automation_priority", [])
            primary_currency = state.data.get("booking_data", {}).get("primary_currency", "NGN")
            
            # Configure vendor management
            vendor_config = {
                "onboarding_workflow": self._create_onboarding_workflow(),
                "payment_processing": self._setup_payment_processing(automation_priorities),
                "vendor_scoring": self._setup_vendor_scoring(vendor_count),
                "compliance_checks": self._setup_compliance_checks(primary_currency),
                "communication_templates": self._create_communication_templates(),
                "african_market_features": self._setup_african_features(primary_currency),
                "setup_timestamp": datetime.utcnow().isoformat()
            }
            
            # Store vendor management configuration
            state.data["vendor_management"] = vendor_config
            
            logger.info(f"Vendor management configured for {vendor_count} vendors")
            return state
            
        except Exception as e:
            logger.error(f"Vendor management setup failed: {str(e)}")
            state.add_error(f"Vendor management error: {str(e)}")
            return state
    
    def _create_onboarding_workflow(self) -> Dict[str, Any]:
        """Create vendor onboarding workflow."""
        return {
            "required_documents": [
                "business_registration",
                "tax_certificate",
                "bank_details",
                "insurance_certificate"
            ],
            "verification_steps": [
                "document_validation",
                "credit_check",
                "reference_verification",
                "compliance_screening"
            ],
            "approval_process": {
                "auto_approve_threshold": 50000,
                "manual_review_required": True,
                "approval_levels": 2
            }
        }
    
    def _setup_payment_processing(self, priorities: List[str]) -> Dict[str, Any]:
        """Setup payment processing configuration."""
        config = {
            "payment_methods": ["bank_transfer", "mobile_money", "check"],
            "payment_terms": ["net_30", "net_60", "immediate"],
            "auto_payment_enabled": "Vendor Payment Processing" in priorities,
            "payment_scheduling": True,
            "bulk_payments": True
        }
        return config
    
    def _setup_vendor_scoring(self, vendor_count: str) -> Dict[str, Any]:
        """Setup vendor scoring and performance tracking."""
        return {
            "scoring_criteria": [
                "payment_history",
                "delivery_performance",
                "quality_metrics",
                "compliance_record"
            ],
            "performance_tracking": True,
            "automated_alerts": True,
            "review_frequency": "monthly" if vendor_count in ["1-10", "11-50"] else "weekly"
        }
    
    def _setup_compliance_checks(self, currency: str) -> Dict[str, Any]:
        """Setup compliance checks for vendors."""
        return {
            "kyc_verification": True,
            "sanctions_screening": True,
            "tax_compliance_check": True,
            "local_regulations": self._get_local_regulations(currency),
            "periodic_reviews": True
        }
    
    def _get_local_regulations(self, currency: str) -> List[str]:
        """Get local regulations by currency/region."""
        regulations = {
            "NGN": ["CAC_registration", "FIRS_compliance", "CBN_guidelines"],
            "ZAR": ["CIPC_registration", "SARS_compliance", "SARB_guidelines"],
            "KES": ["Registrar_of_Companies", "KRA_compliance", "CBK_guidelines"],
            "GHS": ["Registrar_General", "GRA_compliance", "BOG_guidelines"]
        }
        return regulations.get(currency, [])
    
    def _create_communication_templates(self) -> Dict[str, str]:
        """Create communication templates for vendor management."""
        return {
            "onboarding_welcome": "Welcome to our vendor network. Please complete the onboarding process.",
            "payment_notification": "Your payment has been processed and will be credited within 2-3 business days.",
            "document_request": "Please provide the following documents to complete your vendor profile.",
            "performance_review": "Your quarterly performance review is available in the vendor portal."
        }
    
    def _setup_african_features(self, currency: str) -> Dict[str, Any]:
        """Setup African market-specific vendor features."""
        return {
            "mobile_money_payments": True,
            "local_banking_integration": True,
            "multi_language_communication": ["en", "ha", "yo", "ig", "sw"],
            "local_business_hours": "Africa/Lagos",
            "currency_hedging": currency != "USD",
            "local_payment_networks": self._get_payment_networks(currency)
        }
    
    def _get_payment_networks(self, currency: str) -> List[str]:
        """Get local payment networks by currency/region."""
        networks = {
            "NGN": ["Interswitch", "Flutterwave", "Paystack"],
            "ZAR": ["PayFast", "Ozow", "SnapScan"],
            "KES": ["M-Pesa", "Airtel Money", "T-Kash"],
            "GHS": ["MTN Mobile Money", "Vodafone Cash", "AirtelTigo Money"]
        }
        return networks.get(currency, [])


class FinancialReconciliationNode(BaseNode):
    """Node for financial reconciliation and reporting."""
    
    def __init__(self, config: NodeConfig):
        super().__init__(config)
        self.node_type = "financial_reconciliation"
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """
        Setup financial reconciliation and multi-currency reporting.
        
        Args:
            state: Current workflow state with reconciliation requirements
            
        Returns:
            Updated state with reconciliation configuration
        """
        try:
            # Extract reconciliation requirements
            automation_priorities = state.data.get("booking_data", {}).get("automation_priority", [])
            primary_currency = state.data.get("booking_data", {}).get("primary_currency", "NGN")
            compliance_requirements = state.data.get("booking_data", {}).get("compliance_requirements", [])
            
            # Configure financial reconciliation
            reconciliation_config = {
                "reconciliation_rules": self._create_reconciliation_rules(automation_priorities),
                "multi_currency_handling": self._setup_multi_currency(primary_currency),
                "automated_matching": self._setup_automated_matching(),
                "exception_handling": self._setup_exception_handling(),
                "reporting_framework": self._setup_reporting(compliance_requirements),
                "african_compliance": self._setup_african_compliance(primary_currency),
                "setup_timestamp": datetime.utcnow().isoformat()
            }
            
            # Store reconciliation configuration
            state.data["reconciliation_config"] = reconciliation_config
            
            logger.info("Financial reconciliation configured successfully")
            return state
            
        except Exception as e:
            logger.error(f"Financial reconciliation setup failed: {str(e)}")
            state.add_error(f"Reconciliation error: {str(e)}")
            return state
    
    def _create_reconciliation_rules(self, priorities: List[str]) -> Dict[str, Any]:
        """Create reconciliation rules based on priorities."""
        rules = {
            "auto_reconciliation": "Multi-currency Reconciliation" in priorities,
            "tolerance_threshold": 0.01,  # 1 cent tolerance
            "matching_criteria": ["amount", "date", "reference"],
            "frequency": "daily"
        }
        return rules
    
    def _setup_multi_currency(self, primary_currency: str) -> Dict[str, Any]:
        """Setup multi-currency handling."""
        return {
            "primary_currency": primary_currency,
            "supported_currencies": ["NGN", "ZAR", "KES", "GHS", "USD", "EUR"],
            "exchange_rate_provider": "central_bank_api",
            "revaluation_frequency": "monthly",
            "hedging_enabled": True
        }
    
    def _setup_automated_matching(self) -> Dict[str, Any]:
        """Setup automated transaction matching."""
        return {
            "matching_algorithms": ["exact_match", "fuzzy_match", "pattern_match"],
            "confidence_threshold": 0.95,
            "auto_approve_threshold": 0.99,
            "machine_learning_enabled": True
        }
    
    def _setup_exception_handling(self) -> Dict[str, Any]:
        """Setup exception handling for reconciliation."""
        return {
            "exception_types": ["unmatched_transactions", "duplicate_entries", "amount_discrepancies"],
            "escalation_rules": {
                "minor_discrepancies": "auto_resolve",
                "major_discrepancies": "manual_review",
                "critical_issues": "immediate_escalation"
            },
            "notification_channels": ["email", "sms", "dashboard"]
        }
    
    def _setup_reporting(self, compliance_requirements: List[str]) -> Dict[str, Any]:
        """Setup reporting framework based on compliance requirements."""
        reports = {
            "standard_reports": ["cash_flow", "balance_sheet", "income_statement"],
            "reconciliation_reports": ["bank_reconciliation", "vendor_reconciliation", "inter_company"],
            "frequency": "monthly"
        }
        
        # Add compliance-specific reports
        if "IFRS Standards" in compliance_requirements:
            reports["ifrs_reports"] = True
        if "CBN Guidelines (Nigeria)" in compliance_requirements:
            reports["cbn_reports"] = True
        if "SARS Compliance (South Africa)" in compliance_requirements:
            reports["sars_reports"] = True
            
        return reports
    
    def _setup_african_compliance(self, currency: str) -> Dict[str, Any]:
        """Setup African market compliance features."""
        return {
            "local_gaap_support": True,
            "regulatory_reporting": self._get_regulatory_reports(currency),
            "audit_trail": True,
            "data_retention": "7_years",
            "local_banking_formats": True
        }
    
    def _get_regulatory_reports(self, currency: str) -> List[str]:
        """Get regulatory reports by currency/region."""
        reports = {
            "NGN": ["CBN_returns", "FIRS_reports", "NSE_filings"],
            "ZAR": ["SARB_returns", "SARS_reports", "JSE_filings"],
            "KES": ["CBK_returns", "KRA_reports", "NSE_filings"],
            "GHS": ["BOG_returns", "GRA_reports", "GSE_filings"]
        }
        return reports.get(currency, [])


# Export all ERP nodes
__all__ = [
    "ERPSystemType",
    "InvoiceStatus", 
    "ERPAssessmentNode",
    "InvoiceProcessingNode",
    "VendorManagementNode",
    "FinancialReconciliationNode"
]
