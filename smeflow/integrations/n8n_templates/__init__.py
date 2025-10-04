"""
n8N Workflow Templates for SMEFlow Platform.

This module provides pre-built n8N workflow templates optimized for African markets,
organized by service category for better maintainability and feature isolation.

Structure:
- payments/: Payment provider integrations (M-Pesa, Paystack, Flutterwave)
- ecommerce/: E-commerce platform integrations (Jumia, Konga)
- communication/: Communication service integrations (WhatsApp, SMS)
- base_template.py: Foundation classes for all templates
"""

from .base_template import N8nWorkflowTemplate
from .payments import MpesaWorkflowTemplate, PaystackWorkflowTemplate
from .ecommerce import JumiaWorkflowTemplate
from .communication import WhatsAppWorkflowTemplate, SMSWorkflowTemplate, EmailWorkflowTemplate

__all__ = [
    'N8nWorkflowTemplate',
    'MpesaWorkflowTemplate', 
    'PaystackWorkflowTemplate',
    'JumiaWorkflowTemplate',
    'WhatsAppWorkflowTemplate',
    'SMSWorkflowTemplate',
    'EmailWorkflowTemplate'
]
