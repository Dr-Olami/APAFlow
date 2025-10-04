"""
SMEFlow n8N Credential Management System.

This module provides secure credential management for n8N workflows with
multi-tenant isolation, encryption, and African market service integrations.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from cryptography.fernet import Fernet
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Session

from smeflow.database.models import Base
from smeflow.core.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)

# Database Models
class N8nCredential(Base):
    """Database model for n8N credentials with tenant isolation."""
    
    __tablename__ = "n8n_credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    credential_name = Column(String(255), nullable=False)
    service_type = Column(String(100), nullable=False)  # e.g., 'mpesa', 'paystack', 'whatsapp'
    encrypted_data = Column(Text, nullable=False)  # Encrypted credential data
    credential_metadata = Column(JSONB, default=dict)  # Additional metadata
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    
    def __repr__(self):
        return f"<N8nCredential(id={self.id}, tenant={self.tenant_id}, service={self.service_type})>"

# Pydantic Models
class CredentialCreate(BaseModel):
    """Model for creating new credentials."""
    credential_name: str = Field(..., min_length=1, max_length=255)
    service_type: str = Field(..., description="Service type (mpesa, paystack, whatsapp, etc.)")
    credential_data: Dict[str, Any] = Field(..., description="Credential data to encrypt")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    expires_in_days: Optional[int] = Field(None, description="Expiration in days")
    
    @field_validator('service_type')
    @classmethod
    def validate_service_type(cls, v):
        allowed_services = [
            'mpesa', 'paystack', 'flutterwave', 'jumia',
            'whatsapp', 'sms', 'email', 'sendgrid', 'mailgun',
            'database', 'api', 'oauth', 'basic_auth'
        ]
        if v.lower() not in allowed_services:
            raise ValueError(f'Service type must be one of: {", ".join(allowed_services)}')
        return v.lower()

class CredentialUpdate(BaseModel):
    """Model for updating existing credentials."""
    credential_name: Optional[str] = Field(None, min_length=1, max_length=255)
    credential_data: Optional[Dict[str, Any]] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)
    is_active: Optional[bool] = Field(None)
    expires_in_days: Optional[int] = Field(None)

class CredentialResponse(BaseModel):
    """Model for credential responses (without sensitive data)."""
    id: str
    tenant_id: str
    credential_name: str
    service_type: str
    metadata: Dict[str, Any]
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    has_expired: bool

class CredentialData(BaseModel):
    """Model for decrypted credential data."""
    id: str
    credential_name: str
    service_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]

# African Market Service Templates
AFRICAN_SERVICE_TEMPLATES = {
    'mpesa': {
        'required_fields': ['consumer_key', 'consumer_secret', 'shortcode', 'passkey'],
        'optional_fields': ['environment', 'callback_url'],
        'description': 'M-Pesa payment integration for Kenya',
        'validation_url': 'https://sandbox.safaricom.co.ke/oauth/v1/generate'
    },
    'paystack': {
        'required_fields': ['secret_key', 'public_key'],
        'optional_fields': ['webhook_secret', 'callback_url'],
        'description': 'Paystack payment integration for Nigeria',
        'validation_url': 'https://api.paystack.co/bank'
    },
    'flutterwave': {
        'required_fields': ['secret_key', 'public_key', 'encryption_key'],
        'optional_fields': ['webhook_secret', 'callback_url'],
        'description': 'Flutterwave payment integration for Africa',
        'validation_url': 'https://api.flutterwave.com/v3/banks'
    },
    'jumia': {
        'required_fields': ['api_key', 'seller_id'],
        'optional_fields': ['webhook_secret', 'environment'],
        'description': 'Jumia e-commerce integration',
        'validation_url': 'https://api.jumia.com/v1/sellers'
    },
    'whatsapp': {
        'required_fields': ['access_token', 'phone_number_id'],
        'optional_fields': ['webhook_verify_token', 'business_account_id'],
        'description': 'WhatsApp Business API integration',
        'validation_url': 'https://graph.facebook.com/v17.0/me'
    }
}

class N8nCredentialManager:
    """Manage n8N credentials with encryption and tenant isolation."""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self._encryption_key = self._get_encryption_key()
        self.cipher = Fernet(self._encryption_key)
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key for credentials."""
        # In production, this should come from a secure key management service
        key = self.settings.CREDENTIAL_ENCRYPTION_KEY
        if not key:
            # Generate a new key (should be stored securely)
            key = Fernet.generate_key()
            logger.warning("Generated new encryption key - store this securely!")
        
        if isinstance(key, str):
            key = key.encode()
        
        return key
    
    def _encrypt_data(self, data: Dict[str, Any]) -> str:
        """Encrypt credential data."""
        try:
            json_data = json.dumps(data, sort_keys=True)
            encrypted_data = self.cipher.encrypt(json_data.encode())
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Error encrypting credential data: {str(e)}")
            raise ValueError("Failed to encrypt credential data")
    
    def _decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt credential data."""
        try:
            decrypted_data = self.cipher.decrypt(encrypted_data.encode())
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Error decrypting credential data: {str(e)}")
            raise ValueError("Failed to decrypt credential data")
    
    def validate_service_credentials(self, service_type: str, credential_data: Dict[str, Any]) -> bool:
        """Validate credential data for specific service type."""
        template = AFRICAN_SERVICE_TEMPLATES.get(service_type)
        if not template:
            return True  # Skip validation for unknown services
        
        required_fields = template.get('required_fields', [])
        missing_fields = [field for field in required_fields if field not in credential_data]
        
        if missing_fields:
            raise ValueError(f"Missing required fields for {service_type}: {', '.join(missing_fields)}")
        
        return True
    
    async def create_credential(
        self,
        tenant_id: str,
        user_id: str,
        credential_request: CredentialCreate
    ) -> CredentialResponse:
        """Create new encrypted credential for tenant."""
        try:
            # Validate service credentials
            self.validate_service_credentials(
                credential_request.service_type,
                credential_request.credential_data
            )
            
            # Check for duplicate credential names within tenant
            existing = self.db.query(N8nCredential).filter(
                N8nCredential.tenant_id == tenant_id,
                N8nCredential.credential_name == credential_request.credential_name,
                N8nCredential.is_active == True
            ).first()
            
            if existing:
                raise ValueError(f"Credential '{credential_request.credential_name}' already exists")
            
            # Calculate expiration date
            expires_at = None
            if credential_request.expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=credential_request.expires_in_days)
            
            # Encrypt credential data
            encrypted_data = self._encrypt_data(credential_request.credential_data)
            
            # Create credential record
            credential = N8nCredential(
                tenant_id=tenant_id,
                credential_name=credential_request.credential_name,
                service_type=credential_request.service_type,
                encrypted_data=encrypted_data,
                credential_metadata=credential_request.metadata,
                expires_at=expires_at,
                created_by=user_id
            )
            
            self.db.add(credential)
            self.db.commit()
            self.db.refresh(credential)
            
            logger.info(
                f"Created credential - Tenant: {tenant_id}, Name: {credential_request.credential_name}, "
                f"Service: {credential_request.service_type}"
            )
            
            return self._to_response_model(credential)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating credential: {str(e)}")
            raise
    
    async def get_credential(
        self,
        tenant_id: str,
        credential_id: str,
        include_data: bool = False
    ) -> Union[CredentialResponse, CredentialData]:
        """Get credential by ID with tenant validation."""
        try:
            credential = self.db.query(N8nCredential).filter(
                N8nCredential.id == credential_id,
                N8nCredential.tenant_id == tenant_id,
                N8nCredential.is_active == True
            ).first()
            
            if not credential:
                raise ValueError(f"Credential {credential_id} not found or access denied")
            
            # Check expiration
            if credential.expires_at and credential.expires_at < datetime.utcnow():
                raise ValueError(f"Credential {credential_id} has expired")
            
            if include_data:
                # Decrypt and return full data
                decrypted_data = self._decrypt_data(credential.encrypted_data)
                return CredentialData(
                    id=str(credential.id),
                    credential_name=credential.credential_name,
                    service_type=credential.service_type,
                    data=decrypted_data,
                    metadata=credential.credential_metadata
                )
            else:
                # Return metadata only
                return self._to_response_model(credential)
        except Exception as e:
            logger.error(f"Error getting credential {credential_id}: {str(e)}")
            raise
    
    async def list_credentials(
        self,
        tenant_id: str,
        service_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[CredentialResponse]:
        """List credentials for tenant with optional filtering."""
        try:
            query = self.db.query(N8nCredential).filter(
                N8nCredential.tenant_id == tenant_id
            )
            
            if active_only:
                query = query.filter(N8nCredential.is_active == True)
            
            if service_type:
                query = query.filter(N8nCredential.service_type == service_type)
            
            credentials = query.order_by(N8nCredential.created_at.desc()).all()
            
            return [self._to_response_model(cred) for cred in credentials]
            
        except Exception as e:
            logger.error(f"Error listing credentials for tenant {tenant_id}: {str(e)}")
            raise
    
    async def update_credential(
        self,
        tenant_id: str,
        credential_id: str,
        user_id: str,
        update_request: CredentialUpdate
    ) -> CredentialResponse:
        """Update existing credential."""
        try:
            credential = self.db.query(N8nCredential).filter(
                N8nCredential.id == credential_id,
                N8nCredential.tenant_id == tenant_id,
                N8nCredential.is_active == True
            ).first()
            
            if not credential:
                raise ValueError(f"Credential {credential_id} not found or access denied")
            
            # Update fields
            if update_request.credential_name:
                credential.credential_name = update_request.credential_name
            
            if update_request.credential_data:
                # Validate new credential data
                self.validate_service_credentials(
                    credential.service_type,
                    update_request.credential_data
                )
                credential.encrypted_data = self._encrypt_data(update_request.credential_data)
            
            if update_request.metadata is not None:
                credential.credential_metadata = update_request.metadata
            
            if update_request.is_active is not None:
                credential.is_active = update_request.is_active
            
            if update_request.expires_in_days:
                credential.expires_at = datetime.utcnow() + timedelta(days=update_request.expires_in_days)
            
            credential.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(credential)
            
            logger.info(f"Updated credential {credential_id} for tenant {tenant_id}")
            
            return self._to_response_model(credential)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating credential {credential_id}: {str(e)}")
            raise
    
    async def delete_credential(
        self,
        tenant_id: str,
        credential_id: str,
        user_id: str
    ) -> bool:
        """Soft delete credential (mark as inactive)."""
        try:
            credential = self.db.query(N8nCredential).filter(
                N8nCredential.id == credential_id,
                N8nCredential.tenant_id == tenant_id,
                N8nCredential.is_active == True
            ).first()
            
            if not credential:
                raise ValueError(f"Credential {credential_id} not found or access denied")
            
            # Soft delete
            credential.is_active = False
            credential.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Deleted credential {credential_id} for tenant {tenant_id}")
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting credential {credential_id}: {str(e)}")
            raise
    
    def _to_response_model(self, credential: N8nCredential) -> CredentialResponse:
        """Convert database model to response model."""
        has_expired = (
            credential.expires_at is not None and
            credential.expires_at < datetime.utcnow()
        )
        
        return CredentialResponse(
            id=str(credential.id),
            tenant_id=str(credential.tenant_id),
            credential_name=credential.credential_name,
            service_type=credential.service_type,
            metadata=credential.credential_metadata,
            is_active=credential.is_active,
            expires_at=credential.expires_at,
            created_at=credential.created_at,
            updated_at=credential.updated_at,
            has_expired=has_expired
        )
    
    def get_service_template(self, service_type: str) -> Optional[Dict[str, Any]]:
        """Get service template for credential validation."""
        return AFRICAN_SERVICE_TEMPLATES.get(service_type)
    
    def list_supported_services(self) -> Dict[str, Dict[str, Any]]:
        """List all supported African market services."""
        return AFRICAN_SERVICE_TEMPLATES
