"""
Tests for agent persistence functionality in SMEFlow.

Tests agent configuration storage, lifecycle management, and tenant isolation
with comprehensive coverage of CRUD operations.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from smeflow.agents.persistence import (
    AgentPersistenceService,
    AgentPersistenceConfig,
    AgentPersistenceData,
    agent_persistence_service
)
from smeflow.agents.base import AgentType, AgentStatus
from smeflow.database.models import Agent as AgentModel, Tenant


class TestAgentPersistenceConfig:
    """Test agent persistence configuration validation."""
    
    def test_valid_automator_config(self):
        """Test valid automator agent configuration."""
        config = AgentPersistenceConfig(
            agent_type=AgentType.AUTOMATOR,
            llm_provider="openai",
            llm_model="gpt-4",
            tools=["web_search", "calculator"],
            region="NG",
            timezone="Africa/Lagos",
            languages=["en", "ha"],
            currency="NGN"
        )
        
        assert config.agent_type == AgentType.AUTOMATOR
        assert config.llm_provider == "openai"
        assert config.tools == ["web_search", "calculator"]
        assert config.region == "NG"
        assert config.currency == "NGN"
    
    def test_valid_mentor_config(self):
        """Test valid mentor agent configuration."""
        config = AgentPersistenceConfig(
            agent_type=AgentType.MENTOR,
            llm_provider="anthropic",
            llm_model="claude-3-sonnet",
            tools=[],  # Mentor agents don't require tools
            region="KE",
            timezone="Africa/Nairobi",
            languages=["en", "sw"],
            currency="KES"
        )
        
        assert config.agent_type == AgentType.MENTOR
        assert config.llm_provider == "anthropic"
        assert config.tools == []
        assert config.region == "KE"
        assert config.currency == "KES"
    
    def test_automator_requires_tools(self):
        """Test that automator agents must have tools."""
        with pytest.raises(ValueError, match="Automator agents must have at least one tool"):
            AgentPersistenceConfig(
                agent_type=AgentType.AUTOMATOR,
                llm_provider="openai",
                llm_model="gpt-4",
                tools=[]  # Empty tools should fail for automator
            )
    
    def test_invalid_language(self):
        """Test validation of language codes."""
        with pytest.raises(ValueError, match="Unsupported language"):
            AgentPersistenceConfig(
                agent_type=AgentType.MENTOR,
                llm_provider="openai",
                llm_model="gpt-4",
                languages=["invalid_lang"]
            )
    
    def test_temperature_validation(self):
        """Test temperature parameter validation."""
        # Valid temperature
        config = AgentPersistenceConfig(
            agent_type=AgentType.MENTOR,
            llm_provider="openai",
            llm_model="gpt-4",
            temperature=1.5
        )
        assert config.temperature == 1.5
        
        # Invalid temperature (too high)
        with pytest.raises(ValueError):
            AgentPersistenceConfig(
                agent_type=AgentType.MENTOR,
                llm_provider="openai",
                llm_model="gpt-4",
                temperature=3.0
            )


class TestAgentPersistenceData:
    """Test agent persistence data model."""
    
    def test_valid_persistence_data(self):
        """Test valid agent persistence data."""
        config = AgentPersistenceConfig(
            agent_type=AgentType.SUPERVISOR,
            llm_provider="openai",
            llm_model="gpt-4"
        )
        
        data = AgentPersistenceData(
            tenant_id="test-tenant",
            name="Test Supervisor",
            description="A test supervisor agent",
            agent_type=AgentType.SUPERVISOR,
            config=config
        )
        
        assert data.tenant_id == "test-tenant"
        assert data.name == "Test Supervisor"
        assert data.agent_type == AgentType.SUPERVISOR
        assert data.status == AgentStatus.INACTIVE  # Default status
        assert data.is_active is True  # Default active state


class TestAgentPersistenceService:
    """Test agent persistence service operations."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def persistence_service(self):
        """Agent persistence service instance."""
        return AgentPersistenceService()
    
    @pytest.fixture
    def sample_config(self):
        """Sample agent configuration."""
        return AgentPersistenceConfig(
            agent_type=AgentType.AUTOMATOR,
            llm_provider="openai",
            llm_model="gpt-4",
            tools=["web_search"],
            region="NG",
            timezone="Africa/Lagos",
            languages=["en"],
            currency="NGN"
        )
    
    @pytest.fixture
    def sample_agent_data(self, sample_config):
        """Sample agent persistence data."""
        return AgentPersistenceData(
            tenant_id="test-tenant",
            name="Test Automator",
            description="A test automator agent",
            agent_type=AgentType.AUTOMATOR,
            config=sample_config
        )
    
    def test_create_agent_success(self, persistence_service, sample_agent_data, mock_db_session):
        """Test successful agent creation."""
        # Mock tenant exists
        mock_tenant = Mock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_tenant
        
        # Mock no existing agent with same name
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_tenant,  # Tenant exists
            None  # No existing agent
        ]
        
        # Mock database operations
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()
        
        # Mock created agent
        created_agent = Mock(spec=AgentModel)
        created_agent.id = uuid.uuid4()
        created_agent.tenant_id = "test-tenant"
        created_agent.name = "Test Automator"
        created_agent.type = "automator"
        created_agent.description = "A test automator agent"
        created_agent.config = sample_agent_data.config.model_dump()
        created_agent.prompts = {}
        created_agent.is_active = True
        created_agent.created_at = datetime.utcnow()
        created_agent.updated_at = datetime.utcnow()
        
        mock_db_session.refresh.side_effect = lambda obj: setattr(obj, 'id', created_agent.id)
        
        with patch('smeflow.agents.persistence.get_db_session', return_value=mock_db_session):
            # Create agent
            result = persistence_service.create_agent(sample_agent_data, mock_db_session)
            
            # Verify database operations
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once()
            
            # Verify result
            assert result.tenant_id == "test-tenant"
            assert result.name == "Test Automator"
            assert result.agent_type == AgentType.AUTOMATOR
    
    def test_create_agent_tenant_not_found(self, persistence_service, sample_agent_data, mock_db_session):
        """Test agent creation with non-existent tenant."""
        # Mock tenant doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with patch('smeflow.agents.persistence.get_db_session', return_value=mock_db_session):
            with pytest.raises(ValueError, match="Tenant test-tenant not found"):
                persistence_service.create_agent(sample_agent_data, mock_db_session)
    
    def test_create_agent_name_conflict(self, persistence_service, sample_agent_data, mock_db_session):
        """Test agent creation with name conflict."""
        # Mock tenant exists
        mock_tenant = Mock()
        mock_existing_agent = Mock()
        
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_tenant,  # Tenant exists
            mock_existing_agent  # Agent with same name exists
        ]
        
        with patch('smeflow.agents.persistence.get_db_session', return_value=mock_db_session):
            with pytest.raises(IntegrityError):
                persistence_service.create_agent(sample_agent_data, mock_db_session)
    
    def test_get_agent_success(self, persistence_service, mock_db_session):
        """Test successful agent retrieval."""
        agent_id = uuid.uuid4()
        tenant_id = "test-tenant"
        
        # Mock database agent
        mock_agent = Mock(spec=AgentModel)
        mock_agent.id = agent_id
        mock_agent.tenant_id = tenant_id
        mock_agent.name = "Test Agent"
        mock_agent.type = "mentor"
        mock_agent.description = "Test description"
        mock_agent.config = {
            "agent_type": "mentor",
            "llm_provider": "openai",
            "llm_model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": None,
            "tools": [],
            "system_prompt": None,
            "custom_prompts": {},
            "region": "NG",
            "timezone": "Africa/Lagos",
            "languages": ["en"],
            "currency": "NGN",
            "timeout_seconds": 30,
            "max_retries": 3,
            "enable_caching": True,
            "tenant_settings": {}
        }
        mock_agent.prompts = {}
        mock_agent.is_active = True
        mock_agent.created_at = datetime.utcnow()
        mock_agent.updated_at = datetime.utcnow()
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_agent
        
        with patch('smeflow.agents.persistence.get_db_session', return_value=mock_db_session):
            result = persistence_service.get_agent(agent_id, tenant_id, mock_db_session)
            
            assert result is not None
            assert result.id == agent_id
            assert result.tenant_id == tenant_id
            assert result.name == "Test Agent"
            assert result.agent_type == AgentType.MENTOR
    
    def test_get_agent_not_found(self, persistence_service, mock_db_session):
        """Test agent retrieval when agent doesn't exist."""
        agent_id = uuid.uuid4()
        tenant_id = "test-tenant"
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with patch('smeflow.agents.persistence.get_db_session', return_value=mock_db_session):
            result = persistence_service.get_agent(agent_id, tenant_id, mock_db_session)
            
            assert result is None
    
    def test_list_agents_success(self, persistence_service, mock_db_session):
        """Test successful agent listing."""
        tenant_id = "test-tenant"
        
        # Mock database agents
        mock_agents = []
        for i in range(3):
            mock_agent = Mock(spec=AgentModel)
            mock_agent.id = uuid.uuid4()
            mock_agent.tenant_id = tenant_id
            mock_agent.name = f"Test Agent {i}"
            mock_agent.type = "automator"
            mock_agent.description = f"Test description {i}"
            mock_agent.config = {
                "agent_type": "automator",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": None,
                "tools": ["web_search"],
                "system_prompt": None,
                "custom_prompts": {},
                "region": "NG",
                "timezone": "Africa/Lagos",
                "languages": ["en"],
                "currency": "NGN",
                "timeout_seconds": 30,
                "max_retries": 3,
                "enable_caching": True,
                "tenant_settings": {}
            }
            mock_agent.prompts = {}
            mock_agent.is_active = True
            mock_agent.created_at = datetime.utcnow()
            mock_agent.updated_at = datetime.utcnow()
            mock_agents.append(mock_agent)
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_agents
        mock_db_session.query.return_value = mock_query
        
        with patch('smeflow.agents.persistence.get_db_session', return_value=mock_db_session):
            result = persistence_service.list_agents(tenant_id, db=mock_db_session)
            
            assert len(result) == 3
            assert all(agent.tenant_id == tenant_id for agent in result)
            assert all(agent.agent_type == AgentType.AUTOMATOR for agent in result)
    
    def test_update_agent_success(self, persistence_service, mock_db_session):
        """Test successful agent update."""
        agent_id = uuid.uuid4()
        tenant_id = "test-tenant"
        
        # Mock existing agent
        mock_agent = Mock(spec=AgentModel)
        mock_agent.id = agent_id
        mock_agent.tenant_id = tenant_id
        mock_agent.name = "Original Name"
        mock_agent.type = "mentor"
        mock_agent.config = {
            "agent_type": "mentor",
            "llm_provider": "openai",
            "llm_model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": None,
            "tools": [],
            "system_prompt": None,
            "custom_prompts": {},
            "region": "NG",
            "timezone": "Africa/Lagos",
            "languages": ["en"],
            "currency": "NGN",
            "timeout_seconds": 30,
            "max_retries": 3,
            "enable_caching": True,
            "tenant_settings": {}
        }
        mock_agent.prompts = {}
        mock_agent.is_active = True
        mock_agent.created_at = datetime.utcnow()
        mock_agent.updated_at = datetime.utcnow()
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_agent
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()
        
        updates = {
            "name": "Updated Name",
            "description": "Updated description"
        }
        
        with patch('smeflow.agents.persistence.get_db_session', return_value=mock_db_session):
            result = persistence_service.update_agent(agent_id, tenant_id, updates, mock_db_session)
            
            assert result is not None
            assert mock_agent.name == "Updated Name"
            assert mock_agent.description == "Updated description"
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once()
    
    def test_update_agent_not_found(self, persistence_service, mock_db_session):
        """Test agent update when agent doesn't exist."""
        agent_id = uuid.uuid4()
        tenant_id = "test-tenant"
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        updates = {"name": "Updated Name"}
        
        with patch('smeflow.agents.persistence.get_db_session', return_value=mock_db_session):
            result = persistence_service.update_agent(agent_id, tenant_id, updates, mock_db_session)
            
            assert result is None
    
    def test_delete_agent_soft_delete(self, persistence_service, mock_db_session):
        """Test soft delete of agent."""
        agent_id = uuid.uuid4()
        tenant_id = "test-tenant"
        
        # Mock existing agent
        mock_agent = Mock(spec=AgentModel)
        mock_agent.id = agent_id
        mock_agent.tenant_id = tenant_id
        mock_agent.is_active = True
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_agent
        mock_db_session.commit = Mock()
        
        with patch('smeflow.agents.persistence.get_db_session', return_value=mock_db_session):
            result = persistence_service.delete_agent(agent_id, tenant_id, soft_delete=True, db=mock_db_session)
            
            assert result is True
            assert mock_agent.is_active is False
            mock_db_session.commit.assert_called_once()
    
    def test_delete_agent_hard_delete(self, persistence_service, mock_db_session):
        """Test hard delete of agent."""
        agent_id = uuid.uuid4()
        tenant_id = "test-tenant"
        
        # Mock existing agent
        mock_agent = Mock(spec=AgentModel)
        mock_agent.id = agent_id
        mock_agent.tenant_id = tenant_id
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_agent
        mock_db_session.delete = Mock()
        mock_db_session.commit = Mock()
        
        with patch('smeflow.agents.persistence.get_db_session', return_value=mock_db_session):
            result = persistence_service.delete_agent(agent_id, tenant_id, soft_delete=False, db=mock_db_session)
            
            assert result is True
            mock_db_session.delete.assert_called_once_with(mock_agent)
            mock_db_session.commit.assert_called_once()
    
    def test_delete_agent_not_found(self, persistence_service, mock_db_session):
        """Test delete when agent doesn't exist."""
        agent_id = uuid.uuid4()
        tenant_id = "test-tenant"
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with patch('smeflow.agents.persistence.get_db_session', return_value=mock_db_session):
            result = persistence_service.delete_agent(agent_id, tenant_id, db=mock_db_session)
            
            assert result is False


class TestTenantIsolation:
    """Test tenant isolation in persistence operations."""
    
    @pytest.fixture
    def persistence_service(self):
        """Agent persistence service instance."""
        return AgentPersistenceService()
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    def test_get_agent_tenant_isolation(self, persistence_service, mock_db_session):
        """Test that agents are isolated by tenant."""
        agent_id = uuid.uuid4()
        tenant_a = "tenant-a"
        tenant_b = "tenant-b"
        
        # Mock agent exists for tenant A but not accessible to tenant B
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with patch('smeflow.agents.persistence.get_db_session', return_value=mock_db_session):
            result = persistence_service.get_agent(agent_id, tenant_b, mock_db_session)
            
            assert result is None
            
            # Verify the query included tenant isolation
            mock_db_session.query.assert_called()
            filter_calls = mock_db_session.query.return_value.filter.call_args_list
            # Should have filtered by both agent_id and tenant_id
            assert len(filter_calls) >= 1
    
    def test_list_agents_tenant_isolation(self, persistence_service, mock_db_session):
        """Test that agent listing is isolated by tenant."""
        tenant_id = "test-tenant"
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        with patch('smeflow.agents.persistence.get_db_session', return_value=mock_db_session):
            persistence_service.list_agents(tenant_id, db=mock_db_session)
            
            # Verify tenant isolation in query
            mock_query.filter.assert_called()
    
    def test_update_agent_tenant_isolation(self, persistence_service, mock_db_session):
        """Test that agent updates are isolated by tenant."""
        agent_id = uuid.uuid4()
        tenant_id = "test-tenant"
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        updates = {"name": "Updated Name"}
        
        with patch('smeflow.agents.persistence.get_db_session', return_value=mock_db_session):
            result = persistence_service.update_agent(agent_id, tenant_id, updates, mock_db_session)
            
            assert result is None  # Should not find agent from different tenant
    
    def test_delete_agent_tenant_isolation(self, persistence_service, mock_db_session):
        """Test that agent deletion is isolated by tenant."""
        agent_id = uuid.uuid4()
        tenant_id = "test-tenant"
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with patch('smeflow.agents.persistence.get_db_session', return_value=mock_db_session):
            result = persistence_service.delete_agent(agent_id, tenant_id, db=mock_db_session)
            
            assert result is False  # Should not find agent from different tenant


class TestAfricanMarketOptimizations:
    """Test African market-specific optimizations in persistence."""
    
    def test_nigerian_market_config(self):
        """Test Nigerian market configuration."""
        config = AgentPersistenceConfig(
            agent_type=AgentType.MENTOR,
            llm_provider="openai",
            llm_model="gpt-4",
            region="NG",
            timezone="Africa/Lagos",
            languages=["en", "ha", "yo", "ig"],
            currency="NGN"
        )
        
        assert config.region == "NG"
        assert config.timezone == "Africa/Lagos"
        assert "ha" in config.languages  # Hausa
        assert "yo" in config.languages  # Yoruba
        assert "ig" in config.languages  # Igbo
        assert config.currency == "NGN"
    
    def test_kenyan_market_config(self):
        """Test Kenyan market configuration."""
        config = AgentPersistenceConfig(
            agent_type=AgentType.AUTOMATOR,
            llm_provider="anthropic",
            llm_model="claude-3-sonnet",
            tools=["mpesa_integration"],
            region="KE",
            timezone="Africa/Nairobi",
            languages=["en", "sw"],
            currency="KES"
        )
        
        assert config.region == "KE"
        assert config.timezone == "Africa/Nairobi"
        assert "sw" in config.languages  # Swahili
        assert config.currency == "KES"
        assert "mpesa_integration" in config.tools
    
    def test_south_african_market_config(self):
        """Test South African market configuration."""
        config = AgentPersistenceConfig(
            agent_type=AgentType.SUPERVISOR,
            llm_provider="openai",
            llm_model="gpt-4",
            region="ZA",
            timezone="Africa/Johannesburg",
            languages=["en"],
            currency="ZAR"
        )
        
        assert config.region == "ZA"
        assert config.timezone == "Africa/Johannesburg"
        assert config.currency == "ZAR"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
