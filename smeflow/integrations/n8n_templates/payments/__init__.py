"""
African Payment Provider Templates for n8N.

This module provides individual payment provider integrations optimized for African markets.
Each provider has its own module for better maintainability and feature isolation.
"""

from .mpesa import MpesaWorkflowTemplate
from .paystack import PaystackWorkflowTemplate

__all__ = [
    'MpesaWorkflowTemplate',
    'PaystackWorkflowTemplate'
]
