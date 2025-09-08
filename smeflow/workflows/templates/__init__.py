"""
Modular Workflow Templates for SMEFlow.

This package provides industry-specific workflow templates organized by workflow type
for better maintainability and scalability.
"""

# Import base models and enums
from .base import (
    IndustryType,
    FormFieldType,
    FormField,
    IndustryTemplate,
    IndustryTemplateFactory
)

# Import all workflow template modules
from . import consulting
from . import healthcare
from . import retail
from . import compliance_workflows
from . import erp_integration
from . import marketing_campaigns

# Maintain backward compatibility - export everything that was previously available
__all__ = [
    "IndustryType",
    "FormFieldType", 
    "FormField",
    "IndustryTemplate",
    "IndustryTemplateFactory",
    "consulting",
    "healthcare", 
    "retail",
    "compliance_workflows",
    "erp_integration",
    "marketing_campaigns"
]
