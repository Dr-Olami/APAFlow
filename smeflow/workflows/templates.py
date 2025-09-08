"""
Industry-Specific Workflow Templates for SMEFlow.

This module provides pre-built workflow templates tailored for different
African SME industries with customizable forms and business processes.

DEPRECATED: This file has been refactored into a modular structure.
Please import from smeflow.workflows.templates instead.
"""

# Import everything from the new modular structure for backward compatibility
from .templates import (
    IndustryType,
    FormFieldType,
    FormField,
    IndustryTemplate,
    IndustryTemplateFactory
)

# Re-export everything for backward compatibility
__all__ = [
    "IndustryType",
    "FormFieldType",
    "FormField",
    "IndustryTemplate",
    "IndustryTemplateFactory"
]
