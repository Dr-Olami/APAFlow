"""
Compliance Workflow Nodes for WORKFLOW-005 Compliance Workflows.

This module implements specialized nodes for regulatory compliance,
audit management, and risk assessment workflows with African market
optimizations for GDPR, POPIA, and CBN compliance.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
import logging
from enum import Enum

from .nodes import BaseNode, NodeConfig
from .state import WorkflowState

logger = logging.getLogger(__name__)


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks."""
    GDPR = "gdpr"
    POPIA = "popia"
    CBN = "cbn"
    ISO27001 = "iso27001"
    SOC2 = "soc2"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceAssessmentNode(BaseNode):
    """Node for assessing current compliance status."""
    
    def __init__(self):
        config = NodeConfig(
            name="compliance_assessment",
            description="Assess current compliance status and requirements",
            required_inputs=["organization_info", "compliance_frameworks"],
            outputs=["compliance_status", "assessment_results"],
            region_specific=True,
            supported_regions=["NG", "ZA", "KE", "GH", "UG", "TZ", "RW", "ET"],
            supported_languages=["en", "ha", "yo", "ig", "sw", "af", "zu", "am", "fr"]
        )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """Assess compliance status based on organization and frameworks."""
        org_info = state.data.get("organization_info", {})
        frameworks = state.data.get("compliance_frameworks", [])
        
        # Perform compliance assessment
        assessment_results = {
            "assessment_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "organization": org_info.get("name", "Unknown"),
            "region": state.region,
            "frameworks_assessed": frameworks,
            "overall_score": 0,
            "framework_scores": {},
            "gaps_identified": [],
            "recommendations": []
        }
        
        # Assess each framework
        for framework in frameworks:
            score = await self._assess_framework(framework, org_info, state.region)
            assessment_results["framework_scores"][framework] = score
            
            if score < 70:  # Below 70% compliance
                assessment_results["gaps_identified"].append({
                    "framework": framework,
                    "score": score,
                    "risk_level": "high" if score < 50 else "medium"
                })
        
        # Calculate overall score
        if assessment_results["framework_scores"]:
            assessment_results["overall_score"] = sum(
                assessment_results["framework_scores"].values()
            ) / len(assessment_results["framework_scores"])
        
        # Generate recommendations
        assessment_results["recommendations"] = await self._generate_recommendations(
            assessment_results, state.region
        )
        
        # Store results
        state.data["compliance_status"] = "assessed"
        state.data["assessment_results"] = assessment_results
        
        return state
    
    async def _assess_framework(self, framework: str, org_info: Dict, region: str) -> float:
        """Assess compliance for a specific framework."""
        # Mock assessment logic - in production, this would integrate with
        # compliance scanning tools and regulatory databases
        
        base_score = 60.0  # Starting baseline
        
        # Regional adjustments
        if framework == "gdpr" and region in ["NG", "ZA", "KE"]:
            base_score += 10  # Better GDPR compliance in these regions
        elif framework == "popia" and region == "ZA":
            base_score += 15  # Native POPIA compliance
        elif framework == "cbn" and region == "NG":
            base_score += 15  # Native CBN compliance
        
        # Organization size factor
        employee_count = org_info.get("employee_count", 0)
        if employee_count > 100:
            base_score += 5  # Larger orgs typically have better compliance
        
        return min(base_score, 100.0)
    
    async def _generate_recommendations(self, results: Dict, region: str) -> List[Dict]:
        """Generate compliance recommendations based on assessment."""
        recommendations = []
        
        for gap in results["gaps_identified"]:
            framework = gap["framework"]
            
            if framework == "gdpr":
                recommendations.append({
                    "priority": "high",
                    "framework": framework,
                    "action": "Implement data protection impact assessments",
                    "timeline": "30 days",
                    "cost_estimate": "medium"
                })
            elif framework == "popia" and region == "ZA":
                recommendations.append({
                    "priority": "high",
                    "framework": framework,
                    "action": "Establish Information Officer role and processes",
                    "timeline": "14 days",
                    "cost_estimate": "low"
                })
            elif framework == "cbn" and region == "NG":
                recommendations.append({
                    "priority": "critical",
                    "framework": framework,
                    "action": "Implement data residency controls for financial data",
                    "timeline": "7 days",
                    "cost_estimate": "high"
                })
        
        return recommendations


class AuditTrailNode(BaseNode):
    """Node for setting up automated audit trails."""
    
    def __init__(self):
        config = NodeConfig(
            name="audit_trail_setup",
            description="Configure automated audit trail logging",
            required_inputs=["assessment_results"],
            outputs=["audit_config", "logging_setup"],
            timeout_seconds=600
        )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """Set up comprehensive audit trail system."""
        assessment = state.data.get("assessment_results", {})
        frameworks = assessment.get("frameworks_assessed", [])
        
        audit_config = {
            "audit_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "frameworks": frameworks,
            "logging_level": "comprehensive",
            "retention_period_days": 2555,  # 7 years for compliance
            "encryption_enabled": True,
            "immutable_storage": True,
            "log_categories": []
        }
        
        # Configure logging categories based on frameworks
        if "gdpr" in frameworks:
            audit_config["log_categories"].extend([
                "data_access", "data_modification", "data_deletion",
                "consent_changes", "data_export", "right_to_be_forgotten"
            ])
        
        if "popia" in frameworks:
            audit_config["log_categories"].extend([
                "personal_info_processing", "cross_border_transfers",
                "data_subject_requests", "security_incidents"
            ])
        
        if "cbn" in frameworks:
            audit_config["log_categories"].extend([
                "financial_transactions", "data_residency_checks",
                "regulatory_reporting", "system_access"
            ])
        
        # Remove duplicates
        audit_config["log_categories"] = list(set(audit_config["log_categories"]))
        
        # Configure logging infrastructure
        logging_setup = {
            "log_storage": "loki",  # Using Loki for centralized logging
            "backup_storage": "graylog",
            "alert_thresholds": {
                "failed_access_attempts": 5,
                "data_export_volume_mb": 100,
                "suspicious_activity_score": 0.8
            },
            "real_time_monitoring": True,
            "automated_reports": True
        }
        
        state.data["audit_config"] = audit_config
        state.data["logging_setup"] = logging_setup
        
        return state


class ComplianceReportingNode(BaseNode):
    """Node for automated compliance reporting."""
    
    def __init__(self):
        config = NodeConfig(
            name="compliance_reporting",
            description="Set up automated regulatory reporting",
            required_inputs=["audit_config", "assessment_results"],
            outputs=["reporting_config", "report_schedule"],
            region_specific=True,
            supported_regions=["NG", "ZA", "KE", "GH", "UG", "TZ", "RW", "ET"]
        )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """Configure automated compliance reporting."""
        assessment = state.data.get("assessment_results", {})
        frameworks = assessment.get("frameworks_assessed", [])
        region = state.region
        
        reporting_config = {
            "config_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "region": region,
            "frameworks": frameworks,
            "reports": [],
            "delivery_methods": ["email", "api", "dashboard"],
            "encryption_required": True
        }
        
        # Configure reports based on frameworks and region
        if "gdpr" in frameworks:
            reporting_config["reports"].append({
                "type": "gdpr_compliance_report",
                "frequency": "monthly",
                "recipients": ["dpo@organization.com"],
                "format": "pdf",
                "sections": ["data_processing_activities", "consent_status", 
                           "data_breaches", "subject_requests"]
            })
        
        if "popia" in frameworks and region == "ZA":
            reporting_config["reports"].append({
                "type": "popia_compliance_report",
                "frequency": "quarterly",
                "recipients": ["information_officer@organization.com"],
                "format": "pdf",
                "sections": ["processing_register", "cross_border_transfers",
                           "security_measures", "incident_reports"]
            })
        
        if "cbn" in frameworks and region == "NG":
            reporting_config["reports"].append({
                "type": "cbn_regulatory_report",
                "frequency": "monthly",
                "recipients": ["compliance@organization.com", "cbn_liaison@organization.com"],
                "format": "xml",
                "sections": ["data_residency_status", "financial_data_processing",
                           "system_security", "operational_risk"]
            })
        
        # Set up report schedule
        report_schedule = {
            "next_reports": [],
            "automated_generation": True,
            "quality_checks": True,
            "approval_workflow": True
        }
        
        # Calculate next report dates
        for report in reporting_config["reports"]:
            next_date = self._calculate_next_report_date(report["frequency"])
            report_schedule["next_reports"].append({
                "type": report["type"],
                "due_date": next_date.isoformat(),
                "status": "scheduled"
            })
        
        state.data["reporting_config"] = reporting_config
        state.data["report_schedule"] = report_schedule
        
        return state
    
    def _calculate_next_report_date(self, frequency: str) -> datetime:
        """Calculate next report due date based on frequency."""
        now = datetime.utcnow()
        
        if frequency == "daily":
            return now + timedelta(days=1)
        elif frequency == "weekly":
            return now + timedelta(weeks=1)
        elif frequency == "monthly":
            return now + timedelta(days=30)
        elif frequency == "quarterly":
            return now + timedelta(days=90)
        elif frequency == "annually":
            return now + timedelta(days=365)
        else:
            return now + timedelta(days=30)  # Default to monthly


class RiskAssessmentNode(BaseNode):
    """Node for automated risk assessment and scoring."""
    
    def __init__(self):
        config = NodeConfig(
            name="risk_assessment",
            description="Perform automated compliance risk assessment",
            required_inputs=["assessment_results", "audit_config"],
            outputs=["risk_profile", "mitigation_plan"],
            timeout_seconds=900
        )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """Perform comprehensive risk assessment."""
        assessment = state.data.get("assessment_results", {})
        audit_config = state.data.get("audit_config", {})
        
        risk_profile = {
            "assessment_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "overall_risk_score": 0,
            "risk_categories": {},
            "critical_risks": [],
            "recommendations": []
        }
        
        # Assess different risk categories
        risk_categories = {
            "data_privacy": await self._assess_data_privacy_risk(assessment),
            "regulatory_compliance": await self._assess_regulatory_risk(assessment),
            "operational_security": await self._assess_security_risk(audit_config),
            "financial_impact": await self._assess_financial_risk(assessment),
            "reputational_risk": await self._assess_reputational_risk(assessment)
        }
        
        risk_profile["risk_categories"] = risk_categories
        
        # Calculate overall risk score (weighted average)
        weights = {
            "data_privacy": 0.25,
            "regulatory_compliance": 0.30,
            "operational_security": 0.20,
            "financial_impact": 0.15,
            "reputational_risk": 0.10
        }
        
        overall_score = sum(
            risk_categories[category] * weights[category]
            for category in risk_categories
        )
        risk_profile["overall_risk_score"] = round(overall_score, 2)
        
        # Identify critical risks
        for category, score in risk_categories.items():
            if score >= 8.0:  # High risk threshold
                risk_profile["critical_risks"].append({
                    "category": category,
                    "score": score,
                    "level": "critical" if score >= 9.0 else "high",
                    "immediate_action_required": score >= 9.0
                })
        
        # Generate mitigation plan
        mitigation_plan = await self._generate_mitigation_plan(risk_profile)
        
        state.data["risk_profile"] = risk_profile
        state.data["mitigation_plan"] = mitigation_plan
        
        return state
    
    async def _assess_data_privacy_risk(self, assessment: Dict) -> float:
        """Assess data privacy risk score (1-10 scale)."""
        base_risk = 5.0
        
        # Check GDPR compliance
        gdpr_score = assessment.get("framework_scores", {}).get("gdpr", 100)
        if gdpr_score < 70:
            base_risk += 2.0
        
        # Check POPIA compliance
        popia_score = assessment.get("framework_scores", {}).get("popia", 100)
        if popia_score < 70:
            base_risk += 1.5
        
        return min(base_risk, 10.0)
    
    async def _assess_regulatory_risk(self, assessment: Dict) -> float:
        """Assess regulatory compliance risk score."""
        overall_score = assessment.get("overall_score", 100)
        
        if overall_score >= 90:
            return 2.0
        elif overall_score >= 80:
            return 4.0
        elif overall_score >= 70:
            return 6.0
        elif overall_score >= 60:
            return 8.0
        else:
            return 10.0
    
    async def _assess_security_risk(self, audit_config: Dict) -> float:
        """Assess operational security risk score."""
        base_risk = 3.0
        
        if not audit_config.get("encryption_enabled", False):
            base_risk += 3.0
        
        if not audit_config.get("immutable_storage", False):
            base_risk += 2.0
        
        return min(base_risk, 10.0)
    
    async def _assess_financial_risk(self, assessment: Dict) -> float:
        """Assess financial impact risk score."""
        gaps = assessment.get("gaps_identified", [])
        
        high_risk_gaps = [gap for gap in gaps if gap.get("risk_level") == "high"]
        
        if len(high_risk_gaps) >= 3:
            return 8.0
        elif len(high_risk_gaps) >= 2:
            return 6.0
        elif len(high_risk_gaps) >= 1:
            return 4.0
        else:
            return 2.0
    
    async def _assess_reputational_risk(self, assessment: Dict) -> float:
        """Assess reputational risk score."""
        overall_score = assessment.get("overall_score", 100)
        
        if overall_score < 50:
            return 9.0
        elif overall_score < 70:
            return 6.0
        elif overall_score < 85:
            return 4.0
        else:
            return 2.0
    
    async def _generate_mitigation_plan(self, risk_profile: Dict) -> Dict:
        """Generate risk mitigation plan."""
        return {
            "plan_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "priority_actions": [
                {
                    "action": f"Address {risk['category']} risks",
                    "priority": risk["level"],
                    "timeline": "immediate" if risk["immediate_action_required"] else "30 days",
                    "estimated_effort": "high" if risk["score"] >= 9.0 else "medium"
                }
                for risk in risk_profile["critical_risks"]
            ],
            "monitoring_frequency": "daily" if risk_profile["overall_risk_score"] >= 8.0 else "weekly",
            "review_schedule": "weekly" if risk_profile["overall_risk_score"] >= 7.0 else "monthly"
        }


class ComplianceMonitoringNode(BaseNode):
    """Node for setting up real-time compliance monitoring."""
    
    def __init__(self):
        config = NodeConfig(
            name="compliance_monitoring",
            description="Configure real-time compliance monitoring and alerts",
            required_inputs=["risk_profile", "audit_config"],
            outputs=["monitoring_config", "alert_rules"],
            timeout_seconds=300
        )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """Set up comprehensive compliance monitoring system."""
        risk_profile = state.data.get("risk_profile", {})
        audit_config = state.data.get("audit_config", {})
        
        monitoring_config = {
            "config_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "monitoring_enabled": True,
            "real_time_alerts": True,
            "dashboard_enabled": True,
            "metrics_collection": {
                "compliance_score": True,
                "policy_violations": True,
                "data_access_patterns": True,
                "security_incidents": True,
                "regulatory_changes": True
            },
            "data_sources": [
                "application_logs", "database_audit_logs", 
                "security_events", "user_activities", "system_metrics"
            ]
        }
        
        # Configure alert rules based on risk profile
        alert_rules = {
            "rules": [],
            "notification_channels": ["email", "slack", "dashboard"],
            "escalation_matrix": {
                "low": ["compliance_team@organization.com"],
                "medium": ["compliance_team@organization.com", "security_team@organization.com"],
                "high": ["compliance_team@organization.com", "security_team@organization.com", "ciso@organization.com"],
                "critical": ["compliance_team@organization.com", "security_team@organization.com", "ciso@organization.com", "ceo@organization.com"]
            }
        }
        
        # Add standard alert rules
        standard_rules = [
            {
                "name": "policy_violation_detected",
                "condition": "policy_violation_count > 5 in 1h",
                "severity": "high",
                "description": "Multiple policy violations detected"
            },
            {
                "name": "unusual_data_access",
                "condition": "data_access_volume > baseline * 3",
                "severity": "medium",
                "description": "Unusual data access patterns detected"
            },
            {
                "name": "compliance_score_drop",
                "condition": "compliance_score < 70",
                "severity": "high",
                "description": "Compliance score dropped below threshold"
            },
            {
                "name": "failed_audit_check",
                "condition": "audit_check_failure = true",
                "severity": "critical",
                "description": "Critical audit check failed"
            }
        ]
        
        # Add region-specific rules
        region = state.region
        if region == "NG":  # Nigeria - CBN specific
            standard_rules.append({
                "name": "data_residency_violation",
                "condition": "financial_data_location != 'NG'",
                "severity": "critical",
                "description": "CBN data residency requirement violated"
            })
        elif region == "ZA":  # South Africa - POPIA specific
            standard_rules.append({
                "name": "cross_border_transfer_alert",
                "condition": "cross_border_transfer = true AND consent_verified = false",
                "severity": "high",
                "description": "Unauthorized cross-border data transfer detected"
            })
        
        alert_rules["rules"] = standard_rules
        
        state.data["monitoring_config"] = monitoring_config
        state.data["alert_rules"] = alert_rules
        
        return state


class PolicyGenerationNode(BaseNode):
    """Node for generating compliance policies and procedures."""
    
    def __init__(self):
        config = NodeConfig(
            name="policy_generation",
            description="Generate compliance policies and procedures",
            required_inputs=["assessment_results", "risk_profile"],
            outputs=["policies", "procedures"],
            timeout_seconds=600
        )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """Generate comprehensive compliance policies."""
        assessment = state.data.get("assessment_results", {})
        risk_profile = state.data.get("risk_profile", {})
        frameworks = assessment.get("frameworks_assessed", [])
        
        policies = {
            "policy_set_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0",
            "frameworks": frameworks,
            "policies": []
        }
        
        procedures = {
            "procedure_set_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "procedures": []
        }
        
        # Generate framework-specific policies
        if "gdpr" in frameworks:
            gdpr_policies = await self._generate_gdpr_policies()
            policies["policies"].extend(gdpr_policies)
            
            gdpr_procedures = await self._generate_gdpr_procedures()
            procedures["procedures"].extend(gdpr_procedures)
        
        if "popia" in frameworks:
            popia_policies = await self._generate_popia_policies()
            policies["policies"].extend(popia_policies)
            
            popia_procedures = await self._generate_popia_procedures()
            procedures["procedures"].extend(popia_procedures)
        
        if "cbn" in frameworks:
            cbn_policies = await self._generate_cbn_policies()
            policies["policies"].extend(cbn_policies)
            
            cbn_procedures = await self._generate_cbn_procedures()
            procedures["procedures"].extend(cbn_procedures)
        
        # Add risk-based policies
        risk_based_policies = await self._generate_risk_based_policies(risk_profile)
        policies["policies"].extend(risk_based_policies)
        
        state.data["policies"] = policies
        state.data["procedures"] = procedures
        
        return state
    
    async def _generate_gdpr_policies(self) -> List[Dict]:
        """Generate GDPR-specific policies."""
        return [
            {
                "id": "gdpr_data_protection",
                "title": "Data Protection Policy (GDPR)",
                "framework": "gdpr",
                "category": "data_protection",
                "description": "Comprehensive data protection policy ensuring GDPR compliance",
                "key_requirements": [
                    "Lawful basis for processing",
                    "Data subject rights implementation",
                    "Privacy by design and default",
                    "Data protection impact assessments"
                ],
                "review_frequency": "annually",
                "mandatory": True
            },
            {
                "id": "gdpr_consent_management",
                "title": "Consent Management Policy",
                "framework": "gdpr",
                "category": "consent",
                "description": "Policy for managing data subject consent",
                "key_requirements": [
                    "Clear and specific consent requests",
                    "Consent withdrawal mechanisms",
                    "Consent record keeping",
                    "Regular consent review"
                ],
                "review_frequency": "quarterly",
                "mandatory": True
            }
        ]
    
    async def _generate_popia_policies(self) -> List[Dict]:
        """Generate POPIA-specific policies."""
        return [
            {
                "id": "popia_information_processing",
                "title": "Personal Information Processing Policy (POPIA)",
                "framework": "popia",
                "category": "information_processing",
                "description": "Policy for processing personal information under POPIA",
                "key_requirements": [
                    "Information Officer appointment",
                    "Processing register maintenance",
                    "Cross-border transfer controls",
                    "Data subject request handling"
                ],
                "review_frequency": "annually",
                "mandatory": True
            }
        ]
    
    async def _generate_cbn_policies(self) -> List[Dict]:
        """Generate CBN-specific policies."""
        return [
            {
                "id": "cbn_data_residency",
                "title": "Data Residency Policy (CBN)",
                "framework": "cbn",
                "category": "data_residency",
                "description": "Policy ensuring CBN data residency requirements",
                "key_requirements": [
                    "Financial data must remain in Nigeria",
                    "Regular residency audits",
                    "Vendor compliance verification",
                    "Incident response procedures"
                ],
                "review_frequency": "quarterly",
                "mandatory": True
            }
        ]
    
    async def _generate_gdpr_procedures(self) -> List[Dict]:
        """Generate GDPR-specific procedures."""
        return [
            {
                "id": "gdpr_data_breach_response",
                "title": "GDPR Data Breach Response Procedure",
                "framework": "gdpr",
                "steps": [
                    "Immediate containment (within 1 hour)",
                    "Risk assessment (within 4 hours)",
                    "Supervisory authority notification (within 72 hours)",
                    "Data subject notification (if high risk)",
                    "Documentation and lessons learned"
                ],
                "roles_responsible": ["DPO", "Security Team", "Legal Team"]
            }
        ]
    
    async def _generate_popia_procedures(self) -> List[Dict]:
        """Generate POPIA-specific procedures."""
        return [
            {
                "id": "popia_data_subject_request",
                "title": "POPIA Data Subject Request Procedure",
                "framework": "popia",
                "steps": [
                    "Request verification (within 1 day)",
                    "Identity confirmation (within 2 days)",
                    "Data retrieval and review (within 28 days)",
                    "Response delivery (within 30 days)",
                    "Request logging and monitoring"
                ],
                "roles_responsible": ["Information Officer", "Data Team"]
            }
        ]
    
    async def _generate_cbn_procedures(self) -> List[Dict]:
        """Generate CBN-specific procedures."""
        return [
            {
                "id": "cbn_data_residency_audit",
                "title": "CBN Data Residency Audit Procedure",
                "framework": "cbn",
                "steps": [
                    "Monthly data location verification",
                    "Vendor compliance checks",
                    "Infrastructure audit",
                    "Compliance reporting to CBN",
                    "Corrective action implementation"
                ],
                "roles_responsible": ["Compliance Officer", "IT Team", "Legal Team"]
            }
        ]
    
    async def _generate_risk_based_policies(self, risk_profile: Dict) -> List[Dict]:
        """Generate policies based on risk assessment."""
        policies = []
        
        overall_risk = risk_profile.get("overall_risk_score", 0)
        
        if overall_risk >= 7.0:
            policies.append({
                "id": "high_risk_monitoring",
                "title": "High Risk Monitoring Policy",
                "framework": "risk_management",
                "category": "monitoring",
                "description": "Enhanced monitoring for high-risk environments",
                "key_requirements": [
                    "Daily compliance checks",
                    "Real-time alert monitoring",
                    "Weekly risk assessments",
                    "Immediate escalation procedures"
                ],
                "review_frequency": "monthly",
                "mandatory": True
            })
        
        return policies


class ComplianceIntegrationNode(BaseNode):
    """Node for integrating with external compliance systems."""
    
    def __init__(self):
        config = NodeConfig(
            name="compliance_integration",
            description="Integrate with external compliance and regulatory systems",
            required_inputs=["policies", "monitoring_config"],
            outputs=["integration_config", "api_connections"],
            region_specific=True,
            supported_regions=["NG", "ZA", "KE", "GH", "UG", "TZ", "RW", "ET"]
        )
        super().__init__(config)
    
    async def _execute_logic(self, state: WorkflowState) -> WorkflowState:
        """Set up integrations with external compliance systems."""
        region = state.region
        policies = state.data.get("policies", {})
        frameworks = policies.get("frameworks", [])
        
        integration_config = {
            "config_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "region": region,
            "integrations": [],
            "api_endpoints": {},
            "authentication": {},
            "sync_frequency": "daily"
        }
        
        api_connections = {
            "connections": [],
            "health_checks": [],
            "fallback_procedures": []
        }
        
        # Regional government API integrations
        if region == "NG":  # Nigeria
            if "cbn" in frameworks:
                integration_config["integrations"].append({
                    "name": "CBN Regulatory Portal",
                    "type": "regulatory_reporting",
                    "endpoint": "https://api.cbn.gov.ng/regulatory",
                    "authentication_type": "api_key",
                    "data_types": ["financial_data_residency", "compliance_reports"]
                })
            
            # FIRS (Federal Inland Revenue Service) integration
            integration_config["integrations"].append({
                "name": "FIRS Tax Portal",
                "type": "tax_compliance",
                "endpoint": "https://api.firs.gov.ng/tax",
                "authentication_type": "certificate",
                "data_types": ["tax_reports", "vat_returns"]
            })
        
        elif region == "ZA":  # South Africa
            if "popia" in frameworks:
                integration_config["integrations"].append({
                    "name": "Information Regulator SA",
                    "type": "privacy_regulator",
                    "endpoint": "https://api.inforegulator.org.za/popia",
                    "authentication_type": "oauth2",
                    "data_types": ["breach_notifications", "compliance_reports"]
                })
            
            # SARS (South African Revenue Service) integration
            integration_config["integrations"].append({
                "name": "SARS eFiling",
                "type": "tax_compliance",
                "endpoint": "https://api.sars.gov.za/efiling",
                "authentication_type": "certificate",
                "data_types": ["tax_returns", "vat_submissions"]
            })
        
        elif region == "KE":  # Kenya
            # KRA (Kenya Revenue Authority) integration
            integration_config["integrations"].append({
                "name": "KRA iTax Portal",
                "type": "tax_compliance",
                "endpoint": "https://api.kra.go.ke/itax",
                "authentication_type": "pin_certificate",
                "data_types": ["income_tax", "vat_returns", "paye"]
            })
        
        # Common integrations for all regions
        if "gdpr" in frameworks:
            integration_config["integrations"].append({
                "name": "EU GDPR Compliance Hub",
                "type": "privacy_compliance",
                "endpoint": "https://api.gdpr-hub.eu/compliance",
                "authentication_type": "oauth2",
                "data_types": ["adequacy_decisions", "regulatory_updates"]
            })
        
        # Set up health checks for all integrations
        for integration in integration_config["integrations"]:
            api_connections["health_checks"].append({
                "name": integration["name"],
                "endpoint": f"{integration['endpoint']}/health",
                "frequency": "hourly",
                "timeout_seconds": 30,
                "retry_attempts": 3
            })
        
        state.data["integration_config"] = integration_config
        state.data["api_connections"] = api_connections
        
        return state


class AfricanMarketComplianceHelper:
    """Helper class for African market-specific compliance optimizations."""
    
    @staticmethod
    def get_data_residency_requirements(region: str, frameworks: List[str]) -> Dict[str, Any]:
        """Get data residency requirements for African markets."""
        requirements = {
            "data_localization": False,
            "cross_border_restrictions": [],
            "storage_requirements": {},
            "processing_limitations": []
        }
        
        if region == "NG":  # Nigeria
            if "cbn" in [f.lower() for f in frameworks]:
                requirements.update({
                    "data_localization": True,
                    "cross_border_restrictions": [
                        "Financial data must remain in Nigeria",
                        "Customer PII requires CBN approval for cross-border transfer"
                    ],
                    "storage_requirements": {
                        "financial_data": "Nigeria only",
                        "customer_data": "Nigeria preferred, ECOWAS allowed with approval",
                        "backup_data": "Nigeria + one ECOWAS country maximum"
                    },
                    "processing_limitations": [
                        "Real-time financial processing must occur in Nigeria",
                        "Batch processing allowed in approved ECOWAS locations"
                    ]
                })
        
        elif region == "ZA":  # South Africa
            if "popia" in [f.lower() for f in frameworks]:
                requirements.update({
                    "data_localization": False,  # POPIA allows cross-border with adequacy
                    "cross_border_restrictions": [
                        "Adequate protection required for cross-border transfers",
                        "Data subject consent required for transfers outside SADC"
                    ],
                    "storage_requirements": {
                        "personal_data": "South Africa preferred, SADC allowed",
                        "sensitive_data": "South Africa only without explicit consent",
                        "backup_data": "SADC region allowed"
                    },
                    "processing_limitations": [
                        "Automated decision-making requires human oversight",
                        "Profiling requires explicit consent"
                    ]
                })
        
        return requirements
    
    @staticmethod
    def get_regulatory_reporting_schedule(region: str, frameworks: List[str]) -> Dict[str, Any]:
        """Get regulatory reporting schedules for African markets."""
        schedule = {
            "mandatory_reports": [],
            "filing_deadlines": {},
            "notification_requirements": []
        }
        
        if region == "NG":
            schedule["mandatory_reports"].extend([
                "CBN Quarterly Compliance Report",
                "FIRS Monthly VAT Returns",
                "NITDA Data Protection Impact Assessment"
            ])
            schedule["filing_deadlines"].update({
                "cbn_quarterly": "15th of month following quarter end",
                "firs_vat": "21st of following month",
                "nitda_dpia": "Within 72 hours of high-risk processing"
            })
        
        elif region == "ZA":
            schedule["mandatory_reports"].extend([
                "SARS Monthly VAT Returns",
                "Information Regulator Breach Notifications",
                "SARB Cross-border Transaction Reports"
            ])
            schedule["filing_deadlines"].update({
                "sars_vat": "25th of following month",
                "popia_breach": "Within 72 hours of discovery",
                "sarb_forex": "Within 30 days of transaction"
            })
        
        elif region == "KE":
            schedule["mandatory_reports"].extend([
                "KRA Monthly Returns",
                "CBK Prudential Returns",
                "ODPC Data Protection Compliance Report"
            ])
            schedule["filing_deadlines"].update({
                "kra_returns": "20th of following month",
                "cbk_prudential": "7th of following month",
                "odpc_compliance": "Quarterly - 30th of month following quarter"
            })
        
        return schedule
    
    @staticmethod
    def get_cultural_compliance_considerations(region: str) -> Dict[str, Any]:
        """Get cultural and linguistic compliance considerations."""
        considerations = {
            "languages": [],
            "cultural_factors": [],
            "communication_preferences": {},
            "business_practices": []
        }
        
        if region == "NG":
            considerations.update({
                "languages": ["English", "Hausa", "Yoruba", "Igbo"],
                "cultural_factors": [
                    "Respect for traditional authority structures",
                    "Importance of relationship-building in business",
                    "Religious considerations (Islamic and Christian practices)"
                ],
                "communication_preferences": {
                    "formal_tone": True,
                    "relationship_first": True,
                    "indirect_communication": True
                },
                "business_practices": [
                    "Extended decision-making processes",
                    "Importance of face-to-face meetings",
                    "Respect for seniority and hierarchy"
                ]
            })
        
        elif region == "ZA":
            considerations.update({
                "languages": ["English", "Afrikaans", "Zulu", "Xhosa"],
                "cultural_factors": [
                    "Ubuntu philosophy - interconnectedness",
                    "Transformation and B-BBEE considerations",
                    "Multi-cultural sensitivity"
                ],
                "communication_preferences": {
                    "formal_tone": False,
                    "relationship_first": True,
                    "direct_communication": True
                },
                "business_practices": [
                    "Emphasis on transformation and empowerment",
                    "Collaborative decision-making",
                    "Social responsibility expectations"
                ]
            })
        
        elif region == "KE":
            considerations.update({
                "languages": ["English", "Swahili"],
                "cultural_factors": [
                    "Harambee spirit - collective responsibility",
                    "Respect for elders and traditional leadership",
                    "Strong entrepreneurial culture"
                ],
                "communication_preferences": {
                    "formal_tone": True,
                    "relationship_first": True,
                    "respectful_communication": True
                },
                "business_practices": [
                    "Community consultation important",
                    "Long-term relationship focus",
                    "Innovation and technology adoption"
                ]
            })
        
        return considerations
