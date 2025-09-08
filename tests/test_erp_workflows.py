"""
Unit tests for ERP Integration workflows.

This module contains comprehensive tests for ERP integration templates,
nodes, and African market optimizations.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import uuid

from smeflow.workflows.templates.erp_integration import create_erp_integration_template
from smeflow.workflows.erp_nodes import (
    ERPAssessmentNode,
    InvoiceProcessingNode,
    VendorManagementNode,
    FinancialReconciliationNode,
    ERPSystemType,
    InvoiceStatus
)
from smeflow.workflows.nodes import NodeConfig
from smeflow.workflows.state import WorkflowState
from smeflow.workflows.templates.base import IndustryType, FormFieldType


class TestERPIntegrationTemplate:
    """Test ERP integration template creation and validation."""
    
    def test_create_erp_integration_template(self):
        """Test ERP integration template creation."""
        template = create_erp_integration_template()
        
        # Basic template validation
        assert template.industry == IndustryType.ERP_INTEGRATION
        assert template.name == "ERP Integration & Financial Automation"
        assert "invoice processing" in template.description.lower()
        
        # Form fields validation
        assert len(template.booking_form_fields) == 10
        assert len(template.confirmation_fields) == 3
        
        # Required form fields
        field_names = [field.name for field in template.booking_form_fields]
        assert "company_name" in field_names
        assert "current_erp_system" in field_names
        assert "integration_modules" in field_names
        assert "primary_currency" in field_names
        assert "compliance_requirements" in field_names
        
        # Workflow structure validation
        assert len(template.workflow_nodes) == 13  # start to end
        assert len(template.workflow_edges) == 12
        
        # African market support
        assert "NG" in template.supported_regions
        assert "ZA" in template.supported_regions
        assert "KE" in template.supported_regions
        assert "NGN" in template.supported_currencies
        assert "ZAR" in template.supported_currencies
        assert "en" in template.supported_languages
        assert "ha" in template.supported_languages
    
    def test_erp_template_form_field_types(self):
        """Test form field types are correctly configured."""
        template = create_erp_integration_template()
        
        # Check specific field types
        field_types = {field.name: field.field_type for field in template.booking_form_fields}
        
        assert field_types["company_name"] == FormFieldType.TEXT
        assert field_types["current_erp_system"] == FormFieldType.SELECT
        assert field_types["integration_modules"] == FormFieldType.MULTISELECT
        assert field_types["primary_currency"] == FormFieldType.SELECT
        assert field_types["compliance_requirements"] == FormFieldType.MULTISELECT
    
    def test_erp_template_business_configuration(self):
        """Test business configuration settings."""
        template = create_erp_integration_template()
        
        # Business hours
        assert template.business_hours["timezone"] == "Africa/Lagos"
        assert template.business_hours["monday"]["start"] == "08:00"
        assert template.business_hours["friday"]["end"] == "18:00"
        
        # Integration settings
        assert "erp_system" in template.required_integrations
        assert "financial_system" in template.required_integrations
        assert "banking_apis" in template.optional_integrations
        
        # Policy settings
        assert template.advance_booking_days == 30
        assert "72 hours" in template.cancellation_policy


class TestERPAssessmentNode:
    """Test ERP assessment node functionality."""
    
    @pytest.fixture
    def assessment_node(self):
        """Create ERP assessment node for testing."""
        config = NodeConfig(
            name="test_assessment",
            description="ERP assessment node for testing"
        )
        return ERPAssessmentNode(config)
    
    @pytest.fixture
    def sample_state(self):
        """Create sample workflow state."""
        state = WorkflowState(
            workflow_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4())
        )
        state.data["booking_data"] = {
            "current_erp_system": "SAP",
            "business_type": "Manufacturing",
            "integration_modules": ["Invoice Processing", "Vendor Management"],
            "monthly_invoice_volume": "201-500",
            "primary_currency": "NGN"
        }
        return state
    
    @pytest.mark.asyncio
    async def test_erp_assessment_execution(self, assessment_node, sample_state):
        """Test ERP assessment node execution."""
        result = await assessment_node.execute(sample_state)
        
        # Check assessment results
        assert "erp_assessment" in result.data
        assessment = result.data["erp_assessment"]
        
        assert assessment["erp_system_type"] == "SAP"
        assert assessment["business_type"] == "Manufacturing"
        assert assessment["integration_complexity"] in ["Low", "Medium", "High"]
        assert assessment["recommended_approach"] in ["Fresh Implementation", "Enterprise Integration", "Phased Integration", "Standard Integration"]
        assert "weeks" in assessment["estimated_timeline"]
        assert isinstance(assessment["compatibility_score"], int)
        assert 1 <= assessment["compatibility_score"] <= 10
    
    @pytest.mark.asyncio
    async def test_complexity_assessment(self, assessment_node):
        """Test complexity assessment logic."""
        # High complexity case
        state_high = WorkflowState(
            workflow_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4())
        )
        state_high.data["booking_data"] = {
            "current_erp_system": "SAP",
            "integration_modules": ["Invoice Processing", "Vendor Management", "Financial Reconciliation", "Inventory Management", "HR Payroll", "Customer Management"]
        }
        result = await assessment_node.execute(state_high)
        assert result.data["erp_assessment"]["integration_complexity"] == "High"
        
        # Low complexity case
        state_low = WorkflowState(
            workflow_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4())
        )
        state_low.data["booking_data"] = {
            "current_erp_system": "QuickBooks",
            "integration_modules": ["Invoice Processing"]
        }
        result = await assessment_node.execute(state_low)
        assert result.data["erp_assessment"]["integration_complexity"] in ["Low", "Medium"]
    
    @pytest.mark.asyncio
    async def test_assessment_error_handling(self, assessment_node):
        """Test error handling in assessment node."""
        # Empty state
        empty_state = WorkflowState(
            workflow_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4())
        )
        result = await assessment_node.execute(empty_state)
        assert len(result.errors) > 0


class TestInvoiceProcessingNode:
    """Test invoice processing node functionality."""
    
    @pytest.fixture
    def invoice_node(self):
        """Create invoice processing node for testing."""
        config = NodeConfig(
            name="test_invoice",
            description="Invoice processing node for testing"
        )
        return InvoiceProcessingNode(config)
    
    @pytest.fixture
    def sample_state(self):
        """Create sample workflow state."""
        state = WorkflowState(
            workflow_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4())
        )
        state.data["booking_data"] = {
            "monthly_invoice_volume": "201-500",
            "automation_priority": ["Invoice Approval Workflow", "Tax Calculation"],
            "primary_currency": "NGN"
        }
        return state
    
    @pytest.mark.asyncio
    async def test_invoice_processing_setup(self, invoice_node, sample_state):
        """Test invoice processing configuration."""
        result = await invoice_node.execute(sample_state)
        
        # Check invoice processing configuration
        assert "invoice_processing" in result.data
        config = result.data["invoice_processing"]
        
        assert "workflow_rules" in config
        assert "approval_matrix" in config
        assert "validation_rules" in config
        assert "african_market_optimizations" in config
        
        # Check workflow rules
        rules = config["workflow_rules"]
        assert rules["multi_level_approval"] is True  # Because "Invoice Approval Workflow" in priorities
        assert rules["auto_tax_calculation"] is True  # Because "Tax Calculation" in priorities
    
    @pytest.mark.asyncio
    async def test_approval_matrix_configuration(self, invoice_node):
        """Test approval matrix based on invoice volume."""
        # Medium volume
        state_medium = WorkflowState(
            workflow_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4())
        )
        state_medium.data["booking_data"] = {
            "monthly_invoice_volume": "100-500",
            "automation_priority": [],
            "primary_currency": "NGN"
        }
        result = await invoice_node.execute(state_medium)
        approval_matrix = result.data["invoice_processing"]["approval_matrix"]
        assert approval_matrix["levels"] == 3
        
        # High volume
        state_high = WorkflowState(
            workflow_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4())
        )
        state_high.data["booking_data"] = {
            "monthly_invoice_volume": "1000+",
            "automation_priority": [],
            "primary_currency": "NGN"
        }
        result = await invoice_node.execute(state_high)
        approval_matrix = result.data["invoice_processing"]["approval_matrix"]
        assert approval_matrix["levels"] == 4
    
    @pytest.mark.asyncio
    async def test_african_market_optimizations(self, invoice_node, sample_state):
        """Test African market-specific optimizations."""
        result = await invoice_node.execute(sample_state)
        optimizations = result.data["invoice_processing"]["african_market_optimizations"]
        
        assert optimizations["mobile_money_integration"] is True
        assert optimizations["local_banking_apis"] is True
        assert "en" in optimizations["multi_language_support"]
        assert "ha" in optimizations["multi_language_support"]
        assert optimizations["business_hours"] == "Africa/Lagos"
        
        # Check Nigerian-specific settings
        tax_rates = optimizations["local_tax_rates"]
        assert tax_rates["vat"] == 7.5
        assert tax_rates["withholding"] == 5.0
        
        compliance = optimizations["compliance_frameworks"]
        assert "CBN" in compliance
        assert "FIRS" in compliance


class TestVendorManagementNode:
    """Test vendor management node functionality."""
    
    @pytest.fixture
    def vendor_node(self):
        """Create vendor management node for testing."""
        config = NodeConfig(
            name="test_vendor",
            description="Vendor management node for testing"
        )
        return VendorManagementNode(config)
    
    @pytest.fixture
    def sample_state(self):
        """Create sample workflow state."""
        state = WorkflowState(
            workflow_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4())
        )
        state.data["booking_data"] = {
            "vendor_count": "51-100",
            "automation_priority": ["Vendor Payment Processing"],
            "primary_currency": "ZAR"
        }
        return state
    
    @pytest.mark.asyncio
    async def test_vendor_management_setup(self, vendor_node, sample_state):
        """Test vendor management configuration."""
        result = await vendor_node.execute(sample_state)
        
        # Check configuration
        assert "vendor_management" in result.data
        config = result.data["vendor_management"]
        
        assert "onboarding_workflow" in config
        assert "payment_processing" in config
        assert "vendor_scoring" in config
        assert "compliance_checks" in config
        assert "african_market_features" in config
    
    @pytest.mark.asyncio
    async def test_payment_processing_configuration(self, vendor_node, sample_state):
        """Test payment processing configuration."""
        result = await vendor_node.execute(sample_state)
        payment_config = result.data["vendor_management"]["payment_processing"]
        
        assert payment_config["auto_payment_enabled"] is True  # Because "Vendor Payment Processing" in priorities
        assert "bank_transfer" in payment_config["payment_methods"]
        assert "mobile_money" in payment_config["payment_methods"]
        assert payment_config["bulk_payments"] is True
    
    @pytest.mark.asyncio
    async def test_south_african_optimizations(self, vendor_node, sample_state):
        """Test South African market optimizations."""
        result = await vendor_node.execute(sample_state)
        african_features = result.data["vendor_management"]["african_market_features"]
        
        assert african_features["mobile_money_payments"] is True
        assert african_features["local_banking_integration"] is True
        assert "PayFast" in african_features["local_payment_networks"]
        assert "Ozow" in african_features["local_payment_networks"]
    
    @pytest.mark.asyncio
    async def test_vendor_scoring_setup(self, vendor_node):
        """Test vendor scoring configuration based on vendor count."""
        # Small vendor count
        state_small = WorkflowState(
            workflow_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4())
        )
        state_small.data["booking_data"] = {
            "vendor_count": "1-10",
            "automation_priority": [],
            "primary_currency": "NGN"
        }
        result = await vendor_node.execute(state_small)
        scoring = result.data["vendor_management"]["vendor_scoring"]
        assert scoring["review_frequency"] == "monthly"
        
        # Large vendor count
        state_large = WorkflowState(
            workflow_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4())
        )
        state_large.data["booking_data"] = {
            "vendor_count": "500+",
            "automation_priority": [],
            "primary_currency": "NGN"
        }
        result = await vendor_node.execute(state_large)
        scoring = result.data["vendor_management"]["vendor_scoring"]
        assert scoring["review_frequency"] == "weekly"


class TestFinancialReconciliationNode:
    """Test financial reconciliation node functionality."""
    
    @pytest.fixture
    def reconciliation_node(self):
        """Create financial reconciliation node for testing."""
        config = NodeConfig(
            name="test_reconciliation",
            description="Financial reconciliation node for testing"
        )
        return FinancialReconciliationNode(config)
    
    @pytest.fixture
    def sample_state(self):
        """Create sample workflow state."""
        state = WorkflowState(
            workflow_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4())
        )
        state.data["booking_data"] = {
            "automation_priority": ["Multi-currency Reconciliation"],
            "primary_currency": "KES",
            "compliance_requirements": ["IFRS Standards", "KRA Requirements (Kenya)"]
        }
        return state
    
    @pytest.mark.asyncio
    async def test_reconciliation_setup(self, reconciliation_node, sample_state):
        """Test financial reconciliation configuration."""
        result = await reconciliation_node.execute(sample_state)
        
        # Check configuration
        assert "reconciliation_config" in result.data
        config = result.data["reconciliation_config"]
        
        assert "reconciliation_rules" in config
        assert "multi_currency_handling" in config
        assert "automated_matching" in config
        assert "reporting_framework" in config
        assert "african_compliance" in config
    
    @pytest.mark.asyncio
    async def test_multi_currency_handling(self, reconciliation_node, sample_state):
        """Test multi-currency configuration."""
        result = await reconciliation_node.execute(sample_state)
        multi_currency = result.data["reconciliation_config"]["multi_currency_handling"]
        
        assert multi_currency["primary_currency"] == "KES"
        assert "NGN" in multi_currency["supported_currencies"]
        assert "USD" in multi_currency["supported_currencies"]
        assert multi_currency["exchange_rate_provider"] == "central_bank_api"
        assert multi_currency["hedging_enabled"] is True
    
    @pytest.mark.asyncio
    async def test_compliance_reporting(self, reconciliation_node, sample_state):
        """Test compliance-specific reporting configuration."""
        result = await reconciliation_node.execute(sample_state)
        reporting = result.data["reconciliation_config"]["reporting_framework"]
        
        # Check IFRS compliance
        assert reporting["ifrs_reports"] is True
        
        # Check standard reports
        assert "cash_flow" in reporting["standard_reports"]
        assert "balance_sheet" in reporting["standard_reports"]
        assert reporting["frequency"] == "monthly"
    
    @pytest.mark.asyncio
    async def test_kenyan_compliance_features(self, reconciliation_node, sample_state):
        """Test Kenyan market compliance features."""
        result = await reconciliation_node.execute(sample_state)
        african_compliance = result.data["reconciliation_config"]["african_compliance"]
        
        assert african_compliance["local_gaap_support"] is True
        assert african_compliance["audit_trail"] is True
        assert african_compliance["data_retention"] == "7_years"
        
        # Check Kenyan regulatory reports
        regulatory_reports = african_compliance["regulatory_reporting"]
        assert "CBK_returns" in regulatory_reports
        assert "KRA_reports" in regulatory_reports


class TestERPEnums:
    """Test ERP-related enums."""
    
    def test_erp_system_type_enum(self):
        """Test ERP system type enum values."""
        assert ERPSystemType.SAP == "sap"
        assert ERPSystemType.ORACLE == "oracle"
        assert ERPSystemType.HUBSPOT == "hubspot"
        assert ERPSystemType.QUICKBOOKS == "quickbooks"
        assert ERPSystemType.LOCAL_ERP == "local_erp"
    
    def test_invoice_status_enum(self):
        """Test invoice status enum values."""
        assert InvoiceStatus.PENDING == "pending"
        assert InvoiceStatus.APPROVED == "approved"
        assert InvoiceStatus.REJECTED == "rejected"
        assert InvoiceStatus.PAID == "paid"
        assert InvoiceStatus.OVERDUE == "overdue"


class TestERPIntegration:
    """Test end-to-end ERP integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_nigerian_sme_integration(self):
        """Test complete Nigerian SME ERP integration scenario."""
        # Create template
        template = create_erp_integration_template()
        
        # Simulate Nigerian SME booking data
        state = WorkflowState(
            workflow_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4())
        )
        state.data["booking_data"] = {
            "company_name": "Lagos Manufacturing Ltd",
            "business_type": "Manufacturing",
            "current_erp_system": "Spreadsheets",
            "integration_modules": ["Invoice Processing", "Vendor Management"],
            "monthly_invoice_volume": "51-200",
            "vendor_count": "11-50",
            "primary_currency": "NGN",
            "compliance_requirements": ["CBN Guidelines (Nigeria)", "Local Tax Laws"],
            "automation_priority": ["Invoice Approval Workflow", "Tax Calculation"]
        }
        
        # Test assessment node
        assessment_config = NodeConfig(name="assessment", description="ERP assessment node")
        assessment_node = ERPAssessmentNode(assessment_config)
        state = await assessment_node.execute(state)
        
        assert state.data["erp_assessment"]["erp_system_type"] == "Spreadsheets"
        assert state.data["erp_assessment"]["recommended_approach"] == "Fresh Implementation"
        
        # Test invoice processing node
        invoice_config = NodeConfig(name="invoice", description="Invoice processing node")
        invoice_node = InvoiceProcessingNode(invoice_config)
        state = await invoice_node.execute(state)
        
        # Verify Nigerian optimizations
        optimizations = state.data["invoice_processing"]["african_market_optimizations"]
        assert optimizations["local_tax_rates"]["vat"] == 7.5
        assert "CBN" in optimizations["compliance_frameworks"]
        
        # Test vendor management node
        vendor_config = NodeConfig(name="vendor", description="Vendor management node")
        vendor_node = VendorManagementNode(vendor_config)
        state = await vendor_node.execute(state)
        
        # Verify Nigerian payment networks
        payment_networks = state.data["vendor_management"]["african_market_features"]["local_payment_networks"]
        assert "Interswitch" in payment_networks
        assert "Flutterwave" in payment_networks
    
    @pytest.mark.asyncio
    async def test_south_african_enterprise_integration(self):
        """Test South African enterprise ERP integration scenario."""
        state = WorkflowState(
            workflow_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4())
        )
        state.data["booking_data"] = {
            "company_name": "Cape Town Enterprises",
            "business_type": "Financial Services",
            "current_erp_system": "SAP",
            "integration_modules": ["Invoice Processing", "Vendor Management", "Financial Reconciliation", "Tax Compliance"],
            "monthly_invoice_volume": "1000+",
            "vendor_count": "500+",
            "primary_currency": "ZAR",
            "compliance_requirements": ["SARS Compliance (South Africa)", "IFRS Standards"],
            "automation_priority": ["Multi-currency Reconciliation", "Audit Trail Generation"]
        }
        
        # Test reconciliation node
        reconciliation_config = NodeConfig(name="reconciliation", description="Financial reconciliation node")
        reconciliation_node = FinancialReconciliationNode(reconciliation_config)
        state = await reconciliation_node.execute(state)
        
        # Verify South African compliance
        african_compliance = state.data["reconciliation_config"]["african_compliance"]
        regulatory_reports = african_compliance["regulatory_reporting"]
        assert "SARB_returns" in regulatory_reports
        assert "SARS_reports" in regulatory_reports
        
        # Verify multi-currency handling
        multi_currency = state.data["reconciliation_config"]["multi_currency_handling"]
        assert multi_currency["primary_currency"] == "ZAR"
        assert multi_currency["hedging_enabled"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
