"""
Unit tests for WORKFLOW-005 Compliance Workflows.

Tests compliance workflow template, nodes, and African market optimizations
for GDPR, POPIA, and CBN regulatory compliance.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from smeflow.workflows.templates import IndustryTemplateFactory, IndustryType
from smeflow.workflows.compliance_nodes import (
    ComplianceAssessmentNode, AuditTrailNode, ComplianceReportingNode,
    RiskAssessmentNode, ComplianceMonitoringNode, PolicyGenerationNode,
    ComplianceIntegrationNode, AfricanMarketComplianceHelper,
    ComplianceFramework, RiskLevel
)
from smeflow.workflows.state import WorkflowState


class TestComplianceWorkflowTemplate:
    """Test compliance workflow template creation and validation."""
    
    def test_compliance_workflows_enum_exists(self):
        """Test that COMPLIANCE_WORKFLOWS enum value exists."""
        assert hasattr(IndustryType, 'COMPLIANCE_WORKFLOWS')
        assert IndustryType.COMPLIANCE_WORKFLOWS == "compliance_workflows"
    
    def test_create_compliance_workflows_template(self):
        """Test compliance workflows template creation."""
        template = IndustryTemplateFactory.create_compliance_workflows_template()
        
        assert template.industry == IndustryType.COMPLIANCE_WORKFLOWS
        assert template.name == "Regulatory Compliance & Audit Management"
        assert template.description is not None
        assert len(template.booking_form_fields) > 0
        assert len(template.workflow_nodes) > 0
        assert len(template.workflow_edges) > 0
    
    def test_compliance_template_form_fields(self):
        """Test compliance template form fields structure."""
        template = IndustryTemplateFactory.create_compliance_workflows_template()
        
        # Check required form fields
        field_names = [field.name for field in template.booking_form_fields]
        
        required_fields = [
            "organization_name", "organization_type", "employee_count",
            "compliance_frameworks", "business_sector", "data_processing_activities",
            "reporting_frequency", "budget_range"
        ]
        
        for required_field in required_fields:
            assert required_field in field_names
    
    def test_compliance_template_workflow_nodes(self):
        """Test compliance template workflow nodes."""
        template = IndustryTemplateFactory.create_compliance_workflows_template()
        
        node_names = [node["name"] for node in template.workflow_nodes]
        
        expected_nodes = [
            "start", "compliance_assessment", "regulatory_mapping",
            "gap_analysis", "policy_generation", "audit_trail_setup",
            "compliance_monitoring", "risk_assessment", "compliance_reporting",
            "compliance_training", "compliance_integration", "compliance_testing",
            "go_live", "end"
        ]
        
        for expected_node in expected_nodes:
            assert expected_node in node_names
    
    def test_compliance_template_african_market_support(self):
        """Test African market compliance optimizations."""
        template = IndustryTemplateFactory.create_compliance_workflows_template()
        
        # Check supported regions
        assert "NG" in template.supported_regions  # Nigeria - CBN
        assert "ZA" in template.supported_regions  # South Africa - POPIA
        assert "KE" in template.supported_regions  # Kenya
        
        # Check supported currencies
        assert "KES" in template.supported_currencies
        assert "NGN" in template.supported_currencies
        assert "ZAR" in template.supported_currencies
        
        # Check multilingual support
        assert "en" in template.supported_languages
        assert "ha" in template.supported_languages  # Hausa
        assert "yo" in template.supported_languages  # Yoruba
        assert "sw" in template.supported_languages  # Swahili
        assert "af" in template.supported_languages  # Afrikaans


class TestComplianceAssessmentNode:
    """Test compliance assessment node functionality."""
    
    @pytest.fixture
    def assessment_node(self):
        """Create compliance assessment node for testing."""
        return ComplianceAssessmentNode()
    
    @pytest.fixture
    def mock_state(self):
        """Create mock workflow state."""
        state = WorkflowState(
            workflow_id=uuid.uuid4(),
            tenant_id="test-tenant",
            region="NG"
        )
        state.data = {
            "organization_info": {
                "name": "Test SME Ltd",
                "employee_count": 50,
                "sector": "fintech"
            },
            "compliance_frameworks": ["gdpr", "cbn", "popia"]
        }
        return state
    
    @pytest.mark.asyncio
    async def test_compliance_assessment_execution(self, assessment_node, mock_state):
        """Test compliance assessment node execution."""
        result_state = await assessment_node.execute(mock_state)
        
        assert "compliance_status" in result_state.data
        assert "assessment_results" in result_state.data
        assert result_state.data["compliance_status"] == "assessed"
        
        assessment = result_state.data["assessment_results"]
        assert "assessment_id" in assessment
        assert "overall_score" in assessment
        assert "framework_scores" in assessment
        assert "gaps_identified" in assessment
        assert "recommendations" in assessment
    
    @pytest.mark.asyncio
    async def test_framework_assessment_cbn_nigeria(self, assessment_node, mock_state):
        """Test CBN framework assessment for Nigerian region."""
        mock_state.region = "NG"
        mock_state.data["compliance_frameworks"] = ["cbn"]
        
        result_state = await assessment_node.execute(mock_state)
        assessment = result_state.data["assessment_results"]
        
        assert "cbn" in assessment["framework_scores"]
        assert assessment["framework_scores"]["cbn"] > 0
    
    @pytest.mark.asyncio
    async def test_framework_assessment_popia_south_africa(self, assessment_node, mock_state):
        """Test POPIA framework assessment for South African region."""
        mock_state.region = "ZA"
        mock_state.data["compliance_frameworks"] = ["popia"]
        
        result_state = await assessment_node.execute(mock_state)
        assessment = result_state.data["assessment_results"]
        
        assert "popia" in assessment["framework_scores"]
        assert assessment["framework_scores"]["popia"] > 0


class TestAuditTrailNode:
    """Test audit trail setup node functionality."""
    
    @pytest.fixture
    def audit_node(self):
        """Create audit trail node for testing."""
        return AuditTrailNode()
    
    @pytest.fixture
    def mock_state_with_assessment(self):
        """Create mock state with assessment results."""
        state = WorkflowState(
            workflow_id=uuid.uuid4(),
            tenant_id="test-tenant",
            region="NG"
        )
        state.data = {
            "assessment_results": {
                "frameworks_assessed": ["gdpr", "cbn", "popia"],
                "overall_score": 75
            }
        }
        return state
    
    @pytest.mark.asyncio
    async def test_audit_trail_setup(self, audit_node, mock_state_with_assessment):
        """Test audit trail configuration setup."""
        result_state = await audit_node.execute(mock_state_with_assessment)
        
        assert "audit_config" in result_state.data
        assert "logging_setup" in result_state.data
        
        audit_config = result_state.data["audit_config"]
        assert audit_config["retention_period_days"] == 2555  # 7 years
        assert audit_config["encryption_enabled"] is True
        assert audit_config["immutable_storage"] is True
        assert len(audit_config["log_categories"]) > 0
    
    @pytest.mark.asyncio
    async def test_gdpr_audit_categories(self, audit_node, mock_state_with_assessment):
        """Test GDPR-specific audit log categories."""
        result_state = await audit_node.execute(mock_state_with_assessment)
        audit_config = result_state.data["audit_config"]
        
        gdpr_categories = [
            "data_access", "data_modification", "data_deletion",
            "consent_changes", "data_export", "right_to_be_forgotten"
        ]
        
        for category in gdpr_categories:
            assert category in audit_config["log_categories"]


class TestComplianceReportingNode:
    """Test compliance reporting node functionality."""
    
    @pytest.fixture
    def reporting_node(self):
        """Create compliance reporting node for testing."""
        return ComplianceReportingNode()
    
    @pytest.fixture
    def mock_state_with_audit(self):
        """Create mock state with audit configuration."""
        state = WorkflowState(
            workflow_id=uuid.uuid4(),
            tenant_id="test-tenant",
            region="ZA"
        )
        state.data = {
            "assessment_results": {
                "frameworks_assessed": ["gdpr", "popia"],
                "overall_score": 80
            },
            "audit_config": {
                "log_categories": ["data_access", "security_incidents"]
            }
        }
        return state
    
    @pytest.mark.asyncio
    async def test_compliance_reporting_setup(self, reporting_node, mock_state_with_audit):
        """Test compliance reporting configuration."""
        result_state = await reporting_node.execute(mock_state_with_audit)
        
        assert "reporting_config" in result_state.data
        assert "report_schedule" in result_state.data
        
        reporting_config = result_state.data["reporting_config"]
        assert reporting_config["region"] == "ZA"
        assert reporting_config["encryption_required"] is True
        assert len(reporting_config["reports"]) > 0
    
    @pytest.mark.asyncio
    async def test_popia_reporting_south_africa(self, reporting_node, mock_state_with_audit):
        """Test POPIA-specific reporting for South Africa."""
        result_state = await reporting_node.execute(mock_state_with_audit)
        reporting_config = result_state.data["reporting_config"]
        
        # Check for POPIA-specific report
        popia_reports = [
            report for report in reporting_config["reports"]
            if report["type"] == "popia_compliance_report"
        ]
        assert len(popia_reports) > 0
        
        popia_report = popia_reports[0]
        assert popia_report["frequency"] == "quarterly"
        assert "information_officer@organization.com" in popia_report["recipients"]


class TestRiskAssessmentNode:
    """Test risk assessment node functionality."""
    
    @pytest.fixture
    def risk_node(self):
        """Create risk assessment node for testing."""
        return RiskAssessmentNode()
    
    @pytest.fixture
    def mock_state_with_compliance_data(self):
        """Create mock state with compliance assessment and audit config."""
        state = WorkflowState(
            workflow_id=uuid.uuid4(),
            tenant_id="test-tenant",
            region="NG"
        )
        state.data = {
            "assessment_results": {
                "overall_score": 65,
                "framework_scores": {"gdpr": 70, "cbn": 60},
                "gaps_identified": [
                    {"framework": "cbn", "score": 60, "risk_level": "high"}
                ]
            },
            "audit_config": {
                "encryption_enabled": True,
                "immutable_storage": True
            }
        }
        return state
    
    @pytest.mark.asyncio
    async def test_risk_assessment_execution(self, risk_node, mock_state_with_compliance_data):
        """Test risk assessment execution."""
        result_state = await risk_node.execute(mock_state_with_compliance_data)
        
        assert "risk_profile" in result_state.data
        assert "mitigation_plan" in result_state.data
        
        risk_profile = result_state.data["risk_profile"]
        assert "overall_risk_score" in risk_profile
        assert "risk_categories" in risk_profile
        assert "critical_risks" in risk_profile
    
    @pytest.mark.asyncio
    async def test_risk_categories_assessment(self, risk_node, mock_state_with_compliance_data):
        """Test risk categories assessment."""
        result_state = await risk_node.execute(mock_state_with_compliance_data)
        risk_profile = result_state.data["risk_profile"]
        
        expected_categories = [
            "data_privacy", "regulatory_compliance", "operational_security",
            "financial_impact", "reputational_risk"
        ]
        
        for category in expected_categories:
            assert category in risk_profile["risk_categories"]
            assert isinstance(risk_profile["risk_categories"][category], (int, float))


class TestComplianceMonitoringNode:
    """Test compliance monitoring node functionality."""
    
    @pytest.fixture
    def monitoring_node(self):
        """Create compliance monitoring node for testing."""
        return ComplianceMonitoringNode()
    
    @pytest.fixture
    def mock_state_with_risk_profile(self):
        """Create mock state with risk profile."""
        state = WorkflowState(
            workflow_id=uuid.uuid4(),
            tenant_id="test-tenant",
            region="NG"
        )
        state.data = {
            "risk_profile": {
                "overall_risk_score": 7.5,
                "critical_risks": [
                    {"category": "regulatory_compliance", "score": 8.0, "level": "high"}
                ]
            },
            "audit_config": {
                "log_categories": ["data_access", "security_incidents"]
            }
        }
        return state
    
    @pytest.mark.asyncio
    async def test_monitoring_setup(self, monitoring_node, mock_state_with_risk_profile):
        """Test compliance monitoring setup."""
        result_state = await monitoring_node.execute(mock_state_with_risk_profile)
        
        assert "monitoring_config" in result_state.data
        assert "alert_rules" in result_state.data
        
        monitoring_config = result_state.data["monitoring_config"]
        assert monitoring_config["monitoring_enabled"] is True
        assert monitoring_config["real_time_alerts"] is True
        assert monitoring_config["dashboard_enabled"] is True
    
    @pytest.mark.asyncio
    async def test_nigeria_specific_alerts(self, monitoring_node, mock_state_with_risk_profile):
        """Test Nigeria-specific CBN alert rules."""
        result_state = await monitoring_node.execute(mock_state_with_risk_profile)
        alert_rules = result_state.data["alert_rules"]
        
        # Check for CBN data residency alert
        cbn_rules = [
            rule for rule in alert_rules["rules"]
            if rule["name"] == "data_residency_violation"
        ]
        assert len(cbn_rules) > 0
        assert cbn_rules[0]["severity"] == "critical"


class TestPolicyGenerationNode:
    """Test policy generation node functionality."""
    
    @pytest.fixture
    def policy_node(self):
        """Create policy generation node for testing."""
        return PolicyGenerationNode()
    
    @pytest.fixture
    def mock_state_with_assessment_and_risk(self):
        """Create mock state with assessment and risk data."""
        state = WorkflowState(
            workflow_id=uuid.uuid4(),
            tenant_id="test-tenant",
            region="ZA"
        )
        state.data = {
            "assessment_results": {
                "frameworks_assessed": ["gdpr", "popia"],
                "overall_score": 75
            },
            "risk_profile": {
                "overall_risk_score": 6.5,
                "critical_risks": []
            }
        }
        return state
    
    @pytest.mark.asyncio
    async def test_policy_generation(self, policy_node, mock_state_with_assessment_and_risk):
        """Test policy and procedure generation."""
        result_state = await policy_node.execute(mock_state_with_assessment_and_risk)
        
        assert "policies" in result_state.data
        assert "procedures" in result_state.data
        
        policies = result_state.data["policies"]
        assert len(policies["policies"]) > 0
        assert policies["version"] == "1.0"
        
        procedures = result_state.data["procedures"]
        assert len(procedures["procedures"]) > 0
    
    @pytest.mark.asyncio
    async def test_gdpr_policy_generation(self, policy_node, mock_state_with_assessment_and_risk):
        """Test GDPR-specific policy generation."""
        result_state = await policy_node.execute(mock_state_with_assessment_and_risk)
        policies = result_state.data["policies"]
        
        gdpr_policies = [
            policy for policy in policies["policies"]
            if policy["framework"] == "gdpr"
        ]
        assert len(gdpr_policies) > 0
        
        # Check for data protection policy
        data_protection_policies = [
            policy for policy in gdpr_policies
            if policy["id"] == "gdpr_data_protection"
        ]
        assert len(data_protection_policies) > 0


class TestComplianceIntegrationNode:
    """Test compliance integration node functionality."""
    
    @pytest.fixture
    def integration_node(self):
        """Create compliance integration node for testing."""
        return ComplianceIntegrationNode()
    
    @pytest.fixture
    def mock_state_with_policies(self):
        """Create mock state with policies and monitoring config."""
        state = WorkflowState(
            workflow_id=uuid.uuid4(),
            tenant_id="test-tenant",
            region="NG"
        )
        state.data = {
            "policies": {
                "frameworks": ["gdpr", "cbn"],
                "policies": []
            },
            "monitoring_config": {
                "monitoring_enabled": True
            }
        }
        return state
    
    @pytest.mark.asyncio
    async def test_integration_setup(self, integration_node, mock_state_with_policies):
        """Test compliance integration setup."""
        result_state = await integration_node.execute(mock_state_with_policies)
        
        assert "integration_config" in result_state.data
        assert "api_connections" in result_state.data
        
        integration_config = result_state.data["integration_config"]
        assert integration_config["region"] == "NG"
        assert len(integration_config["integrations"]) > 0
    
    @pytest.mark.asyncio
    async def test_nigeria_cbn_integration(self, integration_node, mock_state_with_policies):
        """Test Nigeria CBN regulatory integration."""
        result_state = await integration_node.execute(mock_state_with_policies)
        integration_config = result_state.data["integration_config"]
        
        # Check for CBN integration
        cbn_integrations = [
            integration for integration in integration_config["integrations"]
            if integration["name"] == "CBN Regulatory Portal"
        ]
        assert len(cbn_integrations) > 0
        
        cbn_integration = cbn_integrations[0]
        assert cbn_integration["type"] == "regulatory_reporting"
        assert "financial_data_residency" in cbn_integration["data_types"]


class TestComplianceFrameworkEnums:
    """Test compliance framework enums and constants."""
    
    def test_compliance_framework_enum(self):
        """Test ComplianceFramework enum values."""
        assert ComplianceFramework.GDPR == "gdpr"
        assert ComplianceFramework.POPIA == "popia"
        assert ComplianceFramework.CBN == "cbn"
        assert ComplianceFramework.ISO27001 == "iso27001"
        assert ComplianceFramework.SOC2 == "soc2"
        assert ComplianceFramework.HIPAA == "hipaa"
        assert ComplianceFramework.PCI_DSS == "pci_dss"
    
    def test_risk_level_enum(self):
        """Test RiskLevel enum values."""
        assert RiskLevel.LOW == "low"
        assert RiskLevel.MEDIUM == "medium"
        assert RiskLevel.HIGH == "high"
        assert RiskLevel.CRITICAL == "critical"


class TestAfricanMarketCompliance:
    """Test African market-specific compliance optimizations."""
    
    def test_nigerian_cbn_compliance(self):
        """Test Nigerian CBN compliance requirements."""
        template = IndustryTemplateFactory.create_compliance_workflows_template()
        
        # Verify Nigerian market support
        assert "NG" in template.supported_regions
        assert "NGN" in template.supported_currencies
        
        # Check for Hausa and Yoruba language support
        assert "ha" in template.supported_languages  # Hausa
        assert "yo" in template.supported_languages  # Yoruba
    
    def test_south_african_popia_compliance(self):
        """Test South African POPIA compliance requirements."""
        template = IndustryTemplateFactory.create_compliance_workflows_template()
        
        # Verify South African market support
        assert "ZA" in template.supported_regions
        assert "ZAR" in template.supported_currencies
        
        # Check for Afrikaans and Zulu language support
        assert "af" in template.supported_languages  # Afrikaans
        assert "zu" in template.supported_languages  # Zulu
    
    def test_kenyan_market_support(self):
        """Test Kenyan market compliance support."""
        template = IndustryTemplateFactory.create_compliance_workflows_template()
        
        # Verify Kenyan market support
        assert "KE" in template.supported_regions
        assert "KES" in template.supported_currencies
        
        # Check for Swahili language support
        assert "sw" in template.supported_languages  # Swahili


if __name__ == "__main__":
    pytest.main([__file__])
