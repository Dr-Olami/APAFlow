"""
Communication Integration Templates for n8N.

This module provides workflow templates for communication services
optimized for African markets, including WhatsApp Business API,
SMS gateways, and email automation.
"""

from .whatsapp import WhatsAppWorkflowTemplate
from .sms import SMSWorkflowTemplate
from .email import EmailWorkflowTemplate

__all__ = [
    'WhatsAppWorkflowTemplate',
    'SMSWorkflowTemplate',
    'EmailWorkflowTemplate'
]
