"""
Tests for AGENT-003 database models: LLMUsage, LLMCache, and ProviderHealth.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from smeflow.database.models import (
    Base, Tenant, Agent, LLMUsage, LLMCache, ProviderHealth
)
from smeflow.agents.base import AgentType


class TestLLMUsageModel:
    """Test cases for LLMUsage model."""
    
    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing."""
        engine = create_engine("sqlite:///:memory:")
        # Create tables individually to avoid JSONB issues with SQLite
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    region VARCHAR(10) NOT NULL DEFAULT 'NG',
                    subscription_tier VARCHAR(20) NOT NULL DEFAULT 'free',
                    is_active BOOLEAN DEFAULT TRUE,
                    settings TEXT NOT NULL DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS agents (
                    id VARCHAR(50) PRIMARY KEY,
                    tenant_id VARCHAR(50) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    config TEXT NOT NULL DEFAULT '{}',
                    prompts TEXT NOT NULL DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS llm_usage (
                    id VARCHAR(50) PRIMARY KEY,
                    tenant_id VARCHAR(50) NOT NULL,
                    agent_id VARCHAR(50),
                    provider VARCHAR(50) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    cost_usd DECIMAL(10,6) NOT NULL,
                    cost_local DECIMAL(10,2),
                    currency VARCHAR(3),
                    response_time_ms INTEGER,
                    cache_hit BOOLEAN DEFAULT FALSE,
                    request_hash VARCHAR(64),
                    region VARCHAR(10) NOT NULL DEFAULT 'NG',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                    FOREIGN KEY (agent_id) REFERENCES agents(id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS llm_cache (
                    id VARCHAR(50) PRIMARY KEY,
                    cache_key VARCHAR(255) UNIQUE NOT NULL,
                    tenant_id VARCHAR(50),
                    prompt_hash VARCHAR(64) NOT NULL,
                    response_data TEXT NOT NULL,
                    provider VARCHAR(50) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    hit_count INTEGER DEFAULT 0,
                    expires_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS provider_health (
                    id VARCHAR(50) PRIMARY KEY,
                    provider VARCHAR(50) NOT NULL,
                    region VARCHAR(10) NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    error_rate DECIMAL(5,4) DEFAULT 0.0,
                    response_time_avg INTEGER,
                    last_success DATETIME,
                    last_error DATETIME,
                    last_check DATETIME,
                    is_healthy BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    UNIQUE(provider, region)
                )
            """))
            conn.commit()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create test tenant
        tenant = Tenant(
            id="test-tenant",
            name="Test Tenant",
            region="NG"
        )
        session.add(tenant)
        
        # Create test agent
        agent = Agent(
            id=uuid4(),
            tenant_id="test-tenant",
            name="Test Agent",
            type="researcher",
            config={"test": "config"},
            prompts={"system": "You are a helpful assistant"}
        )
        session.add(agent)
        session.commit()
        
        yield session
        session.close()
    
    def test_llm_usage_creation(self, db_session):
        """Test LLMUsage model creation."""
        usage = LLMUsage(
            tenant_id="test-tenant",
            provider="openai",
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost_usd=0.01,
            cost_local=16.5,
            currency="NGN",
            cache_hit=False,
            response_time_ms=500,
            request_hash="test-hash-123",
            region="NG"
        )
        
        db_session.add(usage)
        db_session.commit()
        
        # Verify creation
        saved_usage = db_session.query(LLMUsage).first()
        assert saved_usage.tenant_id == "test-tenant"
        assert saved_usage.provider == "openai"
        assert saved_usage.model == "gpt-4o"
        assert saved_usage.total_tokens == 150
        assert float(saved_usage.cost_usd) == 0.01
        assert saved_usage.currency == "NGN"
        assert saved_usage.cache_hit is False
        assert saved_usage.created_at is not None
    
    def test_llm_usage_with_agent(self, db_session):
        """Test LLMUsage with agent relationship."""
        agent = db_session.query(Agent).first()
        
        usage = LLMUsage(
            tenant_id="test-tenant",
            agent_id=agent.id,
            provider="anthropic",
            model="claude-3-sonnet",
            input_tokens=80,
            output_tokens=40,
            total_tokens=120,
            cost_usd=0.008,
            cache_hit=True,
            response_time_ms=0,
            request_hash="cached-hash-456",
            region="NG"
        )
        
        db_session.add(usage)
        db_session.commit()
        
        # Verify relationship
        saved_usage = db_session.query(LLMUsage).filter_by(agent_id=agent.id).first()
        assert saved_usage.agent_id == agent.id
        assert saved_usage.cache_hit is True
        assert saved_usage.response_time_ms == 0
    
    def test_llm_usage_required_fields(self, db_session):
        """Test LLMUsage required fields validation."""
        # Missing required fields should raise error
        with pytest.raises(IntegrityError):
            usage = LLMUsage(
                # Missing tenant_id
                provider="openai",
                model="gpt-4o"
            )
            db_session.add(usage)
            db_session.commit()
    
    def test_llm_usage_tenant_relationship(self, db_session):
        """Test LLMUsage tenant relationship."""
        usage = LLMUsage(
            tenant_id="test-tenant",
            provider="openai",
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost_usd=0.01,
            region="NG"
        )
        
        db_session.add(usage)
        db_session.commit()
        
        # Test relationship
        tenant = db_session.query(Tenant).first()
        # Test relationship - query usage records for this tenant
        usage_records = db_session.query(LLMUsage).filter(LLMUsage.tenant_id == tenant.id).all()
        assert len(usage_records) == 1
        assert usage_records[0].provider == "openai"


class TestLLMCacheModel:
    """Test cases for LLMCache model."""
    
    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing."""
        engine = create_engine("sqlite:///:memory:")
        # Create tables individually to avoid JSONB issues with SQLite
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    region VARCHAR(10) NOT NULL DEFAULT 'NG',
                    subscription_tier VARCHAR(20) NOT NULL DEFAULT 'free',
                    is_active BOOLEAN DEFAULT TRUE,
                    settings TEXT NOT NULL DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS agents (
                    id VARCHAR(50) PRIMARY KEY,
                    tenant_id VARCHAR(50) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    config TEXT NOT NULL DEFAULT '{}',
                    prompts TEXT NOT NULL DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS llm_usage (
                    id VARCHAR(50) PRIMARY KEY,
                    tenant_id VARCHAR(50) NOT NULL,
                    agent_id VARCHAR(50),
                    provider VARCHAR(50) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    cost_usd DECIMAL(10,6) NOT NULL,
                    cost_local DECIMAL(10,2),
                    currency VARCHAR(3),
                    response_time_ms INTEGER,
                    cache_hit BOOLEAN DEFAULT FALSE,
                    request_hash VARCHAR(64),
                    region VARCHAR(10) NOT NULL DEFAULT 'NG',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                    FOREIGN KEY (agent_id) REFERENCES agents(id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS llm_cache (
                    id VARCHAR(50) PRIMARY KEY,
                    cache_key VARCHAR(255) UNIQUE NOT NULL,
                    tenant_id VARCHAR(50),
                    prompt_hash VARCHAR(64) NOT NULL,
                    response_data TEXT NOT NULL,
                    provider VARCHAR(50) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    hit_count INTEGER DEFAULT 0,
                    expires_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS provider_health (
                    id VARCHAR(50) PRIMARY KEY,
                    provider VARCHAR(50) NOT NULL,
                    region VARCHAR(10) NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    error_rate DECIMAL(5,4) DEFAULT 0.0,
                    response_time_avg INTEGER,
                    last_success DATETIME,
                    last_error DATETIME,
                    last_check DATETIME,
                    is_healthy BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    UNIQUE(provider, region)
                )
            """))
            conn.commit()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create test tenant
        tenant = Tenant(
            id="test-tenant",
            name="Test Tenant",
            region="NG"
        )
        session.add(tenant)
        session.commit()
        
        yield session
        session.close()
    
    def test_llm_cache_creation(self, db_session):
        """Test LLMCache model creation."""
        cache_entry = LLMCache(
            cache_key="test-tenant:hash123",
            tenant_id="test-tenant",
            prompt_hash="hash123",
            response_data={
                "content": "Test response",
                "tokens": 100,
                "cost": 0.01
            },
            provider="openai",
            model="gpt-4o",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        db_session.add(cache_entry)
        db_session.commit()
        
        # Verify creation
        saved_cache = db_session.query(LLMCache).first()
        assert saved_cache.cache_key == "test-tenant:hash123"
        assert saved_cache.tenant_id == "test-tenant"
        assert saved_cache.prompt_hash == "hash123"
        assert saved_cache.response_data["content"] == "Test response"
        assert saved_cache.provider == "openai"
        assert saved_cache.hit_count == 0
        assert saved_cache.created_at is not None
    
    def test_llm_cache_global_entry(self, db_session):
        """Test LLMCache global entry (no tenant)."""
        cache_entry = LLMCache(
            cache_key="global:hash456",
            tenant_id=None,  # Global cache
            prompt_hash="hash456",
            response_data={
                "content": "Global response",
                "tokens": 50
            },
            provider="anthropic",
            model="claude-3-haiku",
            expires_at=datetime.utcnow() + timedelta(hours=12)
        )
        
        db_session.add(cache_entry)
        db_session.commit()
        
        # Verify global entry
        saved_cache = db_session.query(LLMCache).filter_by(tenant_id=None).first()
        assert saved_cache.cache_key == "global:hash456"
        assert saved_cache.tenant_id is None
        assert saved_cache.response_data["content"] == "Global response"
    
    def test_llm_cache_hit_count_increment(self, db_session):
        """Test LLMCache hit count increment."""
        cache_entry = LLMCache(
            cache_key="test-key",
            prompt_hash="test-hash",
            response_data={"content": "test"},
            provider="openai",
            model="gpt-4o",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        db_session.add(cache_entry)
        db_session.commit()
        
        # Simulate cache hits
        cache_entry.hit_count += 1
        db_session.commit()
        
        cache_entry.hit_count += 1
        db_session.commit()
        
        # Verify hit count
        saved_cache = db_session.query(LLMCache).first()
        assert saved_cache.hit_count == 2
    
    def test_llm_cache_expiration(self, db_session):
        """Test LLMCache expiration logic."""
        # Expired entry
        expired_cache = LLMCache(
            cache_key="expired-key",
            prompt_hash="expired-hash",
            response_data={"content": "expired"},
            provider="openai",
            model="gpt-4o",
            expires_at=datetime.utcnow() - timedelta(hours=1)  # Expired
        )
        
        # Valid entry
        valid_cache = LLMCache(
            cache_key="valid-key",
            prompt_hash="valid-hash",
            response_data={"content": "valid"},
            provider="openai",
            model="gpt-4o",
            expires_at=datetime.utcnow() + timedelta(hours=1)  # Valid
        )
        
        db_session.add_all([expired_cache, valid_cache])
        db_session.commit()
        
        # Query only valid entries
        valid_entries = db_session.query(LLMCache).filter(
            LLMCache.expires_at > datetime.utcnow()
        ).all()
        
        assert len(valid_entries) == 1
        assert valid_entries[0].cache_key == "valid-key"


class TestProviderHealthModel:
    """Test cases for ProviderHealth model."""
    
    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing."""
        engine = create_engine("sqlite:///:memory:")
        # Create tables individually to avoid JSONB issues with SQLite
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    region VARCHAR(10) NOT NULL DEFAULT 'NG',
                    subscription_tier VARCHAR(20) NOT NULL DEFAULT 'free',
                    is_active BOOLEAN DEFAULT TRUE,
                    settings TEXT NOT NULL DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS agents (
                    id VARCHAR(50) PRIMARY KEY,
                    tenant_id VARCHAR(50) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    config TEXT NOT NULL DEFAULT '{}',
                    prompts TEXT NOT NULL DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS llm_usage (
                    id VARCHAR(50) PRIMARY KEY,
                    tenant_id VARCHAR(50) NOT NULL,
                    agent_id VARCHAR(50),
                    provider VARCHAR(50) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    cost_usd DECIMAL(10,6) NOT NULL,
                    cost_local DECIMAL(10,2),
                    currency VARCHAR(3),
                    response_time_ms INTEGER,
                    cache_hit BOOLEAN DEFAULT FALSE,
                    request_hash VARCHAR(64),
                    region VARCHAR(10) NOT NULL DEFAULT 'NG',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                    FOREIGN KEY (agent_id) REFERENCES agents(id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS llm_cache (
                    id VARCHAR(50) PRIMARY KEY,
                    cache_key VARCHAR(255) UNIQUE NOT NULL,
                    tenant_id VARCHAR(50),
                    prompt_hash VARCHAR(64) NOT NULL,
                    response_data TEXT NOT NULL,
                    provider VARCHAR(50) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    hit_count INTEGER DEFAULT 0,
                    expires_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS provider_health (
                    id VARCHAR(50) PRIMARY KEY,
                    provider VARCHAR(50) NOT NULL,
                    region VARCHAR(10) NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    error_rate DECIMAL(5,4) DEFAULT 0.0,
                    response_time_avg INTEGER,
                    last_success DATETIME,
                    last_error DATETIME,
                    last_check DATETIME,
                    is_healthy BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    UNIQUE(provider, region)
                )
            """))
            conn.commit()
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_provider_health_creation(self, db_session):
        """Test ProviderHealth model creation."""
        health = ProviderHealth(
            provider="openai",
            region="NG",
            is_healthy=True,
            success_count=100,
            error_count=5,
            error_rate=0.05,
            response_time_avg=500,
            last_success=datetime.utcnow(),
            last_check=datetime.utcnow()
        )
        
        db_session.add(health)
        db_session.commit()
        
        # Verify creation
        saved_health = db_session.query(ProviderHealth).first()
        assert saved_health.provider == "openai"
        assert saved_health.region == "NG"
        assert saved_health.is_healthy is True
        assert saved_health.success_count == 100
        assert saved_health.error_count == 5
        assert float(saved_health.error_rate) == 0.05
        assert saved_health.response_time_avg == 500
    
    def test_provider_health_multiple_regions(self, db_session):
        """Test ProviderHealth for multiple regions."""
        # Same provider, different regions
        health_ng = ProviderHealth(
            provider="openai",
            region="NG",
            is_healthy=True,
            success_count=50,
            error_count=2
        )
        
        health_ke = ProviderHealth(
            provider="openai",
            region="KE",
            is_healthy=False,
            success_count=20,
            error_count=10
        )
        
        db_session.add_all([health_ng, health_ke])
        db_session.commit()
        
        # Verify separate records
        ng_health = db_session.query(ProviderHealth).filter_by(region="NG").first()
        ke_health = db_session.query(ProviderHealth).filter_by(region="KE").first()
        
        assert ng_health.is_healthy is True
        assert ke_health.is_healthy is False
        assert ng_health.success_count == 50
        assert ke_health.success_count == 20
    
    def test_provider_health_error_rate_calculation(self, db_session):
        """Test error rate calculation logic."""
        health = ProviderHealth(
            provider="anthropic",
            region="ZA",
            success_count=80,
            error_count=20
        )
        
        # Calculate error rate
        total_requests = health.success_count + health.error_count
        health.error_rate = health.error_count / total_requests if total_requests > 0 else 0
        
        db_session.add(health)
        db_session.commit()
        
        # Verify calculation
        saved_health = db_session.query(ProviderHealth).first()
        assert float(saved_health.error_rate) == 0.2  # 20/100
    
    def test_provider_health_defaults(self, db_session):
        """Test ProviderHealth default values."""
        health = ProviderHealth(
            provider="test-provider",
            region="US"
        )
        
        db_session.add(health)
        db_session.commit()
        
        # Verify defaults
        saved_health = db_session.query(ProviderHealth).first()
        assert saved_health.is_healthy is True  # Default
        assert saved_health.success_count == 0  # Default
        assert saved_health.error_count == 0  # Default
        assert saved_health.error_rate is None or float(saved_health.error_rate) == 0.0  # Default
        assert saved_health.id is not None


class TestLLMModelsIntegration:
    """Integration tests for LLM models."""
    
    @pytest.fixture
    def db_session(self):
        """Create in-memory database session with full schema."""
        engine = create_engine("sqlite:///:memory:")
        # Create tables individually to avoid JSONB issues with SQLite
        from sqlalchemy import text
        with engine.connect() as conn:
            # Create tables without JSONB columns for SQLite compatibility
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    region VARCHAR(10) NOT NULL DEFAULT 'NG',
                    subscription_tier VARCHAR(20) NOT NULL DEFAULT 'free',
                    is_active BOOLEAN DEFAULT TRUE,
                    settings TEXT NOT NULL DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS agents (
                    id VARCHAR(50) PRIMARY KEY,
                    tenant_id VARCHAR(50) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    config TEXT NOT NULL DEFAULT '{}',
                    prompts TEXT NOT NULL DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS llm_usage (
                    id VARCHAR(50) PRIMARY KEY,
                    tenant_id VARCHAR(50) NOT NULL,
                    agent_id VARCHAR(50),
                    provider VARCHAR(50) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    cost_usd DECIMAL(10,6) NOT NULL,
                    cost_local DECIMAL(10,2),
                    currency VARCHAR(3),
                    response_time_ms INTEGER,
                    cache_hit BOOLEAN DEFAULT FALSE,
                    request_hash VARCHAR(64),
                    region VARCHAR(10) NOT NULL DEFAULT 'NG',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                    FOREIGN KEY (agent_id) REFERENCES agents(id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS llm_cache (
                    id VARCHAR(50) PRIMARY KEY,
                    cache_key VARCHAR(255) UNIQUE NOT NULL,
                    tenant_id VARCHAR(50),
                    prompt_hash VARCHAR(64) NOT NULL,
                    response_data TEXT NOT NULL,
                    provider VARCHAR(50) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    hit_count INTEGER DEFAULT 0,
                    expires_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS provider_health (
                    id VARCHAR(50) PRIMARY KEY,
                    provider VARCHAR(50) NOT NULL,
                    region VARCHAR(10) NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    error_rate DECIMAL(5,4) DEFAULT 0.0,
                    response_time_avg INTEGER,
                    last_success DATETIME,
                    last_error DATETIME,
                    last_check DATETIME,
                    is_healthy BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    UNIQUE(provider, region)
                )
            """))
            conn.commit()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create test data
        tenant = Tenant(
            id="integration-tenant",
            name="Integration Tenant",
            region="NG"
        )
        
        agent = Agent(
            id=uuid4(),
            tenant_id="integration-tenant",
            name="Integration Agent",
            type="researcher",
            config={"test": "config"},
            prompts={"system": "Test prompt"}
        )
        
        session.add_all([tenant, agent])
        session.commit()
        
        yield session
        session.close()
    
    def test_complete_llm_workflow(self, db_session):
        """Test complete LLM workflow with all models."""
        agent = db_session.query(Agent).first()
        
        # 1. Create usage record
        usage2 = LLMUsage(
            tenant_id="integration-tenant",
            agent_id=agent.id,
            provider="openai",
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost_usd=0.01,
            cost_local=16.5,
            currency="NGN",
            cache_hit=False,
            response_time_ms=500,
            request_hash="workflow-hash",
            region="NG"
        )
        
        # 2. Create cache entry
        cache = LLMCache(
            cache_key="integration-tenant:workflow-hash",
            tenant_id="integration-tenant",
            prompt_hash="workflow-hash",
            response_data={
                "content": "Cached response",
                "tokens": 150,
                "cost": 0.01
            },
            provider="openai",
            model="gpt-4o",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        # 3. Update provider health
        health = ProviderHealth(
            provider="openai",
            region="NG",
            is_healthy=True,
            success_count=1,
            error_count=0,
            error_rate=0.0,
            response_time_avg=500,
            last_success=datetime.utcnow(),
            last_check=datetime.utcnow()
        )
        
        db_session.add_all([usage2, cache, health])
        db_session.commit()
        
        # Verify all records created
        assert db_session.query(LLMUsage).count() == 1
        assert db_session.query(LLMCache).count() == 1
        assert db_session.query(ProviderHealth).count() == 1
        
        # Verify relationships
        tenant = db_session.query(Tenant).first()
        assert len(tenant.llm_usage) == 1
        
        # Verify data consistency
        saved_usage = db_session.query(LLMUsage).first()
        saved_cache = db_session.query(LLMCache).first()
        saved_health = db_session.query(ProviderHealth).first()
        
        assert saved_usage.request_hash == saved_cache.prompt_hash
        assert saved_usage.provider == saved_health.provider
        assert saved_usage.region == saved_health.region
    
    def test_tenant_isolation(self, db_session):
        """Test tenant isolation across LLM models."""
        # Create second tenant
        tenant2 = Tenant(
            id="tenant-2",
            name="Tenant 2",
            region="KE"
        )
        db_session.add(tenant2)
        db_session.commit()
        
        # Create records for both tenants
        usage1 = LLMUsage(
            tenant_id="integration-tenant",
            provider="openai",
            model="gpt-4o",
            input_tokens=80,
            output_tokens=20,
            total_tokens=100,
            cost_usd=0.01,
            region="NG"
        )

        usage2 = LLMUsage(
            tenant_id="tenant-2",
            provider="openai",
            model="gpt-4o",
            input_tokens=150,
            output_tokens=50,
            total_tokens=200,
            cost_usd=0.02,
            region="KE"
        )

        cache1 = LLMCache(
            cache_key="integration-tenant:hash1",
            tenant_id="integration-tenant",
            prompt_hash="hash1",
            response_data={"content": "Response 1"},
            provider="openai",
            model="gpt-4o",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        cache2 = LLMCache(
            cache_key="tenant-2:hash2",
            tenant_id="tenant-2",
            prompt_hash="hash2",
            response_data={"content": "Response 2"},
            provider="openai",
            model="gpt-4o",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        db_session.add_all([usage1, usage2, cache1, cache2])
        db_session.commit()
        
        # Verify tenant isolation
        tenant1_usage = db_session.query(LLMUsage).filter_by(tenant_id="integration-tenant").all()
        tenant2_usage = db_session.query(LLMUsage).filter_by(tenant_id="tenant-2").all()
        
        assert len(tenant1_usage) == 1
        assert len(tenant2_usage) == 1
        assert tenant1_usage[0].total_tokens == 100
        assert tenant2_usage[0].total_tokens == 200
        
        tenant1_cache = db_session.query(LLMCache).filter_by(tenant_id="integration-tenant").all()
        tenant2_cache = db_session.query(LLMCache).filter_by(tenant_id="tenant-2").all()
        
        assert len(tenant1_cache) == 1
        assert len(tenant2_cache) == 1
        assert tenant1_cache[0].response_data["content"] == "Response 1"
        assert tenant2_cache[0].response_data["content"] == "Response 2"


if __name__ == "__main__":
    pytest.main([__file__])
