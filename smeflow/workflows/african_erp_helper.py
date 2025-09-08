"""
African Market ERP Integration Helper.

This module provides specialized functionality for ERP integration
optimized for African markets, including local ERPs, banking APIs,
and financial compliance requirements.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AfricanRegion(str, Enum):
    """African regions supported for ERP integration."""
    NIGERIA = "NG"
    SOUTH_AFRICA = "ZA"
    KENYA = "KE"
    GHANA = "GH"
    UGANDA = "UG"
    TANZANIA = "TZ"
    RWANDA = "RW"
    ETHIOPIA = "ET"


class LocalERPSystem(str, Enum):
    """Local African ERP systems."""
    TALLY_AFRICA = "tally_africa"
    SAGE_PASTEL = "sage_pastel"
    QUICKBOOKS_AFRICA = "quickbooks_africa"
    XERO_AFRICA = "xero_africa"
    ODOO_AFRICA = "odoo_africa"
    CUSTOM_LOCAL = "custom_local"


class AfricanERPHelper:
    """Helper class for African market ERP integration optimizations."""
    
    @staticmethod
    def get_local_erp_systems(region: str) -> List[Dict[str, Any]]:
        """
        Get popular local ERP systems by African region.
        
        Args:
            region: African region code (NG, ZA, KE, etc.)
            
        Returns:
            List of local ERP systems with integration details
        """
        erp_systems = {
            "NG": [
                {
                    "name": "Tally ERP 9 Nigeria",
                    "type": LocalERPSystem.TALLY_AFRICA,
                    "market_share": "35%",
                    "integration_complexity": "Medium",
                    "api_availability": True,
                    "local_support": True,
                    "compliance_features": ["VAT", "FIRS_integration", "CBN_reporting"]
                },
                {
                    "name": "Sage Pastel Nigeria",
                    "type": LocalERPSystem.SAGE_PASTEL,
                    "market_share": "25%",
                    "integration_complexity": "Low",
                    "api_availability": True,
                    "local_support": True,
                    "compliance_features": ["VAT", "Payroll", "FIRS_integration"]
                },
                {
                    "name": "QuickBooks Nigeria",
                    "type": LocalERPSystem.QUICKBOOKS_AFRICA,
                    "market_share": "20%",
                    "integration_complexity": "Low",
                    "api_availability": True,
                    "local_support": True,
                    "compliance_features": ["VAT", "Multi_currency", "Banking_integration"]
                }
            ],
            "ZA": [
                {
                    "name": "Sage Pastel Evolution",
                    "type": LocalERPSystem.SAGE_PASTEL,
                    "market_share": "40%",
                    "integration_complexity": "Medium",
                    "api_availability": True,
                    "local_support": True,
                    "compliance_features": ["VAT", "SARS_integration", "BEE_reporting"]
                },
                {
                    "name": "Syspro South Africa",
                    "type": LocalERPSystem.CUSTOM_LOCAL,
                    "market_share": "15%",
                    "integration_complexity": "High",
                    "api_availability": True,
                    "local_support": True,
                    "compliance_features": ["Manufacturing", "SARS_integration", "Multi_currency"]
                },
                {
                    "name": "Xero South Africa",
                    "type": LocalERPSystem.XERO_AFRICA,
                    "market_share": "25%",
                    "integration_complexity": "Low",
                    "api_availability": True,
                    "local_support": True,
                    "compliance_features": ["VAT", "Banking_integration", "Payroll"]
                }
            ],
            "KE": [
                {
                    "name": "Tally Kenya",
                    "type": LocalERPSystem.TALLY_AFRICA,
                    "market_share": "30%",
                    "integration_complexity": "Medium",
                    "api_availability": True,
                    "local_support": True,
                    "compliance_features": ["VAT", "KRA_integration", "NHIF_NSSF"]
                },
                {
                    "name": "Odoo Kenya",
                    "type": LocalERPSystem.ODOO_AFRICA,
                    "market_share": "20%",
                    "integration_complexity": "Medium",
                    "api_availability": True,
                    "local_support": True,
                    "compliance_features": ["VAT", "Multi_currency", "Manufacturing"]
                }
            ],
            "GH": [
                {
                    "name": "Tally Ghana",
                    "type": LocalERPSystem.TALLY_AFRICA,
                    "market_share": "25%",
                    "integration_complexity": "Medium",
                    "api_availability": True,
                    "local_support": True,
                    "compliance_features": ["VAT", "GRA_integration", "SSNIT"]
                }
            ]
        }
        
        return erp_systems.get(region, [])
    
    @staticmethod
    def get_banking_apis(region: str) -> List[Dict[str, Any]]:
        """
        Get local banking APIs and payment systems by region.
        
        Args:
            region: African region code
            
        Returns:
            List of banking APIs and integration details
        """
        banking_apis = {
            "NG": [
                {
                    "name": "Flutterwave",
                    "type": "payment_gateway",
                    "services": ["payments", "transfers", "fx", "collections"],
                    "api_docs": "https://developer.flutterwave.com",
                    "supported_banks": ["GTBank", "First Bank", "Access Bank", "Zenith Bank"],
                    "mobile_money": ["MTN Mobile Money", "Airtel Money"],
                    "compliance": ["CBN_licensed", "PCI_DSS"]
                },
                {
                    "name": "Paystack",
                    "type": "payment_gateway",
                    "services": ["payments", "subscriptions", "transfers"],
                    "api_docs": "https://paystack.com/docs",
                    "supported_banks": ["All Nigerian Banks"],
                    "mobile_money": ["Bank USSD", "QR Payments"],
                    "compliance": ["CBN_licensed", "PCI_DSS"]
                },
                {
                    "name": "Interswitch",
                    "type": "payment_processor",
                    "services": ["card_processing", "pos", "web_payments"],
                    "api_docs": "https://developer.interswitchng.com",
                    "supported_banks": ["All Nigerian Banks"],
                    "compliance": ["CBN_licensed", "EMV_certified"]
                }
            ],
            "ZA": [
                {
                    "name": "PayFast",
                    "type": "payment_gateway",
                    "services": ["payments", "subscriptions", "marketplace"],
                    "api_docs": "https://developers.payfast.co.za",
                    "supported_banks": ["All South African Banks"],
                    "mobile_money": ["SnapScan", "Zapper"],
                    "compliance": ["SARB_approved", "PCI_DSS"]
                },
                {
                    "name": "Ozow",
                    "type": "payment_gateway",
                    "services": ["instant_eft", "recurring_payments"],
                    "api_docs": "https://docs.ozow.com",
                    "supported_banks": ["FNB", "Standard Bank", "ABSA", "Nedbank"],
                    "compliance": ["SARB_approved", "PCI_DSS"]
                }
            ],
            "KE": [
                {
                    "name": "M-Pesa API",
                    "type": "mobile_money",
                    "services": ["payments", "transfers", "bill_payments"],
                    "api_docs": "https://developer.safaricom.co.ke",
                    "supported_banks": ["Integration with all banks"],
                    "mobile_money": ["M-Pesa"],
                    "compliance": ["CBK_licensed"]
                },
                {
                    "name": "Flutterwave Kenya",
                    "type": "payment_gateway",
                    "services": ["payments", "mobile_money", "bank_transfers"],
                    "api_docs": "https://developer.flutterwave.com",
                    "supported_banks": ["KCB", "Equity Bank", "Co-op Bank"],
                    "mobile_money": ["M-Pesa", "Airtel Money"],
                    "compliance": ["CBK_licensed"]
                }
            ]
        }
        
        return banking_apis.get(region, [])
    
    @staticmethod
    def get_tax_compliance_requirements(region: str) -> Dict[str, Any]:
        """
        Get tax compliance requirements by African region.
        
        Args:
            region: African region code
            
        Returns:
            Tax compliance requirements and integration details
        """
        tax_requirements = {
            "NG": {
                "tax_authority": "Federal Inland Revenue Service (FIRS)",
                "vat_rate": 7.5,
                "withholding_tax_rates": {
                    "services": 5.0,
                    "goods": 5.0,
                    "rent": 10.0,
                    "dividends": 10.0
                },
                "filing_requirements": {
                    "vat_returns": "monthly",
                    "company_income_tax": "annually",
                    "withholding_tax": "monthly",
                    "annual_returns": "annually"
                },
                "electronic_filing": {
                    "platform": "FIRS Integrated Tax Administration System (ITAS)",
                    "api_available": True,
                    "mandatory_threshold": 25000000  # NGN
                },
                "compliance_deadlines": {
                    "vat_returns": "21st of following month",
                    "withholding_tax": "21st of following month",
                    "company_income_tax": "6 months after year end"
                }
            },
            "ZA": {
                "tax_authority": "South African Revenue Service (SARS)",
                "vat_rate": 15.0,
                "withholding_tax_rates": {
                    "dividends": 20.0,
                    "interest": 15.0,
                    "royalties": 12.0
                },
                "filing_requirements": {
                    "vat_returns": "monthly/bi-monthly",
                    "income_tax": "annually",
                    "provisional_tax": "bi-annually",
                    "paye": "monthly"
                },
                "electronic_filing": {
                    "platform": "SARS eFiling",
                    "api_available": True,
                    "mandatory": True
                },
                "compliance_deadlines": {
                    "vat_returns": "25th of following month",
                    "income_tax": "Last day of February (companies)",
                    "provisional_tax": "End of August and February"
                }
            },
            "KE": {
                "tax_authority": "Kenya Revenue Authority (KRA)",
                "vat_rate": 16.0,
                "withholding_tax_rates": {
                    "services": 5.0,
                    "rent": 10.0,
                    "dividends": 5.0,
                    "interest": 15.0
                },
                "filing_requirements": {
                    "vat_returns": "monthly",
                    "income_tax": "annually",
                    "withholding_tax": "monthly",
                    "paye": "monthly"
                },
                "electronic_filing": {
                    "platform": "KRA iTax",
                    "api_available": True,
                    "mandatory": True
                },
                "compliance_deadlines": {
                    "vat_returns": "20th of following month",
                    "withholding_tax": "20th of following month",
                    "income_tax": "6 months after year end"
                }
            }
        }
        
        return tax_requirements.get(region, {})
    
    @staticmethod
    def get_financial_reporting_standards(region: str) -> Dict[str, Any]:
        """
        Get financial reporting standards by African region.
        
        Args:
            region: African region code
            
        Returns:
            Financial reporting standards and requirements
        """
        reporting_standards = {
            "NG": {
                "primary_standard": "Nigerian GAAP / IFRS",
                "regulatory_body": "Financial Reporting Council of Nigeria (FRCN)",
                "mandatory_ifrs": {
                    "public_companies": True,
                    "banks": True,
                    "insurance": True,
                    "threshold": 2000000000  # NGN 2 billion
                },
                "reporting_currency": "NGN",
                "audit_requirements": {
                    "mandatory_audit_threshold": 500000000,  # NGN 500 million
                    "audit_firms": "SEC registered"
                },
                "filing_requirements": {
                    "annual_returns": "Corporate Affairs Commission (CAC)",
                    "deadline": "18 months after incorporation, then annually"
                }
            },
            "ZA": {
                "primary_standard": "IFRS",
                "regulatory_body": "Companies and Intellectual Property Commission (CIPC)",
                "mandatory_ifrs": {
                    "public_companies": True,
                    "banks": True,
                    "insurance": True,
                    "large_companies": True
                },
                "reporting_currency": "ZAR",
                "audit_requirements": {
                    "mandatory_audit_threshold": 10000000,  # ZAR 10 million
                    "audit_firms": "IRBA registered"
                },
                "filing_requirements": {
                    "annual_returns": "CIPC",
                    "deadline": "30 business days after AGM"
                }
            },
            "KE": {
                "primary_standard": "IFRS",
                "regulatory_body": "Institute of Certified Public Accountants of Kenya (ICPAK)",
                "mandatory_ifrs": {
                    "public_companies": True,
                    "banks": True,
                    "insurance": True,
                    "large_entities": True
                },
                "reporting_currency": "KES",
                "audit_requirements": {
                    "mandatory_audit_threshold": 50000000,  # KES 50 million
                    "audit_firms": "ICPAK registered"
                },
                "filing_requirements": {
                    "annual_returns": "Registrar of Companies",
                    "deadline": "30 days after AGM"
                }
            }
        }
        
        return reporting_standards.get(region, {})
    
    @staticmethod
    def get_integration_recommendations(
        region: str,
        business_type: str,
        monthly_volume: str,
        current_erp: str
    ) -> Dict[str, Any]:
        """
        Get integration recommendations based on African market context.
        
        Args:
            region: African region code
            business_type: Type of business
            monthly_volume: Monthly transaction volume
            current_erp: Current ERP system
            
        Returns:
            Tailored integration recommendations
        """
        # Get regional data
        local_erps = AfricanERPHelper.get_local_erp_systems(region)
        banking_apis = AfricanERPHelper.get_banking_apis(region)
        tax_requirements = AfricanERPHelper.get_tax_compliance_requirements(region)
        
        # Determine complexity and recommendations
        volume_complexity = {
            "1-50": "Low",
            "51-200": "Medium",
            "201-500": "Medium",
            "501-1000": "High",
            "1000+": "High"
        }
        
        recommendations = {
            "integration_approach": "Standard Integration",
            "recommended_local_erps": local_erps[:2],  # Top 2 local ERPs
            "priority_integrations": [],
            "compliance_focus": [],
            "estimated_timeline": "4-6 weeks",
            "budget_range": "$5,000 - $15,000",
            "success_factors": []
        }
        
        # Adjust based on volume
        complexity = volume_complexity.get(monthly_volume, "Medium")
        if complexity == "High":
            recommendations["integration_approach"] = "Phased Integration"
            recommendations["estimated_timeline"] = "8-12 weeks"
            recommendations["budget_range"] = "$15,000 - $50,000"
        
        # Add regional priorities
        if region == "NG":
            recommendations["priority_integrations"].extend([
                "Flutterwave API", "FIRS Tax Integration", "CBN Compliance"
            ])
            recommendations["compliance_focus"].extend([
                "VAT Automation", "Withholding Tax", "CBN Reporting"
            ])
        elif region == "ZA":
            recommendations["priority_integrations"].extend([
                "PayFast API", "SARS eFiling", "Banking Integration"
            ])
            recommendations["compliance_focus"].extend([
                "VAT Automation", "SARS Compliance", "BEE Reporting"
            ])
        elif region == "KE":
            recommendations["priority_integrations"].extend([
                "M-Pesa API", "KRA iTax", "Mobile Banking"
            ])
            recommendations["compliance_focus"].extend([
                "VAT Automation", "KRA Compliance", "Mobile Money Integration"
            ])
        
        # Add business type specific recommendations
        if business_type in ["Manufacturing", "Distribution"]:
            recommendations["success_factors"].extend([
                "Inventory Management Integration",
                "Supply Chain Optimization",
                "Multi-location Support"
            ])
        elif business_type in ["Retail/E-commerce"]:
            recommendations["success_factors"].extend([
                "POS Integration",
                "E-commerce Platform Sync",
                "Customer Analytics"
            ])
        elif business_type in ["Financial Services"]:
            recommendations["success_factors"].extend([
                "Regulatory Compliance",
                "Risk Management",
                "Audit Trail Automation"
            ])
        
        return recommendations
    
    @staticmethod
    def get_local_business_practices(region: str) -> Dict[str, Any]:
        """
        Get local business practices and cultural considerations.
        
        Args:
            region: African region code
            
        Returns:
            Local business practices and cultural considerations
        """
        practices = {
            "NG": {
                "business_hours": {
                    "standard": "08:00-17:00",
                    "banking": "08:00-15:00",
                    "government": "08:00-16:00"
                },
                "payment_preferences": [
                    "Bank Transfer", "Mobile Money", "Cash", "Cheque"
                ],
                "communication_preferences": [
                    "WhatsApp Business", "SMS", "Email", "Phone Calls"
                ],
                "cultural_considerations": [
                    "Relationship-based business culture",
                    "Respect for hierarchy",
                    "Multi-language support (English, Hausa, Yoruba, Igbo)"
                ],
                "public_holidays": [
                    "New Year's Day", "Good Friday", "Easter Monday",
                    "Workers' Day", "Children's Day", "Democracy Day",
                    "Independence Day", "Christmas Day", "Boxing Day"
                ]
            },
            "ZA": {
                "business_hours": {
                    "standard": "08:00-17:00",
                    "banking": "09:00-15:30",
                    "government": "08:00-16:30"
                },
                "payment_preferences": [
                    "EFT", "Credit Card", "Debit Card", "Mobile Payments"
                ],
                "communication_preferences": [
                    "Email", "WhatsApp", "SMS", "Phone Calls"
                ],
                "cultural_considerations": [
                    "Multi-cultural environment",
                    "BEE compliance requirements",
                    "Multi-language support (English, Afrikaans, Zulu, Xhosa)"
                ],
                "public_holidays": [
                    "New Year's Day", "Human Rights Day", "Good Friday",
                    "Family Day", "Freedom Day", "Workers' Day",
                    "Youth Day", "National Women's Day", "Heritage Day",
                    "Day of Reconciliation", "Christmas Day", "Day of Goodwill"
                ]
            },
            "KE": {
                "business_hours": {
                    "standard": "08:00-17:00",
                    "banking": "09:00-15:00",
                    "government": "08:00-17:00"
                },
                "payment_preferences": [
                    "M-Pesa", "Bank Transfer", "Mobile Banking", "Cash"
                ],
                "communication_preferences": [
                    "WhatsApp", "SMS", "M-Pesa Messages", "Email"
                ],
                "cultural_considerations": [
                    "Mobile-first economy",
                    "Community-oriented business culture",
                    "Multi-language support (English, Swahili)"
                ],
                "public_holidays": [
                    "New Year's Day", "Good Friday", "Easter Monday",
                    "Labour Day", "Madaraka Day", "Mashujaa Day",
                    "Jamhuri Day", "Christmas Day", "Boxing Day"
                ]
            }
        }
        
        return practices.get(region, {})


# Export helper class
__all__ = ["AfricanERPHelper", "AfricanRegion", "LocalERPSystem"]
