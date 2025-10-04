"""
Unit tests for SMEFlow n8N Phase 2 Integration.

Tests webhook endpoints, credential management, and multi-tenant security
with comprehensive coverage of African market integrations.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from smeflow.integrations.n8n_webhooks import (
    WorkflowTriggerRequest,
    WorkflowTriggerResponse,
    ExecutionStatusResponse,
    TenantWorkflowsResponse
)
from smeflow.integrations.n8n_credentials import (
    N8nCredentialManager,
    CredentialCreate,
    CredentialUpdate,
    CredentialResponse,
    CredentialData,
    N8nCredential,
    AFRICAN_SERVICE_TEMPLATES
)
from smeflow.auth.jwt_middleware import UserInfo


class TestN8nWebhooks:
    """Test n8N webhook endpoints."""
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        return UserInfo(
            user_id=str(uuid4()),
            tenant_id=str(uuid4()),
            email="test@smeflow.com",
            roles=["user"]
        )
    
    @pytest.fixture
    def mock_n8n_client(self):
        """Mock n8N client."""
        with patch('smeflow.integrations.n8n_webhooks.SMEFlowN8nClient') as mock:
            client = AsyncMock()
            mock.return_value = client
            yield client
    
    @pytest.mark.asyncio
    async def test_trigger_workflow_success(self, mock_user, mock_n8n_client):
        """Test successful workflow trigger."""
        # Setup
        workflow_id = str(uuid4())
        execution_id = str(uuid4())
        
        # Mock workflow validation
        mock_n8n_client.get_workflow.return_value = {
            'id': workflow_id,
            'name': 'Test Workflow',
            'active': True,
            'tags': [f'tenant:{mock_user.tenant_id}']
        }
        
        # Mock workflow trigger
        mock_n8n_client.trigger_workflow.return_value = {
            'id': execution_id,
            'status': 'running'
        }
        
        # Test request
        request = WorkflowTriggerRequest(
            workflow_id=workflow_id,
            input_data={'test': 'data'},
            priority='high'
        )
        
        # Import and test the function
        from smeflow.integrations.n8n_webhooks import trigger_workflow
        
        with patch('smeflow.integrations.n8n_webhooks.get_n8n_client', return_value=mock_n8n_client):
            with patch('smeflow.integrations.n8n_webhooks.validate_tenant_workflow_access', return_value=True):
                response = await trigger_workflow(
                    workflow_id=workflow_id,
                    request=request,
                    background_tasks=MagicMock(),
                    user=mock_user,
                    db=MagicMock()
                )
        
        # Assertions
        assert response.workflow_id == workflow_id
        assert response.execution_id == execution_id
        assert response.status == 'running'
        assert response.tenant_id == mock_user.tenant_id
        
        # Verify client calls
        mock_n8n_client.trigger_workflow.assert_called_once()
        call_args = mock_n8n_client.trigger_workflow.call_args[0]
        assert call_args[0] == workflow_id
        assert call_args[1]['tenant_id'] == mock_user.tenant_id
        assert call_args[1]['priority'] == 'high'
    
    @pytest.mark.asyncio
    async def test_trigger_workflow_access_denied(self, mock_user, mock_n8n_client):
        """Test workflow trigger with access denied."""
        workflow_id = str(uuid4())
        
        request = WorkflowTriggerRequest(
            workflow_id=workflow_id,
            input_data={'test': 'data'}
        )
        
        from smeflow.integrations.n8n_webhooks import trigger_workflow
        from fastapi import HTTPException
        
        with patch('smeflow.integrations.n8n_webhooks.get_n8n_client', return_value=mock_n8n_client):
            with patch('smeflow.integrations.n8n_webhooks.validate_tenant_workflow_access', return_value=False):
                with pytest.raises(HTTPException) as exc_info:
                    await trigger_workflow(
                        workflow_id=workflow_id,
                        request=request,
                        background_tasks=MagicMock(),
                        user=mock_user,
                        db=MagicMock()
                    )
                
                assert exc_info.value.status_code == 403
                assert "does not have access" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_execution_status_success(self, mock_user, mock_n8n_client):
        """Test successful execution status retrieval."""
        execution_id = str(uuid4())
        workflow_id = str(uuid4())
        
        # Mock execution data
        mock_n8n_client.get_execution.return_value = {
            'id': execution_id,
            'workflowId': workflow_id,
            'status': 'success',
            'startedAt': '2025-10-04T12:00:00Z',
            'finishedAt': '2025-10-04T12:05:00Z',
            'data': {
                'tenant_id': mock_user.tenant_id,
                'resultData': {'result': 'success'}
            }
        }
        
        from smeflow.integrations.n8n_webhooks import get_execution_status
        
        with patch('smeflow.integrations.n8n_webhooks.get_n8n_client', return_value=mock_n8n_client):
            response = await get_execution_status(
                execution_id=execution_id,
                user=mock_user
            )
        
        # Assertions
        assert response.execution_id == execution_id
        assert response.workflow_id == workflow_id
        assert response.status == 'success'
        assert response.progress == 100.0
        assert response.tenant_id == mock_user.tenant_id
        assert response.result == {'result': 'success'}
    
    @pytest.mark.asyncio
    async def test_list_tenant_workflows_success(self, mock_user, mock_n8n_client):
        """Test successful tenant workflows listing."""
        tenant_tag = f"tenant:{mock_user.tenant_id}"
        
        # Mock workflows
        mock_n8n_client.get_workflows.return_value = [
            {
                'id': str(uuid4()),
                'name': 'Tenant Workflow',
                'active': True,
                'tags': [tenant_tag],
                'createdAt': '2025-10-04T10:00:00Z'
            },
            {
                'id': str(uuid4()),
                'name': 'Public Workflow',
                'active': True,
                'tags': ['public'],
                'createdAt': '2025-10-04T11:00:00Z'
            },
            {
                'id': str(uuid4()),
                'name': 'Other Tenant Workflow',
                'active': True,
                'tags': ['tenant:other-tenant'],
                'createdAt': '2025-10-04T12:00:00Z'
            }
        ]
        
        from smeflow.integrations.n8n_webhooks import list_tenant_workflows
        
        with patch('smeflow.integrations.n8n_webhooks.get_n8n_client', return_value=mock_n8n_client):
            response = await list_tenant_workflows(
                tenant_id=mock_user.tenant_id,
                user=mock_user
            )
        
        # Assertions
        assert response.tenant_id == mock_user.tenant_id
        assert response.total_count == 2  # Only tenant and public workflows
        assert response.active_count == 2
        
        # Check workflow details
        workflow_names = [w['name'] for w in response.workflows]
        assert 'Tenant Workflow' in workflow_names
        assert 'Public Workflow' in workflow_names
        assert 'Other Tenant Workflow' not in workflow_names


class TestN8nCredentialManager:
    """Test n8N credential management."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = MagicMock(spec=Session)
        return db
    
    @pytest.fixture
    def credential_manager(self, mock_db):
        """Create credential manager with mocked dependencies."""
        from cryptography.fernet import Fernet
        # Generate a valid Fernet key for testing
        test_key = Fernet.generate_key()
        
        with patch('smeflow.integrations.n8n_credentials.get_settings') as mock_settings:
            mock_settings.return_value.CREDENTIAL_ENCRYPTION_KEY = test_key
            manager = N8nCredentialManager(mock_db)
            return manager
    
    def test_validate_service_credentials_mpesa_success(self, credential_manager):
        """Test M-Pesa credential validation success."""
        credential_data = {
            'consumer_key': 'test_key',
            'consumer_secret': 'test_secret',
            'shortcode': '174379',
            'passkey': 'test_passkey'
        }
        
        result = credential_manager.validate_service_credentials('mpesa', credential_data)
        assert result is True
    
    def test_validate_service_credentials_mpesa_missing_fields(self, credential_manager):
        """Test M-Pesa credential validation with missing fields."""
        credential_data = {
            'consumer_key': 'test_key',
            # Missing required fields
        }
        
        with pytest.raises(ValueError) as exc_info:
            credential_manager.validate_service_credentials('mpesa', credential_data)
        
        assert "Missing required fields" in str(exc_info.value)
        assert "consumer_secret" in str(exc_info.value)
    
    def test_validate_service_credentials_paystack_success(self, credential_manager):
        """Test Paystack credential validation success."""
        credential_data = {
            'secret_key': 'sk_test_123',
            'public_key': 'pk_test_123'
        }
        
        result = credential_manager.validate_service_credentials('paystack', credential_data)
        assert result is True
    
    def test_validate_service_credentials_whatsapp_success(self, credential_manager):
        """Test WhatsApp credential validation success."""
        credential_data = {
            'access_token': 'test_token',
            'phone_number_id': '123456789'
        }
        
        result = credential_manager.validate_service_credentials('whatsapp', credential_data)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_create_credential_success(self, credential_manager, mock_db):
        """Test successful credential creation."""
        tenant_id = str(uuid4())
        user_id = str(uuid4())
        
        # Mock database query
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        request = CredentialCreate(
            credential_name='Test M-Pesa',
            service_type='mpesa',
            credential_data={
                'consumer_key': 'test_key',
                'consumer_secret': 'test_secret',
                'shortcode': '174379',
                'passkey': 'test_passkey'
            },
            metadata={'environment': 'sandbox'}
        )
        
        # Mock credential creation
        mock_credential = MagicMock()
        mock_credential.id = uuid4()
        mock_credential.tenant_id = tenant_id
        mock_credential.credential_name = request.credential_name
        mock_credential.service_type = request.service_type
        mock_credential.credential_metadata = request.metadata  # Use correct field name
        mock_credential.is_active = True
        mock_credential.expires_at = None
        mock_credential.created_at = datetime.utcnow()
        mock_credential.updated_at = datetime.utcnow()
        
        # Mock the database operations properly
        def mock_refresh(obj):
            # Simulate database refresh by setting the missing attributes
            obj.id = mock_credential.id
            obj.created_at = mock_credential.created_at
            obj.updated_at = mock_credential.updated_at
            obj.is_active = mock_credential.is_active
            obj.expires_at = mock_credential.expires_at
            return obj
        
        mock_db.refresh.side_effect = mock_refresh
        
        result = await credential_manager.create_credential(
            tenant_id=tenant_id,
            user_id=user_id,
            credential_request=request
        )
        
        # Assertions
        assert isinstance(result, CredentialResponse)
        assert result.credential_name == request.credential_name
        assert result.service_type == request.service_type
        assert result.tenant_id == tenant_id
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_credential_duplicate_name(self, credential_manager, mock_db):
        """Test credential creation with duplicate name."""
        tenant_id = str(uuid4())
        user_id = str(uuid4())
        
        # Mock existing credential
        existing_credential = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_credential
        
        request = CredentialCreate(
            credential_name='Existing Credential',
            service_type='mpesa',
            credential_data={
                'consumer_key': 'test_key',
                'consumer_secret': 'test_secret',
                'shortcode': '174379',
                'passkey': 'test_passkey'
            }
        )
        
        with pytest.raises(ValueError) as exc_info:
            await credential_manager.create_credential(
                tenant_id=tenant_id,
                user_id=user_id,
                credential_request=request
            )
        
        assert "already exists" in str(exc_info.value)
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_credential_with_data(self, credential_manager, mock_db):
        """Test getting credential with decrypted data."""
        tenant_id = str(uuid4())
        credential_id = str(uuid4())
        
        # Mock credential
        mock_credential = MagicMock()
        mock_credential.id = credential_id
        mock_credential.tenant_id = tenant_id
        mock_credential.credential_name = 'Test Credential'
        mock_credential.service_type = 'mpesa'
        mock_credential.expires_at = None
        mock_credential.credential_metadata = {}  # Use correct field name
        
        # Mock encrypted data
        test_data = {'consumer_key': 'test_key', 'consumer_secret': 'test_secret'}
        mock_credential.encrypted_data = credential_manager._encrypt_data(test_data)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_credential
        
        result = await credential_manager.get_credential(
            tenant_id=tenant_id,
            credential_id=credential_id,
            include_data=True
        )
        
        # Assertions
        assert isinstance(result, CredentialData)
        assert result.id == str(credential_id)
        assert result.credential_name == 'Test Credential'
        assert result.service_type == 'mpesa'
        assert result.data == test_data
    
    @pytest.mark.asyncio
    async def test_get_credential_access_denied(self, credential_manager, mock_db):
        """Test getting credential with wrong tenant."""
        tenant_id = str(uuid4())
        credential_id = str(uuid4())
        
        # Mock no credential found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError) as exc_info:
            await credential_manager.get_credential(
                tenant_id=tenant_id,
                credential_id=credential_id
            )
        
        assert "not found or access denied" in str(exc_info.value)
    
    def test_get_service_template_mpesa(self, credential_manager):
        """Test getting M-Pesa service template."""
        template = credential_manager.get_service_template('mpesa')
        
        assert template is not None
        assert 'required_fields' in template
        assert 'consumer_key' in template['required_fields']
        assert 'consumer_secret' in template['required_fields']
        assert template['description'] == 'M-Pesa payment integration for Kenya'
    
    def test_list_supported_services(self, credential_manager):
        """Test listing all supported services."""
        services = credential_manager.list_supported_services()
        
        assert isinstance(services, dict)
        assert 'mpesa' in services
        assert 'paystack' in services
        assert 'flutterwave' in services
        assert 'whatsapp' in services
        assert 'jumia' in services
        
        # Verify African market services are included
        african_services = ['mpesa', 'paystack', 'flutterwave', 'jumia']
        for service in african_services:
            assert service in services
            assert 'required_fields' in services[service]
            assert 'description' in services[service]


class TestAfricanServiceTemplates:
    """Test African market service templates."""
    
    def test_mpesa_template_structure(self):
        """Test M-Pesa template structure."""
        template = AFRICAN_SERVICE_TEMPLATES['mpesa']
        
        assert 'required_fields' in template
        assert 'optional_fields' in template
        assert 'description' in template
        assert 'validation_url' in template
        
        required_fields = template['required_fields']
        assert 'consumer_key' in required_fields
        assert 'consumer_secret' in required_fields
        assert 'shortcode' in required_fields
        assert 'passkey' in required_fields
        
        optional_fields = template['optional_fields']
        assert 'environment' in optional_fields
        assert 'callback_url' in optional_fields
    
    def test_paystack_template_structure(self):
        """Test Paystack template structure."""
        template = AFRICAN_SERVICE_TEMPLATES['paystack']
        
        required_fields = template['required_fields']
        assert 'secret_key' in required_fields
        assert 'public_key' in required_fields
        
        assert 'Nigeria' in template['description']
    
    def test_flutterwave_template_structure(self):
        """Test Flutterwave template structure."""
        template = AFRICAN_SERVICE_TEMPLATES['flutterwave']
        
        required_fields = template['required_fields']
        assert 'secret_key' in required_fields
        assert 'public_key' in required_fields
        assert 'encryption_key' in required_fields
        
        assert 'Africa' in template['description']
    
    def test_jumia_template_structure(self):
        """Test Jumia template structure."""
        template = AFRICAN_SERVICE_TEMPLATES['jumia']
        
        required_fields = template['required_fields']
        assert 'api_key' in required_fields
        assert 'seller_id' in required_fields
        
        assert 'e-commerce' in template['description']
    
    def test_whatsapp_template_structure(self):
        """Test WhatsApp template structure."""
        template = AFRICAN_SERVICE_TEMPLATES['whatsapp']
        
        required_fields = template['required_fields']
        assert 'access_token' in required_fields
        assert 'phone_number_id' in required_fields
        
        assert 'WhatsApp Business API' in template['description']
    
    def test_all_templates_have_required_structure(self):
        """Test that all templates have required structure."""
        required_keys = ['required_fields', 'description']
        
        for service_type, template in AFRICAN_SERVICE_TEMPLATES.items():
            for key in required_keys:
                assert key in template, f"Template {service_type} missing {key}"
            
            assert isinstance(template['required_fields'], list)
            assert isinstance(template['description'], str)
            assert len(template['description']) > 0


class TestN8nIntegrationSecurity:
    """Test security aspects of n8N integration."""
    
    def test_credential_encryption_decryption(self):
        """Test credential encryption and decryption."""
        from cryptography.fernet import Fernet
        # Generate a valid Fernet key for testing
        test_key = Fernet.generate_key()
        
        with patch('smeflow.integrations.n8n_credentials.get_settings') as mock_settings:
            mock_settings.return_value.CREDENTIAL_ENCRYPTION_KEY = test_key
            
            manager = N8nCredentialManager(MagicMock())
            
            # Test data
            original_data = {
                'consumer_key': 'test_key_123',
                'consumer_secret': 'secret_value_456',
                'shortcode': '174379'
            }
            
            # Encrypt
            encrypted = manager._encrypt_data(original_data)
            assert isinstance(encrypted, str)
            assert encrypted != json.dumps(original_data)
            
            # Decrypt
            decrypted = manager._decrypt_data(encrypted)
            assert decrypted == original_data
    
    def test_tenant_isolation_in_workflow_access(self):
        """Test tenant isolation in workflow access validation."""
        from smeflow.integrations.n8n_webhooks import validate_tenant_workflow_access
        
        # This would be tested with actual n8N client in integration tests
        # Here we test the logic structure
        tenant_id = str(uuid4())
        workflow_id = str(uuid4())
        
        # Mock client would be used in actual test
        # The function should check workflow tags for tenant access
        pass  # Placeholder for integration test
    
    def test_credential_access_logging(self):
        """Test that credential access is properly logged."""
        # This would test audit logging for credential access
        # Important for compliance and security monitoring
        pass  # Placeholder for integration test
