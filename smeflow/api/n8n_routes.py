"""
SMEFlow n8N API Routes.

This module provides REST API endpoints for n8N integration including
webhook management, credential management, and workflow operations.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from smeflow.auth.jwt_middleware import get_current_user, UserInfo
from smeflow.database.connection import get_db_session
from smeflow.integrations.n8n_webhooks import router as webhook_router
from smeflow.integrations.n8n_credentials import (
    N8nCredentialManager,
    CredentialCreate,
    CredentialUpdate,
    CredentialResponse,
    CredentialData,
    AFRICAN_SERVICE_TEMPLATES
)

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/n8n", tags=["n8n-integration"])

# Include webhook routes
router.include_router(webhook_router)

# Credential Management Routes
@router.post("/credentials", response_model=CredentialResponse)
async def create_credential(
    credential_request: CredentialCreate,
    user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Create new n8N credential with encryption and tenant isolation.
    
    This endpoint allows authenticated users to create encrypted credentials
    for external services used in n8N workflows.
    """
    try:
        manager = N8nCredentialManager(db)
        
        credential = await manager.create_credential(
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            credential_request=credential_request
        )
        
        return credential
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating credential: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create credential")

@router.get("/credentials", response_model=List[CredentialResponse])
async def list_credentials(
    user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    service_type: Optional[str] = None,
    active_only: bool = True
):
    """
    List n8N credentials for the current tenant.
    
    Returns all credentials accessible to the current tenant,
    with optional filtering by service type.
    """
    try:
        manager = N8nCredentialManager(db)
        
        credentials = await manager.list_credentials(
            tenant_id=user.tenant_id,
            service_type=service_type,
            active_only=active_only
        )
        
        return credentials
        
    except Exception as e:
        logger.error(f"Error listing credentials: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list credentials")

@router.get("/credentials/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    credential_id: str,
    user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get n8N credential details (without sensitive data).
    
    Returns credential metadata and configuration without
    exposing the actual credential values.
    """
    try:
        manager = N8nCredentialManager(db)
        
        credential = await manager.get_credential(
            tenant_id=user.tenant_id,
            credential_id=credential_id,
            include_data=False
        )
        
        return credential
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting credential {credential_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get credential")

@router.get("/credentials/{credential_id}/data", response_model=CredentialData)
async def get_credential_data(
    credential_id: str,
    user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get decrypted n8N credential data.
    
    Returns the actual credential values for use in workflows.
    This endpoint should be used carefully and only when necessary.
    """
    try:
        manager = N8nCredentialManager(db)
        
        credential = await manager.get_credential(
            tenant_id=user.tenant_id,
            credential_id=credential_id,
            include_data=True
        )
        
        # Log access for security audit
        logger.info(
            f"Credential data accessed - ID: {credential_id}, "
            f"Tenant: {user.tenant_id}, User: {user.email}"
        )
        
        return credential
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting credential data {credential_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get credential data")

@router.put("/credentials/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: str,
    update_request: CredentialUpdate,
    user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Update existing n8N credential.
    
    Allows updating credential data, metadata, and configuration
    while maintaining encryption and tenant isolation.
    """
    try:
        manager = N8nCredentialManager(db)
        
        credential = await manager.update_credential(
            tenant_id=user.tenant_id,
            credential_id=credential_id,
            user_id=user.user_id,
            update_request=update_request
        )
        
        return credential
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating credential {credential_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update credential")

@router.delete("/credentials/{credential_id}")
async def delete_credential(
    credential_id: str,
    user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Delete n8N credential (soft delete).
    
    Marks the credential as inactive rather than permanently deleting it
    to maintain audit trails and prevent data loss.
    """
    try:
        manager = N8nCredentialManager(db)
        
        success = await manager.delete_credential(
            tenant_id=user.tenant_id,
            credential_id=credential_id,
            user_id=user.user_id
        )
        
        if success:
            return {"message": "Credential deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete credential")
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting credential {credential_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete credential")

# Service Template Routes
@router.get("/services")
async def list_supported_services():
    """
    List all supported African market services.
    
    Returns templates and requirements for all supported
    external services that can be integrated with n8N.
    """
    return {
        "services": AFRICAN_SERVICE_TEMPLATES,
        "total_count": len(AFRICAN_SERVICE_TEMPLATES),
        "categories": {
            "payment": ["mpesa", "paystack", "flutterwave"],
            "ecommerce": ["jumia"],
            "communication": ["whatsapp", "sms", "email", "sendgrid", "mailgun"],
            "integration": ["database", "api", "oauth", "basic_auth"]
        }
    }

@router.get("/services/{service_type}")
async def get_service_template(service_type: str):
    """
    Get service template for specific service type.
    
    Returns the required fields, validation rules, and
    configuration template for a specific service.
    """
    template = AFRICAN_SERVICE_TEMPLATES.get(service_type.lower())
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Service type '{service_type}' not supported"
        )
    
    return {
        "service_type": service_type.lower(),
        "template": template,
        "example": _get_service_example(service_type.lower())
    }

# Workflow Management Routes (Basic)
@router.get("/workflows/templates")
async def list_workflow_templates(
    user: UserInfo = Depends(get_current_user)
):
    """
    List available n8N workflow templates.
    
    Returns workflow templates available to the current tenant,
    including both tenant-specific and public templates.
    """
    try:
        from smeflow.integrations.n8n_wrapper import SMEFlowN8nClient, N8nConfig
        from smeflow.core.config import get_settings
        
        settings = get_settings()
        config = N8nConfig(
            base_url=settings.N8N_BASE_URL or "http://localhost:5678",
            api_key=settings.N8N_API_KEY or "default-api-key"
        )
        
        client = SMEFlowN8nClient(config=config)
        templates = client.get_available_templates()
        
        return {
            "templates": templates,
            "total_count": len(templates),
            "tenant_id": user.tenant_id
        }
        
    except Exception as e:
        logger.error(f"Error listing workflow templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list workflow templates")

# Helper functions
def _get_service_example(service_type: str) -> dict:
    """Get example credential data for service type."""
    examples = {
        'mpesa': {
            'consumer_key': 'your_consumer_key',
            'consumer_secret': 'your_consumer_secret',
            'shortcode': '174379',
            'passkey': 'your_passkey',
            'environment': 'sandbox'
        },
        'paystack': {
            'secret_key': 'sk_test_your_secret_key',
            'public_key': 'pk_test_your_public_key',
            'webhook_secret': 'your_webhook_secret'
        },
        'flutterwave': {
            'secret_key': 'FLWSECK_TEST-your_secret_key',
            'public_key': 'FLWPUBK_TEST-your_public_key',
            'encryption_key': 'FLWSECK_TEST-your_encryption_key'
        },
        'jumia': {
            'api_key': 'your_jumia_api_key',
            'seller_id': 'your_seller_id',
            'environment': 'sandbox'
        },
        'whatsapp': {
            'access_token': 'your_whatsapp_access_token',
            'phone_number_id': 'your_phone_number_id',
            'webhook_verify_token': 'your_verify_token'
        }
    }
    
    return examples.get(service_type, {})
